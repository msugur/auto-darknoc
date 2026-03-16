#!/usr/bin/env bash
# =============================================================
# Dark NOC — Teardown Script
# =============================================================
# PURPOSE:
#   Removes all Dark NOC components from both clusters.
#   Useful for resetting between demo runs or cleanup.
#
# USAGE:
#   chmod +x teardown.sh
#   source configs/hub/env.sh
#   ./teardown.sh [--confirm]
#
# WARNING:
#   This will DELETE:
#   - All dark-noc-* namespaces (and their PVCs)
#   - GPU MachineSet (terminates g5.2xlarge instance)
#   - ACM ManagedCluster enrollment
#   - All operator subscriptions
#
#   It will NOT delete:
#   - openshift-logging, openshift-nfd, nvidia-gpu-operator namespaces
#   - ACM MultiClusterHub (takes 20+ min to redeploy)
#   - RHOAI DataScienceCluster
# =============================================================
set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

if [[ "${1:-}" != "--confirm" ]]; then
  echo -e "${RED}WARNING: This will destroy all Dark NOC components.${NC}"
  echo ""
  echo "This will delete:"
  echo "  - All dark-noc-* namespaces on Hub (data will be lost)"
  echo "  - GPU MachineSet (terminates g5.2xlarge AWS instance)"
  echo "  - Edge cluster logging configuration"
  echo "  - Langfuse, Kafka, MinIO, pgvector data"
  echo ""
  echo "Run with --confirm to proceed:"
  echo "  ./teardown.sh --confirm"
  exit 0
fi

echo -e "${YELLOW}Starting Dark NOC teardown...${NC}"

# ─── EDGE CLUSTER ───────────────────────────────
echo ""
echo "→ Removing edge cluster components..."
oc --context=${EDGE_CONTEXT:-} delete clusterlogforwarder instance \
  -n openshift-logging --ignore-not-found=true
oc --context=${EDGE_CONTEXT:-} delete namespace dark-noc-edge \
  --ignore-not-found=true

# ─── HUB: AGENT AND MCP ─────────────────────────
echo "→ Removing agent and MCP servers..."
oc delete namespace dark-noc-hub dark-noc-mcp dark-noc-ui \
  --ignore-not-found=true

# ─── HUB: DATA LAYER ────────────────────────────
echo "→ Removing data layer (Kafka, MinIO, PostgreSQL, Langfuse)..."
oc delete namespace dark-noc-kafka dark-noc-observability \
  dark-noc-rag dark-noc-minio dark-noc-servicenow-mock \
  --ignore-not-found=true

# ─── HUB: AAP ───────────────────────────────────
echo "→ Removing AAP..."
oc delete automationcontroller aap -n aap --ignore-not-found=true
oc delete edacontroller eda -n aap --ignore-not-found=true
# Leave aap namespace and operator installed

# ─── HUB: ACM ManagedCluster ────────────────────
echo "→ Detaching edge cluster from ACM..."
oc delete managedcluster edge-01 --ignore-not-found=true

# ─── HUB: GPU MachineSet ────────────────────────
echo -e "${YELLOW}→ Deleting GPU MachineSet (terminates g5.2xlarge instance)...${NC}"
echo "  This will incur AWS costs until instance terminates (~2 min)"
GPU_MS=$(oc get machinesets -n openshift-machine-api \
  -l dark-noc/role=gpu-inference -o name 2>/dev/null || echo "")
if [[ -n "${GPU_MS}" ]]; then
  oc delete -n openshift-machine-api "${GPU_MS}"
  echo "  MachineSet deleted — AWS instance terminating"
else
  echo "  No GPU MachineSet found (already deleted?)"
fi

# ─── LOGGING (Hub) ──────────────────────────────
echo "→ Removing LokiStack and ClusterLogging from hub..."
oc delete clusterlogging instance -n openshift-logging --ignore-not-found=true
oc delete lokistack logging-loki -n openshift-logging --ignore-not-found=true

echo ""
echo -e "${GREEN}Teardown complete.${NC}"
echo ""
echo "Notes:"
echo "  - PVCs may remain — delete manually if needed:"
echo "    oc delete pvc --all -n dark-noc-minio"
echo "  - GPU instance on AWS takes ~2 min to terminate"
echo "  - Operators remain installed (subscription intact)"
echo "  - To fully reset: delete and recreate subscriptions"
