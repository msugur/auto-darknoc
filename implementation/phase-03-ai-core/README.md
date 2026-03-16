# Phase 03 — AI Core

## Overview
**Goal:** Fully operational AI inference stack: RHOAI DataScienceCluster, vLLM serving Granite 4.0 H-Tiny on GPU, LlamaStack distribution, and RAG knowledge base seeded with NOC runbooks + product documentation corpus.

**Duration:** 1-2 days (GPU driver init takes time)
**Clusters:** Hub only
**Depends on:** Phase 01 (GPU Operator + RHOAI operator), Phase 02 (MinIO for model registry, pgvector for RAG)
**Unblocks:** Phase 04 (AAP needs LlamaStack endpoint), Phase 05 (LangGraph agent needs vLLM + LlamaStack + RAG)

---

## Why This Phase Matters

The entire Dark NOC intelligence depends on this phase:

- **RHOAI DataScienceCluster** → Activates KServe, model registry, AI workbench — the AI platform layer
- **vLLM + Granite 4.0 H-Tiny** → The inference engine analyzing edge logs and generating remediations
- **LlamaStack** → Standardized agent framework that wraps vLLM with tool calling, safety, and memory
- **RAG seeding** → Loads NOC runbooks into pgvector so the AI has domain knowledge for better decisions
- **Model profiles** → Lets you swap model backends from Red Hat OpenShift AI Hub catalog without refactoring downstream components

---

## Components Deployed

```
Hub Cluster:
  redhat-ods-operator     ← DataScienceCluster CR activates RHOAI 3.3
  dark-noc-hub            ← vLLM InferenceService (Granite 4.0 H-Tiny)
  dark-noc-hub            ← LlamaStack Distribution + Server
  dark-noc-rag            ← RAG seed job (embeds NOC runbooks → pgvector)
```

---

## Model: IBM Granite 4.0 H-Tiny

| Property | Value |
|----------|-------|
| Architecture | Hybrid Mamba-2 + MoE Transformer |
| Parameters | 7B total / 1B active |
| VRAM at INT8 | ~8 GB (fits A10G 24GB) |
| Context window | 128K tokens |
| Languages | English, French, German, Spanish, Portuguese, Japanese, Korean, Chinese |
| License | Apache 2.0 |
| vLLM version | 0.15.1 with `--tool-call-parser=granite` |

---

## Execution Order

```
1. Apply DataScienceCluster CR      (activates RHOAI 3.3 components)
2. Create ServingRuntime            (vLLM 0.15.1 runtime template)
3. Create Hardware Profile          (A10G GPU configuration)
4. Download Granite H-Tiny         (from HuggingFace → MinIO rhoai-models)
5. Deploy vLLM InferenceService    (serves Granite on GPU)
6. Deploy LlamaStack Distribution  (wraps vLLM with agent API)
7. Seed RAG runbook corpus         (embed 10 NOC runbooks → pgvector)
8. Seed product docs corpus        (embed Red Hat + tool docs → pgvector)
9. Validate inference              (test structured output)
```

## Modular Model Profiles (AI Hub Catalog)

The repo supports model switching through profile files:

- `models/profiles/*.env`
- rendered output: `generated/`
- renderer: `scripts/render-model-profile.sh`

### How to switch model

```bash
# 1) Pick or create a profile
ls implementation/phase-03-ai-core/models/profiles

# 2) Update MODEL_STORAGE_URI from Red Hat AI Hub Catalog
#    (copy the OCI model URI from the catalog entry)

# 3) Render manifests for that profile
./scripts/render-model-profile.sh --profile granite-4-h-tiny

# 4) Apply generated manifests (or use --apply)
oc apply -f implementation/phase-03-ai-core/generated/model-binding-configmap.granite-4-h-tiny.yaml
oc apply -f implementation/phase-03-ai-core/generated/vllm-inferenceservice.granite-4-h-tiny.yaml
oc apply -f implementation/phase-03-ai-core/generated/llamastack-distribution.granite-4-h-tiny.yaml

# 5) Sync chatbot namespace model binding + restart consumers
oc -n dark-noc-ui create configmap dark-noc-model-binding \
  --from-literal=MODEL_ID=\"granite-4-h-tiny\" \
  --from-literal=VLLM_URL=\"http://granite-vllm-predictor.dark-noc-hub.svc:8080/v1\" \
  --from-literal=MODEL_API_URL=\"http://granite-vllm-predictor.dark-noc-hub.svc:8080/v1/completions\" \
  --from-literal=INFERENCE_SERVICE_NAME=\"granite-vllm\" \
  --dry-run=client -o yaml | oc apply -f -
oc -n dark-noc-hub rollout restart deploy/dark-noc-agent
oc -n dark-noc-ui rollout restart deploy/dark-noc-chatbot
```

### Bind an already-running model in `my-first-model`

If you already deploy models there (example: `llama-32-3b-instruct` runtime), bind Dark NOC to that service without redeploying AI core:

```bash
./scripts/bind-existing-model.sh \
  --namespace my-first-model \
  --inference-service granite-31-8b-lab-v1 \
  --model-id granite-3.1-8b-lab-v1
```

---

## Files in This Phase

```
phase-03-ai-core/
├── README.md                          ← This file
├── COMMANDS.md                        ← All commands with context
├── models/
│   ├── model-binding-configmap.yaml   ← Default model binding for hub consumers
│   └── profiles/
│       ├── profile.template.env       ← Template for new model profiles
│       ├── granite-4-h-tiny.env       ← Default Granite profile
│       └── llama-3.2-3b-instruct.env  ← Example alternate catalog profile
├── generated/                         ← Rendered model-specific manifests
├── rhoai/
│   ├── datasciencecluster.yaml       ← Activates RHOAI 3.3
│   ├── hardware-profile.yaml         ← A10G GPU hardware profile
│   └── serving-runtime.yaml          ← vLLM 0.15.1 ServingRuntime
├── vllm/
│   ├── vllm-inferenceservice.yaml     ← Legacy fixed manifest
│   └── vllm-inferenceservice.tmpl.yaml← Template rendered per model profile
├── llamastack/
│   ├── llamastack-distribution.yaml   ← Legacy fixed manifest
│   └── llamastack-distribution.tmpl.yaml ← Template rendered per model profile
└── rag/
    ├── seed-knowledge-base.py         ← Seeds NOC runbooks into pgvector
    ├── seed-product-docs.py           ← Seeds official product/tool docs into pgvector
    ├── documentation-sources.yaml     ← Version-pinned documentation URL manifest
    ├── rag-docs-seed-job.yaml         ← Kubernetes Job for docs ingestion
    └── runbooks/                      ← 10 NOC runbook text files
        ├── nginx-oomkilled.md
        ├── nginx-crashloop.md
        ├── nginx-config-error.md
        ├── network-timeout.md
        ├── storage-full.md
        ├── certificate-expired.md
        ├── dns-failure.md
        ├── kafka-consumer-lag.md
        ├── postgres-connection-pool.md
        └── aap-job-failure.md
```

---

## Next Phase
Once Granite inference is validated: **[Phase 04 — Automation](../phase-04-automation/README.md)**
