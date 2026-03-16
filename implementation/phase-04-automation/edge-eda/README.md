# Edge EDA (edge-01) - Fast Local Self-Heal Pattern

## Purpose
Run a lightweight edge-local fast-path runner on `edge-01` for sub-minute remediation when hub latency or connectivity is degraded.

## Why Edge EDA
- Lower MTTR for repetitive incidents.
- Edge autonomy during hub/API interruptions.
- Reduces hub event load for known-safe remediations.

## Operating Model
- **Edge fast-path runner:** local webhook-triggered remediation (safe actions only).
- **Hub EDA + Agent:** global coordination, RCA, audit, ticketing, policy.
- Edge runner actions are written to pod logs in `dark-noc-edge`; these logs are forwarded to hub through the existing edge log-forwarding pipeline.

## Safe Fast-Path Actions (recommended)
- Restart nginx deployment.
- Scale deployment within bounded min/max.
- Rollout restart on config drift detection.

## Files
- `edge-eda-runner-deployment.yaml`: edge webhook runner deployment/service + local remediation logic.
- `edge-eda-rulebook.yaml`: optional rulebook pattern reference.

## Notes
- The initial `ansible-rulebook` runtime path was blocked by image/runtime constraints (`quay` auth and JVM dependency). The deployed manifest now uses a deterministic lightweight local runner for reliability in this environment.
- Keep edge fast-path scope narrow. Avoid destructive or multi-system workflows on edge.
- Use hub governance (AAP/ACM) as source of truth for policy and approval.
