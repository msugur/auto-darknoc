# One-Click Deploy (Prod)

## Prerequisites
- Hub and Edge clusters reachable
- Argo destination cluster name for edge: `edge-cluster`
- Quay image pull credentials configured for runtime namespaces
- Filled secret templates:
  - `gitops/prod/secrets/platform-credentials.template.yaml` -> `platform-credentials.real.yaml`
  - `gitops/prod/secrets/notification-credentials.template.yaml` -> `notification-credentials.real.yaml`
  - `gitops/prod/secrets/mcp-integrations.template.yaml` -> `mcp-integrations.real.yaml`
  - `gitops/prod/secrets/ui-access.template.yaml` -> `ui-access.real.yaml`
  - `gitops/prod/secrets/aap-admin.template.yaml` -> `aap-admin.real.yaml`
  - `gitops/prod/secrets/data-runtime.template.yaml` -> `data-runtime.real.yaml`

## Bootstrap on Hub
```bash
oc login <hub-api> -u <admin>
oc apply -k gitops/prod/argocd
```

## Required per-cluster edits before sync
- Set `REPLACE_WITH_HUB_KAFKA_BOOTSTRAP_ROUTE` in `gitops/prod/stacks/edge/data-pipeline/kustomization.yaml`.
- Set `langfuse.nextauth.url` in `gitops/prod/apps/langfuse-hub.yaml`.

## Apply prod secrets
```bash
oc create namespace dark-noc-gitops --dry-run=client -o yaml | oc apply -f -
oc create namespace dark-noc-mcp --dry-run=client -o yaml | oc apply -f -
oc create namespace dark-noc-ui --dry-run=client -o yaml | oc apply -f -
oc create namespace aap --dry-run=client -o yaml | oc apply -f -
oc create namespace dark-noc-minio --dry-run=client -o yaml | oc apply -f -
oc create namespace dark-noc-rag --dry-run=client -o yaml | oc apply -f -
oc create namespace dark-noc-observability --dry-run=client -o yaml | oc apply -f -
oc apply -f gitops/prod/secrets/platform-credentials.real.yaml
oc apply -f gitops/prod/secrets/notification-credentials.real.yaml
oc apply -f gitops/prod/secrets/mcp-integrations.real.yaml
oc apply -f gitops/prod/secrets/ui-access.real.yaml
oc apply -f gitops/prod/secrets/aap-admin.real.yaml
oc apply -f gitops/prod/secrets/data-runtime.real.yaml
oc -n dark-noc-hub create secret docker-registry quay-pull --docker-server=quay.io --docker-username='<quay-user>' --docker-password='<quay-token>' --docker-email='<email>' --dry-run=client -o yaml | oc apply -f -
oc -n dark-noc-mcp create secret docker-registry quay-pull --docker-server=quay.io --docker-username='<quay-user>' --docker-password='<quay-token>' --docker-email='<email>' --dry-run=client -o yaml | oc apply -f -
oc -n dark-noc-ui create secret docker-registry quay-pull --docker-server=quay.io --docker-username='<quay-user>' --docker-password='<quay-token>' --docker-email='<email>' --dry-run=client -o yaml | oc apply -f -
oc -n dark-noc-hub secrets link default quay-pull --for=pull
oc -n dark-noc-hub secrets link dark-noc-agent quay-pull --for=pull
oc -n dark-noc-mcp secrets link default quay-pull --for=pull
oc -n dark-noc-mcp secrets link mcp-openshift-sa quay-pull --for=pull
oc -n dark-noc-ui secrets link default quay-pull --for=pull
```

## Start one-click deployment
```bash
oc apply -f gitops/prod/argocd/root-application.yaml
```

Then open Argo CD and sync `auto-darknoc-prod-root` (or keep autosync enabled).

## Built-in behavior
- Predeploy gate validates OCP version and scales hub worker MachineSet if configured.
- Failed app sync sends summary to Slack `#demos`.
- Successful full sync posts masked Access Center to Slack and sends masked email to configured recipient.

## Portability note
- Keep `*.real.yaml` files out of Git.
- Only commit `*.template.yaml` with placeholders.
- For a new cluster/ServiceNow instance, create new `*.real.yaml` files and re-apply secrets before Argo sync.

## Executive observability pack
- Grafana provisioning-as-code (datasource + dashboards) is included in GitOps.
- Dashboard details: `gitops/prod/docs/OBSERVABILITY_DASHBOARDS.md`
