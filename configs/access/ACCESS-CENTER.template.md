# Telco Autonomous Agentic AI Remediation Access Center (Template)

Do not commit real credentials. Keep filled copy local as `configs/access/ACCESS-CENTER.local.md`.

## Cluster Access
- Hub API: `https://<hub-api-server>:6443`
- Edge API: `https://<edge-api-server>:6443`
- Hub admin username: `<admin-user>`
- Edge admin username: `<admin-user>`
- Hub token source: `<where token is generated>`
- Edge token source: `<where token is generated>`

## Hub Platform URLs
- OpenShift Console: `https://console-openshift-console.apps.<hub-domain>`
- OpenShift AI Dashboard: `https://data-science-gateway.apps.<hub-domain>`
- AAP Gateway: `https://aap-enterprise-aap.apps.<hub-domain>`
- AAP Controller UI: `https://aap-enterprise-controller-aap.apps.<hub-domain>`
- Dashboard UI: `https://dark-noc-dashboard-dark-noc-ui.apps.<hub-domain>`
- NOC Chat API/UI: `https://dark-noc-chatbot-dark-noc-ui.apps.<hub-domain>`
- Langfuse UI: `https://langfuse-dark-noc-observability.apps.<hub-domain>`

## Integration Access
- Slack workspace: `<workspace-url>`
- Slack channel: `#demos`
- Slack bot token location: `<vault/secret-manager reference>`
- ServiceNow instance: `https://<instance>.service-now.com`
- ServiceNow user: `<username>`
- ServiceNow password location: `<vault/secret-manager reference>`

## Runtime Secrets (Reference Only)
- `configs/hub/env.sh` (local only, gitignored)
- `configs/edge/env.sh` (local only, gitignored)
- Kubernetes secrets in namespaces:
  - `dark-noc-mcp`
  - `dark-noc-hub`
  - `dark-noc-observability`

## Notes
- Caller policy in ServiceNow: `Mithun Sugur`
- Edge site canonical name: `edge-01`
