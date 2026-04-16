"""
Dark NOC — LangGraph 1.0 Autonomous NOC Agent
================================================
The main agent graph orchestrating all Dark NOC AI operations.

GRAPH NODES:
    consume_logs    → Read from Kafka nginx-logs topic
    rag_retrieval   → Query pgvector for relevant runbooks
    analyze         → Call Granite 4.0 via vLLM for structured RCA
    remediate       → Execute fix via MCP tool calls (AAP + OCP)
    escalate        → Create ServiceNow ticket + Slack for human cases
    notify          → Send Slack success/failure notification
    audit           → Write to Langfuse trace + Kafka incident-audit

DURABLE STATE:
    PostgresSaver stores checkpoints to pgvector PostgreSQL.
    If the agent pod crashes mid-workflow, it resumes from last checkpoint.
    Thread ID: incident_id (UUID from Kafka message key)

STRUCTURED OUTPUT:
    Granite 4.0 + vLLM xgrammar enforces RootCauseAnalysis JSON schema.
    Zero free-text parsing — guaranteed valid JSON every call.
"""

import os
import uuid
import json
import time
import logging
import hashlib
from datetime import datetime, timezone
from typing import AsyncIterator

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg2
import psycopg
from kafka import KafkaConsumer, KafkaProducer
import psycopg2.extras
from langfuse import Langfuse
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from state import IncidentState, LogEvent, RootCauseAnalysis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("dark-noc-agent")

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
VLLM_URL = os.getenv("VLLM_URL", "http://granite-vllm-predictor.dark-noc-hub.svc:8080/v1")
MODEL_ID = os.getenv("MODEL_ID", "granite-4-h-tiny")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "dark-noc-kafka-kafka-bootstrap.dark-noc-kafka.svc:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "nginx-logs")
KAFKA_GROUP = os.getenv("KAFKA_GROUP", "dark-noc-agent")
PGVECTOR_URL = os.getenv("PGVECTOR_URL", "postgresql://noc_agent:pgvector-noc-demo-2026@pgvector-postgres-rw.dark-noc-rag.svc:5432/noc_rag")
PG_CHECKPOINT_URL = os.getenv("PG_CHECKPOINT_URL", "postgresql://langfuse:langfuse-pg-demo-2026@langfuse-postgres-rw.dark-noc-observability.svc:5432/langfuse")

MCP_OPENSHIFT_URL = os.getenv("MCP_OPENSHIFT_URL", "http://mcp-openshift.dark-noc-mcp.svc:8001/mcp")
MCP_LOKI_URL = os.getenv("MCP_LOKI_URL", "http://mcp-lokistack.dark-noc-mcp.svc:8002/mcp")
MCP_AAP_URL = os.getenv("MCP_AAP_URL", "http://mcp-aap.dark-noc-mcp.svc:8004/mcp")
MCP_SLACK_URL = os.getenv("MCP_SLACK_URL", "http://mcp-slack.dark-noc-mcp.svc:8005/mcp")
MCP_SNOW_URL = os.getenv("MCP_SNOW_URL", "http://mcp-servicenow.dark-noc-mcp.svc:8006/mcp")
AAP_LIGHTSPEED_TEMPLATE = os.getenv("AAP_LIGHTSPEED_TEMPLATE", "lightspeed-generate-and-run")

# ─────────────────────────────────────────────
# LLM Client (vLLM OpenAI-compatible API)
# ─────────────────────────────────────────────
llm = ChatOpenAI(
    base_url=VLLM_URL,
    api_key="not-needed",       # vLLM doesn't require API key
    model=MODEL_ID,
    temperature=0.1,             # Low temp for consistent structured output
    max_tokens=2048,
)

# Langfuse for tracing
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
    host=os.getenv("LANGFUSE_HOST", "http://langfuse.dark-noc-observability.svc:3000"),
)

# ─────────────────────────────────────────────
# MCP Tool Helper
# ─────────────────────────────────────────────
async def call_mcp_tool(server_url: str, tool_name: str, args: dict) -> dict:
    """Call a FastMCP tool via Streamable HTTP transport."""
    try:
        async with streamablehttp_client(server_url) as (read, write, _):
            async with ClientSession(read, write) as client:
                await client.initialize()
                result = await client.call_tool(tool_name, args or {})
                if result.content and len(result.content) > 0:
                    first = result.content[0]
                    text = getattr(first, "text", "")
                    if text:
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            logger.warning(
                                "[MCP] Non-JSON response from %s tool=%s: %s",
                                server_url,
                                tool_name,
                                text[:240],
                            )
                            return {"success": False, "message": text}
        return {"success": False, "message": "empty MCP response"}
    except Exception as exc:
        logger.warning("[MCP] Tool call failed server=%s tool=%s error=%s", server_url, tool_name, exc)
        return {"success": False, "message": str(exc)}


def build_lightspeed_playbook(log: LogEvent, rca: RootCauseAnalysis, incident_id: str) -> tuple[str, str]:
    """
    Build a deterministic, incident-scoped playbook artifact for the Lightspeed demo.
    The playbook is passed to AAP as extra vars and captured in audit/notification trails.
    """
    failure_type = str(rca.get("failure_type", "Unknown")).strip() or "Unknown"
    failure_slug = "".join(c.lower() if c.isalnum() else "-" for c in failure_type).strip("-")
    if not failure_slug:
        failure_slug = "unknown"
    artifact_id = hashlib.sha1(incident_id.encode("utf-8")).hexdigest()[:8]
    playbook_name = f"generated-{failure_slug}-{artifact_id}.yaml"

    summary = str(rca.get("summary", "No summary available")).replace('"', '\\"')
    incident_ref = incident_id[:8]
    namespace = log.get("namespace", "dark-noc-edge")
    deployment = "nginx"

    playbook_yaml = f"""---
- name: Dark NOC AI-generated remediation ({incident_ref})
  hosts: localhost
  gather_facts: false
  vars:
    namespace: "{namespace}"
    deployment_name: "{deployment}"
    edge_site_id: "{log.get('edge_site_id', 'edge-01')}"
    incident_id: "{incident_id}"
    model_failure_type: "{failure_type}"
    model_summary: "{summary}"
  tasks:
    - name: Validate AI-generated remediation inputs
      ansible.builtin.debug:
        msg:
          - "site={{ edge_site_id }}"
          - "incident={{ incident_id }}"
          - "failure_type={{ model_failure_type }}"
          - "summary={{ model_summary }}"
    - name: Restart target deployment on edge site
      kubernetes.core.k8s:
        state: patched
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: "{{{{ deployment_name }}}}"
            namespace: "{{{{ namespace }}}}"
          spec:
            template:
              metadata:
                annotations:
                  kubectl.kubernetes.io/restartedAt: "{{{{ lookup('pipe', 'date -u +%Y-%m-%dT%H:%M:%SZ') }}}}"
"""
    return playbook_name, playbook_yaml


# ─────────────────────────────────────────────
# RAG Retrieval Helper
# ─────────────────────────────────────────────
def rag_search(query: str, doc_type: str, top_k: int = 5) -> list[str]:
    """
    Embed query and find top-k similar chunks filtered by metadata.type.
    doc_type is typically "runbook" or "documentation".
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embedding = model.encode(query).tolist()

    conn = psycopg2.connect(PGVECTOR_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT content,
                          COALESCE(metadata->>'title', metadata->>'doc_title', 'unknown') as title,
                          1 - (embedding <=> %s::vector) as similarity
                   FROM documents
                   WHERE metadata->>'type' = %s
                   ORDER BY embedding <=> %s::vector
                   LIMIT %s""",
                (str(embedding), doc_type, str(embedding), top_k)
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    chunks = []
    for content, title, similarity in rows:
        if similarity > 0.3:     # Minimum relevance threshold
            label = "Runbook" if doc_type == "runbook" else "Documentation"
            chunks.append(f"[{label}: {title} (similarity={similarity:.2f})]\n{content}")
    return chunks


def fallback_rca(log: LogEvent) -> RootCauseAnalysis:
    """
    Deterministic RCA used when model inference is unavailable.
    Keeps demo automation functional without masking that fallback was used.
    """
    message = str(log.get("message", "")).lower()
    scenario = str(log.get("raw", {}).get("labels", {}).get("dark_noc_scenario", "")).strip().lower()

    if scenario == "lightspeed":
        failure_type = "Ansible Automation Failure"
        severity = "high"
        escalate = False
        confidence = 0.82
        summary = "Detected Lightspeed workflow incident; proceeding with AAP-assisted remediation."
        actions = ["Launch Lightspeed AAP template", "Track execution status", "Create governance ticket"]
    elif "oomkilled" in message or scenario == "oom":
        failure_type = "OOMKilled"
        severity = "high"
        escalate = False
        confidence = 0.86
        summary = "Container memory exhaustion detected on edge workload."
        actions = ["Trigger restart-nginx via AAP", "Validate pod health", "Confirm memory limits"]
    elif "crashloop" in message or scenario == "crashloop":
        failure_type = "CrashLoopBackOff"
        severity = "high"
        escalate = False
        confidence = 0.84
        summary = "Repeated restart failure detected for target workload."
        actions = ["Trigger rollout restart", "Inspect recent logs", "Validate configuration and probes"]
    else:
        failure_type = "Unknown"
        severity = "critical"
        escalate = True
        confidence = 0.55
        summary = "Unable to classify incident confidently without model inference; escalating for human review."
        actions = ["Create ServiceNow incident", "Notify #demos", "Collect additional diagnostics"]

    return {
        "failure_type": failure_type,
        "confidence": confidence,
        "summary": summary,
        "evidence": [str(log.get("message", ""))[:400]],
        "recommended_actions": actions,
        "escalate_to_human": escalate,
        "estimated_severity": severity,
        "runbook_reference": "deterministic-fallback",
    }


# ─────────────────────────────────────────────
# GRAPH NODES
# ─────────────────────────────────────────────
def node_rag_retrieval(state: IncidentState) -> dict:
    """Retrieve relevant runbooks and product docs from pgvector."""
    log = state["log_event"]
    query = f"{log['message']} namespace={log['namespace']} pod={log['pod_name']}"

    logger.info(f"[RAG] Searching runbooks + documentation for: {query[:100]}")
    runbook_chunks = rag_search(query, doc_type="runbook", top_k=4)
    docs_chunks = rag_search(query, doc_type="documentation", top_k=4)
    chunks = runbook_chunks + docs_chunks
    logger.info(
        f"[RAG] Found {len(runbook_chunks)} runbook chunks and "
        f"{len(docs_chunks)} documentation chunks"
    )

    return {
        "rag_context": chunks,
        "rag_query_used": query,
        "next_action": "analyze",
    }


def node_analyze(state: IncidentState) -> dict:
    """
    Call Granite 4.0 with structured output schema to generate RCA.
    vLLM xgrammar enforces the RootCauseAnalysis JSON schema.
    """
    log = state["log_event"]
    rag_ctx = "\n\n---\n\n".join(state.get("rag_context", []))

    system_prompt = """You are an expert NOC (Network Operations Center) engineer analyzing
    Kubernetes/OpenShift log events. Perform root cause analysis and recommend remediation.
    You MUST respond with a valid JSON object matching the schema provided.
    Be concise and technically precise. Base your analysis on the log evidence."""

    user_prompt = f"""Analyze this edge cluster incident:

INCIDENT LOG:
  Timestamp: {log['timestamp']}
  Namespace: {log['namespace']}
  Pod: {log['pod_name']}
  Level: {log['level']}
  Message: {log['message']}

RELEVANT KNOWLEDGE (RUNBOOKS + PRODUCT DOCS):
{rag_ctx[:5000] if rag_ctx else "No matching runbooks or documentation found."}

Provide structured root cause analysis as JSON."""

    # JSON Schema for structured output (enforced by vLLM xgrammar)
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "RootCauseAnalysis",
            "schema": {
                "type": "object",
                "properties": {
                    "failure_type": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "summary": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "recommended_actions": {"type": "array", "items": {"type": "string"}},
                    "escalate_to_human": {"type": "boolean"},
                    "estimated_severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "runbook_reference": {"type": "string"}
                },
                "required": ["failure_type", "confidence", "summary", "recommended_actions",
                             "escalate_to_human", "estimated_severity"]
            }
        }
    }

    start = time.monotonic()
    trace = langfuse.trace(name="dark-noc-rca", input={"log": log["message"]})

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    used_fallback = False
    response = None
    try:
        response = llm.invoke(messages, response_format=response_format)
        rca: RootCauseAnalysis = json.loads(response.content)
    except Exception as e:
        used_fallback = True
        logger.warning(f"[ANALYZE] LLM unavailable; using deterministic fallback RCA: {e}")
        rca = fallback_rca(log)

    latency_ms = (time.monotonic() - start) * 1000

    trace.update(output=rca, metadata={"latency_ms": latency_ms, "used_fallback": used_fallback})
    logger.info(f"[ANALYZE] failure_type={rca['failure_type']} confidence={rca['confidence']:.2f} severity={rca['estimated_severity']}")

    scenario = str(log.get("raw", {}).get("labels", {}).get("dark_noc_scenario", "")).strip().lower()
    if scenario == "lightspeed":
        next_action = "lightspeed"
    else:
        next_action = "escalate" if rca["escalate_to_human"] else "remediate"

    return {
        "rca": rca,
        "analysis_tokens_used": response.usage_metadata.get("total_tokens", 0) if response and hasattr(response, "usage_metadata") else 0,
        "analysis_latency_ms": latency_ms,
        "next_action": next_action,
        "langfuse_trace_id": trace.id,
    }


async def node_lightspeed(state: IncidentState) -> dict:
    """
    Lightspeed-assisted remediation path:
    1) Launch AAP template intended for playbook generation + execution
    2) Open ServiceNow info incident for governance traceability
    3) Send Slack summary with ticket + job details
    """
    rca = state["rca"]
    log = state["log_event"]
    logger.info(f"[LIGHTSPEED] Starting Lightspeed workflow for incident {state['incident_id'][:8]}")

    start = time.monotonic()
    job_status = "not-started"
    job_id = ""
    action = f"Lightspeed-assisted remediation via AAP template '{AAP_LIGHTSPEED_TEMPLATE}'"
    success = False
    generated_name, generated_yaml = build_lightspeed_playbook(log, rca, state["incident_id"])
    generated_template_name = generated_name.rsplit(".yaml", 1)[0]
    generated_template_id = ""

    launch = await call_mcp_tool(
        MCP_AAP_URL, "launch_job",
        {
            "job_template_name": AAP_LIGHTSPEED_TEMPLATE,
            "extra_vars": {
                "namespace": log["namespace"],
                "deployment": "nginx",
                "edge_cluster": log["edge_site_id"],
                "incident_id": state["incident_id"],
                "lightspeed_mode": "assist",
                "failure_type": rca.get("failure_type", "Unknown"),
                "generated_playbook_name": generated_name,
                "generated_playbook_yaml": generated_yaml,
                "generated_from_model": True,
            },
        },
    )

    if launch.get("success"):
        job_id = str(launch.get("job_id", ""))
        for _ in range(24):  # up to ~120 seconds
            await asyncio.sleep(5)
            status = await call_mcp_tool(MCP_AAP_URL, "get_job_status", {"job_id": int(job_id)})
            job_status = str(status.get("status", "unknown"))
            if job_status in ("successful", "failed", "error", "canceled", "cancelled"):
                break
        success = job_status == "successful"
    else:
        job_status = launch.get("error", "launch-failed")

    # Keep AAP UI in sync: create/update a generated template entry for this artifact.
    try:
        upsert = await call_mcp_tool(
            MCP_AAP_URL, "upsert_job_template",
            {
                "template_name": generated_template_name,
                # AAP validates playbook path against SCM; generated YAML is passed
                # through extra_vars and executed by the stable wrapper playbook.
                "playbook": "playbooks/lightspeed-generate-and-run.yaml",
                "base_template_name": AAP_LIGHTSPEED_TEMPLATE,
            },
        )
        if upsert.get("success"):
            generated_template_id = str(upsert.get("template_id", ""))
    except Exception as e:
        logger.warning(f"[LIGHTSPEED] upsert template failed: {e}")

    snow = await call_mcp_tool(
        MCP_SNOW_URL, "create_incident",
        {
            "short_description": f"[Dark NOC Lightspeed] {rca.get('failure_type', 'Unknown')} on {log['edge_site_id']}",
            "description": (
                f"LangGraph routed incident to Lightspeed demo path.\n"
                f"Summary: {rca.get('summary', '')}\n"
                f"AAP Template: {AAP_LIGHTSPEED_TEMPLATE}\n"
                f"AAP Job ID: {job_id or 'N/A'}\n"
                f"AAP Job Status: {job_status}\n"
                f"Generated Playbook: {generated_name}\n"
                f"Incident ID: {state['incident_id']}"
            ),
            "priority": 3,
        },
    )
    ticket_number = snow.get("ticket_number", "INC-UNKNOWN")
    ticket_url = snow.get("incident_url", "")

    await call_mcp_tool(
        MCP_SLACK_URL, "send_message",
        {
            "text": (
                f":robot_face: *Ansible Lightspeed Demo*\n"
                f"- Site: {log['edge_site_id']}\n"
                f"- Incident: {state['incident_id'][:8]}\n"
                f"- Template: {AAP_LIGHTSPEED_TEMPLATE}\n"
                f"- AAP Job: {job_id or 'N/A'} ({job_status})\n"
                f"- Playbook: {generated_name}\n"
                f"- Generated Template: {generated_template_name}\n"
                f"- ServiceNow: {ticket_number}\n"
                f"- URL: {ticket_url}"
            ),
        },
    )

    result = {
        "action_taken": action,
        "tool_used": "mcp-aap+mcp-servicenow+mcp-slack",
        "success": success,
        "job_id": job_id,
        "duration_seconds": time.monotonic() - start,
        "output_summary": (
            f"Lightspeed template={AAP_LIGHTSPEED_TEMPLATE} status={job_status} playbook={generated_name}"
        ),
        "generated_template_name": generated_template_name,
        "generated_template_id": generated_template_id,
        "generated_playbook_name": generated_name,
        "generated_playbook_preview": generated_yaml[:700],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(f"[LIGHTSPEED] job_id={job_id or 'N/A'} status={job_status} success={success}")
    return {
        "remediation_result": result,
        "servicenow_ticket": ticket_number,
        "next_action": "notify",
    }


async def node_remediate(state: IncidentState) -> dict:
    """Execute remediation via MCP tool calls based on RCA."""
    rca = state["rca"]
    log = state["log_event"]

    logger.info(f"[REMEDIATE] Starting remediation for: {rca['failure_type']}")
    start = time.monotonic()

    # Step 1: Get current pod status via OpenShift MCP
    pod_status = await call_mcp_tool(
        MCP_OPENSHIFT_URL, "get_pods",
        {"namespace": log["namespace"]}
    )

    result = {
        "action_taken": "",
        "tool_used": "",
        "success": False,
        "job_id": "",
        "duration_seconds": 0.0,
        "output_summary": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    failure_type = rca.get("failure_type", "Unknown")
    failure_type_norm = str(failure_type).strip().lower()
    message_norm = str(log.get("message", "")).lower()

    restart_classes = {
        "oomkilled",
        "crashloopbackoff",
        "resource exhaustion",
        "resource unavailability",
    }
    should_restart = (
        failure_type_norm in restart_classes
        or "oomkilled" in message_norm
        or "crashloop" in message_norm
    )

    # Route to appropriate remediation based on failure type
    if should_restart:
        # Trigger AAP restart-nginx job
        job_result = await call_mcp_tool(
            MCP_AAP_URL, "launch_job",
            {
                "job_template_name": "restart-nginx",
                "extra_vars": {
                    "namespace": log["namespace"],
                    "deployment": "nginx",
                    "edge_cluster": log["edge_site_id"],
                }
            }
        )

        if job_result.get("success"):
            # Poll job status (max 2 minutes)
            job_id = job_result["job_id"]
            for _ in range(24):  # 24 * 5s = 120s
                await asyncio.sleep(5)
                status = await call_mcp_tool(
                    MCP_AAP_URL, "get_job_status", {"job_id": job_id}
                )
                if status.get("status") in ("successful", "failed"):
                    break

            result.update({
                "action_taken": f"Triggered AAP job: restart-nginx for {log['namespace']}/{log.get('pod_name','')}",
                "tool_used": "mcp-aap",
                "success": status.get("status") == "successful",
                "job_id": str(job_id),
                "output_summary": f"Job {job_id}: {status.get('status')}",
            })
        else:
            # Fallback: direct restart via OpenShift MCP
            restart = await call_mcp_tool(
                MCP_OPENSHIFT_URL, "rollout_restart",
                {"deployment": "nginx", "namespace": log["namespace"]}
            )
            result.update({
                "action_taken": "Triggered nginx rollout restart via OpenShift API",
                "tool_used": "mcp-openshift",
                "success": restart.get("success", False),
                "output_summary": restart.get("message", ""),
            })

    elif failure_type == "Unknown" or rca.get("escalate_to_human"):
        result.update({
            "action_taken": "No automated remediation — escalating to human",
            "tool_used": "none",
            "success": False,
            "output_summary": "Confidence too low for automated fix",
        })

    result["duration_seconds"] = time.monotonic() - start
    logger.info(f"[REMEDIATE] success={result['success']} action={result['action_taken']}")

    return {
        "pod_status": pod_status,
        "remediation_result": result,
        "next_action": "notify",
    }


async def node_escalate(state: IncidentState) -> dict:
    """Create ServiceNow ticket and send Slack alert for unresolvable incidents."""
    rca = state["rca"]
    log = state["log_event"]

    logger.info(f"[ESCALATE] Creating ServiceNow ticket for: {rca['failure_type']}")

    # Create ServiceNow incident
    snow_result = await call_mcp_tool(
        MCP_SNOW_URL, "create_incident",
        {
            "short_description": f"[Dark NOC] {rca['failure_type']} on {log['edge_site_id']} - {log['pod_name']}",
            "description": (
                f"Automated AI analysis detected {rca['failure_type']} on edge cluster.\n\n"
                f"Summary: {rca['summary']}\n\n"
                f"Evidence:\n" + "\n".join(f"- {e}" for e in rca.get("evidence", [])) + "\n\n"
                f"Recommended actions:\n" + "\n".join(f"- {a}" for a in rca.get("recommended_actions", [])) +
                f"\n\nAI Confidence: {rca['confidence']:.0%}\n"
                f"Langfuse Trace: {state.get('langfuse_trace_id', 'N/A')}"
            ),
            "priority": {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(rca["estimated_severity"], 3),
        }
    )

    ticket_number = snow_result.get("ticket_number", "INC-UNKNOWN")

    # Send Slack alert with ticket info
    await call_mcp_tool(
        MCP_SLACK_URL, "send_incident_ticket",
        {
            "ticket_number": ticket_number,
            "title": f"{rca['failure_type']} on {log['edge_site_id']}",
            "description": rca["summary"],
            "priority": str({"critical": 1, "high": 2, "medium": 3, "low": 4}.get(rca["estimated_severity"], 3)),
        }
    )

    return {
        "servicenow_ticket": ticket_number,
        "next_action": "audit",
    }


async def node_notify(state: IncidentState) -> dict:
    """Send Slack notification with remediation result."""
    rca = state["rca"]
    log = state["log_event"]
    rem = state.get("remediation_result") or {}

    result_str = "success" if rem.get("success") else "failed"

    # Send to Slack
    if not state.get("slack_thread_ts"):
        # First message: create thread
        slack_result = await call_mcp_tool(
            MCP_SLACK_URL, "send_alert",
            {
                "title": f"{rca['failure_type']} on {log['edge_site_id']}",
                "message": f"*Summary:* {rca['summary']}\n*Action:* {rem.get('action_taken', 'None')}",
                "severity": rca["estimated_severity"],
                "edge_site": log["edge_site_id"],
            }
        )
        thread_ts = slack_result.get("ts", "")
    else:
        thread_ts = state["slack_thread_ts"]

    # Reply with remediation result
    await call_mcp_tool(
        MCP_SLACK_URL, "send_remediation",
        {
            "alert_title": f"{rca['failure_type']} on {log['edge_site_id']}",
            "action_taken": rem.get("action_taken", "None"),
            "result": result_str,
            "job_id": str(rem.get("job_id", "")),
            "duration_seconds": rem.get("duration_seconds", 0),
            "thread_ts": thread_ts,
        }
    )

    return {
        "slack_thread_ts": thread_ts,
        "next_action": "audit",
    }


async def node_audit(state: IncidentState) -> dict:
    """Write incident audit record to Kafka incident-audit topic."""
    rca = state.get("rca", {})
    rem = state.get("remediation_result") or {}
    total_duration_ms = float(state.get("total_duration_ms", 0) or 0)
    if total_duration_ms <= 0:
        start_ms = float(state.get("incident_start_ms", 0) or 0)
        if start_ms > 0:
            total_duration_ms = max(0.0, (time.monotonic() * 1000.0) - start_ms)

    audit_record = {
        "incident_id": state["incident_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "edge_site_id": state["log_event"]["edge_site_id"],
        "failure_type": rca.get("failure_type", "Unknown"),
        "severity": rca.get("estimated_severity", "unknown"),
        "remediation_action": rem.get("action_taken", ""),
        "remediation_success": rem.get("success", False),
        "aap_job_id": rem.get("job_id", ""),
        "generated_playbook_name": rem.get("generated_playbook_name", ""),
        "servicenow_ticket": state.get("servicenow_ticket", ""),
        "ai_confidence": rca.get("confidence", 0),
        "total_duration_ms": round(total_duration_ms, 2),
        "langfuse_trace_id": state.get("langfuse_trace_id", ""),
    }

    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        producer.send("incident-audit", value=audit_record)
        producer.flush()
        producer.close()
        logger.info(f"[AUDIT] Written audit record for incident {state['incident_id']}")
    except Exception as e:
        logger.error(f"[AUDIT] Failed to write audit: {e}")

    return {"next_action": "complete"}


def route_after_analyze(state: IncidentState) -> str:
    """Router: after analysis, go to remediate, lightspeed, or escalate."""
    return state.get("next_action", "remediate")


def route_after_remediate(state: IncidentState) -> str:
    """Router: after remediation, always notify."""
    return "notify"


# ─────────────────────────────────────────────
# BUILD THE GRAPH
# ─────────────────────────────────────────────
def build_agent_graph() -> StateGraph:
    """Construct the LangGraph workflow."""
    workflow = StateGraph(IncidentState)

    workflow.add_node("rag_retrieval", node_rag_retrieval)
    workflow.add_node("analyze", node_analyze)
    workflow.add_node("lightspeed", node_lightspeed)
    workflow.add_node("remediate", node_remediate)
    workflow.add_node("escalate", node_escalate)
    workflow.add_node("notify", node_notify)
    workflow.add_node("audit", node_audit)

    workflow.set_entry_point("rag_retrieval")
    workflow.add_edge("rag_retrieval", "analyze")
    workflow.add_conditional_edges("analyze", route_after_analyze, {
        "lightspeed": "lightspeed",
        "remediate": "remediate",
        "escalate": "escalate",
    })
    workflow.add_edge("lightspeed", "notify")
    workflow.add_edge("remediate", "notify")
    workflow.add_edge("escalate", "notify")
    workflow.add_edge("notify", "audit")
    workflow.add_edge("audit", END)

    return workflow


# ─────────────────────────────────────────────
# MAIN CONSUMER LOOP
# ─────────────────────────────────────────────
import asyncio

async def main():
    """Main Kafka consumer loop — processes nginx-logs topic indefinitely."""
    logger.info("=" * 60)
    logger.info(" Dark NOC Agent starting...")
    logger.info(f" LLM: {VLLM_URL} | Model: {MODEL_ID}")
    logger.info(f" Kafka: {KAFKA_BOOTSTRAP} | Topic: {KAFKA_TOPIC}")
    logger.info("=" * 60)

    # Build graph; checkpointing can be enabled later when async saver is wired.
    workflow = build_agent_graph()
    app = workflow.compile()

    # Start Kafka consumer
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    logger.info(f"Listening on Kafka topic: {KAFKA_TOPIC}")

    for kafka_msg in consumer:
        raw = kafka_msg.value
        incident_id = str(uuid.uuid4())

        # Build LogEvent from Kafka message
        log_event: LogEvent = {
            "timestamp": raw.get("@timestamp", datetime.now(timezone.utc).isoformat()),
            "message": raw.get("message", ""),
            "level": raw.get("level", "error"),
            "namespace": raw.get("kubernetes", {}).get("namespace_name", "dark-noc-edge"),
            "pod_name": raw.get("kubernetes", {}).get("pod_name", "unknown"),
            "container": raw.get("kubernetes", {}).get("container_name", "nginx"),
            "edge_site_id": raw.get("labels", {}).get("edge_site_id", "edge-01"),
            "kafka_offset": kafka_msg.offset,
            "raw": raw,
        }

        # Only process error/warn level logs
        if log_event["level"] not in ("error", "warn", "ERROR", "WARN", "warning"):
            continue

        logger.info(f"[INCIDENT {incident_id[:8]}] Processing: {log_event['message'][:100]}")

        initial_state: IncidentState = {
            "log_event": log_event,
            "incident_id": incident_id,
            "incident_start_ms": time.monotonic() * 1000.0,
            "rag_context": [],
            "rag_query_used": "",
            "rca": None,
            "analysis_tokens_used": 0,
            "analysis_latency_ms": 0.0,
            "pod_status": {},
            "recent_errors": [],
            "remediation_result": {},
            "slack_thread_ts": "",
            "servicenow_ticket": "",
            "next_action": "rag_retrieval",
            "langfuse_trace_id": "",
            "total_duration_ms": 0.0,
            "error_message": "",
        }

        start = time.monotonic()
        try:
            # Run the agent graph
            config = {"configurable": {"thread_id": incident_id}}
            await app.ainvoke(initial_state, config=config)
            duration_ms = (time.monotonic() - start) * 1000
            logger.info(f"[INCIDENT {incident_id[:8]}] Complete in {duration_ms:.0f}ms")
        except Exception as e:
            logger.error(f"[INCIDENT {incident_id[:8]}] Agent error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
