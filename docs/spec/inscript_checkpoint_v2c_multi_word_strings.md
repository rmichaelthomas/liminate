# CHECKPOINT
## Inscript Programming Language — Multi-Word Strings
### v2c — The D7 Question

**Status:** RECOMMENDATIONS FOR ARCHITECT
**Date:** May 12, 2026
**Author:** Rob Thomas / R. Michael Thomas (architect) and Claude (builder, drafting)
**Document type:** Checkpoint — deep analysis of D7 (multi-word strings), the single open design question deferred through v2a §72 and confirmed as next-up in v2b. Three candidate approaches are evaluated against every locked spec surface. Open design questions enumerated for the architect. External review recommended before locking.
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Continues from `inscript_addendum_v2b_composition_returns.md` (May 12, 2026), §84. The D7 deferral was catalogued in the v1 dogfooding gap inventory (D7), triaged in the v2 Design Triage §5 as needing a dedicated checkpoint, explicitly deferred in v2a §72 with three candidate approaches documented, and reconfirmed as the next open question in v2b's resume prompt. This checkpoint does not lock any spec change — it presents the analysis and recommendations for architect decision, with external review (Gemini + ChatGPT) recommended before locking, matching the pattern used for v1a/v1b/v1c/v1d.

---

## HOW TO READ THIS DOCUMENT

- §85 frames the problem: what multi-word strings are, why they matter, and which spec surfaces they touch.
- §86 evaluates **Approach A — Quoting** against each spec surface.
- §87 evaluates **Approach B — Hyphenation Convention** against each spec surface.
- §88 evaluates **Approach C — Multi-Word Phrase Spans** against each spec surface.
- §89 presents a **comparative analysis** — a single table with all tradeoffs side by side, followed by the prose-as-syntax stress test.
- §90 presents the **recommended hybrid** and its rationale.
- §91 catalogs **interactions with locked decisions** — every § that would change under each approach.
- §92 presents **test sentences** that any chosen approach must handle correctly.
- §93 enumerates **open design questions for the architect**.
- §94 is the resume prompt.

---

## §85 — WHAT D7 IS AND WHY IT NEEDS ITS OWN CHECKPOINT

The Inscript Programming Language's lexer splits input on whitespace (inception §22). Every token is a single word. User-provided string values are single words that are not in the vocabulary table and are not numbers (v1d §61). This means the language cannot express multi-word values like `in progress`, `high priority`, `Los Angeles`, `net 30`, `blood pressure`, or `interactive narrative`.

This limitation was logged during the v1 build (v1d §61), surfaced as gap D7 during v1 dogfooding (gap inventory, May 12, 2026), triaged as needing a dedicated checkpoint (v2 Design Triage §5), and explicitly deferred through v2a (§72) and v2b. The v1 hyphenation workaround (`in-progress`, `gap-inventory`, `find-large`) was adopted throughout dogfooding and remains valid.

**Why a dedicated checkpoint.** D7 touches more spec surfaces than any other v2-design item (Design Triage §5):

1. **Lexer** — the whitespace-splitting rule (inception §22, v1c §46) is foundational. Any multi-word mechanism either adds a new lexer state (quotes) or adds lookahead beyond one token (phrase spans) or changes nothing (hyphenation).
2. **Parser** — value positions currently expect single tokens. Multi-token values change the slot-filling shape (inception §17).
3. **Prose-as-syntax invariant** (v7.5g §13) — "valid inscriptions are readable as English prose." Does `"in progress"` count as prose? Does `in-progress`?
4. **Reserved-word list** (v1a §29, v1c §47, v2a §73) — multi-word phrases could collide with reserved phrases like `equal to`. A string value containing a reserved word (e.g., `"filter"`) inverts the v1c §46 exclusion rule.
5. **Domain packs** (§19 Mechanism 1) — each pack adds 10–15 terms. If a healthcare pack introduces `blood pressure` as a multi-word concept, the lexer needs to know about it.
6. **The `of` connective** (v2a §68, generalized in v2b §77) — `show "total amount" of order1` changes what constitutes a valid field reference.
7. **Canonical rendering** (v1a §33, extended in v2a §71) — how does the renderer emit multi-word strings? With quotes? Without?
8. **Round-trip property** — parsing the renderer's output must produce the same AST. Multi-word strings must survive the parse → render → re-parse cycle.

The v1 hyphenation workaround handles naming (compositions, variables, field names) well. It handles category values (`in-progress`, `high-priority`) acceptably. It does not handle data that arrives from external systems with spaces in it, nor does it handle prose-natural English like `remember a patient called pat1 with diagnosis as chest pain` — `chest-pain` is passable but degrades the prose quality that is the language's reason for existing.

---

## §86 — APPROACH A: QUOTING

The lexer gains a quote state. When it encounters an opening double-quote character (`"`), it accumulates all characters (including spaces) until the closing double-quote, producing a single `QUOTED_STRING` token. The token's value is the text between the quotes, with the quotes stripped.

### Lexer impact

The whitespace-splitting rule (inception §22) is *modified*, not replaced. Outside of quotes, whitespace splitting works exactly as before. Inside quotes, whitespace is preserved as part of the token value. This is a new lexer state — the lexer must track whether it is inside quotes.

**Unclosed quotes.** If a line ends without a closing quote, the lexer produces an error: *"I see an opening quote mark but no closing one on this line. Each quoted phrase needs both opening and closing marks."* Quotes do not span lines — this preserves the one-statement-per-line rule (inception §22, whitespace normalization).

**Escaped quotes.** v1/v2 does not support escape characters. A quoted string cannot contain a literal double-quote. This is acceptable for the v1/v2 target domains — business categories, healthcare terms, and compliance labels do not typically contain quote marks. If this limitation becomes real, backslash escaping (`\"`) could be added in a future version, but adding it now would introduce a second special character for a problem that doesn't exist yet.

**Decorative punctuation.** Commas, periods, question marks, and exclamation marks inside quotes are *preserved* — they are part of the string value, not decorative. Outside quotes, punctuation stripping (inception §22) continues unchanged. `remember a note called n1 with text as "Hello, world!"` stores `Hello, world!` — the comma and exclamation mark are data, not decoration.

### Parser impact

A `QUOTED_STRING` token is valid anywhere an `UNKNOWN` token is valid in a value position: after `with` (without `as`), after `as` in a `with...as` clause, after an operator in a `where` clause. The parser treats `QUOTED_STRING` exactly like `UNKNOWN` for slot-filling purposes, except that its value may contain spaces.

**Not valid in name positions.** Multi-word names are not supported — `remember a list called "my big list"` is a parse error. Names remain single tokens with letters, digits, and hyphens (inception §22). The error message: *"Names can't have spaces. Try a hyphenated name like 'my-big-list' instead."* This preserves the name-reference simplicity throughout the language — names are lookup keys, not display labels.

**Not valid in field-name positions in `with...as`.** `remember an order called o1 with "total amount" as 75` — whether this is valid depends on a design question (§93, Question M). If multi-word field names are allowed, the `of` connective and the `where` clause field-reference position must also accept `QUOTED_STRING` tokens. If they are not, fields remain single tokens and the constraint is clean.

### Prose-as-syntax impact

Quote marks are the first piece of "programming syntax" the language would introduce. Every other construct reads as English prose. `with status as "in progress"` reads as English with punctuation; `with status as in-progress` reads as slightly bent English; `with status as in progress` reads as natural English.

The impact is real but bounded. Quote marks appear in English prose — they delimit titles, special terms, and direct speech. A non-programmer encountering `remember an order with status as "in progress"` would understand it. They would not mistake the quotes for decoration (the way commas are decorative in the language), because quote marks in English enclose specific content.

The prose-as-syntax invariant (v7.5g §13) says "valid inscriptions are readable as English prose." A quoted phrase is readable as English prose with a quoted term — which is a thing English does. The invariant holds, with a softening: the language now contains one piece of syntax that is also a common English punctuation mark.

### Reserved-word interaction

Quoting *resolves* the v1c §46 conflict rather than creating one. Currently, `remember a list called items with filter and blue` fails because `filter` is a reserved VERB token. Under quoting, `remember a list called items with "filter" and blue` would succeed — the quotes explicitly mark `filter` as a string value, not a verb reference. The lexer produces a `QUOTED_STRING` token, which the parser treats as a value, bypassing vocabulary lookup entirely.

This is a question for the architect (§93, Question N): should quoting override reserved-word exclusion in value positions? The mechanical answer is yes — the quotes unambiguously mark the content as data. The philosophical answer is also yes — a compliance domain pack might need categories like `"filter"`, `"count"`, or `"combine"` as status labels.

### Domain-pack interaction

None. Quoting is self-delimiting — the lexer does not need to know the domain pack's vocabulary to identify quoted strings. A healthcare domain pack can introduce `"blood pressure"` and `"chest pain"` without any registry, collision detection, or phrase-boundary rules. This is the strongest advantage of quoting over phrase spans.

### Canonical rendering and round-trip

The renderer emits multi-word string values with quotes: `with status as "in progress"`. Single-word string values can be emitted without quotes: `with status as active`. Re-parsing the rendered output produces the same AST. The round-trip property holds.

**Design question (§93, Question O):** Should the renderer *always* quote string values, even single-word ones? `with status as "active"` is noisier but uniform. `with status as active` is cleaner but introduces a visual distinction between single-word and multi-word values that has no semantic meaning. The recommendation is to quote only multi-word values — the renderer is an aid to reading, and unnecessary quotes reduce readability.

### Case normalization

The lexer lowercases all input before vocabulary lookup (inception §22, v1d §57). Should quoted strings also be lowercased? `"In Progress"` and `"in progress"` — same or different?

The v1 answer was: all input is lowercased, case distinctions are lost. Extending this to quoted strings is consistent: `"In Progress"` becomes `"in progress"` at the lexer level. The alternative — preserving case inside quotes — would make quoted strings the first case-sensitive construct in the language, creating an inconsistency that users would discover painfully (`where status is "In Progress"` fails to match data stored as `"in progress"`).

**Recommendation:** lowercase inside quotes, consistent with the rest of the language. Case-sensitive strings are a future consideration alongside the broader type system (Q8 from the inception checkpoint).

### Cost summary

| Dimension | Cost |
|---|---|
| Lexer change | New state: inside-quote accumulation. Moderate complexity. |
| Parser change | Accept `QUOTED_STRING` in value positions. Small. |
| Prose-as-syntax | Softened — one syntactic mark enters the language. Bounded. |
| Reserved words | *Resolved* — quotes disambiguate data from vocabulary. |
| Domain packs | None — self-delimiting, no registry needed. |
| Round-trip | Clean — renderer emits quotes for multi-word values. |
| Implementation effort | Moderate — lexer state machine, one new token type. |

---

## §87 — APPROACH B: HYPHENATION CONVENTION

No language change. Multi-word concepts are written as hyphenated single tokens: `in-progress`, `chest-pain`, `high-priority`, `los-angeles`. This is already valid in v1/v2 — hyphens are valid name characters (inception §22). The "approach" is to formally bless hyphenation as the documented convention and close D7 without a language change.

### Lexer impact

None. Zero change to the lexer.

### Parser impact

None. Zero change to the parser.

### Prose-as-syntax impact

Mixed. `with status as in-progress` is readable English — hyphens are common in English compound adjectives (`well-known`, `self-employed`, `on-site`). But hyphens in noun phrases are less natural: `with city as los-angeles` and `with diagnosis as chest-pain` read as slightly awkward. For category labels (`active`, `pending`, `in-progress`, `high-priority`), hyphenation is comfortable. For proper nouns and medical terms, it degrades.

The prose-as-syntax invariant holds for category labels but weakens for data values that are multi-word noun phrases.

### Reserved-word interaction

No change. Hyphenated tokens are single tokens — `filter-status` is an UNKNOWN, not a VERB followed by an UNKNOWN. The reserved-word exclusion (v1c §46) does not apply to hyphenated tokens that happen to contain a reserved word as a substring.

However, this creates an undocumented escape hatch: `with label as not-applicable` succeeds because `not-applicable` is a single UNKNOWN token, while `with label as not` fails because `not` is a reserved OPERATOR token. The workaround is functional but the asymmetry is surprising.

### Domain-pack interaction

Each domain pack would document its hyphenated conventions: `blood-pressure`, `heart-rate`, `chest-pain` for healthcare; `net-30`, `accounts-receivable`, `high-priority` for business. The burden is on the pack author to choose hyphenated forms that pass the word salad test (§20). There is no collision mechanism to manage — hyphenated tokens are ordinary UNKNOWN tokens.

The risk: domain packs authored by different people might hyphenate the same concept differently (`chest-pain` vs `chest-pains`, `in-progress` vs `in-prog`). Without a registry, consistency is a documentation concern, not an enforcement concern.

### Canonical rendering and round-trip

No change. Hyphenated values are single tokens, rendered and parsed identically. The round-trip property holds trivially.

### Cost summary

| Dimension | Cost |
|---|---|
| Lexer change | None. |
| Parser change | None. |
| Prose-as-syntax | Varies — comfortable for categories, awkward for noun phrases. |
| Reserved words | No change (hyphenated tokens bypass the exclusion rule by accident). |
| Domain packs | Documentation burden, no enforcement mechanism. |
| Round-trip | Trivial. |
| Implementation effort | Zero. |

---

## §88 — APPROACH C: MULTI-WORD PHRASE SPANS

The lexer maintains a phrase registry — a set of known multi-word phrases. When the lexer encounters a token, it checks whether the token plus the next token(s) form a registered phrase. If so, the tokens are combined into a single token. If not, each token is emitted separately.

### Lexer impact

This is the most invasive change of the three approaches. The whitespace-splitting rule (inception §22) is *fundamentally altered* — the lexer no longer splits on whitespace unconditionally. It splits on whitespace, then *re-combines* tokens that match registered phrases.

**Phrase registry structure.** The registry is a set of multi-word strings: `{"in progress", "blood pressure", "chest pain", "high priority", ...}`. The lexer, after whitespace splitting, performs a greedy left-to-right scan: at each position, it checks whether the current token starts a registered phrase. If so, it consumes the required number of tokens and emits a single PHRASE token. If not, it emits the current token and advances.

**Greedy vs. longest-match.** If the registry contains both `blood` (as a standalone term) and `blood pressure`, the greedy scan must prefer the longer match. This is the standard longest-match rule from lexer theory, but it adds complexity — the lexer must look ahead by the maximum phrase length in the registry before committing to a token classification.

**Lookahead depth.** v1c §51 specifies that the parser uses one-token lookahead. Phrase spans move lookahead into the *lexer*, which currently uses zero lookahead (pure whitespace splitting). The maximum lookahead is the maximum phrase length in the registry. For domain packs with 2-word phrases, this is one extra token. For 3-word phrases (`net 30 days`?), it is two. The depth is bounded but variable per session.

### Parser impact

`PHRASE` tokens are treated like `UNKNOWN` tokens in value positions — the parser does not distinguish between a single-word value and a multi-word phrase. This is clean from the parser's perspective. The complexity is entirely in the lexer.

### Prose-as-syntax impact

Perfect. `with status as in progress` reads as natural English. `with diagnosis as chest pain` reads as natural English. This is the approach that best preserves the prose-as-syntax invariant.

### Reserved-word interaction

This is where phrase spans become dangerous. The lexer's vocabulary lookup (inception §22) tags words by category *before* phrase combination. If a phrase contains a reserved word, the lexer must decide whether to tag it as a reserved word or as part of a phrase.

**Collision scenario 1: `equal to` is a registered operator phrase.** If a domain pack registers `equal to` as a category label (unlikely but illustrative), the lexer cannot distinguish between the operator `equal to` and the data value `equal to`. The phrase registry collides with the reserved-word table.

**Collision scenario 2: `in progress` where `in` might become a future connective.** The inception checkpoint (§25) defers several connectives to v2. If `in` were added as a connective, the phrase `in progress` would start with a CONNECTIVE token, and the phrase registry would need to override vocabulary lookup — a precedence inversion.

**Collision scenario 3: `not applicable`.** `not` is a reserved OPERATOR token. `not applicable` as a phrase requires the lexer to suppress `not`'s operator classification when followed by `applicable` and the pair is in the registry. This is context-dependent vocabulary lookup — the most fundamental complexity of natural-language parsing.

**Mitigation:** Phrase registry entries could be required to contain no reserved words. This eliminates collisions but also eliminates many natural English phrases: `not applicable`, `to do`, `a priori`, `is pending`.

### Domain-pack interaction

Heavy. Each domain pack must register its multi-word phrases with the lexer. The lexer must reload its phrase registry when the active domain pack changes. Cross-pack collision detection is required: if the healthcare pack registers `blood pressure` and the cooking pack registers `blood orange`, and both packs are active, the lexer must handle `blood` followed by either `pressure` or `orange` without ambiguity — which it can (longest match handles this), but the *testing surface* grows combinatorially.

**"Known" is itself ambiguous.** The phrase registry defines which multi-word combinations the lexer recognizes. Anything not in the registry is split into separate tokens. This means the user must know what is registered and what is not. `in progress` works if registered; `in transit` fails silently (parsed as two tokens — `in` and `transit` — likely producing a confusing parse error) if not registered. The distinction between "this phrase works" and "this phrase doesn't" is invisible and depends on configuration, not on the language's rules.

### Canonical rendering and round-trip

The renderer must emit multi-word phrases without any delimiter (since the approach's soul is "no syntax marks"). `with status as in progress` renders as written. Re-parsing succeeds *only if the phrase registry is loaded*. Without the registry, re-parsing splits `in progress` into two tokens and fails. The round-trip property depends on runtime state (the active phrase registry), not just on the text — a new kind of fragility.

### Cost summary

| Dimension | Cost |
|---|---|
| Lexer change | Fundamental — phrase registry, greedy matching, variable lookahead. |
| Parser change | Small — PHRASE tokens treated as UNKNOWN. |
| Prose-as-syntax | Perfect — reads as natural English. |
| Reserved words | Collision risk. Mitigation (ban reserved words in phrases) limits utility. |
| Domain packs | Heavy — registry per pack, cross-pack collision detection, reload on activation. |
| Round-trip | **Fragile** — depends on runtime phrase registry state. |
| Implementation effort | High — lexer rewrite, registry infrastructure, collision detection. |

---

## §89 — COMPARATIVE ANALYSIS

### Side-by-side tradeoff table

| Dimension | A (Quoting) | B (Hyphenation) | C (Phrase Spans) |
|---|---|---|---|
| **Lexer complexity** | Moderate (new state) | None | High (registry, lookahead) |
| **Parser complexity** | Small | None | Small |
| **Prose-as-syntax** | Softened (one syntax mark) | Varies (categories OK, nouns awkward) | Perfect |
| **Reserved-word safety** | Resolves conflicts | Unchanged (accidental escape hatch) | Creates new conflicts |
| **Domain-pack cost** | None | Documentation only | Registry + collision detection |
| **Round-trip robustness** | Clean | Trivial | Fragile (registry-dependent) |
| **Generality** | Universal — any multi-word value | Limited — not all concepts hyphenate naturally | Limited to registered phrases |
| **User knowledge required** | Learn one rule: "use quotes for multi-word values" | Learn one convention: "hyphenate multi-word values" | Know which phrases are registered |
| **Implementation effort** | Moderate | Zero | High |
| **Future extensibility** | Clean — escape characters, interpolation could layer on top | Dead end — cannot grow beyond hyphenation | Complex — every new phrase must be registered |

### The prose-as-syntax stress test

The Design Triage §5 asked: "Does `"in progress"` count as prose? Does `in-progress`?" Let's test each approach against the word salad test (§20) — "any new construct must be understandable by a non-programmer in context without explanation."

**Test sentence:** `remember a patient called pat1 with diagnosis as chest pain and priority as high`

| Approach | What the user writes | Word-salad-test pass? |
|---|---|---|
| A (Quoting) | `remember a patient called pat1 with diagnosis as "chest pain" and priority as high` | Yes — a non-programmer reads the quotes as "the phrase chest pain." Natural English uses quotes this way. |
| B (Hyphenation) | `remember a patient called pat1 with diagnosis as chest-pain and priority as high` | Marginal — `chest-pain` is not standard English. A non-programmer would understand it but might wonder why the hyphen is there. |
| C (Phrase Spans) | `remember a patient called pat1 with diagnosis as chest pain and priority as high` | Yes — reads as natural English. But the non-programmer cannot tell where the value ends and the next clause begins without knowing the registry. In this case, does `and` separate `chest pain` from `priority`, or is `pain and priority` a three-word phrase? The parser knows (because `and` is a reserved connective), but the *reader* doesn't know the rules that make it work. |

**Test sentence 2:** `remember a task called t1 with status as not applicable`

| Approach | What the user writes | Word-salad-test pass? |
|---|---|---|
| A (Quoting) | `with status as "not applicable"` | Yes — quotes clearly delimit the phrase. `not` inside quotes is data, not an operator. |
| B (Hyphenation) | `with status as not-applicable` | Yes — the hyphen makes `not-applicable` a single token, bypassing `not`'s operator role. But a non-programmer might not know that `not applicable` (without hyphen) would fail. |
| C (Phrase Spans) | `with status as not applicable` | **Fails.** `not` is an OPERATOR token. The phrase registry would need to override vocabulary lookup. If `not applicable` is registered, the lexer must suppress `not`'s classification. If it is not registered, the lexer produces OPERATOR(`not`) + UNKNOWN(`applicable`), which is a parse error or — worse — a valid but semantically wrong expression (negation of a comparison against `applicable`). |

The phrase-spans approach fails the reserved-word stress test. The quoting approach handles it cleanly. The hyphenation approach handles it by convention.

### The domain-pack scaling test

Imagine a healthcare domain pack with 12 multi-word terms (`blood pressure`, `heart rate`, `chest pain`, `shortness of breath`, `range of motion`, `body mass index`, `white blood cell`, `red blood cell`, `blood oxygen level`, `blood sugar level`, `emergency room`, `intensive care`).

| Approach | What the pack author must do | What the user must know |
|---|---|---|
| A (Quoting) | Document the terms. No lexer configuration. | Wrap multi-word values in quotes. |
| B (Hyphenation) | Document the hyphenated forms. | Use the hyphenated forms (`blood-pressure`, `heart-rate`). |
| C (Phrase Spans) | Register all 12 phrases with the lexer. Handle `of` inside `shortness of breath` and `range of motion` (collision with the `of` connective, v2a §68). Handle `blood` appearing in four different phrases. Test all combinations against the base vocabulary and any other active domain packs. | Know which phrases are registered. Discover by trial and error when a phrase they expect to work isn't registered. |

Note the `of` collision: `shortness of breath` contains the reserved connective `of`. Under phrase spans, the lexer must suppress `of`'s connective classification inside this phrase. Under quoting, `"shortness of breath"` is unambiguous. Under hyphenation, `shortness-of-breath` is a single token.

---

## §90 — RECOMMENDATION: QUOTING AS UNIVERSAL MECHANISM, HYPHENATION BLESSED AS CONVENTION

**Recommended approach: Approach A (quoting) as the universal multi-word string mechanism, with Approach B (hyphenation) formally documented as the encouraged convention for simple cases. Approach C (phrase spans) is not recommended.**

The reasoning follows from three principles already locked in the spec:

**Principle 1 — deterministic interpretation (v1c §52).** The language must never silently misinterpret input. Phrase spans (Approach C) fail this principle when a multi-word value contains a reserved word and the phrase is not registered. Quoting makes the value boundary explicit. Determinism wins over naturalness.

**Principle 2 — vocabulary scaling through mechanisms external to the base vocabulary (inception §19).** Phrase spans require each domain pack to register phrases with the lexer — a scaling mechanism that couples domain vocabulary to the lexer's internal state. Quoting decouples the two: the lexer handles quotes universally, domain packs contribute no lexer configuration. The base mechanism stays small; the domain vocabulary stays external.

**Principle 3 — the clarity budget (inception §19, §20).** Adding one piece of syntax (quote marks) to the language costs clarity. But it costs *once* — the rule is "use quotes for multi-word values." Phrase spans cost clarity *per phrase* — the user must learn which phrases are registered. The per-phrase cost grows with domain packs; the per-rule cost does not.

**Why hyphenation is blessed, not replaced.** Hyphenation already works for names (`find-large`, `gap-inventory`), field names (`heart-rate`, `total-amount`), and simple category values (`in-progress`, `high-priority`). These are the 80% case. Quoting handles the 20% case that hyphenation cannot: proper nouns (`"Los Angeles"`), medical terms (`"chest pain"`), data imported from external systems (`"in progress"` matching a CRM's status field), and values containing reserved words (`"not applicable"`).

The two mechanisms coexist without conflict:
- `with status as in-progress` — valid, single token, no quotes needed.
- `with status as "in progress"` — valid, quoted multi-word string.
- `with status as "not applicable"` — valid, reserved word inside quotes is data.
- `with diagnosis as "chest pain"` — valid, multi-word noun phrase.

**No overlap ambiguity.** `with status as "in-progress"` (a hyphenated word inside quotes) produces the value `in-progress` — the same value as without quotes. Quoting a single-word value is redundant but not an error. The renderer emits without quotes when the value is single-token, with quotes when multi-word. This is a rendering choice, not a semantic distinction.

### What is NOT recommended

**Approach C (phrase spans) is not recommended for v2.** The reserved-word collision risk, the registry-dependent round-trip fragility, and the per-domain-pack configuration cost are all too high. Phrase spans might be revisited in a future version where the language has a richer type system and a more sophisticated lexer, but that version would need to solve the collision problem first — and quoting solves it today.

**Mandatory quoting for all strings is not recommended.** Requiring `with status as "active"` when `with status as active` already works would add visual noise to every program for no semantic benefit. The recommendation is that quotes are required only for multi-word values — single-word values remain bare UNKNOWN tokens.

---

## §91 — INTERACTIONS WITH LOCKED DECISIONS

If the architect adopts the recommended approach (quoting + hyphenation blessed), these locked sections are affected:

| Section | Current state | Change under quoting |
|---|---|---|
| **Inception §22 (lexer spec)** | Whitespace splitting, no special characters besides colon. | Add: quote-state accumulation. Whitespace splitting unchanged outside quotes. |
| **v1c §46 (vocabulary words cannot be string values)** | Reserved words are always tagged by vocabulary category. | Add: `QUOTED_STRING` tokens bypass vocabulary lookup. A quoted reserved word is data. |
| **v1d §61 (single-token strings)** | Multi-word strings not supported. | **Superseded** — multi-word strings supported via quoting. Single-word bare strings unchanged. |
| **v2a §72 (D7 deferral)** | Deferred to a dedicated checkpoint. | **Resolved** — this checkpoint is that checkpoint. |
| **v1a §33 / v2a §71 (canonical rendering)** | Renderer emits single-word values without delimiters. | Add: renderer emits multi-word values with quotes. Single-word values remain unquoted. |
| **v2a §68 / v2b §77 (`of` connective)** | Field references are single UNKNOWN tokens. | **Design question (§93 Q-M)**: do quoted strings in field-reference position work? `show "total amount" of order1`? |
| **v2a §69 (fifth `and` rule, multi-field show)** | Field names in `each ... show X and Y` are UNKNOWN tokens. | **Design question (§93 Q-M)**: can `each the orders show "total amount" and status` work? |
| **Inception §22 (decorative punctuation stripping)** | Commas, periods, question marks, exclamation marks stripped. | Add: inside quotes, punctuation is preserved (it's data). |
| **v1d §57 (case normalization)** | All input lowercased. | Quoted strings also lowercased (recommended; see §86). |

No locked *decision* is reversed. v1d §61 is superseded (its constraint is relaxed), not contradicted (single-word bare strings still work exactly as before). All other changes are additive — they extend existing rules to cover the new token type.

---

## §92 — TEST SENTENCES FOR D7

Any approach the architect adopts must handle these sentences correctly. They are written for the recommended approach (quoting) but the test semantics apply to any approach.

**Sentence 69 — Basic multi-word string value**
```
remember an order called o1 with status as "in progress"
show o1
```
→ `status: in progress`
**Tests:** Quoted multi-word value stored correctly. Display omits quotes (values are data, quotes are syntax).

**Sentence 70 — Multi-word string in a where clause**
```
remember an order called o1 with status as "in progress"
remember an order called o2 with status as shipped
remember a list called orders with o1 and o2
keep the orders where status is "in progress"
```
→ Auto-shows: `status: in progress` (one match)
**Tests:** String equality comparison works with quoted multi-word values.

**Sentence 71 — Reserved word inside quotes**
```
remember a category called c1 with label as "not applicable"
show label of c1
```
→ `not applicable`
**Tests:** `not` inside quotes is data, not an operator. v1c §46 exclusion bypassed by quoting.

**Sentence 72 — Mixed single-word and multi-word values**
```
remember a task called t1 with status as "in progress" and priority as high
show t1
```
→ `status: in progress, priority: high`
**Tests:** Multi-word and single-word values coexist in the same record. `and` correctly separates the `status` field (with quoted value) from the `priority` field (with bare value).

**Sentence 73 — Quoted value in `of` expression (if Q-M allows it)**
```
remember a metric called m1 with "blood pressure" as 120
show "blood pressure" of m1
```
→ `120`
**Tests:** Quoted string as a field name in `of` expression. (This sentence is conditional on Question M — if multi-word field names are disallowed, this sentence becomes an error test.)

**Sentence 74 — Quoted value does not affect hyphenated values**
```
remember a task called t1 with status as in-progress
remember a task called t2 with status as "in progress"
show status of t1
show status of t2
```
→ Line 3: `in-progress`
→ Line 4: `in progress`
**Tests:** Hyphenated value `in-progress` and quoted value `"in progress"` are *different strings*. They are stored as entered (after lowercasing). This is correct — they are different data, and the user chose to write them differently.

**Sentence 75 — Unclosed quote error**
```
remember a note called n1 with text as "hello world
```
→ Error: *"I see an opening quote mark but no closing one on this line. Each quoted phrase needs both opening and closing marks."*
**Tests:** Unclosed quotes produce a clear error.

**Sentence 76 — Empty quotes**
```
remember a note called n1 with text as ""
```
→ Error: *"There's nothing between these quote marks. If you want to store a value, put it between the quotes."*
**Tests:** Empty quoted strings are rejected. (Design question: should they be? See §93 Q-R.)

**Sentence 77 — Quoted single word (redundant but not an error)**
```
remember a task called t1 with status as "active"
remember a task called t2 with status as active
show status of t1
show status of t2
```
→ Line 3: `active`
→ Line 4: `active`
**Tests:** Quoting a single word is redundant but valid. The stored value is the same whether quoted or not. The renderer emits both without quotes (both are single-word values after the quotes are stripped).

---

## §93 — OPEN DESIGN QUESTIONS FOR THE ARCHITECT

These need a decision before implementation. They are independent of the approach choice (the approach itself is Question L) — all but L apply only if quoting is adopted.

| Q | Question | My recommendation | Cost of getting it wrong |
|---|---|---|---|
| **L** | **D7 approach.** Quoting, hyphenation only, or phrase spans? | **Quoting + hyphenation blessed** (§90). | If wrong: the lexer changes in a way that creates collision risks (phrase spans), or the language cannot express multi-word data from external systems (hyphenation only). |
| **M** | **Multi-word field names.** Should `with "total amount" as 75` and `show "total amount" of order1` be valid? | **No — field names remain single tokens (hyphenation for multi-word fields).** Allowing multi-word field names means every field-reference position in the parser (`where`, `of`, multi-field `show`) must accept `QUOTED_STRING`, and the `and` disambiguation in `each ... show` becomes harder: is `"total amount" and status` two fields or a three-word quoted phrase that hasn't been closed? Single-token field names keep the parser simple. | If wrong: the parser's field-reference positions become more complex, and the fifth `and` rule (§69) may need re-examination. |
| **N** | **Quoted reserved words as values.** Should `with label as "filter"` succeed? | **Yes.** Quotes explicitly mark the content as data. This is the whole point of having a quoting mechanism — it disambiguates data from syntax. If the user needs a category called `"filter"`, they should be able to express it. | If wrong: the v1c §46 exclusion rule gains an exception that feels arbitrary ("quotes work for multi-word values but not for single reserved words"), or users cannot express domain data that happens to collide with the vocabulary. |
| **O** | **Renderer quoting policy.** Should the renderer always quote string values, or only multi-word ones? | **Only multi-word.** `with status as active` is cleaner than `with status as "active"`. The renderer is an aid to reading. | If wrong: every program gains visual noise from unnecessary quotes on single-word values. |
| **P** | **Case normalization inside quotes.** Should `"In Progress"` be lowercased to `"in progress"`? | **Yes — consistent with the rest of the language.** Case-sensitive strings are a future type-system concern (Q8). | If wrong: users discover case sensitivity only inside quotes, creating a trap. |
| **Q** | **Quoted strings in composition names.** Should `remember how to "find big orders": ...` be valid? | **No — composition names are single tokens (hyphenated for multi-word).** Same rationale as Question M: names are lookup keys, not display labels. The parser expects a single token after `how to`. | If wrong: composition-call parsing must handle multi-word names, which changes how the parser identifies the colon delimiter. |
| **R** | **Empty quotes.** Should `""` be valid? | **No — reject with a clear error.** An empty string is not a meaningful value in the language's target domains. If a future version adds string operations (concatenation, interpolation), empty strings might become meaningful, but that version would also add a richer type system. For now, empty quotes are a typo. | If wrong: the symbol table gains empty-string entries that produce confusing behavior in comparisons (`where status is ""` — comparing against nothing). |

---

## §94 — RESUME PROMPT (Inscript Programming Language v2c — D7 Multi-Word Strings)

*We are resuming from the Inscript Programming Language Multi-Word Strings Checkpoint v2c (May 12, 2026), which is the dedicated D7 checkpoint deferred through v2a §72 and confirmed in v2b. **This checkpoint does not lock any decision — it presents analysis and recommendations for the architect.** Three approaches were evaluated: (A) quoting, (B) hyphenation convention, (C) multi-word phrase spans. Approach C was not recommended — reserved-word collisions, registry-dependent round-trip fragility, and per-domain-pack configuration cost are too high. **The recommendation is Approach A (quoting) as the universal multi-word string mechanism, with Approach B (hyphenation) formally blessed as the encouraged convention for simple cases.** Quote marks in value positions are the first (and only) piece of "programming syntax" in the language — the prose-as-syntax invariant holds with a bounded softening. Quoting resolves (not creates) reserved-word conflicts: `"filter"` as a data value is unambiguous. Domain packs require no lexer configuration. The round-trip property is clean. **Seven open design questions (L–R in §93)** need the architect's decisions: L is the approach choice itself; M–R are sub-decisions within the quoting approach (multi-word field names, quoted reserved words, renderer policy, case normalization, composition names, empty quotes). The recommendations for M–R are: field names stay single-token (M), quoted reserved words work (N), renderer quotes only multi-word values (O), case normalized inside quotes (P), composition names stay single-token (Q), empty quotes rejected (R). **Nine test sentences (69–77)** in §92 must pass under any chosen approach. **External review (Gemini + ChatGPT) is recommended before locking**, matching the pattern used for v1a–v1d. The next step after architect decisions and external review is a v2c addendum that locks the chosen approach and its sub-decisions, extends the build boundary, and updates the vocabulary/lexer specification.*

---

## PROVENANCE NOTE

This checkpoint was produced from:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - §10 (concept-layer vocabulary) — the language names what people do, not how machines work. Quoting names what the user is doing ("this phrase is data") without machine-facing syntax.
  - §17 (verb signatures, slot filling) — value positions referenced throughout for where `QUOTED_STRING` tokens would be valid.
  - §19 (vocabulary scaling, domain packs) — the domain-pack scaling test in §89 is driven by §19 Mechanism 1.
  - §20 (word salad test) — the prose-as-syntax stress test in §89 applies the word salad test to all three approaches.
  - §22 (lexer specification) — whitespace splitting, case normalization, decorative punctuation, valid name characters, multi-word `equal to` — all referenced in §86/§87/§88 as the surfaces that D7 touches.
  - §25 (v1/v2 deferral table) — Q8 (type system) referenced for case-sensitivity deferral.
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - §29 (reserved word list, exclusion rule) — referenced in §86 (quoting resolves conflicts), §87 (hyphenation bypasses by accident), §88 (phrase spans create conflicts).
  - §33 (canonical prose rendering) — referenced in §91 (rendering of quoted multi-word values).
- **`inscript_addendum_v1b_design_resolutions.md`** (May 11, 2026):
  - §41 (composition call syntax) — referenced in §93 Q-Q (composition names stay single-token).
  - §43 (`from` disambiguation) — referenced for the parser path where `QUOTED_STRING` values would appear.
  - §44 (complete disambiguation ruleset) — extended by D7 if multi-word field names are allowed (§93 Q-M).
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026):
  - §46 (vocabulary words cannot be string values) — directly addressed: quoting provides a mechanism to use vocabulary words as data values.
  - §50 (five-outcome taxonomy) — new errors from D7 (unclosed quotes, empty quotes) map to Outcome 4 (parse error).
  - §51 (parser lookahead) — phrase spans (§88) would move lookahead into the lexer.
  - §52 (deterministic interpretation only) — invoked in §90 as the deciding principle against phrase spans.
- **`inscript_addendum_v1d_build_boundary.md`** (May 11, 2026):
  - §57 (case normalization) — referenced in §86 for the case-inside-quotes question.
  - §61 (single-token strings) — the constraint that D7 supersedes.
- **`inscript_addendum_v2a_dogfooding_resolutions.md`** (May 12, 2026):
  - §67 (`keep` verb) — `keep` with quoted values in `where` clauses (test sentence 70).
  - §68 (`of` connective) — interaction with quoted field names (§93 Q-M).
  - §69 (fifth `and` rule) — interaction with quoted field names in multi-field show.
  - §71 (descriptor preservation) — canonical rendering extension.
  - §72 (D7 deferral) — the deferral this checkpoint resolves.
  - §73 (vocabulary table) — no vocabulary changes from D7.
- **`inscript_addendum_v2b_composition_returns.md`** (May 12, 2026):
  - §77 (generalized `of`) — `show "total amount" of order1` interaction (§93 Q-M).
  - §84 (build boundary) — D7's implementation would extend this.
- **`inscript_v2_design_triage_2026_05_12.md`** (May 12, 2026):
  - §5 (D7 deserves its own checkpoint) — this is that checkpoint.
  - §7 Q-E (D7 approach) — deferred to dedicated checkpoint; now addressed.
- **`inscript_gap_inventory_2026_05_12_v1_dogfooding.md`** (May 12, 2026):
  - D7 (single-token strings preclude domain-natural language) — the gap this checkpoint addresses.
  - U6 (no multi-word headings/labels) — partially resolved by quoting: `show "section A"` would work.
- **`mobius_paradigm_checkpoint_v7_5g_inscript_resolution.md`**: §13 (prose-as-syntax invariant) — the principle that quoting softens but does not violate.
- **External review:** Not yet solicited. Recommended before locking (§94).
- **Filename:** `inscript_checkpoint_v2c_multi_word_strings.md` — domain `inscript` (provisional, pre-vault), class `checkpoint`, version `v2c` (third in the v2 series, following v2a/v2b addenda), subtitle `multi_word_strings`.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE MULTI-WORD STRINGS CHECKPOINT v2c*

*May 12, 2026*

*The language that reads as English prose now needs to hold data that has spaces in it.*
*Quoting is one syntax mark — the first the language has ever needed.*
*It costs one rule to learn: "wrap multi-word values in quotes."*
*It resolves the reserved-word collision that v1c §46 created.*
*It scales to every domain pack without a single line of registry configuration.*
*The clarity budget absorbs the cost because the cost is bounded and the benefit is universal.*
