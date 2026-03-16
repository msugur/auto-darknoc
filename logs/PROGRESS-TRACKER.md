# Dark NOC — Live Progress Tracker

> Updated after every session. Tracks what's done, what's in progress, and what's next.

---

## Implementation Status

### Phase 01 — Foundation (Operators + GPU Node)
| Step | Component | Status | Cluster | Notes |
|------|-----------|--------|---------|-------|
| 1 | Hub Namespaces | ✅ Done | Hub | Applied from `hub-namespaces.yaml` |
| 2 | Edge Namespace | ✅ Done | Edge | `dark-noc-edge` and `openshift-logging` created |
| 3 | NFD Operator | ✅ Done | Hub | Subscription present, CSVs healthy |
| 4 | cert-manager | ✅ Done | Hub | Subscription present, CSV `Succeeded` |
| 5 | Service Mesh | ✅ Done | Hub | Subscription present, CSV `Succeeded` |
| 6 | GPU Operator | ✅ Done | Hub | Subscription present, no degraded COs |
| 7 | GPU MachineSet (g5.2xlarge) | ⚠️ Issue found | Hub | SNO + existing GPU detected; likely not required |
| 8 | Wave 1 Operators (7x parallel) | ✅ Done | Hub | Kafka/AAP/ACM/Logging/Loki/CNPG/RHOAI all present; Loki OG fixed |
| 9 | Edge Logging Operator | ✅ Done | Edge | `cluster-logging.v6.4.2` Succeeded |
| 10 | Wave 2 Activation (MCH + DSC) | ✅ Done | Hub | `default-dsc Ready=True`; `MultiClusterHub Running (2.15.1)` |
| 11 | Hub Worker Capacity Scale-up | ✅ Done | Hub | Scaled `ocp-56g8n-worker-us-east-2a` to 1 (new worker joined) |

### Phase 02 — Data Pipeline
| Step | Component | Status | Cluster | Notes |
|------|-----------|--------|---------|-------|
| 1 | MinIO PVC + Deployment | ✅ Done | Hub | MinIO pod running with 200Gi gp3-csi PVC |
| 2 | MinIO Bucket Init Job | ✅ Done | Hub | Buckets created: `rhoai-models`, `loki-chunks`, `langfuse-data` |
| 3 | Kafka KRaft Cluster | ✅ Done | Hub | `dark-noc-kafka` ready in KRaft mode |
| 4 | Kafka Topics (5x) | ✅ Done | Hub | All 5 topics `READY=True` |
| 5 | Langfuse PostgreSQL | ✅ Done | Hub | CNPG cluster healthy (`langfuse-postgres-1`) |
| 6 | pgvector Build + Deploy | ✅ Done | Hub | Build `pgvector-postgres:16.4-v0.8.1` completed; CNPG cluster healthy |
| 7 | Redis + ClickHouse | ✅ Done | Hub | Both backends running in `dark-noc-observability` |
| 8 | Langfuse Web | ✅ Done | Hub | Helm chart `langfuse-1.5.22` deployed; web+worker running; route live |
| 8a | Langfuse ClickHouse stability fix | ✅ Done | Hub | ClickHouse OOM loop resolved by raising resources (`requests: 500m/2Gi`, `limits: 2000m/8Gi`); pod now `1/1 Running` |
| 8b | Agent -> Langfuse tracing keys | ✅ Done | Hub | Configured `agent-secrets` with project keys (`darknoc`) + Langfuse host, restarted agent, and validated fresh incident processing without `Langfuse client is disabled` warning |
| 9 | LokiStack + ClusterLogging | ✅ Done | Hub | LokiStack ready (`1x.demo`) + CLF collector DS `2/2` |
| 10 | Edge ClusterLogForwarder | ✅ Done | Edge | CLF `Ready=True`, collector DS `1/1` |
| 11 | End-to-end log validation | ✅ Done | Both | Edge nginx logs confirmed in hub Kafka `nginx-logs` (3 messages consumed) |

### Phase 03 — AI Core
| Step | Component | Status | Cluster | Notes |
|------|-----------|--------|---------|-------|
| 1 | DataScienceCluster CR | ✅ Done | Hub | `default-dsc` already present and Ready |
| 2 | Hardware Profile (A10G) | ✅ Done | Hub | Created `nvidia-a10g-gpu` (adapted to cluster GPU labels) |
| 3 | Granite model → MinIO | ⏳ Pending | Hub | Deferred; running with OCI fallback model source for now |
| 4 | vLLM InferenceService | ✅ Done | Hub | `granite-vllm` Ready=True; predictor running on GPU |
| 5 | LlamaStack Distribution | ✅ Done | Hub | `dark-noc-llamastack` Ready (`AVAILABLE=1`, server `0.4.2.1+rhai0`) after rh-dev env + DB privilege fixes |
| 6 | RAG Knowledge Base Seed | ✅ Done | Hub | Runbooks seeded (53 chunks) + product docs seeded (666 chunks) into pgvector |
| 7 | Inference validation | ✅ Done | Hub | In-pod `/v1/models` check returned model list (`granite-4-h-tiny`) |

### Phase 04 — Automation
| Step | Component | Status | Cluster | Notes |
|------|-----------|--------|---------|-------|
| 1 | AutomationController (AAP) | ✅ Done | Hub | Controller licensed and operational; API launch test successful (`job id 1`) |
| 1b | AAP credential rotation (`admin`) | ✅ Done | Hub+Repo | Updated repo defaults/manifests to `redhat`; rotated `aap` + `dark-noc-mcp` secrets; restarted `mcp-aap` + chatbot and validated AAP API auth |
| 1c | AAP edge credential refresh (`edge-01-k8s`) | ✅ Done | Hub+Edge | Fixed UI-triggered remediation failure by rotating expired edge API token in AAP credential; revalidated with successful `restart-nginx` job `29` |
| 1a | Enterprise AAP (Gateway+Hub+EDA) | ⚠️ Blocked | Hub | Gateway/UI up, but Hub PVC provisioning fails on AWS EBS CSI (`Volume capabilities not supported`) |
| 2 | EDA Controller | ⏳ Pending | Hub | |
| 2a | Edge EDA pattern assets | ✅ Done | Repo | Added `edge-eda` docs + deployable runner templates for `edge-01` |
| 2b | Edge local fast-path activation | ✅ Done | Edge | `edge-eda-runner` active on `edge-01`; OOM webhook event remediated nginx locally |
| 3 | EDA Rulebook upload | ⏳ Pending | Hub | Kafka source plugin |
| 4 | MultiClusterHub (ACM) | ✅ Done | Hub | Running `2.15.1` |
| 5 | Edge cluster import | ⏳ Pending | Edge | Klusterlet install |
| 6 | ACM ApplicationSet | ⏳ Pending | Hub | GitOps to edge |

### Phase 05 — Agent & MCP
| Step | Component | Status | Cluster | Notes |
|------|-----------|--------|---------|-------|
| 1 | Build mcp-openshift image | ✅ Done | Hub | Build `mcp-openshift-2` complete; Dockerfile fixed to provide `oc` shim |
| 2 | Build mcp-lokistack image | ✅ Done | Hub | Build `mcp-lokistack-2` complete |
| 3 | Build mcp-kafka image | ✅ Done | Hub | Build `mcp-kafka-1` complete |
| 4 | Build mcp-aap image | ✅ Done | Hub | Build `mcp-aap-1` complete |
| 5 | Build mcp-slack image | ✅ Done | Hub | Build `mcp-slack-1` complete (placeholder token secret in use) |
| 6 | Build mcp-servicenow image | ✅ Done | Hub | Build `mcp-servicenow-2` complete |
| 7 | Deploy all 6 MCP servers | ✅ Done | Hub | All deployments `1/1 Available`, services exposed on ports `8001-8006` |
| 7a | ServiceNow -> Slack auto notify | ✅ Done | Hub | `mcp-servicenow` now posts Slack message on each ticket create using `SLACK_BOT_TOKEN` |
| 7b | ServiceNow Slack link guarantee | ✅ Done | Hub+Repo | `mcp-servicenow` now always includes clickable incident URL in Slack ticket notification (sys_id link with ticket-number fallback), rebuilt as `mcp-servicenow-6` and rolled out |
| 7c | ServiceNow->Slack link verification test | ✅ Done | Hub+External | Live MCP `create_incident` test produced `INC0010007` with `incident_url` present and Slack post success (`sent=true`, `ts=1773159597.026269`) |
| 8 | Build LangGraph agent image | ✅ Done | Hub | BuildConfig created; image built successfully (`dark-noc-agent-14`, digest `sha256:e9f58e...`) |
| 9 | Deploy LangGraph agent | ✅ Done | Hub | Deployment rolled out; pod `ready=true`, consuming `nginx-logs` Kafka topic |
| 10 | Test MCP tool calls | ✅ Done | Hub | MCP `mcp-aap` now targets enterprise controller route; `restart-nginx` template (`id=8`) bound to `edge-01-k8s` credential and launch-validated |
| 10a | SCM playbook path prep | ✅ Done | Repo | Canonical file created: `playbooks/restart-nginx.yaml` for AAP project/template mapping |
| 10b | Real playbook switch in AAP | ✅ Done | Hub | Created internal SCM project `DarkNOC-Internal-SCM` and switched template to `playbooks/restart-nginx.yaml` |
| 10c | End-to-end remediation test | ✅ Done | Hub+Edge | AAP job `id=18` successful; edge nginx rollout confirmed (`restartedAt` + new pod) |
| 10d | LangGraph notify null-safety fix | ✅ Done | Hub+Repo | Patched `remediation_result` null handling in `node_notify`/`node_audit` and initial state; rebuilt agent (`dark-noc-agent-16`); no recurring `NoneType` crash in new incident run |
| 11 | Edge site naming standardization | ✅ Done | Both | Canonical site ID set to `edge-01` across configs/manifests/agent/slack defaults |
| 12 | Hub runtime rename (`edge-01`) | ✅ Done | Hub | `mcp-openshift` now uses `edge-01-kubeconfig`; AAP template `restart-nginx` defaults `edge_cluster=edge-01` |
| 13 | Edge live label rename (`edge-01`) | ✅ Done | Edge | Patched namespace `dark-noc-edge` label `dark-noc/site-id=edge-01`; verified no remaining old site-id in edge workload objects |

### Phase 06 — Dashboard
| Step | Component | Status | Cluster | Notes |
|------|-----------|--------|---------|-------|
| 1 | ServiceNow mock build + deploy | ✅ Done | Hub | Build `servicenow-mock-1` complete; deployment/route healthy |
| 2 | React dashboard build + deploy | ✅ Done | Hub | Build `dark-noc-dashboard-1` complete; route healthy |
| 2a | Enterprise UI upgrade | ✅ Done | Hub+Repo | Added MCP/platform status matrix + direct UI links + topology/error-flow SVG + EDA usage panel; deployed live |
| 3 | Chatbot backend | ✅ Done | Hub | Build `dark-noc-chatbot-1` complete; summary API healthy |
| 3a | Chatbot integrations API | ✅ Done | Hub+Repo | Added `/api/integrations` endpoint with MCP/service probes + dashboard URL catalog; currently `12/12 up` |
| 3b | Real ServiceNow integration | ✅ Done | Hub+External | `dark-noc-mcp/servicenow-secrets` switched to `dev365997`; runtime validation ticket `INC0010002` created from `mcp-servicenow` pod |
| 3c | ServiceNow caller policy | ✅ Done | Hub+External | Global caller enforced as `Mithun Sugur`; user provisioned in ServiceNow and caller-validated incident `INC0010003` created |
| 3d | Executive dashboard refresh | ✅ Done | Hub+Repo | Added Access Center with URLs+credentials, enhanced visual layout, and edge/hub EDA workflow panel |
| 3e | Topology + workflow wording update | ✅ Done | Hub+Repo | Topology zones renamed (`CORE · Hub -AI intelligence -Control Plane`, `DATA + MCP Agents`), edge `EDA-runner` node added, workflow expanded to 8 steps |
| 3f | NOC chat agentic knowledge responses | ✅ Done | Hub+Repo | `/api/chat` now returns agentic stack, AI model, workflow details, incident summary, and access URLs/credentials |
| 3g | Interactive NOC chat (model + MCP runtime payload) | ✅ Done | Hub+Repo | `/api/chat` executes live orchestration each query; model connectivity fixed to internal vLLM endpoint (`granite-vllm-predictor.dark-noc-hub.svc:8080/v1/completions`) and now returns `model_source=live`; UI includes session chat log + MCP status pills |
| 3h | Executive reply strict formatting | ✅ Done | Hub+Repo | Enforced deterministic executive structure in chatbot replies (`Summary`, `MCP Status`, `Model Output`, `Next Action`) with low-signal model text sanitization |
| 3i | Executive chat UI structured rendering | ✅ Done | Hub+Repo | Chat panel now parses executive headers and renders section cards with bullet lines for clean leadership-facing display |
| 3j | Quick Ask + Executive Brief actions | ✅ Done | Hub+Repo | Added one-click executive prompts (`Incident Posture`, `MCP Health`, `Remediation Status`, `Ticket+Slack Trace`) plus `Generate Executive Incident Brief` card in NOC Chat |
| 3k | C-level presentation deck | ✅ Done | Repo | Added executive deck with business value, telco narrative, Red Hat value map, workflow, KPI/ROI model, and technical appendix (`docs/presentation/Dark-NOC-Executive-Deck.md`) |
| 3l | UI Demo Mode trigger panel | ✅ Done | Hub+Repo | Added one-click `OOM/CrashLoop/Escalation` demo triggers in dashboard + new chatbot API endpoint (`/api/demo/trigger`) that publishes demo events to Kafka with direct links for AAP/ServiceNow/Slack/Langfuse |
| 3m | Executive topology visual deployed | ✅ Done | Hub+Repo | Upgraded topology panel with curved workflow arrows, product-level labels, flow legend, and lane clarity; deployed as dashboard build `dark-noc-dashboard-9` and verified live assets |
| 3n | Topology overlap cleanup + lane routing | ✅ Done | Hub+Repo | Re-routed arrows into structured telemetry/remediation/escalation lanes to remove overlap; deployed as dashboard build `dark-noc-dashboard-10` (`index-CwWCFhDA.js`) |

### Phase 07 — Edge Workloads
| Step | Component | Status | Cluster | Notes |
|------|-----------|--------|---------|-------|
| 1 | nginx deployment (edge) | ✅ Done | Edge | Running with stdout JSON logs |
| 2 | Failure simulator CronJob | ✅ Done | Edge | Installed and tested via one-shot `nginx-oom-now`; CronJob remains suspended by default |
| 3 | Verify logs → Kafka | ✅ Done | Both | Hub consumed `nginx-logs` successfully |

### Phase 08 — Validation
| Step | Component | Status | Cluster | Notes |
|------|-----------|--------|---------|-------|
| 1 | Run test-scenarios.sh (OOMKill) | ✅ Done | Both | Edge local OOM test validated: memory restored to `128Mi/64Mi`, restart timestamp changed, new nginx pod running |
| 2 | Run test-scenarios.sh (CrashLoop) | 🔄 In Progress | Both | AAP/Slack/ServiceNow integration validated with targeted incidents |
| 2a | Slack validation notification | ✅ Done | External | Posted info message to `#demos` (`ts=1773074977.088439`) |
| 2b | ServiceNow info ticket | ✅ Done | Hub Mock | Created `INC0000002` in deployed ServiceNow mock; real instance API auth currently rejected (401) |
| 2c | Hub reporting proof (edge->hub) | ✅ Done | Both | Live trigger captured on hub Kafka (`nginx-logs`) with `dark-noc_site-id=edge-01` and updated `restartedAt=2026-03-09T17:05:41Z` |
| 2d | Real ServiceNow ticket validation | ✅ Done | External | Real ServiceNow (`dev365997`) auth and create validated: `INC0010001` (local), `INC0010002` (from mcp-servicenow pod) |
| 2e | Guided E2E walkthrough (issue→EDA/Kafka→LangGraph→AAP→ITSM/Slack→Chatbot) | ✅ Done | Hub+Edge+External | CrashLoop injected and traced end-to-end (`INCIDENT 8c873e35`); AAP job `id=20` successful; ServiceNow info ticket `INC0010004`; Slack post success (`ts=1773082658.446029`); chatbot executive query validated |
| 2f | Full platform re-validation + E2E replay | ✅ Done | Hub+Edge+External | Service sweep healthy (Dark NOC core 1/1); edge `edge-eda-runner` + `nginx` running; triggered Kafka incidents and validated LangGraph processing (`INCIDENT fe3f8920`, `2f771b21`), AAP remediation job `id=25` successful, ServiceNow ticket `INC0010005` (caller `Mithun Sugur`), Slack confirmation post (`ts=1773158887.542969`), dashboard integrations `12/12` |
| 2g | Lightspeed generated-template automation hardening | ✅ Done | Hub+Repo+External | Fixed `mcp-aap` secret env mismatch and deployment rollback; synchronized source trees; rebuilt `dark-noc-agent-24` + `mcp-aap-4`; stabilized upsert behavior; final validation incident `c914d202` with AAP job `79` successful, ServiceNow `INC0010029`, generated template `generated-ansible-job-failure-f0ec346d` (`id=15`) |
| 3 | Full demo rehearsal | ⏳ Pending | Both | |

---

## Legend
- ✅ Done
- 🔄 In Progress
- ⏳ Pending
- ❌ Blocked
- ⚠️ Issue found

---

## What We Need From You

| Item | Status | Notes |
|------|--------|-------|
| Hub cluster oc login | ✅ Received | Token TTL is short; refresh as needed during execution |
| Edge cluster oc login | ✅ Received | Used for edge kubeconfig secret in MCP OpenShift server |
| Slack Bot Token | ✅ Received | Bot token configured in `dark-noc-mcp/slack-secrets`; channel `#demos` |
| AWS region confirmation | ✅ Received | Using us-east-2 from active node naming |

---

## Command Log Summary
See `logs/COMMANDS-LOG.md` for all successful commands with outputs.

---

## Session History
| Session | Date | What Was Done |
|---------|------|---------------|
| Session 001 | 2026-02-26 | Architecture design + all 96 project files created |
| Session 002 | 2026-02-27 | Scope + technical summary confirmed; deployment pending credentials |
| Session 003 | 2026-03-03 | Both clusters upgraded to 4.21.3; hub Wave 0/1 healthy; MinIO + Kafka + Langfuse PostgreSQL deployed |

### Repo Hygiene
| Step | Component | Status | Cluster | Notes |
|------|-----------|--------|---------|-------|
| RH-1 | Single-source consolidation (`dark-noc`) | ✅ Done | local | Merged `darknoc-demo` into `dark-noc`, removed transient artifacts, deleted `darknoc-demo`; `dark-noc` is now source-of-truth |
| RH-2 | Empty-folder + transient-artifact cleanup + START-HERE guide | ✅ Done | local | Removed all empty directories and transient artifacts; added `docs/deployment/START-HERE.md`; updated root README link for newcomer redeploy flow |
| RH-3 | Lightspeed documentation normalization + deployment-order hardening | ✅ Done | local | Root README, START-HERE, redeploy runbook, and Phase 04/05 READMEs now explicitly cover Lightspeed placement, sequence, and validation checkpoints |
| RH-4 | Canonical ordered deployment layer (manifest + dry-run/apply/validate scripts) | ✅ Done | local | Added `deploy/manifest-order.tsv`, orchestration scripts, access template, and docs wiring for deterministic dependency-safe deployment |
| RH-5 | Modular model-profile layer (AI Hub catalog -> vLLM/LlamaStack/Agent/Chatbot binding) | ✅ Done | local | Added profile envs + templated manifests + `render-model-profile.sh` + binding ConfigMaps + docs (`MODEL-PROFILES.md`) so model switching is centralized and repeatable |
| RH-6 | Cross-namespace model binding (`my-first-model` -> Dark NOC) + Granite 3.1 profile | ✅ Done | local | Added `bind-existing-model.sh`, `granite-3.1-8b-lab-v1` profile, `my-first-model` ISVC manifest, and docs for one-command endpoint binding/restart |
| RH-7 | Live Granite 3.1 bind execution (`my-first-model` -> Dark NOC) | 🔄 In Progress | Hub | ISVC `granite-31-8b-lab-v1` created; currently `READY=False`; binding blocked intermittently by hub API DNS (`no such host`) from execution shell |
| RH-8 | Switch Dark NOC inference binding to `my-first-model/llama-32-3b-instruct` | ✅ Done | Hub | Stuck predictor pod deleted and ISVC recovered (`READY=True` observed); `dark-noc-model-binding` updated in hub/ui namespaces; agent/chatbot restarted; rollout verification may require retry due intermittent hub API DNS |
| RH-9 | Post-switch verification retry (`llama-32-3b-instruct`) | ✅ Done | Hub+my-first-model | Rollouts succeeded (`dark-noc-agent`, `dark-noc-chatbot`), both pods `Running`, `my-first-model/isvc llama-32-3b-instruct READY=True`; intermittent API DNS affects some non-critical readbacks |
| RH-10 | Lightspeed E2E rerun from bastion (post model endpoint repair) | ✅ Done | Hub+Bastion | Incident `1d8d7d34` processed; AAP job `81` successful on `lightspeed-generate-and-run`; ServiceNow `INC0010030` created; required fixes applied: model endpoint repoint + FQDN + predictor replica scale-up |
| RH-11 | LLM/vLLM to MCP connectivity verification (in-pod, protocol-level) | ✅ Done | Hub+Bastion | Agent pod validated `vLLM /models` + `/completions` (200); wired MCP endpoints (`OpenShift/Loki/AAP/Slack/ServiceNow`) reachable and returning expected protocol errors (`406` without stream header, `400 Missing session ID` with stream header) |
| RH-12 | Full connectivity verification (LLM/vLLM -> chatbot/langgraph/langfuse/kafka/openshift + all 13 integrations) | ✅ Done | Hub+Bastion | Verified `vLLM /models` + `/completions` = 200, chatbot `model_source=live`, integrations `13/13 up`, Kafka TCP ok, LangGraph incident processing active; fixed agent `LANGFUSE_HOST` to `langfuse-web` and revalidated health 200; OpenShift MCP pod has RBAC-scoped restrictions for list operations |
| RH-13 | Dashboard topology/workflow refresh for current vLLM + Lightspeed architecture | ✅ Done | local | Updated demo trigger names, topology labels, RAG/model details, MCP-LangGraph wiring text, and added platform cake layer (OpenShift/OpenShift AI/AWS/NVIDIA) |
| RH-14 | Dashboard compile sanity check | ✅ Done | local | Installed dashboard dependencies (`npm install`) and validated production build success (`vite v6.0.11`, dist artifacts generated) |
| RH-15 | Dashboard live rollout of latest UI changes | ⚠️ Issue found | Hub | Multiple retries still blocked by DNS resolution in execution shell for both API and route hosts (`api.ocp.v8w9c...` and `dark-noc-dashboard...` no such host); latest probe confirms global DNS outage in shell (public hosts fail too) |
| RH-16 | Dashboard redeployability hardening (BuildConfig + ordered steps) | ✅ Done | local | Added dashboard ImageStream/BuildConfig manifest, wired into `manifest-order.tsv`, and documented one-command build/rollout flow in Phase 06 README |
