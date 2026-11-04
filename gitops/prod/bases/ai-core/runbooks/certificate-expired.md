# Runbook: Certificate Expired — TLS Certificate Rotation

## Symptoms
- `curl` returns: `SSL certificate problem: certificate has expired`
- Browser shows certificate warning
- Kafka TLS connections fail with: `certificate verify failed`
- Alert: `CertificateExpirySoon` (< 30 days) or expired

## Root Cause Analysis
1. cert-manager ClusterIssuer renewal failed
2. Manual cert not renewed before expiry
3. Kafka cluster CA cert expired (90-day default)
4. RHOAI serving cert expired

## Diagnostic Steps
```bash
# Check cert-manager certificates
oc get certificate -A | grep -v True

# Check specific cert expiry
oc get secret <cert-secret> -n <namespace> \
  -o jsonpath='{.data.tls\.crt}' | base64 -d | \
  openssl x509 -noout -dates

# Check cert-manager logs for renewal failures
oc logs -n cert-manager deployment/cert-manager | grep -i "error\|fail" | tail -20
```

## Remediation Steps

### Option 1: Trigger cert-manager Renewal
```bash
# Delete certificate secret — cert-manager will renew automatically
oc delete secret <tls-secret-name> -n <namespace>
# cert-manager detects missing secret and re-issues within 60 seconds

# Watch renewal:
oc get certificate -n <namespace> -w
# Expected: READY changes from False → True
```

### Option 2: Manually Rotate Kafka CA
```bash
# Annotate Kafka cluster to trigger CA rotation
oc annotate kafka dark-noc-kafka -n dark-noc-kafka \
  strimzi.io/force-renew-certificates="true"

# Watch certificate rollout (Kafka restarts pods):
oc get pods -n dark-noc-kafka -w

# After rotation: re-copy new CA cert to edge
oc get secret dark-noc-kafka-cluster-ca-cert -n dark-noc-kafka -o yaml | \
  oc --context=${EDGE_CONTEXT} apply -n openshift-logging -f -

# Restart edge collector
oc --context=${EDGE_CONTEXT} rollout restart daemonset/collector -n openshift-logging
```

## Verification
```bash
# Verify cert is valid and has > 30 days remaining
oc get secret <cert-secret> -n <namespace> \
  -o jsonpath='{.data.tls\.crt}' | base64 -d | \
  openssl x509 -noout -checkend 2592000  # 30 days
# Expected: Certificate will not expire
```

## Prevention
- cert-manager auto-renews at `renewBefore` threshold (default: 30 days before expiry)
- Alert on `certmanager_certificate_expiration_timestamp_seconds < time() + 30*24*3600`
- For Kafka: set `renewalDays: 30` in Kafka CR spec
