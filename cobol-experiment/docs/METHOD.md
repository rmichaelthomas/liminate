# Method — Translating a COBOL Rule to Liminate

A repeatable procedure for turning a COBOL business rule into a validated `.limn`
specification. The goal is the *rule*, not the program.

## Step 0 — Find the rule, discard the plumbing

A COBOL program is mostly not the rule. Skip:

- `IDENTIFICATION` / `ENVIRONMENT` divisions (entirely plumbing)
- `DATA DIVISION` storage layout (`PIC`, `PACKED-DECIMAL`, `REDEFINES`) — these
  are *how the data is stored*, not *what the rule decides*
- `DISPLAY` / `ACCEPT` I/O, `PERFORM` control flow, `GOBACK` / `STOP RUN`

What's left — the `IF` / `EVALUATE` conditions, the arithmetic, the
`COMPUTE`/`ADD GIVING` calculations, the 88-level condition names — is the rule.

## Step 1 — Resolve the condition names

COBOL 88-levels hide meaning. `IF female` means nothing until you find:

```cobol
01  gender   PIC X.
    88  female  VALUE "F".
```

So `female` is `gender is "F"`. Inline every condition name; the reader of the
`.limn` should never need a lookup table.

## Step 2 — Make precedence explicit

`A AND B OR C AND D` in COBOL binds as `(A AND B) OR (C AND D)`, but the source
doesn't say so. In Liminate, write the rule as separate, self-evident statements
where possible. Two `permit` lines beat one compound line with hidden precedence.

## Step 3 — Map the verb

| COBOL intent | Liminate verb |
|---|---|
| enforce a condition must hold | `require` (halts if false) |
| enforce a condition must NOT hold | `forbid` (halts if true) |
| allow / note when a condition holds | `permit` (never halts) |
| compute a value | arithmetic in a `remember` / value position |
| filter a set | `filter ... where` |
| ordered steps | `then` |
| set membership | `includes` |

Pick `require` vs `permit` by what the COBOL does on the false branch. If the
program rejects/errors when the condition fails, it's `require` (or `forbid`). If
it merely branches to a different message, model both branches — often two
`permit` lines, or a `choose`.

## Step 4 — Handle boundary conditions explicitly

This is the high-fidelity-risk step. Liminate operators:

- `is above` / `is below` are **strict** (`>` / `<`). Verified.
- For `>= N` on integers, use `is above (N-1)`.
- For `<= N` on integers, use `is below (N+1)`.
- Record the inclusive/exclusive intent in a `because "..."` clause so the
  reader sees *why* the boundary is where it is.

Never let a boundary translation be silent. Boundaries are where COBOL rewrites
go wrong and where audits focus.

## Step 5 — Attach rationale

Use `because "..."` to carry the *why* — statute, policy number, SOX control —
as inert metadata. The interpreter preserves it, renders it, and (in the product
layer) Receipts can verify against it. This is the auditability COBOL never had.

Use `about "..."` on the first line to declare the rule's topic.

## Step 6 — Validate

```bash
liminate --quiet your_translation.limn
bash scripts/validate_translations.sh
```

If the interpreter rejects it, the translation is wrong — fix the `.limn`, not
the expectation. If it cannot be expressed at all without contortion, log it:
that's a signal about where the vocabulary or a domain pack needs to grow.

## Worked instance

See `corpus/tier3_worked_example/WALKTHROUGH.md` for this method applied
end-to-end to `RETIREMENT-AGE.cobol`, including the one boundary-condition
decision (`age >= 60` → `age is above 59`).
