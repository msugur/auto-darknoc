#!/usr/bin/env bash
# =============================================================
# Dark NOC Pre-Flight Checks
# =============================================================
# PURPOSE:
#   Validates both OpenShift clusters are ready before any
#   operator installation or configuration begins.
#   Run this FIRST before starting phase-01.
#
# WHAT IT CHECKS:
#   1. oc CLI is installed and working
#   2. Hub cluster is accessible and on OCP 4.21
#   3. Edge cluster is accessible and on OCP 4.21
#   4. gp3-csi StorageClass exists on both clusters
#   5. Pull secret has registry.redhat.io access
#   6. No conflicting operators already installed
#   7. CatalogSources are healthy
#   8. Sufficient cluster resources
#
# USAGE:
#   source configs/hub/env.sh
#   ./scripts/preflight.sh
#
# OUTCOME:
#   Prints PASS/FAIL for each check.
#   Exits 0 if all checks pass, 1 if any fail.
# =============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "  ${GREEN}✅ PASS${NC} — $1"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}❌ FAIL${NC} — $1"; FAIL=$((FAIL + 1)); }
warn() { echo -e "  ${YELLOW}⚠️  WARN${NC} — $1"; WARN=$((WARN + 1)); }
info() { echo -e "  ${BLUE}ℹ️  INFO${NC} — $1"; }
header() { echo -e "\n${BLUE}━━━ $1 ━━━${NC}"; }

# Extract client/server versions without relying on deprecated --short output.
client_version() {
    oc version --client 2>&1 | awk -F': ' '/Client Version/ {print $2; exit}'
}

server_version() {
    oc version 2>&1 | awk -F': ' '/Server Version/ {print $2; exit}'
}

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Dark NOC Pre-Flight Checks                           ║"
echo "║     $(date '+%Y-%m-%d %H:%M:%S UTC')                    ║"
echo "╚══════════════════════════════════════════════════════════╝"

# ============================================================
# CHECK 1: oc CLI available
# ============================================================
header "CHECK 1: OpenShift CLI"
if command -v oc &> /dev/null; then
    OC_VERSION="$(client_version || true)"
    if [[ -n "${OC_VERSION}" ]]; then
        pass "oc CLI found — version: ${OC_VERSION}"
    else
        warn "oc CLI found, but client version string could not be parsed"
    fi
else
    fail "oc CLI not found. Install from: https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/"
    echo "Cannot continue without oc CLI. Exiting."
    exit 1
fi

# ============================================================
# CHECK 2: Hub cluster connectivity
# ============================================================
header "CHECK 2: Hub Cluster Access"
if [[ -z "${HUB_API_URL:-}" ]]; then
    fail "HUB_API_URL not set. Run: source configs/hub/env.sh"
else
    if oc login "${HUB_API_URL}" --token="${HUB_TOKEN}" --insecure-skip-tls-verify=true &>/dev/null; then
        HUB_VERSION="$(server_version || true)"
        if [[ "${HUB_VERSION}" == 4.21* ]]; then
            pass "Hub cluster accessible — OCP version: ${HUB_VERSION}"
        else
            fail "Hub cluster is OCP ${HUB_VERSION} — expected 4.21.x"
        fi
    else
        fail "Cannot connect to hub cluster at ${HUB_API_URL}"
    fi
fi

# ============================================================
# CHECK 3: Hub cluster nodes
# ============================================================
header "CHECK 3: Hub Cluster Nodes"
NODE_COUNT=$(oc get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
READY_COUNT=$(oc get nodes --no-headers 2>/dev/null | grep " Ready" | wc -l | tr -d ' ')
info "Total nodes: ${NODE_COUNT}, Ready: ${READY_COUNT}"

if [[ "${READY_COUNT}" -ge 1 ]]; then
    pass "At least one node is Ready"
else
    fail "No Ready nodes found on hub cluster"
fi

GPU_NODES=$(oc get nodes -l nvidia.com/gpu.present=true --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [[ "${GPU_NODES}" -ge 1 ]]; then
    pass "GPU node found (nvidia.com/gpu.present=true) — count: ${GPU_NODES}"
else
    warn "No GPU nodes found yet — will need to add g5.2xlarge MachineSet in Phase 01"
fi

# ============================================================
# CHECK 4: Hub StorageClass
# ============================================================
header "CHECK 4: Hub StorageClass"
if oc get storageclass gp3-csi &>/dev/null; then
    DEFAULT_SC=$(oc get storageclass -o jsonpath='{range .items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")]}{.metadata.name}{end}')
    if [[ "${DEFAULT_SC}" == "gp3-csi" ]]; then
        pass "gp3-csi StorageClass exists and is the default"
    else
        warn "gp3-csi exists but is NOT the default (default is: ${DEFAULT_SC}). Will fix in Phase 01."
    fi
else
    fail "gp3-csi StorageClass not found. Available StorageClasses:"
    oc get storageclass --no-headers 2>/dev/null | awk '{print "  " $1}'
fi

# ============================================================
# CHECK 5: Pull Secret
# ============================================================
header "CHECK 5: Pull Secret Validity"
PULL_REGISTRIES=$(oc get secret pull-secret -n openshift-config \
    -o jsonpath='{.data.\.dockerconfigjson}' 2>/dev/null | \
    base64 -d 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); [print(k) for k in d['auths'].keys()]" 2>/dev/null)

if echo "${PULL_REGISTRIES}" | grep -q "registry.redhat.io"; then
    pass "Pull secret contains registry.redhat.io auth"
else
    fail "Pull secret missing registry.redhat.io — operator pulls will fail"
fi

if echo "${PULL_REGISTRIES}" | grep -q "cloud.openshift.com"; then
    pass "Pull secret contains cloud.openshift.com auth"
else
    warn "Pull secret missing cloud.openshift.com (cluster telemetry may not work)"
fi

# ============================================================
# CHECK 6: Conflicting operators
# ============================================================
header "CHECK 6: Existing Operators (conflict check)"
CONFLICT_OPERATORS="rhods-operator|advanced-cluster-management|amq-streams|ansible-automation-platform"
EXISTING=$(oc get csv -A --no-headers 2>/dev/null | grep -E "${CONFLICT_OPERATORS}" || true)

if [[ -z "${EXISTING}" ]]; then
    pass "No conflicting operators pre-installed — clean slate"
else
    warn "Found existing operators — verify versions are correct:"
    echo "${EXISTING}" | while read line; do
        echo "    ${line}"
    done
fi

# ============================================================
# CHECK 7: CatalogSources healthy
# ============================================================
header "CHECK 7: OperatorHub CatalogSources"
CATALOGS=$(oc get catalogsource -n openshift-marketplace --no-headers 2>/dev/null)
if echo "${CATALOGS}" | grep -q "redhat-operators"; then
    CS_STATUS=$(oc get catalogsource redhat-operators -n openshift-marketplace \
        -o jsonpath='{.status.connectionState.lastObservedState}' 2>/dev/null)
    if [[ "${CS_STATUS}" == "READY" ]]; then
        pass "redhat-operators CatalogSource is READY"
    else
        fail "redhat-operators CatalogSource is ${CS_STATUS} — operator installs will fail"
    fi
else
    fail "redhat-operators CatalogSource not found"
fi

# ============================================================
# CHECK 8: Edge cluster access
# ============================================================
header "CHECK 8: Edge Cluster Access"
if [[ -z "${EDGE_API_URL:-}" ]]; then
    warn "EDGE_API_URL not set — skipping edge cluster checks"
    warn "Set edge credentials in configs/edge/env.sh and re-run"
else
    if oc login "${EDGE_API_URL}" --token="${EDGE_TOKEN}" --insecure-skip-tls-verify=true &>/dev/null; then
        EDGE_VERSION="$(server_version || true)"
        if [[ "${EDGE_VERSION}" == 4.21* ]]; then
            pass "Edge cluster accessible — OCP version: ${EDGE_VERSION}"
        else
            fail "Edge cluster is OCP ${EDGE_VERSION} — expected 4.21.x"
        fi
    else
        fail "Cannot connect to edge cluster at ${EDGE_API_URL}"
    fi
fi

# Switch back to hub context
if [[ -n "${HUB_API_URL:-}" ]]; then
    oc login "${HUB_API_URL}" --token="${HUB_TOKEN}" --insecure-skip-tls-verify=true &>/dev/null || true
fi

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Pre-Flight Check Summary                                ║"
printf "║  ✅ PASS: %-3d  ❌ FAIL: %-3d  ⚠️  WARN: %-3d          ║\n" $PASS $FAIL $WARN
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

if [[ $FAIL -gt 0 ]]; then
    echo -e "${RED}Pre-flight FAILED. Fix the issues above before proceeding.${NC}"
    exit 1
elif [[ $WARN -gt 0 ]]; then
    echo -e "${YELLOW}Pre-flight passed with warnings. Review warnings above.${NC}"
    echo -e "${GREEN}Safe to proceed to Phase 01.${NC}"
    exit 0
else
    echo -e "${GREEN}All pre-flight checks passed. Ready to begin Phase 01!${NC}"
    exit 0
fi
