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

HUB_ENV_FILE="$ROOT_DIR/configs/hub/env.sh"
EDGE_ENV_FILE="$ROOT_DIR/configs/edge/env.sh"
EDGE_DEST_NAME="${EDGE_DEST_NAME:-edge-cluster}"
SKIP_PREFLIGHT=false
SKIP_PLACEHOLDER_CHECK=false
CREATE_QUAY_PULL=false
COMMIT_RUNTIME_CONFIG=false
SINGLE_CLUSTER=false

usage() {
  cat <<'EOF'
Usage: ./scripts/one-click-gitops.sh [options]

Options:
  --hub-env <path>         Hub env file (default: configs/hub/env.sh)
  --edge-env <path>        Edge env file (default: configs/edge/env.sh)
  --edge-destination <n>   Argo destination cluster name for edge apps (default: edge-cluster)
  --skip-preflight         Skip scripts/preflight.sh
  --skip-placeholder-check Skip REPLACE_WITH_* checks in required GitOps files
  --create-quay-pull       Create quay-pull image pull secrets from QUAY_USERNAME/QUAY_TOKEN/QUAY_EMAIL
  --commit-runtime-config  Commit+push non-secret runtime route updates (Kafka/Langfuse) to current git branch
  --single-cluster         Hub and edge share one cluster that already runs OpenShift AI
                           (uses gitops/prod/apps-single; EDGE_* defaults to HUB_*)
  -h, --help               Show help

Required:
  - Hub + edge env files with:
      HUB_API_URL, EDGE_API_URL (EDGE_API_URL optional with --single-cluster)
  - Hub auth: HUB_TOKEN or HUB_USERNAME+HUB_PASSWORD
  - Edge auth: EDGE_TOKEN or EDGE_USERNAME+EDGE_PASSWORD
  - Quay credentials if private app images are used (--create-quay-pull)
  - Runtime secret files are auto-rendered (no manual secret editing required)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub-env) HUB_ENV_FILE="$2"; shift 2 ;;
    --edge-env) EDGE_ENV_FILE="$2"; shift 2 ;;
    --edge-destination) EDGE_DEST_NAME="$2"; shift 2 ;;
    --skip-preflight) SKIP_PREFLIGHT=true; shift ;;
    --skip-placeholder-check) SKIP_PLACEHOLDER_CHECK=true; shift ;;
    --create-quay-pull) CREATE_QUAY_PULL=true; shift ;;
    --commit-runtime-config) COMMIT_RUNTIME_CONFIG=true; shift ;;
    --single-cluster) SINGLE_CLUSTER=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

[[ -f "$HUB_ENV_FILE" ]] || { echo "Missing hub env file: $HUB_ENV_FILE"; exit 1; }

# shellcheck source=/dev/null
source "$HUB_ENV_FILE"
if [[ -f "$EDGE_ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$EDGE_ENV_FILE"
fi

: "${HUB_API_URL:?HUB_API_URL not set}"
if [[ "$SINGLE_CLUSTER" == "true" ]]; then
  # Edge workloads run on the hub; the edge identity is a scoped SA token
  # created below, never the (short-lived) hub login token.
  export EDGE_API_URL="$HUB_API_URL"
  export EDGE_USERNAME="${HUB_USERNAME:-admin}"
  export EDGE_PASSWORD="${HUB_PASSWORD:-}"
  export EDGE_TOKEN=""
  export EDGE_APPS_DOMAIN="${HUB_APPS_DOMAIN:-}"
  EDGE_DEST_NAME="in-cluster"
fi
: "${EDGE_API_URL:?EDGE_API_URL not set}"

HUB_USERNAME="${HUB_USERNAME:-${HUB_CLUSTER_ADMIN_USERNAME:-admin}}"
HUB_PASSWORD="${HUB_PASSWORD:-${HUB_CLUSTER_ADMIN_PASSWORD:-${HUB_CONSOLE_PASSWORD:-}}}"
EDGE_USERNAME="${EDGE_USERNAME:-${EDGE_CLUSTER_ADMIN_USERNAME:-admin}}"
EDGE_PASSWORD="${EDGE_PASSWORD:-${EDGE_CLUSTER_ADMIN_PASSWORD:-${EDGE_CONSOLE_PASSWORD:-}}}"

infer_apps_domain() {
  local api="$1"
  local host
  host="$(echo "$api" | sed -E 's#https?://([^/:]+).*#\1#')"
  if [[ "$host" == api.* ]]; then
    echo "${host/api./apps.}"
  else
    echo "$host"
  fi
}

set_edge_kafka_route() {
  local file="$1"
  local route="$2"
  RUNTIME_ROUTE="$route" perl -0777 -i -pe 's#(path:\s*/spec/outputs/0/kafka/url\s*\n\s*value:\s*).*$#$1$ENV{RUNTIME_ROUTE}#m' "$file"
}

set_langfuse_route() {
  local file="$1"
  local route="$2"
  RUNTIME_ROUTE="$route" perl -0777 -i -pe 's#(nextauth:\s*\n\s*url:\s*")[^"]*(")#$1$ENV{RUNTIME_ROUTE}$2#s' "$file"
}

echo "== Login: hub =="
if [[ -n "${HUB_TOKEN:-}" ]]; then
  oc login "$HUB_API_URL" --token="$HUB_TOKEN" --insecure-skip-tls-verify=true >/dev/null
elif [[ -n "${HUB_PASSWORD:-}" ]]; then
  oc login "$HUB_API_URL" -u "$HUB_USERNAME" -p "$HUB_PASSWORD" --insecure-skip-tls-verify=true >/dev/null
else
  echo "Hub auth missing: set HUB_TOKEN or HUB_USERNAME/HUB_PASSWORD"
  exit 1
fi
HUB_TOKEN="${HUB_TOKEN:-$(oc whoami -t 2>/dev/null || true)}"

if [[ "$SINGLE_CLUSTER" == "false" && -z "${EDGE_TOKEN:-}" && -n "${EDGE_PASSWORD:-}" ]]; then
  echo "== Login: edge (derive token) =="
  oc login "$EDGE_API_URL" -u "$EDGE_USERNAME" -p "$EDGE_PASSWORD" --insecure-skip-tls-verify=true >/dev/null
  EDGE_TOKEN="$(oc whoami -t 2>/dev/null || true)"
  if [[ -z "$EDGE_TOKEN" ]]; then
    echo "Failed to derive EDGE_TOKEN from username/password login"
    exit 1
  fi
  echo "== Re-login: hub =="
  if [[ -n "${HUB_TOKEN:-}" ]]; then
    oc login "$HUB_API_URL" --token="$HUB_TOKEN" --insecure-skip-tls-verify=true >/dev/null
  else
    oc login "$HUB_API_URL" -u "$HUB_USERNAME" -p "$HUB_PASSWORD" --insecure-skip-tls-verify=true >/dev/null
  fi
fi

required_secrets=(
  "$ROOT_DIR/gitops/prod/secrets/platform-credentials.real.yaml"
  "$ROOT_DIR/gitops/prod/secrets/notification-credentials.real.yaml"
  "$ROOT_DIR/gitops/prod/secrets/argocd-notifications.real.yaml"
  "$ROOT_DIR/gitops/prod/secrets/mcp-integrations.real.yaml"
  "$ROOT_DIR/gitops/prod/secrets/ui-access.real.yaml"
  "$ROOT_DIR/gitops/prod/secrets/grafana-admin.real.yaml"
  "$ROOT_DIR/gitops/prod/secrets/aap-admin.real.yaml"
  "$ROOT_DIR/gitops/prod/secrets/data-runtime.real.yaml"
)

required_runtime_files=(
  "$ROOT_DIR/gitops/prod/bases/automation/aap-edge-access.real.yaml"
)

# rg is not always installed (macOS); fall back to grep for placeholder checks.
has_placeholder() {
  if command -v rg >/dev/null 2>&1; then rg -n "$1" "$2" >/dev/null; else grep -n "$1" "$2" >/dev/null; fi
}

if [[ "$SINGLE_CLUSTER" == "true" ]]; then
  echo "== Single-cluster: create scoped edge operator identity =="
  oc create namespace dark-noc-edge --dry-run=client -o yaml | oc apply -f -
  oc apply -f "$ROOT_DIR/gitops/prod/stacks/edge/foundation-single/edge-operator-sa.yaml"
  for _ in $(seq 1 30); do
    EDGE_TOKEN="$(oc -n dark-noc-edge get secret dark-noc-edge-operator-token -o jsonpath='{.data.token}' 2>/dev/null | base64 -d 2>/dev/null || true)"
    [[ -n "$EDGE_TOKEN" ]] && break
    sleep 2
  done
  [[ -n "$EDGE_TOKEN" ]] || { echo "Timed out waiting for dark-noc-edge-operator token"; exit 1; }
  export EDGE_TOKEN
fi

echo "== Render secret templates into .real.yaml files =="
EDGE_API_URL="$EDGE_API_URL" EDGE_TOKEN="${EDGE_TOKEN:-}" \
  "$ROOT_DIR/scripts/render-prod-secrets.sh" --hub-env "$HUB_ENV_FILE" --edge-env "$EDGE_ENV_FILE"

for f in "${required_secrets[@]}"; do
  [[ -f "$f" ]] || { echo "Missing required secret file: $f"; exit 1; }
done
for f in "${required_runtime_files[@]}"; do
  [[ -f "$f" ]] || { echo "Missing required generated file: $f"; exit 1; }
done

HUB_APPS_DOMAIN="$(infer_apps_domain "$HUB_API_URL")"
KAFKA_BOOTSTRAP_ROUTE="${HUB_KAFKA_BOOTSTRAP_ROUTE:-tls://dark-noc-kafka-kafka-bootstrap-dark-noc-kafka.${HUB_APPS_DOMAIN}:443}"
route_host="$(oc get route -n dark-noc-kafka dark-noc-kafka-kafka-bootstrap -o jsonpath='{.spec.host}' 2>/dev/null || true)"
if [[ -n "$route_host" ]]; then
  KAFKA_BOOTSTRAP_ROUTE="tls://${route_host}:443"
fi
if [[ "$SINGLE_CLUSTER" == "false" ]]; then
  set_edge_kafka_route "$ROOT_DIR/gitops/prod/stacks/edge/data-pipeline/kustomization.yaml" "$KAFKA_BOOTSTRAP_ROUTE"
fi

LANGFUSE_ROUTE="${LANGFUSE_ROUTE:-https://langfuse-dark-noc-observability.${HUB_APPS_DOMAIN}}"
route_host="$(oc get route -n dark-noc-observability langfuse -o jsonpath='{.spec.host}' 2>/dev/null || true)"
if [[ -n "$route_host" ]]; then
  LANGFUSE_ROUTE="https://${route_host}"
fi
set_langfuse_route "$ROOT_DIR/gitops/prod/apps/langfuse-hub.yaml" "$LANGFUSE_ROUTE"

if [[ "$SKIP_PLACEHOLDER_CHECK" == "false" ]]; then
  if [[ "$SINGLE_CLUSTER" == "false" ]] && has_placeholder "REPLACE_WITH_HUB_KAFKA_BOOTSTRAP_ROUTE" "$ROOT_DIR/gitops/prod/stacks/edge/data-pipeline/kustomization.yaml"; then
    echo "Placeholder still present in edge data-pipeline kustomization."
    echo "Update gitops/prod/stacks/edge/data-pipeline/kustomization.yaml first."
    exit 1
  fi
  if has_placeholder "REPLACE_WITH_LANGFUSE_ROUTE" "$ROOT_DIR/gitops/prod/apps/langfuse-hub.yaml"; then
    echo "Placeholder still present in langfuse app values."
    echo "Update gitops/prod/apps/langfuse-hub.yaml first."
    exit 1
  fi
fi

if [[ "$COMMIT_RUNTIME_CONFIG" == "true" ]]; then
  echo "== Commit runtime route config =="
  git -C "$ROOT_DIR" add \
    gitops/prod/stacks/edge/data-pipeline/kustomization.yaml \
    gitops/prod/apps/langfuse-hub.yaml
  if git -C "$ROOT_DIR" diff --cached --quiet; then
    echo "No runtime route changes to commit."
  else
    git -C "$ROOT_DIR" commit -m "chore(runtime): set hub kafka and langfuse route for ${HUB_APPS_DOMAIN}"
    git -C "$ROOT_DIR" push
  fi
fi

if [[ "$SKIP_PREFLIGHT" == "false" ]]; then
  echo "== Preflight =="
  SINGLE_CLUSTER="$SINGLE_CLUSTER" "$ROOT_DIR/scripts/preflight.sh"
  echo "== Re-login: hub (after preflight context changes) =="
  if [[ -n "${HUB_TOKEN:-}" ]]; then
    oc login "$HUB_API_URL" --token="$HUB_TOKEN" --insecure-skip-tls-verify=true >/dev/null
  else
    oc login "$HUB_API_URL" -u "$HUB_USERNAME" -p "$HUB_PASSWORD" --insecure-skip-tls-verify=true >/dev/null
  fi
fi

echo "== Bootstrap OpenShift GitOps operator =="
oc apply -f "$ROOT_DIR/gitops/prod/argocd/openshift-gitops-subscription.yaml" 2>/dev/null || true
echo "Waiting for Argo CD CRDs..."
for _ in $(seq 1 90); do
  if oc get crd argocds.argoproj.io applications.argoproj.io appprojects.argoproj.io >/dev/null 2>&1; then break; fi
  sleep 10
done
oc wait --for=condition=Established crd/argocds.argoproj.io crd/applications.argoproj.io crd/appprojects.argoproj.io --timeout=300s
echo "== Apply Argo CD instance + project =="
oc apply -k "$ROOT_DIR/gitops/prod/argocd"

echo "== Ensure runtime namespaces exist =="
for ns in dark-noc-gitops dark-noc-mcp dark-noc-ui dark-noc-hub aap dark-noc-minio dark-noc-rag dark-noc-observability dark-noc-grafana openshift-logging; do
  oc create namespace "$ns" --dry-run=client -o yaml | oc apply -f -
done

echo "== Apply prod secrets =="
for f in "${required_secrets[@]}"; do
  oc apply -f "$f"
done
for f in "${required_runtime_files[@]}"; do
  oc apply -f "$f"
done

if [[ "$CREATE_QUAY_PULL" == "true" ]]; then
  : "${QUAY_USERNAME:?QUAY_USERNAME not set}"
  : "${QUAY_TOKEN:?QUAY_TOKEN not set}"
  : "${QUAY_EMAIL:?QUAY_EMAIL not set}"

  echo "== Create quay pull secrets =="
  for ns in dark-noc-hub dark-noc-mcp dark-noc-ui; do
    oc -n "$ns" create secret docker-registry quay-pull \
      --docker-server=quay.io \
      --docker-username="$QUAY_USERNAME" \
      --docker-password="$QUAY_TOKEN" \
      --docker-email="$QUAY_EMAIL" \
      --dry-run=client -o yaml | oc apply -f -
  done

  oc -n dark-noc-hub secrets link default quay-pull --for=pull || true
  oc -n dark-noc-hub secrets link dark-noc-agent quay-pull --for=pull || true
  oc -n dark-noc-mcp secrets link default quay-pull --for=pull || true
  oc -n dark-noc-mcp secrets link mcp-openshift-sa quay-pull --for=pull || true
  oc -n dark-noc-ui secrets link default quay-pull --for=pull || true
fi

echo "== Edge kubeconfig for mcp-openshift (dark-noc-mcp/edge-01-kubeconfig) =="
if [[ -n "${EDGE_TOKEN:-}" ]]; then
  _kc="$(mktemp)"
  KUBECONFIG="$_kc" oc config set-cluster edge-01 --server="$EDGE_API_URL" --insecure-skip-tls-verify=true >/dev/null
  KUBECONFIG="$_kc" oc config set-credentials edge-01 --token="$EDGE_TOKEN" >/dev/null
  KUBECONFIG="$_kc" oc config set-context edge-01 --cluster=edge-01 --user=edge-01 --namespace=dark-noc-edge >/dev/null
  KUBECONFIG="$_kc" oc config use-context edge-01 >/dev/null
  oc -n dark-noc-mcp create secret generic edge-01-kubeconfig --from-file=config="$_kc" \
    --dry-run=client -o yaml | oc apply -f -
  rm -f "$_kc"
else
  echo "Warning: EDGE_TOKEN empty; edge-01-kubeconfig not created (mcp-openshift will not start)."
fi

echo "== Trigger root app sync graph =="
if [[ "$SINGLE_CLUSTER" == "true" ]]; then
  ROOT_APP_FILE="$ROOT_DIR/gitops/prod/argocd/root-application-single.yaml"
else
  ROOT_APP_FILE="$ROOT_DIR/gitops/prod/argocd/root-application.yaml"
fi
oc apply -f "$ROOT_APP_FILE"

echo "== Edge destination check =="
if [[ "$SINGLE_CLUSTER" == "false" ]] && oc -n openshift-gitops get applications.argoproj.io foundation-edge >/dev/null 2>&1; then
  configured_dest="$(oc -n openshift-gitops get applications.argoproj.io foundation-edge -o jsonpath='{.spec.destination.name}')"
  if [[ "$configured_dest" != "$EDGE_DEST_NAME" ]]; then
    echo "Warning: edge app destination is '$configured_dest' but expected '$EDGE_DEST_NAME'."
    echo "If needed, update gitops/prod/apps/*edge*.yaml destination.name and commit to Git."
  else
    echo "Edge destination name matches expected: $EDGE_DEST_NAME"
  fi
fi

echo ""
echo "One-click bootstrap submitted."
echo "Next checks:"
echo "  oc -n openshift-gitops get applications.argoproj.io"
echo "  oc -n openshift-gitops get application auto-darknoc-prod-root -o jsonpath='{.status.sync.status}{\" \"}{.status.health.status}{\"\\n\"}'"
