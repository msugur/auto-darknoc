# Phase 06 — Dashboard & UI

## Overview
**Goal:** React 19 NOC dashboard, Slack chatbot integration, and ServiceNow mock running. The dashboard provides the live visualization layer for the demo.

**Duration:** 1-2 days
**Clusters:** Hub only
**Depends on:** Phase 05 (agent publishes to Kafka agent-events topic)
**Unblocks:** Phase 08 (full end-to-end demo needs dashboard for visualization)

---

## Why This Phase Matters

The dashboard transforms the autonomous NOC from "black box AI" to a visible, explainable system:

- **Real-time incident feed** → Engineers see each incident as it happens
- **Agent trace visualization** → Each LangGraph node transition shown live
- **Langfuse integration** → Click any incident → see full AI trace + tokens + latency
- **ServiceNow mock** → Creates/tracks tickets visible in dashboard + Slack
- **Chatbot** → NOC engineers can ask: "What happened to nginx at 14:32?"

---

## Components Deployed

```
Hub Cluster:
  dark-noc-ui              ← React 19 Dashboard (Node.js BuildConfig)
  dark-noc-ui              ← Chatbot (FastAPI + LangGraph conversational mode)
  dark-noc-servicenow-mock ← ServiceNow REST API mock (FastAPI)
```

---

## Dashboard Features

### Main Views
1. **Incident Feed** — Live stream of all detected incidents + status
2. **Agent Workflow** — Animated LangGraph node execution graph
3. **Cluster Health** — Hub + Edge cluster status tiles
4. **Metrics** — Incidents resolved, MTTR, AI confidence scores
5. **Langfuse Link** — One-click to full trace for any incident

### Real-time Updates
- Kafka `agent-events` topic → Server-Sent Events (SSE) → React state
- No polling — pure event-driven using SSE WebSocket

---

## Files in This Phase

```
phase-06-dashboard/
├── README.md
├── servicenow-mock/
│   ├── main.py             ← FastAPI ServiceNow mock (4 endpoints)
│   ├── Dockerfile
│   └── deployment.yaml
├── dashboard/
│   ├── src/
│   │   ├── App.jsx          ← Main dashboard React app
│   │   ├── components/
│   │   │   ├── IncidentFeed.jsx
│   │   │   ├── AgentWorkflow.jsx
│   │   │   ├── ClusterHealth.jsx
│   │   │   └── MetricsPanel.jsx
│   │   └── index.jsx
│   ├── package.json
│   ├── Dockerfile
│   ├── buildconfig.yaml   ← ImageStream + binary BuildConfig
│   └── deployment.yaml
└── chatbot/
    ├── main.py             ← FastAPI chatbot backend
    ├── model-binding-configmap.yaml ← Shared model binding in dark-noc-ui
    └── deployment.yaml
```

---

## Next Phase
Once dashboard is accessible: **[Phase 07 — Edge Workloads](../phase-07-edge-workloads/README.md)**

---

## Dashboard Build/Rollout Quick Commands

```bash
oc apply -f implementation/phase-06-dashboard/dashboard/buildconfig.yaml -n dark-noc-ui
oc start-build dark-noc-dashboard \
  --from-dir=implementation/phase-06-dashboard/dashboard \
  --follow -n dark-noc-ui
oc apply -f implementation/phase-06-dashboard/dashboard/deployment.yaml -n dark-noc-ui
oc -n dark-noc-ui rollout status deploy/dark-noc-dashboard
```
