# Model Profiles for LlamaStack/vLLM

This repo supports modular model switching for the Hub AI stack.

## Goal

Bind different model backends (from Red Hat OpenShift AI Hub Catalog) to the same Telco Autonomous Agentic AI Remediation control plane:

- vLLM serving layer
- LlamaStack distribution
- LangGraph agent model target
- NOC chatbot model target

## Files

- Profiles: `implementation/phase-03-ai-core/models/profiles/*.env`
- Renderer: `scripts/render-model-profile.sh`
- Rendered output: `implementation/phase-03-ai-core/generated/`
- Hub binding ConfigMap: `implementation/phase-03-ai-core/models/model-binding-configmap.yaml`
- UI binding ConfigMap: `implementation/phase-06-dashboard/chatbot/model-binding-configmap.yaml`

## Workflow

1. Open Red Hat OpenShift AI Hub Catalog and choose a model.
2. Copy the OCI/model URI for the selected model.
3. Update or create a profile under `models/profiles/`.
4. Render manifests:

```bash
./scripts/render-model-profile.sh --profile <profile-name>
```

5. Apply rendered manifests:

```bash
oc apply -f implementation/phase-03-ai-core/generated/model-binding-configmap.<profile-name>.yaml
oc apply -f implementation/phase-03-ai-core/generated/vllm-inferenceservice.<profile-name>.yaml
oc apply -f implementation/phase-03-ai-core/generated/llamastack-distribution.<profile-name>.yaml
```

6. Apply same model binding to `dark-noc-ui` namespace and restart consumers:

```bash
oc -n dark-noc-ui create configmap dark-noc-model-binding \
  --from-literal=MODEL_ID="<model-id>" \
  --from-literal=VLLM_URL="http://<inferenceservice>-predictor.dark-noc-hub.svc:8080/v1" \
  --from-literal=MODEL_API_URL="http://<inferenceservice>-predictor.dark-noc-hub.svc:8080/v1/completions" \
  --from-literal=INFERENCE_SERVICE_NAME="<inferenceservice>" \
  --dry-run=client -o yaml | oc apply -f -
oc -n dark-noc-hub rollout restart deploy/dark-noc-agent
oc -n dark-noc-ui rollout restart deploy/dark-noc-chatbot
```

## Bind Existing `my-first-model` InferenceService

If the model is already deployed in namespace `my-first-model` (for example with `vLLM NVIDIA GPU ServingRuntime for KServe v0.9.1.0`), bind Telco Autonomous Agentic AI Remediation directly to that endpoint:

```bash
./scripts/bind-existing-model.sh \
  --namespace my-first-model \
  --inference-service granite-31-8b-lab-v1 \
  --model-id granite-3.1-8b-lab-v1
```

This updates both `dark-noc-hub` and `dark-noc-ui` `dark-noc-model-binding` ConfigMaps and rolls out agent/chatbot.

## `granite-3.1-8b-lab-v1` quick path

1. Deploy the model in `my-first-model`:
   - `implementation/phase-03-ai-core/models/my-first-model/granite-3.1-8b-lab-v1-isvc.yaml`
2. Wait for `READY=True`:
   - `oc -n my-first-model get isvc granite-31-8b-lab-v1`
3. Bind into Telco Autonomous Agentic AI Remediation:
   - use `scripts/bind-existing-model.sh` command above.

## Notes

- For Granite-family models, set `TOOL_CALL_PARSER="granite"` in profile.
- For non-Granite models, leave `TOOL_CALL_PARSER` empty unless validated for that model/runtime.
- Keep profile names stable; they are attached as Kubernetes labels (`dark-noc/model-profile`).
