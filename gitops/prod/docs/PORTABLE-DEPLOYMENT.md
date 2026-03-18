# Portable Deployment Inputs (Manual)

For each new environment, provide these values outside Git by creating `*.real.yaml` from templates.

## Required secret files
- `gitops/prod/secrets/platform-credentials.real.yaml`
- `gitops/prod/secrets/notification-credentials.real.yaml`
- `gitops/prod/secrets/mcp-integrations.real.yaml`
- `gitops/prod/secrets/ui-access.real.yaml`
- `gitops/prod/secrets/aap-admin.real.yaml`
- `gitops/prod/secrets/data-runtime.real.yaml`

## Required non-secret edits per cluster
- `gitops/prod/stacks/edge/data-pipeline/kustomization.yaml`
  - Set `REPLACE_WITH_HUB_KAFKA_BOOTSTRAP_ROUTE`.
- `gitops/prod/apps/langfuse-hub.yaml`
  - Set `langfuse.nextauth.url` to the target Langfuse route.

## Security rule
- Commit only `*.template.yaml`.
- Never commit `*.real.yaml`.
