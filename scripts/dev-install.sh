#!/usr/bin/env bash
set -euo pipefail

echo "== ai-security-camera dev install =="

if command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
  echo "uv: ${UV_BIN}"
else
  echo "uv: not found (pip fallback)"
fi

PIP_INDEX="$(python3 -m pip config get global.index-url 2>/dev/null || true)"
if [[ -n "${PIP_INDEX}" ]]; then
  echo "pip global.index-url is set"
else
  echo "pip global.index-url is not set"
fi

if [[ -n "${UV_INDEX_URL:-}" ]]; then
  echo "UV_INDEX_URL is set"
else
  echo "UV_INDEX_URL is not set"
fi

python3.12 -m venv .venv
source .venv/bin/activate

if ! python -m pip install --upgrade pip; then
  echo "pip upgrade failed. continuing with existing pip."
fi

install_dev() {
  python -m pip install -e ".[dev]"
}

if install_dev; then
  echo "Install complete (current index settings)."
else
  echo
  echo "Install failed with current package index settings."
  echo "If Takumi Guard token is expired/invalid, private index auth can fail with 401."
  echo
  if [[ "${GUARD_STRICT:-0}" == "1" ]]; then
    echo "GUARD_STRICT=1 is set, so fallback is disabled. Please fix your token and retry."
    exit 1
  fi

  echo "Retrying once with public PyPI fallback..."
  PIP_INDEX_URL="https://pypi.org/simple" python -m pip install -e ".[dev]"
  echo
  echo "Install complete via public PyPI fallback."
  echo "Tip: refresh Takumi Guard token to restore protected installs."
fi

echo "Install complete. Next: source .venv/bin/activate && pytest"
