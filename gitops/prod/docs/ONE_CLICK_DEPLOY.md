# One-Click Deploy (Single Input Model)

This deploy path is designed to need only:
- Hub API URL + hub access credentials
- Edge API URL + edge access credentials

All other values are auto-generated/defaulted during deploy, including:
- runtime `.real.yaml` secret files
- service URLs (from OpenShift Routes when available)
- tool credentials (`admin/redhat` defaults for deployed tools)
- Slack/ServiceNow defaults already configured in render script

## 1) Prepare env files

Create `configs/hub/env.sh` from example and set:
- `HUB_API_URL`
- either `HUB_TOKEN` or `HUB_USERNAME` + `HUB_PASSWORD`
- `EDGE_API_URL`
- either `EDGE_TOKEN` or `EDGE_USERNAME` + `EDGE_PASSWORD`

`configs/edge/env.sh` is optional if edge values are already in `configs/hub/env.sh`.

Optional:
- Quay creds if private images are used:
  - `QUAY_USERNAME`, `QUAY_TOKEN`, `QUAY_EMAIL`

## 2) Run one command

```bash
source configs/hub/env.sh
# source configs/edge/env.sh   # optional
./scripts/one-click-gitops.sh --create-quay-pull
```

If edge destination name is different from `edge-cluster`:

```bash
./scripts/one-click-gitops.sh --edge-destination <your-edge-destination-name> --create-quay-pull
```

## 3) Verify

```bash
oc -n openshift-gitops get applications.argoproj.io
./scripts/deploy-validate.sh dashboard
```

Expected final state: all apps `Synced/Healthy`.

## UI/Chatbot release workflow

When dashboard/chatbot source changes, publish fresh images and update the UI stack tags:

```bash
export QUAY_USERNAME='<your-quay-user>'
export QUAY_TOKEN='<your-quay-token>'
./scripts/release-ui-images.sh
git add gitops/prod/stacks/hub/ui/kustomization.yaml
git commit -m "release(ui): dashboard+chatbot"
git push
```

Then sync `ui-hub` in Argo CD.

## Notes

- No manual placeholder editing is required.
- No manual secret template editing is required.
- Keep `*.real.yaml` out of Git.
