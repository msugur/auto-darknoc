# Autonomous Dark NOC Quickstart Proposal

## Document metadata
- Proposal target: New Red Hat-style quickstart experience for autonomous edge operations
- Source repository: https://github.com/msugur/auto-darknoc
- Repository branch/reference used: `main` at commit `4d5c836390d291c1235e650053f507458fe246d2`
- Current solution model in repo: Hub + Edge GitOps deployment with Argo CD app-of-apps
- Date: 2026-04-03

## Executive summary
Autonomous Dark NOC is a production-oriented, AI-assisted edge operations solution that combines OpenShift, OpenShift AI, AAP/EDA, ACM, Kafka, Loki, Langfuse, and a LangGraph+MCP agent mesh. The solution already includes most of the technical assets required for a compelling quickstart, including phased manifests, GitOps composition, validation scripts, and executive dashboards.

The highest-value quickstart is a guided "incident-to-remediation" experience that deploys hub + edge components, triggers a controlled edge failure, and demonstrates closed-loop auto-remediation plus escalation with full evidence. The quickstart should prioritize deterministic setup, explicit validation gates, secure runtime secret handling, and clear business outcome telemetry (MTTD, MTTR, auto-remediation %, escalation %).

The repository is close to this target. The primary release-readiness gap is consistency between docs and executable automation for one-click flow, specifically that `ONE_CLICK_DEPLOY.md` references scripts not currently present on `origin/main` (`scripts/one-click-gitops.sh`, `scripts/render-prod-secrets.sh`).

## **Please describe your vision for a new quickstart**
### What would you like to see?
I want a quickstart that feels like an operational product experience, not a manifest walkthrough.

1. A single guided path that starts with minimal inputs and ends with a successful incident auto-remediation demonstration.
2. A built-in predeploy gate that verifies platform versions and capacity before deployment starts.
3. Deterministic GitOps orchestration using the existing app-of-apps structure and sync waves.
4. Automatic generation of a post-run evidence pack suitable for leadership review.
5. A two-lane experience in one quickstart:
   - Demo lane: fast path to first value.
   - Production lane: hardening and governance controls.

The target user experience should be:
1. Enter cluster and integration inputs.
2. Click deploy.
3. Watch deployment progress by stage.
4. Trigger a demo failure.
5. Observe remediation and escalation evidence.
6. Export a summary report.

The quickstart should preserve these architectural strengths already present in the repo:
1. Hub/edge split with ACM and Argo control.
2. LangGraph orchestration with MCP tools.
3. AAP/EDA for procedural automation.
4. Kafka + logging as event backbone.
5. Dashboard + Grafana + Langfuse for explainability and ops trust.

## **Is your suggestion related to a specific use case? Please describe.**
### A clear description of what the quickstart demonstrates and its value.
Yes. The use case is autonomous incident operations for distributed edge infrastructure in telco-style environments.

The quickstart demonstrates this end-to-end flow:
1. A workload failure is introduced on an edge cluster (`OOMKilled` or `CrashLoopBackOff`).
2. Edge telemetry is forwarded to hub Kafka.
3. The AI agent classifies and reasons about the incident using model inference + RAG context.
4. The agent executes remediation via AAP/EDA for known patterns.
5. If confidence is low or remediation fails, the system escalates via ServiceNow and Slack.
6. All decisions and actions are traceable in Langfuse and visualized in dashboard and Grafana.

Business value demonstrated:
1. Faster operational response from minutes/hours to sub-minute/sub-two-minute flows for common incidents.
2. Reduced alert fatigue through policy-driven auto-remediation.
3. Better compliance and auditability through trace and event evidence.
4. Better executive communication through business impact and SLO panels.

Operational KPIs this quickstart should surface by default:
1. Mean time to detect (MTTD).
2. Mean time to remediate (MTTR).
3. Auto-remediation rate.
4. Escalation rate.
5. AAP job success rate.
6. AI confidence trends.

## **Describe the solution you'd like to see**
### A clear description of what you want to happen, or how you'd build it.
I would build the quickstart as a structured, outcome-first workflow with strict gates and explicit outputs.

### 1) Input and environment model
The quickstart should ask only for:
1. Hub API URL + auth.
2. Edge API URL + auth.
3. Optional ServiceNow and Slack credentials.
4. Optional Quay pull credentials.

It should then render runtime inputs into generated secret artifacts from templates, with a hard rule that no live credentials are committed.

### 2) Predeploy gate (must-pass)
The quickstart should run and enforce checks before sync:
1. OpenShift version compliance (target currently 4.21.x per repo gate).
2. Operator readiness for required stack.
3. Node/pod capacity checks and optional worker scale action.
4. Route/domain reachability checks.
5. Destination cluster registration checks for Argo (`edge-cluster` mapping).

The current repo already has this pattern in `gitops/prod/stacks/hub/predeploy-gates/predeploy-job.yaml` and `predeploy-rbac.yaml`; the quickstart should expose its results clearly.

### 3) GitOps orchestration model
The quickstart should use the existing app-of-apps structure:
1. Root app: `gitops/prod/argocd/root-application.yaml`.
2. Child apps: 14 environment apps under `gitops/prod/apps/*.yaml`.
3. Sync-wave orchestration from predeploy to notification publication.

Recommended quickstart stage mapping:
1. Stage A: predeploy (`-6`).
2. Stage B: foundation/minio/data pipeline (`-5` to `-3`).
3. Stage C: AI and automation (`-2` to `-1`).
4. Stage D: agent and UI (`0` to `1`).
5. Stage E: observability and notifications (`2` to `3`).

### 4) AI + automation integration behavior
The quickstart should validate these contracts explicitly:
1. Model endpoint binding for agent/chatbot from `dark-noc-model-binding`.
2. AAP template availability for standard and Lightspeed paths.
3. MCP server health across OpenShift, Loki, Kafka, AAP, Slack, ServiceNow.
4. Incident audit topic writes and consumption.

### 5) Demo trigger and proof flow
The quickstart should include two mandatory test scenarios:
1. OOMKill auto-remediation scenario.
2. Escalation scenario with ServiceNow + Slack.

Evidence output should include:
1. AAP job ID and status.
2. ServiceNow incident number (when escalated).
3. Slack message permalink or timestamp.
4. Langfuse trace ID.
5. Dashboard incident timeline record.
6. SLO snapshot from Grafana and dashboard panels.

### 6) Operational UX and dashboards
The quickstart should explicitly feature the current executive UI capabilities already present in `implementation/phase-06-dashboard/dashboard/src/App.jsx`:
1. Business Impact Panel.
2. Critical SLO (Live Data).
3. Demo Mode UI Trigger.
4. Integration Status Matrix.
5. Access Center (Live Credentials).
6. Incident Movie Replay.
7. Edge + Hub workflow diagram with layered infrastructure context.

### 7) Day-2 hardening profile
After quickstart success, the same guide should provide a hardening section:
1. Replace default credentials and rotate secrets.
2. Move runtime secrets to enterprise secret manager.
3. Lock AppProject source/destination/RBAC scopes further.
4. Add backup/restore policy for data plane components.
5. Pin image digests for immutable release promotion.
6. Add policy checks and admission controls for changes.

### 8) Release-readiness fixes required now
To make this truly one-click for any new cluster, these are immediate fixes:
1. Resolve doc/code mismatch in `ONE_CLICK_DEPLOY.md` by adding or removing references to missing scripts.
2. Align `PORTABLE-DEPLOYMENT.md`, `RECOVERY-CHECKLIST.md`, and one-click docs into one canonical path.
3. Ensure all validation scripts support token and username/password auth consistently.
4. Add a single command that orchestrates: preflight, render secrets, bootstrap Argo, sync root, validate.
5. Add CI lint checks that fail if docs reference non-existent scripts.

## **Additional context**
### Add any other context or screenshots about the suggestion here.

### Existing repo assets that strongly support the quickstart
1. Deployment phases and ordered manifests:
   - `deploy/manifest-order.tsv`
   - `implementation/phase-01..08`
2. GitOps composition:
   - `gitops/prod/argocd/*`
   - `gitops/prod/apps/*`
   - `gitops/prod/stacks/*`
3. Validation tooling:
   - `scripts/preflight.sh`
   - `scripts/deploy-dry-run.sh`
   - `scripts/deploy-apply.sh`
   - `scripts/deploy-validate.sh`
4. Recovery and portability:
   - `RECOVERY-CHECKLIST.md`
   - `gitops/prod/docs/PORTABLE-DEPLOYMENT.md`
5. Observability and executive reporting:
   - `gitops/prod/stacks/hub/observability/*`
   - `gitops/prod/docs/OBSERVABILITY_DASHBOARDS.md`

### Suggested screenshot set for the quickstart page
1. Argo CD app tree with all apps `Synced/Healthy`.
2. Dashboard with Business Impact + Critical SLO + Incident Movie Replay.
3. Edge+Hub workflow visualization panel.
4. AAP Jobs page showing remediation run.
5. Langfuse trace detail for the same incident.
6. Grafana executive dashboard with SLO and LLM/GPU panels.
7. ServiceNow incident record and Slack channel notification thread.

### Suggested quickstart acceptance criteria
1. Deployment completes from clean clusters without manual YAML editing.
2. First incident is auto-remediated within agreed demo SLA.
3. Escalation scenario produces both ITSM and chat notification artifacts.
4. End-to-end evidence export is generated and shareable.
5. Teardown and redeploy can be repeated with the same steps.

### Suggested rollout plan for the quickstart itself
1. Milestone 1: documentation-script consistency and one-command bootstrap.
2. Milestone 2: guided validation with auto evidence export.
3. Milestone 3: production hardening profile and policy checks.
4. Milestone 4: reusable quickstart package publication.

## Final recommendation
Proceed with a new quickstart centered on "Autonomous Edge Incident Remediation" using the existing GitOps architecture. The repository already contains nearly all required building blocks. Closing the one-click script consistency gap and packaging validation/evidence flow will make this quickstart both technically robust and compelling for customer-facing demos and field adoption.
