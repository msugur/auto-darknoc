# Session 001 — Dark NOC Project Kickoff + Full File Structure

**Date**: 2026-02-26
**Session Goal**: Design full solution architecture + create complete GitHub project structure
**Status**: ✅ COMPLETE — 96 files created

---

## What We Accomplished

### Architecture Design
- Designed end-to-end Autonomous Dark NOC solution
- Two SNO clusters: Hub (inference + orchestration) + Edge (log source)
- Full product stack with exact version pinning
- Defined 8 implementation phases covering all components

### Presentation
- Created 32-slide executive presentation: `/Users/msugur/Documents/Claude/DarkNOC-Presentation.md`
- Covers: Executive Overview, Prerequisites, Technical Overview, Workflow,
  Red Hat Product Capabilities, Implementation Plan, Outcomes, Demo Script

### Project Structure Created: 96 files across 8 phases
- Root: `/Users/msugur/Documents/Claude/dark-noc/`

---

## Files Created by Phase

### Foundation (Phase 01) — 14 files
- 11 operator subscription YAMLs (wave-0 and wave-1)
- hub + edge namespace YAMLs
- GPU MachineSet + helper script
- README + COMMANDS guide

### Data Pipeline (Phase 02) — 12 files
- MinIO: PVC + Deployment + Init Job
- Kafka: KRaft cluster + 5 topics
- PostgreSQL: Langfuse + pgvector (with BuildConfig)
- Langfuse: Redis + ClickHouse + Values + Secrets
- Logging: LokiStack + ClusterLogging + Edge CLF
- COMMANDS guide

### AI Core (Phase 03) — 16 files
- RHOAI DataScienceCluster + HardwareProfile
- vLLM InferenceService (Granite 4.0 H-Tiny)
- LlamaStack Distribution
- RAG seed script (Python)
- 10 NOC runbooks (nginx OOM, crashloop, network, storage, cert, kafka, dns, postgres, nginx-config-error, aap)
- README

### Automation (Phase 04) — 8 files
- AAP AutomationController + EDA Controller + Rulebook
- ACM MultiClusterHub + ManagedCluster
- Ansible playbook: restart-nginx
- README

### Agent & MCP (Phase 05) — 22 files
- 6x FastMCP servers (server.py + requirements.txt each):
  mcp-openshift, mcp-lokistack, mcp-kafka, mcp-aap, mcp-slack, mcp-servicenow
- LangGraph agent: agent.py + state.py + requirements.txt + Dockerfile + deployment.yaml
- mcp-openshift Dockerfile
- Combined MCP servers deployment YAML
- README

### Dashboard (Phase 06) — 5 files
- ServiceNow mock: main.py + Dockerfile + deployment.yaml
- README

### Edge Workloads (Phase 07) — 3 files
- nginx-deployment.yaml (with JSON logging)
- failure-cronjob.yaml (OOMKill simulator)
- README

### Phase 08 Validation — 2 files
- test-scenarios.sh (OOMKill + CrashLoop automated tests)
- README

### Root-level files — 8 files
- README.md, .gitignore
- configs/hub/env.sh.example, configs/edge/env.sh.example
- scripts/preflight.sh, scripts/teardown.sh
- docs/architecture/overview.md
- logs/COMMANDS-LOG.md

---

## Key Decisions Made

1. **Kafka KRaft-only**: Streams 3.1 has NO ZooKeeper — all yamls use KRaft mode
2. **RHOAI 3.3 fresh install**: Cannot upgrade from 2.x — documented as warning
3. **MinIO for all object storage**: Replaces S3 for air-gapped/demo use
4. **ServiceNow mock**: FastAPI service simulating 4 REST endpoints
5. **pgvector custom image**: Must be built via BuildConfig — base PG16 + pgvector extension
6. **LangGraph PostgresSaver**: Durable agent state survives pod restarts
7. **vLLM Structured Outputs**: JSON schema enforcement via xgrammar (no free-text parsing)
8. **Granite 4.0 H-Tiny**: 7B total / 1B active MoE, fits in 8GB VRAM at INT8

---

## Next Session Goals
- [ ] Provide hub cluster kubeconfig / oc login command
- [ ] Provide edge cluster kubeconfig / oc login command
- [ ] Confirm Slack workspace + provide Bot Token
- [ ] Confirm AWS region for GPU worker MachineSet
- [ ] Run preflight.sh to assess cluster readiness
- [ ] Begin Phase 01 deployment
