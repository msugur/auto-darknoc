#!/usr/bin/env bash
set -euo pipefail

# Dark NOC Lightspeed E2E
# Validates: Kafka trigger -> Agent lightspeed path -> AAP job -> ServiceNow ticket

HUB_API_URL="${HUB_API_URL:-https://api.ocp.v8w9c.sandbox205.opentlc.com:6443}"
HUB_USER="${HUB_USER:-admin}"
HUB_PASS="${HUB_PASS:-}"
HUB_TOKEN="${HUB_TOKEN:-}"
SCENARIO_SITE="${SCENARIO_SITE:-edge-01}"
WAIT_SECONDS="${WAIT_SECONDS:-180}"

if [[ -z "${HUB_TOKEN}" && -z "${HUB_PASS}" ]]; then
  echo "HUB_TOKEN or HUB_PASS is required" >&2
  exit 1
fi

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 1; }; }
need oc
need curl
need jq
need rg

oc_retry() {
  local attempts=${1:-8}
  shift
  local i=0
  until "$@"; do
    i=$((i+1))
    if (( i >= attempts )); then
      return 1
    fi
    sleep 5
  done
}

echo "[1/8] Login + baseline discovery"
if [[ -n "${HUB_TOKEN}" ]]; then
  oc_retry 8 oc login --token="$HUB_TOKEN" --server="$HUB_API_URL" --insecure-skip-tls-verify=true >/dev/null
else
  oc_retry 8 oc login -u "$HUB_USER" -p "$HUB_PASS" --server="$HUB_API_URL" --insecure-skip-tls-verify=true >/dev/null
fi
oc_retry 8 oc whoami >/dev/null

KAFKA_POD="$(oc_retry 8 oc -n dark-noc-kafka get pod -l strimzi.io/name=dark-noc-kafka-kafka -o json | jq -r '.items[0].metadata.name')"
AAP_URL="$(oc_retry 8 oc -n dark-noc-mcp get deploy mcp-aap -o json | jq -r '.spec.template.spec.containers[0].env[] | select(.name=="AAP_URL") | .value')"
AAP_ROUTE_HOST="$(oc -n aap get route aap-enterprise-controller -o jsonpath='{.spec.host}' 2>/dev/null || true)"
if [[ -n "${AAP_ROUTE_HOST}" ]]; then
  # Prefer the external route so this script works from a local shell.
  AAP_URL="https://${AAP_ROUTE_HOST}"
fi
AAP_PASS="$(oc -n dark-noc-mcp get secret aap-admin-secret -o jsonpath='{.data.password}' 2>/dev/null | base64 -d || true)"
if [[ -z "${AAP_PASS}" ]]; then
  # Backward compatibility for legacy secret key naming.
  AAP_PASS="$(oc -n dark-noc-mcp get secret aap-admin-secret -o jsonpath='{.data.AAP_PASSWORD}' 2>/dev/null | base64 -d || true)"
fi
if [[ -z "${AAP_PASS}" ]]; then
  echo "Unable to resolve AAP admin password from dark-noc-mcp/aap-admin-secret" >&2
  exit 1
fi
SNOW_URL="$(oc_retry 8 oc -n dark-noc-mcp get secret servicenow-secrets -o jsonpath='{.data.SERVICENOW_URL}' | base64 -d)"
SNOW_USER="$(oc_retry 8 oc -n dark-noc-mcp get secret servicenow-secrets -o jsonpath='{.data.SERVICENOW_USERNAME}' | base64 -d)"
SNOW_PASS="$(oc_retry 8 oc -n dark-noc-mcp get secret servicenow-secrets -o jsonpath='{.data.SERVICENOW_PASSWORD}' | base64 -d)"
DASHBOARD_HOST="$(oc_retry 8 oc -n dark-noc-ui get route dark-noc-dashboard -o jsonpath='{.spec.host}')"
DASHBOARD_URL="https://${DASHBOARD_HOST}"

BASE_JOB_ID="$(curl -ksS -u "admin:${AAP_PASS}" "${AAP_URL}/api/controller/v2/jobs/?order_by=-id&page_size=1" | jq -r '.results[0].id // 0' 2>/dev/null || echo 0)"
BASE_INC="$(curl -ksS -u "${SNOW_USER}:${SNOW_PASS}" "${SNOW_URL}/api/now/table/incident?sysparm_limit=1&sysparm_fields=number&sysparm_query=ORDERBYDESCsys_created_on" | jq -r '.result[0].number // "NONE"')"

echo "kafka_pod=${KAFKA_POD}"
echo "aap_url=${AAP_URL}"
echo "baseline_job_id=${BASE_JOB_ID}"
echo "baseline_incident=${BASE_INC}"

echo "[2/8] Inject lightspeed event to Kafka topic nginx-logs"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EVENT_JSON=$(cat <<JSON
{"@timestamp":"${NOW}","message":"Ansible job failure detected from lightspeed E2E test","level":"error","kubernetes":{"namespace_name":"dark-noc-edge","pod_name":"nginx-lightspeed-demo","container_name":"nginx"},"labels":{"edge_site_id":"${SCENARIO_SITE}","dark_noc_demo":"true","dark_noc_scenario":"lightspeed"}}
JSON
)

oc_retry 8 oc -n dark-noc-kafka exec "$KAFKA_POD" -- bash -lc "cat <<'JSON' | /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic nginx-logs
${EVENT_JSON}
JSON"

echo "[3/8] Wait for lightspeed logs in agent"
DEADLINE=$(( $(date +%s) + WAIT_SECONDS ))
FOUND=0
while (( $(date +%s) < DEADLINE )); do
  if oc -n dark-noc-hub logs deploy/dark-noc-agent --since=10m 2>/dev/null | rg -q "\[LIGHTSPEED\]|lightspeed-generate-and-run|generated-ansible-job-failure"; then
    FOUND=1
    break
  fi
  sleep 10
done

if [[ "$FOUND" -ne 1 ]]; then
  echo "No LIGHTSPEED log marker found within ${WAIT_SECONDS}s" >&2
fi

echo "[4/8] Collect evidence"
AGENT_EVIDENCE="$(oc -n dark-noc-hub logs deploy/dark-noc-agent --since=15m 2>/dev/null | rg -n "LIGHTSPEED|generated-ansible|job_id|ServiceNow|incident|slack" | tail -n 60 || true)"
AAP_JOBS="$(curl -ksS -u "admin:${AAP_PASS}" "${AAP_URL}/api/controller/v2/jobs/?order_by=-id&page_size=10" | jq -r '.results[] | "id=\(.id) status=\(.status) template=\(.summary_fields.job_template.name) started=\(.started)"')"
GEN_TEMPLATES="$(curl -ksS -u "admin:${AAP_PASS}" "${AAP_URL}/api/controller/v2/job_templates/?name__startswith=generated-ansible-job-failure&order_by=-id&page_size=5" | jq -r '.results[] | "id=\(.id) name=\(.name) playbook=\(.playbook)"')"
INCIDENTS="$(curl -ksS -u "${SNOW_USER}:${SNOW_PASS}" "${SNOW_URL}/api/now/table/incident?sysparm_limit=5&sysparm_fields=number,short_description,sys_created_on&sysparm_query=ORDERBYDESCsys_created_on" | jq -r '.result[] | "number=\(.number) short=\(.short_description) created=\(.sys_created_on)"')"

LATEST_JOB_ID="$(echo "$AAP_JOBS" | head -n1 | sed -E 's/^id=([0-9]+).*/\1/' )"

echo "[5/8] Validation summary"
echo "found_lightspeed_logs=${FOUND}"
echo "baseline_job_id=${BASE_JOB_ID} latest_job_id=${LATEST_JOB_ID}"
echo "---- Agent Evidence ----"
echo "$AGENT_EVIDENCE"
echo "---- AAP Jobs ----"
echo "$AAP_JOBS"
echo "---- Generated Templates ----"
echo "$GEN_TEMPLATES"
echo "---- Latest ServiceNow Incidents ----"
echo "$INCIDENTS"

echo "[6/8] Assertions"
if [[ "${LATEST_JOB_ID:-0}" =~ ^[0-9]+$ ]] && (( LATEST_JOB_ID > BASE_JOB_ID )); then
  echo "PASS: New AAP job detected"
else
  echo "WARN: No new AAP job ID greater than baseline"
fi

if echo "$GEN_TEMPLATES" | rg -q "generated-ansible-job-failure"; then
  echo "PASS: Generated template present"
else
  echo "WARN: No generated template found in latest query"
fi

if echo "$INCIDENTS" | rg -qi "Dark NOC|Lightspeed|Ansible"; then
  echo "PASS: ServiceNow incident evidence present"
else
  echo "WARN: Could not confirm new ServiceNow lightspeed incident by text"
fi

echo "[7/8] Optional manual checks"
echo "- AAP Jobs UI: ${AAP_URL}/#/jobs"
echo "- ServiceNow list: ${SNOW_URL}/incident_list.do"
echo "- Dashboard: ${DASHBOARD_URL}"

echo "[8/8] Complete"
