#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

: "${HUB_API_URL:?HUB_API_URL not set}"
: "${HUB_TOKEN:?HUB_TOKEN not set}"
: "${EDGE_API_URL:?EDGE_API_URL not set}"
: "${EDGE_TOKEN:?EDGE_TOKEN not set}"

login_hub() { oc login "$HUB_API_URL" --token="$HUB_TOKEN" --insecure-skip-tls-verify=true >/dev/null; }
login_edge() { oc login "$EDGE_API_URL" --token="$EDGE_TOKEN" --insecure-skip-tls-verify=true >/dev/null; }

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
