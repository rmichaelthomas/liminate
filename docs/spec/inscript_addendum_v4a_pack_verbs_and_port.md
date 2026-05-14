# ADDENDUM
## Inscript Programming Language — Pack Verbs and TypeScript Port
### v4a — Extending the Domain Pack Contract

**Status:** LOCKED — EXTENDS `inscript_addendum_v3b_quoted_string_case_preservation.md`
**Date:** May 13, 2026
**Author:** Rob Thomas / R. Michael Thomas (architect) and Claude (builder, drafting)
**Document type:** Addendum — extends the domain pack contract to support pack-level verbs, defines the first domain pack with a verb (UI pack), and scopes the TypeScript parser port. No new base vocabulary. No new base verbs.
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v3b_quoted_string_case_preservation.md` (May 13, 2026), which extends v3a/v2d/v2c/v2b/v2a/v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (May 11–13, 2026). Continues from §132. Modifies the Python interpreter only to extend the domain pack contract (pack-level verbs) and add the `navigate` verb as the first pack verb. Does not modify the base vocabulary, the base verb set, or any prior locked decision. New infrastructure in the Möbius monorepo is limited to the TypeScript parser port package (`@mobius/inscript-lang`). A companion document — `inscript_inception_checkpoint_v1_client_surface.md` — captures the design for the Möbius client rendering adapter and proposal engine integration that motivated this addendum. That design is not in this addendum's build scope.

---

## HOW TO READ THIS DOCUMENT

- §133–§146 continue the section numbering from v3b.
- §133 establishes session context.
- §134–§136 specify the UI domain pack (vocabulary, verb, component schemas).
- §137 specifies the extended domain pack contract for pack-level verbs.
- §138 specifies the TypeScript parser port scope.
- §139 defines the build phases and sequence.
- §140 adds test sentences 118–127.
- §141 states the build boundary.
- §142 lists open questions.
- §143 is the resume prompt.

---

### §133 — SESSION CONTEXT

This addendum originated from a conversation about whether Inscript could be used to build applications — specifically, Möbius client surfaces authored in prose by non-programmers. That question produced a broader design for a UI domain pack, a rendering adapter, and a proposal engine (captured separately in the client surface inception checkpoint). This addendum extracts the two pieces that are ready to build now: the infrastructure (pack verb contract + TypeScript port) and the first domain pack that exercises it (UI pack with `navigate`).

The domain pack contract extension is motivated by a specific need — the UI pack requires `navigate` as a verb, and the v3a pack contract only supports nouns — but is designed as a general-purpose extension so future packs (game, healthcare, home automation) can register their own verbs without touching interpreter code.

---

## Part I — UI Domain Pack

### §134 — DOMAIN PACK VOCABULARY

**Decision: The UI domain pack adds 10 nouns to the active vocabulary when loaded. LOCKED as v4a UI domain pack vocabulary.**

| Word | Category | What it names |
|---|---|---|
| `screen` | noun | A distinct view or page |
| `button` | noun | An interactive click/tap element |
| `input` | noun | A text entry field |
| `text` | noun | A display-only text element |
| `list-view` | noun | A scrollable display of a list's contents |
| `card` | noun | A bounded content container |
| `image` | noun | A visual element |
| `section` | noun | A grouping container |
| `header` | noun | A title/heading area |
| `nav` | noun | A navigation element (tab bar, menu, sidebar) |

**Word salad test (§20).** Every word passes. A non-programmer already uses all ten when describing an app: "I want a screen with a header, a list of my orders, and a button to filter them."

**What was deliberately excluded.** Layout-mechanism words (`row`, `column`, `grid`, `flex`) are mechanism-layer, not concept-layer. If dogfooding surfaces a genuine gap, they would be added then.

**Pack JSON:**

```json
{
  "name": "ui",
  "vocabulary": [
    { "word": "screen", "category": "noun" },
    { "word": "button", "category": "noun" },
    { "word": "input", "category": "noun" },
    { "word": "text", "category": "noun" },
    { "word": "list-view", "category": "noun" },
    { "word": "card", "category": "noun" },
    { "word": "image", "category": "noun" },
    { "word": "section", "category": "noun" },
    { "word": "header", "category": "noun" },
    { "word": "nav", "category": "noun" }
  ],
  "verbs": [
    {
      "word": "navigate",
      "slots": [
        { "name": "target", "connective": "to", "required": true, "type_constraint": "screen" }
      ],
      "execution": { "type": "set_value", "target_name": "current-screen", "source_slot": "target" }
    }
  ],
  "declarations": [],
  "script": []
}
```

**Reserved word collision.** Per v1a §29, pack words are added to the reserved list during activation.

---

### §135 — UI DOMAIN PACK VERB: `navigate`

**Decision: The UI domain pack adds one verb: `navigate`. Pack-level — only active when the UI pack is loaded, not part of the base vocabulary. Slot signature: `navigate to <screen-name>`. LOCKED as v4a UI pack verb.**

**Why a new verb is needed.** `show` means "display a value." Repurposing it for screen transitions breaks the word salad test.

**Why pack-level, not base.** `navigate` is only meaningful with screens. A business rules program has no use for it. The base vocabulary stays permanently small (§19). The domain pack mechanism exists for contextually relevant vocabulary.

**Why no other verbs are added.** Every other UI action is expressible through existing verbs plus pack nouns. Screen creation uses `remember`. Data display uses `show`. Interaction handling uses `when`. Conditional routing uses `choose`.

**Slot signature:**

| Slot | Connective | Required | Type constraint | Example |
|---|---|---|---|---|
| TARGET | `to` | Yes | Record with descriptor `screen` | `navigate to dashboard` |

`navigate` without `to` is a parse error: "'navigate' needs a destination — try: navigate to <screen-name>."

The type constraint tells the semantic analyzer to check that the target is a record whose descriptor is `screen`. Non-screen targets produce: "'counter' is a number, not a screen. 'navigate to' expects a screen."

**Execution.** Sets a symbol called `current-screen` to the target screen's name. Defined in the pack JSON as `{ "type": "set_value", "target_name": "current-screen", "source_slot": "target" }`.

---

### §136 — COMPONENT SCHEMAS: PREDEFINED WITH FREEFORM OVERFLOW

**Decision: The UI domain pack defines predefined field schemas for each component type. Fields not in the schema are accepted and stored as metadata (freeform overflow). LOCKED as v4a schema architecture.**

| Component | Known fields |
|---|---|
| `screen` | `title` |
| `button` | `label`, `action` |
| `input` | `label`, `placeholder`, `value` |
| `text` | `content` |
| `list-view` | `source` |
| `card` | `title`, `content` |
| `image` | `source`, `alt` |
| `section` | `title` |
| `header` | `title`, `subtitle` |
| `nav` | `items` |

Unknown fields are accepted like any record field. `remember a button called submit with label as "Save" and color as blue` works — `color` is stored and accessible via `show color of submit`.

Schema enforcement is NOT semantic validation. A `button` without `label` is not an error. Inscript's invariant (§52) is deterministic interpretation of what the prose says, not enforcement of what it should say.

**v4a scope note.** The schemas are defined and documented. A rendering adapter that interprets them is specified in the companion inception checkpoint, not built here.

---

## Part II — Pack Verb Contract Extension

### §137 — GENERAL-PURPOSE PACK VERB CONTRACT

**Decision: The domain pack contract is extended so packs can register verbs with slot signatures, not just nouns. The contract is general-purpose — any pack can define any verb via JSON. LOCKED as v4a pack verb contract.**

**Why the extension is needed.** The v3a pack contract (§118) supports `declarations` and `script`. Packs cannot add verbs. Without extending the contract, `navigate` would have to be a base verb — always reserved — violating §19.

**Extended pack JSON schema:**

```json
{
  "verbs": [
    {
      "word": "<verb-name>",
      "slots": [
        {
          "name": "<slot-name>",
          "connective": "<connective-word>",
          "required": true,
          "type_constraint": "<descriptor-or-type>"
        }
      ],
      "execution": {
        "type": "<execution-type>",
        "target_name": "<symbol-to-set>",
        "source_slot": "<slot-name>"
      }
    }
  ]
}
```

**Slot definition fields:**

| Field | Required | Meaning |
|---|---|---|
| `name` | Yes | Slot's internal name (error messages, AST) |
| `connective` | Yes | Connective that introduces this slot |
| `required` | Yes | Whether the slot must be filled |
| `type_constraint` | No | If present, semantic analyzer checks target is a record whose descriptor matches |

**Execution definition fields:**

| Field | Required | Meaning |
|---|---|---|
| `type` | Yes | Execution behavior. v4a defines: `set_value` |
| `target_name` | For `set_value` | Symbol name to set |
| `source_slot` | For `set_value` | Which slot's resolved value to use |

**Parser handling.** Pack verbs are registered in the vocabulary as VERB tokens during activation. Slot signatures are stored in a pack verb signature table. Parser verb-dispatch checks the pack table after the base table. Slot filling follows the same algorithm as base verbs.

**Semantic analyzer handling.** When a slot has `type_constraint`, the analyzer checks: (1) target name exists, (2) target is a record, (3) record's descriptor matches the constraint (case-insensitive). Failure produces a plain-English error.

**Pack deactivation.** Verbs removed from vocabulary and signature table. Programs referencing pack verbs without the pack produce: "I don't recognize the word 'navigate'. It might be part of a domain pack that isn't loaded."

**Backward compatibility.** The `verbs` field is optional. Packs without it load as before.

**What this enables for future packs:**

| Pack | Verb | Signature |
|---|---|---|
| UI | `navigate to <screen>` | One slot, `to`, type `screen` |
| Game | `reveal <item> to <player>` | Two slots |
| Healthcare | `prescribe <medication> for <patient>` | Two slots, `for` |
| Home | `activate <device>` | One slot, bare target |

**Python implementation scope:**

| File | Change |
|---|---|
| `vocabulary.py` | `PackVerbSignature` type. Registration/deregistration methods. |
| `parser.py` | Pack verb dispatch after base verb dispatch. Slot filling from pack signature table. |
| `analyzer.py` | Type-constraint checking for pack verb slots. |
| `interpreter.py` | Pack verb execution dispatch. `set_value` execution type. |
| `adapter.py` | Extend `DomainPack` to include `verbs`. Extend JSON loading. |

---

## Part III — TypeScript Parser Port

### §138 — PORT SCOPE

**Decision: The TypeScript port covers lexer, reorderer, parser, semantic analyzer, and canonical renderer. New package `@mobius/inscript-lang` in the Möbius monorepo. Interpreter NOT ported. Pack verb contract included from day one. LOCKED as v4a TypeScript port scope.**

**Package structure:**

```
packages/inscript-lang/
├── src/
│   ├── vocabulary.ts
│   ├── lexer.ts
│   ├── reorderer.ts
│   ├── parser.ts
│   ├── analyzer.ts
│   ├── renderer.ts
│   ├── result.ts
│   ├── types.ts
│   └── index.ts
├── test/
│   ├── test_sentences.ts
│   └── ...
├── package.json
└── tsconfig.json
```

**Public API:**

```typescript
interface ValidationResult {
  status: 'success' | 'amber' | 'error';
  canonical?: string;
  ast?: InscriptAST;
  amberMessage?: string;
  errorMessage?: string;
  errorKind?: string;
}

function validate(source: string, packConfig?: PackConfig): ValidationResult[];
function validateLine(line: string, symbolTable?: SymbolTable, packConfig?: PackConfig): ValidationResult;
```

**What is NOT ported:** interpreter, listener, adapter contract, CLI. Execution stays in Python.

**Sync contract.** Both implementations validate against the same 127 test sentences. Same outcome category + same canonical rendering = passing.

**Why this port matters beyond v4a.** The TypeScript port is the foundation for: the tile interface (Branch C — real-time validation as tiles are arranged), client-side proposal validation (Branch E — the proposal engine validates generated programs without a network round-trip), and any future TypeScript consumer of Inscript validation.

---

## Part IV — Build Specification

### §139 — BUILD PHASES AND SEQUENCE

**Decision: The v4a build proceeds in two phases. LOCKED as v4a build sequence.**

**Phase 1 — Python pack verb contract + UI domain pack.**

1. Extend the Python domain pack contract to support pack-level verbs (§137).
2. Define the UI domain pack JSON with `navigate` and the 10 nouns (§134).
3. Test sentences 118–127 pass against the Python interpreter with the UI pack loaded.

**Acceptance criteria:** `--pack` loads the UI pack. `navigate to dashboard` parses, analyzes, executes. Pack nouns reserved when active. `navigate` unrecognized when pack not loaded. All 127 test sentences pass.

**Phase 2 — TypeScript parser port (`@mobius/inscript-lang`).**

1. Port lexer, reorderer, parser, semantic analyzer, canonical renderer.
2. Include pack verb contract from day one.
3. Validate against all 127 test sentences.

**Acceptance criteria:** All 127 sentences produce the same outcome and canonical rendering as Python.

---

### §140 — TEST SENTENCES (118–127)

Ten new test sentences. Require the UI pack loaded via `--pack`.

**Sentence 118 — `navigate to` basic.**
```
remember a screen called dashboard with title as "Orders"
navigate to dashboard
```
→ Canonical `navigate to dashboard`. Sets `current-screen` to `"dashboard"`.

**Sentence 119 — `navigate to` nonexistent screen (semantic error).**
```
navigate to settings
```
⚠ "I can't find 'settings'. You might need to 'remember' it first."

**Sentence 120 — `navigate to` non-screen record (semantic error).**
```
remember a number called counter with 5
navigate to counter
```
⚠ "'counter' is a number, not a screen. 'navigate to' expects a screen."

**Sentence 121 — `navigate` without `to` (parse error).**
```
navigate dashboard
```
⚠ "'navigate' needs a destination — try: navigate to <screen-name>."

**Sentence 122 — UI component with known fields.**
```
remember a button called submit with label as "Save" and action as save-order
show label of submit
```
→ `Save`.

**Sentence 123 — UI component with freeform overflow.**
```
remember a button called submit with label as "Save" and color as blue and size as large
show color of submit
```
→ `blue`.

**Sentence 124 — `when` handler on UI component.**
```
remember a button called refresh with label as "Refresh"
remember a list called orders with order1 and order2

when refresh is equal to clicked
  show orders
```
→ Handler registers with dependency on `refresh`.

**Sentence 125 — `navigate` inside `when` action block.**
```
remember a screen called settings with title as "Settings"

when mode is equal to admin
  navigate to settings
```
→ Parses and analyzes correctly inside action block.

**Sentence 126 — `navigate` as reserved word in name position (pack active).**
```
remember a value called navigate with 5
```
⚠ "The word 'navigate' is reserved in Inscript — it's used as a verb. Please choose a different name."

**Sentence 127 — Pack noun in name position without pack (no error).**
```
remember a value called button with 5
```
→ Succeeds without pack. `button` is only reserved when the UI pack is active.

---

### §141 — BUILD BOUNDARY

**v4a builds:**

| Component | Scope |
|---|---|
| **Pack verb contract (§137)** | General-purpose. JSON-defined slot signatures. Type constraints. `set_value` execution type. Backward-compatible. |
| **UI domain pack (§134)** | 10 nouns + 1 verb. Pack JSON in `examples/pack_ui.json`. |
| **`navigate` verb (§135)** | Pack-level. `navigate to <screen-name>`. Type constraint `screen`. Sets `current-screen`. |
| **Test sentences 118–127 (§140)** | 10 new sentences. |
| **`@mobius/inscript-lang` (§138)** | TypeScript port of lexer, reorderer, parser, analyzer, renderer. 127 sentences as sync. |

**v4a does NOT build:**

- Möbius client / rendering adapter (see companion inception checkpoint)
- Proposal engine / intent observer (see companion inception checkpoint)
- Tile interface (Branch C — foundation laid, interface deferred)
- Interpreter TypeScript port (execution stays in Python)
- Layout vocabulary, component nesting, `transform`/`compare`, domain pack activation syntax
- Client name / identity decisions (Branch D)

---

### §142 — OPEN QUESTIONS

| # | Question | Category |
|---|---|---|
| V4-Q1 | **Pack verb execution types beyond `set_value`.** Future pack verbs may need more complex execution. The contract is extensible. | Language design |
| V4-Q2 | **Pack verb connective reuse.** `navigate` uses `to`, which has multiple meanings. Verb-first dispatch handles it, but complex multi-slot verbs may create ambiguity. | Language design |

---

## WHAT IS LOCKED

- **UI domain pack vocabulary (§134).** 10 nouns. Word salad test passed.
- **`navigate` as pack-level verb (§135).** Only active with UI pack. `navigate to <screen-name>`. Type constraint `screen`. Sets `current-screen`.
- **Component schemas with freeform overflow (§136).** Predefined fields per component. Unknown fields accepted.
- **General-purpose pack verb contract (§137).** JSON-defined verbs with slot signatures, type constraints, execution types. Backward-compatible.
- **TypeScript port scope (§138).** `@mobius/inscript-lang`. Lexer through renderer. No interpreter. 127 sentences as sync.
- **Two-phase build (§139).** Phase 1 Python, Phase 2 TypeScript.
- **Ten test sentences (§140).** Sentences 118–127.

This addendum does NOT modify any prior locked decision except to extend the domain pack contract (§137). The 34-word base vocabulary is unchanged. The two-phase execution model is unchanged. All v3b locks are unchanged. The pack JSON schema is backward-compatible.

---

### §143 — RESUME PROMPT (Inscript Programming Language v4a)

*We are resuming from the Inscript Programming Language Pack Verbs and TypeScript Port Addendum v4a (May 13, 2026), which extends v3b (May 13, 2026) and back through the full addendum chain to the Inception Checkpoint v1 (May 11, 2026).*

*v4a does two things: (1) Extends the Python domain pack contract so packs can register verbs with slot signatures in JSON — general-purpose, not navigate-specific. The parser reads signatures dynamically, the semantic analyzer checks type constraints, and the interpreter dispatches execution types (`set_value` is the first). (2) Defines the UI domain pack: 10 nouns (`screen`, `button`, `input`, `text`, `list-view`, `card`, `image`, `section`, `header`, `nav`) + 1 pack verb (`navigate to <screen-name>`, type-constrained to screen records, sets `current-screen`). Component schemas are predefined with freeform overflow. Ten new test sentences (118–127). Python files modified: `vocabulary.py`, `parser.py`, `analyzer.py`, `interpreter.py`, `adapter.py`.*

*Phase 2 is a TypeScript parser port — new package `@mobius/inscript-lang` in the Möbius monorepo. Ports lexer, reorderer, parser, semantic analyzer, canonical renderer. Does NOT port the interpreter. Includes the pack verb contract from day one. All 127 test sentences as sync contract.*

*A companion document — `inscript_inception_checkpoint_v1_client_surface.md` — captures the design for building Möbius clients with Inscript (rendering adapter, event mapping, proposal engine, Narratia integration). That work is scoped separately and not in v4a.*

*The build specification is now twelve documents plus the 127-sentence test suite. 34-word base vocabulary unchanged. Pack verb contract is the only structural extension to the Python interpreter.*

---

## PROVENANCE NOTE

This addendum was produced from:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026): Domain pack architecture (§19), word salad test (§20), Q7 (deployment target).
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026): Reserved word collision on pack activation (§29), AST-state-filtered tile tray (§31).
- **`inscript_addendum_v3a_event_driven_execution.md`** (May 12, 2026): Adapter contract (§116), domain pack registration (§118), event queue (§119).
- **`inscript_addendum_v3b_quoted_string_case_preservation.md`** (May 13, 2026): Current state — 667 tests, 117 sentences, 34 reserved words. §132 is the prior section endpoint.
- **`rmichaelthomas/inscript` repo** (scanned May 13, 2026): v3b current, `adapter.py` with `DomainPack`/`Adapter`/`TestAdapter`, `--pack` CLI flag.
- **`rmichaelthomas/mobius` monorepo** (scanned May 13, 2026): `packages/core/src/inscript/` (structural sibling for port), `packages/narrative-core/`, `packages/inference/`.
- **Conversation** (May 13, 2026): Ten architect decisions across two documents.
- **Filename:** `inscript_addendum_v4a_pack_verbs_and_port.md` — domain `inscript`, class `addendum`, version `v4a`, subtitle `pack_verbs_and_port`.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE PACK VERBS AND TYPESCRIPT PORT ADDENDUM v4a*

*May 13, 2026*

*The base vocabulary is still sacred.*
*But now the packs can speak too.*
