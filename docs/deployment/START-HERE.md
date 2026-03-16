# Dark NOC Start Here

This is the fastest path to redeploy this solution from this repository.

## 1) Prepare Access

1. Log in to hub cluster (`oc login ...`).
2. Log in to edge cluster (`oc login ...`).
3. Verify both contexts are reachable with `oc whoami` and `oc get ns`.

## 2) Configure Environment

1. Copy templates:
   - `configs/hub/env.sh.example` -> `configs/hub/env.sh`
   - `configs/edge/env.sh.example` -> `configs/edge/env.sh`
2. Fill cluster URLs, tokens, and integration endpoints/secrets.
3. Source env:
   - `source configs/hub/env.sh`

## 3) Run Preflight

1. Execute `scripts/preflight.sh`.
2. If pod-capacity is constrained on hub, scale worker capacity before continuing.

## 4) Deploy by Phase (Strict Order)

1. `implementation/phase-01-foundation/`
2. `implementation/phase-02-data-pipeline/`
3. `implementation/phase-03-ai-core/`
4. `implementation/phase-04-automation/`
5. `implementation/phase-05-agent-mcp/`
6. `implementation/phase-06-dashboard/`
7. `implementation/phase-07-edge-workloads/`
8. `implementation/phase-08-validation/`

Use each phase `README.md` and `COMMANDS.md` as the execution source.

### Phase 03 model selection (recommended)

Before applying Phase 03 AI manifests, select a model profile (AI Hub catalog URI) and render manifests:

1. Edit profile in `implementation/phase-03-ai-core/models/profiles/*.env`.
2. Render:
   - `./scripts/render-model-profile.sh --profile <profile-name>`
3. Apply rendered files from `implementation/phase-03-ai-core/generated/`.
4. Restart:
   - `oc -n dark-noc-hub rollout restart deploy/dark-noc-agent`
   - `oc -n dark-noc-ui rollout restart deploy/dark-noc-chatbot`

Or use the orchestrated deploy layer:
- `deploy/manifest-order.tsv`
- `scripts/deploy-dry-run.sh`
- `scripts/deploy-apply.sh`
- `scripts/deploy-validate.sh`

## 4.1) Lightspeed-Specific Ordering (Must Follow)

1. Complete Phase 04 AAP deployment:
   - `implementation/phase-04-automation/aap/automation-controller.yaml`
   - `implementation/phase-04-automation/aap/eda-controller.yaml`
2. Configure Lightspeed demo template path:
   - `implementation/phase-04-automation/aap/lightspeed-demo-template.md`
3. Deploy Phase 05 MCP AAP + agent:
   - `implementation/phase-05-agent-mcp/mcp-servers/mcp-aap/`
   - `implementation/phase-05-agent-mcp/agent/`
4. Verify agent can execute Lightspeed workflow end-to-end:
   - generated playbook metadata in incident audit
   - AAP job success
   - ServiceNow ticket and Slack notification
5. Validate generated AAP template entry is visible in AAP Job Templates.

## 5) Validate End-to-End

1. Run `implementation/phase-08-validation/test-scenarios.sh`.
2. Validate:
   - AAP job success
   - Lightspeed path: generated template entry appears in AAP
   - ServiceNow incident creation
   - Slack notification
   - Dashboard/Chatbot updates

## 6) Use These as Source of Truth

1. `docs/deployment/redeploy-runbook.md`
2. `logs/PROGRESS-TRACKER.md`
3. `logs/COMMANDS-LOG.md`
4. `logs/session-notes/`

## 7) Optional Cleanup

1. Remove all deployed components with `scripts/teardown.sh`.
