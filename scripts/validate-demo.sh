#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/7] Checking required folders..."
for d in configs scripts docs implementation logs playbooks; do
  [[ -d "$d" ]] || { echo "Missing folder: $d"; exit 1; }
done

echo "[2/7] Checking required tracker files..."
for f in logs/COMMANDS-LOG.md logs/PROGRESS-TRACKER.md docs/deployment/redeploy-runbook.md; do
  [[ -f "$f" ]] || { echo "Missing file: $f"; exit 1; }
done

echo "[3/7] Ensuring no local cache artifacts are packaged..."
if find . -type f \( -name '.DS_Store' -o -name '*.pyc' \) | grep -q .; then
  echo "Found unwanted cache files:" 
  find . -type f \( -name '.DS_Store' -o -name '*.pyc' \)
  exit 1
fi

echo "[4/7] Checking for obvious embedded secrets..."
if rg -nP "sha256~[A-Za-z0-9_-]{20,}|xox[abep]-[A-Za-z0-9-]{20,}|xoxe\\.xoxp-[A-Za-z0-9-]{20,}|sk-lf-[0-9a-f-]{20,}|pk-lf-[0-9a-f-]{20,}" . \
  --glob '!scripts/validate-demo.sh' \
  | rg -v "REPLACE-WITH|<your-|\\.\\.\\." >/tmp/darknoc-demo-secret-scan.txt; then
  echo "Potential secret-like strings found:" 
  sed -n '1,80p' /tmp/darknoc-demo-secret-scan.txt
  exit 1
fi

echo "[5/7] Validating deployment file inventory..."
YAML_COUNT=$(find implementation -type f \( -name '*.yaml' -o -name '*.yml' \) | wc -l | awk '{print $1}')
PY_COUNT=$(find implementation -type f -name '*.py' | wc -l | awk '{print $1}')
MD_COUNT=$(find . -type f -name '*.md' | wc -l | awk '{print $1}')
echo "YAML files: $YAML_COUNT"
echo "Python files: $PY_COUNT"
echo "Markdown files: $MD_COUNT"

if [[ "$YAML_COUNT" -lt 40 ]]; then
  echo "Unexpectedly low YAML count: $YAML_COUNT"
  exit 1
fi

echo "[6/7] Checking scripts are executable..."
for s in scripts/preflight.sh scripts/teardown.sh implementation/phase-08-validation/test-scenarios.sh implementation/phase-01-foundation/machineset/check-machineset.sh; do
  [[ -x "$s" ]] || { echo "Expected executable but not executable: $s"; exit 1; }
done

echo "[7/7] Checking placeholder credentials are templated..."
rg -n "<CHANGE-ME-|REPLACE-WITH|<your-" configs implementation >/tmp/darknoc-demo-placeholders.txt || true
PLACEHOLDERS=$(wc -l /tmp/darknoc-demo-placeholders.txt | awk '{print $1}')
echo "Placeholder markers found: $PLACEHOLDERS"

cat <<MSG

Validation complete: PASS
- Structure: OK
- Cache artifact check: OK
- Secret pattern scan: OK
- File inventory: OK
- Executable scripts: OK
- Placeholder credentials: OK
MSG
