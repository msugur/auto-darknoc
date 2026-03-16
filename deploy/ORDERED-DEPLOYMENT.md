# Ordered Deployment (Dependency-Wired)

This is the canonical deployment workflow for new engineers.

## 0) Prepare local env

1. `cp configs/hub/env.sh.example configs/hub/env.sh`
2. `cp configs/edge/env.sh.example configs/edge/env.sh`
3. Fill values.
4. `source configs/hub/env.sh`

Optional access workbook:
- `configs/access/ACCESS-CENTER.template.md`

## 1) Run preflight

```bash
./scripts/preflight.sh
```

## 2) Dry-run (full ordered plan)

Client-side dry-run:
```bash
./scripts/deploy-dry-run.sh
```

Server-side dry-run (stricter):
```bash
./scripts/deploy-dry-run.sh --server
```

## 3) Apply in dependency order

Apply everything that is `action=apply` in the ordered plan:
```bash
./scripts/deploy-apply.sh
```

Run up to a specific step:
```bash
./scripts/deploy-apply.sh --through 034
```

Run a specific phase only:
```bash
./scripts/deploy-apply.sh --phase data-pipeline
```

## 4) Execute manual/build/helm steps

`deploy-apply.sh` will print all `manual`/`helm`/`script` actions with file references. Complete each before moving to next phase.

Key manual checkpoints:
1. Fill MachineSet placeholders (`phase-01-foundation/machineset/check-machineset.sh`).
2. Build pgvector image from BuildConfig.
3. Fill Langfuse secrets and run Helm install using `langfuse-values.yaml`.
4. Configure AAP Lightspeed template via `phase-04-automation/aap/lightspeed-demo-template.md`.
5. Build/push all MCP + agent images before Phase 05 deployments.

## 5) Validate each phase

```bash
./scripts/deploy-validate.sh foundation
./scripts/deploy-validate.sh data-pipeline
./scripts/deploy-validate.sh ai-core
./scripts/deploy-validate.sh automation
./scripts/deploy-validate.sh agent-mcp
./scripts/deploy-validate.sh dashboard
./scripts/deploy-validate.sh edge-workloads
```

Full validation:
```bash
./scripts/deploy-validate.sh all
```

## 6) Run E2E tests

```bash
./implementation/phase-08-validation/test-scenarios.sh
./scripts/validate-demo.sh
```

## 7) Ordered manifest source

- `deploy/manifest-order.tsv` is the source-of-truth order list.
- Update it first when adding/changing deployment steps.
