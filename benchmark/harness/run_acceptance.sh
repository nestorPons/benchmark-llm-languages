#!/usr/bin/env bash
# Run the language-agnostic acceptance tests for a task.
#
# Usage:
#   run_acceptance.sh <task> [base_url] [workdir]
#
# It reads tasks/<task>/acceptance/checks.json. Checks are HTTP (against a
# running service) and/or command (CLI steps run in workdir), and are identical
# for every language.

set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$HARNESS_DIR")"

TASK="${1:?usage: run_acceptance.sh <task> [base_url] [workdir]}"
BASE_URL="${2:-}"
WORKDIR="${3:-}"

CHECKS="${ROOT_DIR}/tasks/${TASK}/acceptance/checks.json"

if [[ ! -f "$CHECKS" ]]; then
  echo "error: checks.json not found: $CHECKS" >&2
  exit 2
fi

ARGS=(--checks "$CHECKS")
[[ -n "$BASE_URL" ]] && ARGS+=(--base-url "$BASE_URL")
[[ -n "$WORKDIR" ]] && ARGS+=(--workdir "$WORKDIR")

exec python3 "$HARNESS_DIR/acceptance.py" "${ARGS[@]}"
