# Provenance and Licensing

Every source in this experiment, where it came from, and its license status.
**This file is the reason the suite clones instead of vendoring.**

## The licensing situation (read this first)

Of the three Tier 1 sample repos, **none carries an explicit license file.**
Under default copyright, "no license" means *all rights reserved* — the code is
publicly viewable but not freely redistributable. Therefore:

- We **do not commit** upstream COBOL sample files into the `liminate` repo.
- We **clone them at runtime** via `scripts/fetch_corpus.sh` into
  `corpus/_fetched/` (gitignored).
- The **one exception** is the single Tier 3 worked-example program
  (`retirement_eligibility.cobol`), reproduced as a short excerpt for commentary
  and education with full attribution. This is a defensible fair-use excerpt (37
  lines, transformative purpose: demonstrating a translation method), but if the
  upstream author objects it can be replaced with a clone-and-point reference
  like everything else.

If any source later needs to ship inside the repo, get an explicit license from
the upstream author first.

---

## Tier 1 — Business-logic samples (scripted, not vendored)

### mortgagesample
- **URL:** https://github.com/rradclif/mortgagesample
- **What:** IBM Dependency Based Build sample — a mortgage application with
  payment calculation (`epsmpmt.cbl`), input validation (`epsnbrvl.cbl`), and
  CICS/DB2 variants. Real-shaped financial business logic.
- **License:** None stated. Clone only.
- **Why it's here:** mortgage payment + eligibility validation is canonical
  banking business logic and a strong second worked-example candidate.

### cobol-samples (neopragma)
- **URL:** https://github.com/neopragma/cobol-samples
- **What:** Short, well-commented programs illustrating COBOL constructs —
  conditional logic (`IFEVAL.CBL`), 88-level condition names (`COND88.CBL`),
  interest/calc samples (`INVCALC.CBL`). Each has a companion notes file.
- **License:** None stated. Clone only.
- **Why it's here:** the cleanest small examples of the COBOL constructs that
  carry business rules (88-levels, EVALUATE), useful for building a translation
  pattern catalog.

### learn_cobol (kalsmic)
- **URL:** https://github.com/kalsmic/learn_cobol
- **What:** ~40 small programs, many of which are self-contained business rules:
  `RETIREMENT-AGE`, `DISCOUNT`, `COMPOUND-INTEREST`, `MORTGAGE`, `PAYROL00`,
  `ELECTRICITY-BILL`, `RETIREMENT-AGE`, `AGE-CHECK`.
- **License:** None stated. Clone only.
- **Why it's here:** the highest density of isolable business rules in the
  corpus — ideal for building out many small COBOL-to-`.limn` translation pairs.
- **Worked example source:** `RETIREMENT-AGE.cobol` (see Tier 3).

---

## Tier 2 — NIST CCVS85 conformance suite (public domain)

- **What:** The NIST COBOL 85 Compiler Validation System (CCVS85, aka ANSI85) —
  ~459 COBOL test programs (the user guide cites ~300 programs each containing
  several independent tests). Originally issued under FIPS-21-2.
- **License:** US Federal Government work; treated as public domain. (NIST's
  own current test suites are released CC0 / not subject to US copyright; the
  historical CCVS85 README notes "can be used free, copyrights are likely
  reserved" — so attribute, and prefer it for structure analysis over
  redistribution.)
- **Canonical sources:**
  - GnuCOBOL bundles it: https://sourceforge.net/projects/gnucobol/files/nist/
    (the `newcob.val` archive)
  - opensourcecobol repo (cloned by `fetch_corpus.sh tier2`)
- **Why it's here:** exercises the full breadth of COBOL language features. Use
  it to understand COBOL's structure and to stress-test any future automated
  COBOL parser — *not* as a source of business rules (these test the compiler,
  not business logic).

---

## Tier 3 — The worked example (excerpt vendored, with attribution)

- **File:** `corpus/tier3_worked_example/retirement_eligibility.cobol`
- **Source:** `RETIREMENT-AGE.cobol` from kalsmic/learn_cobol (above).
- **Status:** 37-line excerpt reproduced for educational commentary with
  attribution in the file header. Replaceable with a clone-and-point reference
  if needed.
- **Translation:** `retirement_eligibility.limn`, validated against the real
  Liminate interpreter (v0.14.1). See `WALKTHROUGH.md`.

---

## The X-COBOL research dataset (separate fetch)

- **URL (dataset):** https://zenodo.org/records/7968845
- **URL (paper):** https://arxiv.org/abs/2306.04892
- **What:** 84 COBOL repositories mined from GitHub with rich development-cycle
  metadata (8 CSVs + extracted `.cbl` sources), built for empirical COBOL
  research.
- **License:** See the Zenodo record (Creative Commons; confirm the exact
  variant on the record page before redistributing).
- **How to get it:** `scripts/fetch_xcobol.sh` (Zenodo is not always reachable
  from automated environments, so this is a manual-run script).
- **Why it's here:** the largest ready-made COBOL corpus for analysis — the
  right substrate for any statistical claim about COBOL verb usage, comment
  density, or rule patterns.
