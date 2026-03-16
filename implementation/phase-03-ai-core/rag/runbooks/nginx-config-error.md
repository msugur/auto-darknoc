# Runbook: nginx Configuration Error — 502/503 Bad Gateway

## Symptoms
- HTTP responses: `502 Bad Gateway` or `503 Service Unavailable`
- nginx access log: `upstream timed out (110) while reading response header`
- nginx error log: `connect() failed (111: Connection refused) while connecting to upstream`
- Edge service not serving traffic

## Root Cause Analysis
1. Upstream backend service unreachable (proxy_pass target down)
2. Incorrect upstream URL in nginx configuration
3. Upstream response timeout too low
4. Backend service SSL certificate mismatch (if using HTTPS backend)
5. DNS resolution failure for upstream hostname

## Diagnostic Steps
```bash
# Check nginx error log for upstream errors
oc exec -n dark-noc-edge deploy/nginx -- \
  tail -50 /var/log/nginx/error.log

# Test upstream connectivity directly
oc exec -n dark-noc-edge deploy/nginx -- \
  curl -sv http://<upstream-service>:<port>/healthz

# Validate nginx config
oc exec -n dark-noc-edge deploy/nginx -- nginx -t

# Check upstream service status
oc get pods -n dark-noc-edge -l app=<upstream-app>
oc get endpoints -n dark-noc-edge <upstream-service>
```

## Remediation Steps

### Fix 1: Update Upstream URL
```bash
# Check current nginx config
oc exec -n dark-noc-edge deploy/nginx -- cat /etc/nginx/nginx.conf | grep proxy_pass

# Edit ConfigMap with correct upstream
oc edit configmap nginx-config -n dark-noc-edge
# Fix: proxy_pass http://<correct-service>:<correct-port>/;

# Reload nginx (graceful — no dropped connections)
oc exec -n dark-noc-edge deploy/nginx -- nginx -s reload
```

### Fix 2: Increase Upstream Timeout
```bash
# Add to nginx server block:
#   proxy_connect_timeout 30s;
#   proxy_read_timeout 60s;
#   proxy_send_timeout 60s;
oc edit configmap nginx-config -n dark-noc-edge
oc exec -n dark-noc-edge deploy/nginx -- nginx -s reload
```

### Fix 3: Restart Upstream Service
```bash
# If upstream pods are unhealthy:
oc rollout restart deployment/<upstream-app> -n dark-noc-edge
oc rollout status deployment/<upstream-app> -n dark-noc-edge
```

## Verification
```bash
# Confirm nginx returns 200
curl -sk http://nginx.dark-noc-edge.svc/healthz
# Expected: 200 OK

# Check nginx access log shows successful proxying
oc exec -n dark-noc-edge deploy/nginx -- \
  tail -10 /var/log/nginx/access.log | grep " 200 "
```
