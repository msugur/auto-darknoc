# Phase 01 — Foundation: Commands Reference

> All commands must be run after sourcing your environment: `source configs/hub/env.sh`

---

## Step 1: Create Hub Namespaces

```bash
# WHY: All Dark NOC components need dedicated namespaces before any operator
# or workload can be deployed. Namespaces define resource boundaries and
# RBAC scope for each layer of the stack.
#
# EXPECTED OUTPUT: 8 namespaces created
# OUTCOME: Logical separation between data, AI, UI, and ops layers

oc apply -f implementation/phase-01-foundation/namespaces/hub-namespaces.yaml

# VERIFY:
oc get namespaces -l app.kubernetes.io/part-of=dark-noc
# Expected: 8 namespaces in Active state
```

---

## Step 2: Create Edge Namespace

```bash
# WHY: Edge cluster needs its own namespace for the log forwarding
# component. Minimal footprint — only 1 namespace needed on edge.
#
# Run on EDGE cluster (switch context first)
# EXPECTED OUTPUT: dark-noc-edge namespace created

oc --context=${EDGE_CONTEXT} apply -f \
  implementation/phase-01-foundation/namespaces/edge-namespaces.yaml
```

---

## Step 3: Wave 0 — Node Feature Discovery (NFD)

```bash
# WHY: NFD MUST be installed first. The GPU Operator uses NFD labels
# (feature.node.kubernetes.io/pci-10de.present=true) to identify GPU nodes.
# Without NFD, the GPU Operator won't know which nodes need drivers.
#
# EXPECTED OUTPUT: NFD operator installed, NodeFeatureDiscovery CR created
# OUTCOME: Node labels for GPU discovery appear within 2 minutes

oc apply -f implementation/phase-01-foundation/operators/wave-0-nfd-subscription.yaml

# WAIT for NFD operator to install (30-60 seconds):
oc wait --for=condition=Succeeded csv \
  -n openshift-nfd \
  -l operators.coreos.com/nfd.openshift-nfd \
  --timeout=120s

# VERIFY NFD labels on nodes:
oc get nodes -o json | jq -r \
  '.items[].metadata.labels | keys[] | select(startswith("feature.node"))'
# Expected: feature.node.kubernetes.io/pci-10de.present=true (on GPU node)
```

---

## Step 4: Wave 0 — cert-manager

```bash
# WHY: cert-manager must be installed before Service Mesh.
# Service Mesh webhooks require cert-manager CRDs to be present.
# Also used by LlamaStack and AAP for TLS.
#
# EXPECTED OUTPUT: cert-manager operator + CA certificates created
# OUTCOME: TLS automation available for all Dark NOC services

oc apply -f implementation/phase-01-foundation/operators/wave-0-certmanager-subscription.yaml

# WAIT for cert-manager operator:
oc wait --for=condition=Succeeded csv \
  -n cert-manager-operator \
  -l operators.coreos.com/cert-manager-operator.cert-manager-operator \
  --timeout=180s

# VERIFY cert-manager pods:
oc get pods -n cert-manager
# Expected: cert-manager, cert-manager-cainjector, cert-manager-webhook — all Running

# VERIFY ClusterIssuers (created after cert-manager pods are Ready):
sleep 30  # Wait for webhooks to register
oc apply -f implementation/phase-01-foundation/operators/wave-0-certmanager-subscription.yaml
oc get clusterissuer
# Expected: dark-noc-selfsigned-issuer (Ready), dark-noc-ca-issuer (Ready after ~30s)
```

---

## Step 5: Wave 0 — Service Mesh

```bash
# WHY: RHOAI 3.3 requires Service Mesh for model serving ingress.
# Install before RHOAI or operator admission webhooks will fail.
# Also provides mTLS between Dark NOC microservices.
#
# EXPECTED OUTPUT: Service Mesh + Kiali operators installed
# OUTCOME: Istio control plane running, mTLS available

oc apply -f implementation/phase-01-foundation/operators/wave-0-servicemesh-subscription.yaml

# WAIT for both Service Mesh and Kiali CSVs:
oc wait --for=condition=Succeeded csv \
  -n openshift-operators \
  -l operators.coreos.com/kiali-ossm.openshift-operators \
  --timeout=300s

# VERIFY Service Mesh control plane (takes 3-5 minutes):
oc wait --for=condition=Ready smcp/basic -n istio-system --timeout=300s
oc get pods -n istio-system
# Expected: istiod-*, kiali-* pods Running
```

---

## Step 6: Wave 0 — NVIDIA GPU Operator

```bash
# WHY: GPU Operator installs NVIDIA drivers, container toolkit, and
# device plugin on the GPU worker node. Without this, kubernetes
# cannot schedule pods that request nvidia.com/gpu resources.
#
# TIMING: Takes 5-10 minutes to compile CUDA kernel module.
# EXPECTED OUTPUT: GPU Operator installed, ClusterPolicy created
# OUTCOME: nvidia.com/gpu resource appears in node allocatable

# First, ensure GPU worker node is Running (from machineset step):
oc get nodes -l node-role.kubernetes.io/gpu-worker

oc apply -f implementation/phase-01-foundation/operators/wave-0-gpu-operator-subscription.yaml

# WAIT for GPU Operator CSV:
oc wait --for=condition=Succeeded csv \
  -n nvidia-gpu-operator \
  -l operators.coreos.com/gpu-operator-certified.nvidia-gpu-operator \
  --timeout=300s

# WAIT for driver daemonset to complete on GPU node (5-10 min):
oc rollout status ds/nvidia-driver-daemonset -n nvidia-gpu-operator --timeout=600s

# VERIFY GPU visible to Kubernetes:
GPU_NODE=$(oc get nodes -l nvidia.com/gpu.present=true -o name | head -1)
oc get ${GPU_NODE} -o jsonpath='{.status.allocatable.nvidia\.com/gpu}'
# Expected: 1
```

---

## Step 7: Add GPU Worker Node (MachineSet)

```bash
# WHY: Hub SNO cluster may have no schedulable capacity for stateful workloads.
# If your environment already has a GPU or this is a constrained demo cluster,
# treat this step as optional and scale at least one non-GPU worker first.
# For GPU inference, we need a g5.2xlarge
# (A10G 24GB VRAM) node to run Granite 4.0 H-Tiny via vLLM.
# Must be done BEFORE GPU Operator so drivers install on node creation.
#
# PREREQUISITE: Fill in all <PLACEHOLDERS> first
# EXPECTED OUTPUT: New Machine in Provisioned → Running state
# OUTCOME: GPU worker node joins cluster after ~7 minutes

# Step 7a: Get placeholder values
chmod +x implementation/phase-01-foundation/machineset/check-machineset.sh
./implementation/phase-01-foundation/machineset/check-machineset.sh

# Step 7b: Apply the machineset (after filling placeholders)
oc apply -f implementation/phase-01-foundation/machineset/gpu-worker-machineset.yaml

# Step 7c: Watch machine provision:
watch oc get machines -n openshift-machine-api
# Expected progression: Provisioning → Provisioned → Running (~7 min)

# Step 7d: Verify node joined with GPU labels:
oc get nodes -l dark-noc/gpu-worker=true
```

---

## Step 7b: Capacity Guardrail (SNO Pod Saturation)

```bash
# WHY: On OpenTLC SNO, default pod capacity can hit 250/250 quickly after
# ACM/RHOAI operator installs. If saturated, MinIO/Kafka/PostgreSQL pods stay Pending.
#
# EXPECTED OUTPUT: At least one additional worker node joins and reaches Ready.

NODE=$(oc get nodes -o name | head -n1 | cut -d/ -f2)
echo -n "allocatable_pods=" && oc get node "$NODE" -o jsonpath='{.status.allocatable.pods}{"\n"}'
echo -n "current_non_terminated_pods=" && \
  oc get pods -A --field-selector spec.nodeName=$NODE,status.phase!=Succeeded,status.phase!=Failed --no-headers | wc -l

# If current ~= allocatable, scale one worker MachineSet (example):
oc -n openshift-machine-api get machinesets
oc -n openshift-machine-api scale machineset <worker-machineset-name> --replicas=1
watch oc get nodes
```

---

## Step 8: Wave 1 — Platform Operators (Hub)

```bash
# WHY: All Wave 1 operators can be installed in parallel since they
# don't depend on each other. Installing simultaneously saves ~10 minutes.
# RHOAI, Kafka, ACM, AAP, Logging, Loki, CloudNativePG all install now.
#
# EXPECTED OUTPUT: 7 operators installed
# OUTCOME: All CRDs available for Phase 02 deployments

oc apply -f implementation/phase-01-foundation/operators/wave-1-rhoai-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-kafka-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-acm-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-aap-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-logging-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-loki-subscription.yaml
oc apply -f implementation/phase-01-foundation/operators/wave-1-cloudnativepg-subscription.yaml

# WAIT for all Wave 1 operators (run in parallel in 2 terminals):
# Terminal 1:
watch oc get csv.operators.coreos.com -A | grep -E "rhods|amqstreams|advanced-cluster|aap-operator"
# Terminal 2:
watch oc get csv.operators.coreos.com -A | grep -E "cluster-logging|loki|cloudnative-pg"

# ALL must show: Succeeded before proceeding to Phase 02

# NOTE:
# In clusters with ACM installed, `oc get subscription` can resolve to
# ACM app subscriptions. Use OLM-qualified resources for accuracy:
oc get subscriptions.operators.coreos.com -A
oc get installplans.operators.coreos.com -A
oc get csv.operators.coreos.com -A
```

---

## Step 9: Wave 1 — Logging Operator (Edge)

```bash
# WHY: Edge cluster also needs the Logging operator for
# ClusterLogForwarder. This is a lightweight install — no LokiStack,
# no local log storage. Just the operator CRDs.
#
# Run on EDGE cluster:
oc --context=${EDGE_CONTEXT} apply -f \
  implementation/phase-01-foundation/operators/edge-logging-subscription.yaml

# VERIFY on edge:
oc --context=${EDGE_CONTEXT} get csv -n openshift-logging
# Expected: cluster-logging.v6.4.x   Succeeded
```

---

## Phase 01 Complete Verification

```bash
# Run all checks:
echo "=== Hub Namespaces ==="
oc get namespaces -l app.kubernetes.io/part-of=dark-noc --no-headers | wc -l
# Expected: 8

echo "=== All Operators Succeeded ==="
oc get csv -A | grep -v Succeeded | grep -v NAME
# Expected: No output (all CSVs at Succeeded)

echo "=== GPU Node Ready ==="
oc get nodes -l nvidia.com/gpu.present=true -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}'
# Expected: True

echo "=== GPU Allocatable ==="
oc get nodes -l nvidia.com/gpu.present=true \
  -o jsonpath='{.items[0].status.allocatable.nvidia\.com/gpu}'
# Expected: 1

echo "=== cert-manager ClusterIssuers ==="
oc get clusterissuer
# Expected: dark-noc-selfsigned-issuer Ready, dark-noc-ca-issuer Ready

echo "=== Service Mesh ==="
oc get smcp -n istio-system
# Expected: basic   ComponentsReady   True
```

---

## Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| CSV stuck at Pending | `oc get installplan -A` | Approve: `oc patch installplan <name> -n <ns> --type merge -p '{"spec":{"approved":true}}'` |
| GPU Operator stuck | `oc describe pod -n nvidia-gpu-operator -l app=nvidia-driver-daemonset` | Usually kernel module compile — wait 10 min |
| Service Mesh webhook error | `oc get pods -n cert-manager` | cert-manager not ready; wait for webhook pod |
| NFD no GPU label | `oc get nodes -o json | jq '.items[].metadata.labels'` | GPU node not joined yet; wait for machineset |
| MachineSet stuck Provisioning | AWS Console → EC2 → check launch errors | Usually subnet/SG placeholder not replaced |
