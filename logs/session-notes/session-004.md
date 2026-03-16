# Session 004 — Phase 03 Hub Progress + LlamaStack Blocker

**Date**: 2026-03-04
**Session Goal**: Continue fixing deployment after Phase 02 completion; advance AI Core on hub.
**Status**: 🔄 IN PROGRESS

---

## Completed This Session

- Confirmed hub runtime health:
  - `granite-vllm` InferenceService is `Ready=True`.
  - Kafka cluster and topics healthy.
  - Hub CLF/Loki collector running (`instance` DaemonSet healthy).
- Validated vLLM endpoint from inside predictor pod:
  - `/v1/models` returned model list with `granite-4-h-tiny`.
- Reworked `phase-03-ai-core/llamastack/llamastack-distribution.yaml` to current `llamastack.io/v1alpha1` shape.
- Fixed LLSD image authorization issue:
  - switched from unauthorized `quay.io/opendatahub/llamastack:0.3.5`
  - to operator-supported `distribution.name: rh-dev`.

## Current Blockers

1. **LlamaStack startup crash on hub**
- LLSD deployment mounts `dark-noc-llamastack-user-config` and expects `/etc/llama-stack/config.yaml`.
- Existing config content is from old schema (v2 dict-style `apis`) and fails with llama-stack `0.4.2.1+rhai0`.
- Error seen repeatedly:
  - `ValidationError: apis Input should be a valid list`
  - `providers Field required`

2. **Edge access token expired**
- Separate edge kubeconfig login failed with:
  - `The token provided is invalid or expired.`
- Edge work cannot continue until a new token is provided.

## Files Updated This Session

- `implementation/phase-03-ai-core/llamastack/llamastack-distribution.yaml`
- `logs/PROGRESS-TRACKER.md`
- `logs/COMMANDS-LOG.md`
- `logs/session-notes/session-004.md`

## Next Actions

1. Get a fresh edge login token and resume edge checks.
2. Patch `dark-noc-llamastack-user-config` to llama-stack 0.4 schema (providers + list-style apis), then verify LLSD `Available=True`.
3. After LLSD is stable, proceed to Phase 03 step 6 (RAG seed) and Phase 04 AAP deployment.

---

## Final Outcome Update (Session 004)

- LlamaStack blocker resolved on hub.
- Final LLSD state:
  - `dark-noc-llamastack` => `PHASE=Ready`, `AVAILABLE=1`, `SERVER VERSION=0.4.2.1+rhai0`.
- Key remediations that made it work:
  - aligned LLSD manifest to `llamastack.io/v1alpha1`
  - switched to operator-supported distribution (`rh-dev`)
  - set required runtime env vars (`POSTGRES_*`, `VLLM_*`, `INFERENCE_MODEL`)
  - granted `CREATE/USAGE` on schema `public` for DB user `langfuse`
  - added embedding provider env to satisfy `vllm-embedding` registration.

### Remaining Blocker
- Edge token refresh still required to continue edge-side deployment and validation steps.

---

## Edge Continuation Update

- Edge access restored with refreshed token.
- Verified edge runtime:
  - `dark-noc-edge` and `openshift-logging` active.
  - nginx running.
  - edge CLF `instance` healthy; collector DS ready.
- Failure simulator fixed and validated:
  - Image corrected to `quay.io/openshift/origin-cli:4.21`.
  - Patch command corrected to lower both memory limit and request.
  - One-shot job `nginx-oom-now` completed successfully.
- End-to-end log flow reconfirmed:
  - Fresh edge traffic generated.
  - Hub Kafka consumer on `nginx-logs` processed 5 messages.
- Residual note:
  - Edge collector still reports intermittent `AllBrokersDown` route disconnects; pipeline self-recovers and message delivery is working.

---

## Phase 03 Step 6 Completion Update (RAG Seed into pgvector)

- Status: ✅ COMPLETE
- Namespace: `dark-noc-rag`
- Runtime evidence:
  - `job.batch/rag-seed` is `Complete`.
  - `pgvector-postgres-1` is `Running`.
  - `documents` row count in `noc_rag` is `53`.

### Notes

- Live schema in `documents` is currently:
  - `id`, `content`, `embedding`, `metadata`
- The seeded rows are valid and queryable, but metadata currently does not include `source_file` keys (all rows returned as `unknown` when grouped by `metadata->>'source_file'`).
- This does not block Phase 03 completion; if per-runbook attribution is required in dashboard/analytics, update the seeder metadata mapping in a follow-up patch.

---

## RAG Documentation Corpus Update (2026-03-05)

- Added documentation ingestion pipeline files:
  - `implementation/phase-03-ai-core/rag/documentation-sources.yaml`
  - `implementation/phase-03-ai-core/rag/seed-product-docs.py`
  - `implementation/phase-03-ai-core/rag/rag-docs-seed-job.yaml`
- Ran `rag-docs-seed` Job on hub and loaded official docs/tool references into pgvector.
- Final RAG corpus counts in `noc_rag.documents`:
  - `runbook`: 53
  - `documentation`: 666
- Products ingested include OCP 4.21, OpenShift AI docs, ACM 2.15, AAP 2.5, Streams 3.1, Logging 6.4, Service Mesh 3.1, and supporting tool docs (Llama Stack, vLLM, pgvector, LangGraph, Langfuse, FastMCP).

### Agent Retrieval Enhancement

- Updated `phase-05-agent-mcp/agent/agent.py` RAG node to retrieve both:
  - `metadata.type = runbook`
  - `metadata.type = documentation`
- Prompt context changed from runbook-only to combined knowledge context for RCA.

---

## Phase 05 Agent Deployment Update (2026-03-05)

- Added OpenShift build assets for agent:
  - `implementation/phase-05-agent-mcp/agent/buildconfig.yaml`
- Stabilized agent image build by resolving version conflicts in `requirements.txt` and runtime packaging path in `Dockerfile`.
- Updated MCP client usage in `agent.py` to `ClientSession` API for `mcp==1.24.0`.
- Updated checkpointer connection to `psycopg` (v3) for `PostgresSaver`.
- Final runtime result on hub:
  - Deployment rolled out successfully.
  - Running pod healthy (`READY=true`, `RESTARTS=0`).
  - Logs confirm Kafka subscription and group join on `nginx-logs`.

### Cleanup Performed

- Cluster cleanup:
  - Removed failed/cancelled agent builds (`dark-noc-agent-5` through `dark-noc-agent-9`).
  - Removed stale OpenShift build pods (`dark-noc-agent-*-build`) from `dark-noc-hub`.
- Repo cleanup:
  - Deleted Python cache folders (`__pycache__`, `*.pyc`) under phase-03/phase-05 paths.
  - Removed `.DS_Store` files from `dark-noc/` tree.
