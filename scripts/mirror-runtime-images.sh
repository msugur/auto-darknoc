#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUAY_REPO="${QUAY_REPO:-quay.io/msugur/auto-darknoc}"
TAG_SUFFIX="${TAG_SUFFIX:-$(git -C "$ROOT_DIR" rev-parse --short HEAD)}"
PUSH_LATEST="${PUSH_LATEST:-true}"
LOCAL_REGISTRY_PORT="${LOCAL_REGISTRY_PORT:-5000}"

: "${QUAY_USERNAME:?QUAY_USERNAME is required}"
: "${QUAY_TOKEN:?QUAY_TOKEN is required}"

AUTH_FILE="$(mktemp "${TMPDIR:-/tmp}/darknoc-mirror-auth.XXXXXX.json")"
PF_LOG="$(mktemp "${TMPDIR:-/tmp}/darknoc-registry-port-forward.XXXXXX.log")"
PF_PID=""

cleanup() {
  rm -f "$AUTH_FILE" "$PF_LOG"
  if [[ -n "$PF_PID" ]] && kill -0 "$PF_PID" >/dev/null 2>&1; then
    kill "$PF_PID" >/dev/null 2>&1 || true
    wait "$PF_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "== Preparing temporary registry auth =="
OC_TOKEN="$(oc whoami -t)"
SRC_AUTH="$(printf 'admin:%s' "$OC_TOKEN" | base64 | tr -d '\n')"
DST_AUTH="$(printf '%s:%s' "$QUAY_USERNAME" "$QUAY_TOKEN" | base64 | tr -d '\n')"
python3 - "$AUTH_FILE" "$LOCAL_REGISTRY_PORT" "$SRC_AUTH" "$DST_AUTH" <<'PY'
import json
import sys

path, port, src_auth, dst_auth = sys.argv[1:5]
with open(path, "w", encoding="utf-8") as fh:
    json.dump(
        {
            "auths": {
                f"localhost:{port}": {"auth": src_auth},
                f"127.0.0.1:{port}": {"auth": src_auth},
                "quay.io": {"auth": dst_auth},
            }
        },
        fh,
    )
PY
chmod 600 "$AUTH_FILE"

echo "== Opening internal registry port-forward =="
oc -n openshift-image-registry port-forward \
  "svc/image-registry" "${LOCAL_REGISTRY_PORT}:5000" >"$PF_LOG" 2>&1 &
PF_PID="$!"
sleep 2
if ! kill -0 "$PF_PID" >/dev/null 2>&1; then
  cat "$PF_LOG"
  exit 1
fi

get_digest() {
  local namespace="$1"
  local image_stream="$2"
  oc -n "$namespace" get is "$image_stream" \
    -o jsonpath='{.status.tags[?(@.tag=="latest")].items[0].image}'
}

mirror_one() {
  local component="$1"
  local source="$2"
  local version_tag="$3"
  local latest_tag="$4"

  echo "== Mirroring ${component} =="
  oc image mirror --registry-config="$AUTH_FILE" --insecure=true "$source" "${QUAY_REPO}:${version_tag}"
  if [[ "$PUSH_LATEST" == "true" ]]; then
    oc image mirror --registry-config="$AUTH_FILE" --insecure=true "$source" "${QUAY_REPO}:${latest_tag}"
  fi
}

runtime_images=(
  "dark-noc-agent|dark-noc-hub|dark-noc-agent|agent"
  "mcp-openshift|dark-noc-mcp|mcp-openshift|mcp-openshift"
  "mcp-lokistack|dark-noc-mcp|mcp-lokistack|mcp-lokistack"
  "mcp-kafka|dark-noc-mcp|mcp-kafka|mcp-kafka"
  "mcp-aap|dark-noc-mcp|mcp-aap|mcp-aap"
  "mcp-slack|dark-noc-mcp|mcp-slack|mcp-slack"
  "mcp-servicenow|dark-noc-mcp|mcp-servicenow|mcp-servicenow"
  "dark-noc-dashboard|dark-noc-ui|dark-noc-dashboard|dashboard"
  "dark-noc-chatbot|dark-noc-ui|dark-noc-chatbot|chatbot"
)

for item in "${runtime_images[@]}"; do
  IFS="|" read -r component namespace image_stream tag_prefix <<<"$item"
  digest="$(get_digest "$namespace" "$image_stream")"
  mirror_one \
    "$component" \
    "localhost:${LOCAL_REGISTRY_PORT}/${namespace}/${image_stream}@${digest}" \
    "${tag_prefix}-${TAG_SUFFIX}" \
    "${tag_prefix}-latest"
done

cat <<EOF

Runtime image mirror complete.
- ${QUAY_REPO}:agent-${TAG_SUFFIX}
- ${QUAY_REPO}:mcp-openshift-${TAG_SUFFIX}
- ${QUAY_REPO}:mcp-lokistack-${TAG_SUFFIX}
- ${QUAY_REPO}:mcp-kafka-${TAG_SUFFIX}
- ${QUAY_REPO}:mcp-aap-${TAG_SUFFIX}
- ${QUAY_REPO}:mcp-slack-${TAG_SUFFIX}
- ${QUAY_REPO}:mcp-servicenow-${TAG_SUFFIX}
- ${QUAY_REPO}:dashboard-${TAG_SUFFIX}
- ${QUAY_REPO}:chatbot-${TAG_SUFFIX}
EOF
