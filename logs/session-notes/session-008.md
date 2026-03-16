# Session 008 — Lightspeed Upsert Stabilization

**Date**: 2026-03-11
**Status**: ✅ COMPLETE

## Objectives
- Recover `mcp-aap` rollout failure.
- Ensure latest Lightspeed upsert code is deployed from `darknoc-demo` source.
- Validate end-to-end Lightspeed workflow with generated AAP template visibility.

## Key Fixes Applied
1. Fixed `mcp-aap` deployment env mismatch:
   - Root cause: deployment expected secret key `password`; secret contained `AAP_PASSWORD`.
   - Action: `oc set env deploy/mcp-aap --from=secret/aap-admin-secret` and rollout restart.
2. Synced code trees and rebuilt from `darknoc-demo`:
   - Updated files:
     - `implementation/phase-05-agent-mcp/agent/agent.py`
     - `implementation/phase-05-agent-mcp/agent/state.py`
     - `implementation/phase-05-agent-mcp/mcp-servers/mcp-aap/server.py`
3. Fixed upsert target playbook path:
   - Use stable SCM playbook `playbooks/lightspeed-generate-and-run.yaml` for generated template entries.
4. Hardened MCP AAP upsert idempotency:
   - `upsert_job_template` now treats already-desired template state as success on intermittent patch 400.

## Validation Evidence
- Final run trigger: `lightspeed` demo event queued.
- Latest incident: `c914d202-6b78-4edb-bdf1-4379452a20a0`.
- AAP: job `79` succeeded (template `lightspeed-generate-and-run`).
- ServiceNow: `INC0010029` created.
- Generated template visible in AAP:
  - Name: `generated-ansible-job-failure-f0ec346d`
  - ID: `15`
  - Playbook: `playbooks/lightspeed-generate-and-run.yaml`
- Agent logs: latest Lightspeed run completed without new upsert-warning line.

## Notes
- Source-of-truth deployment path should remain `darknoc-demo` to avoid drift from `dark-noc`.
- Existing historical warnings in logs remain for prior runs and are expected.
