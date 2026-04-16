#!/usr/bin/env bash
set -euo pipefail

if ! command -v oc >/dev/null 2>&1; then
  if [[ -x /usr/local/bin/oc ]]; then
    oc() { /usr/local/bin/oc "$@"; }
  fi
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HUB_ENV_FILE="$ROOT_DIR/configs/hub/env.sh"
EDGE_ENV_FILE="$ROOT_DIR/configs/edge/env.sh"
SECRETS_DIR="$ROOT_DIR/gitops/prod/secrets"
AUTOMATION_DIR="$ROOT_DIR/gitops/prod/bases/automation"

usage() {
  cat <<'EOF'
Usage: ./scripts/render-prod-secrets.sh [options]

Options:
  --hub-env <path>   Hub env file (default: configs/hub/env.sh)
  --edge-env <path>  Edge env file (default: configs/edge/env.sh)
  --secrets-dir <p>  Secrets directory (default: gitops/prod/secrets)
  --automation-dir <p> Automation templates dir (default: gitops/prod/bases/automation)
  -h, --help         Show help

Required env inputs (from hub/edge env files or shell):
  HUB_API_URL, EDGE_API_URL

Everything else is auto-generated or defaults to admin/redhat.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub-env) HUB_ENV_FILE="$2"; shift 2 ;;
    --edge-env) EDGE_ENV_FILE="$2"; shift 2 ;;
    --secrets-dir) SECRETS_DIR="$2"; shift 2 ;;
    --automation-dir) AUTOMATION_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

[[ -f "$HUB_ENV_FILE" ]] || { echo "Missing hub env file: $HUB_ENV_FILE"; exit 1; }

# shellcheck source=/dev/null
source "$HUB_ENV_FILE" >/dev/null 2>&1 || true
if [[ -f "$EDGE_ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$EDGE_ENV_FILE" >/dev/null 2>&1 || true
fi

: "${HUB_API_URL:?HUB_API_URL not set}"
: "${EDGE_API_URL:?EDGE_API_URL not set}"

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

can_query_cluster() {
  command -v oc >/dev/null 2>&1 && oc whoami >/dev/null 2>&1
}

route_url() {
  local namespace="$1"
  local route="$2"
  local fallback="$3"
  local host=""

  if can_query_cluster; then
    host="$(oc get route -n "$namespace" "$route" -o jsonpath='{.spec.host}' 2>/dev/null || true)"
  fi
  if [[ -n "$host" ]]; then
    echo "https://${host}"
  else
    echo "$fallback"
  fi
}

random_hex() {
  local bytes="${1:-16}"
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex "$bytes"
  else
    od -An -N "$bytes" -tx1 /dev/urandom | tr -d ' \n'
  fi
}

HUB_APPS_DOMAIN="${HUB_APPS_DOMAIN:-$(infer_apps_domain "${HUB_API_URL:-}")}"
EDGE_APPS_DOMAIN="${EDGE_APPS_DOMAIN:-$(infer_apps_domain "${EDGE_API_URL:-}")}"

HUB_CONSOLE_URL="${HUB_CONSOLE_URL:-https://console-openshift-console.${HUB_APPS_DOMAIN}}"
EDGE_CONSOLE_URL="${EDGE_CONSOLE_URL:-https://console-openshift-console.${EDGE_APPS_DOMAIN}}"
HUB_CONSOLE_USERNAME="${HUB_CONSOLE_USERNAME:-${HUB_CLUSTER_ADMIN_USERNAME:-${HUB_USERNAME:-admin}}}"
EDGE_CONSOLE_USERNAME="${EDGE_CONSOLE_USERNAME:-${EDGE_CLUSTER_ADMIN_USERNAME:-${EDGE_USERNAME:-admin}}}"
HUB_CONSOLE_PASSWORD="${HUB_CONSOLE_PASSWORD:-${HUB_CLUSTER_ADMIN_PASSWORD:-${HUB_PASSWORD:-redhat}}}"
EDGE_CONSOLE_PASSWORD="${EDGE_CONSOLE_PASSWORD:-${EDGE_CLUSTER_ADMIN_PASSWORD:-${EDGE_PASSWORD:-redhat}}}"
if [[ -z "${HUB_CPU_MACHINESET:-}" ]] && can_query_cluster; then
  HUB_CPU_MACHINESET="$(oc get machineset -n openshift-machine-api -o jsonpath='{range .items[?(@.metadata.labels["machine.openshift.io/cluster-api-machine-role"]=="worker")]}{.metadata.name}{"\n"}{end}' 2>/dev/null | head -n1 || true)"
fi
HUB_CPU_MACHINESET="${HUB_CPU_MACHINESET:-}"

DASHBOARD_URL="${DASHBOARD_URL:-$(route_url dark-noc-ui dark-noc-dashboard "https://dark-noc-dashboard-dark-noc-ui.${HUB_APPS_DOMAIN}")}"
CHATBOT_URL="${CHATBOT_URL:-$(route_url dark-noc-ui dark-noc-chatbot "https://dark-noc-chatbot-dark-noc-ui.${HUB_APPS_DOMAIN}")}"
GRAFANA_URL="${GRAFANA_URL:-$(route_url dark-noc-grafana grafana "https://grafana-dark-noc-grafana.${HUB_APPS_DOMAIN}")}"
LANGFUSE_URL="${LANGFUSE_URL:-${LANGFUSE_HOST:-$(route_url dark-noc-observability langfuse "https://langfuse-dark-noc-observability.${HUB_APPS_DOMAIN}")}}"
AAP_URL="${AAP_URL:-$(route_url aap aap-enterprise-controller "https://aap-enterprise-controller-aap.${HUB_APPS_DOMAIN}")}"
AAP_USERNAME="${AAP_USERNAME:-admin}"
AAP_PASSWORD="${AAP_PASSWORD:-redhat}"
AAP_LIGHTSPEED_URL="${AAP_LIGHTSPEED_URL:-${AAP_URL}/#/templates/job_template/${AAP_JOB_TEMPLATE_ID:-42}/details}"

GRAFANA_USERNAME="${GRAFANA_USERNAME:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-redhat}"
LANGFUSE_USERNAME="${LANGFUSE_USERNAME:-admin}"
LANGFUSE_PASSWORD="${LANGFUSE_PASSWORD:-redhat}"
KAFKA_UI_URL="${KAFKA_UI_URL:-https://kafka-ui-dark-noc-kafka.${HUB_APPS_DOMAIN}}"
KAFKA_UI_USERNAME="${KAFKA_UI_USERNAME:-admin}"
KAFKA_UI_PASSWORD="${KAFKA_UI_PASSWORD:-redhat}"
LOKI_UI_URL="${LOKI_UI_URL:-${GRAFANA_URL}/explore}"

MINIO_ROOT_USER="${MINIO_ROOT_USER:-admin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-redhat}"
if [[ ${#MINIO_ROOT_PASSWORD} -lt 8 ]]; then
  MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD}123"
fi
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-admin}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-redhat}"
PGVECTOR_PASSWORD="${PGVECTOR_PASSWORD:-redhat}"
LANGFUSE_DB_PASSWORD="${LANGFUSE_DB_PASSWORD:-redhat}"
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-redhat}"
LANGFUSE_SALT="${LANGFUSE_SALT:-$(random_hex 16)}"
LANGFUSE_ENCRYPTION_KEY="${LANGFUSE_ENCRYPTION_KEY:-}"
if [[ -z "$LANGFUSE_ENCRYPTION_KEY" || "$LANGFUSE_ENCRYPTION_KEY" == "redhat" ]]; then
  LANGFUSE_ENCRYPTION_KEY="$(random_hex 32)"
fi
LANGFUSE_NEXTAUTH_SECRET="${LANGFUSE_NEXTAUTH_SECRET:-$(random_hex 16)}"
LANGFUSE_PUBLIC_KEY="${LANGFUSE_PUBLIC_KEY:-admin}"
LANGFUSE_SECRET_KEY="${LANGFUSE_SECRET_KEY:-redhat}"
PGVECTOR_URL="${PGVECTOR_URL:-postgresql://noc_agent:redhat@pgvector-postgres-rw.dark-noc-rag.svc:5432/noc_rag}"
PG_CHECKPOINT_URL="${PG_CHECKPOINT_URL:-$PGVECTOR_URL}"

SNOW_URL="${SNOW_URL:-${SERVICENOW_URL:-https://dev365997.service-now.com}}"
SNOW_USERNAME="${SNOW_USERNAME:-${SERVICENOW_USERNAME:-admin}}"
SNOW_PASSWORD="${SNOW_PASSWORD:-${SERVICENOW_PASSWORD:-REPLACE_WITH_SERVICENOW_PASSWORD}}"
SERVICENOW_UI_URL="${SERVICENOW_UI_URL:-${SNOW_URL}/nav_to.do?uri=%2Fincident_list.do}"
SLACK_WORKSPACE_URL="${SLACK_WORKSPACE_URL:-https://octo-emerging-tech.slack.com}"
SLACK_NOC_CHANNEL="${SLACK_NOC_CHANNEL:-#demos}"
SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN:-REPLACE_WITH_XOXB_TOKEN}"
CALLER_NAME="${CALLER_NAME:-Dark NOC Bot}"

NOTIFY_EMAIL="${NOTIFY_EMAIL:-msugur@example.com}"
SMTP_HOST="${SMTP_HOST:-smtp.example.com}"
SMTP_USER="${SMTP_USER:-admin}"
SMTP_PASSWORD="${SMTP_PASSWORD:-redhat}"

replace() {
  local file="$1"
  local from="$2"
  local to="$3"
  REPLACE_FROM="$from" REPLACE_TO="$to" perl -0777 -i -pe 's/\Q$ENV{REPLACE_FROM}\E/$ENV{REPLACE_TO}/g' "$file"
}

render() {
  local src="$1"
  local dst="$2"
  cp "$src" "$dst"
}

render "$SECRETS_DIR/platform-credentials.template.yaml" "$SECRETS_DIR/platform-credentials.real.yaml"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_HUB_CONSOLE_URL" "$HUB_CONSOLE_URL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_HUB_API_URL" "${HUB_API_URL:-}"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_EDGE_CONSOLE_URL" "$EDGE_CONSOLE_URL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_EDGE_API_URL" "${EDGE_API_URL:-}"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_HUB_CPU_MACHINESET" "$HUB_CPU_MACHINESET"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_DASHBOARD_ROUTE" "$DASHBOARD_URL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_CHATBOT_ROUTE" "$CHATBOT_URL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_GRAFANA_ROUTE" "$GRAFANA_URL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_LANGFUSE_ROUTE" "$LANGFUSE_URL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_AAP_ROUTE" "$AAP_URL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_SERVICENOW_URL" "$SNOW_URL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_SERVICENOW_USERNAME" "$SNOW_USERNAME"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_SERVICENOW_PASSWORD" "$SNOW_PASSWORD"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_SLACK_WORKSPACE_URL" "$SLACK_WORKSPACE_URL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_SLACK_CHANNEL" "$SLACK_NOC_CHANNEL"
replace "$SECRETS_DIR/platform-credentials.real.yaml" "REPLACE_WITH_XOXB_TOKEN" "$SLACK_BOT_TOKEN"

render "$SECRETS_DIR/mcp-integrations.template.yaml" "$SECRETS_DIR/mcp-integrations.real.yaml"
replace "$SECRETS_DIR/mcp-integrations.real.yaml" "REPLACE_WITH_SERVICENOW_URL" "$SNOW_URL"
replace "$SECRETS_DIR/mcp-integrations.real.yaml" "REPLACE_WITH_SERVICENOW_USERNAME" "$SNOW_USERNAME"
replace "$SECRETS_DIR/mcp-integrations.real.yaml" "REPLACE_WITH_SERVICENOW_PASSWORD" "$SNOW_PASSWORD"
replace "$SECRETS_DIR/mcp-integrations.real.yaml" "REPLACE_WITH_CALLER_NAME" "$CALLER_NAME"
replace "$SECRETS_DIR/mcp-integrations.real.yaml" "REPLACE_WITH_XOXB_TOKEN" "$SLACK_BOT_TOKEN"
replace "$SECRETS_DIR/mcp-integrations.real.yaml" "REPLACE_WITH_SLACK_CHANNEL" "$SLACK_NOC_CHANNEL"

render "$SECRETS_DIR/notification-credentials.template.yaml" "$SECRETS_DIR/notification-credentials.real.yaml"
replace "$SECRETS_DIR/notification-credentials.real.yaml" "msugur@redhat.com" "$NOTIFY_EMAIL"
replace "$SECRETS_DIR/notification-credentials.real.yaml" "REPLACE_WITH_SMTP_HOST" "$SMTP_HOST"
replace "$SECRETS_DIR/notification-credentials.real.yaml" "REPLACE_WITH_SMTP_USER" "$SMTP_USER"
replace "$SECRETS_DIR/notification-credentials.real.yaml" "REPLACE_WITH_SMTP_PASSWORD" "$SMTP_PASSWORD"

render "$SECRETS_DIR/argocd-notifications.template.yaml" "$SECRETS_DIR/argocd-notifications.real.yaml"
replace "$SECRETS_DIR/argocd-notifications.real.yaml" "REPLACE_WITH_XOXB_TOKEN" "$SLACK_BOT_TOKEN"

render "$SECRETS_DIR/ui-access.template.yaml" "$SECRETS_DIR/ui-access.real.yaml"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_SERVICENOW_URL" "$SNOW_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_SERVICENOW_INCIDENTS_URL" "$SERVICENOW_UI_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_SERVICENOW_USERNAME" "$SNOW_USERNAME"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_SERVICENOW_PASSWORD" "$SNOW_PASSWORD"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_SLACK_WORKSPACE_URL" "$SLACK_WORKSPACE_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_HUB_CONSOLE_URL" "$HUB_CONSOLE_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_EDGE_CONSOLE_URL" "$EDGE_CONSOLE_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_HUB_CONSOLE_USERNAME" "$HUB_CONSOLE_USERNAME"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_HUB_CONSOLE_PASSWORD" "$HUB_CONSOLE_PASSWORD"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_EDGE_CONSOLE_USERNAME" "$EDGE_CONSOLE_USERNAME"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_EDGE_CONSOLE_PASSWORD" "$EDGE_CONSOLE_PASSWORD"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_AAP_URL" "$AAP_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_AAP_LIGHTSPEED_URL" "$AAP_LIGHTSPEED_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_AAP_USERNAME" "$AAP_USERNAME"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_AAP_PASSWORD" "$AAP_PASSWORD"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_GRAFANA_URL" "$GRAFANA_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_GRAFANA_USERNAME" "$GRAFANA_USERNAME"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_GRAFANA_PASSWORD" "$GRAFANA_PASSWORD"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_LANGFUSE_URL" "$LANGFUSE_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_LANGFUSE_USERNAME" "$LANGFUSE_USERNAME"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_LANGFUSE_PASSWORD" "$LANGFUSE_PASSWORD"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_KAFKA_UI_URL" "$KAFKA_UI_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_KAFKA_UI_USERNAME" "$KAFKA_UI_USERNAME"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_KAFKA_UI_PASSWORD" "$KAFKA_UI_PASSWORD"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_LOKI_UI_URL" "$LOKI_UI_URL"
replace "$SECRETS_DIR/ui-access.real.yaml" "REPLACE_WITH_DASHBOARD_URL" "$DASHBOARD_URL"

render "$SECRETS_DIR/grafana-admin.template.yaml" "$SECRETS_DIR/grafana-admin.real.yaml"
replace "$SECRETS_DIR/grafana-admin.real.yaml" "REPLACE_WITH_GRAFANA_ADMIN_USER" "$GRAFANA_USERNAME"
replace "$SECRETS_DIR/grafana-admin.real.yaml" "REPLACE_WITH_GRAFANA_ADMIN_PASSWORD" "$GRAFANA_PASSWORD"

render "$SECRETS_DIR/aap-admin.template.yaml" "$SECRETS_DIR/aap-admin.real.yaml"
replace "$SECRETS_DIR/aap-admin.real.yaml" "REPLACE_WITH_AAP_ADMIN_PASSWORD" "$AAP_PASSWORD"

render "$SECRETS_DIR/data-runtime.template.yaml" "$SECRETS_DIR/data-runtime.real.yaml"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_MINIO_ROOT_USER" "$MINIO_ROOT_USER"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_MINIO_ROOT_PASSWORD" "$MINIO_ROOT_PASSWORD"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_MINIO_ACCESS_KEY" "$MINIO_ACCESS_KEY"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_MINIO_SECRET_KEY" "$MINIO_SECRET_KEY"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_PGVECTOR_PASSWORD" "$PGVECTOR_PASSWORD"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_LANGFUSE_DB_PASSWORD" "$LANGFUSE_DB_PASSWORD"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_LANGFUSE_SALT" "$LANGFUSE_SALT"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_LANGFUSE_ENCRYPTION_KEY" "$LANGFUSE_ENCRYPTION_KEY"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_LANGFUSE_NEXTAUTH_SECRET" "$LANGFUSE_NEXTAUTH_SECRET"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_CLICKHOUSE_PASSWORD" "$CLICKHOUSE_PASSWORD"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_PGVECTOR_URL" "$PGVECTOR_URL"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_PG_CHECKPOINT_URL" "$PG_CHECKPOINT_URL"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_LANGFUSE_PUBLIC_KEY" "$LANGFUSE_PUBLIC_KEY"
replace "$SECRETS_DIR/data-runtime.real.yaml" "REPLACE_WITH_LANGFUSE_SECRET_KEY" "$LANGFUSE_SECRET_KEY"

render "$AUTOMATION_DIR/aap-edge-access.template.yaml" "$AUTOMATION_DIR/aap-edge-access.real.yaml"
replace "$AUTOMATION_DIR/aap-edge-access.real.yaml" "REPLACE_WITH_EDGE_API_URL" "${EDGE_API_URL:-}"
replace "$AUTOMATION_DIR/aap-edge-access.real.yaml" "REPLACE_WITH_EDGE_CLUSTER_TOKEN" "${EDGE_TOKEN:-}"

echo "Rendered:"
echo "  $SECRETS_DIR/platform-credentials.real.yaml"
echo "  $SECRETS_DIR/mcp-integrations.real.yaml"
echo "  $SECRETS_DIR/notification-credentials.real.yaml"
echo "  $SECRETS_DIR/argocd-notifications.real.yaml"
echo "  $SECRETS_DIR/ui-access.real.yaml"
echo "  $SECRETS_DIR/grafana-admin.real.yaml"
echo "  $SECRETS_DIR/aap-admin.real.yaml"
echo "  $SECRETS_DIR/data-runtime.real.yaml"
echo "  $AUTOMATION_DIR/aap-edge-access.real.yaml"
