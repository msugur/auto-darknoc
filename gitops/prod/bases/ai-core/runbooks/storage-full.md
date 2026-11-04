# Runbook: Storage Full — PVC Capacity Exhaustion

## Symptoms
- Pod events: `No space left on device`
- nginx logs: `open() "/var/log/nginx/error.log" failed (28: No space left on device)`
- `oc get pvc` shows PVC at 100% usage
- Alert: `KubePersistentVolumeFillingUp`

## Root Cause Analysis
1. Log rotation not configured — logs grew unbounded
2. Core dump files filling disk
3. PVC sized too small for workload
4. Temp files not cleaned up

## Remediation Steps

### Immediate: Free Space
```bash
# Find what's consuming space
oc exec -n dark-noc-edge deploy/nginx -- df -h /var/log
oc exec -n dark-noc-edge deploy/nginx -- du -sh /var/log/nginx/*

# Rotate / truncate logs immediately
oc exec -n dark-noc-edge deploy/nginx -- \
  sh -c "cat /dev/null > /var/log/nginx/access.log && \
         cat /dev/null > /var/log/nginx/error.log"

# Remove old compressed logs
oc exec -n dark-noc-edge deploy/nginx -- \
  find /var/log/nginx -name "*.gz" -delete
```

### Permanent: Expand PVC
```bash
# gp3-csi supports online expansion — no downtime needed
oc patch pvc nginx-logs-pvc -n dark-noc-edge \
  --type merge \
  -p '{"spec":{"resources":{"requests":{"storage":"10Gi"}}}}'

# Verify expansion (may take 1-2 minutes)
oc get pvc nginx-logs-pvc -n dark-noc-edge
```

### Configure Log Rotation
```bash
# Add logrotate configuration to nginx ConfigMap
oc edit configmap nginx-config -n dark-noc-edge
# Add: error_log /var/log/nginx/error.log warn;
# Add: access_log /var/log/nginx/access.log combined buffer=16k flush=5m;
```

## Prevention
- Configure PVC usage alerts at 80% threshold
- Implement log rotation via ConfigMap
- Use OpenShift Logging (Vector) to ship logs off-pod — don't store on PVC
