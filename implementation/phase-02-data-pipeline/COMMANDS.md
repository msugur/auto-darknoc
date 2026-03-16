# Phase 02 — Data Pipeline: Commands Reference

> Source your environment first: `source configs/hub/env.sh`

---

## Step 1: Deploy MinIO

```bash
# WHY: MinIO is required by LokiStack, RHOAI model registry, and
# Langfuse for blob storage. It must be running before any component
# that uses object storage is deployed.
#
# EXPECTED OUTPUT: MinIO pod Running, 3 buckets created
# OUTCOME: On-cluster S3-compatible storage available at
#   http://minio.dark-noc-minio.svc:9000

oc apply -f implementation/phase-02-data-pipeline/minio/minio-pvc.yaml \
  -n dark-noc-minio
oc apply -f implementation/phase-02-data-pipeline/minio/minio-deployment.yaml \
  -n dark-noc-minio

# Wait for MinIO to be ready:
oc rollout status deploy/minio -n dark-noc-minio --timeout=120s

# VERIFY MinIO health:
oc exec -n dark-noc-minio deploy/minio -- \
  curl -sf http://localhost:9000/minio/health/ready && echo "MinIO Ready"

# If MinIO pod remains Pending with "Too many pods", your hub is saturated.
# Add worker capacity before proceeding:
oc -n openshift-machine-api get machinesets
oc -n openshift-machine-api scale machineset <worker-machineset-name> --replicas=1
watch oc get nodes
```

---

## Step 2: Create MinIO Buckets

```bash
# WHY: Components fail on startup if their expected buckets don't exist.
# LokiStack: needs loki-chunks, RHOAI: needs rhoai-models, Langfuse: langfuse-data
#
# EXPECTED OUTPUT: Job Completed, 3 lines "Bucket created successfully"
# OUTCOME: All 3 required buckets exist in MinIO

oc apply -f implementation/phase-02-data-pipeline/minio/minio-init-job.yaml \
  -n dark-noc-minio

# Wait for job to complete (~10 seconds):
oc wait --for=condition=Complete job/minio-init -n dark-noc-minio --timeout=60s

# VERIFY buckets:
oc logs job/minio-init -n dark-noc-minio
# Expected:
#   Bucket created successfully: rhoai-models
#   Bucket created successfully: loki-chunks
#   Bucket created successfully: langfuse-data
```

---

## Step 3: Deploy Kafka KRaft Cluster

```bash
# WHY: Kafka is the real-time nervous system of Dark NOC.
# The edge logs travel through Kafka to reach the AI pipeline.
# KRaft mode (no ZooKeeper) is required for Streams 3.1.
#
# EXPECTED OUTPUT: Kafka cluster Ready, 1 pod running (controller+broker)
# OUTCOME: Kafka available at dark-noc-kafka-kafka-bootstrap:9092/9093

oc apply -f implementation/phase-02-data-pipeline/kafka/kafka-cluster.yaml \
  -n dark-noc-kafka

# Wait for Kafka to be ready (2-3 minutes for KRaft init):
oc wait --for=condition=Ready kafka/dark-noc-kafka \
  -n dark-noc-kafka --timeout=300s

# VERIFY Kafka status:
oc get kafka -n dark-noc-kafka
# Expected: dark-noc-kafka   True   (READY=True)

oc get pods -n dark-noc-kafka
# Expected: dark-noc-kafka-dual-role-0   Running
```

---

## Step 4: Create Kafka Topics

```bash
# WHY: Topics must exist before producers write to them.
# KafkaTopic CRs are managed by the Entity Operator — GitOps friendly.
#
# EXPECTED OUTPUT: 5 KafkaTopic CRs with Ready=True
# OUTCOME: All 5 topics available: nginx-logs, noc-alerts,
#   remediation-jobs, agent-events, incident-audit

oc apply -f implementation/phase-02-data-pipeline/kafka/kafka-topics.yaml \
  -n dark-noc-kafka

# VERIFY topics created:
oc get kafkatopic -n dark-noc-kafka
# Expected: 5 topics, all READY=True

# Test topic by producing a test message:
oc exec -n dark-noc-kafka dark-noc-kafka-dual-role-0 -- \
  bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
# Expected: agent-events, incident-audit, nginx-logs, noc-alerts, remediation-jobs
```

---

## Step 5: Deploy Langfuse PostgreSQL

```bash
# WHY: Langfuse Web needs PostgreSQL to be running before it starts.
# CloudNativePG creates the DB, user, and schema automatically.
#
# EXPECTED OUTPUT: langfuse-postgres-1 pod Running, cluster Healthy
# OUTCOME: PostgreSQL available at langfuse-postgres-rw:5432

oc apply -f implementation/phase-02-data-pipeline/postgresql/langfuse-postgres-cluster.yaml \
  -n dark-noc-observability

# Wait for PostgreSQL cluster to be ready (~60 seconds):
oc wait --for=condition=Ready cluster.postgresql.cnpg.io/langfuse-postgres \
  -n dark-noc-observability --timeout=180s

# VERIFY:
oc get cluster.postgresql.cnpg.io -n dark-noc-observability
# Expected: langfuse-postgres   1   1   Healthy

# Get generated DB password (used in Step 9 secret creation):
oc get secret langfuse-postgres-app -n dark-noc-observability \
  -o jsonpath='{.data.password}' | base64 -d
```

---

## Step 6: Build pgvector Image

```bash
# WHY: Standard PostgreSQL images don't have pgvector extension.
# We build a custom image PG16+pgvector0.8.1 using OpenShift BuildConfig.
# This image is used by the RAG database cluster.
#
# EXPECTED OUTPUT: Build Completed, ImageStream tag 16.4-v0.8.1 ready
# OUTCOME: Internal image registry has pgvector-postgres:16.4-v0.8.1

oc apply -f implementation/phase-02-data-pipeline/postgresql/pgvector-buildconfig.yaml \
  -n dark-noc-rag

# Start the build (watches compile output — takes ~3 minutes):
oc start-build pgvector-postgres --follow -n dark-noc-rag

# VERIFY image stream:
oc get imagestream pgvector-postgres -n dark-noc-rag
# Expected: tag 16.4-v0.8.1 present
```

---

## Step 7: Deploy pgvector Cluster

```bash
# WHY: The LangGraph agent uses pgvector for RAG — querying
# embedded NOC runbooks to add context to AI remediation decisions.
#
# EXPECTED OUTPUT: pgvector-postgres-1 pod Running, vector extension loaded
# OUTCOME: RAG database ready for knowledge base seeding (Phase 03)

oc apply -f implementation/phase-02-data-pipeline/postgresql/pgvector-cluster.yaml \
  -n dark-noc-rag

# Wait for cluster ready:
oc wait --for=condition=Ready cluster.postgresql.cnpg.io/pgvector-postgres \
  -n dark-noc-rag --timeout=180s

# VERIFY vector extension:
oc exec -n dark-noc-rag pgvector-postgres-1 -- \
  psql -U noc_agent -d noc_rag -c "SELECT extname FROM pg_extension;"
# Expected: vector
```

---

## Step 8: Deploy Redis + ClickHouse

```bash
# WHY: Both are required dependencies for Langfuse Web.
# Redis handles background job queuing; ClickHouse stores traces.
# Both must be running before langfuse-web pod starts.
#
# EXPECTED OUTPUT: Redis Running, ClickHouse Running
# OUTCOME: Full Langfuse backend stack ready

# Bootstrap secret for ClickHouse dependency (replaced in Step 9):
oc -n dark-noc-observability create secret generic langfuse-secrets \
  --from-literal=CLICKHOUSE_PASSWORD='REPLACE_WITH_CLICKHOUSE_PASSWORD' \
  --dry-run=client -o yaml | oc apply -f -

oc apply -f implementation/phase-02-data-pipeline/langfuse/redis-deployment.yaml \
  -n dark-noc-observability

oc apply -f implementation/phase-02-data-pipeline/langfuse/clickhouse-deployment.yaml \
  -n dark-noc-observability

# Wait for both:
oc rollout status deploy/redis -n dark-noc-observability --timeout=120s
oc rollout status deploy/clickhouse -n dark-noc-observability --timeout=180s

# VERIFY:
oc exec -n dark-noc-observability deploy/redis -- redis-cli ping
# Expected: PONG

oc exec -n dark-noc-observability deploy/clickhouse -- \
  clickhouse-client --query "SELECT version()"
# Expected: 24.8.x
```

---

## Step 9: Deploy Langfuse Web

```bash
# WHY: Langfuse captures all AI traces, evaluations, and feedback.
# Must be running before the LangGraph agent is deployed.
# Provides the observability URL used by the agent's Langfuse SDK.
#
# EXPECTED OUTPUT: Langfuse pod Running, Route accessible
# OUTCOME: Langfuse UI at https://langfuse-dark-noc-observability.apps.<domain>

# Generate + apply complete runtime secret:
# openssl rand -base64 32  # NEXTAUTH_SECRET / SALT
# openssl rand -hex 32     # ENCRYPTION_KEY
DB_PASSWORD="$(oc get secret langfuse-postgres-app -n dark-noc-observability -o jsonpath='{.data.password}' | base64 -d)"
oc create secret generic langfuse-secrets \
  -n dark-noc-observability \
  --from-literal=DATABASE_PASSWORD="${DB_PASSWORD}" \
  --from-literal=CLICKHOUSE_PASSWORD='REPLACE_WITH_CLICKHOUSE_PASSWORD' \
  --from-literal=REDIS_PASSWORD='' \
  --from-literal=NEXTAUTH_SECRET="$(openssl rand -base64 32)" \
  --from-literal=SALT="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -hex 32)" \
  --from-literal=S3_ACCESS_KEY_ID='admin' \
  --from-literal=S3_SECRET_ACCESS_KEY='darknoc-minio-secret' \
  --dry-run=client -o yaml | oc apply -f -

helm repo add langfuse https://langfuse.github.io/langfuse-k8s --force-update

helm upgrade --install langfuse langfuse/langfuse \
  --namespace dark-noc-observability \
  --values implementation/phase-02-data-pipeline/langfuse/langfuse-values.yaml \
  --version 1.5.22 \
  --wait --timeout 5m

oc apply -f implementation/phase-02-data-pipeline/langfuse/langfuse-route.yaml \
  -n dark-noc-observability

# Get Langfuse URL:
oc get route langfuse -n dark-noc-observability
# Visit URL and create initial admin/org.
```

---

## Step 10: Deploy LokiStack + ClusterLogging (Hub)

```bash
# WHY: LokiStack stores historical logs. The LokiStack MCP server
# queries it for logs older than what's in Kafka. ClusterLogging
# activates the Vector DaemonSet on hub nodes.
#
# EXPECTED OUTPUT: LokiStack Ready, collector DaemonSet Running on all nodes
# OUTCOME: Historical log storage available for MCP queries

oc apply -f implementation/phase-02-data-pipeline/logging/lokistack-hub.yaml \
  -n openshift-logging

# Wait for LokiStack (takes 2-8 minutes, depending on cluster size):
oc wait --for=condition=Ready lokistack/logging-loki \
  -n openshift-logging --timeout=480s

oc apply -f implementation/phase-02-data-pipeline/logging/clusterlogging-hub.yaml \
  -n openshift-logging

# VERIFY collector is running:
oc wait --for=condition=Ready clusterlogforwarder/instance \
  -n openshift-logging --timeout=300s
oc rollout status ds/instance -n openshift-logging --timeout=240s
# Expected: DaemonSet instance READY on each node
```

---

## Step 11: Configure Edge Log Forwarding

```bash
# WHY: This is THE critical data path. Without this, edge nginx
# failures never reach the AI pipeline. Test this thoroughly.
#
# PREREQUISITE: Kafka TLS cert must be copied to edge first.
# EXPECTED OUTPUT: CLF Ready, Vector sending to Kafka
# OUTCOME: nginx-logs Kafka topic receives edge logs

# Step 11a: Copy Kafka CA cert from Hub to Edge cluster
# (ACM ManifestWork handles this automatically after Phase 04,
#  but for testing before ACM: manual copy)
oc get secret dark-noc-kafka-cluster-ca-cert \
  -n dark-noc-kafka \
  -o yaml | \
  grep -v "resourceVersion\|uid\|creationTimestamp\|namespace" | \
  oc --context=${EDGE_CONTEXT} apply -n openshift-logging -f -

# Step 11b: Apply CLF on Edge cluster:
# First, inject the externally reachable Kafka bootstrap route host
# into the edge CLF template.
HUB_BOOTSTRAP_HOST=$(oc get route dark-noc-kafka-kafka-bootstrap \
  -n dark-noc-kafka -o jsonpath='{.spec.host}')
sed "s/REPLACE-WITH-HUB-KAFKA-BOOTSTRAP-HOST/${HUB_BOOTSTRAP_HOST}/g" \
  implementation/phase-02-data-pipeline/logging/clusterlogforwarder-edge.yaml \
  > /tmp/clusterlogforwarder-edge-runtime.yaml

oc --context=${EDGE_CONTEXT} apply -f \
  /tmp/clusterlogforwarder-edge-runtime.yaml

# Wait for CLF ready:
oc --context=${EDGE_CONTEXT} wait \
  --for=condition=Ready clusterlogforwarder/instance \
  -n openshift-logging --timeout=120s

# VERIFY end-to-end: trigger a test log and check Kafka
# (nginx must be deployed first — see Phase 07)
# If collector shows `AllBrokersDown` or disconnect errors, verify
# cross-cluster network reachability to:
#   dark-noc-kafka-kafka-bootstrap-<ns>.apps.<hub-domain>:443
#
# For route listener stability on sandbox routers, set timeout:
oc annotate route dark-noc-kafka-kafka-bootstrap -n dark-noc-kafka \
  haproxy.router.openshift.io/timeout=10m --overwrite
oc annotate route dark-noc-kafka-dual-role-0 -n dark-noc-kafka \
  haproxy.router.openshift.io/timeout=10m --overwrite
```

---

## Phase 02 Complete Verification

```bash
echo "=== MinIO ==="
oc exec -n dark-noc-minio deploy/minio -- \
  curl -sf http://localhost:9000/minio/health/ready && echo "OK"

echo "=== Kafka ==="
oc get kafka dark-noc-kafka -n dark-noc-kafka \
  -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
# Expected: True

echo "=== Kafka Topics ==="
oc get kafkatopic -n dark-noc-kafka --no-headers | wc -l
# Expected: 5

echo "=== LangFuse PostgreSQL ==="
oc get cluster langfuse-postgres -n dark-noc-observability \
  -o jsonpath='{.status.phase}'
# Expected: Cluster in healthy state

echo "=== pgvector ==="
oc get cluster pgvector-postgres -n dark-noc-rag \
  -o jsonpath='{.status.phase}'

echo "=== Redis ==="
oc exec -n dark-noc-observability deploy/redis -- redis-cli ping

echo "=== LokiStack ==="
oc get lokistack logging-loki -n openshift-logging \
  -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
# Expected: True

echo "=== Langfuse Route ==="
oc get route langfuse -n dark-noc-observability -o jsonpath='{.spec.host}'
```
