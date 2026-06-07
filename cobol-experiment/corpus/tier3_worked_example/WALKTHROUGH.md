# Worked Example — Retirement Eligibility

**The thesis in one file pair.** This is the proof-of-concept at the heart of the
experiment: take a real business rule encoded in COBOL, and express the *rule it
encodes* in Liminate — so that for the first time the person governed by the rule
can read it.

This is not a COBOL-to-Java transpile. It does not preserve COBOL's execution. It
reclaims COBOL's original *role*: the readable specification of the rule.

---

## The source rule (COBOL)

From `learn_cobol/RETIREMENT-AGE.cobol` (see `docs/PROVENANCE.md` for sourcing).
The business rule lives in one paragraph:

```cobol
       process-retirement.
           IF female AND age >= 60 OR male AND age >= 65
              DISPLAY "RETIREMENT AGE"
           ELSE
              DISPLAY "NOT RETIREMENT AGE"
           END-IF.
```

The rule: **a woman reaches retirement age at 60; a man reaches it at 65.**

To actually *read* that rule from the COBOL, you have to:

- know that `female` and `male` are 88-level condition names defined 25 lines
  earlier against a one-character field `gender`;
- know COBOL's operator precedence to resolve `A AND B OR C AND D` correctly
  (it binds as `(female AND age>=60) OR (male AND age>=65)` — but nothing on the
  line tells you that);
- know that `age` is `PIC 99 PACKED-DECIMAL`, a storage detail irrelevant to the
  rule but unavoidable in the source;
- mentally separate the *rule* from the `DISPLAY`/`ACCEPT`/`PERFORM` plumbing
  around it.

The readability COBOL promised is a façade. The surface is English-shaped; the
meaning is programmer-only.

---

## The same rule (Liminate)

From `corpus/tier3_worked_example/retirement_eligibility.limn`, validated against
the real interpreter (v0.14.1):

```
about "retirement eligibility"

remember a value called gender with "F"
remember a value called age with 62

permit gender is "F" and age is above 59 because "statutory retirement age 60 for women"
permit gender is "M" and age is above 64 because "statutory retirement age 65 for men"

show "Eligibility evaluated against statutory thresholds."
```

Every line is the rule. There is no plumbing to subtract. The thresholds are on
the line. The rationale for each threshold travels *with* the rule as a `because`
clause — inert metadata the interpreter never executes but always preserves, so
an auditor reading the program sees *why* 60 and *why* 65.

---

## What the interpreter actually does with it

Run it:

```bash
liminate corpus/tier3_worked_example/retirement_eligibility.limn
```

Captured output (`retirement_eligibility.actual.txt`):

```
I understand this as: remember a value called gender with "F"
I understand this as: remember a value called age with 62
I understand this as: permit gender is "F" and age is above 59 because "statutory retirement age 60 for women"
Permitted: gender is "F" and age is above 59. age is 62.
I understand this as: permit gender is "M" and age is above 64 because "statutory retirement age 65 for men"
I understand this as: show "Eligibility evaluated against statutory thresholds."
Eligibility evaluated against statutory thresholds.
```

The interpreter echoes each statement in canonical form ("I understand this as:")
*before* acting on it, so you can confirm the rule was understood as written —
then it reports that the 62-year-old woman is permitted.

---

## The one translation decision worth flagging

COBOL says `age >= 60`. Liminate's `is above` is **strict** greater-than
(verified: 60 `is above` 59 is true; 60 `is above` 60 is false). For integer
ages, `age >= 60` is exactly `age is above 59`, so the translation is faithful.

This is deliberately surfaced rather than hidden, because **this is where
fidelity risk lives in every real COBOL migration**: the boundary conditions.
`>=` vs `>`, rounding modes, off-by-one in inclusive ranges. A migration tool
that quietly picks one is the reason nobody trusts the rewrite. Liminate makes
the boundary explicit and readable, and the `because` clause can record the
inclusive-vs-exclusive intent in plain language.

This single decision is the entire Receipts / Invariant value proposition in
miniature: the rule is now in a form where the boundary can be *seen, verified,
and challenged* — not buried in `PIC` clauses and operator precedence.

---

## Why this is the demo

Put the two files side by side and ask the question that sells the thesis:

> Which one can your compliance officer read? Which one can the 62-year-old
> woman whose retirement it governs read?

The COBOL runs. The Liminate file runs *and* is legible to the person the rule is
about. That gap — six decades wide — is the whole pitch.
