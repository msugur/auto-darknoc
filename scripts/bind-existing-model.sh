#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  ./scripts/bind-existing-model.sh \
    --namespace my-first-model \
    --inference-service <isvc-name> \
    --model-id <model-id>

Example:
  ./scripts/bind-existing-model.sh \
    --namespace my-first-model \
    --inference-service granite-31-8b-lab-v1 \
    --model-id granite-3.1-8b-lab-v1

What it does:
  1) Validates the InferenceService exists
  2) Builds model endpoint URL: http://<isvc>-predictor.<ns>.svc:8080/v1
  3) Updates model-binding ConfigMap in:
     - dark-noc-hub
     - dark-noc-ui
  4) Restarts dark-noc-agent and dark-noc-chatbot
USAGE
}

NS=""
ISVC=""
MODEL_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --namespace) NS="$2"; shift 2 ;;
    --inference-service) ISVC="$2"; shift 2 ;;
    --model-id) MODEL_ID="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -n "$NS" ]] || { echo "--namespace required" >&2; exit 1; }
[[ -n "$ISVC" ]] || { echo "--inference-service required" >&2; exit 1; }
[[ -n "$MODEL_ID" ]] || { echo "--model-id required" >&2; exit 1; }

oc -n "$NS" get inferenceservice "$ISVC" >/dev/null

MODEL_BASE_URL="http://${ISVC}-predictor.${NS}.svc:8080/v1"
MODEL_COMPLETIONS_URL="${MODEL_BASE_URL}/completions"

echo "Binding model endpoint: ${MODEL_BASE_URL}"

auto_apply_cm() {
  local target_ns="$1"
  oc -n "$target_ns" create configmap dark-noc-model-binding \
    --from-literal=MODEL_ID="$MODEL_ID" \
    --from-literal=VLLM_URL="$MODEL_BASE_URL" \
    --from-literal=MODEL_API_URL="$MODEL_COMPLETIONS_URL" \
    --from-literal=INFERENCE_SERVICE_NAME="$ISVC" \
    --dry-run=client -o yaml | oc apply -f -
}

auto_apply_cm dark-noc-hub
auto_apply_cm dark-noc-ui

oc -n dark-noc-hub rollout restart deploy/dark-noc-agent
oc -n dark-noc-ui rollout restart deploy/dark-noc-chatbot

echo "Done. Verify:"
echo "  oc -n dark-noc-hub get configmap dark-noc-model-binding -o yaml"
echo "  oc -n dark-noc-ui get configmap dark-noc-model-binding -o yaml"
echo "  oc -n dark-noc-hub rollout status deploy/dark-noc-agent"
echo "  oc -n dark-noc-ui rollout status deploy/dark-noc-chatbot"
