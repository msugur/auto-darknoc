# Phase 02 — Data Pipeline

## Overview
**Goal:** All data infrastructure running: MinIO (object storage), Kafka 3.1 (event streaming), PostgreSQL clusters (Langfuse + pgvector), Langfuse 3.x (observability), LokiStack (log storage), and the Edge ClusterLogForwarder shipping nginx logs to Hub Kafka.

**Duration:** 1 day
**Clusters:** Hub (all components) + Edge (ClusterLogForwarder only)
**Depends on:** Phase 01 (all operators installed)
**Unblocks:** Phase 03 (AI Core needs LlamaStack endpoint + pgvector), Phase 04 (AAP needs Kafka topics)

---

## Why This Phase Matters

The Dark NOC's intelligence depends entirely on receiving accurate, timely, structured log data from the edge cluster. This phase builds the **data spine**:

- **MinIO** → All other components need object storage (LokiStack for logs, RHOAI for model weights, Langfuse for blob data)
- **Kafka** → The real-time nervous system connecting edge logs to hub AI; without it, the agent has nothing to analyze
- **PostgreSQL** → Both Langfuse and pgvector need PostgreSQL as their metadata/data store
- **Langfuse** → Must be running before the LangGraph agent is deployed so traces are captured from Day 1
- **LokiStack** → Long-term log storage enables the LokiStack MCP server to query historical logs
- **ClusterLogForwarder** → The actual log pipeline from edge nginx → hub Kafka; testing this proves the data path

---

## Components Deployed

```
Hub Cluster:
  dark-noc-minio          ← MinIO (200Gi PVC) — 3 buckets
  dark-noc-kafka          ← Kafka KRaft single node — 5 topics
  dark-noc-observability  ← PostgreSQL + Redis + ClickHouse + Langfuse Web
  dark-noc-rag            ← pgvector PostgreSQL cluster
  openshift-logging       ← LokiStack (1x.extra-small) + ClusterLogging

Edge Cluster:
  openshift-logging       ← Vector DaemonSet + ClusterLogForwarder → Hub Kafka
```

---

## Execution Order

```
1. MinIO deployment                (dark-noc-minio)
2. MinIO bucket creation           (minio mc client)
3. Kafka KRaft cluster             (dark-noc-kafka)
4. Kafka topics                    (dark-noc-kafka)
5. Langfuse PostgreSQL             (dark-noc-observability)
6. pgvector build + deploy         (dark-noc-rag)
7. Redis + ClickHouse              (dark-noc-observability)
8. Langfuse Web                    (dark-noc-observability)
9. LokiStack + ClusterLogging      (openshift-logging on hub)
10. Edge ClusterLogForwarder        (openshift-logging on edge)
11. Validate: nginx crash → Kafka   (end-to-end data path test)
```

## Known-Good Notes (from live deployment)

- If hub workloads remain `Pending` with scheduler message `Too many pods`, scale one worker MachineSet before continuing.
- For OLM checks, use qualified resources to avoid ACM CRD collisions:
  - `subscriptions.operators.coreos.com`
  - `installplans.operators.coreos.com`
  - `csv.operators.coreos.com`
- CloudNativePG must watch all namespaces (OperatorGroup `spec: {}` in `cnpg-system`) for clusters in `dark-noc-observability` and `dark-noc-rag`.
- `minio-init-job.yaml` sets `HOME=/tmp` for `mc` under restricted SCC.

---

## Files in This Phase

```
phase-02-data-pipeline/
├── README.md                          ← This file
├── COMMANDS.md                        ← All commands with context
├── minio/
│   ├── minio-deployment.yaml         ← MinIO Deployment + Service + Route
│   ├── minio-pvc.yaml                ← 200Gi gp3-csi PVC
│   └── minio-init-job.yaml           ← Job to create 3 buckets via mc CLI
├── kafka/
│   ├── kafka-cluster.yaml            ← Kafka KRaft single-node (demo)
│   └── kafka-topics.yaml             ← 5 KafkaTopic CRs
├── postgresql/
│   ├── langfuse-postgres-cluster.yaml  ← CloudNativePG for Langfuse
│   ├── pgvector-buildconfig.yaml       ← Build custom PG16+pgvector image
│   └── pgvector-cluster.yaml           ← CloudNativePG with pgvector image
├── langfuse/
│   ├── redis-deployment.yaml         ← Redis standalone
│   ├── clickhouse-deployment.yaml    ← ClickHouse single-shard
│   ├── langfuse-values.yaml          ← Helm values for Langfuse
│   └── langfuse-secrets.yaml         ← Database URL, API keys (template)
│   └── langfuse-route.yaml           ← OpenShift route for langfuse-web service
└── logging/
    ├── lokistack-hub.yaml            ← LokiStack CR (MinIO backend)
    ├── clusterlogging-hub.yaml       ← ClusterLogging CR (hub)
    └── clusterlogforwarder-edge.yaml ← Edge Vector → Hub Kafka
```

---

## Next Phase
Once all data path tests pass: **[Phase 03 — AI Core](../phase-03-ai-core/README.md)**
