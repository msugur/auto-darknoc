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
```

## Start one-click deployment
```bash
oc apply -f gitops/prod/argocd/root-application.yaml
```

Then open Argo CD and sync `auto-darknoc-prod-root` (or keep autosync enabled).

## Built-in behavior
- PreSync gate validates OCP version and scales hub worker MachineSet if configured.
- Failed app sync sends summary to Slack `#demos`.
- Successful full sync posts masked Access Center to Slack and sends masked email to `msugur@redhat.com`.
