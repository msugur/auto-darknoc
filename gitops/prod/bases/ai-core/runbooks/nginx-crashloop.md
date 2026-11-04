# Runbook: nginx CrashLoopBackOff — Configuration Error Remediation

## Symptoms
- Pod status: `CrashLoopBackOff`
- `oc logs <pod>` shows: `nginx: configuration file test failed`
- Exit code 1 in pod events
- Alert: `KubePodCrashLooping` with reason=Error

## Root Cause Analysis
nginx CrashLoopBackOff most commonly caused by:
1. Invalid nginx.conf syntax (bad ConfigMap edit)
2. Required upstream service unreachable (proxy_pass target down)
3. Missing SSL certificate file (if TLS configured)
4. Port conflict (another process using nginx's port)
5. Permission denied reading config or log files

## Diagnostic Steps
```bash
# Get exit code and crash reason
oc describe pod <nginx-pod> -n dark-noc-edge | grep -A5 "Last State"

# Check logs from crashed container
oc logs <nginx-pod> -n dark-noc-edge --previous

# Test nginx config syntax (without restarting)
oc exec deploy/nginx -n dark-noc-edge -- nginx -t 2>&1
```

## Remediation Steps

### Option 1: Fix ConfigMap Syntax Error
```bash
# Edit ConfigMap
oc edit configmap nginx-config -n dark-noc-edge

# Validate syntax before saving:
# echo "$NEW_CONFIG" | docker run --rm -i nginx:alpine nginx -t -c /dev/stdin

# Force pod restart with new config
oc rollout restart deployment/nginx -n dark-noc-edge
oc rollout status deployment/nginx -n dark-noc-edge --timeout=120s
```

### Option 2: Rollback to Last Known Good Config
```bash
# View rollout history
oc rollout history deployment/nginx -n dark-noc-edge

# Rollback to previous revision
oc rollout undo deployment/nginx -n dark-noc-edge
oc rollout status deployment/nginx -n dark-noc-edge
```

### Option 3: Emergency — Replace with Default Config
```bash
# Apply default minimal nginx config
oc create configmap nginx-config \
  --from-literal=nginx.conf="events{} http{server{listen 80; location /healthz {return 200;}}}" \
  -n dark-noc-edge --dry-run=client -o yaml | oc apply -f -

oc rollout restart deployment/nginx -n dark-noc-edge
```

## Verification
```bash
oc get pods -n dark-noc-edge  # Status: Running
oc exec deploy/nginx -n dark-noc-edge -- nginx -t  # test is successful
curl http://nginx.dark-noc-edge.svc/healthz  # 200 OK
```

## Prevention
- Always run `nginx -t` before applying ConfigMap changes
- Use GitOps (ACM) for config management — prevents manual errors
- CI pipeline should validate nginx config before push
