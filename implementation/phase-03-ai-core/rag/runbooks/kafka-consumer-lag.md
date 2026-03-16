# Runbook: Kafka Consumer Lag — LangGraph Agent Behind on Events

## Symptoms
- `agent-events` or `nginx-logs` topic consumer lag > 1000 messages
- LangGraph agent not processing new incidents
- Kafka metrics: `kafka_consumergroup_lag` high
- Incident response time > 5 minutes (SLA breach)

## Root Cause Analysis
1. LangGraph agent pod crashed/restarting
2. LLM inference timeout causing slow processing
3. Kafka partition count too low (single consumer overloaded)
4. Agent backpressure from slow downstream (AAP, Slack)

## Diagnostic Steps
```bash
# Check consumer group lag
oc exec -n dark-noc-kafka dark-noc-kafka-dual-role-0 -- \
  bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group dark-noc-agent

# Check LangGraph agent pod
oc get pods -n dark-noc-hub -l app=dark-noc-agent
oc logs -n dark-noc-hub deploy/dark-noc-agent | tail -50

# Check inference latency
oc logs -n dark-noc-hub deploy/dark-noc-agent | grep "inference_time" | tail -10
```

## Remediation Steps

### Option 1: Restart Agent (Quick Fix)
```bash
oc rollout restart deployment/dark-noc-agent -n dark-noc-hub
oc rollout status deployment/dark-noc-agent -n dark-noc-hub --timeout=120s

# Watch lag decrease:
watch "oc exec -n dark-noc-kafka dark-noc-kafka-dual-role-0 -- \
  bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group dark-noc-agent"
```

### Option 2: Skip Old Messages (Last Resort)
```bash
# Reset consumer offset to latest (skip backlog)
# WARNING: Unprocessed incidents will be missed
oc exec -n dark-noc-kafka dark-noc-kafka-dual-role-0 -- \
  bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group dark-noc-agent \
  --topic nginx-logs \
  --reset-offsets --to-latest \
  --execute
```

### Option 3: Reduce Inference Batch Size
If lag is from LLM being slow, reduce `max_tokens` in agent config:
Edit ConfigMap `dark-noc-agent-config` → set `MAX_TOKENS=1024` (from 4096)

## Prevention
- Alert: `kafka_consumergroup_lag{group="dark-noc-agent"} > 100` for 5 minutes
- Implement agent heartbeat check (liveness probe on consumer health endpoint)
- Use KEDA to scale agent replicas based on consumer lag
