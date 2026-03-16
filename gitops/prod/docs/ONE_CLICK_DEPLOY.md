# One-Click Deploy (Prod)

## Prerequisites
- Hub and Edge clusters reachable
- Argo destination cluster name for edge: `edge-cluster`
- Quay image pull credentials configured for runtime namespaces
- Filled secret templates:
  - `gitops/prod/secrets/platform-credentials.template.yaml` -> `platform-credentials.real.yaml`
  - `gitops/prod/secrets/notification-credentials.template.yaml` -> `notification-credentials.real.yaml`

## Bootstrap on Hub
```bash
oc login <hub-api> -u <admin>
oc apply -k gitops/prod/argocd
```

## Apply prod secrets
```bash
oc apply -f gitops/prod/secrets/platform-credentials.real.yaml
oc apply -f gitops/prod/secrets/notification-credentials.real.yaml
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
- Successful full sync posts masked Access Center to Slack and sends masked email to `msugur@redhat.com`.

## Executive observability pack
- Grafana provisioning-as-code (datasource + dashboards) is included in GitOps.
- Dashboard details: `gitops/prod/docs/OBSERVABILITY_DASHBOARDS.md`
