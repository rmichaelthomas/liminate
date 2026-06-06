#!/usr/bin/env bash
#
# validate_translations.sh — run every .limn translation through the real
# Liminate interpreter and confirm it parses and executes.
#
# This enforces the core discipline: a translation only counts if the
# interpreter accepts it. The .limn file is not a mockup of the language;
# it is the language.
#
# Usage:
#   bash scripts/validate_translations.sh
#
# Requires: liminate on PATH (pip install liminate / pipx install liminate)

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v liminate >/dev/null 2>&1; then
  echo "ERROR: 'liminate' not found on PATH."
  echo "Install it:  pipx install liminate   (or)   pip install liminate"
  exit 1
fi

echo "Liminate version: $(liminate --version)"
echo "Validating all .limn translations ..."
echo

fail=0
count=0
while IFS= read -r -d '' f; do
  count=$((count+1))
  if liminate --quiet "$f" >/dev/null 2>&1; then
    echo "  PASS  ${f#"$ROOT"/}"
  else
    echo "  FAIL  ${f#"$ROOT"/}"
    fail=$((fail+1))
  fi
done < <(find "$ROOT/corpus" "$ROOT/translations" -name '*.limn' -print0 2>/dev/null)

echo
if [ "$count" -eq 0 ]; then
  echo "No .limn files found."
  exit 0
fi
if [ "$fail" -eq 0 ]; then
  echo "All $count translation(s) accepted by the interpreter."
else
  echo "$fail of $count translation(s) failed."
  exit 1
fi
