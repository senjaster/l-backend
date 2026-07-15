#!/usr/bin/env bash
# Compile pinned lock files for linux/amd64 (the Docker/CI target platform).
# Run this script whenever requirements.in or requirements-dev.in changes.
#
# Prerequisites: activate .venv first (pip-tools is in requirements-dev.in)
#   source .venv/bin/activate

set -euo pipefail

PIP_ARGS="--platform linux_x86_64 --python-version 3.14 --only-binary :all:"

echo "==> Compiling requirements.txt (prod only)..."
pip-compile requirements.in \
  --output-file requirements.txt \
  --no-header \
  --strip-extras \
  --quiet \
  --pip-args="$PIP_ARGS"

echo "==> Compiling requirements-dev.txt (prod + dev)..."
pip-compile requirements.in requirements-dev.in \
  --output-file requirements-dev.txt \
  --no-header \
  --strip-extras \
  --quiet \
  --pip-args="$PIP_ARGS"

echo "Done."
echo "  requirements.txt:     $(wc -l < requirements.txt | tr -d ' ') packages"
echo "  requirements-dev.txt: $(wc -l < requirements-dev.txt | tr -d ' ') packages"
