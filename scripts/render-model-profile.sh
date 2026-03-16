#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE_DIR="${ROOT_DIR}/implementation/phase-03-ai-core/models/profiles"
OUT_DIR="${ROOT_DIR}/implementation/phase-03-ai-core/generated"

usage() {
  cat <<USAGE
Usage:
  ./scripts/render-model-profile.sh --profile <name> [--apply]

Examples:
  ./scripts/render-model-profile.sh --profile granite-4-h-tiny
  ./scripts/render-model-profile.sh --profile llama-3.2-3b-instruct --apply

What it does:
  1. Loads profile from phase-03-ai-core/models/profiles/<name>.env
  2. Renders vLLM and LlamaStack manifests into phase-03-ai-core/generated/
  3. Renders shared model-binding ConfigMap for agent/chatbot
  4. Optionally applies rendered files to the hub cluster
USAGE
}

PROFILE_NAME_ARG=""
APPLY="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE_NAME_ARG="$2"
      shift 2
      ;;
    --apply)
      APPLY="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${PROFILE_NAME_ARG}" ]]; then
  echo "--profile is required" >&2
  usage
  exit 1
fi

PROFILE_FILE="${PROFILE_DIR}/${PROFILE_NAME_ARG}.env"
if [[ ! -f "${PROFILE_FILE}" ]]; then
  echo "Profile not found: ${PROFILE_FILE}" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${PROFILE_FILE}"

required_vars=(
  PROFILE_NAME VLLM_RUNTIME_NAME INFERENCE_SERVICE_NAME MODEL_ID MODEL_STORAGE_URI
  VLLM_IMAGE VLLM_VERSION MAX_MODEL_LEN GPU_MEMORY_UTILIZATION LLAMASTACK_DISTRIBUTION
)
for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "Missing required variable in ${PROFILE_FILE}: ${var}" >&2
    exit 1
  fi
done

mkdir -p "${OUT_DIR}"

if [[ -n "${TOOL_CALL_PARSER:-}" ]]; then
  TOOL_ARGS_BLOCK=$(cat <<ARGS
        - "--enable-auto-tool-choice"
        - "--tool-call-parser=${TOOL_CALL_PARSER}"
        - "--guided-decoding-backend=xgrammar"
ARGS
)
else
  TOOL_ARGS_BLOCK="        # Tool parser disabled for this profile"
fi

render_file() {
  local src="$1"
  local dst="$2"

  sed \
    -e "s|__PROFILE_NAME__|${PROFILE_NAME}|g" \
    -e "s|__VLLM_RUNTIME_NAME__|${VLLM_RUNTIME_NAME}|g" \
    -e "s|__INFERENCE_SERVICE_NAME__|${INFERENCE_SERVICE_NAME}|g" \
    -e "s|__MODEL_ID__|${MODEL_ID}|g" \
    -e "s|__MODEL_STORAGE_URI__|${MODEL_STORAGE_URI}|g" \
    -e "s|__VLLM_IMAGE__|${VLLM_IMAGE}|g" \
    -e "s|__VLLM_VERSION__|${VLLM_VERSION}|g" \
    -e "s|__MAX_MODEL_LEN__|${MAX_MODEL_LEN}|g" \
    -e "s|__GPU_MEMORY_UTILIZATION__|${GPU_MEMORY_UTILIZATION}|g" \
    -e "s|__LLAMASTACK_DISTRIBUTION__|${LLAMASTACK_DISTRIBUTION}|g" \
    -e "s|__TOOL_ARGS_BLOCK__|${TOOL_ARGS_BLOCK//$'\n'/\\n}|g" \
    "${src}" > "${dst}"
}

render_file \
  "${ROOT_DIR}/implementation/phase-03-ai-core/vllm/vllm-inferenceservice.tmpl.yaml" \
  "${OUT_DIR}/vllm-inferenceservice.${PROFILE_NAME}.yaml"

render_file \
  "${ROOT_DIR}/implementation/phase-03-ai-core/llamastack/llamastack-distribution.tmpl.yaml" \
  "${OUT_DIR}/llamastack-distribution.${PROFILE_NAME}.yaml"

cat > "${OUT_DIR}/model-binding-configmap.${PROFILE_NAME}.yaml" <<CFG
apiVersion: v1
kind: ConfigMap
metadata:
  name: dark-noc-model-binding
  namespace: dark-noc-hub
  labels:
    app.kubernetes.io/part-of: dark-noc
    dark-noc/model-profile: ${PROFILE_NAME}
data:
  MODEL_ID: "${MODEL_ID}"
  VLLM_URL: "http://${INFERENCE_SERVICE_NAME}-predictor.dark-noc-hub.svc:8080/v1"
  MODEL_API_URL: "http://${INFERENCE_SERVICE_NAME}-predictor.dark-noc-hub.svc:8080/v1/completions"
  INFERENCE_SERVICE_NAME: "${INFERENCE_SERVICE_NAME}"
CFG

echo "Rendered profile: ${PROFILE_NAME}"
echo " - ${OUT_DIR}/vllm-inferenceservice.${PROFILE_NAME}.yaml"
echo " - ${OUT_DIR}/llamastack-distribution.${PROFILE_NAME}.yaml"
echo " - ${OUT_DIR}/model-binding-configmap.${PROFILE_NAME}.yaml"

if [[ "${APPLY}" == "true" ]]; then
  echo "Applying model binding and AI manifests to hub..."
  oc apply -f "${OUT_DIR}/model-binding-configmap.${PROFILE_NAME}.yaml"
  oc apply -f "${OUT_DIR}/vllm-inferenceservice.${PROFILE_NAME}.yaml"
  oc apply -f "${OUT_DIR}/llamastack-distribution.${PROFILE_NAME}.yaml"

  # Chatbot lives in dark-noc-ui; duplicate binding there for env refs.
  oc -n dark-noc-ui get configmap dark-noc-model-binding >/dev/null 2>&1 || true
  oc -n dark-noc-ui create configmap dark-noc-model-binding \
    --from-literal=MODEL_ID="${MODEL_ID}" \
    --from-literal=VLLM_URL="http://${INFERENCE_SERVICE_NAME}-predictor.dark-noc-hub.svc:8080/v1" \
    --from-literal=MODEL_API_URL="http://${INFERENCE_SERVICE_NAME}-predictor.dark-noc-hub.svc:8080/v1/completions" \
    --from-literal=INFERENCE_SERVICE_NAME="${INFERENCE_SERVICE_NAME}" \
    --dry-run=client -o yaml | oc apply -f -

  echo "Model profile applied. Restart deployments to pick up new env values:"
  echo "  oc -n dark-noc-hub rollout restart deploy/dark-noc-agent"
  echo "  oc -n dark-noc-ui rollout restart deploy/dark-noc-chatbot"
fi
