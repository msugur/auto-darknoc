# Phase 04 — Automation

## Overview
**Goal:** AAP 2.5 (Automation Controller + EDA Controller) running, ACM 2.15 managing both clusters, edge workloads and GitOps integration deployed, and Ansible Lightspeed demo template path prepared.

**Duration:** 1 day
**Clusters:** Hub (all) + Edge (ManagedCluster enrollment)
**Depends on:** Phase 01 (AAP + ACM operators), Phase 02 (Kafka for EDA triggers)
**Unblocks:** Phase 05 (Agent needs AAP REST API + ACM for cluster management)

---

## Why This Phase Matters

- **AAP Automation Controller** → Executes Ansible playbooks for edge remediation. The LangGraph agent calls its REST API to trigger healing jobs.
- **EDA Controller** → Watches Kafka `remediation-jobs` topic and auto-triggers job templates for known patterns — the fast-path (no AI needed for simple cases).
- **Ansible Lightspeed Path** → Uses AAP template workflow to execute AI-assisted/generated playbook content in a governed way.
- **Edge EDA Pattern (optional)** → Lightweight rulebook runner on `edge-01` can execute local safe remediations and report outcomes to hub.
- **ACM MultiClusterHub** → Federates both clusters; enables GitOps pull-based config to edge; provides unified cluster view for dashboard.

---

## Components Deployed

```
Hub Cluster:
  aap                     ← AutomationController CR + EDAController CR
  open-cluster-management ← MultiClusterHub CR

Edge Cluster:
  edge-eda-runner         ← Optional local fast remediation runner
```

---

## Files in This Phase

```
phase-04-automation/
├── README.md
├── aap/
│   ├── automation-controller.yaml    ← AutomationController CR
│   ├── eda-controller.yaml           ← EDAController CR
│   ├── eda-rulebook.yaml             ← EDA Kafka rulebook for fast-path
│   ├── aap-platform.yaml             ← Enterprise AAP platform CR
│   └── lightspeed-demo-template.md   ← Lightspeed template setup/usage
├── edge-eda/
│   ├── README.md                     ← edge-01 EDA operating model
│   ├── edge-eda-rulebook.yaml        ← local safe remediation rules
│   └── edge-eda-runner-deployment.yaml ← lightweight ansible-rulebook runner
├── acm/
│   ├── multiclusterhub.yaml          ← ACM MultiClusterHub CR
│   └── managed-cluster.yaml          ← Edge cluster enrollment
└── playbooks/
    ├── restart-nginx.yaml            ← Ansible playbook: restart nginx pod
    └── restart-nginx-aap-api.yaml    ← AAP API-driven restart path
```

---

## Next Phase
Once AAP jobs and ACM GitOps are validated: **[Phase 05 — Agent & MCP](../phase-05-agent-mcp/README.md)**

## EDA Placement
- **Current deployment:** EDA controller on Hub (`aap` namespace).
- **Edge option:** deploy `edge-eda` runner for local fast-path during hub latency/outage windows.

## Lightspeed Placement
- **Current deployment model:** Lightspeed-assisted generation/execution is orchestrated via AAP template workflow and LangGraph in Phase 05.
- **Template reference:** `aap/lightspeed-demo-template.md`
