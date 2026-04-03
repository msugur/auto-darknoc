# Security Policy

## Reporting a secret leak
If a credential appears in Git history or code:

1. Rotate/revoke the credential immediately with the provider.
2. Remove plaintext from current manifests/config.
3. Rewrite Git history to purge the leaked value from all commits.
4. Force-push rewritten history.
5. Notify collaborators to rebase/reclone.

## Repository controls
- Keep runtime secrets out of Git (`*.real.yaml` must never be committed).
- Commit only secret templates with placeholders.
- CI secret scanning is enforced via GitHub Actions (`.github/workflows/secret-scan.yml`).

## Operational guidance
- Do not assume deleting a file or making repo private removes leaked credentials.
- Treat any exposed token/password as compromised.
- Keep rotation logs outside this repository.
