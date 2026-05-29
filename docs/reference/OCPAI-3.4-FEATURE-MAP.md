# OpenShift AI 3.4 Feature Map for Dark NOC

Last updated: 2026-05-29

This branch targets a new OpenShift AI 3.4 redeploy of Autonomous Dark NOC.
The goal is to keep the existing hub/edge incident-remediation demo and add a
visible AI platform story: governed model access, optimized RAG, model training,
evaluation, registry promotion, and rebinding the NOC agent to a better model.

## Feature Mapping

| OpenShift AI 3.4 capability | Status in 3.4 | Dark NOC demo use |
|---|---|---|
| Models-as-a-Service | GA | Govern Granite/new model access with subscriptions, API keys, token quotas, rate limits, and showback. |
| MLflow Operator in DataScienceCluster | GA | Track model training, AutoML, AutoRAG, and evaluation runs. |
| Model Registry with OCI ModelCar storage | GA | Register baseline and candidate models, track lineage, and promote the approved model. |
| MLServer ServingRuntime | GA | Serve structured ML models from AutoML, such as severity or MTTR predictors. |
| NeMo Guardrails | Supported | Gate prompts/responses before AAP remediation and ServiceNow/Slack actions. |
| Llama Stack Responses API | Technology Preview | Demo OpenAI-compatible agent orchestration for incident analysis. |
| AutoML | Technology Preview | Train and compare incident severity/MTTR predictors from tabular incident history. |
| AutoRAG | Technology Preview | Optimize runbook retrieval for Dark NOC RCA and remediation recommendations. |
| RAGAS evaluation provider | Technology Preview | Score answer relevance, retrieval quality, and factual consistency for runbook RAG. |
| Garak evaluation provider | Technology Preview | Security/safety scan candidate LLM behavior before promotion. |
| llm-d distributed inference | Technology Preview | Optional advanced serving path for larger models and better inference observability. |
| MCP Catalog | Developer Preview | Compare built-in Red Hat MCP servers with Dark NOC custom MCP servers. |
| OpenShift AI MCP server | Developer Preview | Demo platform-native cluster troubleshooting tools alongside existing MCP mesh. |

## Implementation Boundary

Automated in GitOps:

- Operator channel is pinned to `stable-3.4`.
- `DataScienceCluster` enables MLflow Operator, TrustyAI, KubeRay, and
  Kubeflow Trainer.
- A GitOps-visible `ocpai-34-feature-gates` ConfigMap records which demo
  features are expected and whether they are GA, Technology Preview, or
  Developer Preview.
- A model lifecycle contract is deployed in `dark-noc-ml-lifecycle`.

Performed after the platform CRDs are present:

- MaaS model endpoints, subscriptions, API keys, quotas, and external provider
  routes.
- AutoML and AutoRAG optimization runs.
- MLflow experiment instances and run records.
- Model Registry entries and model version promotion.
- NeMo Guardrails policies and guarded endpoints.
- Optional llm-d `LLMInferenceService` migration for larger models.
- Optional MCP Catalog/server deployment.

## Demo Narrative

1. Start with the baseline Dark NOC incident remediation flow.
2. Show MaaS as the governed model consumption layer.
3. Show AutoRAG improving runbook retrieval against Dark NOC incident questions.
4. Show AutoML training a structured severity/MTTR model from incident history.
5. Show MLflow run tracking and Model Registry version lineage.
6. Promote the candidate model only after RAGAS/Garak/TrustyAI/guardrail gates.
7. Rebind the agent/chatbot endpoint and replay the incident to show improved
   confidence and lower escalation.

## Source References

- Red Hat OpenShift AI 3.4 documentation index:
  https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4
- Red Hat OpenShift AI 3.4 release notes:
  https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/release_notes/index
- Working with AutoRAG:
  https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/working_with_autorag/index
- Govern LLM access with Models-as-a-Service:
  https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/govern_llm_access_with_models-as-a-service/index
- Working with MLflow:
  https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/working_with_mlflow/index
- Ensuring AI safety with guardrails:
  https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/enabling_ai_safety_with_guardrails/index
