# Dark NOC Access Center (Masked)

Generated: 2026-03-16 (America/New_York)

## Cluster Access

- Hub Console: `https://console-openshift-console.apps.ocp.ms2b2.sandbox2859.opentlc.com`
- Hub API: `https://api.ocp.ms2b2.sandbox2859.opentlc.com:6443`
- Hub OCP Version: `4.21.3`
- Hub Login: `admin / gBdY*********nocf`
- Edge Console: `https://console-openshift-console.apps.ocp.79zl4.sandbox951.opentlc.com`
- Edge API: `https://api.ocp.79zl4.sandbox951.opentlc.com:6443`
- Edge OCP Version: `4.21.3`
- Edge Login: `admin / VW9U********auFc`

## GitOps

- Argo CD URL: `https://openshift-gitops-server-openshift-gitops.apps.ocp.ms2b2.sandbox2859.opentlc.com`
- Argo Operator: `openshift-gitops-operator.v1.19.2`
- Argo Login: `admin / u5ZE************************gzj`

## AI + Inference

- OpenShift AI Operator: `rhods-operator.3.3.0`
- DataScienceCluster: `default-dsc (Ready=True)`
- InferenceService: `llama-32-3b-instruct`
- Inference Endpoint: `http://llama-32-3b-instruct-predictor.my-first-model.svc.cluster.local`
- LlamaStack Service: `dark-noc-llamastack-service.dark-noc-hub.svc:8321`

## App URLs

- Dashboard UI: `https://dark-noc-dashboard-dark-noc-ui.apps.ocp.ms2b2.sandbox2859.opentlc.com`
- Grafana: `https://grafana-dark-noc-grafana.apps.ocp.ms2b2.sandbox2859.opentlc.com`
- Langfuse: `https://langfuse-dark-noc-observability.apps.ocp.ms2b2.sandbox2859.opentlc.com`

## App Credentials

- Grafana: `admin / red***`
- AAP (target config): `admin / red***`
- Langfuse: app-signup enabled; no fixed admin password stored in-cluster.

## AAP URLs

- AAP: `https://aap-aap.apps.ocp.ms2b2.sandbox2859.opentlc.com`
- AAP Enterprise: `https://aap-enterprise-aap.apps.ocp.ms2b2.sandbox2859.opentlc.com`
- AAP Controller: `https://aap-enterprise-controller-aap.apps.ocp.ms2b2.sandbox2859.opentlc.com`
- AAP EDA: `https://aap-enterprise-eda-aap.apps.ocp.ms2b2.sandbox2859.opentlc.com`
- AAP Hub: `https://aap-enterprise-hub-aap.apps.ocp.ms2b2.sandbox2859.opentlc.com`

## External Integrations

- GitHub User: `msugur@redhat.com`
- GitHub PAT: `ghp_********************************QEfa`
- GitHub Repo: `https://github.com/msugur/auto-darknoc`
- Quay Namespace: `msugur`
- Quay Robot: `msugur+msugur`
- Quay Token: `A2KS**********************************************1P5B`
- ServiceNow URL: `https://dev365997.service-now.com`
- ServiceNow Login: `admin / D$*********9Uh4`
- Slack Workspace: `https://octo-emerging-tech.slack.com`
- Slack Channel: `#demos`
- Slack Bot Token (provided): `xoxb-*********************************wZqX`
- Slack App Token (provided): `xapp-*************************************************f489`

## Platform Operator Versions (Hub)

- CloudNativePG: `1.28.1`
- Loki Operator: `6.4.3`
- OpenShift Pipelines: `1.21.0`
- OpenShift Serverless: `1.37.1`
- Service Mesh 2: `2.6.14`
- Service Mesh 3: `3.2.2`
- Kiali Operator: `2.17.4`
- AAP Operator: `2.5.0`

## Notes

- This file is safe to share in demo channels (masked values only).
- Source of truth templates:
  - `gitops/prod/docs/ACCESS-CENTER.template.md`
  - `gitops/prod/secrets/*.template.yaml`
