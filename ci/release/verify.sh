#!/usr/bin/env nix-shell
#!nix-shell -I nixpkgs=channel:nixos-unstable-small --pure --keep POETRY_PYPI_TOKEN_PYPI -p git poetry -i bash
# shellcheck shell=bash

set -euo pipefail

dry_run="${1:-false}"

# verify pyproject.toml
poetry check

# verify that the lock file is consistent with pyproject.toml
poetry lock --check

# verify that we have a token available to push to pypi using set -u
if [ "${dry_run}" = "false" ]; then
  : "${POETRY_PYPI_TOKEN_PYPI}"
fi
