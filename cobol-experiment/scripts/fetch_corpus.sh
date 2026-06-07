#!/usr/bin/env bash
#
# fetch_corpus.sh — reproducibly source the public COBOL corpus.
#
# This script clones the scriptable sources (Tier 1 business samples and the
# Tier 2 NIST suite). Nothing here is committed to the liminate repo, because
# none of the upstream sample repos carry an explicit license (see
# docs/PROVENANCE.md). We clone at runtime so the experiment is reproducible
# without redistributing other people's code.
#
# Usage:
#   bash scripts/fetch_corpus.sh          # fetch everything
#   bash scripts/fetch_corpus.sh tier1    # business-logic samples only
#   bash scripts/fetch_corpus.sh tier2    # NIST suite only
#
# Output goes to corpus/_fetched/ which is gitignored.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/corpus/_fetched"
TARGET="${1:-all}"

mkdir -p "$DEST"

clone() {
  local url="$1" dir="$2"
  if [ -d "$DEST/$dir" ]; then
    echo "  [skip] $dir already present"
  else
    echo "  [clone] $url"
    git clone --depth 1 "$url" "$DEST/$dir" >/dev/null 2>&1
  fi
}

fetch_tier1() {
  echo "Tier 1 — business-logic COBOL samples"
  # Mortgage application (IBM DBB sample; mortgage payment + validation logic)
  clone "https://github.com/rradclif/mortgagesample.git" "mortgagesample"
  # General-purpose business samples (conditional logic, 88-levels, EVALUATE)
  clone "https://github.com/neopragma/cobol-samples.git" "cobol-samples"
  # Learning corpus with many small business rules (payroll, retirement,
  # discount, compound interest, mortgage, electricity bill, etc.)
  clone "https://github.com/kalsmic/learn_cobol.git" "learn_cobol"
}

fetch_tier2() {
  echo "Tier 2 — NIST CCVS85 (ANSI 85) conformance suite"
  echo "  The NIST COBOL test suite (~459 programs) is US-government public"
  echo "  domain. GnuCOBOL bundles it. The cleanest reproducible source is the"
  echo "  GnuCOBOL repo's tests/cobol85 directory (newcob.val archive)."
  clone "https://github.com/opensourcecobol/opensourcecobol.git" "opensourcecobol"
  echo "  NOTE: The canonical newcob.val archive is also downloadable from"
  echo "  SourceForge: https://sourceforge.net/projects/gnucobol/files/nist/"
  echo "  That host is not always reachable from automated environments; if you"
  echo "  need the raw NIST programs, download newcob.val manually and place it"
  echo "  in corpus/_fetched/nist/."
}

case "$TARGET" in
  tier1) fetch_tier1 ;;
  tier2) fetch_tier2 ;;
  all)   fetch_tier1; echo; fetch_tier2 ;;
  *) echo "Unknown target: $TARGET (use tier1, tier2, or all)"; exit 1 ;;
esac

echo
echo "Done. Fetched sources are in: corpus/_fetched/ (gitignored)"
echo "See docs/PROVENANCE.md for what each source is and its license status."
