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
ORDER_FILE="$ROOT_DIR/deploy/manifest-order.tsv"

MODE="client"
THROUGH="999"
PHASE_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server) MODE="server"; shift ;;
    --through) THROUGH="$2"; shift 2 ;;
    --phase) PHASE_FILTER="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -f "$ORDER_FILE" ]] || { echo "Missing order file: $ORDER_FILE"; exit 1; }

# Expect env from configs/hub/env.sh (+edge vars)
: "${HUB_API_URL:?HUB_API_URL not set}"
: "${EDGE_API_URL:?EDGE_API_URL not set}"

HUB_USERNAME="${HUB_USERNAME:-${HUB_CLUSTER_ADMIN_USERNAME:-admin}}"
HUB_PASSWORD="${HUB_PASSWORD:-${HUB_CLUSTER_ADMIN_PASSWORD:-${HUB_CONSOLE_PASSWORD:-}}}"
EDGE_USERNAME="${EDGE_USERNAME:-${EDGE_CLUSTER_ADMIN_USERNAME:-admin}}"
EDGE_PASSWORD="${EDGE_PASSWORD:-${EDGE_CLUSTER_ADMIN_PASSWORD:-${EDGE_CONSOLE_PASSWORD:-}}}"

current_cluster=""
login_cluster() {
  local c="$1"
  if [[ "$c" == "hub" ]]; then
    if [[ -n "${HUB_TOKEN:-}" ]]; then
      oc login "$HUB_API_URL" --token="$HUB_TOKEN" --insecure-skip-tls-verify=true >/dev/null
    else
      [[ -n "${HUB_PASSWORD:-}" ]] || { echo "Missing hub auth"; exit 1; }
      oc login "$HUB_API_URL" -u "$HUB_USERNAME" -p "$HUB_PASSWORD" --insecure-skip-tls-verify=true >/dev/null
    fi
  elif [[ "$c" == "edge" ]]; then
    if [[ -n "${EDGE_TOKEN:-}" ]]; then
      oc login "$EDGE_API_URL" --token="$EDGE_TOKEN" --insecure-skip-tls-verify=true >/dev/null
    else
      [[ -n "${EDGE_PASSWORD:-}" ]] || { echo "Missing edge auth"; exit 1; }
      oc login "$EDGE_API_URL" -u "$EDGE_USERNAME" -p "$EDGE_PASSWORD" --insecure-skip-tls-verify=true >/dev/null
    fi
  fi
}

pass=0
skip=0
warn=0
fail=0

while IFS=$'\t' read -r id phase cluster action path notes; do
  [[ "$id" == "id" ]] && continue
  [[ "$id" =~ ^[0-9]+$ ]] || continue

  if (( 10#$id > 10#$THROUGH )); then
    skip=$((skip+1))
    continue
  fi

  if [[ -n "$PHASE_FILTER" && "$phase" != "$PHASE_FILTER" ]]; then
    skip=$((skip+1))
    continue
  fi

  full_path="$ROOT_DIR/$path"

  if [[ ! -e "$full_path" ]]; then
    echo "[FAIL] $id $phase $action $path :: file missing"
    fail=$((fail+1))
    continue
  fi

  if [[ "$action" != "apply" ]]; then
    echo "[WARN] $id $phase $action $path :: dry-run not applicable ($notes)"
    warn=$((warn+1))
    continue
  fi

  if [[ "$cluster" != "$current_cluster" ]]; then
    login_cluster "$cluster"
    current_cluster="$cluster"
  fi

  if oc apply --dry-run="$MODE" -f "$full_path" >/dev/null 2>&1; then
    echo "[PASS] $id $phase $cluster apply $path"
    pass=$((pass+1))
  else
    echo "[FAIL] $id $phase $cluster apply $path"
    fail=$((fail+1))
  fi

done < "$ORDER_FILE"

echo ""
echo "Summary: pass=$pass warn=$warn fail=$fail skipped=$skip mode=$MODE"
[[ $fail -eq 0 ]]
