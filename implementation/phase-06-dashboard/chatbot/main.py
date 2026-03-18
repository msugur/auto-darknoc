"""
Dark NOC Chatbot Backend (Phase 06)
===================================
FastAPI backend for dashboard integration.
Provides:
  - health endpoint
  - summary endpoint for dashboard cards
  - interactive chat endpoint backed by model + MCP runtime state
"""

from __future__ import annotations

import json
import os
import statistics
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer, KafkaProducer
from pydantic import BaseModel


APP_VERSION = "0.1.0"
SERVICENOW_URL = os.getenv(
    "SERVICENOW_URL",
    "http://servicenow-mock.dark-noc-servicenow-mock.svc:8080",
)
SERVICENOW_API_KEY = os.getenv("SERVICENOW_API_KEY", "")
SERVICENOW_MODE = os.getenv("SERVICENOW_MODE", "mock").lower()  # mock|real
SERVICENOW_USERNAME = os.getenv("SERVICENOW_USERNAME", "")
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD", "")
SLACK_WORKSPACE_URL = os.getenv("SLACK_WORKSPACE_URL", "")
SERVICENOW_UI_URL = os.getenv("SERVICENOW_UI_URL", "")
OPENSHIFT_CONSOLE_URL = os.getenv("OPENSHIFT_CONSOLE_URL", "")
OPENSHIFT_EDGE_CONSOLE_URL = os.getenv("OPENSHIFT_EDGE_CONSOLE_URL", "")
AAP_UI_URL = os.getenv("AAP_UI_URL", "")
AAP_LIGHTSPEED_URL = os.getenv("AAP_LIGHTSPEED_URL", "")
GRAFANA_URL = os.getenv("GRAFANA_URL", "")
LANGFUSE_URL = os.getenv("LANGFUSE_URL", "")
KAFKA_UI_URL = os.getenv("KAFKA_UI_URL", "")
LOKI_UI_URL = os.getenv("LOKI_UI_URL", "")
OPENSHIFT_USERNAME = os.getenv("OPENSHIFT_USERNAME", "")
OPENSHIFT_PASSWORD = os.getenv("OPENSHIFT_PASSWORD", "")
OPENSHIFT_EDGE_USERNAME = os.getenv("OPENSHIFT_EDGE_USERNAME", "")
OPENSHIFT_EDGE_PASSWORD = os.getenv("OPENSHIFT_EDGE_PASSWORD", "")
AAP_UI_USERNAME = os.getenv("AAP_UI_USERNAME", "")
AAP_UI_PASSWORD = os.getenv("AAP_UI_PASSWORD", "")
KAFKA_UI_USERNAME = os.getenv("KAFKA_UI_USERNAME", "")
KAFKA_UI_PASSWORD = os.getenv("KAFKA_UI_PASSWORD", "")
SERVICENOW_UI_USERNAME = os.getenv("SERVICENOW_UI_USERNAME", "")
SERVICENOW_UI_PASSWORD = os.getenv("SERVICENOW_UI_PASSWORD", "")
GRAFANA_UI_USERNAME = os.getenv("GRAFANA_UI_USERNAME", "")
GRAFANA_UI_PASSWORD = os.getenv("GRAFANA_UI_PASSWORD", "")
LANGFUSE_UI_USERNAME = os.getenv("LANGFUSE_UI_USERNAME", "")
LANGFUSE_UI_PASSWORD = os.getenv("LANGFUSE_UI_PASSWORD", "")
SLACK_UI_USERNAME = os.getenv("SLACK_UI_USERNAME", "")
SLACK_UI_PASSWORD = os.getenv("SLACK_UI_PASSWORD", "")
MCP_OPENSHIFT_URL = os.getenv("MCP_OPENSHIFT_URL", "http://mcp-openshift.dark-noc-mcp.svc:8001")
MCP_LOKI_URL = os.getenv("MCP_LOKI_URL", "http://mcp-lokistack.dark-noc-mcp.svc:8002")
MCP_KAFKA_URL = os.getenv("MCP_KAFKA_URL", "http://mcp-kafka.dark-noc-mcp.svc:8003")
MCP_AAP_URL = os.getenv("MCP_AAP_URL", "http://mcp-aap.dark-noc-mcp.svc:8004")
MCP_SLACK_URL = os.getenv("MCP_SLACK_URL", "http://mcp-slack.dark-noc-mcp.svc:8005")
MCP_SERVICENOW_URL = os.getenv("MCP_SERVICENOW_URL", "http://mcp-servicenow.dark-noc-mcp.svc:8006")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "granite-4-h-tiny")
AGENT_FRAMEWORK = os.getenv("AGENT_FRAMEWORK", "LangGraph + MCP + LlamaStack")
MODEL_API_URL = os.getenv(
    "MODEL_API_URL",
    "http://granite-vllm-predictor.dark-noc-hub.svc:8080/v1/completions",
)
MODEL_TIMEOUT_SECONDS = float(os.getenv("MODEL_TIMEOUT_SECONDS", "20"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "280"))
DEMO_KAFKA_BOOTSTRAP = os.getenv(
    "DEMO_KAFKA_BOOTSTRAP",
    "dark-noc-kafka-kafka-bootstrap.dark-noc-kafka.svc:9092",
)
DEMO_TOPIC = os.getenv("DEMO_TOPIC", "nginx-logs")
SLO_AUDIT_TOPIC = os.getenv("SLO_AUDIT_TOPIC", "incident-audit")
SLO_LOOKBACK_HOURS = int(os.getenv("SLO_LOOKBACK_HOURS", "24"))
SLO_MAX_MESSAGES = int(os.getenv("SLO_MAX_MESSAGES", "500"))
INTEGRATIONS_CACHE_TTL_SECONDS = float(os.getenv("INTEGRATIONS_CACHE_TTL_SECONDS", "10"))

chat_sessions: dict[str, list[dict[str, str]]] = {}
EXEC_REPLY_MAX_CHARS = 1600
integrations_cache: dict[str, Any] = {"ts": 0.0, "payload": None}

app = FastAPI(
    title="Dark NOC Chatbot API",
    version=APP_VERSION,
    description="Dashboard helper API for Dark NOC",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class DemoTriggerRequest(BaseModel):
    scenario: str = "crashloop"
    site: str = "edge-01"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def is_real_servicenow() -> bool:
    return SERVICENOW_MODE == "real" or bool(SERVICENOW_USERNAME and SERVICENOW_PASSWORD)


def normalize_session_id(session_id: str | None) -> str:
    return session_id.strip() if session_id and session_id.strip() else str(uuid4())


def mcp_slice(integrations_payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = integrations_payload.get("integrations", [])
    return [item for item in items if item.get("group") == "mcp"]


def _clean_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.lower().startswith(("note:", "(note:", "i've revised", "let me know")):
            continue
        lines.append(line)
    return lines


def _extract_model_insight(raw_model_reply: str) -> str:
    lines = _clean_lines(raw_model_reply)
    if not lines:
        return "Model inference completed; no structured RCA text returned."
    first = lines[0].replace("**", "").replace("`", "")
    alnum_count = sum(ch.isalnum() for ch in first)
    if alnum_count < 8:
        return "Model inference completed; likely cause indicates a transient workload/resource condition."
    if len(first) > 220:
        first = first[:217].rstrip() + "..."
    return first


def format_executive_reply(
    user_message: str,
    raw_model_reply: str,
    summary_payload: dict[str, Any],
    integrations_payload: dict[str, Any],
) -> str:
    mcp_agents = mcp_slice(integrations_payload)
    mcp_lines = [
        f"- {agent.get('name')}: {agent.get('status')} (http={agent.get('http_code') or 'n/a'})"
        for agent in mcp_agents
    ]
    if not mcp_lines:
        mcp_lines = ["- No MCP status available."]

    down_agents = [agent.get("name") for agent in mcp_agents if agent.get("status") != "up"]
    if down_agents:
        action_1 = f"Recover unhealthy MCP agents first: {', '.join(down_agents)}."
    else:
        action_1 = "All MCP agents are healthy; proceed with remediation workflow execution."

    site = summary_payload.get("site") or "edge-01"
    cluster = summary_payload.get("cluster") or "hub"
    incidents = summary_payload.get("open_incidents") or 0
    up = integrations_payload.get("up") or 0
    total = integrations_payload.get("total") or 0
    model_insight = _extract_model_insight(raw_model_reply)

    reply = (
        "Summary:\n"
        f"- Site: {site} | Cluster: {cluster}\n"
        f"- Open incidents: {incidents}\n"
        f"- Integrations: {up}/{total} up\n"
        f"- Request: {user_message}\n\n"
        "MCP Status:\n"
        + "\n".join(mcp_lines)
        + "\n\n"
        "Model Output:\n"
        f"- {model_insight}\n\n"
        "Next Action:\n"
        f"1. {action_1}\n"
        "2. If remediation is executed, confirm ServiceNow ticket update and Slack notification.\n"
        "3. Validate edge-01 workload recovery and Kafka/Loki telemetry continuity."
    )
    if len(reply) > EXEC_REPLY_MAX_CHARS:
        return reply[: EXEC_REPLY_MAX_CHARS - 3].rstrip() + "..."
    return reply


def build_context_message(
    user_message: str,
    summary_payload: dict[str, Any],
    integrations_payload: dict[str, Any],
    history: list[dict[str, str]],
) -> str:
    mcp_agents = mcp_slice(integrations_payload)
    mcp_line = ", ".join(
        [f"{agent.get('name')}={agent.get('status')}" for agent in mcp_agents]
    ) or "no-mcp-data"
    workflow_steps = integrations_payload.get("eda_usage", {}).get("workflow", [])
    recent = history[-4:]
    convo = "\n".join([f"{item['role']}: {item['content']}" for item in recent]) or "none"
    return (
        "You are the Dark NOC assistant for executive operations display.\n"
        "Return concise, deterministic text only (no markdown tables, no disclaimers, no self-references).\n"
        "Use exactly these headers: Summary, MCP Status, Model Output, Next Action.\n"
        "Keep output under 140 words.\n"
        f"Agent framework: {AGENT_FRAMEWORK}\n"
        f"Model name: {AI_MODEL_NAME}\n"
        f"Site: {summary_payload.get('site')} | Cluster: {summary_payload.get('cluster')}\n"
        f"Open incidents: {summary_payload.get('open_incidents')}\n"
        f"Integrations up/total: {integrations_payload.get('up')}/{integrations_payload.get('total')}\n"
        f"MCP status snapshot: {mcp_line}\n"
        f"EDA workflow: {' | '.join(workflow_steps)}\n"
        f"Recent conversation: {convo}\n"
        f"User request: {user_message}"
    )


async def call_live_model(prompt: str) -> tuple[str, str]:
    """Call the model endpoint. Returns (reply, source)."""
    if not MODEL_API_URL:
        return "", "disabled"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": AI_MODEL_NAME,
        "prompt": prompt,
        "max_tokens": MODEL_MAX_TOKENS,
        "temperature": 0.2,
    }
    try:
        async with httpx.AsyncClient(timeout=MODEL_TIMEOUT_SECONDS, verify=False) as client:
            resp = await client.post(
                MODEL_API_URL,
                headers={**headers, "X-Model": AI_MODEL_NAME},
                json=payload,
            )
        if resp.status_code != 200:
            return "", f"http-{resp.status_code}"
        data = resp.json()
        choices = data.get("choices", [])
        if choices:
            first = choices[0]
            text = (first.get("text") or first.get("message", {}).get("content") or "").strip()
            if text:
                return text, "live"
        return "", "empty"
    except Exception:
        return "", "unreachable"


def fallback_response(
    user_message: str,
    summary_payload: dict[str, Any],
    integrations_payload: dict[str, Any],
) -> str:
    mcp_agents = mcp_slice(integrations_payload)
    mcp_lines = []
    for agent in mcp_agents:
        mcp_lines.append(
            f"- {agent.get('name')}: {agent.get('status')} (http={agent.get('http_code') or 'n/a'})"
        )
    mcp_text = "\n".join(mcp_lines) if mcp_lines else "- no MCP status available"
    return (
        "Summary:\n"
        f"- Site: {summary_payload.get('site')} | Cluster: {summary_payload.get('cluster')}\n"
        f"- Open incidents: {summary_payload.get('open_incidents')}\n"
        f"- Integrations: {integrations_payload.get('up')}/{integrations_payload.get('total')} up\n"
        f"- Request: {user_message}\n\n"
        "MCP Status:\n"
        f"{mcp_text}\n\n"
        "Model Output:\n"
        "- Live model unavailable; using deterministic operational fallback.\n\n"
        "Next Action:\n"
        "1. Restore model endpoint connectivity if required.\n"
        "2. Continue remediation via MCP tools and verify ServiceNow + Slack updates."
    )


async def probe_http(url: str, timeout: float = 4.0) -> dict[str, Any]:
    """
    Lightweight service probe.
    200/401/403/404/405 are treated as reachable (service up, route exists).
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            resp = await client.get(url)
            status_code = resp.status_code
            reachable = status_code in {200, 401, 403, 404, 405}
            return {
                "status": "up" if reachable else f"http-{status_code}",
                "http_code": status_code,
                "reachable": reachable,
            }
    except Exception:
        return {"status": "down", "http_code": None, "reachable": False}


async def fetch_servicenow_incident_count() -> tuple[int, str]:
    """Fetch incident count from real or mock ServiceNow target."""
    try:
        async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
            if is_real_servicenow():
                resp = await client.get(
                    f"{SERVICENOW_URL}/api/now/table/incident?sysparm_limit=100&sysparm_fields=number",
                    auth=(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
                )
                if resp.status_code == 200:
                    return len(resp.json().get("result", [])), "up"
                return 0, f"http-{resp.status_code}"

            resp = await client.get(
                f"{SERVICENOW_URL}/api/now/table/incident",
                headers={"X-API-Key": SERVICENOW_API_KEY},
            )
            if resp.status_code == 200:
                data = resp.json()
                return int(data.get("count", 0)), "up"
            return 0, f"http-{resp.status_code}"
    except Exception:
        return 0, "down"


def fetch_recent_incident_audits() -> list[dict[str, Any]]:
    """
    Read recent incident-audit records directly from Kafka.
    Uses end-offset seek to avoid scanning full topic.
    """
    consumer = KafkaConsumer(
        SLO_AUDIT_TOPIC,
        bootstrap_servers=DEMO_KAFKA_BOOTSTRAP,
        auto_offset_reset="latest",
        enable_auto_commit=False,
        consumer_timeout_ms=2500,
        value_deserializer=lambda m: m.decode("utf-8", errors="replace"),
    )
    records: list[dict[str, Any]] = []
    try:
        consumer.poll(timeout_ms=800)
        partitions = consumer.assignment()
        if not partitions:
            return records

        max_per_partition = max(50, int(SLO_MAX_MESSAGES / max(1, len(partitions))))
        for tp in partitions:
            end_offset = consumer.end_offsets([tp])[tp]
            start_offset = max(0, end_offset - max_per_partition)
            consumer.seek(tp, start_offset)

        cutoff = datetime.now(timezone.utc).timestamp() - (SLO_LOOKBACK_HOURS * 3600)
        for msg in consumer:
            raw = msg.value
            try:
                data = json.loads(raw)
            except Exception:
                continue

            ts = parse_iso8601(str(data.get("timestamp", "")))
            if ts and ts.timestamp() >= cutoff:
                records.append(data)
            elif not ts:
                # Keep malformed timestamp records to avoid dropping live metrics completely.
                records.append(data)

            if len(records) >= SLO_MAX_MESSAGES:
                break
    finally:
        consumer.close()
    return records


def compute_slo_metrics(records: list[dict[str, Any]], integrations_up: int, integrations_total: int) -> dict[str, Any]:
    total = len(records)
    if total == 0:
        return {
            "window_hours": SLO_LOOKBACK_HOURS,
            "sample_size": 0,
            "mttd_seconds": None,
            "mttd_estimated": True,
            "mttr_seconds": None,
            "p95_recovery_seconds": None,
            "edge_remediation_pct": None,
            "auto_remediation_pct": None,
            "escalation_pct": None,
            "aap_success_pct": None,
            "ai_confidence_avg": None,
            "incidents_per_hour": 0.0,
            "platform_availability_pct": round((integrations_up / integrations_total) * 100, 2) if integrations_total else 0.0,
        }

    durations = []
    durations_for_p95 = []
    auto_remediated = 0
    edge_remediated = 0
    escalated = 0
    aap_total = 0
    aap_success = 0
    confidence_vals = []
    mttd_samples = []
    mttd_estimated = False

    for rec in records:
        remediation_success = bool(rec.get("remediation_success", False))
        remediation_action = str(rec.get("remediation_action", "") or "")
        servicenow_ticket = str(rec.get("servicenow_ticket", "") or "")
        aap_job_id = str(rec.get("aap_job_id", "") or "")
        edge_site = str(rec.get("edge_site_id", "") or "")

        dur_ms = float(rec.get("total_duration_ms", 0) or 0)
        if dur_ms > 0:
            dur_sec = dur_ms / 1000.0
            durations.append(dur_sec)
            durations_for_p95.append(dur_sec)

            # MTTD is not emitted directly today; estimate from first segment of full lifecycle.
            mttd_samples.append(max(1.0, dur_sec * 0.2))
            mttd_estimated = True

        confidence = float(rec.get("ai_confidence", 0) or 0)
        if confidence > 0:
            confidence_vals.append(confidence)

        if remediation_success and not servicenow_ticket:
            auto_remediated += 1
        if remediation_success and edge_site:
            edge_remediated += 1
        if servicenow_ticket or "escalat" in remediation_action.lower():
            escalated += 1
        if aap_job_id:
            aap_total += 1
            if remediation_success:
                aap_success += 1

    mttr = statistics.mean(durations) if durations else None
    mttd = statistics.mean(mttd_samples) if mttd_samples else None
    p95 = statistics.quantiles(durations_for_p95, n=20)[18] if len(durations_for_p95) >= 20 else (max(durations_for_p95) if durations_for_p95 else None)

    return {
        "window_hours": SLO_LOOKBACK_HOURS,
        "sample_size": total,
        "mttd_seconds": round(mttd, 2) if mttd is not None else None,
        "mttd_estimated": mttd_estimated,
        "mttr_seconds": round(mttr, 2) if mttr is not None else None,
        "p95_recovery_seconds": round(p95, 2) if p95 is not None else None,
        "edge_remediation_pct": round((edge_remediated / total) * 100, 2),
        "auto_remediation_pct": round((auto_remediated / total) * 100, 2),
        "escalation_pct": round((escalated / total) * 100, 2),
        "aap_success_pct": round((aap_success / aap_total) * 100, 2) if aap_total else None,
        "ai_confidence_avg": round(statistics.mean(confidence_vals), 3) if confidence_vals else None,
        "incidents_per_hour": round(total / max(1, SLO_LOOKBACK_HOURS), 2),
        "platform_availability_pct": round((integrations_up / integrations_total) * 100, 2) if integrations_total else 0.0,
    }


def build_incident_movie_and_impact(records: list[dict[str, Any]], slo_metrics: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(
        records,
        key=lambda rec: parse_iso8601(str(rec.get("timestamp", ""))) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    movie: list[dict[str, Any]] = []
    auto_resolved = 0
    escalated = 0
    success_count = 0
    confidence_vals: list[float] = []

    for rec in ordered[:8]:
        ts_raw = str(rec.get("timestamp", "") or "")
        ts = parse_iso8601(ts_raw)
        incident_id = str(rec.get("incident_id", "n/a") or "n/a")
        failure_type = str(rec.get("failure_type", "unknown") or "unknown")
        severity = str(rec.get("severity", "unknown") or "unknown").upper()
        action = str(rec.get("remediation_action", "n/a") or "n/a")
        success = bool(rec.get("remediation_success", False))
        servicenow_ticket = str(rec.get("servicenow_ticket", "") or "")
        aap_job_id = str(rec.get("aap_job_id", "") or "")
        edge_site = str(rec.get("edge_site_id", "edge-01") or "edge-01")

        if success:
            success_count += 1
        if success and not servicenow_ticket:
            auto_resolved += 1
        if servicenow_ticket:
            escalated += 1

        confidence = float(rec.get("ai_confidence", 0) or 0)
        if confidence > 0:
            confidence_vals.append(confidence)

        stage = "Escalated"
        if success and not servicenow_ticket:
            stage = "Auto-Remediated"
        elif success:
            stage = "Remediated"

        badges = [f"severity:{severity}", f"site:{edge_site}", f"failure:{failure_type}"]
        if aap_job_id:
            badges.append("aap")
        if servicenow_ticket:
            badges.append("servicenow")

        movie.append(
            {
                "timestamp": ts.isoformat() if ts else ts_raw,
                "incident_id": incident_id,
                "title": f"{failure_type} on {edge_site}",
                "stage": stage,
                "summary": f"Action: {action} · Result: {'success' if success else 'failed'}",
                "artifacts": {
                    "aap_job_id": aap_job_id or None,
                    "servicenow_ticket": servicenow_ticket or None,
                    "langfuse_trace_id": str(rec.get('langfuse_trace_id', '') or '') or None,
                },
                "badges": badges,
            }
        )

    total = len(records)
    mttr = float(slo_metrics.get("mttr_seconds") or 0)
    baseline_manual_mttr = 900.0
    per_incident_saved = max(0.0, baseline_manual_mttr - mttr)
    total_seconds_saved = per_incident_saved * auto_resolved
    hours_returned = total_seconds_saved / 3600.0

    impact = {
        "incidents_processed": total,
        "remediation_success_pct": round((success_count / total) * 100, 2) if total else 0.0,
        "tickets_avoided": auto_resolved,
        "escalated_tickets": escalated,
        "hours_returned_to_ops": round(hours_returned, 2),
        "estimated_cost_saved_usd": round(hours_returned * 120.0, 2),
        "model_confidence_avg": round(statistics.mean(confidence_vals), 3) if confidence_vals else None,
        "baseline_manual_mttr_seconds": baseline_manual_mttr,
    }
    return movie, impact


def build_demo_event(scenario: str, site: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    normalized = scenario.strip().lower()
    if normalized == "oom":
        message = "OOMKilled: UI demo trigger on edge-01"
        pod_name = "nginx-demo-oom"
    elif normalized == "lightspeed":
        message = "Ansible playbook generation requested for edge recovery (Lightspeed demo trigger)"
        pod_name = "nginx-demo-lightspeed"
    elif normalized == "escalation":
        message = "Kernel panic and persistent data corruption in edge control process - requires human escalation"
        pod_name = "edge-core-critical-demo"
    else:
        normalized = "crashloop"
        message = "CrashLoopBackOff: nginx configuration test failed from UI demo trigger"
        pod_name = "nginx-demo-crashloop"

    return {
        "@timestamp": now,
        "message": message,
        "level": "error",
        "kubernetes": {
            "namespace_name": "dark-noc-edge",
            "pod_name": pod_name,
            "container_name": "nginx",
        },
        "labels": {
            "edge_site_id": site,
            "dark_noc_demo": "true",
            "dark_noc_scenario": normalized,
        },
    }


def publish_demo_event(event: dict[str, Any]) -> int:
    producer = KafkaProducer(
        bootstrap_servers=DEMO_KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    future = producer.send(DEMO_TOPIC, value=event)
    metadata = future.get(timeout=10)
    producer.flush(timeout=10)
    producer.close(timeout=10)
    return int(metadata.offset)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "dark-noc-chatbot", "version": APP_VERSION}


@app.get("/api/summary")
async def summary() -> dict:
    tickets, servicenow_state = await fetch_servicenow_incident_count()

    return {
        "timestamp": utc_now(),
        "agent_status": "running",
        "cluster": "hub",
        "site": "edge-01",
        "open_incidents": tickets,
        "servicenow": servicenow_state,
    }


async def _build_integrations_payload() -> dict[str, Any]:
    snow_probe = (
        f"{SERVICENOW_URL}/api/now/table/incident?sysparm_limit=1"
        if is_real_servicenow()
        else f"{SERVICENOW_URL}/health"
    )
    targets = [
        {
            "id": "mcp-openshift",
            "name": "MCP OpenShift",
            "group": "mcp",
            "probe_url": f"{MCP_OPENSHIFT_URL}/",
            "ui_url": OPENSHIFT_CONSOLE_URL,
        },
        {
            "id": "mcp-aap",
            "name": "MCP AAP",
            "group": "mcp",
            "probe_url": f"{MCP_AAP_URL}/",
            "ui_url": AAP_UI_URL,
        },
        {
            "id": "mcp-kafka",
            "name": "MCP Kafka",
            "group": "mcp",
            "probe_url": f"{MCP_KAFKA_URL}/",
            "ui_url": KAFKA_UI_URL,
        },
        {
            "id": "mcp-lokistack",
            "name": "MCP LokiStack",
            "group": "mcp",
            "probe_url": f"{MCP_LOKI_URL}/",
            "ui_url": LOKI_UI_URL,
        },
        {
            "id": "mcp-slack",
            "name": "MCP Slack",
            "group": "mcp",
            "probe_url": f"{MCP_SLACK_URL}/",
            "ui_url": SLACK_WORKSPACE_URL,
        },
        {
            "id": "mcp-servicenow",
            "name": "MCP ServiceNow",
            "group": "mcp",
            "probe_url": f"{MCP_SERVICENOW_URL}/",
            "ui_url": SERVICENOW_UI_URL,
        },
        {
            "id": "servicenow",
            "name": "ServiceNow",
            "group": "platform",
            "probe_url": snow_probe,
            "ui_url": SERVICENOW_UI_URL,
        },
        {
            "id": "slack",
            "name": "Slack",
            "group": "platform",
            "probe_url": "https://slack.com/api/api.test",
            "ui_url": SLACK_WORKSPACE_URL,
        },
        {
            "id": "openshift",
            "name": "OpenShift Hub",
            "group": "platform",
            "probe_url": OPENSHIFT_CONSOLE_URL,
            "ui_url": OPENSHIFT_CONSOLE_URL,
        },
        {
            "id": "openshift-edge",
            "name": "OpenShift Edge",
            "group": "platform",
            "probe_url": OPENSHIFT_EDGE_CONSOLE_URL,
            "ui_url": OPENSHIFT_EDGE_CONSOLE_URL,
        },
        {
            "id": "aap",
            "name": "AAP Controller",
            "group": "platform",
            "probe_url": f"{AAP_UI_URL}/api/controller/v2/ping/",
            "ui_url": AAP_UI_URL,
        },
        {
            "id": "grafana",
            "name": "Grafana",
            "group": "platform",
            "probe_url": f"{GRAFANA_URL}/api/health",
            "ui_url": GRAFANA_URL,
        },
        {
            "id": "langfuse",
            "name": "Langfuse",
            "group": "platform",
            "probe_url": f"{LANGFUSE_URL}/api/public/health",
            "ui_url": LANGFUSE_URL,
        },
        {
            "id": "kafka",
            "name": "Kafka",
            "group": "platform",
            "probe_url": f"{MCP_KAFKA_URL}/",
            "ui_url": KAFKA_UI_URL,
        },
        {
            "id": "lokistack",
            "name": "LokiStack",
            "group": "platform",
            "probe_url": f"{MCP_LOKI_URL}/",
            "ui_url": LOKI_UI_URL,
        },
    ]

    integrations: list[dict[str, Any]] = []
    up_count = 0
    for target in targets:
        if target["id"] == "servicenow" and is_real_servicenow():
            try:
                async with httpx.AsyncClient(timeout=6.0, verify=False) as client:
                    resp = await client.get(target["probe_url"], auth=(SERVICENOW_USERNAME, SERVICENOW_PASSWORD))
                probe = {
                    "status": "up" if resp.status_code == 200 else f"http-{resp.status_code}",
                    "http_code": resp.status_code,
                    "reachable": resp.status_code == 200,
                }
            except Exception:
                probe = {"status": "down", "http_code": None, "reachable": False}
        else:
            probe = await probe_http(target["probe_url"])
        if probe["status"] == "up":
            up_count += 1
        integrations.append(
            {
                "id": target["id"],
                "name": target["name"],
                "group": target["group"],
                "status": probe["status"],
                "http_code": probe["http_code"],
                "ui_url": target["ui_url"],
            }
        )

    audits = fetch_recent_incident_audits()
    slo_metrics = compute_slo_metrics(audits, up_count, len(integrations))
    incident_movie, business_impact = build_incident_movie_and_impact(audits, slo_metrics)

    return {
        "timestamp": utc_now(),
        "total": len(integrations),
        "up": up_count,
        "down": len(integrations) - up_count,
        "slo": slo_metrics,
        "incident_movie": incident_movie,
        "business_impact": business_impact,
        "integrations": integrations,
        "access": [
            {
                "name": "ServiceNow Incident Portal",
                "url": SERVICENOW_UI_URL,
                "username": SERVICENOW_UI_USERNAME,
                "password": SERVICENOW_UI_PASSWORD,
            },
            {
                "name": "AAP Controller UI",
                "url": AAP_UI_URL,
                "username": AAP_UI_USERNAME,
                "password": AAP_UI_PASSWORD,
            },
            {
                "name": "AAP Lightspeed UI",
                "url": AAP_LIGHTSPEED_URL,
                "username": AAP_UI_USERNAME,
                "password": AAP_UI_PASSWORD,
            },
            {
                "name": "Grafana",
                "url": GRAFANA_URL,
                "username": GRAFANA_UI_USERNAME,
                "password": GRAFANA_UI_PASSWORD,
            },
            {
                "name": "Langfuse",
                "url": LANGFUSE_URL,
                "username": LANGFUSE_UI_USERNAME,
                "password": LANGFUSE_UI_PASSWORD,
            },
            {
                "name": "OpenShift Hub Console",
                "url": OPENSHIFT_CONSOLE_URL,
                "username": OPENSHIFT_USERNAME,
                "password": OPENSHIFT_PASSWORD,
            },
            {
                "name": "OpenShift Edge Console",
                "url": OPENSHIFT_EDGE_CONSOLE_URL,
                "username": OPENSHIFT_EDGE_USERNAME,
                "password": OPENSHIFT_EDGE_PASSWORD,
            },
            {
                "name": "Kafka Console",
                "url": KAFKA_UI_URL,
                "username": KAFKA_UI_USERNAME,
                "password": KAFKA_UI_PASSWORD,
            },
            {
                "name": "Slack Workspace",
                "url": SLACK_WORKSPACE_URL,
                "username": SLACK_UI_USERNAME,
                "password": SLACK_UI_PASSWORD,
            },
        ],
        "eda_usage": {
            "where": "Hub AAP EDA + Edge local EDA runner (`edge-01`)",
            "how": "Edge runner executes immediate safe remediations (restart/reset), then logs flow to hub Kafka where AAP EDA and LangGraph continue global workflows.",
            "workflow": [
                "Failure detected on edge-01 workload (OOM/Crash/health).",
                "edge EDA-runner executes local safe remediation immediately.",
                "Edge CLF forwards workload and remediation logs to hub Kafka.",
                "Hub AAP EDA evaluates pattern rules for known failure classes.",
                f"Agentic loop ({AGENT_FRAMEWORK}) enriches context and RCA using {AI_MODEL_NAME}.",
                "MCP tools orchestrate actions across OpenShift, AAP, Loki, Kafka.",
                "ServiceNow incident is created/updated and caller policy is applied.",
                "Slack notification is sent with ticket + remediation details.",
            ],
        },
    }


async def get_integrations_payload(force_refresh: bool = False) -> dict[str, Any]:
    now = time.time()
    cached_payload = integrations_cache.get("payload")
    cached_ts = float(integrations_cache.get("ts", 0.0) or 0.0)
    if (
        not force_refresh
        and cached_payload is not None
        and (now - cached_ts) <= INTEGRATIONS_CACHE_TTL_SECONDS
    ):
        return cached_payload

    payload = await _build_integrations_payload()
    integrations_cache["payload"] = payload
    integrations_cache["ts"] = now
    return payload


@app.get("/api/integrations")
async def integrations(force_refresh: bool = False) -> dict:
    return await get_integrations_payload(force_refresh=force_refresh)


@app.post("/api/demo/trigger")
async def trigger_demo(req: DemoTriggerRequest) -> dict:
    event = build_demo_event(req.scenario, req.site)
    offset = publish_demo_event(event)
    scenario = event["labels"]["dark_noc_scenario"]
    next_steps = [
        "Watch AAP Jobs for restart-nginx execution (for crashloop/oom).",
        "Watch ServiceNow incident list for escalation scenario.",
        "Watch Slack #demos for incident/remediation notifications.",
        "Watch Langfuse traces for darknoc project updates.",
    ]
    if scenario == "lightspeed":
        next_steps = [
            "Watch AAP Jobs for template lightspeed-generate-and-run.",
            "Verify generated template entry appears in AAP Job Templates.",
            "Watch ServiceNow for the Lightspeed governance incident.",
            "Watch Slack #demos for Lightspeed job + ticket summary.",
        ]
    return {
        "timestamp": utc_now(),
        "status": "queued",
        "scenario": scenario,
        "site": req.site,
        "topic": DEMO_TOPIC,
        "kafka_offset": offset,
        "event_message": event["message"],
        "next_steps": next_steps,
        "links": {
            "dashboard": os.getenv("DASHBOARD_URL", ""),
            "aap_jobs": f"{AAP_UI_URL}/#/jobs",
            "servicenow_incidents": SERVICENOW_UI_URL,
            "slack": SLACK_WORKSPACE_URL,
            "langfuse": LANGFUSE_URL,
        },
    }


@app.post("/api/chat")
async def chat(req: ChatRequest) -> dict:
    msg = req.message.strip()
    if not msg:
        return {"reply": "Please enter a question.", "session_id": normalize_session_id(req.session_id)}

    session_id = normalize_session_id(req.session_id)
    history = chat_sessions.setdefault(session_id, [])
    summary_payload = await summary()
    integrations_payload = await get_integrations_payload(force_refresh=False)

    model_prompt = build_context_message(msg, summary_payload, integrations_payload, history)
    raw_model_reply, model_source = await call_live_model(model_prompt)
    if not raw_model_reply:
        model_reply = fallback_response(msg, summary_payload, integrations_payload)
    else:
        model_reply = format_executive_reply(msg, raw_model_reply, summary_payload, integrations_payload)

    history.append({"role": "user", "content": msg})
    history.append({"role": "assistant", "content": model_reply})
    if len(history) > 20:
        del history[:-20]

    return {
        "timestamp": utc_now(),
        "session_id": session_id,
        "reply": model_reply,
        "model_name": AI_MODEL_NAME,
        "model_source": model_source,
        "agent_framework": AGENT_FRAMEWORK,
        "open_incidents": summary_payload.get("open_incidents"),
        "site": summary_payload.get("site"),
        "integrations_up": integrations_payload.get("up"),
        "integrations_total": integrations_payload.get("total"),
        "mcp_status": mcp_slice(integrations_payload),
        "workflow": integrations_payload.get("eda_usage", {}).get("workflow", []),
    }
