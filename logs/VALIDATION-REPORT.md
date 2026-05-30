# Dark NOC Demo Package Validation Report

**Package Folder:** `darknoc-demo`  
**Generated On:** 2026-05-30  
**Validation Type:** Static package validation + live GitOps/runtime snapshot

## 1) Packaging Outcome

- Source packaged from `dark-noc/` into clean `darknoc-demo/`.
- Excluded artifacts:
  - `.DS_Store`
  - `__pycache__/`
  - `*.pyc`
- Removed empty directories after copy.
- Re-templated hardcoded credentials in reusable manifests:
  - `implementation/phase-04-automation/aap/automation-controller.yaml`
  - `implementation/phase-02-data-pipeline/postgresql/langfuse-postgres-cluster.yaml`
  - `implementation/phase-02-data-pipeline/postgresql/pgvector-cluster.yaml`

## 2) Static Validation (`scripts/validate-demo.sh`)

**Result:** PASS

Checks executed:
1. Required folder structure exists.
2. Required tracking files exist (`COMMANDS-LOG.md`, `PROGRESS-TRACKER.md`, redeploy runbook).
3. No cache artifacts (`.DS_Store`, `*.pyc`).
4. Secret-pattern scan for obvious embedded live tokens.
5. Deployment inventory threshold check.
6. Script executable bit checks.
7. Placeholder credential marker check.

File inventory from validation:
- YAML files: `55`
- Python files: `12`
- Markdown files: `35`
- Placeholder markers: `15`

## 3) Live Runtime/Build Snapshot (Hub)

Cluster context:
- user: `admin`
- api: `https://api.ocp.z6ch9.sandbox2776.opentlc.com:6443`

GitOps:
- All 14 Argo applications are `Synced Healthy`.
- Latest release branch: `ocpai-3.4`

Deployments at capture time:
- `dark-noc-ui`: `dark-noc-dashboard` `1/1`, `dark-noc-chatbot` `1/1`
- `dark-noc-mcp`: all 6 MCP deployments `1/1`
- `dark-noc-hub`: `dark-noc-agent` `1/1`

Runtime images:
- `quay.io/msugur/auto-darknoc:agent-ocpai-3.4-ready`
- `quay.io/msugur/auto-darknoc:mcp-openshift-ocpai-3.4-ready`
- `quay.io/msugur/auto-darknoc:mcp-lokistack-ocpai-3.4-ready`
- `quay.io/msugur/auto-darknoc:mcp-kafka-ocpai-3.4-ready`
- `quay.io/msugur/auto-darknoc:mcp-aap-ocpai-3.4-ready`
- `quay.io/msugur/auto-darknoc:mcp-slack-ocpai-3.4-ready`
- `quay.io/msugur/auto-darknoc:mcp-servicenow-ocpai-3.4-ready`
- `quay.io/msugur/auto-darknoc:dashboard-ocpai-3.4-ready`
- `quay.io/msugur/auto-darknoc:chatbot-ocpai-3.4-ready`

Final end-to-end rehearsal:
- Incident `675de4c2-b537-403f-a259-31bbcc53f6cf`
- AAP job `8` completed `successful`
- ServiceNow ticket `INC0010014`
- Audit record written
- Integrations API reported `15/15 up`

## 4) Artifacts Included for Reuse

- Full implementation manifests and deployment assets under `implementation/`
- Config templates under `configs/`
- Operational scripts under `scripts/`
- Runbook/deployment docs under `docs/`
- Project tracker and command history under `logs/`
- Package inventory index: `logs/PACKAGE-INVENTORY.txt`

## 5) Recommended Next Action

For a new environment, start from:
1. `docs/deployment/redeploy-runbook.md`
2. `scripts/preflight.sh`
3. `implementation/phase-01-foundation/COMMANDS.md`
4. `scripts/validate-demo.sh` before each release handoff
