# Dark NOC Product & Tool Version Matrix

Last updated: 2026-03-11 15:54 EDT

## 1) Red Hat Platform Stack

| Product | Version | Where Used |
|---|---:|---|
| OpenShift Container Platform | 4.21.3 | Hub and Edge cluster base |
| Red Hat OpenShift AI Operator | 3.3.0 | Hub AI core (`DataScienceCluster`, model serving) |
| Red Hat Advanced Cluster Management (ACM) | 2.15.1 | Hub/Edge multicluster lifecycle and policy |
| Red Hat Ansible Automation Platform (AAP) | 2.5.x | Hub controller, EDA, automation workflows |
| Red Hat Streams for Apache Kafka (AMQ Streams) | 3.1.0 | Kafka operator on Hub |
| Apache Kafka (KRaft mode) | 4.0.0 (`metadataVersion: 4.0-IV3`) | Event backbone (`nginx-logs`, remediation, audit topics) |
| Red Hat OpenShift Logging | 6.4.2 | Hub + Edge logging pipeline |
| Red Hat Loki Operator | 6.4.2 | Hub LokiStack deployment |
| OpenShift Service Mesh | 3.1.0 | Hub service connectivity/security layer |
| CloudNativePG Operator | 1.28.1 | PostgreSQL clusters for Langfuse + pgvector |
| NVIDIA GPU Operator | v25.3 channel | GPU enablement on Hub |
| cert-manager | stable-v1 channel | TLS cert lifecycle automation |

## 2) AI / Agentic Stack

| Product | Version | Where Used |
|---|---:|---|
| Granite | 4.0 H-Tiny | Incident reasoning/RCA model |
| vLLM | 0.15.1 | Inference serving layer |
| LlamaStack runtime | 0.4.2.1+rhai0 | AI runtime/orchestration layer |
| LangGraph | 1.0.0 | Autonomous NOC workflow engine |
| FastMCP | 3.0.2 | MCP servers for tool integration |
| pgvector | 0.8.1 | RAG vector index in Postgres |

## 3) Data, Observability, and UI

| Product | Version | Where Used |
|---|---:|---|
| Langfuse (target app version) | 3.14.5 | LLM/agent observability |
| Langfuse Helm chart | 1.5.22 | Langfuse deployment artifact |
| Langfuse app image tag (values file) | 3.155.1 | Current chart values pin |
| Redis | Manifest-driven | Langfuse cache/queue |
| ClickHouse | Manifest-driven | Langfuse analytics store |
| MinIO | Manifest-driven | S3-compatible object storage |

## 4) Runtime Libraries and Build Images

### Python and App Libraries

| Library / Runtime | Version | Where Used |
|---|---:|---|
| Python base image | 3.12-slim | Agent, MCP servers, chatbot, ServiceNow mock |
| FastAPI | 0.115.0 | Chatbot + ServiceNow mock |
| Uvicorn | 0.37.0 / 0.32.0 | MCP servers / chatbot+mock |
| httpx | 0.28.1 | MCP and chatbot API clients |
| kafka-python-ng | 2.2.3 | Agent, MCP Kafka, chatbot events |
| openai | 1.69.0 | Model API client in agent |
| langchain | 0.3.20 | Agent orchestration layer |
| langchain-openai | 0.3.10 | LangChain OpenAI compatibility |
| langchain-core | >=0.3.75,<1.0.0 | Core chain primitives |
| langgraph-checkpoint-postgres | 2.0.25 | LangGraph checkpointing |
| psycopg2-binary | 2.9.10 | PostgreSQL connectivity |
| mcp | 1.24.0 | MCP client/runtime integration |
| langfuse (SDK) | 2.57.0 | Tracing/telemetry export |
| sentence-transformers | 3.4.0 | Embeddings/RAG ingestion |
| torch | 2.8.0+cpu | Embedding/runtime dependency |
| python-dotenv | 1.1.0 | Environment loading |

### Frontend/Container Build Images

| Image | Version | Where Used |
|---|---:|---|
| Node.js build image | node:22-alpine | Dashboard build stage |
| NGINX runtime image | nginxinc/nginx-unprivileged:1.27-alpine | Dashboard runtime |

## 5) MCP Integrations in Scope

| MCP Server | Backend Integration |
|---|---|
| `mcp-openshift` | OpenShift/Kubernetes API operations |
| `mcp-kafka` | Kafka topic produce/consume/lag checks |
| `mcp-lokistack` | Loki LogQL queries |
| `mcp-aap` | AAP Controller REST API (job templates/jobs) |
| `mcp-slack` | Slack Bot API messaging/alerts |
| `mcp-servicenow` | ServiceNow incident create/update/get |

## 6) Source of Truth (for updates)

When versions change, update this file from these primary artifacts:

- `docs/architecture/overview.md`
- `implementation/phase-03-ai-core/rag/documentation-sources.yaml`
- `implementation/phase-02-data-pipeline/kafka/kafka-cluster.yaml`
- `implementation/phase-05-agent-mcp/agent/requirements.txt`
- `implementation/phase-05-agent-mcp/mcp-servers/*/requirements.txt`
- `implementation/phase-06-dashboard/chatbot/requirements.txt`
- `implementation/phase-06-dashboard/servicenow-mock/Dockerfile`
- `implementation/phase-06-dashboard/dashboard/Dockerfile`

## 7) Version Notes

- `Langfuse` appears in two places with different values (`3.14.5` target docs vs `3.155.1` image tag in values). Keep both visible until you standardize deployment values.
- AAP is managed as `2.5` operator/platform family; patch-level may vary by catalog at deployment time.
