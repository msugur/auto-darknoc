# Dark NOC Final Handoff Evidence

Captured: 2026-05-30

## Git

- Repository: `https://github.com/msugur/auto-darknoc`
- Branch: `ocpai-3.4`
- Release image tag suffix: `ocpai-3.4-ready`

## GitOps Status

- Argo applications: `14/14 Synced Healthy`
- `agent-mcp-hub`: `Synced Healthy`
- `ui-hub`: `Synced Healthy`

## Runtime Images

- `dark-noc-agent`: `quay.io/msugur/auto-darknoc:agent-ocpai-3.4-ready`
- `mcp-openshift`: `quay.io/msugur/auto-darknoc:mcp-openshift-ocpai-3.4-ready`
- `mcp-lokistack`: `quay.io/msugur/auto-darknoc:mcp-lokistack-ocpai-3.4-ready`
- `mcp-kafka`: `quay.io/msugur/auto-darknoc:mcp-kafka-ocpai-3.4-ready`
- `mcp-aap`: `quay.io/msugur/auto-darknoc:mcp-aap-ocpai-3.4-ready`
- `mcp-slack`: `quay.io/msugur/auto-darknoc:mcp-slack-ocpai-3.4-ready`
- `mcp-servicenow`: `quay.io/msugur/auto-darknoc:mcp-servicenow-ocpai-3.4-ready`
- `dark-noc-dashboard`: `quay.io/msugur/auto-darknoc:dashboard-ocpai-3.4-ready`
- `dark-noc-chatbot`: `quay.io/msugur/auto-darknoc:chatbot-ocpai-3.4-ready`

## Final End-to-End Rehearsal

- Trigger timestamp: `2026-05-30T02:41:29Z`
- Kafka offset: `2`
- Incident: `675de4c2-b537-403f-a259-31bbcc53f6cf`
- AAP job: `8`
- AAP status: `successful`
- ServiceNow ticket: `INC0010014`
- ServiceNow state: `1`
- Audit: record written
- Integrations API: `15/15 up`
- Platform availability: `100%`

## Demo Links

- Dashboard: `https://dark-noc-dashboard-dark-noc-ui.apps.ocp.z6ch9.sandbox2776.opentlc.com`
- Chatbot: `https://dark-noc-chatbot-dark-noc-ui.apps.ocp.z6ch9.sandbox2776.opentlc.com`
- AAP jobs: `https://aap-enterprise-controller-aap.apps.ocp.z6ch9.sandbox2776.opentlc.com/#/jobs`
- ServiceNow incidents: `https://dev354749.service-now.com/nav_to.do?uri=%2Fincident_list.do`
- Slack workspace: `https://octo-emerging-tech.slack.com`
- Langfuse: `https://langfuse-dark-noc-observability.apps.ocp.z6ch9.sandbox2776.opentlc.com`
