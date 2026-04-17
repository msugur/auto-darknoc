# Telco Autonomous Agentic AI Remediation - Prod GitOps

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
- `secrets/`: all credentials/access are manual-input templates; no live secrets committed
- `docs/`: operator deployment guides
  - portability checklist: `docs/PORTABLE-DEPLOYMENT.md`
