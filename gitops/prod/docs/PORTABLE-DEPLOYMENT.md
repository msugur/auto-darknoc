# Portable Deployment Inputs (Automated)

For each new environment, provide only these values outside Git:

## Required inputs
- `HUB_API_URL`
- Hub auth: `HUB_TOKEN` or `HUB_USERNAME` + `HUB_PASSWORD`
- `EDGE_API_URL`
- Edge auth: `EDGE_TOKEN` or `EDGE_USERNAME` + `EDGE_PASSWORD`

Notes:
- Edge values can be in `configs/hub/env.sh`; separate `configs/edge/env.sh` is optional.
- If username/password is provided, token is auto-derived during one-click deploy.

## Optional inputs
- `SNOW_URL` (default: `https://<instance>.service-now.com`)
- `SNOW_USERNAME` (default: `admin`)
- `SNOW_PASSWORD` (default: `REPLACE_WITH_SERVICENOW_PASSWORD`)
- `QUAY_USERNAME`, `QUAY_TOKEN`, `QUAY_EMAIL` (required only for private Quay images and `--create-quay-pull`)

## Auto-generated during deploy
- `*.real.yaml` secret files are rendered from templates by `scripts/render-prod-secrets.sh`.
- Hub Kafka bootstrap and Langfuse route placeholders are auto-filled by `scripts/one-click-gitops.sh`.
- Use `--commit-runtime-config` to commit/push those non-secret route values when Argo source-of-truth is GitHub `main`.
- Service credentials for deployed tools default to `admin/redhat` unless overridden.
- URLs are inferred from OpenShift Routes when available, else generated from cluster app domains.

## Security rule
- Commit only `*.template.yaml`.
- Never commit `*.real.yaml`.
