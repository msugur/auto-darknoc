# Session 013 — Modular Model Binding for AI Hub Catalog

**Date**: 2026-03-11
**Goal**: Make model selection modular so different OpenShift AI Hub Catalog models can be bound to LlamaStack without repo-wide edits.

## Changes Delivered

1. Added profile-driven model layer:
- `implementation/phase-03-ai-core/models/profiles/profile.template.env`
- `implementation/phase-03-ai-core/models/profiles/granite-4-h-tiny.env`
- `implementation/phase-03-ai-core/models/profiles/llama-3.2-3b-instruct.env`

2. Added render templates:
- `implementation/phase-03-ai-core/vllm/vllm-inferenceservice.tmpl.yaml`
- `implementation/phase-03-ai-core/llamastack/llamastack-distribution.tmpl.yaml`

3. Added renderer utility:
- `scripts/render-model-profile.sh`
- Supports render-only and `--apply` paths.

4. Added shared model-binding ConfigMaps:
- Hub: `implementation/phase-03-ai-core/models/model-binding-configmap.yaml`
- UI: `implementation/phase-06-dashboard/chatbot/model-binding-configmap.yaml`

5. Updated consumers to read model binding:
- Agent deployment now reads `MODEL_ID` and `VLLM_URL` from ConfigMap.
- Chatbot deployment now reads `AI_MODEL_NAME` and `MODEL_API_URL` from ConfigMap.
- `configMapKeyRef.optional=true` set for backward compatibility.

6. Docs updated:
- `docs/reference/MODEL-PROFILES.md`
- `implementation/phase-03-ai-core/README.md`
- `docs/deployment/START-HERE.md`
- root `README.md` reference link added.

## Validation

- `bash -n scripts/render-model-profile.sh` passed.
- Render test profiles:
  - `granite-4-h-tiny`
  - `llama-3.2-3b-instruct`
- Generated manifests created under `implementation/phase-03-ai-core/generated/`.

## Next Recommended Action

1. Pick a target model from OpenShift AI Hub Catalog.
2. Update `MODEL_STORAGE_URI` in a profile file.
3. Run:
   - `./scripts/render-model-profile.sh --profile <profile> --apply`
4. Restart:
   - `oc -n dark-noc-hub rollout restart deploy/dark-noc-agent`
   - `oc -n dark-noc-ui rollout restart deploy/dark-noc-chatbot`
