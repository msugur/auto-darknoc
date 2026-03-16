# Dark NOC Demo Package Validation Report

**Package Folder:** `darknoc-demo`  
**Generated On:** 2026-03-10  
**Validation Type:** Static package validation + live runtime/build snapshot

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
- api: `https://api.ocp.v8w9c.sandbox205.opentlc.com:6443`

Deployments at capture time:
- `dark-noc-ui`: `dark-noc-dashboard` `1/1`, `dark-noc-chatbot` `1/1`
- `dark-noc-mcp`: all 6 MCP deployments `1/1`
- `dark-noc-hub`: `dark-noc-agent` `1/1`

Recent successful builds:
- Dashboard: `dark-noc-dashboard-10` (latest, complete)
- Chatbot: `dark-noc-chatbot-11` (latest, complete)
- Agent: `dark-noc-agent-16` (complete)
- MCP ServiceNow: `mcp-servicenow-6` (complete)

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
