# Dark NOC Demo — Reusable Package

This `darknoc-demo` folder is the clean, reusable deployment package derived from the current validated solution state.

## Included
- `implementation/` phase-by-phase manifests, Dockerfiles, BuildConfigs, MCP servers, agent, dashboard.
- `configs/` environment templates (`env.sh.example` for hub/edge).
- `scripts/` preflight + teardown + package validation script.
- `docs/` architecture, deployment runbook, executive deck/slides.
- `playbooks/` canonical `restart-nginx.yaml`.
- `logs/` project tracker + commands log + session notes.

## Clean-up Applied
- Removed cache/system artifacts from package (`.DS_Store`, `*.pyc`, `__pycache__`).
- Removed empty placeholder folders.
- Templated hardcoded credentials in:
  - `implementation/phase-04-automation/aap/automation-controller.yaml`
  - `implementation/phase-02-data-pipeline/postgresql/langfuse-postgres-cluster.yaml`
  - `implementation/phase-02-data-pipeline/postgresql/pgvector-cluster.yaml`

## Dry-Run / Validation
Run:

```bash
cd darknoc-demo
./scripts/validate-demo.sh
```

## Redeploy Entry Points
1. `docs/deployment/redeploy-runbook.md`
2. `scripts/preflight.sh`
3. `implementation/phase-01-foundation/COMMANDS.md`
4. `implementation/phase-02-data-pipeline/COMMANDS.md`

## Git Readiness
Folder is ready for a clean repo initialization:

```bash
cd darknoc-demo
git init
git add .
git commit -m "Initial reusable Dark NOC demo package"
```
