# Runbook: DNS Failure — Service Resolution Issues

## Symptoms
- Pod logs: `dial tcp: lookup <service>.svc.cluster.local: no such host`
- `nslookup` fails inside pods
- Kafka connection fails with DNS error (not TCP refusal)
- Inter-service calls failing across namespaces

## Root Cause Analysis
1. CoreDNS pods not running or crashing
2. DNS search domains misconfigured in pod spec
3. NetworkPolicy blocking DNS traffic (port 53)
4. DNS cache poisoning (rare)
5. Service endpoint not yet populated (pods not ready)

## Diagnostic Steps
```bash
# Test DNS from inside a pod
oc exec -n dark-noc-hub deploy/dark-noc-agent -- \
  nslookup dark-noc-kafka-kafka-bootstrap.dark-noc-kafka.svc.cluster.local

# Check CoreDNS pods
oc get pods -n openshift-dns
oc logs -n openshift-dns -l dns.operator.openshift.io/daemonset-dns | tail -20

# Check DNS operator
oc get dns.operator/default

# Verify service exists
oc get svc dark-noc-kafka-kafka-bootstrap -n dark-noc-kafka
oc get endpoints dark-noc-kafka-kafka-bootstrap -n dark-noc-kafka
```

## Remediation Steps

### Fix 1: Restart CoreDNS
```bash
oc rollout restart daemonset/dns-default -n openshift-dns
oc rollout status daemonset/dns-default -n openshift-dns
```

### Fix 2: Check NetworkPolicy for DNS
```bash
# Ensure port 53 is not blocked
oc get networkpolicy -A | xargs -I{} oc describe networkpolicy {} -n <namespace>
# Look for any policy blocking UDP/TCP port 53
```

### Fix 3: Verify Service + Endpoints
```bash
# If endpoints are empty, the backing pods aren't ready
oc get endpoints -A | grep "<empty>"
# For each: check if pods are Running with readiness probe passing
```

## Prevention
- Monitor: `coredns_dns_responses_total{rcode="SERVFAIL"}` rate
- Don't use hostNetwork: true (bypasses cluster DNS)
- Always use FQDN: `service.namespace.svc.cluster.local` for cross-namespace
