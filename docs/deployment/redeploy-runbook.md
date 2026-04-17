# Telco Autonomous Agentic AI Remediation Redeploy Runbook (Validated Path)

This runbook tracks the deployment sequence validated against the live hub cluster and captures required fixes for reproducible redeploys.

## Scope

- Hub: OCP 4.21.x
- Edge: OCP 4.21.x
- Environment: OpenTLC-style cluster with possible SNO pod-capacity constraints

## Critical Pre-Checks

1. Ensure OCP API and operators are healthy.
2. Check pod-capacity on hub primary node:
   - If `current_non_terminated_pods` is near `allocatable.pods`, scale a worker MachineSet first.
3. Use OLM-qualified resource names:
   - `subscriptions.operators.coreos.com`
   - `installplans.operators.coreos.com`
   - `csv.operators.coreos.com`

## Foundation Fixes Already Backported

1. CNPG subscription source set to `certified-operators`.
2. CNPG OperatorGroup is all-namespaces (`spec: {}`).
3. Loki OperatorGroup is all-namespaces (`spec: {}`).
4. MultiClusterHub manifest uses minimal valid spec (invalid overrides removed).

## Data Pipeline Fixes Already Backported

1. `minio-init-job.yaml` includes `HOME=/tmp` for `mc` write path.
2. Langfuse PostgreSQL initial manifest does not require cross-namespace backup secret.
3. Redis/ClickHouse bootstrap path documented before full Langfuse secrets injection.

## Validated Completed Components (Hub)

1. MinIO running with 200Gi PVC and required buckets.
2. Kafka KRaft cluster running with 5 topics ready.
3. Langfuse PostgreSQL (CNPG) healthy.
4. pgvector image built and pushed; pgvector PostgreSQL (CNPG) healthy.
5. Redis and ClickHouse running.

## Remaining for Full End-to-End

1. Deploy Langfuse Web (Helm) with finalized secret values.
2. Deploy LokiStack + ClusterLogging.
3. Configure and validate edge ClusterLogForwarder to hub Kafka.
4. Continue AI Core, Automation, Agent/MCP, Dashboard, Edge workload simulator, and validation phases.

## Lightspeed-Specific Sequence (Order Sensitive)

1. Complete Phase 04 AAP deployment (`automation-controller`, `eda-controller`).
2. Configure Lightspeed template path in AAP:
   - `implementation/phase-04-automation/aap/lightspeed-demo-template.md`
3. Deploy Phase 05 MCP AAP and LangGraph agent.
4. Verify Lightspeed scenario processing:
   - AAP job succeeds via `lightspeed-generate-and-run`
   - Generated template entry appears in AAP Job Templates
   - ServiceNow + Slack updates are emitted

## Troubleshooting: AAP Edge Remediation `401 Unauthorized`

Symptom:
- `restart-nginx` or `lightspeed-generate-and-run` jobs fail in AAP.
- Job stdout shows `Status code was 401` against the edge API URL.

Root cause:
- Edge cluster tokens become invalid after cluster rebuild/recreate, but AAP still holds the old bearer token.

Recovery steps:
1. Generate a fresh edge token from the edge admin account:
   - `oc login --server=<EDGE_API_URL> -u <EDGE_ADMIN_USER> -p '<EDGE_ADMIN_PASSWORD>'`
   - `oc whoami -t`
2. Switch back to hub and update the hub secret:
   - `oc login --server=<HUB_API_URL> -u <HUB_ADMIN_USER> -p '<HUB_ADMIN_PASSWORD>'`
   - `oc -n aap set data secret/aap-edge-credentials EDGE_API_URL='<EDGE_API_URL>' EDGE_API_TOKEN='<NEW_EDGE_TOKEN>'`
3. Update AAP credential `edge-01-k8s` to the same host/token:
   - Controller UI: Credentials -> `edge-01-k8s` -> Edit -> save new token
   - or Controller API PATCH `/api/controller/v2/credentials/<id>/`
4. Re-run demo triggers and confirm:
   - `crashloop` and `oom` show `Auto-Remediated`
   - `lightspeed` shows `Remediated`
   - `escalation` shows `Escalated` with ServiceNow incident

## Source of Truth During Deployment

- `logs/PROGRESS-TRACKER.md`
- `logs/COMMANDS-LOG.md`
- `logs/session-notes/session-003.md` (and subsequent sessions)
