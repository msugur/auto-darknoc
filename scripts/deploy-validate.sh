#!/usr/bin/env bash
set -euo pipefail

if ! command -v oc >/dev/null 2>&1; then
  if [[ -x /usr/local/bin/oc ]]; then
    oc() { /usr/local/bin/oc "$@"; }
  else
    echo "oc CLI not found in PATH"
    exit 1
  fi
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

: "${HUB_API_URL:?HUB_API_URL not set}"
: "${EDGE_API_URL:?EDGE_API_URL not set}"
HUB_USERNAME="${HUB_USERNAME:-${HUB_CLUSTER_ADMIN_USERNAME:-admin}}"
HUB_PASSWORD="${HUB_PASSWORD:-${HUB_CLUSTER_ADMIN_PASSWORD:-${HUB_CONSOLE_PASSWORD:-}}}"
EDGE_USERNAME="${EDGE_USERNAME:-${EDGE_CLUSTER_ADMIN_USERNAME:-admin}}"
EDGE_PASSWORD="${EDGE_PASSWORD:-${EDGE_CLUSTER_ADMIN_PASSWORD:-${EDGE_CONSOLE_PASSWORD:-}}}"

login_hub() {
  if [[ -n "${HUB_TOKEN:-}" ]]; then
    oc login "$HUB_API_URL" --token="$HUB_TOKEN" --insecure-skip-tls-verify=true >/dev/null
  else
    [[ -n "${HUB_PASSWORD:-}" ]] || { echo "Missing hub auth"; exit 1; }
    oc login "$HUB_API_URL" -u "$HUB_USERNAME" -p "$HUB_PASSWORD" --insecure-skip-tls-verify=true >/dev/null
  fi
}
login_edge() {
  if [[ -n "${EDGE_TOKEN:-}" ]]; then
    oc login "$EDGE_API_URL" --token="$EDGE_TOKEN" --insecure-skip-tls-verify=true >/dev/null
  else
    [[ -n "${EDGE_PASSWORD:-}" ]] || { echo "Missing edge auth"; exit 1; }
    oc login "$EDGE_API_URL" -u "$EDGE_USERNAME" -p "$EDGE_PASSWORD" --insecure-skip-tls-verify=true >/dev/null
  fi
}

phase="${1:-all}"

validate_foundation() {
  echo "== Validate Foundation =="
  login_hub
  oc get ns dark-noc-hub dark-noc-kafka dark-noc-observability dark-noc-mcp >/dev/null
  oc get csv -A | rg -i 'nfd|gpu|rhods|amq|aap|advanced-cluster-management|loki|logging|cloudnativepg' >/dev/null
  login_edge
  oc get ns dark-noc-edge >/dev/null
}

validate_data_pipeline() {
  echo "== Validate Data Pipeline =="
  login_hub
  oc -n dark-noc-minio get pods,pvc >/dev/null
  oc -n dark-noc-kafka get kafka,kafkatopic >/dev/null
  oc -n dark-noc-observability get pods >/dev/null
  oc -n openshift-logging get pods >/dev/null
  login_edge
  oc -n openshift-logging get clusterlogforwarder >/dev/null
}

validate_ai_core() {
  echo "== Validate AI Core =="
  login_hub
  oc -n redhat-ods-applications get pods >/dev/null
  oc -n dark-noc-hub get inferenceservice >/dev/null
}

validate_automation() {
  echo "== Validate Automation =="
  login_hub
  oc -n aap get deploy,pods,route >/dev/null
  oc -n open-cluster-management get multiclusterhub >/dev/null
}

validate_agent_mcp() {
  echo "== Validate Agent & MCP =="
  login_hub
  oc -n dark-noc-mcp get pods >/dev/null
  oc -n dark-noc-hub get pods -l app=dark-noc-agent >/dev/null
}

validate_dashboard() {
  echo "== Validate Dashboard =="
  login_hub
  oc -n dark-noc-ui get pods,route >/dev/null

  local dashboard_host chatbot_host
  dashboard_host="$(oc -n dark-noc-ui get route dark-noc-dashboard -o jsonpath='{.spec.host}')"
  chatbot_host="$(oc -n dark-noc-ui get route dark-noc-chatbot -o jsonpath='{.spec.host}')"
  [[ -n "$dashboard_host" ]] || { echo "Missing dark-noc-dashboard route host"; exit 1; }
  [[ -n "$chatbot_host" ]] || { echo "Missing dark-noc-chatbot route host"; exit 1; }

  local summary_json integrations_json
  summary_json="$(curl -ksSf "https://${dashboard_host}/api/summary")" || {
    echo "Dashboard same-origin API check failed: /api/summary"
    exit 1
  }
  integrations_json="$(curl -ksSf "https://${dashboard_host}/api/integrations")" || {
    echo "Dashboard same-origin API check failed: /api/integrations"
    exit 1
  }

  python3 - "$summary_json" "$integrations_json" <<'PY'
import json
import sys

summary = json.loads(sys.argv[1])
integrations = json.loads(sys.argv[2])

if not isinstance(summary, dict):
    raise SystemExit("summary payload is not an object")
if not isinstance(integrations, dict):
    raise SystemExit("integrations payload is not an object")

total = int(integrations.get("total", 0) or 0)
items = integrations.get("integrations") or []
access = integrations.get("access") or []

if total <= 0:
    raise SystemExit("integrations total is 0; live dashboard data not populated")
if not items:
    raise SystemExit("integrations list is empty; live dashboard data not populated")
if not access:
    raise SystemExit("access center list is empty; credentials/URLs not populated")

print("dashboard-live-check: ok")
PY
}

validate_edge_workloads() {
  echo "== Validate Edge Workloads =="
  login_edge
  oc -n dark-noc-edge get pods >/dev/null
}

case "$phase" in
  foundation) validate_foundation ;;
  data-pipeline) validate_data_pipeline ;;
  ai-core) validate_ai_core ;;
  automation) validate_automation ;;
  agent-mcp) validate_agent_mcp ;;
  dashboard) validate_dashboard ;;
  edge-workloads) validate_edge_workloads ;;
  all)
    validate_foundation
    validate_data_pipeline
    validate_ai_core
    validate_automation
    validate_agent_mcp
    validate_dashboard
    validate_edge_workloads
    ;;
  *)
    echo "Usage: $0 [all|foundation|data-pipeline|ai-core|automation|agent-mcp|dashboard|edge-workloads]"
    exit 1
    ;;
esac

echo "Validation OK for phase: $phase"
