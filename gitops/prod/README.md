# Auto Dark NOC - Prod GitOps

Single production GitOps model for Hub + Edge OpenShift using Argo CD app-of-apps.

## Key decisions locked
- Prod-only deployment
- Real ServiceNow integration (no mock deployment)
- Slack workspace/channel: `octo-emerging-tech.slack.com` / `#demos`
- Images: `quay.io/msugur/auto-darknoc:<component-tag>`
- Current release image tags (`ocpai-3.4-ready`):
  - `quay.io/msugur/auto-darknoc:agent-ocpai-3.4-ready`
  - `quay.io/msugur/auto-darknoc:mcp-openshift-ocpai-3.4-ready`
  - `quay.io/msugur/auto-darknoc:mcp-lokistack-ocpai-3.4-ready`
  - `quay.io/msugur/auto-darknoc:mcp-kafka-ocpai-3.4-ready`
  - `quay.io/msugur/auto-darknoc:mcp-aap-ocpai-3.4-ready`
  - `quay.io/msugur/auto-darknoc:mcp-slack-ocpai-3.4-ready`
  - `quay.io/msugur/auto-darknoc:mcp-servicenow-ocpai-3.4-ready`
  - `quay.io/msugur/auto-darknoc:dashboard-ocpai-3.4-ready`
  - `quay.io/msugur/auto-darknoc:chatbot-ocpai-3.4-ready`
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
