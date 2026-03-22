#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UI_KUSTOMIZATION="$ROOT_DIR/gitops/prod/stacks/hub/ui/kustomization.yaml"

QUAY_REPO="${QUAY_REPO:-quay.io/msugur/auto-darknoc}"
TAG_SUFFIX="${TAG_SUFFIX:-$(git -C "$ROOT_DIR" rev-parse --short HEAD)}"
PUSH_LATEST="${PUSH_LATEST:-true}"

if command -v podman >/dev/null 2>&1; then
  OCI_BIN="podman"
elif command -v docker >/dev/null 2>&1; then
  OCI_BIN="docker"
else
  echo "Need podman or docker installed."
  exit 1
fi

if [[ -n "${QUAY_USERNAME:-}" && -n "${QUAY_TOKEN:-}" ]]; then
  echo "== Registry login =="
  echo "$QUAY_TOKEN" | "$OCI_BIN" login -u "$QUAY_USERNAME" --password-stdin quay.io
fi

DASHBOARD_SRC="$ROOT_DIR/implementation/phase-06-dashboard/dashboard"
CHATBOT_SRC="$ROOT_DIR/implementation/phase-06-dashboard/chatbot"

DASHBOARD_TAG="${QUAY_REPO}:dashboard-${TAG_SUFFIX}"
CHATBOT_TAG="${QUAY_REPO}:chatbot-${TAG_SUFFIX}"

echo "== Build dashboard image =="
"$OCI_BIN" build -t "$DASHBOARD_TAG" "$DASHBOARD_SRC"
echo "== Build chatbot image =="
"$OCI_BIN" build -t "$CHATBOT_TAG" "$CHATBOT_SRC"

echo "== Push versioned tags =="
"$OCI_BIN" push "$DASHBOARD_TAG"
"$OCI_BIN" push "$CHATBOT_TAG"

if [[ "$PUSH_LATEST" == "true" ]]; then
  DASHBOARD_LATEST="${QUAY_REPO}:dashboard-latest"
  CHATBOT_LATEST="${QUAY_REPO}:chatbot-latest"
  echo "== Push latest aliases =="
  "$OCI_BIN" tag "$DASHBOARD_TAG" "$DASHBOARD_LATEST"
  "$OCI_BIN" tag "$CHATBOT_TAG" "$CHATBOT_LATEST"
  "$OCI_BIN" push "$DASHBOARD_LATEST"
  "$OCI_BIN" push "$CHATBOT_LATEST"
fi

echo "== Update UI stack image tags =="
python3 - "$UI_KUSTOMIZATION" "$DASHBOARD_TAG" "$CHATBOT_TAG" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
dashboard = sys.argv[2]
chatbot = sys.argv[3]
text = path.read_text()

text = re.sub(
    r"(name:\s*dark-noc-chatbot[\s\S]*?path:\s*/spec/template/spec/containers/0/image\s*\n\s*value:\s*)([^\n]+)",
    rf"\1{chatbot}",
    text,
    count=1,
)
text = re.sub(
    r"(name:\s*dark-noc-dashboard[\s\S]*?path:\s*/spec/template/spec/containers/0/image\s*\n\s*value:\s*)([^\n]+)",
    rf"\1{dashboard}",
    text,
    count=1,
)
path.write_text(text)
PY

cat <<EOF

Release complete.
- Dashboard image: $DASHBOARD_TAG
- Chatbot image:   $CHATBOT_TAG

Next:
1) git add gitops/prod/stacks/hub/ui/kustomization.yaml
2) git commit -m "release(ui): dashboard/chatbot ${TAG_SUFFIX}"
3) git push
4) Argo sync app: ui-hub
EOF
