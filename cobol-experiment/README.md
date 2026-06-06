# COBOL Experiment Suite

**Testing one hypothesis: that the rules embedded in COBOL can be re-expressed in
Liminate so the people governed by those rules can read them.**

COBOL and Liminate share a thesis — durable, readable business logic that the
people commissioning it can read. COBOL won the durability half (it still runs
banking, insurance, payroll, and benefits worldwide) and lost the readability
half (its English-shaped syntax is legible only to programmers, and only with the
data division, precedence rules, and storage clauses in hand).

This suite assembles public COBOL sources and tests whether Liminate can reclaim
the readability half: not by transpiling COBOL's *execution*, but by re-expressing
the *rule it encodes* as a `.limn` specification that runs on the real
interpreter and that a compliance officer — or the affected citizen — can read.

> Start here: [`corpus/tier3_worked_example/WALKTHROUGH.md`](corpus/tier3_worked_example/WALKTHROUGH.md)
> — one COBOL business rule, side by side with its validated Liminate translation.

---

## The three tiers

| Tier | What | Use |
|---|---|---|
| **Tier 1** | Business-logic COBOL samples (mortgage, payroll, retirement, discount, interest) | The corpus to translate. Real-shaped rules. |
| **Tier 2** | NIST CCVS85 conformance suite (~459 programs, public domain) | Understand COBOL's full structure; stress-test any future parser. Not a source of business rules. |
| **Tier 3** | One fully worked example: COBOL → `.limn`, validated end-to-end | The thesis demo. |

Provenance and license status for every source is in
[`docs/PROVENANCE.md`](docs/PROVENANCE.md). **Short version:** the upstream
sample repos carry no explicit license, so this suite *clones them at runtime*
rather than committing them. Only the single Tier 3 excerpt is vendored, with
attribution.

---

## Layout

```
cobol-experiment/
├── README.md                     ← you are here
├── .gitignore                    ← ignores corpus/_fetched/ (cloned sources)
├── corpus/
│   ├── tier1_business_samples/   ← (populated by fetch_corpus.sh → _fetched/)
│   ├── tier2_nist/               ← (populated by fetch_corpus.sh → _fetched/)
│   └── tier3_worked_example/
│       ├── retirement_eligibility.cobol      ← source rule (attributed excerpt)
│       ├── retirement_eligibility.limn       ← validated translation
│       ├── retirement_eligibility.actual.txt ← captured interpreter output
│       └── WALKTHROUGH.md                    ← the side-by-side
├── translations/                 ← add new COBOL→.limn pairs here
├── scripts/
│   ├── fetch_corpus.sh           ← clone Tier 1 + Tier 2 sources
│   ├── fetch_xcobol.sh           ← download the X-COBOL research dataset (Zenodo)
│   └── validate_translations.sh  ← run every .limn through the interpreter
└── docs/
    ├── PROVENANCE.md             ← sources + license status
    └── METHOD.md                 ← how to translate a COBOL rule to .limn
```

---

## Quick start

```bash
# 1. Get the interpreter
pipx install liminate        # or: pip install liminate
liminate --version           # expect 0.14.x

# 2. Run the worked example (no corpus fetch needed — it's vendored)
liminate corpus/tier3_worked_example/retirement_eligibility.limn

# 3. Validate every translation in the suite
bash scripts/validate_translations.sh

# 4. (Optional) Fetch the full corpus to translate more rules
bash scripts/fetch_corpus.sh         # Tier 1 + Tier 2 → corpus/_fetched/
bash scripts/fetch_xcobol.sh         # X-COBOL dataset (run locally)
```

---

## The discipline

A translation only counts if **the real interpreter accepts it.** The `.limn`
file is not a sketch of the language — it *is* the language, lexed, parsed,
type-checked, and run. `scripts/validate_translations.sh` enforces this: every
`.limn` in the suite must execute. The worked example was validated against
Liminate v0.14.1 before being committed.

This mirrors the project's core rule: verify against the real artifact, never
pattern-match from memory.

---

## What success looks like

The hypothesis is supported if, across a representative sample of COBOL business
rules, we can:

1. **Isolate the rule** from COBOL's plumbing (data division, PERFORM/DISPLAY
   scaffolding, storage clauses).
2. **Express it in the base 58-word vocabulary** (plus domain packs where a
   domain noun is genuinely needed) such that the interpreter accepts it.
3. **Keep it legible** to a non-programmer — the word-salad test holds.
4. **Surface the fidelity-risk decisions** (boundary conditions, rounding,
   inclusive ranges) on the readable surface instead of burying them.

Where a rule *cannot* be expressed cleanly, that's the more interesting result:
it tells us exactly where the vocabulary or the pack system needs to grow, the
same way prior domain lenses surfaced the deontic and temporal eras.
