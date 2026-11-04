# Runbook: AAP Job Failure — Ansible Automation Platform

## Symptoms
- Ansible job template fails with non-zero exit code
- AAP Controller shows job in `Failed` state
- Slack notification: `Remediation job FAILED: <job-id>`
- Edge workload still down after supposed remediation

## Root Cause Analysis
1. Invalid inventory — edge node not reachable
2. Playbook syntax error (YAML lint failure)
3. SSH key / kubeconfig expired for edge access
4. Missing Ansible collection not installed in EE (Execution Environment)
5. EDA triggered wrong job template (rule matching error)

## Diagnostic Steps
```bash
# Get job failure details via AAP REST API
AAP_URL="https://aap.aap.svc"
JOB_ID="<failed-job-id>"

curl -sk -u admin:${AAP_PASSWORD} \
  "${AAP_URL}/api/v2/jobs/${JOB_ID}/stdout/?format=txt" | tail -50

# Check EDA activation logs (if EDA-triggered)
oc logs -n aap deployment/eda-server | grep -i "error\|fail" | tail -20

# Check Execution Environment connectivity to edge
oc exec -n aap deployment/awx-task -- \
  oc --kubeconfig /runner/kubeconfig get nodes
```

## Remediation Steps

### Fix 1: Update Inventory / Kubeconfig
```bash
# Regenerate edge kubeconfig token (tokens expire after 24h by default)
oc --context=${EDGE_CONTEXT} create token dark-noc-aap-sa \
  -n dark-noc-edge --duration=8760h > /tmp/edge-token.txt

# Update AAP credential with new token
# (via AAP UI: Resources → Credentials → dark-noc-edge-kubeconfig → Edit)
```

### Fix 2: Re-run Failed Job
```bash
# Relaunch the failed job via REST API
curl -sk -u admin:${AAP_PASSWORD} \
  -X POST \
  "${AAP_URL}/api/v2/jobs/${JOB_ID}/relaunch/" \
  -H "Content-Type: application/json"
```

### Fix 3: Manual Override
```bash
# If AAP is completely broken, apply fix directly:
oc --context=${EDGE_CONTEXT} rollout restart deployment/nginx -n dark-noc-edge
oc --context=${EDGE_CONTEXT} rollout status deployment/nginx -n dark-noc-edge
```

## Prevention
- AAP kubeconfig credentials: use ServiceAccount token with 1-year expiry
- Test job templates weekly with a canary run
- EDA rulebook: send failed job alerts to `noc-alerts` Kafka topic
- Langfuse: track remediation success rate (target > 95%)
