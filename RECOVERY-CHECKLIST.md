# Auto Dark NOC Recovery Checklist

Use this checklist when returning after cluster teardown.

## 1. Get code
```bash
git clone https://github.com/msugur/auto-darknoc.git
cd auto-darknoc
git checkout main
```

## 2. Login to new Hub cluster
```bash
oc login <HUB_API_URL> -u <admin> -p '<password>'
```

## 3. Prepare runtime secrets (manual)
Copy templates to real files and fill values:
```bash
cp gitops/prod/secrets/platform-credentials.template.yaml gitops/prod/secrets/platform-credentials.real.yaml
cp gitops/prod/secrets/notification-credentials.template.yaml gitops/prod/secrets/notification-credentials.real.yaml
cp gitops/prod/secrets/mcp-integrations.template.yaml gitops/prod/secrets/mcp-integrations.real.yaml
cp gitops/prod/secrets/ui-access.template.yaml gitops/prod/secrets/ui-access.real.yaml
cp gitops/prod/secrets/aap-admin.template.yaml gitops/prod/secrets/aap-admin.real.yaml
cp gitops/prod/secrets/data-runtime.template.yaml gitops/prod/secrets/data-runtime.real.yaml
```

## 4. Cluster-specific edits before sync
- Set hub Kafka route for edge forwarding in:
  - `gitops/prod/stacks/edge/data-pipeline/kustomization.yaml`
- Set Langfuse external URL in:
  - `gitops/prod/apps/langfuse-hub.yaml`

## 5. Bootstrap Argo CD on Hub
```bash
oc apply -k gitops/prod/argocd
```

## 6. Create required namespaces and apply secrets
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
```

## 7. Configure Quay pull secret
```bash
oc -n dark-noc-hub create secret docker-registry quay-pull --docker-server=quay.io --docker-username='<quay-user>' --docker-password='<quay-token>' --docker-email='<email>' --dry-run=client -o yaml | oc apply -f -
oc -n dark-noc-mcp create secret docker-registry quay-pull --docker-server=quay.io --docker-username='<quay-user>' --docker-password='<quay-token>' --docker-email='<email>' --dry-run=client -o yaml | oc apply -f -
oc -n dark-noc-ui create secret docker-registry quay-pull --docker-server=quay.io --docker-username='<quay-user>' --docker-password='<quay-token>' --docker-email='<email>' --dry-run=client -o yaml | oc apply -f -

oc -n dark-noc-hub secrets link default quay-pull --for=pull
oc -n dark-noc-hub secrets link dark-noc-agent quay-pull --for=pull
oc -n dark-noc-mcp secrets link default quay-pull --for=pull
oc -n dark-noc-mcp secrets link mcp-openshift-sa quay-pull --for=pull
oc -n dark-noc-ui secrets link default quay-pull --for=pull
```

## 8. Start full GitOps deployment
```bash
oc apply -f gitops/prod/argocd/root-application.yaml
```

## 9. Verify apps
```bash
oc -n openshift-gitops get applications
```
Expect all applications to become `Synced` and `Healthy`.

## 10. References
- `gitops/prod/docs/ONE_CLICK_DEPLOY.md`
- `gitops/prod/docs/PORTABLE-DEPLOYMENT.md`
