# Runbook: nginx OOMKilled — Out of Memory Remediation

## Symptoms
- Pod status shows `OOMKilled` in `oc get pods`
- `LAST STATE: OOMKilled` in `oc describe pod`
- nginx logs contain: `worker process exited on signal 9`
- Alert: `KubePodCrashLooping` or pod restart count > 3

## Root Cause Analysis
nginx pod was killed by the Linux OOM (Out of Memory) killer because:
1. Memory limit set too low for current traffic volume
2. Memory leak in nginx worker process (rare but possible)
3. Large request body buffering causing memory spike
4. Too many nginx worker processes for available RAM

## Immediate Remediation Steps

### Option 1: Increase Memory Limit (Most Common Fix)
```bash
# Check current limits
oc get pod <nginx-pod> -n dark-noc-edge -o jsonpath='{.spec.containers[0].resources}'

# Patch deployment to increase memory
oc patch deployment nginx -n dark-noc-edge \
  --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"512Mi"}]'

# Scale to restart pods with new limits
oc rollout restart deployment/nginx -n dark-noc-edge
oc rollout status deployment/nginx -n dark-noc-edge
```

### Option 2: Reduce Worker Processes
```bash
# Edit nginx ConfigMap to reduce workers
oc edit configmap nginx-config -n dark-noc-edge
# Change: worker_processes auto;
# To:     worker_processes 2;
```

### Option 3: Limit Request Buffer Size
Add to nginx config: `client_body_buffer_size 16k; client_max_body_size 1m;`

## Verification
```bash
oc get pods -n dark-noc-edge  # All pods Running
oc top pods -n dark-noc-edge  # Memory usage < 80% of limit
oc get events -n dark-noc-edge | grep OOMKilled  # No new OOM events
```

## Prevention
- Set memory requests = 80% of memory limits (avoid OOM)
- Monitor with: `oc adm top pods --sort-by=memory -n dark-noc-edge`
- Set HPA with memory-based scaling if traffic is variable
- Implement nginx rate limiting to prevent burst traffic spikes

## Escalation
If OOM persists after increasing limits to 1Gi: investigate nginx access logs
for large request patterns. Check for nginx module memory leaks with `valgrind`.
Create ServiceNow incident with priority P2.
