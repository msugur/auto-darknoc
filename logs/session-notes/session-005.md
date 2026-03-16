# Session 005 — Phase 05 MCP Servers Built, Deployed, and Cleaned

**Date**: 2026-03-06
**Session Goal**: Complete MCP server deployment on hub and clean failed build artifacts.
**Status**: ✅ COMPLETE

---

## Completed This Session

- Added missing Dockerfiles for MCP servers:
  - `mcp-aap`, `mcp-kafka`, `mcp-lokistack`, `mcp-servicenow`, `mcp-slack`
- Fixed `mcp-openshift` Dockerfile to provide `oc` command path expected by `server.py`.
- Created/updated MCP prerequisite secrets in `dark-noc-mcp`:
  - `edge-01-kubeconfig`
  - `aap-admin-secret` (placeholder password)
  - `slack-secrets` (placeholder bot token)
- Built all six MCP images in OpenShift internal registry:
  - `mcp-openshift-2`
  - `mcp-lokistack-2`
  - `mcp-kafka-1`
  - `mcp-aap-1`
  - `mcp-slack-1`
  - `mcp-servicenow-2`
- Applied `mcp-servers-deployment.yaml` and verified rollouts:
  - `mcp-openshift`, `mcp-lokistack`, `mcp-kafka`, `mcp-aap`, `mcp-slack`, `mcp-servicenow` all `1/1 Available`.
- Verified runtime startup logs for each MCP pod (`Uvicorn running on 0.0.0.0`).

## Fixes Applied

1. **Dependency conflict (uvicorn)**
- Root cause: `fastmcp==3.0.2` requires `uvicorn>=0.35`, but files were pinned to `0.32.0`.
- Fix: updated all MCP `requirements.txt` files to `uvicorn==0.37.0`.

2. **Dependency conflict (httpx)**
- Root cause: `fastmcp==3.0.2` requires `httpx>=0.28.1`, but some files pinned `0.27.0`.
- Fix: updated MCP `requirements.txt` for `aap`, `lokistack`, `slack`, `servicenow` to `httpx==0.28.1`.

3. **Missing MCP build artifacts**
- Root cause: only `mcp-openshift` originally had a Dockerfile.
- Fix: added Dockerfiles for the other five MCP servers.

## Cleanup Performed

- Deleted failed build objects:
  - `mcp-openshift-1`
  - `mcp-lokistack-1`
- Removed corresponding failed build pods.
- Current build set in `dark-noc-mcp` is clean and complete.

## Current State Summary

- Phase 05 MCP deployment is operational on hub.
- Agent deployment remains healthy and consuming Kafka.
- Phase 06 Step 1 completed:
  - `servicenow-mock` image built and deployed in `dark-noc-servicenow-mock`.
  - Route health check returns: `{"status":"ok","incidents_count":0}`.
- Phase 06 Step 2/3 completed:
  - Added missing `dashboard/` React project and `chatbot/` FastAPI backend files.
  - Built/deployed in `dark-noc-ui`:
    - `dark-noc-chatbot-1`
    - `dark-noc-dashboard-1`
  - Verified routes:
    - `/health` and `/api/summary` on chatbot route return HTTP 200 with valid JSON.
    - dashboard route serves built `index.html`.
- Remaining for full end-to-end MCP tool execution:
  - Replace placeholder `slack-secrets` token with real `xoxb-...`.
  - Apply/activate AAP license (current job launch error: `License is missing`).

## AAP + Slack Completion Progress (Continuation)

- AAP deployment advanced:
  - Applied `automation-controller.yaml` in namespace `aap`.
  - Core pods are up: `aap-web`, `aap-task`, `aap-postgres`.
  - AAP API reachable and authenticated at `/api/v2/*`.
- MCP AAP integration updated:
  - `dark-noc-mcp/aap-admin-secret` updated with real AAP admin password.
  - `mcp-aap` deployment updated to `AAP_URL=http://aap-service.aap.svc` and restarted.
  - Confirmed AAP template bootstrap: created `restart-nginx` (`id=8`).
- Current blocker:
  - Resolved with uploaded manifest (`ce63ce2e-...zip`) via AAP config API.
  - `license_info` now populated (`SER0569` trial, compliant=true).
  - `restart-nginx` template launch now succeeds (`job id 1`, status `successful`).
  - Remaining work is replacing bootstrap demo playbook (`hello_world.yml`) with real remediation project/playbooks.
- Slack status:
  - `slack-secrets` updated with provided token and channel set to `#demos`.
  - Final token updated to bot token `xoxb-...`.
  - Validation succeeded:
    - `auth.test` => `ok:true`
    - `chat.postMessage` => `ok:true` (channel `C08MUDSNHED`)
  - Slack integration is now unblocked and operational.
