# Session 003 — Cluster Upgrades Complete + Hub Phase 01 Start

**Date**: 2026-03-03
**Session Goal**: Upgrade both clusters to OCP 4.21.x and begin Phase 01 deployment.
**Status**: 🔄 IN PROGRESS

---

## What Was Completed

- Upgraded **hub** from `4.20.14` to `4.21.3`.
- Upgraded **edge** from `4.20.14` to `4.21.3`.
- Diagnosed upgrade blocker on both clusters:
  - `machine-api-operator` and `control-plane-machine-set-operator` rollouts stuck with `ProgressDeadlineExceeded`.
  - Root cause: single node was cordoned (`spec.unschedulable=true`), preventing new operator pods from scheduling.
- Remediation executed on both clusters:
  - `oc adm uncordon <sno-node>`
  - restart machine-api related deployments in `openshift-machine-api`.
- Verified both clusters reached upgrade completion state in `ClusterVersion`.
- Started Hub Phase 01:
  - Applied hub namespaces from `implementation/phase-01-foundation/namespaces/hub-namespaces.yaml`.
- Established reliable execution path via OpenTLC bastion SSH and continued hub install checks from bastion.
- Verified hub health post-upgrade:
  - `oc whoami` => `system:admin`
  - `ClusterVersion` => `4.21.3`, `AVAILABLE=True`, `PROGRESSING=False`
  - All core ClusterOperators healthy.
- Verified Wave 0 + Wave 1 subscriptions exist on hub.
- Diagnosed and fixed Loki operator install failure:
  - Error: `UnsupportedOperatorGroup` (`OwnNamespace InstallModeType not supported`)
  - Fix: removed `spec.targetNamespaces` from `openshift-operators-redhat-og` to make it global scope.
  - Result: `loki-operator.v6.4.2` moved to `Succeeded`.
- Began Wave 2 on hub:
  - `DataScienceCluster` already exists as `default-dsc` and is `Ready=True`.
  - Created `MultiClusterHub` (`open-cluster-management/multiclusterhub`) with minimal valid spec.
- Phase 02 started on hub and advanced:
  - MinIO deployed (`PVC + Deployment + Routes`) in `dark-noc-minio`.
  - MinIO buckets created successfully: `rhoai-models`, `loki-chunks`, `langfuse-data`.
  - Kafka KRaft cluster (`dark-noc-kafka`) deployed and healthy.
  - All 5 Kafka topics created and `READY=True`.
  - CloudNativePG operator corrected and installed (`cloudnative-pg.v1.28.1`).
  - Langfuse PostgreSQL cluster deployed and healthy in `dark-noc-observability`.
  - pgvector BuildConfig executed; custom image `pgvector-postgres:16.4-v0.8.1` built and pushed to internal registry.
  - pgvector PostgreSQL cluster deployed and healthy in `dark-noc-rag`.
  - Langfuse backend services deployed:
    - Redis running and healthy.
    - ClickHouse running with 20Gi PVC bound and service exposed.
  - Langfuse web/worker deployed via Helm (`langfuse-1.5.22`, app `3.155.1`):
    - Route created: `https://langfuse-dark-noc-observability.apps.ocp.v8w9c.sandbox205.opentlc.com`
    - Runtime fixes applied: `clickhouse.clusterEnabled=false`, explicit `REDIS_HOST/REDIS_PORT`.
  - Hub logging complete on OCP 4.21 API:
    - LokiStack deployed and tuned to `size: 1x.demo` for sandbox capacity.
    - Replaced deprecated `ClusterLogging` CR with `observability.openshift.io/v1 ClusterLogForwarder`.
    - Hub collector DaemonSet rolled out (`2/2`).
  - Edge logging foundation complete:
    - `openshift-logging` namespace + edge logging operator installed (`cluster-logging.v6.4.2`).
  - Edge CLF migrated to `observability.openshift.io/v1` with service account + RBAC.
  - Hub Kafka CA secret copied to edge and CLF reached `Ready=True`.
  - Edge collector DaemonSet rolled out (`1/1`).
  - Hub Kafka updated with external route listener (`9094`, passthrough) for cross-cluster access.
  - Edge nginx deployed and fixed for OpenShift SCC + stdout JSON access logging.
  - End-to-end edge->hub Kafka validation fixed:
    - Added route listener timeout tuning (`haproxy.router.openshift.io/timeout=10m`).
    - Confirmed delivery by consuming edge nginx records from hub `nginx-logs` topic.
  - Repository reconciliation pass completed:
    - Phase 01/02 READMEs and COMMANDS updated to reflect live-known deployment behavior.
    - Added `docs/deployment/redeploy-runbook.md`.
    - Backported critical manifest fixes (MinIO init, CNPG source/scope, MCH spec, Langfuse PG bootstrap).
- Capacity remediation:
  - Hub node was pod-saturated (`250/250` allocatable pods), blocking scheduling.
  - Scaled worker MachineSet `ocp-56g8n-worker-us-east-2a` from 0 to 1.
  - New worker joined and unblocked storage scheduling and stateful workloads.

---

## Current Notes

- Hub API showed intermittent timeout behavior during some list operations after upgrade.
- Existing operator footprint on hub is non-empty (e.g., pre-existing RHOAI 3.2.x related content), so Phase 01 operator steps require reconciliation rather than blind apply.
- Auth tokens expire quickly; periodic refreshed `oc login` is required.
- Attempted Wave 0 operator apply on hub, but command repeatedly stalled on API discovery (`/api` timeout). Switched to readiness probing and confirmed repeated hub API timeouts.
- Retried hub readiness (`/readyz`) and `oc get co` after waiting; both still fail with request timeouts to hub API endpoint.
- Attempted to continue on edge instead; edge `/readyz` and `get clusterversion` also timed out repeatedly, indicating a wider API responsiveness window affecting execution.
- Some `oc get csv -A` output includes repeated `rhods-operator` rows across namespaces in this environment; actionable status checks are being done with targeted queries per namespace/subscription.
- Initial `MultiClusterHub` manifest from repo failed admission because current ACM rejected `spec.overrides.components.observability` key; deployment proceeded with minimal spec and succeeded.
- `oc get subscription` shortname conflicted with ACM `subscriptions.apps.open-cluster-management.io`; OLM resources must be queried as `subscriptions.operators.coreos.com`.
- CloudNativePG initially stalled due:
  - wrong catalog source (`community-operators` instead of `certified-operators`)
  - duplicate OperatorGroups in `cnpg-system`
  - namespace-scoped OperatorGroup limiting watch to `cnpg-system`
  All corrected; operator now watches all namespaces.

---

## Next Actions

1. Monitor `MultiClusterHub` until `status.phase=Running`.
2. Start Phase 03 AI Core deployment on hub (RHOAI profile + model serving path).
3. Keep validating log-to-agent path while AI components come online.
4. Keep `COMMANDS-LOG.md` and `PROGRESS-TRACKER.md` updated per execution step.
