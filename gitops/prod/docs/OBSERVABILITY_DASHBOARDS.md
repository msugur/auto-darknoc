# Observability Dashboard Pack

Grafana is fully provisioned by GitOps from `gitops/prod/stacks/hub/observability`.

## Included Dashboards

1. `Dark NOC Executive Overview`
2. `LLM + GPU Performance`
3. `Langfuse Operations`

These dashboards are loaded automatically from:

- `gitops/prod/stacks/hub/observability/dashboards/01-exec-overview.json`
- `gitops/prod/stacks/hub/observability/dashboards/02-llm-gpu-performance.json`
- `gitops/prod/stacks/hub/observability/dashboards/03-langfuse-operations.json`

## Datasource

- Name: `Prometheus`
- UID: `prometheus`
- URL: `https://thanos-querier.openshift-monitoring.svc:9091`
- Auth: in-cluster ServiceAccount token (provisioned automatically)

## Login

- Grafana route: `https://grafana-dark-noc-grafana.apps.<cluster-domain>`
- Username: `admin`
- Password: `redhat`
