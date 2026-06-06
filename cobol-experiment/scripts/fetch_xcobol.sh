#!/usr/bin/env bash
#
# fetch_xcobol.sh — download the X-COBOL research dataset from Zenodo.
#
# X-COBOL (Ali et al., 2023) is a dataset of 84 COBOL repositories mined from
# GitHub with rich development-cycle metadata, built specifically for empirical
# research on COBOL comprehension. It is the largest ready-made COBOL corpus
# for analysis.
#
#   Paper:   https://arxiv.org/abs/2306.04892
#   Dataset: https://zenodo.org/records/7968845
#   Site:    https://mir-sam-ali.github.io/X-COBOL/
#
# Zenodo is not reachable from some automated environments, so this is a
# separate manual-run script rather than part of fetch_corpus.sh.
#
# Usage:
#   bash scripts/fetch_xcobol.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/corpus/_fetched/x-cobol"
ZENODO_RECORD="7968845"

mkdir -p "$DEST"
cd "$DEST"

echo "Fetching X-COBOL dataset (Zenodo record $ZENODO_RECORD) ..."
echo "If this fails, download manually from:"
echo "  https://zenodo.org/records/$ZENODO_RECORD"
echo

# Zenodo exposes a record API listing the files and their direct download URLs.
if command -v curl >/dev/null 2>&1; then
  curl -L -o zenodo_record.json \
    "https://zenodo.org/api/records/$ZENODO_RECORD" || {
      echo "Could not reach Zenodo API. Download the archive manually."
      exit 1
    }
  echo "Record metadata saved to zenodo_record.json."
  echo "Open it to find the archive download link (usually a .zip), then:"
  echo "  curl -L -o x-cobol.zip '<link from zenodo_record.json>'"
  echo "  unzip x-cobol.zip"
else
  echo "curl not found. Download the dataset archive manually from the URL above."
fi

echo
echo "Once unzipped, the dataset contains:"
echo "  - cobol_files_data.csv  (per-file metadata: lines, comments, commits)"
echo "  - 7 more CSVs of repo/commit/issue/PR metadata"
echo "  - COBOL_Files/          (extracted .cbl sources, one dir per repo)"
