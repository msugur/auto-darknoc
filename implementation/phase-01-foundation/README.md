# Phase 01 — Foundation

## Overview
**Goal:** Both clusters have all required operators installed and running. Hub cluster has a GPU worker node. All 19 namespaces exist. Pre-flight checks pass.

**Duration:** 1–2 days
**Clusters:** Hub + Edge
**Depends on:** Nothing (first phase)
**Unblocks:** All other phases

---

## Why This Phase Matters

Every subsequent component (Kafka, RHOAI, LangGraph, AAP) is deployed as a Kubernetes operator or operator-managed workload. If the Operator Lifecycle Manager (OLM) catalog sources are not healthy, or the pull secret is invalid, or the GPU node doesn't have the NVIDIA driver installed, **everything else fails silently or with cryptic errors**.

This phase establishes the bedrock:
1. **Verified cluster state** — we know exactly what we're starting with
2. **Clean namespace structure** — no component bleeds into another's namespace
3. **Working operator catalog** — all Red Hat operators can be fetched and installed
4. **GPU worker node** — vLLM inference requires a physical GPU; without it, Granite 4.0 cannot run

---

## Files in This Phase

```
phase-01-foundation/
├── README.md                          ← This file
├── COMMANDS.md                        ← All commands with full context
├── preflight/
│   └── preflight-checks.sh           ← Symlink to ../../scripts/preflight.sh
├── namespaces/
│   ├── hub-namespaces.yaml           ← All 14 hub namespaces as YAML
│   └── edge-namespaces.yaml          ← All 5 edge namespaces as YAML
├── operators/
│   ├── wave-0-nfd-subscription.yaml           ← Node Feature Discovery
│   ├── wave-0-gpu-operator-subscription.yaml  ← NVIDIA GPU Operator
│   ├── wave-0-certmanager-subscription.yaml   ← cert-manager
│   ├── wave-0-servicemesh-subscription.yaml   ← OpenShift Service Mesh
│   ├── wave-1-rhoai-subscription.yaml         ← Red Hat OpenShift AI 3.3
│   ├── wave-1-acm-subscription.yaml           ← Red Hat ACM 2.15
│   ├── wave-1-kafka-subscription.yaml         ← Red Hat Streams for Kafka 3.1
│   ├── wave-1-aap-subscription.yaml           ← Red Hat AAP 2.5
│   ├── wave-1-logging-subscription.yaml       ← OpenShift Logging 6.4
│   ├── wave-1-loki-subscription.yaml          ← Loki Operator 6.4
│   ├── wave-1-cloudnativepg-subscription.yaml ← CloudNativePG
│   └── edge-logging-subscription.yaml         ← Logging on edge cluster
└── machineset/
    ├── gpu-worker-machineset.yaml     ← g5.2xlarge GPU worker for hub
    └── check-machineset.sh           ← Verify GPU node is ready
```

---

## Execution Steps

### Step 1: Pre-flight Checks
```bash
source configs/hub/env.sh
./scripts/preflight.sh
```
**Expected:** All checks PASS or WARN (no FAIL)

### Step 2: Create Namespaces (Hub)
```bash
oc login $HUB_API_URL --token=$HUB_TOKEN
oc apply -f implementation/phase-01-foundation/namespaces/hub-namespaces.yaml
```

### Step 3: Create Namespaces (Edge)
```bash
oc login $EDGE_API_URL --token=$EDGE_TOKEN
oc apply -f implementation/phase-01-foundation/namespaces/edge-namespaces.yaml
```

### Step 4: Fix StorageClass (if gp3-csi is not default)
```bash
oc login $HUB_API_URL --token=$HUB_TOKEN
# Only run if gp3-csi is NOT already the default
oc patch storageclass gp2 -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
oc patch storageclass gp3-csi -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

### Step 5: Install Wave 0 Operators (Hub — sequential, each depends on previous)
```bash
oc apply -f implementation/phase-01-foundation/operators/wave-0-nfd-subscription.yaml
# Wait for NFD CSV to reach Succeeded before next
watch oc get csv -n openshift-nfd

oc apply -f implementation/phase-01-foundation/operators/wave-0-gpu-operator-subscription.yaml
# Wait for GPU Operator CSV
watch oc get csv -n nvidia-gpu-operator

oc apply -f implementation/phase-01-foundation/operators/wave-0-certmanager-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-0-servicemesh-subscription.yaml
# Wait for both CSVs
```

### Step 6: Add GPU Worker MachineSet (Hub)
```bash
# Edit machineset YAML with your cluster infra details first
oc apply -f implementation/phase-01-foundation/machineset/gpu-worker-machineset.yaml
# Monitor machine provisioning (takes 5-10 min)
watch oc get machines -n openshift-machine-api
```

### Step 7: Install Wave 1 Operators (Hub — all in parallel)
```bash
oc apply -f implementation/phase-01-foundation/operators/wave-1-rhoai-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-acm-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-kafka-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-aap-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-logging-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-loki-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-cloudnativepg-subscription.yaml
# Monitor all CSVs
watch oc get csv -A | grep -E "rhods|acm|amq-streams|aap|cluster-logging|loki|cloudnative"
```

### Step 7b: Capacity Guardrail for SNO/OpenTLC
```bash
# If workload pods stay Pending with "Too many pods", scale one worker MachineSet.
oc -n openshift-machine-api get machinesets
oc -n openshift-machine-api scale machineset <worker-machineset-name> --replicas=1
watch oc get nodes
```

### Step 8: Install Edge Logging Operator
```bash
oc login $EDGE_API_URL --token=$EDGE_TOKEN
oc apply -f implementation/phase-01-foundation/operators/edge-logging-subscription.yaml
watch oc get csv -n openshift-logging
```

---

## Verification Checklist

```bash
# Hub: All Wave 0 CSVs Succeeded
oc get csv -n openshift-nfd
oc get csv -n nvidia-gpu-operator
oc get csv -n openshift-cert-manager-operator

# Hub: GPU worker node ready with NVIDIA labels
oc get nodes -l nvidia.com/gpu.present=true
oc get nodes -l node.kubernetes.io/instance-type=g5.2xlarge

# Hub: All Wave 1 CSVs Succeeded
oc get csv -A | grep -E "Succeeded" | grep -E "rhods|acm|amq-streams|aap|cluster-logging|loki|cloudnative"

# Edge: Logging CSV Succeeded
oc login $EDGE_API_URL --token=$EDGE_TOKEN
oc get csv -n openshift-logging

# Both: All namespaces Active
oc get namespaces | grep dark-noc
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| CSV stuck in `Installing` | Image pull failing | Check pull secret, verify `registry.redhat.io` auth |
| CSV stuck in `Pending` | Previous operator in same namespace | Delete old CSV first |
| GPU node not appearing | MachineSet config error | Check MachineSet events: `oc describe machineset <name> -n openshift-machine-api` |
| NFD labels missing on GPU node | NFD DaemonSet not running | Verify NFD CSV is Succeeded, check DaemonSet pods |
| Wave 1 operators failing | Wave 0 not complete | Wait for Service Mesh + cert-manager CSVs to reach Succeeded |
| Workloads stuck Pending with `Too many pods` | SNO pod capacity saturated | Scale one worker MachineSet to add schedulable capacity |
| `oc get subscription` returns unexpected CRD | ACM subscription CRD name clash | Use `subscriptions.operators.coreos.com` explicitly |

---

## Next Phase
Once all checks pass: **[Phase 02 — Data Pipeline](../phase-02-data-pipeline/README.md)**
