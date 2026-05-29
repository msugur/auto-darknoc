# OpenShift AI 3.4 Redeploy Plan

Branch: `ocpai-3.4`

This plan upgrades the existing Dark NOC GitOps deployment to a new OpenShift AI
3.4 platform and adds a model lifecycle demo path.

## 1. Prepare Runtime Inputs

Use the existing one-click flow, but point Argo CD to this branch:

```bash
cp configs/hub/env.sh.example configs/hub/env.sh
cp configs/edge/env.sh.example configs/edge/env.sh
```

Set the new hub and edge cluster API/auth values, then set the Git source branch
to `ocpai-3.4` in your runtime config or Argo application source.

## 2. Bootstrap GitOps

```bash
source configs/hub/env.sh
source configs/edge/env.sh
./scripts/preflight.sh
./scripts/one-click-gitops.sh --commit-runtime-config --create-quay-pull
```

Verify the OpenShift AI operator channel:

```bash
oc -n redhat-ods-operator get subscription rhods-operator -o jsonpath='{.spec.channel}{"\n"}'
```

Expected:

```text
stable-3.4
```

Verify the 3.4 platform components:

```bash
oc get datasciencecluster default-dsc -o yaml
oc -n redhat-ods-applications get pods
oc -n dark-noc-hub get configmap ocpai-34-feature-gates -o yaml
```

## 3. Demo Feature Enablement

The branch enables the platform components required for the demo. Some 3.4
features are configured through OpenShift AI UI/API after install because their
CRDs and exact generated objects depend on the target cluster, identity groups,
model catalog entries, and storage locations.

Post-install actions:

- Configure MaaS subscriptions for `noc-admins`, `noc-engineers`, and
  `noc-viewers`.
- Generate a MaaS API key and update `dark-noc-model-binding` to use the MaaS
  endpoint.
- Create an MLflow tracking server/experiment for `dark-noc-incident-models`.
- Create an AutoRAG run using the Dark NOC runbooks and product docs corpus.
- Create an AutoML run using incident audit data for severity or MTTR
  prediction.
- Register the baseline model and candidate model in Model Registry.
- Add NeMo Guardrails policies for prompt injection, PII, and remediation
  action validation.
- Run RAGAS/Garak/TrustyAI evaluation before promotion.

## 4. Model Training and Promotion Flow

The training story should use real Dark NOC artifacts:

- Training data: incident audit topic exports, ServiceNow records, runbook
  labels, remediation outcomes, and MTTR.
- Baseline model: current Granite/vLLM or MaaS-backed model endpoint.
- Candidate model: tuned or newly trained model plus AutoML structured
  predictor where appropriate.
- Evaluation: RCA accuracy, escalation precision, remediation correctness,
  retrieval citation quality, guardrail pass rate, and latency.
- Promotion: Model Registry marks the candidate as approved; `dark-noc-model-
  binding` is updated; agent/chatbot rollouts restart.

Rebind command pattern:

```bash
./scripts/bind-existing-model.sh \
  --namespace <serving-namespace> \
  --inference-service <approved-model-service> \
  --model-id <approved-model-id>
```

## 5. Demo Verification

```bash
./scripts/deploy-validate.sh all
./scripts/validate-demo.sh
```

Then replay the incident:

```bash
oc -n dark-noc-edge create job --from=cronjob/nginx-failure-simulator nginx-failure-manual
```

Expected result:

- Kafka receives edge failure events.
- Dark NOC agent analyzes through the 3.4 model access path.
- Guardrails approve or block unsafe actions.
- AAP remediates known incidents.
- Slack/ServiceNow/Langfuse/Grafana show evidence.
- The promoted model shows improved confidence or accuracy against the baseline
  evaluation record.
