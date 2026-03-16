# Runbook: PostgreSQL Connection Pool Exhaustion

## Symptoms
- Application errors: `FATAL: remaining connection slots are reserved`
- `FATAL: too many connections`
- Langfuse or pgvector slow/unresponsive
- `oc logs deploy/langfuse` shows DB connection timeout

## Root Cause Analysis
1. Connection pool not configured — each app opens new connections
2. Max connections too low for number of app replicas
3. Connection leak — connections not closed after use
4. Long-running queries holding connections

## Diagnostic Steps
```bash
# Check current connections (via CloudNativePG pod)
oc exec -n dark-noc-observability langfuse-postgres-1 -- \
  psql -U langfuse -d langfuse \
  -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check max_connections setting
oc exec -n dark-noc-observability langfuse-postgres-1 -- \
  psql -U langfuse -d langfuse -c "SHOW max_connections;"

# Find long-running queries
oc exec -n dark-noc-observability langfuse-postgres-1 -- \
  psql -U langfuse -d langfuse \
  -c "SELECT pid, now()-pg_stat_activity.query_start AS duration, query
      FROM pg_stat_activity
      WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
```

## Remediation Steps

### Fix 1: Terminate Idle Connections
```bash
oc exec -n dark-noc-observability langfuse-postgres-1 -- \
  psql -U langfuse -d langfuse \
  -c "SELECT pg_terminate_backend(pid)
      FROM pg_stat_activity
      WHERE state = 'idle'
        AND query_start < now() - interval '10 minutes';"
```

### Fix 2: Increase max_connections
```bash
# Edit CloudNativePG cluster
oc edit cluster langfuse-postgres -n dark-noc-observability
# Under spec.postgresql.parameters:
#   max_connections: "300"  (increase from 200)
# CloudNativePG applies with a rolling restart
```

### Fix 3: Add PgBouncer Connection Pooler
CloudNativePG supports built-in PgBouncer pooler:
```yaml
# Add to CloudNativePG Cluster spec:
spec:
  managed:
    services:
      disabledDefaultServices: []
  # Add separate Pooler CR for connection pooling
```

## Prevention
- Use connection pool library in app (SQLAlchemy pool, Langfuse built-in pooling)
- Alert on: `pg_stat_activity_count > max_connections * 0.8`
- Set `idle_in_transaction_session_timeout = 30000` (30s) to auto-kill stuck txns
