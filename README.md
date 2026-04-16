# 🔴 Autonomous Dark NOC — Telco Edge AI Solution

> AI-Driven Self-Healing Telco Edge Operations powered by Red Hat OpenShift AI

[![OpenShift](https://img.shields.io/badge/OpenShift-4.21-red)](https://www.redhat.com/en/technologies/cloud-computing/openshift)
[![RHOAI](https://img.shields.io/badge/OpenShift%20AI-3.3-red)](https://www.redhat.com/en/technologies/cloud-computing/openshift/openshift-ai)
[![Kafka](https://img.shields.io/badge/Streams%20for%20Kafka-3.1-orange)](https://www.redhat.com/en/resources/amq-streams-datasheet)
[![AAP](https://img.shields.io/badge/AAP-2.5-red)](https://www.redhat.com/en/technologies/management/ansible)
[![ACM](https://img.shields.io/badge/ACM-2.15-red)](https://www.redhat.com/en/technologies/management/advanced-cluster-management)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0-blue)](https://langchain-ai.github.io/langgraph/)
[![Granite](https://img.shields.io/badge/Granite-4.0-purple)](https://www.ibm.com/granite)
[![Langfuse](https://img.shields.io/badge/Langfuse-3.x-green)](https://langfuse.com)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Validated Redeploy](#validated-redeploy)
- [Project Structure](#project-structure)
- [Implementation Phases](#implementation-phases)
- [Red Hat Products Used](#red-hat-products-used)
- [Command Log](#command-log)
- [Contributing](#contributing)

---

## Overview

The **Autonomous Dark NOC** is a fully AI-driven network operations solution for Telco edge environments. It autonomously detects failures at distributed edge sites, performs deep log analysis using IBM Granite 4.0 AI models, generates and executes Ansible remediation playbooks — all without human intervention. When AI cannot resolve an issue, it automatically creates ServiceNow tickets and notifies teams via Slack.

### Key Capabilities
| Capability | Technology | Result |
|-----------|-----------|--------|
| Real-time log streaming | Red Hat Streams for Kafka 3.1 | < 1s edge → hub |
| AI log analysis | IBM Granite 4.0 + RHOAI 3.3 | < 5s root cause analysis |
| RAG-grounded decisions | Llama Stack + pgvector | Runbook-based remediation |
| Automated remediation | AAP 2.5 + EDA | < 30s MTTR for routine faults |
| Multi-cluster management | ACM 2.15 | Hub controls edge fleet |
| Full observability | Langfuse 3.x | Every AI decision traced |
| Human-in-the-loop | LangGraph 1.0 | Approval gate for P1 incidents |
| Conversational NOC | Chatbot + LangGraph | Natural language cluster ops |
| AI-assisted playbook generation | Ansible Lightspeed + AAP template workflow | Generated remediation playbooks with governed execution |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  HUB SNO CLUSTER (OCP 4.21)  —  AWS us-east-1                  │
│  m5.4xlarge + g5.2xlarge (GPU: 1× NVIDIA A10G)                 │
│                                                                  │
│  RHOAI 3.3 · LlamaStack 0.3.5 · vLLM 0.15.1 · Granite 4.0    │
│  Kafka 3.1 · AAP 2.5 + EDA · ACM 2.15 Hub                     │
│  Langfuse 3.x · pgvector · MinIO · FastMCP 3.0.2               │
│  LangGraph 1.0 Agent · React Dashboard · Chatbot UI             │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Kafka TLS + ACM + AAP API
┌──────────────────────────▼──────────────────────────────────────┐
│  EDGE SNO CLUSTER (OCP 4.21)  —  AWS us-east-1                 │
│  m5.2xlarge                                                     │
│                                                                  │
│  nginx (monitored workload) · Log Generator                     │
│  OpenShift Logging 6.4 (Vector → Hub Kafka)                    │
│  ACM Spoke · Argo CD Pull Agent · AAP Execution Environment     │
└─────────────────────────────────────────────────────────────────┘
```

**Full architecture documentation:** [`docs/architecture/`](docs/architecture/)

---

## Prerequisites

### Minimal Inputs
- Hub API URL + credentials (`token` or `username/password`)
- Edge API URL + credentials (`token` or `username/password`)

Everything else is auto-generated/defaulted during deploy.

### Tool Required
```bash
oc
```

---

## Quick Start (Single Click)

```bash
git clone https://github.com/<your-org>/dark-noc.git
cd dark-noc

cp configs/hub/env.sh.example configs/hub/env.sh
# optional: cp configs/edge/env.sh.example configs/edge/env.sh
# fill hub+edge API/auth values

source configs/hub/env.sh
# optional: source configs/edge/env.sh

./scripts/one-click-gitops.sh --create-quay-pull
# for first-time cluster/domain values with Argo source in GitHub main:
# ./scripts/one-click-gitops.sh --commit-runtime-config --create-quay-pull
oc -n openshift-gitops get applications.argoproj.io
```

Authoritative one-click guide:
- [`gitops/prod/docs/ONE_CLICK_DEPLOY.md`](gitops/prod/docs/ONE_CLICK_DEPLOY.md)

## Deployment Order (Advanced/Manual)

Use this only if you are debugging or doing staged/manual deploy:

1. Phase 01 Foundation
2. Phase 02 Data Pipeline
3. Phase 03 AI Core
4. Phase 04 Automation (AAP/EDA/ACM + Lightspeed template path)
5. Phase 05 Agent & MCP (LangGraph + MCP + Lightspeed orchestration)
6. Phase 06 Dashboard/UI
7. Phase 07 Edge Workloads
8. Phase 08 Validation/E2E

For execution details and command-level order, use:
- [`docs/deployment/START-HERE.md`](docs/deployment/START-HERE.md)
- [`docs/deployment/redeploy-runbook.md`](docs/deployment/redeploy-runbook.md)

---

## Validated Redeploy

Use the validated redeploy sequence captured from live execution:

- [`docs/deployment/START-HERE.md`](docs/deployment/START-HERE.md)
- [`deploy/ORDERED-DEPLOYMENT.md`](deploy/ORDERED-DEPLOYMENT.md)
- [`deploy/manifest-order.tsv`](deploy/manifest-order.tsv)
- [`docs/reference/PRODUCT-VERSION-MATRIX.md`](docs/reference/PRODUCT-VERSION-MATRIX.md)
- [`docs/reference/MODEL-PROFILES.md`](docs/reference/MODEL-PROFILES.md)
- [`docs/deployment/redeploy-runbook.md`](docs/deployment/redeploy-runbook.md)
- [`logs/PROGRESS-TRACKER.md`](logs/PROGRESS-TRACKER.md)
- [`logs/COMMANDS-LOG.md`](logs/COMMANDS-LOG.md)

### Automated Ordered Flow

```bash
source configs/hub/env.sh
./scripts/preflight.sh
./scripts/deploy-dry-run.sh
./scripts/deploy-apply.sh
./scripts/deploy-validate.sh all
```

---

## Project Structure

```
dark-noc/
├── README.md                          # This file
├── .gitignore                         # Git ignore (secrets, temp files)
│
├── docs/                              # Documentation
│   ├── architecture/                  # Architecture diagrams & details
│   ├── reference/                     # Version matrices and reference docs
│   └── presentation/                  # Executive presentation content
│
├── configs/                           # Environment configuration
│   ├── hub/                           # Hub cluster environment variables
│   │   ├── env.sh.example             # Template (copy + fill in)
│   │   └── env.sh                     # Your actual config (gitignored)
│   └── edge/                          # Edge cluster environment variables
│       ├── env.sh.example
│       └── env.sh
│
├── scripts/                           # Utility scripts
│   ├── preflight.sh                   # Pre-flight cluster checks
│   ├── one-click-gitops.sh            # End-to-end GitOps bootstrap
│   ├── render-prod-secrets.sh         # Render runtime .real.yaml from templates
│   └── teardown.sh                    # Full cleanup / uninstall
│
├── logs/                              # Execution logs
│   ├── COMMANDS-LOG.md                # ✅ Every successful command logged here
│   ├── PROGRESS-TRACKER.md            # Live status across all phases
│   └── session-notes/                 # Per-session detailed logs
│       └── session-NNN.md
│
└── implementation/                    # Phase-by-phase build
    ├── phase-01-foundation/           # Operators + namespaces + GPU node
    ├── phase-02-data-pipeline/        # Kafka + PostgreSQL + Langfuse + Logging
    ├── phase-03-ai-core/              # RHOAI + vLLM + LlamaStack + RAG
    ├── phase-04-automation/           # AAP + EDA + ACM
    ├── phase-05-agent-mcp/            # LangGraph agent + 6 FastMCP servers
    ├── phase-06-dashboard/            # React UI + Chatbot + ServiceNow mock
    ├── phase-07-edge-workloads/       # nginx + log generator + ACM GitOps
    └── phase-08-validation/           # End-to-end tests + demo scenarios

Runbooks used by the RAG seed pipeline are under:
`implementation/phase-03-ai-core/rag/runbooks/`
```

---

## Implementation Phases

| Phase | Name | Key Deliverable | Estimated Time |
|-------|------|----------------|----------------|
| [01](implementation/phase-01-foundation/) | Foundation | All operators running, GPU node added | 1-2 days |
| [02](implementation/phase-02-data-pipeline/) | Data Pipeline | Kafka + Langfuse + LokiStack running | 1 day |
| [03](implementation/phase-03-ai-core/) | AI Core | Granite 4.0 serving via RHOAI | 1-2 days |
| [04](implementation/phase-04-automation/) | Automation | AAP + EDA + ACM connected | 1 day |
| [05](implementation/phase-05-agent-mcp/) | Agent & MCP | LangGraph agent + all 6 MCP servers + Lightspeed-driven template upsert path | 2-3 days |
| [06](implementation/phase-06-dashboard/) | Dashboard & UX | React dashboard + chatbot live | 1-2 days |
| [07](implementation/phase-07-edge-workloads/) | Edge Workloads | nginx failure → Kafka flow working | 1 day |
| [08](implementation/phase-08-validation/) | Validation | Full end-to-end demo passing | 1 day |

---

## Red Hat Products Used

| Product | Version | Role |
|---------|---------|------|
| OpenShift Container Platform | 4.21 | Container runtime (both clusters) |
| Red Hat OpenShift AI | 3.3 | MLOps platform, model serving |
| Red Hat ACM | 2.15 | Multi-cluster management |
| Red Hat Streams for Apache Kafka | 3.1 | Event streaming (KRaft, no ZooKeeper) |
| Red Hat Ansible Automation Platform | 2.5 | Automated remediation |
| Event-Driven Ansible (EDA) | 2.5 | Kafka-triggered automation |
| OpenShift Logging | 6.4 | Log collection + LokiStack storage |

---

## Command Log

Every command run during implementation is logged in [`logs/COMMANDS-LOG.md`](logs/COMMANDS-LOG.md).

Format:
```
Phase | Command | Why | Expected Output | Actual Output | Status
```

---

## Technology Stack

| Component | Version | License |
|-----------|---------|---------|
| IBM Granite | 4.0 H-Tiny | Apache 2.0 |
| Llama Stack | 0.3.5 | Apache 2.0 |
| LangGraph | 1.0 | MIT |
| vLLM | 0.15.1 | Apache 2.0 |
| Langfuse | 3.x | Apache 2.0 |
| FastMCP | 3.0.2 | MIT |
| pgvector | 0.8.1 | PostgreSQL License |
| MinIO | Latest | AGPL 3.0 |

---

## License

This project is licensed under the Apache 2.0 License. See [LICENSE](LICENSE) for details.

---

*Red Hat Dark NOC Workshop · Telco Edge AI · February 2026*
