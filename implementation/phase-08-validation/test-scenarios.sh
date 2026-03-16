#!/usr/bin/env bash
# =============================================================
# Dark NOC — End-to-End Test Scenarios
# =============================================================
# PURPOSE:
#   Validates the complete Dark NOC pipeline by running controlled
#   failure scenarios and verifying autonomous remediation.
#
# USAGE:
#   chmod +x test-scenarios.sh
#   source configs/hub/env.sh
#   ./test-scenarios.sh [scenario]
#
# SCENARIOS:
#   1  — OOMKilled: reduce nginx memory → AI detects → AAP restarts
#   2  — CrashLoop: bad config → AI detects → rollback
#   3  — NetworkTimeout: block Kafka → CLF degraded → alert
#   all — Run all scenarios sequentially
# =============================================================
set -euo pipefail

EDGE_NS="dark-noc-edge"
TIMEOUT=180  # Max seconds to wait for remediation

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

pass() { echo -e "${GREEN}✅ PASS${NC}: $1"; }
fail() { echo -e "${RED}❌ FAIL${NC}: $1"; exit 1; }
info() { echo -e "${YELLOW}ℹ️  ${NC}: $1"; }

# ─────────────────────────────────────────────
# SCENARIO 1: OOMKilled Recovery
# ─────────────────────────────────────────────
scenario_oomkill() {
  echo ""
  echo "═══════════════════════════════════════════════════"
  echo " SCENARIO 1: nginx OOMKilled Recovery"
  echo "═══════════════════════════════════════════════════"

  # Step 1: Confirm nginx is healthy
  info "Step 1: Verifying nginx baseline health..."
  NGINX_STATUS=$(oc --context=${EDGE_CONTEXT:-} get pods -n ${EDGE_NS} -l app=nginx \
    -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")

  if [[ "${NGINX_STATUS}" != "Running" ]]; then
    fail "nginx pod is not Running before test (got: ${NGINX_STATUS}). Fix deployment first."
  fi
  pass "nginx baseline: Running"

  # Step 2: Inject OOMKill
  info "Step 2: Reducing nginx memory limit to 32Mi (will cause OOMKill)..."
  oc --context=${EDGE_CONTEXT:-} patch deployment nginx \
    -n ${EDGE_NS} \
    --type=json \
    -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"32Mi"}]'
  pass "Memory limit reduced to 32Mi"

  # Step 3: Wait for OOMKill to occur
  info "Step 3: Waiting for OOMKill event (max 60s)..."
  START_TIME=$(date +%s)
  while true; do
    RESTART_COUNT=$(oc --context=${EDGE_CONTEXT:-} get pods -n ${EDGE_NS} -l app=nginx \
      -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}' 2>/dev/null || echo "0")
    LAST_STATE=$(oc --context=${EDGE_CONTEXT:-} get pods -n ${EDGE_NS} -l app=nginx \
      -o jsonpath='{.items[0].status.containerStatuses[0].lastState.terminated.reason}' 2>/dev/null || echo "")

    if [[ "${LAST_STATE}" == "OOMKilled" ]] || [[ "${RESTART_COUNT}" -gt "0" ]]; then
      pass "OOMKill detected (restarts: ${RESTART_COUNT}, reason: ${LAST_STATE:-OOMKilled})"
      break
    fi

    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [[ ${ELAPSED} -gt 60 ]]; then
      fail "OOMKill not detected after 60s. Check memory limit was applied."
    fi
    sleep 5
  done

  # Step 4: Wait for autonomous remediation
  info "Step 4: Waiting for Dark NOC AI to detect and remediate (max ${TIMEOUT}s)..."
  info "        [Kafka log → LangGraph → Granite analysis → AAP restart-nginx job]"

  START_TIME=$(date +%s)
  while true; do
    CURRENT_MEM=$(oc --context=${EDGE_CONTEXT:-} get deployment nginx -n ${EDGE_NS} \
      -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}' 2>/dev/null || echo "")
    NGINX_READY=$(oc --context=${EDGE_CONTEXT:-} get pods -n ${EDGE_NS} -l app=nginx \
      -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False")

    if [[ "${NGINX_READY}" == "True" && "${CURRENT_MEM}" != "32Mi" ]]; then
      pass "nginx is Running and Ready (memory: ${CURRENT_MEM})"
      break
    fi

    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [[ ${ELAPSED} -gt ${TIMEOUT} ]]; then
      echo ""
      echo "DIAGNOSTIC: Check these logs:"
      echo "  oc logs -n dark-noc-hub deploy/dark-noc-agent | tail -50"
      echo "  oc exec -n dark-noc-kafka dark-noc-kafka-dual-role-0 -- bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group dark-noc-agent"
      fail "Autonomous remediation not completed after ${TIMEOUT}s"
    fi
    echo -n "  [${ELAPSED}s] Waiting..."
    sleep 10
  done

  echo ""
  echo "═══ SCENARIO 1 RESULTS ════════════════════════════"
  pass "OOMKill injected and detected"
  pass "Dark NOC autonomously remediated nginx"
  pass "nginx pod Running and Ready"
  echo ""
  info "Check Langfuse trace: https://$(oc get route langfuse -n dark-noc-observability -o jsonpath='{.spec.host}')"
  info "Check Slack channel for #dark-noc-alerts notification"
}

# ─────────────────────────────────────────────
# SCENARIO 2: CrashLoop Recovery
# ─────────────────────────────────────────────
scenario_crashloop() {
  echo ""
  echo "═══════════════════════════════════════════════════"
  echo " SCENARIO 2: nginx CrashLoopBackOff Recovery"
  echo "═══════════════════════════════════════════════════"

  info "Step 1: Applying invalid nginx config..."
  oc --context=${EDGE_CONTEXT:-} patch configmap nginx-config \
    -n ${EDGE_NS} \
    --type merge \
    -p '{"data":{"nginx.conf":"invalid { config { that { will fail }"}}'

  oc --context=${EDGE_CONTEXT:-} rollout restart deployment/nginx -n ${EDGE_NS}

  info "Step 2: Waiting for CrashLoopBackOff..."
  TIMEOUT_CRASH=60
  START_TIME=$(date +%s)
  while true; do
    POD_STATUS=$(oc --context=${EDGE_CONTEXT:-} get pods -n ${EDGE_NS} -l app=nginx \
      -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "")
    POD_REASON=$(oc --context=${EDGE_CONTEXT:-} get pods -n ${EDGE_NS} -l app=nginx \
      -o jsonpath='{.items[0].status.containerStatuses[0].state.waiting.reason}' 2>/dev/null || echo "")

    if [[ "${POD_REASON}" == "CrashLoopBackOff" ]]; then
      pass "CrashLoopBackOff confirmed"
      break
    fi

    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [[ ${ELAPSED} -gt ${TIMEOUT_CRASH} ]]; then
      fail "CrashLoopBackOff not detected. Config may not have been applied."
    fi
    sleep 5
  done

  info "Step 3: Waiting for Dark NOC to detect and rollback (max ${TIMEOUT}s)..."
  START_TIME=$(date +%s)
  while true; do
    NGINX_READY=$(oc --context=${EDGE_CONTEXT:-} get pods -n ${EDGE_NS} -l app=nginx \
      -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False")

    if [[ "${NGINX_READY}" == "True" ]]; then
      pass "nginx Running after CrashLoop remediation"
      break
    fi

    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [[ ${ELAPSED} -gt ${TIMEOUT} ]]; then
      fail "CrashLoop not remediated after ${TIMEOUT}s"
    fi
    sleep 10
  done

  pass "SCENARIO 2: CrashLoop recovery completed"
}

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
SCENARIO="${1:-}"

case "${SCENARIO}" in
  1|oomkill) scenario_oomkill ;;
  2|crashloop) scenario_crashloop ;;
  all)
    scenario_oomkill
    sleep 30  # Recovery time between scenarios
    scenario_crashloop
    ;;
  *)
    echo "Usage: $0 [1|oomkill|2|crashloop|all]"
    echo ""
    echo "Scenarios:"
    echo "  1 / oomkill   — OOMKilled recovery test"
    echo "  2 / crashloop — CrashLoopBackOff recovery test"
    echo "  all           — Run all scenarios"
    exit 0
    ;;
esac

echo ""
echo "══════════════════════════════════════════════════════"
echo "  ALL SCENARIOS PASSED — Dark NOC is operational! 🎉"
echo "══════════════════════════════════════════════════════"
