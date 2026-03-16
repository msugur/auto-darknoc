# Phase 05 — Agent & MCP Servers

## Overview
**Goal:** 6 FastMCP servers running and the LangGraph 1.0 Dark NOC Agent deployed — the brain of the autonomous NOC.

**Duration:** 2-3 days
**Clusters:** Hub only
**Depends on:** Phase 02 (Kafka), Phase 03 (vLLM + LlamaStack + pgvector), Phase 04 (AAP + ACM)
**Unblocks:** Phase 06 (Dashboard needs agent WebSocket events), Phase 07 (Edge needs to generate real incidents)

---

## Why This Phase Matters

This phase creates the **intelligence layer** — the autonomous decision-making core:

- **6 FastMCP Servers** → Wrap NOC tools as MCP (Model Context Protocol) endpoints so Granite can call them via tool use
- **LangGraph Agent** → Stateful AI workflow: consume logs → analyze → retrieve RAG context → call tools → remediate → report
- **Lightspeed Orchestration** → For Lightspeed-tagged scenarios, agent launches AAP Lightspeed template workflow, upserts generated-template entries, and keeps ITSM/comms in sync.

---

## Architecture

```
Edge nginx crash
    │
    ▼
Kafka nginx-logs topic
    │
    ▼
LangGraph Dark NOC Agent (LangGraph 1.0 + Granite 4.0 H-Tiny)
    │
    ├─→ [RAG Node] pgvector similarity search → runbook + product-doc context
    ├─→ [Analysis Node] Granite: structured JSON root cause analysis
    ├─→ [Tools Node] FastMCP tool calls:
    │       ├─ OpenShift API MCP → get pod status, events
    │       ├─ LokiStack MCP    → query historical logs
    │       ├─ Kafka MCP        → read/produce to topics
    │       ├─ AAP MCP          → trigger Ansible job
    │       ├─ Slack MCP        → send notification
    │       └─ ServiceNow MCP   → create/update ticket
    └─→ [Audit Node] → Langfuse trace + Kafka incident-audit
```

---

## MCP Server Summary

| Server | Port | Tools | Backend |
|--------|------|-------|---------|
| mcp-openshift | 8001 | get_pods, get_events, patch_deployment, rollout_restart | oc CLI |
| mcp-lokistack | 8002 | query_logs, get_recent_errors, count_errors | LokiStack LogQL API |
| mcp-kafka | 8003 | produce_message, consume_topic, get_lag | Kafka bootstrap |
| mcp-aap | 8004 | launch_job, get_job_status, list_job_templates | AAP REST API |
| mcp-slack | 8005 | send_message, send_alert, update_message | Slack Bot API |
| mcp-servicenow | 8006 | create_incident, update_incident, get_incident | ServiceNow mock |

---

## Lightspeed Flow (Deployment-Relevant)

1. Phase 04 must be complete (AAP controller, credentials, and Lightspeed template path).
2. Agent receives Lightspeed scenario event from Kafka (`dark_noc_scenario=lightspeed`).
3. Agent generates incident-scoped playbook payload and launches AAP template `lightspeed-generate-and-run`.
4. MCP AAP upserts/maintains generated template entry in AAP Job Templates.
5. Agent publishes remediation outcome, creates/updates ServiceNow, and sends Slack message.

Operational references:
- `../phase-04-automation/aap/lightspeed-demo-template.md`
- `agent/agent.py`
- `mcp-servers/mcp-aap/server.py`

---

## Files in This Phase

```
phase-05-agent-mcp/
├── README.md
├── mcp-servers/
│   ├── mcp-openshift/
│   │   ├── server.py          ← FastMCP server
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── mcp-lokistack/
│   │   ├── server.py
│   │   └── requirements.txt
│   ├── mcp-kafka/
│   │   ├── server.py
│   │   └── requirements.txt
│   ├── mcp-aap/
│   │   ├── server.py
│   │   └── requirements.txt
│   ├── mcp-slack/
│   │   ├── server.py
│   │   └── requirements.txt
│   ├── mcp-servicenow/
│   │   ├── server.py
│   │   └── requirements.txt
│   └── mcp-servers-deployment.yaml
└── agent/
    ├── agent.py               ← Main LangGraph agent
    ├── state.py               ← LangGraph state schema
    ├── buildconfig.yaml       ← ImageStream + binary BuildConfig
    ├── requirements.txt
    ├── Dockerfile
    └── deployment.yaml
```

---

## Next Phase
Once agent is running and receiving test incidents: **[Phase 06 — Dashboard](../phase-06-dashboard/README.md)**
