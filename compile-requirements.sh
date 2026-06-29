#!/usr/bin/env bash
# Compile pinned lock files for linux/amd64 (the Docker/CI target platform).
# Run this script whenever requirements.txt or requirements_dev.txt changes.
#
# Prerequisites: activate .venv first (pip-tools is in requirements_dev.txt)
#   source .venv/bin/activate

set -euo pipefail

PIP_ARGS="--platform linux_x86_64 --python-version 3.14 --only-binary :all:"

echo "==> Compiling requirements.lock (prod only)..."
pip-compile requirements.txt \
  --output-file requirements.lock \
  --no-header \
  --strip-extras \
  --quiet \
  --pip-args="$PIP_ARGS"

echo "==> Compiling requirements-dev.lock (prod + dev)..."
pip-compile requirements.txt requirements_dev.txt \
  --output-file requirements-dev.lock \
  --no-header \
  --strip-extras \
  --quiet \
  --pip-args="$PIP_ARGS"

echo "Done."
echo "  requirements.lock:     $(wc -l < requirements.lock | tr -d ' ') packages"
echo "  requirements-dev.lock: $(wc -l < requirements-dev.lock | tr -d ' ') packages"
