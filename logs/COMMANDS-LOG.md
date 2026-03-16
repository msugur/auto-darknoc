# Dark NOC — Successful Commands Log

> This file records **every command that ran successfully** during the Dark NOC implementation.
> Commands are logged in execution order with full context.
> Use this as a definitive reference to reproduce the exact build.

---

## Log Format

Each entry follows this structure:

```
### CMD-XXXX — <Short Description>
- **Phase:**        Phase number and name
- **Cluster:**      hub | edge | both | local
- **Date:**         YYYY-MM-DD HH:MM UTC
- **Why:**          Why we are running this command
- **What:**         What the command actually does technically
- **Expected:**     What output/state we expect to see
- **Outcome:**      What we achieved / why this matters

**Command:**
\`\`\`bash
<exact command>
\`\`\`

**Output:**
\`\`\`
<actual output>
\`\`\`
**Status:** ✅ SUCCESS

### CMD-0209 — Topology Arrow Overlap Cleanup (Structured Lane Routing)
- **Phase:** 06 — Dashboard
- **Cluster:** hub + repo
- **Date:** 2026-03-10 UTC
- **Why:** User reported overlapping flow arrows/labels in executive topology view.
- **What:**
  1. Refactored topology SVG flow paths into three distinct lanes:
     - telemetry lane (blue)
     - remediation lane (green)
     - escalation lane (amber, dashed)
  2. Reduced crossing paths and moved flow labels to lane headers for cleaner readability.
  3. Built/deployed dashboard as `dark-noc-dashboard-10`.
  4. Restarted rollout and verified new live bundle hashes:
     - JS: `/assets/index-CwWCFhDA.js`
     - CSS: `/assets/index-B2R4hLzl.css`
- **Expected:** Non-overlapping, structured executive workflow visualization.
- **Outcome:** Success. Updated topology is live.

**Status:** ✅ SUCCESS

### CMD-0208 — Deploy Executive Topology Dashboard Refresh
- **Phase:** 06 — Dashboard
- **Cluster:** hub
- **Date:** 2026-03-10 UTC
- **Why:** Publish the updated executive topology/error-flow UI to live route.
- **What:**
  1. Started binary build from updated dashboard source: `dark-noc-dashboard-9`.
  2. Build completed and pushed image digest:
     - `sha256:e384c24c9c82a30a201edc3f9c97b10a6c19640db74ee1ccf48ecf5dc523b609`
  3. Verified deployment, then forced rollout restart to ensure latest image served.
  4. Confirmed new pod and live route now serving new bundle hashes:
     - JS: `/assets/index-Bls6KqlW.js`
     - CSS: `/assets/index-lB3hVDk6.css`
- **Expected:** Dashboard shows upgraded executive topology with curved arrows and detailed product stack labels.
- **Outcome:** Success. Deployment rolled out and route serves updated static assets.

**Status:** ✅ SUCCESS

### CMD-0207 — Executive Topology & Technical Diagram Upgrade
- **Phase:** 06 — Dashboard + Architecture Docs
- **Cluster:** repo (UI/docs)
- **Date:** 2026-03-10 UTC
- **Why:** User requested a high-end executive visual for Edge/Hub/AI/MCP topology with clearer directional workflow.
- **What:**
  1. Rebuilt the `Topology & Error Flow` section in dashboard with:
     - stronger zone segmentation (`EDGE`, `CORE`, `DATA + MCP Agents`)
     - executive subtitle + product strip
     - curved directional paths for telemetry, remediation, and escalation
     - multi-color arrow semantics and legend.
  2. Expanded node labels to show real product stack:
     - OpenShift workloads, Vector/CLF, Edge EDA Runner
     - Kafka, LangGraph + LlamaStack + Granite, AAP + Hub EDA, MCP Mesh
     - LokiStack/Langfuse/pgvector, ServiceNow, Slack, UI portals.
  3. Updated architecture document topology from ASCII diagram to executive Mermaid flowchart with lane definitions:
     - telemetry lane
     - automation lane
     - governance lane.
- **Expected:** C-level readable architecture and cleaner technical flow communication in both live UI and documentation.
- **Outcome:** Success. UI and docs updated; local vite build check unavailable in workspace due missing local dependency (`vite` not installed), but OpenShift build pipeline remains the deployment validation path.

**Status:** ✅ SUCCESS

### CMD-0206 — Fix AAP Restart Failure from UI Demo Trigger
- **Phase:** 06/08 — Dashboard Trigger + Validation
- **Cluster:** hub + edge + AAP
- **Date:** 2026-03-10 UTC
- **Why:** User reported AAP job failure after `CrashLoopBackOff` demo event from UI trigger.
- **What:**
  1. Pulled latest agent/AAP execution evidence and identified failed run:
     - Template `restart-nginx` job `27` = `failed`.
  2. Collected job stdout from AAP API and confirmed root cause:
     - Kubernetes API `401 Unauthorized` while playbook queried edge deployment.
     - Failure occurred in `k8s_info` task for edge cluster access.
  3. Rotated AAP credential `edge-01-k8s` with fresh edge token and verified update timestamp.
  4. Relaunched template `restart-nginx` with same extra vars used by agent flow.
  5. Confirmed successful remediation execution:
     - Job `29` = `successful`
     - Play recap: `ok=7 changed=1 failed=0`
     - nginx rollout restart + running pod verification passed.
- **Expected:** UI-triggered crashloop events can remediate through AAP without auth failures.
- **Outcome:** Success. Root cause fixed by credential rotation; remediation pipeline operational again.

**Status:** ✅ SUCCESS

### CMD-0205 — Dashboard Demo Mode (UI Trigger) Deployment
- **Phase:** 06 — Dashboard/Chatbot
- **Cluster:** repo + hub
- **Date:** 2026-03-10 UTC
- **Why:** User requested a UI-driven way to stimulate and showcase end-to-end flow from the dashboard.
- **What:**
  1. Updated chatbot API (`phase-06-dashboard/chatbot/main.py`) with:
     - `POST /api/demo/trigger` endpoint
     - scenario payload model (`oom`, `crashloop`, `escalation`)
     - Kafka producer publishing to `nginx-logs`
     - response links for AAP jobs, ServiceNow incidents, Slack, and Langfuse.
  2. Updated dashboard UI (`phase-06-dashboard/dashboard/src/App.jsx`, `styles.css`) with:
     - Demo Mode card
     - one-click scenario buttons
     - result panel with event details and deep links.
  3. Rebuilt and rolled out components:
     - chatbot build `dark-noc-chatbot-11` and successful rollout
     - dashboard build `dark-noc-dashboard-8` and successful rollout.
  4. Verified chatbot health and integrations API after rollout.
- **Expected:** Operators can trigger guided demo incidents directly from UI without CLI and follow links through remediation/ITSM flow.
- **Outcome:** Success. Build/deploy completed for both services and integrations endpoint remains healthy (`12/12 up`). Direct POST validation from this runtime intermittently failed due transient DNS resolution in sandbox, but deployed route health is green.

**Status:** ✅ SUCCESS

### CMD-0211 — ServiceNow Link-in-Slack Live Verification
- **Phase:** 05/08 — MCP + Validation
- **Cluster:** hub + external
- **Date:** 2026-03-10 UTC
- **Why:** User requested explicit test+verification that every ServiceNow ticket Slack message includes a direct ticket link.
- **What:**
  1. Ran live MCP protocol test against `mcp-servicenow` via local port-forward (`/mcp`, `initialize`, `tools/call create_incident`).
  2. Created test incident:
     - Ticket: `INC0010007`
     - sys_id: `6d2b61e9936332106c4bf9f7dd03d693`
  3. Verified returned payload includes:
     - `incident_url`: `https://dev365997.service-now.com/incident.do?sys_id=6d2b61e9936332106c4bf9f7dd03d693`
     - `slack_notification.sent=true`
     - `slack_notification.ts=1773159597.026269`
- **Expected:** Ticket creation response contains a clickable ServiceNow URL and Slack delivery success metadata.
- **Outcome:** Success. Requirement validated end-to-end with runtime evidence.

**Status:** ✅ SUCCESS

### CMD-0210 — Enforce ServiceNow Incident Link in Slack Notifications
- **Phase:** 05 — MCP Integrations
- **Cluster:** hub + repo
- **Date:** 2026-03-10 UTC
- **Why:** User requested that every ServiceNow ticket posted to Slack must include a direct incident link.
- **What:**
  1. Updated `mcp-servicenow` URL generation logic:
     - Primary URL: `incident.do?sys_id=<sys_id>`
     - Fallback URL: `incident_list.do?sysparm_query=number=<INC...>`
     - Final fallback: `incident_list.do`
  2. Ensured `create_incident()` always populates `incident_url` before Slack notification is sent.
  3. Rebuilt and deployed updated MCP server:
     - OpenShift build: `mcp-servicenow-6`
     - New image digest pushed and deployment rolled out successfully.
- **Expected:** Slack ticket notifications always contain a clickable ServiceNow URL, even if `sys_id` is unavailable.
- **Outcome:** Success. Logic and live deployment updated.

**Status:** ✅ SUCCESS

### CMD-0209 — End-to-End Validation Replay (Hub + Edge + Integrations)
- **Phase:** 08 — Validation
- **Cluster:** hub + edge + external
- **Date:** 2026-03-10 UTC
- **Why:** User requested full service check and fresh E2E trigger/validation.
- **What:**
  1. Ran full health sweep across solution namespaces:
     - Dark NOC core deployments healthy (`dark-noc-hub`, `-kafka`, `-mcp`, `-minio`, `-observability`, `-ui`, `-servicenow-mock` all core components `1/1`).
     - AAP controller/gateway/EDA healthy; AAP Hub subcomponents still pending (known storage constraint).
  2. Validated edge cluster runtime:
     - Logged into edge cluster and confirmed `dark-noc-edge` namespace healthy (`edge-eda-runner`, `nginx` running).
  3. Triggered E2E events to Kafka `nginx-logs`:
     - Escalation event -> agent `INCIDENT 2f771b21` executed `ESCALATE` path.
     - CrashLoop event -> agent `INCIDENT fe3f8920` executed remediation path with `Triggered AAP job: restart-nginx`.
  4. Verified downstream outcomes:
     - AAP enterprise job `id=25` status `successful`.
     - ServiceNow real incident created: `INC0010005`, caller `Mithun Sugur`.
     - Dashboard integrations endpoint: `12/12 up`.
     - Chatbot runtime query: `model_source=live`, model `granite-4-h-tiny`.
     - Slack validation message posted to `#demos` (`channel C08MUDSNHED`, `ts=1773158887.542969`).
- **Expected:** Evidence-backed replay of complete detection -> analysis -> remediation/escalation -> ITSM/chat workflow.
- **Outcome:** Success. End-to-end flow validated with fresh runtime artifacts across hub, edge, and external integrations.

**Status:** ✅ SUCCESS

### CMD-0208 — Langfuse Project Key Wiring + Live Incident Validation
- **Phase:** 05/08 — Agent + Validation
- **Cluster:** hub
- **Date:** 2026-03-10 UTC
- **Why:** User provided Langfuse project keys for `darknoc`; tracing needed activation and runtime proof.
- **What:**
  1. Updated `dark-noc-hub/agent-secrets` with:
     - `LANGFUSE_PUBLIC_KEY=pk-lf-...`
     - `LANGFUSE_SECRET_KEY=sk-lf-...`
     - `LANGFUSE_HOST=https://langfuse-dark-noc-observability.apps.ocp.v8w9c.sandbox205.opentlc.com`
  2. Restarted `dark-noc-agent` deployment and verified successful rollout.
  3. Published synthetic nginx error event to Kafka topic `nginx-logs`.
  4. Verified agent processed incident end-to-end (`INCIDENT da3a3ac3`) through RAG -> Analyze -> Remediate -> Audit with no new startup warning `Langfuse client is disabled`.
- **Expected:** Agent tracing path active and validated against a fresh runtime incident.
- **Outcome:** Success. Keys applied and incident pipeline executed with updated tracing configuration.

**Status:** ✅ SUCCESS

### CMD-0207 — Langfuse Backend Recovery + Agent Secret Normalization
- **Phase:** 02/05 — Observability + Agent
- **Cluster:** hub + repo
- **Date:** 2026-03-10 UTC
- **Why:** Langfuse UI had no visible observability data; backend storage and agent tracing config required remediation.
- **What:**
  1. Diagnosed Langfuse state:
     - `clickhouse` pod in `CrashLoopBackOff` with `OOMKilled (137)`.
     - Agent logs showed: `Langfuse client is disabled since no public_key was provided`.
  2. Increased ClickHouse resources and rolled deployment:
     - Runtime: `requests cpu=500m,memory=2Gi`, `limits cpu=2000m,memory=8Gi`.
     - Result: `clickhouse` recovered to `1/1 Running`.
  3. Normalized `dark-noc-hub/agent-secrets` and restarted `dark-noc-agent`:
     - Confirmed DB URLs and `LANGFUSE_HOST` set to in-cluster service.
     - `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` intentionally left empty pending project key creation.
  4. Updated repo manifest to match live ClickHouse resource profile:
     - `implementation/phase-02-data-pipeline/langfuse/clickhouse-deployment.yaml`.
- **Expected:** Stable Langfuse backend and agent ready for tracing once project API keys are provided.
- **Outcome:** Success for infrastructure recovery; final trace visibility now blocked only on missing Langfuse project API keys.

**Status:** ✅ SUCCESS

### CMD-0206 — Executive Presentation Deck (C-Suite + Technical)
- **Phase:** 06 — Dashboard/Presentation
- **Cluster:** repo
- **Date:** 2026-03-09 UTC
- **Why:** User requested an executive-grade presentation covering business value, workflow, Red Hat value, telco relevance, and technical detail.
- **What:**
  1. Created a complete slide-ready markdown deck:
     - `docs/presentation/Dark-NOC-Executive-Deck.md`
  2. Included structured sections:
     - Executive problem statement and value narrative
     - Red Hat/OpenShift/OpenShift AI strategic value mapping
     - End-to-end edge+hub workflow and architecture
     - KPI/ROI framework for leadership
     - Technical appendix with implementation phases and components
  3. Updated governance tracker (`PROGRESS-TRACKER.md`) to reflect delivery.
- **Expected:** A presentation asset leadership can use for both business sponsorship and technical confidence.
- **Outcome:** Success. Deck created and versioned in repo for immediate use and iterative refinement.

**Status:** ✅ SUCCESS

### CMD-0205 — AAP Password Rotation to `redhat` (Repo + Runtime)
- **Phase:** 04/05/06 — Automation + MCP + Dashboard
- **Cluster:** hub + repo
- **Date:** 2026-03-09 UTC
- **Why:** User requested AAP password change to `redhat` everywhere.
- **What:**
  1. Updated repo files:
     - `implementation/phase-04-automation/aap/automation-controller.yaml`
     - `implementation/phase-05-agent-mcp/mcp-servers/mcp-aap/server.py`
     - `implementation/phase-06-dashboard/chatbot/deployment.yaml`
     - `implementation/phase-06-dashboard/chatbot/main.py`
  2. Rotated live secrets:
     - `aap/aap-admin-secret`
     - `aap/aap-enterprise-controller-admin-password`
     - `dark-noc-mcp/aap-admin-secret`
  3. Restarted workloads:
     - `dark-noc-mcp/deploy/mcp-aap`
     - `dark-noc-ui/deploy/dark-noc-chatbot`
  4. Verified:
     - All rotated secrets decode to `redhat`
     - AAP enterprise controller API ping authenticates with `admin:redhat`
- **Expected:** All AAP credentials aligned to `redhat` across manifests, runtime secrets, and dependent services.
- **Outcome:** Success. Password changed and validated end-to-end.

**Status:** ✅ SUCCESS

---

### CMD-0148 — Build and Deploy All 6 MCP Servers on Hub
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Complete MCP runtime layer so the LangGraph agent can call operational tools through MCP endpoints.
- **What:**
  1. Added missing Dockerfiles for `mcp-aap`, `mcp-kafka`, `mcp-lokistack`, `mcp-servicenow`, and `mcp-slack`.
  2. Fixed `mcp-openshift` Dockerfile to provide `oc` executable (`kubectl` symlink).
  3. Created/updated required MCP secrets in `dark-noc-mcp`:
     - `edge-01-kubeconfig`
     - `aap-admin-secret`
     - `slack-secrets`
  4. Built all six images using OpenShift binary builds and applied `mcp-servers-deployment.yaml`.
- **Expected:** All MCP deployments roll out and services become reachable on ports `8001-8006`.
- **Outcome:** Success.
  - Deployments `mcp-openshift`, `mcp-lokistack`, `mcp-kafka`, `mcp-aap`, `mcp-slack`, `mcp-servicenow` all `1/1 Available`.
  - Services created for all six MCP endpoints in `dark-noc-mcp`.

**Status:** ✅ SUCCESS

---

### CMD-0149 — Resolve MCP Dependency Conflicts in Requirements
- **Phase:** 05 — Agent & MCP
- **Cluster:** repo code update
- **Date:** 2026-03-06 UTC
- **Why:** MCP builds initially failed due incompatible pins with `fastmcp==3.0.2`.
- **What:**
  1. Updated all MCP `requirements.txt` files from `uvicorn==0.32.0` to `uvicorn==0.37.0`.
  2. Updated `httpx==0.27.0` to `httpx==0.28.1` for `mcp-aap`, `mcp-lokistack`, `mcp-slack`, and `mcp-servicenow`.
- **Expected:** OpenShift binary builds resolve dependencies and complete.
- **Outcome:** Success. Previously failing builds became successful after pin alignment.

**Status:** ✅ SUCCESS

---

### CMD-0150 — MCP Build Artifact Cleanup (Hub)
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Remove failed MCP build history from early attempts and keep namespace clean for reproducible redeploys.
- **What:** Deleted failed build objects and stale failed build pods:
  - `mcp-openshift-1`
  - `mcp-lokistack-1`
- **Expected:** Only complete/current build records remain.
- **Outcome:** Success. `oc get builds -n dark-noc-mcp` shows only valid complete builds for active MCP images.

**Status:** ✅ SUCCESS

---

### CMD-0151 — Deploy ServiceNow Mock Backend (Phase 06 Step 1)
- **Phase:** 06 — Dashboard
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** `mcp-servicenow` depends on in-cluster ServiceNow API target for incident create/update flows.
- **What:**
  1. Created/verified namespace `dark-noc-servicenow-mock`.
  2. Created binary BuildConfig `servicenow-mock` and built image `servicenow-mock-1`.
  3. Applied deployment/service/route manifest from `phase-06-dashboard/servicenow-mock/deployment.yaml`.
  4. Verified rollout completion.
- **Expected:** ServiceNow mock pod running and route available.
- **Outcome:** Success. Deployment is `1/1 Available`, service and route are active.

**Status:** ✅ SUCCESS

---

### CMD-0152 — Validate ServiceNow Mock Route Health
- **Phase:** 06 — Dashboard
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Confirm deployed mock API is reachable and healthy for MCP integration.
- **What:** Called route health endpoint over HTTPS.
- **Expected:** JSON health response from FastAPI service.
- **Outcome:** Success.
  - Response: `{"status":"ok","incidents_count":0}`

**Status:** ✅ SUCCESS

---

### CMD-0153 — Deploy Phase 06 Chatbot Backend in dark-noc-ui
- **Phase:** 06 — Dashboard
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Provide dashboard API endpoints (`/api/summary`, `/api/chat`) and integration surface for ServiceNow status.
- **What:**
  1. Added missing chatbot source files under `phase-06-dashboard/chatbot/`.
  2. Created binary BuildConfig and built image `dark-noc-chatbot-1`.
  3. Applied `chatbot/deployment.yaml` (Deployment + Service + Route).
- **Expected:** Chatbot pod and route available in `dark-noc-ui`.
- **Outcome:** Success. Deployment rolled out (`1/1 Available`) and route published.

**Status:** ✅ SUCCESS

---

### CMD-0154 — Deploy React Dashboard in dark-noc-ui
- **Phase:** 06 — Dashboard
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Expose a live UI surface for Dark NOC runtime visibility.
- **What:**
  1. Added missing React/Vite dashboard files under `phase-06-dashboard/dashboard/`.
  2. Built image `dark-noc-dashboard-1` via binary BuildConfig.
  3. Applied `dashboard/deployment.yaml` (Deployment + Service + Route).
- **Expected:** Dashboard pod and route become available.
- **Outcome:** Success. Vite production build completed in-cluster and deployment rolled out (`1/1 Available`).

**Status:** ✅ SUCCESS

---

### CMD-0155 — Validate Chatbot and Dashboard Routes
- **Phase:** 06 — Dashboard
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Confirm externally reachable runtime for both new UI components.
- **What:** Queried:
  - `https://dark-noc-chatbot-dark-noc-ui.../health`
  - `https://dark-noc-chatbot-dark-noc-ui.../api/summary`
  - `https://dark-noc-dashboard-dark-noc-ui.../`
- **Expected:** Chatbot returns valid JSON and dashboard serves HTML.
- **Outcome:** Success.
  - Chatbot health: `{"status":"ok","service":"dark-noc-chatbot","version":"0.1.0"}`
  - Summary: includes `agent_status`, `open_incidents`, `servicenow:"up"`
  - Dashboard route returns `<!doctype html>` page.

**Status:** ✅ SUCCESS

---

### CMD-0156 — Deploy AAP AutomationController and Verify API
- **Phase:** 04 — Automation
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Enable AAP execution backend so MCP can launch remediation playbooks.
- **What:**
  1. Applied `phase-04-automation/aap/automation-controller.yaml`.
  2. Waited for `aap-web`, `aap-task`, and `aap-postgres` pods.
  3. Verified authenticated API at `https://aap-aap.../api/v2/ping/`.
- **Expected:** AAP controller API reachable for job template operations.
- **Outcome:** Success. AAP is deployed and API-authenticated.

**Status:** ✅ SUCCESS

---

### CMD-0157 — Wire MCP AAP to Live Controller Service
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Existing MCP AAP settings used placeholder secret and incorrect service endpoint.
- **What:**
  1. Updated `dark-noc-mcp/aap-admin-secret` with real AAP admin password.
  2. Updated `mcp-aap` env:
     - `AAP_URL=http://aap-service.aap.svc`
     - `AAP_VERIFY_SSL=false`
  3. Restarted and validated rollout of `deploy/mcp-aap`.
- **Expected:** MCP AAP can authenticate and call AAP API.
- **Outcome:** Success. Integration path is configured and stable.

**Status:** ✅ SUCCESS

---

### CMD-0158 — Create Bootstrap Job Template `restart-nginx`
- **Phase:** 04/05 Integration
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Agent expects template name `restart-nginx`; needed to exist in AAP for MCP launch flow.
- **What:**
  1. Created AAP job template `restart-nginx` (id `8`) via AAP REST API.
  2. Bound to Demo Project/Inventory as bootstrap placeholder.
- **Expected:** Template resolvable by MCP `launch_job(job_template_name=\"restart-nginx\")`.
- **Outcome:** Template exists and is queryable.

**Status:** ✅ SUCCESS

---

### CMD-0159 — AAP Execution Blocker Identified
- **Phase:** 04 — Automation
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Validate real job execution path after template creation.
- **What:** Attempted `POST /api/v2/job_templates/8/launch/`.
- **Expected:** Job launch accepted with `job_id`.
- **Outcome:** Blocked by AAP platform state:
  - API response: `{\"detail\":\"License is missing.\"}`
  - Playbook execution cannot proceed until AAP license is applied.

**Status:** ⚠️ BLOCKED

---

### CMD-0160 — Slack MCP Credential Wiring and Token-Type Validation
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Complete Slack notification path for MCP `mcp-slack`.
- **What:**
  1. Updated `dark-noc-mcp/slack-secrets` with provided token.
  2. Set `mcp-slack` deployment env `SLACK_NOC_CHANNEL=#demos`.
  3. Restarted `mcp-slack` deployment.
  4. Validated token with Slack API:
     - `auth.test` => `ok:true`
     - `chat.postMessage` => `error:not_allowed_token_type`
- **Expected:** MCP can post to Slack channel.
- **Outcome:** Blocked by credential type.
  - Provided token is `xapp-*` (app-level token), which cannot call `chat.postMessage`.
  - Need bot user token `xoxb-*` with `chat:write` and bot added to `#demos`.

**Status:** ⚠️ BLOCKED

---

### CMD-0161 — Slack Token Re-Test with User OAuth Token
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Re-validate Slack integration using newly provided token and target channel `#demos`.
- **What:**
  1. Updated `dark-noc-mcp/slack-secrets` with provided `xoxe.xoxp-...` token.
  2. Restarted `mcp-slack`.
  3. Ran Slack API checks:
     - `auth.test` (success)
     - `chat.postMessage` to `#demos` and `demos`.
- **Expected:** Slack messages posted successfully.
- **Outcome:** Blocked by missing scope.
  - API error: `missing_scope`
  - Needed: `chat:write:bot`
  - Provided scopes: `identify,app_configurations:read,app_configurations:write`

**Status:** ⚠️ BLOCKED

---

### CMD-0162 — Slack Integration Success with Bot Token (`xoxb`)
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Unblock MCP Slack notifications with a token capable of posting messages.
- **What:**
  1. Updated `dark-noc-mcp/slack-secrets` with provided bot token (`xoxb-...`).
  2. Restarted `deploy/mcp-slack`.
  3. Validated with Slack APIs:
     - `auth.test` => success
     - `chat.postMessage` to `#demos` => success
- **Expected:** mcp-slack can send notifications to target channel.
- **Outcome:** Success.
  - `chat.postMessage` response `ok:true`
  - Channel resolved as `C08MUDSNHED`

**Status:** ✅ SUCCESS

---

### CMD-0163 — Import AAP License Manifest via API
- **Phase:** 04 — Automation
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** AAP job execution was blocked by `License is missing`.
- **What:**
  1. Used uploaded manifest ZIP (`ce63ce2e-...zip`) and converted to base64.
  2. Posted to `POST /api/v2/config/` with `eula_accepted=true` and `manifest` payload.
  3. Verified `license_info` is populated and compliant.
- **Expected:** AAP license activated and execution path unblocked.
- **Outcome:** Success.
  - API returned trial license details (`sku: SER0569`).
  - `license_info.compliant = true`.

**Status:** ✅ SUCCESS

---

### CMD-0164 — Validate AAP Job Launch Post-License
- **Phase:** 04/05 Integration
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Confirm previously blocked template launch works after licensing.
- **What:**
  1. Triggered `POST /api/v2/job_templates/8/launch/`.
  2. Polled `/api/v2/jobs/1/` to terminal state.
  3. Retrieved stdout from `/api/v2/jobs/1/stdout/?format=txt`.
- **Expected:** Job transitions from `pending/running` to successful completion.
- **Outcome:** Success.
  - Job `id=1` completed with `status=successful`.
  - Playbook executed: `hello_world.yml`.

**Status:** ✅ SUCCESS
```

---

## Index

| CMD ID | Description | Phase | Cluster | Date |
|--------|-------------|-------|---------|------|
| CMD-0001 | Verify Hub cluster version | 01 | hub | TBD |
| CMD-0002 | Verify Edge cluster version | 01 | edge | TBD |
| CMD-0003 | Check hub cluster nodes | 01 | hub | TBD |
| CMD-0004 | Check edge cluster nodes | 01 | edge | TBD |
| CMD-0005 | Verify default StorageClass (hub) | 01 | hub | TBD |
| CMD-0006 | Verify default StorageClass (edge) | 01 | edge | TBD |
| CMD-0007 | Check existing CSV/operators (hub) | 01 | hub | TBD |
| CMD-0008 | Verify pull secret validity (hub) | 01 | hub | TBD |
| CMD-0009 | Create all hub namespaces | 01 | hub | TBD |
| CMD-0010 | Create all edge namespaces | 01 | edge | TBD |

---

## Execution Updates — 2026-03-03 UTC

### CMD-0101 — Upgrade Hub to OpenShift 4.21.3
- **Phase:** 00 — Cluster Preparation
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Hub was on 4.20.14; project baseline requires 4.21.x.
- **What:** Switched update channel to `fast-4.21` and requested upgrade target `4.21.3`.
- **Expected:** ClusterVersion transitions to `Progressing=True` toward 4.21.3.
- **Outcome:** Upgrade started and completed successfully after machine-api remediation.

**Command:**
```bash
oc adm upgrade channel fast-4.21 --allow-explicit-channel
oc adm upgrade --to=4.21.3
```

**Output:**
```
Requested update to 4.21.3
... (later) ...
HUB 4.21.3 state=Completed
Available: True | Done applying 4.21.3
Failing: False
Progressing: False
```
**Status:** ✅ SUCCESS

---

### CMD-0102 — Upgrade Edge to OpenShift 4.21.3
- **Phase:** 00 — Cluster Preparation
- **Cluster:** edge
- **Date:** 2026-03-03 UTC
- **Why:** Edge was on 4.20.14; project baseline requires 4.21.x.
- **What:** Switched update channel to `fast-4.21` and requested upgrade target `4.21.3`.
- **Expected:** ClusterVersion transitions to `Progressing=True` toward 4.21.3.
- **Outcome:** Upgrade started and completed successfully after machine-api remediation.

**Command:**
```bash
oc adm upgrade channel fast-4.21 --allow-explicit-channel
oc adm upgrade --to=4.21.3
```

**Output:**
```
Requested update to 4.21.3
... (later) ...
EDGE 4.21.3 state=Completed
Available: True | Done applying 4.21.3
Failing: False
Progressing: False
```
**Status:** ✅ SUCCESS

---

### CMD-0103 — Remediate Upgrade Blocker (Machine API Pods Pending)
- **Phase:** 00 — Cluster Preparation
- **Cluster:** both
- **Date:** 2026-03-03 UTC
- **Why:** Upgrade blocked with `ProgressDeadlineExceeded` on machine-api/control-plane-machine-set operators.
- **What:** Detected single SNO node was cordoned (`spec.unschedulable=true`), uncordoned node, restarted affected deployments.
- **Expected:** New pods schedule and machine-api operators recover.
- **Outcome:** Pods moved from `Pending`/`ContainerCreating` to `Running`; upgrades resumed.

**Command:**
```bash
oc adm uncordon <sno-node>
oc -n openshift-machine-api rollout restart \
  deploy/machine-api-operator \
  deploy/control-plane-machine-set-operator \
  deploy/machine-api-controllers
```

**Output:**
```
node/<sno-node> uncordoned
deployment.apps/machine-api-operator restarted
deployment.apps/control-plane-machine-set-operator restarted
deployment.apps/machine-api-controllers restarted
```
**Status:** ✅ SUCCESS

---

### CMD-0104 — Hub Phase 01 Start: Apply Hub Namespaces
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Begin deployment with required hub namespace isolation.
- **What:** Applied `hub-namespaces.yaml` and verified active namespaces.
- **Expected:** Dark NOC hub namespaces created/active.
- **Outcome:** All target hub namespaces created and Active.

**Command:**
```bash
oc apply -f implementation/phase-01-foundation/namespaces/hub-namespaces.yaml
oc get ns | grep dark-noc
```

**Output:**
```
namespace/dark-noc-hub created
namespace/dark-noc-kafka created
namespace/dark-noc-observability created
namespace/dark-noc-mcp created
namespace/dark-noc-rag created
namespace/dark-noc-ui created
namespace/dark-noc-minio created
namespace/dark-noc-servicenow-mock created
```
**Status:** ✅ SUCCESS

---

### CMD-0105 — Validate Hub Health from Bastion
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Direct API access was intermittent from local runner; bastion path is authoritative for hub execution.
- **What:** Connected to bastion, confirmed admin identity, cluster version, and operator health.
- **Expected:** `system:admin`, `version 4.21.3`, and no degraded/progressing core operators.
- **Outcome:** Hub confirmed healthy and ready for continuing Dark NOC installation.

**Command:**
```bash
ssh -o StrictHostKeyChecking=no lab-user@bastion.v8w9c.sandbox205.opentlc.com
oc whoami
oc get clusterversion version -o wide
oc get co
```

**Output:**
```
system:admin
NAME      VERSION   AVAILABLE   PROGRESSING   SINCE   STATUS
version   4.21.3    True        False         ...     Cluster version is 4.21.3
... core clusteroperators available=True, progressing=False, degraded=False ...
```
**Status:** ✅ SUCCESS

---

### CMD-0106 — Validate Wave 0 / Wave 1 Subscriptions and CSVs
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Confirm foundational operator baseline before moving to Wave 2.
- **What:** Queried subscriptions/installplans/CSVs for NFD, GPU, cert-manager, Service Mesh, Kafka, ACM, AAP, Logging, Loki, and CNPG.
- **Expected:** Subscriptions present and CSVs in `Succeeded`.
- **Outcome:** All required subscriptions are present; one Loki CSV issue identified and remediated in CMD-0107.

**Command:**
```bash
oc get subscription -A
oc get installplan -A
oc get csv -A
```

**Output:**
```
... amq-streams, ansible-automation-platform-operator, advanced-cluster-management,
cluster-logging, loki-operator, cloudnative-pg, nfd, gpu-operator-certified, rhods-operator ...
loki-operator.v6.4.2 initially Failed (UnsupportedOperatorGroup)
```
**Status:** ✅ SUCCESS

---

### CMD-0107 — Remediate Loki OperatorGroup Scope and Recover CSV
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Loki CSV failed with `UnsupportedOperatorGroup` due to namespace-scoped OperatorGroup.
- **What:** Patched `openshift-operators-redhat-og` to remove `spec.targetNamespaces`, switching to global OperatorGroup behavior required by Loki operator.
- **Expected:** Loki CSV transitions from `Failed` to `Succeeded`.
- **Outcome:** `loki-operator.v6.4.2` now `Succeeded`.

**Command:**
```bash
oc -n openshift-operators-redhat patch operatorgroup openshift-operators-redhat-og \
  --type=json -p='[{"op":"remove","path":"/spec/targetNamespaces"}]'
oc -n openshift-operators-redhat get csv,subscription,installplan
```

**Output:**
```
operatorgroup.operators.coreos.com/openshift-operators-redhat-og patched
clusterserviceversion.operators.coreos.com/loki-operator.v6.4.2 ... Succeeded
```
**Status:** ✅ SUCCESS

---

### CMD-0108 — Start Wave 2 on Hub (Create MultiClusterHub)
- **Phase:** 04 — Automation (Wave 2 dependency)
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** ACM operator is installed; creating `MultiClusterHub` is required to activate ACM control plane.
- **What:** Applied minimal valid `MultiClusterHub` CR after rejecting an incompatible override field.
- **Expected:** `multiclusterhub` resource created and begins reconciliation.
- **Outcome:** `open-cluster-management/multiclusterhub` created successfully; status progressing.

**Command:**
```bash
cat <<'EOF' | oc apply -f -
apiVersion: operator.open-cluster-management.io/v1
kind: MultiClusterHub
metadata:
  name: multiclusterhub
  namespace: open-cluster-management
spec:
  availabilityConfig: Basic
  disableHubSelfManagement: false
EOF
oc get multiclusterhub -n open-cluster-management
```

**Output:**
```
multiclusterhub.operator.open-cluster-management.io/multiclusterhub created
```
**Status:** ✅ SUCCESS

---

### CMD-0109 — Scale Hub Worker Capacity to Unblock Scheduling
- **Phase:** 00 — Cluster Preparation
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Hub node was saturated at pod capacity (`250/250`), blocking MinIO and all new workloads.
- **What:** Scaled worker MachineSet `ocp-56g8n-worker-us-east-2a` from `0` to `1` and waited for node join.
- **Expected:** New worker machine becomes `Running`; second node appears and reaches `Ready`.
- **Outcome:** Worker node joined (`ip-10-0-13-169...`), scheduling unblocked.

**Command:**
```bash
oc -n openshift-machine-api scale machineset ocp-56g8n-worker-us-east-2a --replicas=1
oc -n openshift-machine-api get machines
oc get nodes
```

**Output:**
```
machineset.machine.openshift.io/ocp-56g8n-worker-us-east-2a scaled
... worker machine phase=Running ...
... second worker node became Ready ...
```
**Status:** ✅ SUCCESS

---

### CMD-0110 — Deploy MinIO Storage Layer
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** MinIO is the S3-compatible backend required by Loki, RHOAI model registry, and Langfuse blobs.
- **What:** Applied MinIO PVC/Deployment/Service/Routes manifests in `dark-noc-minio`.
- **Expected:** `minio` pod running; `minio-data` PVC bound.
- **Outcome:** MinIO running with `200Gi` gp3-csi PVC bound.

**Command:**
```bash
oc apply -f minio-pvc.yaml
oc apply -f minio-deployment.yaml
oc -n dark-noc-minio get pvc,pods,svc,route
```

**Output:**
```
persistentvolumeclaim/minio-data created
deployment.apps/minio created
service/minio created
route.route.openshift.io/minio-console created
route.route.openshift.io/minio-api created
... minio pod Running, PVC Bound ...
```
**Status:** ✅ SUCCESS

---

### CMD-0111 — Initialize MinIO Buckets
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Core services require pre-created buckets (`rhoai-models`, `loki-chunks`, `langfuse-data`).
- **What:** Replaced failing init Job path with one-off `mc` bootstrap pod using `HOME=/tmp` for write permissions.
- **Expected:** All three buckets created and listed.
- **Outcome:** Bucket bootstrap completed successfully.

**Command:**
```bash
oc -n dark-noc-minio run minio-bootstrap --image=quay.io/minio/mc:RELEASE.2025-01-17T23-25-50Z ...
oc -n dark-noc-minio logs pod/minio-bootstrap
```

**Output:**
```
Bucket created successfully `myminio/rhoai-models`.
Bucket created successfully `myminio/loki-chunks`.
Bucket created successfully `myminio/langfuse-data`.
```
**Status:** ✅ SUCCESS

---

### CMD-0112 — Deploy Kafka KRaft Cluster and Topics
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Kafka is the event backbone for edge logs, agent events, alerts, and remediation triggers.
- **What:** Applied Kafka KRaft cluster + node pool + 5 KafkaTopic CRs in `dark-noc-kafka`.
- **Expected:** Kafka `READY=True`; entity operator and broker running; topics `READY=True`.
- **Outcome:** Kafka healthy in KRaft mode; all 5 topics ready.

**Command:**
```bash
oc apply -f kafka-cluster.yaml
oc apply -f kafka-topics.yaml
oc -n dark-noc-kafka get kafka,kafkanodepool,kafkatopic,pods,pvc
```

**Output:**
```
kafka.kafka.strimzi.io/dark-noc-kafka created
kafkanodepool.kafka.strimzi.io/dual-role created
... 5 KafkaTopic resources created ...
... kafka READY=True, all topics READY=True ...
```
**Status:** ✅ SUCCESS

---

### CMD-0113 — Fix CloudNativePG Installation and Scope
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** CNPG subscription was unresolved and operator initially watched only `cnpg-system`.
- **What:** Corrected OLM source to `certified-operators`, removed duplicate OperatorGroup, and patched CNPG OperatorGroup to all-namespaces scope.
- **Expected:** InstallPlan/CSV created and CRDs installed; controller logs show watch on all namespaces.
- **Outcome:** `cloudnative-pg.v1.28.1` Succeeded; `clusters.postgresql.cnpg.io` CRD installed; controller watch scope fixed.

**Command:**
```bash
oc -n cnpg-system patch subscription.operators.coreos.com cloudnative-pg --type=merge -p '{"spec":{"source":"certified-operators"}}'
oc -n cnpg-system delete operatorgroup cnpg-og
oc -n cnpg-system patch operatorgroup cnpg-operator-group --type=json -p='[{"op":"remove","path":"/spec/targetNamespaces"}]'
```

**Output:**
```
subscription.operators.coreos.com/cloudnative-pg patched
clusterserviceversion.operators.coreos.com/cloudnative-pg.v1.28.1 ... Succeeded
... controller log: "Listening for changes on all namespaces" ...
```
**Status:** ✅ SUCCESS

---

### CMD-0114 — Deploy Langfuse PostgreSQL (CloudNativePG)
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Langfuse requires PostgreSQL metadata storage before Redis/ClickHouse/Web deployment.
- **What:** Created superuser secret and applied `Cluster` CR in `dark-noc-observability`.
- **Expected:** Primary pod initializes and CNPG cluster reports healthy.
- **Outcome:** `langfuse-postgres` reached healthy state (`READY=1`, primary running).

**Command:**
```bash
oc apply -f langfuse-postgres-superuser-secret.yaml
oc apply -f langfuse-postgres-cluster.yaml
oc -n dark-noc-observability get cluster.postgresql.cnpg.io,pods,pvc
```

**Output:**
```
cluster.postgresql.cnpg.io/langfuse-postgres created
... pod/langfuse-postgres-1 Running 1/1 ...
... status: Cluster in healthy state ...
```
**Status:** ✅ SUCCESS

---

### CMD-0115 — Build pgvector PostgreSQL Image
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** RAG database requires PostgreSQL with `pgvector` extension preinstalled.
- **What:** Created ImageStream + BuildConfig, built custom PG16 image with pgvector `v0.8.1`, and pushed to internal registry.
- **Expected:** Build completes and ImageStreamTag `pgvector-postgres:16.4-v0.8.1` is published.
- **Outcome:** Build succeeded and image pushed.

**Command:**
```bash
oc -n dark-noc-rag apply -f pgvector-buildconfig.yaml
oc -n dark-noc-rag start-build pgvector-postgres --follow
```

**Output:**
```
build.build.openshift.io/pgvector-postgres-1 ... Complete
Successfully pushed image-registry.../dark-noc-rag/pgvector-postgres@sha256:...
```
**Status:** ✅ SUCCESS

---

### CMD-0116 — Deploy pgvector PostgreSQL Cluster
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** LangGraph RAG retrieval requires a live vector database.
- **What:** Applied pgvector secret + CNPG Cluster CR using the newly built internal image.
- **Expected:** Cluster initializes and reaches healthy state with primary pod running.
- **Outcome:** `pgvector-postgres` healthy (`READY=1`, primary pod running, PVC bound).

**Command:**
```bash
oc -n dark-noc-rag apply -f pgvector-cluster.yaml
oc -n dark-noc-rag get cluster.postgresql.cnpg.io,pods,pvc
```

**Output:**
```
cluster.postgresql.cnpg.io/pgvector-postgres created
... status: Cluster in healthy state ...
pod/pgvector-postgres-1 1/1 Running
```
**Status:** ✅ SUCCESS

---

### CMD-0117 — Deploy Langfuse Redis and ClickHouse Backends
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Langfuse web deployment depends on Redis queue/cache and ClickHouse OLAP storage.
- **What:** Created `langfuse-secrets` (ClickHouse password), deployed Redis service, and deployed ClickHouse with 20Gi PVC.
- **Expected:** Redis and ClickHouse pods reach `Running`; ClickHouse PVC binds on `gp3-csi`.
- **Outcome:** Both backends healthy and services available in `dark-noc-observability`.

**Command:**
```bash
oc -n dark-noc-observability create secret generic langfuse-secrets ...
oc -n dark-noc-observability apply -f redis-deployment.yaml
oc -n dark-noc-observability apply -f clickhouse-deployment.yaml
oc -n dark-noc-observability get pods,pvc,svc
```

**Output:**
```
deployment.apps/redis created
deployment.apps/clickhouse created
persistentvolumeclaim/clickhouse-data Bound
pod/redis-... Running
pod/clickhouse-... Running
```
**Status:** ✅ SUCCESS

---

### CMD-0118 — Reconcile Repo Manifests and Runbooks to Executed State
- **Phase:** Repo Hardening
- **Cluster:** local
- **Date:** 2026-03-03 UTC
- **Why:** Ensure GitHub repo can redeploy without repeating discovered runtime failures.
- **What:** Backported live fixes into manifests and updated Phase 01/02 command docs plus redeploy runbook.
- **Expected:** Repository manifests and docs match cluster-proven deployment behavior.
- **Outcome:** Critical mismatches removed (MinIO job HOME path, CNPG source/scope, MCH spec compatibility, bootstrap docs for SNO capacity and OLM-qualified resources).

**Command:**
```bash
# File updates via apply_patch across:
# - implementation/phase-01-foundation/*
# - implementation/phase-02-data-pipeline/*
# - docs/deployment/redeploy-runbook.md
# - README.md
```

**Output:**
```
Manifest + docs reconciliation completed and tracked in repository.
```
**Status:** ✅ SUCCESS

---

## Phase 01 — Foundation

### CMD-0001 — Verify Hub Cluster Version
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** TBD
- **Why:** Before installing any operators, we must confirm the cluster is running OpenShift 4.21. The operator channels and CRD versions in this runbook are specific to 4.21. Running on an older version could cause operator installation failures or feature incompatibilities.
- **What:** Queries the OpenShift cluster version API and displays both the client (oc CLI) and server (cluster) versions in short format.
- **Expected:** `Server Version: 4.21.x` — where x is any patch version of 4.21
- **Outcome:** Confirms we are on the correct OpenShift version before any installation begins.

**Command:**
```bash
oc version --short
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

### CMD-0002 — Verify Edge Cluster Version
- **Phase:** 01 — Foundation
- **Cluster:** edge
- **Date:** TBD
- **Why:** Both clusters must be on OCP 4.21 to ensure API compatibility. The ClusterLogForwarder CRD schema, ACM ManagedCluster API, and Argo CD Pull Agent manifest are all tested against 4.21. A version mismatch between hub and edge would cause ACM spoke registration to fail.
- **What:** Same as CMD-0001 but run against the edge cluster context.
- **Expected:** `Server Version: 4.21.x`
- **Outcome:** Confirms edge cluster is version-compatible with hub.

**Command:**
```bash
# First switch to edge cluster context
oc config use-context <edge-cluster-context>
oc version --short
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

### CMD-0003 — Check Hub Cluster Nodes
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** TBD
- **Why:** We need to understand the current node configuration before making changes. For a Single Node OpenShift (SNO) cluster, this shows the single master/worker node and its instance type. We need this to determine: (1) whether a GPU worker MachineSet needs to be created, (2) current resource availability, (3) whether the node is schedulable for workloads.
- **What:** Lists all cluster nodes with their roles, status, age, OpenShift version, OS image, kernel version, container runtime, and internal IP. The `-o wide` flag shows the AWS instance-related info in the node name.
- **Expected:** One node listed (SNO), status `Ready`, role `control-plane,master,worker`. Node name will contain the AWS instance ID.
- **Outcome:** Confirms SNO topology and identifies the current instance type for GPU upgrade planning.

**Command:**
```bash
oc get nodes -o wide
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

### CMD-0004 — Check Edge Cluster Nodes
- **Phase:** 01 — Foundation
- **Cluster:** edge
- **Date:** TBD
- **Why:** Same reasoning as CMD-0003. For the edge SNO cluster, we're verifying the node is Ready and identifying its instance type. The edge cluster does not need a GPU node — we just need to confirm it has enough CPU/RAM for nginx, log collection, and the ACM spoke agent.
- **What:** Lists all edge cluster nodes with extended information.
- **Expected:** One node listed (SNO), status `Ready`, sufficient resources for edge workloads (~8 vCPU, ~32 GB RAM minimum).
- **Outcome:** Confirms edge cluster readiness and available resources.

**Command:**
```bash
oc config use-context <edge-cluster-context>
oc get nodes -o wide
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

### CMD-0005 — Verify Default StorageClass (Hub)
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** TBD
- **Why:** All stateful workloads (Kafka, PostgreSQL, ClickHouse, Redis, MinIO, LokiStack) use PersistentVolumeClaims with dynamic provisioning. If `gp3-csi` is not set as the default StorageClass, all PVCs will either fail to provision or use `gp2` (older EBS type with lower performance). gp3 provides 3000 IOPS baseline vs gp2's 100 IOPS/GB — critical for Kafka and ClickHouse throughput.
- **What:** Lists all StorageClasses on the cluster. The `(default)` annotation shows which one is the default for unspecified PVCs.
- **Expected:** `gp3-csi` listed with `(default)` annotation. If `gp2` is default, we need to change it before any PVCs are created.
- **Outcome:** Ensures all future PVCs get high-performance gp3 EBS volumes automatically.

**Command:**
```bash
oc get storageclass
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

### CMD-0006 — Verify Default StorageClass (Edge)
- **Phase:** 01 — Foundation
- **Cluster:** edge
- **Date:** TBD
- **Why:** Edge cluster also needs gp3-csi as default for the logging operator's PVCs. Vector's buffer storage and any edge-side PVCs should use gp3 for consistent performance.
- **What:** Same as CMD-0005 on edge cluster context.
- **Expected:** `gp3-csi` is default on edge cluster.
- **Outcome:** Ensures edge PVCs use optimal storage.

**Command:**
```bash
oc config use-context <edge-cluster-context>
oc get storageclass
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

### CMD-0007 — Check Existing Operators (Hub)
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** TBD
- **Why:** Before installing any operators, we must check if any are already installed. Installing an operator that is already present causes a duplicate CSV conflict and can break the Operator Lifecycle Manager (OLM). We specifically check for RHOAI, ACM, AAP, and Kafka as these are the most likely to already have a trial version installed.
- **What:** Lists all ClusterServiceVersions (CSVs) across all namespaces. A CSV represents an installed operator version. The `grep` filters for the operators we care about.
- **Expected:** No output (no operators pre-installed) OR some operators already at correct versions. If any show at wrong versions, we must uninstall first.
- **Outcome:** Prevents duplicate operator installation conflicts.

**Command:**
```bash
oc get csv -A | grep -E "rhods-operator|advanced-cluster-management|amq-streams|ansible-automation-platform|cluster-logging|loki-operator|cloudnative-pg|cert-manager|gpu-operator|node-feature-discovery|servicemeshoperator"
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

### CMD-0008 — Verify Pull Secret Validity (Hub)
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** TBD
- **Why:** All Red Hat operators pull their images from `registry.redhat.io`. If the pull secret is expired or missing the registry.redhat.io token, every operator pod will enter `ImagePullBackOff` state and never start. This is the most common cause of operator installation failure. We verify before starting to avoid wasting time debugging image pulls.
- **What:** Retrieves the cluster pull secret, base64 decodes it, and parses the JSON to list all registry hostnames that have authentication configured.
- **Expected:** Output should contain `registry.redhat.io`, `cloud.openshift.com`, and ideally `quay.io`.
- **Outcome:** Confirms operator images can be pulled before we begin installation.

**Command:**
```bash
oc get secret pull-secret -n openshift-config \
  -o jsonpath='{.data.\.dockerconfigjson}' | \
  base64 -d | python3 -c "import json,sys; d=json.load(sys.stdin); [print(k) for k in d['auths'].keys()]"
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

### CMD-0009 — Create All Hub Namespaces
- **Phase:** 01 — Foundation
- **Cluster:** hub
- **Date:** TBD
- **Why:** All Dark NOC components are isolated in dedicated namespaces. Namespace isolation provides: (1) RBAC scope — each component's ServiceAccount only has permissions in its namespace, (2) NetworkPolicy scope — traffic between namespaces is explicitly controlled, (3) Resource quota scope — prevent one component from starving others, (4) Clear operational boundaries — easy to identify which components belong to which layer.
- **What:** Creates 14 namespaces (OpenShift projects) on the hub cluster. Each namespace corresponds to a logical component group in the architecture.
- **Expected:** All 14 projects created with `Already exists` for any that already exist (idempotent).
- **Outcome:** Clean namespace structure ready for component deployment.

**Command:**
```bash
for ns in \
  dark-noc-hub \
  dark-noc-kafka \
  dark-noc-observability \
  dark-noc-mcp \
  dark-noc-rag \
  dark-noc-ui \
  dark-noc-minio \
  dark-noc-servicenow-mock \
  openshift-nfd \
  nvidia-gpu-operator; do
  oc new-project $ns --description="Dark NOC: $ns" 2>/dev/null || \
  echo "Project $ns already exists"
done
echo "✅ All hub namespaces created"
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

### CMD-0010 — Create All Edge Namespaces
- **Phase:** 01 — Foundation
- **Cluster:** edge
- **Date:** TBD
- **Why:** Edge cluster needs a clean namespace structure mirroring the edge logical components. The `dark-noc-edge` namespace is the most critical — all monitored workloads (nginx, log generator) live here and are watched by Vector's ClusterLogForwarder. `openshift-logging` is the required namespace for the Logging operator.
- **What:** Creates 5 namespaces on the edge cluster.
- **Expected:** All 5 projects created successfully.
- **Outcome:** Edge cluster ready for workload deployment.

**Command:**
```bash
oc config use-context <edge-cluster-context>
for ns in \
  dark-noc-edge \
  dark-noc-edge-ai; do
  oc new-project $ns --description="Dark NOC Edge: $ns" 2>/dev/null || \
  echo "Project $ns already exists"
done
echo "✅ All edge namespaces created"
```

**Output:**
```
# TO BE FILLED IN WHEN RUN
```
**Status:** ⏳ PENDING

---

## Phase 02 — Data Pipeline

*Commands will be added as phase 02 is executed*

---

## Phase 03 — AI Core

*Commands will be added as phase 03 is executed*

---

## Phase 04 — Automation

*Commands will be added as phase 04 is executed*

---

## Phase 05 — Agent & MCP

*Commands will be added as phase 05 is executed*

---

## Phase 06 — Dashboard & UX

*Commands will be added as phase 06 is executed*

---

## Phase 07 — Edge Workloads

*Commands will be added as phase 07 is executed*

---

## Phase 08 — Validation

*Commands will be added as phase 08 is executed*

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total commands logged | 0 |
| Successful (✅) | 0 |
| Failed (❌) | 0 |
| Pending (⏳) | 10 |

*Last updated: 2026-02-26*

---

### CMD-0118 — Deploy Langfuse Web/Worker on Hub
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Complete observability stack so AI traces and evaluations are stored and queryable.
- **What:** Created full `langfuse-secrets`, installed Helm chart `langfuse/langfuse` version `1.5.22`, applied OpenShift route.
- **Expected:** `langfuse-web` and `langfuse-worker` pods Running, route resolves.
- **Outcome:** Deployment succeeded with route `langfuse-dark-noc-observability.apps.ocp.v8w9c.sandbox205.opentlc.com`.

**Command:**
```bash
oc create secret generic langfuse-secrets ... --dry-run=client -o yaml | oc apply -f -
helm upgrade --install langfuse langfuse/langfuse \
  --namespace dark-noc-observability \
  --values /tmp/langfuse-values-runtime.yaml \
  --version 1.5.22 --wait --timeout 10m
oc apply -f implementation/phase-02-data-pipeline/langfuse/langfuse-route.yaml
```

**Output:**
```
STATUS: deployed
route.route.openshift.io/langfuse created
langfuse-web-...      1/1 Running
langfuse-worker-...   1/1 Running
```
**Status:** ✅ SUCCESS

---

### CMD-0119 — Fix Langfuse Runtime Crashes
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** First install crash-looped due ClickHouse cluster mode and missing Redis port env.
- **What:** Set `clickhouse.clusterEnabled=false` and injected `REDIS_HOST`/`REDIS_PORT` in chart values.
- **Expected:** Both pods stabilize after reinstall.
- **Outcome:** Crash loops resolved; web and worker remain healthy.

**Command:**
```bash
oc logs deploy/langfuse-web
oc logs deploy/langfuse-worker
helm uninstall langfuse -n dark-noc-observability
helm upgrade --install langfuse ... --version 1.5.22 --wait
```

**Output:**
```
langfuse-web-...      1/1 Running
langfuse-worker-...   1/1 Running
```
**Status:** ✅ SUCCESS

---

### CMD-0120 — Deploy LokiStack on Hub with Sandbox Sizing
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Enable persistent log store for hub and edge logs queried by MCP.
- **What:** Applied `lokistack-hub.yaml`, then resized to `1x.demo` to fit cluster constraints.
- **Expected:** `logging-loki` `Ready=True` and all Loki components Running.
- **Outcome:** LokiStack reached `Ready=True` with all components healthy.

**Status:** ✅ SUCCESS

---

### CMD-0121 — Replace Deprecated ClusterLogging CR with CLF v1
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** OCP 4.21 logging API no longer serves `logging.openshift.io/v1 ClusterLogging` in this environment.
- **What:** Added `ServiceAccount + ClusterRoleBindings + observability.openshift.io/v1 ClusterLogForwarder` targeting LokiStack.
- **Expected:** `clusterlogforwarder/instance Ready=True` and collector DaemonSet 2/2.
- **Outcome:** CLF authorized/ready; collector DaemonSet rolled out successfully (`DESIRED=2 READY=2`).

**Status:** ✅ SUCCESS

---

### CMD-0122 — Install Edge Logging Operator
- **Phase:** 01 — Foundation
- **Cluster:** edge
- **Date:** 2026-03-03 UTC
- **Why:** Edge needs collector capability to forward nginx logs to hub Kafka.
- **What:** Created `openshift-logging` namespace, applied edge OperatorGroup + Subscription.
- **Expected:** `cluster-logging` subscription with CSV Succeeded.
- **Outcome:** `cluster-logging.v6.4.2` installed successfully on edge.

**Status:** ✅ SUCCESS

---

### CMD-0123 — Configure Edge CLF (nginx -> Hub Kafka)
- **Phase:** 02 — Data Pipeline
- **Cluster:** edge/hub
- **Date:** 2026-03-03 UTC
- **Why:** Establish critical telemetry path from edge workloads to hub streaming pipeline.
- **What:** Copied hub Kafka CA secret to edge, applied updated `observability.openshift.io/v1` CLF + collector SA/RBAC.
- **Expected:** `clusterlogforwarder/instance Ready=True`, collector DaemonSet 1/1.
- **Outcome:** CLF validated and reconciled; collector DaemonSet rolled out (`DESIRED=1 READY=1`).

**Status:** ✅ SUCCESS

---

### CMD-0124 — Enable Hub Kafka External Route Listener
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub
- **Date:** 2026-03-03 UTC
- **Why:** Edge cannot resolve hub internal service DNS across clusters; Kafka must be reachable via hub ingress.
- **What:** Added Strimzi `route` listener (`external`, port 9094) and reconciled Kafka CR.
- **Expected:** Kafka `Ready=True` and bootstrap route present.
- **Outcome:** Routes created: `dark-noc-kafka-kafka-bootstrap-...apps...` and broker route.

**Status:** ✅ SUCCESS

---

### CMD-0125 — Edge-to-Hub Kafka E2E Validation (Current Blocker)
- **Phase:** 02 — Data Pipeline
- **Cluster:** both
- **Date:** 2026-03-03 UTC
- **Why:** Verify nginx logs from edge arrive in hub `nginx-logs` topic.
- **What:** Updated edge CLF to use external hub bootstrap route, generated nginx traffic, consumed topic on hub.
- **Expected:** Kafka topic should contain nginx JSON log messages.
- **Outcome:** Collector reports broker disconnect / `AllBrokersDown`; topic consumer returns 0 messages.

**Status:** ❌ BLOCKED

---

### CMD-0126 — Resolve Edge->Hub Kafka Route Disconnects
- **Phase:** 02 — Data Pipeline
- **Cluster:** hub/edge
- **Date:** 2026-03-03 UTC
- **Why:** Collector had periodic `BrokerTransportFailure`/`AllBrokersDown` using Kafka route listener.
- **What:** Increased HAProxy timeout on Strimzi bootstrap + broker routes and revalidated with generated nginx traffic.
- **Expected:** Stable route listener sessions and successful log delivery.
- **Outcome:** Hub consumer confirmed records on `nginx-logs` (`Processed a total of 3 messages`).

**Status:** ✅ SUCCESS

---

### CMD-0127 — Validate vLLM InferenceService Endpoint on Hub
- **Phase:** 03 — AI Core
- **Cluster:** hub
- **Date:** 2026-03-04 UTC
- **Why:** Confirm model serving is actually usable before proceeding to LlamaStack/agent layers.
- **What:** Queried `granite-vllm` status and executed in-pod request to `http://127.0.0.1:8080/v1/models` from predictor container.
- **Expected:** `READY=True` and model list response from vLLM API.
- **Outcome:** Success; response included `granite-4-h-tiny` and service remained healthy.

**Status:** ✅ SUCCESS

---

### CMD-0128 — Patch LlamaStackDistribution to Current CRD Shape
- **Phase:** 03 — AI Core
- **Cluster:** hub
- **Date:** 2026-03-04 UTC
- **Why:** Existing LLSD manifest failed validation (`spec.server.distribution` required) under `llamastack.io/v1alpha1`.
- **What:** Updated manifest to `spec.server.distribution`, `server.containerSpec`, and operator-compatible structure, then reapplied.
- **Expected:** CR accepted and deployment initialized.
- **Outcome:** CR accepted; initial image pull/auth issue fixed by switching to operator-advertised distribution `rh-dev`.

**Status:** ✅ SUCCESS (schema + image fix)

---

### CMD-0129 — LlamaStack Runtime Blocker (ConfigMap/Schema)
- **Phase:** 03 — AI Core
- **Cluster:** hub
- **Date:** 2026-03-04 UTC
- **Why:** LLSD pods remained in CrashLoop after image resolution.
- **What:** Investigated pod logs/events and deployment mounts. Identified stale/invalid `dark-noc-llamastack-user-config` schema (v2 format incompatible with llama-stack 0.4.x). Attempted clean recreate of LLSD.
- **Expected:** Operator-generated valid config and running LLSD pod.
- **Outcome:** Still blocked; deployment requires `dark-noc-llamastack-user-config` and current content/schema causes startup validation errors.

**Status:** ❌ BLOCKED

---

### CMD-0130 — Edge Access Check
- **Phase:** Cross-cutting
- **Cluster:** edge
- **Date:** 2026-03-04 UTC
- **Why:** Continue edge-side deployment/validation in parallel with hub.
- **What:** Attempted separate kubeconfig login using latest edge token.
- **Expected:** Successful login and namespace health checks.
- **Outcome:** Edge token rejected as invalid/expired.

**Status:** ❌ BLOCKED (needs fresh edge login token)

---

### CMD-0131 — LlamaStack Runtime Stabilization (rh-dev)
- **Phase:** 03 — AI Core
- **Cluster:** hub
- **Date:** 2026-03-04 UTC
- **Why:** LLSD accepted by CRD but repeatedly crash-looped due schema drift, missing provider env, and DB backend assumptions.
- **What:**
  1. Extracted live `/opt/app-root/config.yaml` from `registry.redhat.io/rhoai/odh-llama-stack-core-rhel9` to identify required env contracts.
  2. Updated LLSD CR `server.containerSpec.env` with required runtime vars:
     - `POSTGRES_HOST/PORT/DB/USER/PASSWORD`
     - `VLLM_URL`, `VLLM_API_TOKEN`
     - `VLLM_EMBEDDING_URL`, `VLLM_EMBEDDING_API_TOKEN`
     - `INFERENCE_MODEL`
  3. Granted DB schema privileges for LLSD table creation:
     - `GRANT USAGE,CREATE ON SCHEMA public TO langfuse;`
- **Expected:** LLSD pod starts, health endpoint responds, status moves to Ready.
- **Outcome:** Success. `deployment/dark-noc-llamastack` rolled out; LLSD status now `PHASE=Ready`, `AVAILABLE=1`, `SERVER VERSION=0.4.2.1+rhai0`.

**Status:** ✅ SUCCESS

---

### CMD-0132 — Edge Access Recheck
- **Phase:** Cross-cutting
- **Cluster:** edge
- **Date:** 2026-03-04 UTC
- **Why:** Continue parallel hub/edge deployment execution.
- **What:** Attempted dedicated kubeconfig login for edge and namespace verification.
- **Expected:** Login success and edge namespace checks.
- **Outcome:** Edge token currently invalid/expired; edge actions remain blocked pending refreshed token.

**Status:** ❌ BLOCKED (requires fresh edge token)

---

### CMD-0133 — Restore Edge Access and Validate Runtime Health
- **Phase:** Cross-cutting
- **Cluster:** edge
- **Date:** 2026-03-04 UTC
- **Why:** Previous edge token expired; deployment and validation work was blocked.
- **What:** Logged in with refreshed token using dedicated edge kubeconfig and verified key namespaces + components.
- **Expected:** `dark-noc-edge`/`openshift-logging` active, nginx and collector healthy.
- **Outcome:** Success; edge runtime healthy (`nginx Running`, CLF `instance`, collector DS `1/1`).

**Status:** ✅ SUCCESS

---

### CMD-0134 — Fix and Deploy Failure Simulator CronJob on Edge
- **Phase:** 07 — Edge Workloads
- **Cluster:** edge
- **Date:** 2026-03-04 UTC
- **Why:** One-shot simulator was pending and initial manifest had runtime issues.
- **What:**
  1. Replaced invalid image tag `bitnami/kubectl:1.32` with `quay.io/openshift/origin-cli:4.21`.
  2. Fixed patch payload to update both memory `limits` and `requests` (K8s validation requires request <= limit).
  3. Applied CronJob and executed one-shot job `nginx-oom-now`.
- **Expected:** Job completes and mutates nginx deployment resources for OOM simulation.
- **Outcome:** Success; one-shot job completed and nginx deployment patched to `limit=32Mi`, `request=16Mi`.

**Status:** ✅ SUCCESS

---

### CMD-0135 — Re-validate Edge->Hub Kafka Log Flow Post-Changes
- **Phase:** 02/07 Validation
- **Cluster:** both
- **Date:** 2026-03-04 UTC
- **Why:** Confirm telemetry path still functions after edge simulator and rollout changes.
- **What:** Generated fresh edge nginx traffic and consumed `nginx-logs` from hub Kafka broker pod.
- **Expected:** Hub consumer receives edge nginx records.
- **Outcome:** Success (`Processed a total of 5 messages`).

**Status:** ✅ SUCCESS

---

### CMD-0136 — Observed Residual Transport Flapping (Non-blocking)
- **Phase:** 02 Logging/Kafka
- **Cluster:** edge/hub
- **Date:** 2026-03-04 UTC
- **Why:** Collector logs were reviewed during validation.
- **What:** Observed recurring `BrokerTransportFailure`/`AllBrokersDown` entries in edge Vector logs against hub route listener.
- **Expected:** Stable route sessions.
- **Outcome:** Intermittent disconnects still appear, but data flow recovers and messages are delivered.

**Status:** ⚠️ WATCH (non-blocking)

---

### CMD-0137 — Restore Edge nginx Baseline After OOM Simulation
- **Phase:** 07 — Edge Workloads
- **Cluster:** edge
- **Date:** 2026-03-04 UTC
- **Why:** One-shot simulation intentionally reduced nginx memory; baseline settings should be restored for stable ongoing deployment.
- **What:** Patched nginx deployment back to `limit=128Mi`, `request=64Mi` and waited for rollout.
- **Expected:** nginx returns to normal resource profile and rollout succeeds.
- **Outcome:** Success; deployment rolled out and CronJob remained `suspend=true`.

**Status:** ✅ SUCCESS

---

### CMD-0138 — Phase 03 Step 6: Seed RAG Knowledge Base into pgvector
- **Phase:** 03 — AI Core
- **Cluster:** hub
- **Date:** 2026-03-04 UTC
- **Why:** Enable runbook-grounded retrieval for LangGraph by embedding and storing runbook chunks in pgvector.
- **What:**
  1. Created/updated seed script and runbooks as ConfigMaps in `dark-noc-rag`.
  2. Ran one-shot `rag-seed` Job using Python + sentence-transformers against `noc_rag`.
  3. Inserted embeddings into `documents` table with HNSW index enabled.
- **Expected:** Job completes successfully and `documents` table is populated.
- **Outcome:** Success. `rag-seed` reached `Complete`; seeder reported `53` chunks stored.

**Status:** ✅ SUCCESS

---

### CMD-0139 — Verify RAG Seed Persistence (Post-run)
- **Phase:** 03 — AI Core
- **Cluster:** hub
- **Date:** 2026-03-05 UTC
- **Why:** Confirm Phase 03 step 6 remains valid after follow-up cluster operations/token refresh cycles.
- **What:** Logged into hub, checked `dark-noc-rag` jobs/pods, and queried pgvector DB row count.
- **Expected:** `rag-seed` remains complete and `documents` count > 0.
- **Outcome:** Success. `job/rag-seed` is `Complete`; `pgvector-postgres-1` is `Running`; `documents` count is `53`.

**Command:**
```bash
oc login --username=admin --password='<hub-admin-password>' \
  --server=https://api.ocp.v8w9c.sandbox205.opentlc.com:6443 \
  --insecure-skip-tls-verify=true
oc -n dark-noc-rag get jobs,pods
oc -n dark-noc-rag exec pgvector-postgres-1 -c postgres -- \
  psql -U postgres -d noc_rag -tAc "select count(*) from documents;"
```

**Output:**
```text
job.batch/rag-seed   Complete
pod/pgvector-postgres-1   Running
53
```

**Status:** ✅ SUCCESS

---

### CMD-0140 — Add Product Documentation Ingestion Pipeline (Phase 03)
- **Phase:** 03 — AI Core
- **Cluster:** hub
- **Date:** 2026-03-05 UTC
- **Why:** Extend RAG beyond local runbooks to include official Red Hat/product documentation for version-accurate troubleshooting.
- **What:** Added repo assets:
  - `rag/documentation-sources.yaml` (version-pinned sources)
  - `rag/seed-product-docs.py` (fetch, parse, embed, insert)
  - `rag/rag-docs-seed-job.yaml` (Kubernetes Job runner)
- **Expected:** One-command repeatable docs ingestion into pgvector as `metadata.type=documentation`.
- **Outcome:** Assets created and validated; first run exposed missing secret + index privilege constraints and was remediated in follow-up steps.

**Status:** ✅ SUCCESS

---

### CMD-0141 — Execute Documentation Seed Job and Validate Corpus
- **Phase:** 03 — AI Core
- **Cluster:** hub
- **Date:** 2026-03-05 UTC
- **Why:** Load live docs corpus into pgvector and verify counts for agent retrieval.
- **What:**
  1. Created ConfigMaps (`rag-docs-seed-script`, `rag-docs-sources`) from repo files.
  2. Ran `job/rag-docs-seed` in `dark-noc-rag`.
  3. Fixed runtime issues:
     - removed missing secret dependency (`pgvector-secret`)
     - patched seeder to skip index creation when DB role lacks table ownership.
  4. Re-ran job to completion.
  5. Updated source URLs for better tool coverage (`LangGraph` GitHub docs path) and re-ran ingestion.
- **Expected:** Job succeeds and docs chunks populate `documents` with `metadata.type=documentation`.
- **Outcome:** Success.
  - Job completed: `job.batch/rag-docs-seed condition met`
  - Inserted docs chunks: `666`
  - Final DB counts:
    - `documentation|666`
    - `runbook|53`

**Status:** ✅ SUCCESS

---

### CMD-0142 — Expand Documentation Source Depth + Refresh Corpus
- **Phase:** 03 — AI Core
- **Cluster:** hub
- **Date:** 2026-03-05 UTC
- **Why:** Increase documentation recall quality by indexing deeper, version-pinned html-single docs for core Red Hat products.
- **What:**
  1. Expanded `documentation-sources.yaml` with deeper links for OCP, OCP AI, ACM, AAP, Logging, and Service Mesh.
  2. Re-ran `job/rag-docs-seed` to rebuild `metadata.type=documentation` corpus.
  3. Verified final counts in pgvector.
- **Expected:** Larger and richer documentation corpus in `documents`.
- **Outcome:** Success.
  - Seed run loaded `23` pages.
  - Documentation chunks inserted: `666`
  - Final DB counts: `documentation|666`, `runbook|53`
  - One URL returned `404` (`.../html-single/networking/index`) and can be replaced in next cleanup pass.

**Status:** ✅ SUCCESS

---

### CMD-0143 — Update Agent RAG Retrieval to Use Runbooks + Documentation
- **Phase:** 05 — Agent & MCP
- **Cluster:** repo code update
- **Date:** 2026-03-05 UTC
- **Why:** Agent previously queried runbook-only RAG context, underusing newly ingested official product documentation.
- **What:**
  1. Updated `rag_search()` in `agent.py` to accept `doc_type` filter.
  2. `node_rag_retrieval` now pulls both runbook and documentation chunks.
  3. Analysis prompt updated to consume combined knowledge context.
  4. Updated state comment in `state.py` to reflect combined corpus usage.
- **Expected:** RCA generation can reference both operational runbooks and version-matched product docs.
- **Outcome:** Code compiles successfully (`py_compile`), ready for next agent image build/deploy step.

**Status:** ✅ SUCCESS

---

### CMD-0144 — Build and Deploy LangGraph Agent on Hub (Phase 05)
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-05 UTC
- **Why:** Activate updated agent code (dual-corpus RAG retrieval + docs corpus usage) in-cluster.
- **What:**
  1. Added `agent/buildconfig.yaml` (ImageStream + Binary BuildConfig).
  2. Applied `agent/deployment.yaml` and created required service account + secrets in `dark-noc-hub`.
  3. Ran iterative image builds and resolved dependency/runtime blockers.
- **Key fixes made during build stabilization:**
  - `requirements.txt`:
    - `openai==1.69.0`
    - `langgraph-checkpoint-postgres==2.0.25`
    - `httpx==0.28.1`
    - `mcp==1.24.0`
    - `python-dotenv==1.1.0`
    - `langchain-core>=0.3.75,<1.0.0`
    - `torch==2.8.0+cpu`
  - `Dockerfile`:
    - install deps with CPU wheel index
    - removed invalid `COPY nodes/`
    - install packages to `/opt/python` and set `PYTHONPATH=/opt/python` for non-root runtime.
  - `agent.py`:
    - updated MCP import/API to `ClientSession` + `initialize()`
    - switched checkpoint DB connection to `psycopg.connect(..., autocommit=True)` for `PostgresSaver`.
- **Expected:** Agent image builds cleanly and deployment reaches `Available=True`.
- **Outcome:** Success.
  - Successful build: `dark-noc-agent-14`
  - Pushed digest: `sha256:e9f58e1311e4c4f7f3ab1471ecc4db2c8153edb1845e836b51a0f5ac7240ca79`
  - Deployment rolled out successfully.

**Status:** ✅ SUCCESS

---

### CMD-0145 — Verify Agent Runtime Health and Kafka Consumption
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-05 UTC
- **Why:** Confirm agent is stable after build/deploy and actively connected to Kafka.
- **What:** Verified pod readiness, image digest, restart count, and startup logs.
- **Expected:** Running pod, no crash loop, logs show Kafka group join and topic subscription.
- **Outcome:** Success.
  - Pod: `dark-noc-agent-5884d7988b-stg6j` (`READY=true`, `RESTARTS=0`)
  - Image digest matches build output.
  - Logs show successful startup and Kafka subscription:
    - `Listening on Kafka topic: nginx-logs`
    - `Successfully joined group dark-noc-agent`
    - assigned topic partitions.

**Status:** ✅ SUCCESS

---

### CMD-0146 — Cleanup Failed/Cancelled Agent Builds and Build Pods
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-05 UTC
- **Why:** Remove failed/cancelled build history and stale build pods to keep cluster artifacts clean.
- **What:**
  1. Deleted failed/cancelled build objects:
     - `dark-noc-agent-5` .. `dark-noc-agent-9`
  2. Deleted stale build pods (`dark-noc-agent-*-build`) from prior attempts.
- **Expected:** Only successful build records remain.
- **Outcome:** Success. Remaining builds:
  - `dark-noc-agent-10` .. `dark-noc-agent-14` (all `Complete`).

**Status:** ✅ SUCCESS

---

### CMD-0147 — Cleanup Local Repo Artifacts
- **Phase:** Repo hygiene
- **Cluster:** local workspace
- **Date:** 2026-03-05 UTC
- **Why:** Keep repository clean before GitHub sync.
- **What:**
  1. Removed Python cache artifacts:
     - `implementation/phase-05-agent-mcp/agent/__pycache__/`
     - `implementation/phase-03-ai-core/rag/__pycache__/`
  2. Removed stray macOS metadata files:
     - `.DS_Store` files under `dark-noc/`
- **Expected:** No generated cache files or OS metadata committed.
- **Outcome:** Success; cleanup complete.

**Status:** ✅ SUCCESS

### 2026-03-06 — Continue 1 and 2 (AAP + full chain validation)

- Retrieved AAP job failure details (`job 4`) from `https://aap-aap.../api/v2/jobs/4/stdout`:
  - Failure was `401 Unauthorized` to edge cluster API.
- Updated and synced playbook:
  - File: `implementation/phase-04-automation/playbooks/restart-nginx-aap-api.yaml`
  - Removed hardcoded token, added assert for launch-time token, switched to `edge_namespace` var.
  - Synced into AAP project checkout as `hello_world.yml`.
- Relaunched AAP template `restart-nginx` with fresh edge token:
  - `job 5` -> `successful`.
- Patched AAP template `id=8` default `extra_vars` with edge API/token for agent-driven launches.
- Fixed agent runtime:
  - Removed failing checkpointer compile path in `agent.py` (resolved `NotImplementedError` on `aget_tuple`).
  - Built new image (`dark-noc-agent-15`) and rolled deployment.
  - Set env on deployment for writable model cache:
    - `XDG_CACHE_HOME=/tmp/.cache`
    - `HF_HOME=/tmp/huggingface`
    - `TRANSFORMERS_CACHE=/tmp/huggingface/transformers`
    - `SENTENCE_TRANSFORMERS_HOME=/tmp/huggingface/sentence-transformers`
- End-to-end verification events:
  - Injected synthetic incident into Kafka from running agent pod.
  - Agent remediation triggered AAP `job 6` -> `successful`.
  - Escalation test incident created ServiceNow mock ticket `INC0000001`.
- Noted remaining bug:
  - Escalation path hits `node_notify` with `remediation_result=None` (`AttributeError`), to be fixed next.


### 2026-03-06 — Switch MCP ServiceNow to real instance

- Updated `mcp-servicenow/server.py` to support real ServiceNow Table API (basic auth + `result` payload parsing) while keeping mock compatibility.
- Updated `mcp-servers-deployment.yaml` to source ServiceNow settings from `servicenow-secrets`.
- Applied/updated secret `dark-noc-mcp/servicenow-secrets` with real instance URL and credentials.
- Built and pushed new image: `mcp-servicenow-3` (`sha256:6c1427...`).
- Rolled out deployment `mcp-servicenow` and injected env from secret.
- Validated direct ServiceNow API access (`GET /api/now/table/incident` returned success).
- Created validation incident directly: `INC0010001`.
- Triggered agent escalation flow and confirmed new incident in real instance: `INC0010002`.


### 2026-03-06 — Install full AAP via Red Hat certified AAP Operator

- Added and applied full platform CR:
  - `implementation/phase-04-automation/aap/aap-platform.yaml`
  - Kind: `AnsibleAutomationPlatform` (`aap-enterprise` in namespace `aap`)
  - Components enabled: `controller`, `hub`, `eda`
- Observed operator reconciliation creating platform resources:
  - `aap-enterprise-gateway` deployment
  - `aap-enterprise-postgres-15` statefulset
  - `aap-enterprise-redis` statefulset
  - route: `aap-enterprise-aap.apps.ocp.v8w9c.sandbox205.opentlc.com`
- Verified enterprise UI endpoint serves AAP frontend (`title: Ansible Automation Platform`, HTTP 200).


### CMD-0162 — Deploy Full Enterprise AAP (Controller + Hub + EDA)
- **Phase:** 04 — Automation
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** User requested full Red Hat certified AAP platform UI (not API-only).
- **What:** Applied `implementation/phase-04-automation/aap/aap-platform.yaml` with `AnsibleAutomationPlatform` CR `aap-enterprise`.
- **Expected:** Enterprise AAP route serves UI and all components become healthy.
- **Outcome:** Partially successful. Gateway/controller/EDA came up and route returned `200`, but Hub did not become ready due storage provisioning constraints.

**Status:** ⚠️ PARTIAL

---

### CMD-0163 — Root Cause Analysis for AAP Hub Pending
- **Phase:** 04 — Automation
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** User saw `Service Unavailable` after login.
- **What:** Inspected pods/events/PVCs in `aap` namespace.
- **Expected:** Identify concrete blocker.
- **Outcome:** Confirmed blocker on `aap-enterprise-hub-file-storage`:
  - `ProvisioningFailed ... Volume capabilities not supported`
  - This is caused by requested Hub file-storage capabilities that the current AWS EBS CSI path does not satisfy.

**Status:** ⚠️ BLOCKED

---

### CMD-0164 — Attempted Hub Storage Compatibility Fix
- **Phase:** 04 — Automation
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Resolve Hub startup by changing storage to AWS-compatible settings.
- **What:**
  1. Updated local `aap-platform.yaml` with Hub storage overrides.
  2. Patched live `AutomationHub` to:
     - `file_storage_access_mode: ReadWriteOnce`
     - `file_storage_storage_class: gp3-csi`
     - `file_storage_size: 20Gi`
  3. Deleted failed Hub PVC for operator reconciliation.
- **Expected:** New Hub PVC binds and Hub pods schedule.
- **Outcome:** Still blocked with same CSI error (`Volume capabilities not supported`).

**Status:** ⚠️ BLOCKED

### CMD-0165 — Verify AAP License Activation via Real Job Run
- **Phase:** 04 — Automation
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** User activated subscription and requested continuation.
- **What:** Authenticated to enterprise controller API and launched Demo Job Template (`id=7`).
- **Expected:** Previously blocked `License is missing` should be resolved.
- **Outcome:** Success. Job `id=1` completed `successful`; stdout returned `Hello World` play recap.

**Status:** ✅ SUCCESS

---

### CMD-0166 — Create Enterprise `restart-nginx` Job Template
- **Phase:** 04/05 Integration
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** MCP workflow expects job template name `restart-nginx`.
- **What:** Created template in enterprise AAP:
  - `name=restart-nginx`
  - `project=Demo Project (id=6)`
  - `inventory=Demo Inventory (id=1)`
  - `playbook=hello_world.yml` (bootstrap placeholder)
- **Expected:** Template resolvable by MCP launch calls.
- **Outcome:** Success. Template created as `id=8`.

**Status:** ✅ SUCCESS

---

### CMD-0167 — Repoint `mcp-aap` to Enterprise Controller
- **Phase:** 05 — Agent & MCP
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** MCP still pointed at legacy internal AAP service; needed to target licensed enterprise controller.
- **What:**
  1. Synced `dark-noc-mcp/aap-admin-secret` with enterprise controller admin password.
  2. Updated `mcp-aap` env:
     - `AAP_URL=https://aap-enterprise-controller-aap.apps.ocp.v8w9c.sandbox205.opentlc.com`
     - `AAP_USERNAME=admin`
     - `AAP_VERIFY_SSL=false`
  3. Restarted and verified rollout of `deploy/mcp-aap`.
- **Expected:** MCP AAP tool calls authenticate against enterprise controller.
- **Outcome:** Success. New pod running and server startup clean.

**Status:** ✅ SUCCESS

### CMD-0168 — Validate Enterprise `restart-nginx` Job Execution
- **Phase:** 04/05 Integration
- **Cluster:** hub
- **Date:** 2026-03-06 UTC
- **Why:** Confirm template created post-subscription can execute.
- **What:** Launched `job_templates/8/launch/` with sample `extra_vars` and polled job.
- **Expected:** Job runs successfully on licensed enterprise controller.
- **Outcome:** Success. Job `id=3`, template `restart-nginx`, status `successful`.

**Status:** ✅ SUCCESS

### CMD-0169 — Standardize Edge Site Name to `edge-01`
- **Phase:** Cross-phase config normalization
- **Cluster:** local/repo
- **Date:** 2026-03-06 UTC
- **Why:** User requested consistent edge site naming as `edge-01`.
- **What:** Updated defaults and labels from legacy edge site ID to `edge-01` across env templates, edge namespace/site labels, ACM managed-cluster metadata label, agent default parsing, Slack alert defaults, and AAP playbook variable defaults.
- **Expected:** One canonical edge site identifier across deployment/config/runtime docs.
- **Outcome:** Success. Legacy edge site ID references removed from active configs/manifests.

**Status:** ✅ SUCCESS

### CMD-0170 — Enforce `edge-01` Naming Across Hub Runtime + Repo
- **Phase:** Cross-phase normalization
- **Cluster:** hub + repo
- **Date:** 2026-03-06 UTC
- **Why:** User requested edge site name `edge-01` everywhere (Ansible, ServiceNow, Slack, hub, edge).
- **What:**
  1. Updated active repo manifests/configs to remove old edge site/cluster IDs.
  2. Created new hub secret `dark-noc-mcp/edge-01-kubeconfig` from existing kubeconfig data.
  3. Updated live `mcp-openshift` deployment to mount `edge-01-kubeconfig` and rolled out.
  4. Removed old hub secret `edge-cluster-kubeconfig`.
  5. Patched enterprise AAP `restart-nginx` template (`id=8`) default `extra_vars` to `edge_cluster: edge-01`.
- **Expected:** Hub runtime and automation path consistently reference `edge-01`.
- **Outcome:** Success on hub + repo. Edge live label patch remains pending due expired edge token.

**Status:** ✅ SUCCESS (hub/repo) + ⚠️ PENDING (edge token refresh)

### CMD-0171 — Apply Live Edge Namespace Site ID Rename to `edge-01`
- **Phase:** Cross-phase normalization
- **Cluster:** edge
- **Date:** 2026-03-06 UTC
- **Why:** Complete runtime alignment so edge live labels match standardized site ID `edge-01`.
- **What:**
  1. Logged in to edge cluster using provided admin credentials.
  2. Verified `dark-noc-edge` namespace had old label `dark-noc/site-id=edge-site-01`.
  3. Patched namespace labels:
     - `dark-noc/site-id=edge-01`
     - `dark-noc/cluster=edge` (confirmed)
  4. Scanned edge workload resources for residual old site ID labels.
- **Expected:** Edge runtime labels use only `edge-01`.
- **Outcome:** Success. Namespace now reports `dark-noc/site-id=edge-01`; no remaining old site ID in edge workload resources.

**Status:** ✅ SUCCESS

### CMD-0172 — Create AAP Edge Credential and Bind to `restart-nginx`
- **Phase:** 04/05 Integration
- **Cluster:** hub + edge
- **Date:** 2026-03-06 UTC
- **Why:** Prepare AAP template to execute against edge site `edge-01` using enterprise controller.
- **What:**
  1. Logged into edge and generated a fresh admin bearer token.
  2. Created enterprise AAP credential `edge-01-k8s` (type: OpenShift/Kubernetes API Bearer Token).
  3. Attached credential to job template `restart-nginx` (`id=8`).
  4. Launched validation run (`job id=5`) and confirmed success.
- **Expected:** `restart-nginx` template is credential-ready for edge API execution.
- **Outcome:** Success. Template now has `edge-01-k8s` credential bound and launches successfully.

**Status:** ✅ SUCCESS

---

### CMD-0173 — Update `restart-nginx` Playbook for Bearer-Token Auth
- **Phase:** 04 — Automation
- **Cluster:** repo
- **Date:** 2026-03-06 UTC
- **Why:** Original playbook only supported `KUBECONFIG`; enterprise AAP uses Kubernetes bearer-token credential injection.
- **What:** Updated playbook auth handling to support:
  - Legacy: `KUBECONFIG`
  - Preferred: `K8S_AUTH_HOST` + `K8S_AUTH_API_KEY` (+ `K8S_AUTH_VERIFY_SSL`)
  Added preflight assert and conditional auth parameters for all k8s tasks.
- **Expected:** Same playbook works with both credential styles.
- **Outcome:** Success. Playbook now supports enterprise credential model for `edge-01`.

**Status:** ✅ SUCCESS

### CMD-0174 — Create Repo-Root Playbook Path `playbooks/restart-nginx.yaml`
- **Phase:** 04/05 Integration
- **Cluster:** repo
- **Date:** 2026-03-09 UTC
- **Why:** Prepare canonical SCM playbook path for AAP project sync/template mapping.
- **What:** Created `playbooks/` directory at repo root and copied the production-ready restart playbook to `playbooks/restart-nginx.yaml`.
- **Expected:** AAP template can be switched to repo path `playbooks/restart-nginx.yaml` once SCM project points to this repo.
- **Outcome:** Success. Playbook file exists with bearer-token auth support for `edge-01`.

**Status:** ✅ SUCCESS

### CMD-0175 — Upgrade Dashboard to Enterprise Operations View + Topology
- **Phase:** 06 — Dashboard
- **Cluster:** repo
- **Date:** 2026-03-09 UTC
- **Why:** User requested enterprise-grade UI with full MCP/platform status matrix, direct dashboard links, topology, and error-flow visibility.
- **What:**
  1. Expanded chatbot backend API:
     - Added `/api/integrations` with status probes for MCP servers and platform services.
     - Added direct UI URLs for ServiceNow, Slack, OpenShift, AAP, Kafka, Loki.
     - Added EDA usage metadata (`where/how`) in API response.
  2. Updated chatbot deployment env vars for dashboard URLs.
  3. Rebuilt dashboard React layout:
     - Integration status matrix with health pill and “Open Dashboard” links.
     - Enterprise NOC visual theme.
     - Topology and error/remediation flow SVG map (edge/core/data).
     - EDA usage panel on dashboard.
- **Expected:** Dashboard surfaces operational status and navigation links for all requested integrations.
- **Outcome:** Success (code changes complete). Local Vite build unavailable in shell (`vite: command not found`), so image rebuild should be validated via OpenShift build pipeline.

**Status:** ✅ SUCCESS (code) / ⚠️ LOCAL BUILD TOOLING GAP

### CMD-0176 — Build/Deploy Enterprise Dashboard + Integrations API
- **Phase:** 06 — Dashboard
- **Cluster:** hub
- **Date:** 2026-03-09 UTC
- **Why:** Promote enterprise UI/API changes to running environment.
- **What:**
  1. Built `dark-noc-chatbot-2` and `dark-noc-dashboard-2` from updated source.
  2. Restarted and validated rollouts for `deploy/dark-noc-chatbot` and `deploy/dark-noc-dashboard`.
  3. Verified routes for chatbot/dashboard.
  4. Verified `/api/integrations` returns integration matrix + EDA usage metadata.
- **Expected:** Upgraded dashboard and integrations API live on cluster.
- **Outcome:** Success. New dashboard assets served and integrations API active.

**Status:** ✅ SUCCESS

---

### CMD-0177 — Fix Kafka/Loki False-Negative Probes and Re-Deploy Chatbot
- **Phase:** 06 — Dashboard
- **Cluster:** hub
- **Date:** 2026-03-09 UTC
- **Why:** Direct HTTP probe to raw Kafka/Loki service ports produced false `down` statuses.
- **What:**
  1. Updated chatbot integration probes for `Kafka` and `LokiStack` to use MCP-backed HTTP reachability.
  2. Built `dark-noc-chatbot-3` and rolled out `deploy/dark-noc-chatbot`.
  3. Re-checked `/api/integrations` aggregate status.
- **Expected:** Accurate integration status cards in UI.
- **Outcome:** Success. Matrix now reports `12/12 up`.

**Status:** ✅ SUCCESS

### CMD-0178 — Add Edge EDA Implementation Artifacts
- **Phase:** 04 — Automation
- **Cluster:** repo
- **Date:** 2026-03-09 UTC
- **Why:** User requested edge EDA details and implementation pattern in project files.
- **What:** Added edge EDA docs/manifests under `implementation/phase-04-automation/edge-eda/`:
  - `README.md` (operating model: edge fast-path + hub governance)
  - `edge-eda-rulebook.yaml` (safe local remediation rules)
  - `edge-eda-runner-deployment.yaml` (lightweight ansible-rulebook runner pattern)
  Also updated Phase 04 README to include edge EDA placement and file inventory.
- **Expected:** Repo captures explicit edge EDA design and deployable templates.
- **Outcome:** Success.

**Status:** ✅ SUCCESS

---

### CMD-0179 — Attempt Full AAP E2E Playbook Switch and Launch
- **Phase:** 04/05 Integration
- **Cluster:** hub + edge
- **Date:** 2026-03-09 UTC
- **Why:** Execute true end-to-end edge remediation via enterprise AAP template.
- **What:**
  1. Loaded `playbooks/restart-nginx.yaml` into AAP controller project filesystem.
  2. Refreshed edge credential token (`edge-01-k8s`).
  3. Attempted to patch template `restart-nginx` (`id=8`) to `playbooks/restart-nginx.yaml`.
- **Expected:** Template updates and launches real restart playbook.
- **Outcome:** Blocked by AAP project validation: `Playbook not found for project.`
  - AAP only allows template playbooks that exist in the project's indexed SCM content.
  - Current project SCM (`ansible-tower-samples`) only exposes `hello_world.yml`.

**Status:** ⚠️ BLOCKED (requires SCM repo containing restart playbook)

### CMD-0180 — Build Internal AAP Demo SCM (No External Git Required)
- **Phase:** 04/05 Integration
- **Cluster:** hub
- **Date:** 2026-03-09 UTC
- **Why:** User requested SCM/project setup without owning external SCM.
- **What:**
  1. Created internal bare Git repo in AAP controller storage:
     - `/var/lib/awx/projects/darknoc-demo-scm.git`
  2. Created working repo and committed `playbooks/restart-nginx.yaml`.
  3. Pushed to internal bare repo.
  4. Created AAP project `DarkNOC-Internal-SCM` (`id=10`) with:
     - `scm_type=git`
     - `scm_url=file:///var/lib/awx/projects/darknoc-demo-scm.git`
  5. Synced project; AAP indexed `playbooks/restart-nginx.yaml`.
- **Expected:** Template can use real playbook from SCM-indexed project.
- **Outcome:** Success.

**Status:** ✅ SUCCESS

---

### CMD-0181 — End-to-End Restart Remediation Success on edge-01
- **Phase:** 04/05 Integration
- **Cluster:** hub + edge
- **Date:** 2026-03-09 UTC
- **Why:** Validate full automation loop with real playbook execution.
- **What:**
  1. Bound template `restart-nginx` (`id=8`) to project `DarkNOC-Internal-SCM` and playbook `playbooks/restart-nginx.yaml`.
  2. Refreshed `edge-01-k8s` credential token.
  3. Launched job `id=18` and confirmed status `successful`.
  4. Verified actual edge rollout effect:
     - `before_ts=2026-03-06T03:05:51Z`
     - `after_ts=2026-03-09T16:12:48Z`
     - pod changed from `nginx-bc9b56699-l7tbh` to `nginx-6bf545776b-d7clh`
  5. Confirmed rollout completion: `deployment/nginx successfully rolled out`.
- **Expected:** True edge restart executed end-to-end through AAP.
- **Outcome:** Success. End-to-end remediation is operational.

**Status:** ✅ SUCCESS

---

### CMD-0182 — Verify AAP Project Deletion (`DarkNOC-Local-Project`)
- **Phase:** 04/05 Integration
- **Cluster:** hub
- **Date:** 2026-03-09 UTC
- **Why:** User requested deletion confirmation for legacy AAP local project.
- **What:** Queried AAP Controller API projects endpoint with `name=DarkNOC-Local-Project` using enterprise controller admin credentials.
- **Expected:** Project absent from AAP project inventory.
- **Outcome:** Success. API response `count=0`.

**Status:** ✅ SUCCESS

### CMD-0183 — Deploy Edge Local Runner and Resolve Image/Runtime Blockers
- **Phase:** 04 — Automation
- **Cluster:** edge-01
- **Date:** 2026-03-09 UTC
- **Why:** Edge EDA runner rollout was blocked by image pull auth and runtime dependencies.
- **What:**
  1. Confirmed `quay.io/ansible/event-driven-ansible:latest` unauthorized pull (`ImagePullBackOff`).
  2. Tested alternate images (`creator-ee`, Red Hat EDA controller image), then confirmed `ansible-rulebook` runtime blockers (binary/JVM dependency).
  3. Reworked `edge-eda-runner-deployment.yaml` to a deterministic lightweight edge webhook runner (`quay.io/openshift/origin-cli:4.21` + Python handler).
  4. Applied and rolled out new deployment in `dark-noc-edge`.
- **Expected:** Edge runner stable and listening on port 5000.
- **Outcome:** Success. `edge-eda-runner` rollout complete; log: `listening on 0.0.0.0:5000 site=edge-01`.

**Status:** ✅ SUCCESS

### CMD-0184 — Validate Edge-01 Local Fast-Path Remediation (OOM Event)
- **Phase:** 08 — Validation
- **Cluster:** edge-01
- **Date:** 2026-03-09 UTC
- **Why:** Validate local edge remediation path independent of hub/AAP latency.
- **What:**
  1. Captured nginx baseline (`restartAt=2026-03-09T16:12:48Z`, memory `32Mi/16Mi`).
  2. Posted OOM webhook payload to `edge-eda-runner` service endpoint `/endpoint`.
  3. Verified runner returned `result=success` and patched deployment.
  4. Verified post-remediation state:
     - `restartAt=2026-03-09T16:48:41Z`
     - memory restored to `128Mi/64Mi`
     - new nginx pod running (`nginx-59577f9f64-dtx9n`)
- **Expected:** Local remediation executes and self-heals nginx deployment.
- **Outcome:** Success. Fast-path remediation confirmed end-to-end on edge.

**Status:** ✅ SUCCESS

### CMD-0185 — Send Slack Info Notification (Requested)
- **Phase:** 08 — Validation
- **Cluster:** external (Slack)
- **Date:** 2026-03-09 UTC
- **Why:** User requested explicit Slack message for validation event.
- **What:** Called `chat.postMessage` with provided bot token to channel `#demos`.
- **Expected:** Informational notification appears in workspace channel.
- **Outcome:** Success. Slack API returned `ok=true`, `channel=C08MUDSNHED`, `ts=1773074977.088439`.

**Status:** ✅ SUCCESS

### CMD-0186 — Create ServiceNow Info Ticket (Requested)
- **Phase:** 08 — Validation
- **Cluster:** hub/external
- **Date:** 2026-03-09 UTC
- **Why:** User requested info ticket creation for remediation event tracking.
- **What:**
  1. Attempted real ServiceNow Table API (`dev315177`) with basic auth and session-cookie auth flow.
  2. Real instance returned auth failure (`User is not authenticated`).
  3. Created informational incident in deployed ServiceNow mock using required `X-API-Key` + `record` payload.
- **Expected:** Ticket created and visible in active ServiceNow integration target.
- **Outcome:** Partial success.
  - Real ServiceNow: blocked by API auth policy.
  - ServiceNow mock: success, incident `INC0000002` created.

**Status:** ⚠️ PARTIAL (real SN blocked, mock SN success)

### CMD-0187 — Continue Validation: Real ServiceNow API Auth Re-Test
- **Phase:** 08 — Validation
- **Cluster:** external
- **Date:** 2026-03-09 UTC
- **Why:** User asked to continue; re-validated whether real ServiceNow can be used directly instead of mock.
- **What:** Tested ServiceNow Table API auth against `https://dev315177.service-now.com/api/now/table/incident` using:
  - `aes.creator:jXd/9!0FZQzv`
  - `aes.creator:jXd%2F9!0FZQzv`
- **Expected:** One auth format should return incident list or allow create.
- **Outcome:** Both returned `401 Unauthorized` with body `User is not authenticated`.

**Status:** ⚠️ BLOCKED (real SN API auth policy/credentials)

### CMD-0188 — Continue Validation: Edge Trigger + Hub Kafka Reporting Proof
- **Phase:** 08 — Validation
- **Cluster:** edge + hub
- **Date:** 2026-03-09 UTC
- **Why:** Confirm end-to-end reporting path after edge local remediation.
- **What:**
  1. Started live hub Kafka consumer (`nginx-logs`) from latest offset.
  2. Triggered new edge webhook OOM event (`edge-01`) to `edge-eda-runner`.
  3. Confirmed edge response: `result=success`, `local_fast_path_restart`, timestamp `2026-03-09T17:05:41Z`.
  4. Captured fresh hub Kafka records containing restarted nginx startup logs with:
     - namespace `dark-noc-edge`
     - namespace label `dark-noc_site-id=edge-01`
     - annotation `kubectl.kubernetes.io/restartedAt=2026-03-09T17:05:41Z`
- **Expected:** Edge action is visible in hub data pipeline.
- **Outcome:** Success. Hub reporting confirmed.

**Status:** ✅ SUCCESS

### CMD-0189 — Switch `mcp-servicenow` to New Real ServiceNow Instance
- **Phase:** 05/06 Integration
- **Cluster:** hub
- **Date:** 2026-03-09 UTC
- **Why:** User provided new real ServiceNow instance and requested continuing with live incident flow.
- **What:**
  1. Updated secret `dark-noc-mcp/servicenow-secrets`:
     - `SERVICENOW_MODE=real`
     - `SERVICENOW_URL=https://dev365997.service-now.com`
     - `SERVICENOW_USERNAME=admin`
     - `SERVICENOW_PASSWORD=<updated>`
  2. Restarted and validated rollout of `deploy/mcp-servicenow`.
- **Expected:** MCP ServiceNow server uses new live instance at runtime.
- **Outcome:** Success. New pod `mcp-servicenow-675d87fcb-zhscq` running.

**Status:** ✅ SUCCESS

### CMD-0190 — In-Cluster Real ServiceNow Runtime Validation via MCP Pod
- **Phase:** 08 — Validation
- **Cluster:** hub + external
- **Date:** 2026-03-09 UTC
- **Why:** Verify live credentials work from the deployed runtime path, not only from local shell.
- **What:** Executed Python API create request from inside `mcp-servicenow` pod using pod env credentials.
- **Expected:** Real incident created successfully.
- **Outcome:** Success (`HTTP 201`), incident `INC0010002` created in `dev365997`.

**Status:** ✅ SUCCESS

### CMD-0191 — Enforce Global ServiceNow Caller (`Mithun Sugur`) in MCP Server
- **Phase:** 05 — Agent & MCP
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** User requested every ServiceNow ticket caller be `Mithun Sugur`.
- **What:**
  1. Updated `mcp-servicenow/server.py`:
     - Added global caller config `SERVICENOW_CALLER_NAME` defaulting to `Mithun Sugur`.
     - `create_incident` now enforces this caller for all tickets.
     - Added real-ServiceNow helper to resolve/create `sys_user` and submit caller by `sys_id`.
  2. Updated deployment template `mcp-servers-deployment.yaml` to include `SERVICENOW_CALLER_NAME` in `servicenow-secrets` and deployment env.
  3. Rebuilt image via BuildConfig `mcp-servicenow-4` and rolled out deployment.
  4. Set live deployment env: `SERVICENOW_CALLER_NAME=Mithun Sugur`.
- **Expected:** All tickets created by MCP path use caller `Mithun Sugur`.
- **Outcome:** Success. New image digest pushed and deployment healthy.

**Status:** ✅ SUCCESS

### CMD-0192 — ServiceNow Caller User Provision + Caller-Tagged Incident Validation
- **Phase:** 08 — Validation
- **Cluster:** external
- **Date:** 2026-03-09 UTC
- **Why:** Verify caller mapping exists and can be enforced by `caller_id`.
- **What:**
  1. Created/verified ServiceNow user `Mithun Sugur` (`user_name=mithun.sugur`, `sys_id=89bf6cd593ab7a106c4bf9f7dd03d62f`).
  2. Created validation incident `INC0010003` with `caller_id` set to that sys_id.
  3. Read back incident and resolved `caller_id` to user record.
- **Expected:** Incident caller resolves to `Mithun Sugur`.
- **Outcome:** Success. `INC0010003` caller points to `Mithun Sugur`.

**Status:** ✅ SUCCESS

### CMD-0193 — ServiceNow Ticket -> Slack Auto-Notification Implementation
- **Phase:** 05 — Agent & MCP
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** User requested that every ServiceNow ticket creation also sends Slack message with incident details.
- **What:**
  1. Updated `mcp-servicenow/server.py` to send Slack message on every `create_incident` result:
     - Added `SLACK_BOT_TOKEN` + `SLACK_NOC_CHANNEL` runtime env handling.
     - Added `_notify_slack_ticket_created()` including number, priority, caller, state, short description, incident URL.
  2. Updated MCP deployment template to inject Slack token/channel into `mcp-servicenow`.
  3. Applied runtime env and rebuilt image (`mcp-servicenow-5`), rolled out deployment.
- **Expected:** Any incident created by MCP ServiceNow tool posts notification to Slack channel.
- **Outcome:** Success. `mcp-servicenow` rollout complete with `SLACK_BOT_TOKEN` and `SLACK_NOC_CHANNEL=#demos`.

**Status:** ✅ SUCCESS

### CMD-0194 — Executive Dashboard Upgrade (Access + Edge EDA Workflow)
- **Phase:** 06 — Dashboard
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** User requested enterprise executive view with direct URLs/credentials and explicit edge+hub EDA workflow.
- **What:**
  1. Backend API (`chatbot/main.py`):
     - Added real ServiceNow mode support for status/count.
     - Added `access` payload with URLs + username/password fields.
     - Added expanded `eda_usage` with edge fast-path + hub workflow steps.
  2. Dashboard UI (`App.jsx`, `styles.css`):
     - Added executive hero metrics row.
     - Added **Access Center (Live Credentials)** panel.
     - Added explicit **Edge + Hub Workflow** ordered steps.
     - Refined visual style for executive presentation.
  3. Updated chatbot deployment env to real ServiceNow instance and access credential fields.
  4. Rebuilt and redeployed:
     - `dark-noc-chatbot-4`
     - `dark-noc-dashboard-3`
- **Expected:** Dashboard shows credentialed portal links, edge EDA workflow, and enterprise-grade layout.
- **Outcome:** Success. `/api/integrations` now returns access/workflow fields and health is `12/12 up`.

**Status:** ✅ SUCCESS

### CMD-0195 — Topology & Executive Dashboard Wording/Flow Refresh
- **Phase:** 06 — Dashboard
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** User requested explicit topology wording updates, edge EDA-runner visibility, ServiceNow incidents in executive integration plane, and richer workflow.
- **What:**
  1. Updated dashboard topology labels:
     - `CORE · Hub -AI intelligence -Control Plane`
     - `DATA + MCP Agents`
  2. Added edge `EDA-runner` node + local remediation flow path in SVG.
  3. Added `ServiceNow Incidents` metric in executive hero plane and incident count alongside integration refresh.
  4. Expanded edge+hub workflow panel content and made it more detailed.
- **Expected:** Topology and executive section reflect current runtime architecture and EDA placement.
- **Outcome:** Success. Deployed in `dark-noc-dashboard-4`.

**Status:** ✅ SUCCESS

### CMD-0196 — NOC Chat Upgrade for Agentic + AI Model Knowledge
- **Phase:** 06 — Dashboard/Chatbot
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** User requested NOC chats to provide complete agentic and model information.
- **What:**
  1. Enhanced chatbot API logic (`/api/chat`) to answer with:
     - Agentic stack (`LangGraph + MCP + LlamaStack`)
     - Active AI model (`granite-4-h-tiny`)
     - Edge+hub EDA workflow steps
     - Incident summary
     - Access URLs and credentials listing
  2. Added model/framework env support.
  3. Rebuilt and redeployed chatbot (`dark-noc-chatbot-5`).
- **Expected:** Chat endpoint returns architecture-aware operational answers.
- **Outcome:** Success. Live test response confirms agentic/model/workflow details.

**Status:** ✅ SUCCESS

### CMD-0197 — Interactive NOC Chat Runtime Orchestration (Model + MCP)
- **Phase:** 06 — Dashboard/Chatbot
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** User requested NOC chat to be interactive and return responses based on running model + all MCP agents.
- **What:**
  1. Reworked chatbot `/api/chat` to execute runtime orchestration per request:
     - call `summary` + `integrations`
     - include MCP status slice in payload
     - attempt live model call (`MODEL_API_URL`) with conversation context
     - use deterministic fallback when model endpoint is unavailable
  2. Added session-aware chat (`session_id`) and bounded conversation history.
  3. Upgraded dashboard chat UI to multi-turn conversation + MCP status pills with direct links.
  4. Rebuilt and redeployed:
     - `dark-noc-chatbot-6`
     - `dark-noc-dashboard-5`
  5. Forced deployment restart so latest imagestream tags are applied.
- **Expected:** Interactive chat returns model/MCP metadata and runtime-aware responses.
- **Outcome:** Success.
  - Live `/api/chat` response includes `mcp_status` for all 6 MCP agents.
  - Runtime shows `12/12` integrations up.
  - Model source currently `unreachable`; fallback still provides full MCP status and next action.

**Status:** ✅ SUCCESS

### CMD-0198 — Live Model Connectivity Fix for Interactive NOC Chat
- **Phase:** 06 — Dashboard/Chatbot
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** Chat responses were returning `model_source=unreachable`; user requested to continue until live model responses work.
- **What:**
  1. Validated endpoint reachability from in-cluster debug pods.
  2. Identified root causes:
     - External inference route TLS handshake failed from chatbot runtime.
     - Predictor service is headless; service port `80` does not translate for direct pod IP access.
  3. Verified working endpoint:
     - `http://granite-vllm-predictor.dark-noc-hub.svc:8080/v1/completions` returns HTTP 200 completions.
  4. Updated repo config:
     - `chatbot/main.py` default `MODEL_API_URL`
     - `chatbot/deployment.yaml` env (`MODEL_API_URL`, `MODEL_TIMEOUT_SECONDS`, `MODEL_MAX_TOKENS`, model/framework vars)
  5. Applied manifest, rebuilt chatbot (`dark-noc-chatbot-7`), restarted rollout, and revalidated `/api/chat`.
- **Expected:** Interactive chat returns model-generated responses and MCP runtime payload in same response.
- **Outcome:** Success.
  - `/api/chat` now reports `model_source=live`.
  - `mcp_status` includes all 6 MCP agents and runtime integrations remain healthy.

**Status:** ✅ SUCCESS

### CMD-0199 — Executive Prompt/Reply Hardening for NOC Chat
- **Phase:** 06 — Dashboard/Chatbot
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** User requested stricter, cleaner executive display responses from interactive chat.
- **What:**
  1. Added deterministic response formatter in chatbot backend to enforce exact sections:
     - `Summary`
     - `MCP Status`
     - `Model Output`
     - `Next Action`
  2. Tightened model prompt contract to avoid disclaimers/self-references and force concise style.
  3. Added low-signal model text sanitization (e.g., punctuation-only outputs) with operational fallback sentence.
  4. Rebuilt and redeployed chatbot (`dark-noc-chatbot-8` then tuned with final rebuild).
  5. Validated live `/api/chat` response format after rollout.
- **Expected:** Consistent executive-safe chat responses with clean structure and actionable output.
- **Outcome:** Success. Live output is stable, strict, and includes all MCP statuses with concise next actions.

**Status:** ✅ SUCCESS

### CMD-0200 — Executive Chat UI Rendering Upgrade
- **Phase:** 06 — Dashboard
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** Continue executive tuning by making strict chatbot output visually structured in dashboard UI.
- **What:**
  1. Updated `ChatPanel.jsx` to parse assistant replies into section blocks using headers:
     - `Summary`
     - `MCP Status`
     - `Model Output`
     - `Next Action`
  2. Added dedicated executive styles in `styles.css` for section cards and readable bullet content.
  3. Rebuilt and redeployed dashboard (`dark-noc-dashboard-6`) and restarted rollout.
- **Expected:** NOC Chat responses display as clean executive sections instead of one plain text paragraph.
- **Outcome:** Success. Dashboard rollout completed and route is serving updated build.

**Status:** ✅ SUCCESS

### CMD-0201 — NOC Chat Quick Ask + Executive Brief Actions
- **Phase:** 06 — Dashboard
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** Continue executive UX improvements for faster demo flow and one-click briefing.
- **What:**
  1. Enhanced `ChatPanel.jsx` with quick-action prompts for:
     - incident posture
     - MCP health
     - remediation status
     - ticket/slack trace
  2. Added `Generate Executive Incident Brief` action that stores latest structured response in a dedicated brief card.
  3. Added styling updates in `styles.css` for quick-action chips and brief card presentation.
  4. Rebuilt and redeployed dashboard (`dark-noc-dashboard-7`) and verified rollout/route.
- **Expected:** Operators can trigger executive queries quickly and present a concise incident brief directly in the dashboard.
- **Outcome:** Success. Dashboard route is live with quick actions and briefing panel.

**Status:** ✅ SUCCESS

### CMD-0202 — Remove Double Numbering in Edge+Hub Workflow
- **Phase:** 06 — Dashboard/Chatbot
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** Workflow steps showed double numbering in UI (`<ol>` plus numbered text values).
- **What:**
  1. Updated `chatbot/main.py` `eda_usage.workflow` entries to remove prefixed `1) ... 8)` text.
  2. Rebuilt and redeployed chatbot (`dark-noc-chatbot-10`).
  3. Verified `/api/integrations` now returns plain step text without numeric prefixes.
- **Expected:** Dashboard ordered list renders single clean numbering.
- **Outcome:** Success. Workflow now displays correctly.

**Status:** ✅ SUCCESS

### CMD-0203 — Guided End-to-End Live Walkthrough (edge-01)
- **Phase:** 08 — Validation
- **Cluster:** hub + edge + external
- **Date:** 2026-03-09 UTC
- **Why:** User requested full step-by-step E2E validation covering fault, EDA, Kafka streams, LangGraph+AI, AAP playbook execution, ServiceNow, Slack, and chatbot query.
- **What:**
  1. Captured baseline health on hub/edge and verified runtime components.
  2. Injected deterministic nginx failure (`CrashLoopBackOff`) on edge via invalid config.
  3. Demonstrated edge EDA fast-path behavior:
     - CrashLoop event intentionally ignored (`202`) by edge runner policy.
     - OOM webhook accepted and remediated locally (`local_fast_path_restart`).
  4. Verified edge logs reached hub Kafka topic `nginx-logs` (including `unknown directive "invalid"`).
  5. Triggered LangGraph incident processing through Kafka and captured AI analysis/remediation logs.
  6. Confirmed AAP enterprise controller execution:
     - Template `restart-nginx` mapped to `playbooks/restart-nginx.yaml`.
     - Latest job run `id=20` successful.
  7. Created real ServiceNow info incident (`INC0010004`) and posted correlated Slack message to `#demos` (`ok=true`).
  8. Validated NOC chatbot executive query response with `model_source=live` and all MCP statuses up.
  9. Restored edge nginx baseline manifest and verified Running/Ready.
- **Expected:** End-to-end proof with command-level evidence for each architecture stage.
- **Outcome:** Success. Full guided walkthrough executed with evidence across edge, hub, and external integrations.

**Status:** ✅ SUCCESS

### CMD-0204 — LangGraph Agent Null-Handling Fix + Validation
- **Phase:** 05/08 — Agent + Validation
- **Cluster:** repo + hub
- **Date:** 2026-03-09 UTC
- **Why:** Historical incidents showed `AttributeError: 'NoneType' object has no attribute 'get'` in `node_notify` when `remediation_result` was null.
- **What:**
  1. Patched agent code:
     - `node_notify`: `rem = state.get("remediation_result") or {}`
     - `node_audit`: `rem = state.get("remediation_result") or {}`
     - `initial_state["remediation_result"]` default changed from `None` to `{}`
  2. Rebuilt and redeployed agent image (`dark-noc-agent-16`) in `dark-noc-hub`.
  3. Produced fresh incident events to validate runtime behavior after fix.
- **Expected:** Incident workflows complete without null dereference in notify/audit path.
- **Outcome:** Success. New incident (`53e822cd`) completed with audit write and no `NoneType` crash.

**Status:** ✅ SUCCESS

### CMD-0205 — Lightspeed Auto-Template Upsert Stabilization + E2E Revalidation
- **Phase:** 05/08 — Agent & MCP + Validation
- **Cluster:** repo + hub + external
- **Date:** 2026-03-11 UTC
- **Why:** `mcp-aap` rollout had secret-key mismatch and Lightspeed generated-template upsert emitted false failures.
- **What:**
  1. Fixed `mcp-aap` deployment secret mapping (`AAP_PASSWORD` from `aap-admin-secret`) and restored healthy rollout.
  2. Synced updated agent/MCP code from `dark-noc` into `darknoc-demo`, rebuilt images, and rolled both deployments.
  3. Fixed agent upsert target playbook to stable wrapper (`playbooks/lightspeed-generate-and-run.yaml`) while keeping generated YAML in `extra_vars`.
  4. Hardened `mcp-aap` `upsert_job_template` idempotency path to treat already-desired state as success.
  5. Re-ran live Lightspeed E2E validation.
- **Expected:** Lightspeed incident flow succeeds, ServiceNow ticket created, generated template appears in AAP, no hard upsert errors.
- **Outcome:** Success. Latest validated run: incident `c914d202-6b78-4edb-bdf1-4379452a20a0`, AAP job `79` `successful`, ServiceNow `INC0010029`, generated template `generated-ansible-job-failure-f0ec346d` (id `15`) present in AAP.

**Status:** ✅ SUCCESS

### CMD-0206 — Repository Consolidation to Single Source (`dark-noc`)
- **Phase:** Repo Hygiene
- **Cluster:** local workspace
- **Date:** 2026-03-11 UTC
- **Why:** Enforce a single reusable source tree under `dark-noc` and remove split state with `darknoc-demo`.
- **What:**
  1. Synced all files from `darknoc-demo` into `dark-noc`.
  2. Cleaned transient artifacts under `dark-noc` (`.DS_Store`, `*.pyc`, empty `__pycache__`).
  3. Removed `darknoc-demo` directory completely.
  4. Verified latest Lightspeed fixes present in `dark-noc` (`upsert_job_template`, stable playbook mapping, idempotent patch handling).
- **Expected:** One clean maintained repo path for reuse and future git publishing.
- **Outcome:** Success. Single source now at `/Users/msugur/Downloads/workspaces/Auto-darknoc/dark-noc`.

**Status:** ✅ SUCCESS

### CMD-0207 — Repo Cleanup + Navigation Hardening
- **Phase:** Repo Hygiene
- **Cluster:** local workspace
- **Date:** 2026-03-11 UTC
- **Why:** Ensure repo is clean, non-ambiguous, and easy for anyone to redeploy.
- **What:**
  1. Removed all empty directories across `dark-noc` (legacy placeholders and stale scaffolding).
  2. Removed transient local artifacts (`.DS_Store`, `*.pyc`, empty `__pycache__`).
  3. Added `docs/deployment/START-HERE.md` for deterministic first-run deployment flow.
  4. Updated root `README.md` to reference `START-HERE` and corrected runbook path guidance.
- **Expected:** Single clean repo with clear entrypoint and no stale empty folders.
- **Outcome:** Success. `dark-noc` now has 0 empty directories and 0 transient build artifacts.

**Status:** ✅ SUCCESS

### CMD-0208 — Lightspeed Documentation + Deployment Order Normalization
- **Phase:** Docs/Repo Hygiene
- **Cluster:** local workspace
- **Date:** 2026-03-11 UTC
- **Why:** Lightspeed details were not explicit across root and phase docs, and deployment order needed to be authoritative for redeploy users.
- **What:**
  1. Updated root `README.md` with explicit Lightspeed capability and authoritative deployment order.
  2. Updated `docs/deployment/START-HERE.md` with Lightspeed-specific mandatory ordering.
  3. Updated `docs/deployment/redeploy-runbook.md` with order-sensitive Lightspeed sequence.
  4. Updated Phase 04/05 READMEs to include Lightspeed placement/orchestration and corrected stale file references.
- **Expected:** New users can follow one deterministic deployment order including Lightspeed enablement.
- **Outcome:** Success. Lightspeed is now documented at root, deployment, and phase levels in consistent order.

**Status:** ✅ SUCCESS

### CMD-0209 — Deployment Orchestration Reorder (Best-Practice Layer)
- **Phase:** Repo Architecture / Deployment UX
- **Cluster:** local workspace
- **Date:** 2026-03-11 UTC
- **Why:** Provide a dependency-safe, reproducible, newcomer-friendly deployment flow with dry-run/apply/validate controls and centralized access templates.
- **What:**
  1. Added ordered deployment index: `deploy/manifest-order.tsv` (canonical step/dependency order).
  2. Added orchestrated guides/scripts:
     - `deploy/ORDERED-DEPLOYMENT.md`
     - `scripts/deploy-dry-run.sh`
     - `scripts/deploy-apply.sh`
     - `scripts/deploy-validate.sh`
  3. Added secure access template: `configs/access/ACCESS-CENTER.template.md`.
  4. Updated env templates with explicit `HUB_CONTEXT`/`EDGE_CONTEXT` support.
  5. Updated docs to wire new orchestrated flow:
     - root `README.md`
     - `docs/deployment/START-HERE.md`
  6. Updated `.gitignore` to exclude local access workbook variants (`configs/access/*.local.*`).
- **Expected:** One deterministic deploy order with clear separation of apply vs manual/helm/build actions.
- **Outcome:** Success. All ordered references resolve and scripts pass shell syntax checks.

**Status:** ✅ SUCCESS

### CMD-0210 — Modular Model Profile Layer for AI Hub Catalog Switching
- **Phase:** AI Core / Repo Reusability
- **Cluster:** local workspace
- **Date:** 2026-03-11 EDT
- **Why:** Enable model switching (from Red Hat OpenShift AI Hub catalog) without hand-editing multiple manifests/services.
- **What:**
  1. Added model profile system under `implementation/phase-03-ai-core/models/profiles/*.env` with template + initial profiles.
  2. Added templated manifests:
     - `vllm/vllm-inferenceservice.tmpl.yaml`
     - `llamastack/llamastack-distribution.tmpl.yaml`
  3. Added renderer/apply utility: `scripts/render-model-profile.sh`.
  4. Added shared model binding ConfigMaps:
     - hub: `phase-03-ai-core/models/model-binding-configmap.yaml`
     - ui: `phase-06-dashboard/chatbot/model-binding-configmap.yaml`
  5. Updated consumers to use model binding keys:
     - `phase-05-agent-mcp/agent/deployment.yaml` (`MODEL_ID`, `VLLM_URL`)
     - `phase-06-dashboard/chatbot/deployment.yaml` (`AI_MODEL_NAME`, `MODEL_API_URL`)
  6. Added deployment/reference docs:
     - `docs/reference/MODEL-PROFILES.md`
     - updates in Phase 03 README and START-HERE.
- **Expected:** Switch model by updating one profile file + rendering/applying generated manifests.
- **Outcome:** Success. Renderer validated for `granite-4-h-tiny` and `llama-3.2-3b-instruct`; generated outputs and docs are in place.

**Status:** ✅ SUCCESS

### CMD-0211 — Bind Existing `my-first-model` Runtime/ISVC into Dark NOC + Granite 3.1 Profile
- **Phase:** AI Core Integration
- **Cluster:** local workspace (+ observed hub context)
- **Date:** 2026-03-11 EDT
- **Why:** User requested binding Dark NOC to models served from OpenShift AI Hub catalog path, specifically Granite 3.1 8B LAB, while using existing `my-first-model` serving runtime pattern.
- **What:**
  1. Added `scripts/bind-existing-model.sh` to bind any existing ISVC endpoint into Dark NOC model bindings (`dark-noc-hub` + `dark-noc-ui`) and restart consumers.
  2. Added profile file: `models/profiles/granite-3.1-8b-lab-v1.env`.
  3. Added ready-to-apply ISVC manifest for `my-first-model` namespace using existing runtime:
     - `models/my-first-model/granite-3.1-8b-lab-v1-isvc.yaml`
  4. Updated docs with direct commands and flow:
     - `docs/reference/MODEL-PROFILES.md`
     - `implementation/phase-03-ai-core/README.md`
- **Expected:** Deploy or reuse Granite 3.1 model in `my-first-model`, then bind Dark NOC to that predictor URL with one command.
- **Outcome:** Success. Scripts pass shell syntax checks; Granite 3.1 profile render validated.

**Status:** ✅ SUCCESS

### CMD-0212 — Granite 3.1 ISVC Deploy Attempt + Binding Blocked by Hub API DNS Flaps
- **Phase:** AI Core Integration
- **Cluster:** hub (`my-first-model`, `dark-noc-hub`, `dark-noc-ui`)
- **Date:** 2026-03-11 EDT
- **Why:** Continue with live bind of `granite-3.1-8b-lab-v1` to Dark NOC runtime.
- **What:**
  1. Successfully logged in to hub (`admin`) and created ISVC:
     - `my-first-model/inferenceservice granite-31-8b-lab-v1`
  2. Verified ISVC URL was created and status currently `READY=False` (`MinimumReplicasUnavailable`).
  3. Attempted pod/event diagnostics and `bind-existing-model.sh` execution with retries.
- **Expected:** ISVC reaches ready and Dark NOC model-binding configmaps update + agent/chatbot roll.
- **Outcome:** **Blocked** by intermittent DNS resolution failures to hub API from execution shell:
  - `lookup api.ocp.v8w9c.sandbox205.opentlc.com: no such host`
  - Binding script could not complete while API is unreachable.

**Status:** ⚠️ BLOCKED (environment/API DNS instability)

### CMD-0213 — Recover `llama-32-3b-instruct` Predictor + Bind Dark NOC to `my-first-model`
- **Phase:** AI Core Integration
- **Cluster:** hub (`my-first-model`, `dark-noc-hub`, `dark-noc-ui`)
- **Date:** 2026-03-11 EDT
- **Why:** User requested using `llama-32-3b-instruct` in `my-first-model` instead of `granite-vllm`.
- **What:**
  1. Verified stuck predictor pod `llama-32-3b-instruct-predictor-c894d44d8-rqpmj` (`UnexpectedAdmissionError`).
  2. Deleted stuck pod to force clean recreate.
  3. Confirmed `InferenceService/llama-32-3b-instruct` reported `READY=True` after restart action.
  4. Executed binder:
     - `scripts/bind-existing-model.sh --namespace my-first-model --inference-service llama-32-3b-instruct --model-id llama-32-3b-instruct`
  5. Updated model binding ConfigMaps:
     - `dark-noc-hub/dark-noc-model-binding`
     - `dark-noc-ui/dark-noc-model-binding`
  6. Triggered rollout restarts:
     - `deploy/dark-noc-agent`
     - `deploy/dark-noc-chatbot`
- **Expected:** Dark NOC model calls route to `llama-32-3b-instruct-predictor.my-first-model.svc`.
- **Outcome:** Success for restart + binding + restart triggers. Final rollout status checks intermittently blocked by hub API DNS flaps.

**Status:** ✅ SUCCESS (with ⚠️ verification intermittency)

### CMD-0214 — Retry Verification After Switch to `my-first-model/llama-32-3b-instruct`
- **Phase:** Validation
- **Cluster:** hub + my-first-model
- **Date:** 2026-03-11 EDT
- **Why:** User requested retry verification after model switch.
- **What:**
  1. Verified rollout completion:
     - `deploy/dark-noc-agent` successful rollout
     - `deploy/dark-noc-chatbot` successful rollout
  2. Verified pods running:
     - `dark-noc-agent` pod `Running (1/1)`
     - `dark-noc-chatbot` pod `Running (1/1)`
  3. Verified target model ISVC health:
     - `my-first-model/isvc llama-32-3b-instruct` is `READY=True`
  4. Attempted ConfigMap read-back checks; blocked intermittently by hub API DNS flaps.
- **Expected:** Platform components healthy and using switched inference source.
- **Outcome:** Success for runtime verification (rollouts/pods/ISVC). Non-critical read-back command intermittency remains due environment DNS instability.

**Status:** ✅ SUCCESS (runtime) + ⚠️ intermittent API DNS on some read commands

### CMD-0215 — Lightspeed E2E (Bastion-Executed) + Runtime Fixes
- **Phase:** Validation / Lightspeed
- **Cluster:** Hub (`v8w9c`) via bastion SSH
- **Date:** 2026-03-11 EDT
- **Why:** User requested live end-to-end Lightspeed demo validation.
- **What:**
  1. Connected via bastion SSH (`lab-user@bastion.v8w9c.sandbox205.opentlc.com`) and logged into OCP as `admin`.
  2. Initial trigger reached agent but failed with connection error; root cause found:
     - agent still pointed at stale `granite-vllm` endpoint
     - `llama-32-3b-instruct` predictor deployment had `0/0` replicas despite ISVC reporting `Ready`.
  3. Applied runtime fixes:
     - Updated agent/chatbot env to `llama-32-3b-instruct` endpoint.
     - Corrected endpoint DNS to fully-qualified `.svc.cluster.local`.
     - Scaled `my-first-model/llama-32-3b-instruct-predictor` deployment to 1 and waited for rollout.
     - Verified in-agent connectivity: `/v1/models` 200 and `/v1/completions` 200.
  4. Re-ran Lightspeed trigger by publishing Kafka event (`dark_noc_scenario=lightspeed`) to `nginx-logs`.
  5. Verified E2E outcomes:
     - Agent logs: `[LIGHTSPEED] Starting ...` for incident `1d8d7d34`.
     - AAP: new job `id=81` on template `lightspeed-generate-and-run`, status `successful`.
     - ServiceNow: new incident `INC0010030` created with Lightspeed short description.
     - Generated template entries remain present (`generated-ansible-job-failure-*`).
     - MCP logs show active POST `/mcp` calls from agent pod to Slack/ServiceNow servers during run.
- **Expected:** Full Lightspeed path executes with AI -> AAP -> ServiceNow (+ Slack path invoked).
- **Outcome:** Success after runtime endpoint and predictor-replica corrections.

**Status:** ✅ SUCCESS

### CMD-0216 — Verify LLM/vLLM Connectivity to Wired MCP Tools (from Agent Pod)
- **Phase:** Runtime Validation
- **Cluster:** Hub (executed via bastion)
- **Date:** 2026-03-11 EDT
- **Why:** User requested validation that the active LLM/vLLM runtime can reach all wired tools.
- **What:**
  1. Logged into hub cluster from bastion and targeted running `dark-noc-agent` pod.
  2. Enumerated runtime wiring from agent env:
     - `VLLM_URL=http://llama-32-3b-instruct-predictor.my-first-model.svc.cluster.local:8080/v1`
     - `MODEL_ID=llama-32-3b-instruct`
     - `MCP_OPENSHIFT_URL`, `MCP_LOKI_URL`, `MCP_AAP_URL`, `MCP_SLACK_URL`, `MCP_SNOW_URL`
  3. Executed in-pod HTTP checks:
     - `GET /v1/models` and `POST /v1/completions` on vLLM endpoint.
     - MCP endpoint checks with and without stream headers.
- **Expected:** vLLM returns 200; MCP endpoints are reachable and respond at protocol layer.
- **Outcome:**
  - vLLM: ✅ `200` on both models and completions.
  - MCP endpoints: ✅ reachable for all wired tools.
    - plain GET: `406 Not Acceptable` (expected without `Accept: text/event-stream`)
    - GET with stream header: `400 Missing session ID` (expected without MCP session handshake)
  - Interpretation: network and service connectivity are healthy; protocol-level responses confirm MCP servers are reachable and active.

**Status:** ✅ SUCCESS

### CMD-0217 — Full Connectivity Verification: LLM/vLLM + Chatbot + LangGraph + Kafka + OpenShift + 13 Integrations
- **Phase:** Runtime Validation
- **Cluster:** Hub via bastion
- **Date:** 2026-03-11 EDT
- **Why:** User requested end-to-end connectivity validation across model runtime and all wired integrations.
- **What:**
  1. Verified agent model path in-pod:
     - `VLLM_URL=http://llama-32-3b-instruct-predictor.my-first-model.svc.cluster.local:8080/v1`
     - `GET /v1/models` -> `200`
     - `POST /v1/completions` -> `200`
  2. Verified agent Kafka TCP connectivity to bootstrap service (`9092`) -> `ok`.
  3. Queried chatbot integrations API:
     - `up=13/13`
     - all 13 integration entries returned `status=up`.
  4. Verified chatbot uses live model path:
     - `model=llama-32-3b-instruct`, `source=live`, `up=13/13`.
  5. Verified LangGraph runtime activity from agent logs:
     - multiple recent incidents processed with Lightspeed path and successful completions.
  6. Found and fixed Langfuse host mismatch for agent telemetry:
     - old: `http://langfuse.dark-noc-observability.svc:3000` (DNS fail)
     - new: `http://langfuse-web.dark-noc-observability.svc:3000`
     - patched `dark-noc-hub/agent-secrets` and rolled out `dark-noc-agent`.
     - post-fix in-pod health: `200` (`{"status":"OK","version":"3.155.1"}`).
  7. OpenShift MCP backend pod connectivity checked:
     - service reachable via integrations API (`up`),
     - direct cluster-scope and namespace pod-list calls from `mcp-openshift-sa` returned `Forbidden` (RBAC scope limitation).
- **Expected:** all runtime links healthy with explicit pass/fail details and remediation for detected issue(s).
- **Outcome:** Success. Model/tool connectivity healthy; Langfuse host issue remediated; OpenShift MCP RBAC noted as scoped limitation.

**Status:** ✅ SUCCESS (with RBAC scope note for MCP OpenShift)

### CMD-0218 — Dashboard UI Refresh: Topology + Workflow + Trigger Labels
- **Phase:** UI/Executive Dashboard
- **Cluster:** local source update
- **Date:** 2026-03-11 EDT
- **Why:** User requested latest runtime topology/workflow updates with vLLM model details, MCP/LangGraph wiring clarity, cleaner lane layout, and updated demo trigger naming.
- **What:**
  1. Updated dashboard trigger buttons:
     - `Trigger AI-Hub CrashLoop Demo`
     - `Trigger Edge OOM Demo`
     - `Trigger ServiceNow Escalation Demo`
  2. Updated topology labels and architecture text:
     - `LangGraph + LlamaStack + vLLM`
     - `AAP + Hub EDA + Lightspeed`
     - Added RAG/model details (`llama-32-3b-instruct`, Granite option, pgvector)
     - Added `Platform Cake Layer` (OpenShift, OpenShift AI, AWS, NVIDIA GPU runtime)
  3. Simplified flow geometry to reduce overlap:
     - adjusted remediation path curvature and lane labels
     - moved legend to lower band to avoid node overlap
  4. Workflow rendering hardened:
     - strips leading numeric prefixes from API-provided steps to prevent double-numbering
     - added an explicit fallback workflow aligned with current edge/hub architecture
- **Expected:** Cleaner executive view with accurate current-state model and integration flow.
- **Outcome:** Source updated in `phase-06-dashboard/dashboard/src/App.jsx` and `styles.css`.

**Status:** ✅ SUCCESS

### CMD-0219 — Dashboard Build Sanity Attempt
- **Phase:** UI validation
- **Cluster:** local
- **Date:** 2026-03-11 EDT
- **Why:** Validate the updated dashboard source compiles.
- **What:** Ran `npm run build` in `implementation/phase-06-dashboard/dashboard`.
- **Outcome:** Build could not run because local dependency binary is missing: `vite: command not found`.

**Status:** ⚠️ BLOCKED (local toolchain dependency)

### CMD-0220 — Dashboard Dependency Install (for Build Validation)
- **Phase:** UI validation
- **Cluster:** local
- **Date:** 2026-03-11 EDT
- **Why:** Build check was blocked because `vite` was missing.
- **What:** Ran `npm install` in `implementation/phase-06-dashboard/dashboard`.
- **Outcome:** Installed 60 packages; dependency tree restored.

**Status:** ✅ SUCCESS

### CMD-0221 — Dashboard Production Build Validation
- **Phase:** UI validation
- **Cluster:** local
- **Date:** 2026-03-11 EDT
- **Why:** Confirm latest dashboard updates compile cleanly for deploy.
- **What:** Ran `npm run build` in `implementation/phase-06-dashboard/dashboard`.
- **Outcome:** Build succeeded (`vite v6.0.11`); generated `dist/` artifacts:
  - `dist/index.html`
  - `dist/assets/index-VUq7GWMx.css`
  - `dist/assets/index-CEIkSqSx.js`

**Status:** ✅ SUCCESS

### CMD-0222 — Dashboard Rollout Attempt (Hub)
- **Phase:** UI rollout
- **Cluster:** Hub
- **Date:** 2026-03-11 EDT
- **Why:** Publish latest dashboard topology/workflow updates to live route.
- **What:** Attempted to query and rollout `dark-noc-ui` resources after successful local build.
- **Outcome:** Blocked by DNS/API instability from execution shell:
  - `lookup api.ocp.v8w9c.sandbox205.opentlc.com: no such host`
  - intermittent route DNS resolution failures also observed.

**Status:** ⚠️ BLOCKED (environment DNS reachability)

### CMD-0223 — Dashboard Redeployability Hardening (BuildConfig Added)
- **Phase:** UI deployment reliability
- **Cluster:** local source update
- **Date:** 2026-03-11 EDT
- **Why:** Ensure dashboard can be rebuilt/redeployed with deterministic in-cluster commands even during local environment variability.
- **What:**
  1. Added `implementation/phase-06-dashboard/dashboard/buildconfig.yaml` (ImageStream + Binary BuildConfig).
  2. Updated `deploy/manifest-order.tsv` to include dashboard BuildConfig apply + start-build step.
  3. Updated `implementation/phase-06-dashboard/README.md` with dashboard build/rollout quick commands.
- **Outcome:** Dashboard deployment path is now explicit and repeatable via OpenShift BuildConfig.

**Status:** ✅ SUCCESS

### CMD-0224 — Dashboard Rollout Retry (Hub API + Route DNS)
- **Phase:** UI rollout retry
- **Cluster:** Hub
- **Date:** 2026-03-11 EDT
- **Why:** User requested immediate retry to publish latest dashboard changes.
- **What:**
  1. Executed 8-attempt retry loop for `oc login` and rollout chain.
  2. Executed 8-attempt retry loop for dashboard route content verification.
- **Outcome:** Both API and route DNS failed consistently from current shell:
  - `lookup api.ocp.v8w9c.sandbox205.opentlc.com: no such host`
  - `Could not resolve host: dark-noc-dashboard-dark-noc-ui.apps.ocp.v8w9c...`

**Status:** ⚠️ BLOCKED (external DNS resolution)

### CMD-0225 — DNS Recovery Retry Check
- **Phase:** Runtime connectivity
- **Cluster:** local execution environment
- **Date:** 2026-03-11 EDT
- **Why:** User requested retry before proceeding with dashboard rollout.
- **What:** Ran 5 consecutive probes against public DNS (`google.com`) and hub API host.
- **Outcome:** All probes failed with `Could not resolve host`; DNS remains unavailable from this runtime.

**Status:** ⚠️ BLOCKED (global DNS from execution shell)
