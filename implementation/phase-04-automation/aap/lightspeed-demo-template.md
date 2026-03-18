# AAP Lightspeed Demo Template (`lightspeed-generate-and-run`)

## Purpose
Create a dedicated AAP job template used by the LangGraph `lightspeed` branch.
This template is called through `mcp-aap` and is expected to represent a
Lightspeed-assisted playbook generation + execution workflow.

## Required Template Name
- `lightspeed-generate-and-run`

## Minimum Extra Vars Expected
- `namespace`
- `deployment`
- `edge_cluster`
- `incident_id`
- `lightspeed_mode`
- `failure_type`
- `generated_playbook_name`
- `generated_playbook_yaml`
- `generated_from_model`

## Recommended Setup in AAP UI
1. Create or use an SCM Project that contains your demo playbook path.
2. Create a Job Template named exactly `lightspeed-generate-and-run`.
3. Set inventory/credentials to your edge target (`edge-01` credential).
4. Enable prompt on launch for extra vars.
5. Save and launch once manually to validate permissions.

## API Verification
Use the controller API to verify template exists:

```bash
curl -ksS -u "admin:<AAP_PASSWORD>" \
  "https://<AAP_CONTROLLER_ROUTE>/api/controller/v2/job_templates/?name=lightspeed-generate-and-run" \
  | jq -r '.count, (.results[]?.id // empty), (.results[]?.name // empty)'
```

## Integration Contract
- LangGraph agent branch: `next_action = lightspeed`
- MCP call: `mcp-aap.launch_job(job_template_name=lightspeed-generate-and-run, extra_vars=...)`
- Follow-up actions:
  - ServiceNow incident creation (`mcp-servicenow`)
  - Slack notification (`mcp-slack`)
- Audit trail:
  - `incident-audit.generated_playbook_name` is emitted for executive traceability.
