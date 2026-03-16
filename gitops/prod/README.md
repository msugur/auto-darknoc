# Auto Dark NOC - Prod GitOps

Single production GitOps model for Hub + Edge OpenShift using Argo CD app-of-apps.

## Key decisions locked
- Prod-only deployment
- Real ServiceNow integration (no mock deployment)
- Slack workspace/channel: `octo-emerging-tech.slack.com` / `#demos`
- Images: `quay.io/msugur/auto-darknoc:<component-tag>`
- LlamaStack deployed on hub; model endpoint bound to `my-first-model` inference service

## Folder map
- `argocd/`: Argo bootstrap + root app + failure notifications
- `apps/`: Argo child apps with sync waves
- `stacks/`: hub/edge deployment stacks
- `bases/`: vendored manifests from implementation phases
- `secrets/`: placeholder templates (fill and apply as `.real.yaml`)
- `docs/`: operator deployment guides
