# Runbook: Network Timeout — Edge to Hub Connectivity

## Symptoms
- Kafka consumer lag increasing (edge logs not arriving)
- Vector collector logs: `connection refused` or `timeout`
- `oc get clusterlogforwarder -n openshift-logging` shows degraded
- Alert: `KafkaConsumerLag` > threshold

## Root Cause Analysis
Network timeout between edge and hub caused by:
1. Security group rules blocking Kafka port 9093
2. Hub Kafka pod not ready / restarting
3. Edge cluster DNS failure (cannot resolve hub service)
4. TLS certificate mismatch or expiry
5. Network policy blocking inter-cluster traffic

## Diagnostic Steps
```bash
# On Edge: test connectivity to hub Kafka
oc exec -n openshift-logging daemonset/collector -- \
  nc -zv dark-noc-kafka-kafka-bootstrap.dark-noc-kafka.svc.cluster.local 9093
# Expected: Connection to ... succeeded

# Check Vector logs for error details
oc logs -n openshift-logging daemonset/collector | grep -E "error|kafka" | tail -20

# On Hub: verify Kafka bootstrap service
oc get svc dark-noc-kafka-kafka-bootstrap -n dark-noc-kafka
oc get pods -n dark-noc-kafka

# Check TLS cert expiry
oc get secret dark-noc-kafka-cluster-ca-cert -n dark-noc-kafka \
  -o jsonpath='{.data.ca\.crt}' | base64 -d | \
  openssl x509 -noout -dates
```

## Remediation Steps

### Fix 1: Restart Kafka if unhealthy
```bash
oc rollout restart statefulset/dark-noc-kafka-dual-role -n dark-noc-kafka
oc wait --for=condition=Ready kafka/dark-noc-kafka -n dark-noc-kafka --timeout=300s
```

### Fix 2: Renew Kafka TLS cert on edge
```bash
# Re-copy Kafka CA cert to edge cluster
oc get secret dark-noc-kafka-cluster-ca-cert -n dark-noc-kafka -o yaml | \
  oc --context=${EDGE_CONTEXT} apply -n openshift-logging -f -

# Restart collector to pick up new cert
oc --context=${EDGE_CONTEXT} rollout restart daemonset/collector -n openshift-logging
```

### Fix 3: Check and fix network policies
```bash
oc get networkpolicy -n dark-noc-kafka
# Look for policies that might block external traffic
```

## Verification
```bash
# Trigger a test nginx log and verify it arrives in Kafka
oc --context=${EDGE_CONTEXT} exec -n dark-noc-edge deploy/nginx -- \
  sh -c "echo 'test error' >> /var/log/nginx/error.log"

# Wait 30 seconds, then check Kafka consumer offset
oc exec -n dark-noc-kafka dark-noc-kafka-dual-role-0 -- \
  bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group dark-noc-agent
# LAG should decrease
```
