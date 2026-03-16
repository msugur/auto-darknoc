# Session 007 — Dashboard Demo Mode + Deployment Continuation

**Date**: 2026-03-10
**Session Goal**: Continue deployment work by adding a UI-first E2E trigger path and validating rollout.
**Status**: ✅ COMPLETE

---

## What Was Implemented

- Added a new chatbot endpoint for demo stimulation:
  - `POST /api/demo/trigger`
  - accepts `{ "scenario": "oom|crashloop|escalation", "site": "edge-01" }`
  - publishes structured incident event to Kafka topic `nginx-logs`
  - returns execution guidance + direct links to AAP jobs, ServiceNow incidents, Slack, and Langfuse.

- Upgraded dashboard UI with **Demo Mode (UI Trigger)**:
  - One-click buttons for `OOM`, `CrashLoop`, `Escalation`
  - Displays queued event details and quick-follow links for operator walkthrough.

- Updated files:
  - `implementation/phase-06-dashboard/chatbot/main.py`
  - `implementation/phase-06-dashboard/chatbot/requirements.txt`
  - `implementation/phase-06-dashboard/dashboard/src/App.jsx`
  - `implementation/phase-06-dashboard/dashboard/src/styles.css`

---

## Deployment Evidence

- Chatbot:
  - Build `dark-noc-chatbot-11` completed.
  - Rollout completed successfully.
  - `/health` returned `status=ok`.

- Dashboard:
  - Build `dark-noc-dashboard-8` completed.
  - Rollout completed successfully.

- Integrations API:
  - `/api/integrations` reported `up=12/12`.

---

## Notes / Temporary Constraint

- During direct POST validation to `/api/demo/trigger` from this execution sandbox, DNS resolution intermittently failed (`Could not resolve host`).
- Health and integrations checks remained successful; deployment itself is healthy.
- Next session should run one in-UI button trigger and capture the produced event + downstream evidence (AAP job increment, ServiceNow incident, Slack message).

---

## Next Actions

- Trigger one `OOM` and one `Escalation` scenario from the dashboard UI.
- Verify and screenshot:
  - AAP job execution
  - ServiceNow incident creation/link
  - Slack correlated message
  - NOC chat summary query response
- Append artifacts to `docs/presentation` and update `PROGRESS-TRACKER.md` Phase 08 rehearsal line.

---

## Follow-up Fix (2026-03-10)

- User-reported issue: AAP remediation failed after dashboard `CrashLoopBackOff` trigger.
- Root cause confirmed from AAP job `27` stdout: edge cluster API token expired (`401 Unauthorized`).
- Corrective action:
  - Rotated AAP credential `edge-01-k8s` with fresh edge token.
  - Relaunched template `restart-nginx`.
- Validation result:
  - Job `29` successful.
  - nginx rollout restart and pod Running verification passed.

## Executive Topology Refresh (2026-03-10)

- Upgraded dashboard topology into executive visual format with curved arrows and flow legend.
- Added explicit stack product labels for edge, hub AI control plane, and data/MCP integration zone.
- Updated architecture overview with Mermaid-based technical topology and lane-based workflow framing.
- Local UI build check skipped because local `vite` binary is not installed in this workspace; OpenShift build remains deployment verifier.

## Live Deployment — Executive Topology UI (2026-03-10)

- Built dashboard from updated source as `dark-noc-dashboard-9`.
- Forced dashboard rollout restart to ensure route served newest image.
- Verified live route now references updated asset bundle:
  - `index-Bls6KqlW.js`
  - `index-lB3hVDk6.css`
- Executive topology view is now live in production route.
