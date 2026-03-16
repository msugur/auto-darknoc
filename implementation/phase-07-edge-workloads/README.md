# Phase 07 — Edge Workloads

## Overview
**Goal:** nginx running on Edge cluster with JSON logging, ClusterLogForwarder active, and failure simulator ready for demo triggers.

**Duration:** 0.5 days
**Clusters:** Edge (nginx + CLF), Hub (verify log reception)
**Depends on:** Phase 01 (edge logging operator), Phase 02 (Kafka topics + CLF installed)
**Unblocks:** Phase 08 (validation needs real edge failures)

---

## Why This Phase Matters

Without real edge workloads, there's nothing for the NOC to monitor. This phase creates the "patient" that the Dark NOC AI will diagnose and heal:

- **nginx** → The simulated telco edge VNF/CNF web server
- **JSON log format** → Structured logs that Granite can directly parse
- **Failure simulator** → CronJob that injects controlled failures for demo
- **ClusterLogForwarder** → The log pipeline from edge to hub AI

---

## Demo Trigger: How to Start an Incident

```bash
# One-shot OOMKill trigger (most impressive demo):
oc --context=${EDGE_CONTEXT} create job nginx-oom-now \
  --from=cronjob/nginx-oom-simulator -n dark-noc-edge

# Watch the pipeline in real-time:
# Terminal 1: Edge logs
oc --context=${EDGE_CONTEXT} logs -n dark-noc-edge -l app=nginx -f

# Terminal 2: Kafka receiving logs
oc exec -n dark-noc-kafka dark-noc-kafka-dual-role-0 -- \
  bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic nginx-logs --from-beginning | head -10

# Terminal 3: Agent processing
oc logs -n dark-noc-hub deploy/dark-noc-agent -f | grep INCIDENT

# Terminal 4: Slack (or check #dark-noc-alerts channel)
```

---

## Files in This Phase

```
phase-07-edge-workloads/
├── README.md
├── nginx/
│   └── nginx-deployment.yaml     ← nginx + ConfigMap + Service + Route
└── failure-simulator/
    └── failure-cronjob.yaml      ← OOMKill simulator CronJob
```

---

## Next Phase
Once end-to-end log flow is verified: **[Phase 08 — Validation](../phase-08-validation/README.md)**
