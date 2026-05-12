# ADDENDUM
## Inscript Programming Language — Implementation Hardening
### v1c — Closing Specification Gaps Before First Code

**Status:** LOCKED — EXTENDS `inscript_addendum_v1b_design_resolutions.md`
**Date:** May 11, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Addendum — closes implementation-level specification gaps identified by final external review; no new vocabulary, no pipeline changes, no new deferrals
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v1b_design_resolutions.md` (May 11, 2026), which extends `inscript_addendum_v1a_pre_build.md` (May 11, 2026), which extends `inscript_inception_checkpoint_v1.md` (May 11, 2026). Continues from §45 (Build Specification Complete). A final external review (Gemini, May 11, 2026) of all four documents (inception checkpoint, v1a, v1b, thirty sentences) identified five findings. All five require documentation — some close genuine gaps, others make implicit behaviors explicit so the builder cannot invent undocumented behavior. Two additional gaps discovered during verification: the article `an` is used in checkpoint examples but absent from the vocabulary table, and blank line handling is unspecified. All seven items are resolved here.

---

## HOW TO READ THIS DOCUMENT

- §46–§54 continue the section numbering from v1b.
- This addendum does not change any prior locked decisions. It adds specification where prior documents were silent.
- After this addendum, the build specification is four documents plus the test suite. No further pre-build specification is planned.

---

### §46 — VOCABULARY WORDS CANNOT APPEAR AS STRING VALUES

**Decision: A vocabulary word (any word the lexer tags as VERB, CONNECTIVE, OPERATOR, or ARTICLE) cannot appear in a position where the parser expects an UNKNOWN token — specifically, in value positions (after `with` without `as`, after an operator in a `where` clause) or field reference positions (before an operator in a `where` clause). The parser produces a specific error. LOCKED as parser token-type enforcement rule.**

The gap: v1a §29 locks reserved word enforcement for NAME positions (after `called`, as field names in `with...as` clauses, as composition names after `how to`). But §29 does not address what happens when a vocabulary word appears in a VALUE position.

The scenario: `remember a list called items with filter and blue`. The lexer tags `filter` as VERB. The parser, in a `with` clause (§22 line 438: "After `with` (without `as`) → value"), expects UNKNOWN or NUMBER tokens. It receives a VERB token. The parser classification rules (§22 line 438, §21 line 407) all specify expected token types of UNKNOWN or NUMBER — they do not account for receiving vocabulary-tagged tokens.

The behavior in all cases: any vocabulary-tagged token (VERB, CONNECTIVE, OPERATOR, ARTICLE) appearing where the parser expects UNKNOWN or NUMBER is a parse error. The parser cannot reclassify a vocabulary word as a string value because the lexer's vocabulary lookup is authoritative — if the lexer says it's a VERB, it's a VERB.

This is a structural consequence of unquoted prose literals. The language has no quoting mechanism to distinguish `filter` (the verb) from `filter` (a string value the user wants to store). This is a v1 limitation:

- v1 has 28 reserved words (v1a §29) plus `an` (see §47 below) = 29 words that cannot be used as names OR as string values.
- For the v1 target domains (business rules, compliance, data filtering), this collision space is negligible — 29 words out of the entire English language.
- A quoting or escaping mechanism is a v2 consideration.

Error message for value positions: "The word '[word]' is a [category] in Inscript and can't be used as a value. Try a different word."

This extends v1a §29's error message for name positions ("Please choose a different name") to cover value positions with an appropriate variant.

**Typo handling:** When the parser finds no verb in a statement (Step 1 fails, composition fallback in v1b §41 also fails), the error message should indicate what was found and what was expected. For v1, the error message is: "I don't recognize a command here. Every sentence needs a verb like 'remember', 'show', 'filter', 'count', 'gather', 'combine', or 'each'." This lists the available verbs so the user can identify their typo. Levenshtein distance matching ("Did you mean 'remember'?") is a quality-of-life enhancement for a future version — v1 lists the available verbs instead. The bounded vocabulary (seven verbs) makes this practical; a language with 500 keywords could not list them all.

---

### §47 — ARTICLE `an` AND RESERVED WORD COUNT CORRECTION

**Decision: `an` is recognized as an article, equivalent to `a`. The lexer tags `an` as ARTICLE. `an` is added to the reserved word list. LOCKED as vocabulary correction.**

The inception checkpoint §11 (line 178) lists articles as `the` and `a`. However, the inception checkpoint's own examples use `an` throughout:
- §11 (line 185): `remember an order with total as 75 and status as active`
- §23 (line 448): `remember an order called order1 with total as 75 and status as active`
- WHAT IS LOCKED (line 578): `remember an order with total as 75 and status as active`

The thirty sentences use `an` in sentences 6, 7, and 8. The word `an` is the standard English variant of `a` before vowel sounds. The prose-as-syntax invariant (v7.5g §13: "valid inscriptions are readable as English prose") requires accepting natural English phrasing. Rejecting `an` while accepting `a` would force unnatural prose (`remember a order` instead of `remember an order`).

**Corrected article set:** `the`, `a`, `an` (three articles, not two).

**Corrected reserved word count:** 28 (v1a §29) + 1 (`an`) = **29 reserved words**.

Updated reserved word table (supersedes v1a §29 table):

| Source | Words | Count |
|---|---|---|
| v1 verbs (§11) | `remember`, `show`, `filter`, `count`, `gather`, `combine`, `each` | 7 |
| v1 connectives (§11) | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as` | 9 |
| v1 operators (§11) | `is`, `above`, `below`, `not` | 4 |
| v1 multi-word component (§22) | `equal` | 1 |
| v1 articles (§11 + this correction) | `the`, `a`, `an` | 3 |
| v2 deferred verbs (§11, §21) | `transform`, `choose`, `compare` | 3 |
| v2 deferred connectives (§11) | `when`, `unless` | 2 |
| **Total** | | **29** |

---

### §48 — BLANK LINE AND EMPTY STATEMENT HANDLING

**Decision: Blank lines are skipped by the lexer. A line containing only whitespace produces zero tokens and is not passed to the parser. LOCKED as lexer rule.**

The inception checkpoint §22 (line 432) specifies: "Each newline boundary is a statement separator — one sentence per line." It does not specify what happens with blank lines (consecutive newlines with no content, or lines containing only whitespace).

For v1: blank lines are silently skipped. They serve as visual separators between groups of statements (analogous to paragraph breaks in prose) but carry no semantic meaning. The lexer, after normalizing whitespace and stripping punctuation, checks whether a line produces any tokens. If it produces zero tokens, it advances to the next line without invoking the parser.

This behavior is consistent with the inception checkpoint's examples in §11 (lines 200–210), which show programs with blank lines between statement groups:

```
remember a list called groceries with milk and eggs and bread
show groceries
gather the numbers from 1 to 100
filter the numbers where each is above 50
```

The blank line between `show groceries` and `gather the numbers` is visual, not structural.

**Comment syntax:** v1 has no comment syntax. There is no mechanism to include non-executable text within a program file. Comments are a v2 consideration. In v1, every non-blank line is a statement.

---

### §49 — ITERATOR CONTEXT FOR `each`

**Decision: The interpreter maintains a temporary iterator context, separate from the symbol table, during `each` execution. The iterator context binds the current item for field resolution within the loop body. The context is created when `each` begins iteration and discarded when `each` completes. LOCKED as `each` interpreter mechanism.**

No prior document specifies the mechanism by which the interpreter tracks the "current item" during `each` execution. The inception checkpoint specifies that `each` wraps sub-operations via recursive descent (§21 line 500) and produces output if its sub-operation does (§24 line 476), but the runtime binding is unspecified.

**The mechanism:**

When the interpreter executes `each the orders show total`:

1. It reads `orders` from the symbol table (a list of records).
2. For each item in `orders`, it creates an **iterator context** — a temporary binding that holds the current record.
3. During execution of the sub-operation (`show total`), the interpreter resolves field references (like `total`) against the iterator context first, then falls back to the symbol table.
4. After the sub-operation completes for one item, the iterator context advances to the next item.
5. After the last item, the iterator context is discarded. No trace of it remains in the symbol table or elsewhere.

**The iterator context is NOT a symbol table entry.** It is a separate, temporary mechanism. The symbol table tracks named values created by `remember` and `gather`. The iterator context tracks the current item during `each` loops. These are distinct data structures.

**Field resolution order during `each`:** Iterator context → symbol table. If `total` exists as both a field on the current record AND as a global variable in the symbol table, the iterator context wins. This is the only scope-like behavior in v1 — it is not general scope isolation, it is a single-purpose resolution for `each` loop bodies.

**After the loop:** The iterator context is gone. `total` resolves against the symbol table only. There is no "ghost data" — no stale references, no leaked bindings.

**Flat lists vs. records:** For flat lists (lists of numbers or strings), the iterator context holds a scalar value, not a record. `each the numbers show` — the current item is a number. `show` with no field name displays the current item directly. For lists of records, the current item is a record, and field names resolve against it.

**The `each` pronoun (v1b §37) and the iterator context are related but distinct.** The pronoun resolves at parse time: inside a `where` clause, `each` means "the current item being tested." The iterator context resolves at execution time: during `each` loop execution, the current item is bound for field resolution. The pronoun tells the parser what the sentence means; the iterator context tells the interpreter what data to access.

**Named compositions called from within `each`:** For v1, named composition calls within an `each` loop body do NOT inherit the iterator context. If `each the orders show-details` calls a composition `show-details` whose body is `show total`, the `total` reference resolves against the global symbol table, not the current order. The iterator context is available only to the direct sub-operation of `each`, not to compositions called from that sub-operation. This keeps v1 scope semantics simple. Iterator context inheritance through composition calls is a v2 consideration alongside composition parameters (Q9) and general scope isolation.

---

### §50 — v1 TEXT INTERPRETER OUTPUT TAXONOMY

**Decision: The v1 text interpreter produces exactly five possible outcomes for each statement. LOCKED as v1 interpreter output taxonomy.**

The locked documents specify various error and warning behaviors across multiple sections. This taxonomy collects them in one place and makes the categories explicit so the builder cannot invent new categories or misclassify outcomes.

**Outcome 1 — Success.** All required slots filled. No ambiguity. The parser produces a complete AST. The canonical prose rendering (v1a §33) is displayed: "I understand this as: [canonical prose]." The interpreter executes. If the statement produces output (auto-show per §24, explicit `show`, or `each` with output-producing sub-operation), the output is displayed.

**Outcome 2 — Amber: precedence confirmation.** Parse succeeds, but a `where` clause contains mixed `and`/`or` (v1a §30). The canonical prose rendering is displayed with the parser's precedence interpretation in parenthesized grouping: "I'll read this as: (A AND B) OR C. Is that what you mean? If not, split it into two statements." The user confirms → interpreter executes. The user declines → no execution, statement is returned for editing.

**Outcome 3 — Amber: reorderer ambiguity.** The reorderer (§17) finds that the input words could fill slots in more than one valid way. The reorderer does not guess (§17 line 329). Instead it describes the ambiguity: "I'm not sure if you mean X or Y — can you clarify?" No execution until the user clarifies. This arises when structural connectives (`called`, `with`, `where`) are omitted and the parser cannot deterministically assign UNKNOWN tokens to slots.

**Outcome 4 — Error: parse failure.** The parser cannot build a complete AST. Causes include: no verb found and no named composition match (v1b §41 fallback fails); required slot unfilled after all tokens processed; vocabulary word in a name position (v1a §29: reserved word error); vocabulary word in a value position (§46: token-type enforcement error); unexpected token type in any position. The error message describes what's wrong in plain English (Q6 design principle from §9 line 134: errors say what's missing, not what token was unexpected). No execution.

**Outcome 5 — Error: semantic failure.** The parser succeeds (AST is complete), but the semantic analyzer finds a problem. Causes include: name not found in symbol table ("I can't find 'orders' — you might need to 'remember' it first," per §23 line 468); field not found on record ("'orders' doesn't have a field called 'total'"); type mismatch ("`above` requires numbers, but 'hello' is text," per §23 line 460); `combine` applied to non-numeric list (v1b §38: "I can only combine numbers"). No execution.

**There are no other outcomes.** Every statement the interpreter processes results in exactly one of these five. The builder should not add "warning" or "info" or "suggestion" categories. Amber is not a warning — it is a pause-and-confirm step that gates execution. Error is not a suggestion — it is a halt with an explanation. Success is not qualified — the interpreter either executes or it doesn't.

**Complexity cap (§19 Mechanism 4):** The complexity cap ("This is getting complex — would you like to name part of it?") is an Amber-class outcome in the tile interface (Branch C), where it fires during composition. In the v1 text interpreter, the complexity cap fires as a post-parse suggestion: the statement executes successfully, but the interpreter notes that the sentence exceeds the complexity threshold and suggests decomposition. This is NOT an Amber pause — it does not gate execution. It is a post-execution suggestion. This distinction matters: in text input, the user has already committed the sentence; blocking execution after a successful parse would be punitive. In tile composition, the user is still composing; the amber guides them before they commit. For v1 text input, the complexity cap is informational only.

---

### §51 — PARSER LOOKAHEAD AS EXPLICIT CAPABILITY

**Decision: The parser processes the token list using a traversal mechanism that supports non-consuming lookahead and clause-context tracking. LOCKED as parser capability requirement.**

The locked documents use the word "lookahead" in multiple contexts:
- §22 (line 426): `equal to` multi-word token via "one-word lookahead" in the lexer
- §21 (line 403): `and`/`or` disambiguation via "parser state + lookahead"
- §21 (line 414): `is` dual role via "lookahead"
- v1b §43: `from` disambiguation via "active verb + next-token lookahead"

None of these specify HOW lookahead is performed. The mechanism must support:

1. **Peeking ahead** — inspecting the next token (or next N tokens) without consuming them. Every disambiguation rule in v1b §44 requires checking what comes next before deciding how to classify the current token. The parser must be able to look ahead and then return to the current position.

2. **Consuming** — advancing past a token once its role is determined. After the parser decides that `is` is a comparison introducer (because the next token is `above`), it consumes `is` and moves to `above`.

3. **Clause-context tracking** — maintaining parser state that records which clause the parser is currently inside (`with` clause, `where` clause, `with...as` clause, top-level). Seven disambiguation rules (v1b §44) depend on parser state. The parser must track this as it descends into clause structures and untrack it as it exits.

The implementation pattern (a token stream with `peek`, `consume`, and a state stack for clause context) is the mechanism that makes the seven disambiguation rules in v1b §44 executable. Without it, the parser cannot perform the stateful disambiguation that the locked rules require.

---

### §52 — DETERMINISTIC INTERPRETATION ONLY

**Decision: The interpreter operates exclusively on what the user stated. It does not infer, assume, guess, or fill in unstated information. LOCKED as interpreter invariant.**

This principle is structurally present in the locked documents but never stated as an explicit constraint:
- §17 (line 329): "the reorderer does not guess"
- §17 (line 306): slot filling matches words to slots "by category" — a mechanical process, not an inferential one
- v1a §33: canonical prose rendering shows what the parser understood — verification, not approximation
- §9 (line 134): error messages describe what's missing, implying the system halts rather than guessing

Making this explicit as a build constraint:

1. **No data source inference.** If a verb requires a target and no target is provided, the interpreter produces an error. It does not guess that `filter where total is above 50` means `filter the orders where total is above 50` because `orders` is the only list in the symbol table. The user must name their target.

2. **No field inference.** If a `where` clause references a field that doesn't exist on the target, the interpreter produces a semantic error. It does not search other records for a matching field name or suggest alternatives.

3. **No type coercion.** If `above` requires numbers and receives a string, the interpreter produces a type error. It does not attempt to parse the string as a number (e.g., treating the string `"50"` as the number `50`). Types are what the type inference system (§23) determined them to be.

4. **No implicit operations.** The interpreter does not perform operations the user did not request. `show orders` displays the orders; it does not sort them, format them, or filter out duplicates. `filter` applies exactly the stated condition; it does not apply "common sense" additional filters.

5. **No predictive execution.** The interpreter does not anticipate what the user might want next. It processes the current statement and stops. The proposal engine (§9 line 138, Branch E) is a separate system that operates before the user writes, not during execution.

This constraint distinguishes Inscript from AI coding assistants. A copilot might infer unstated intent. Inscript does not. The prose IS the program. If the prose doesn't say it, it doesn't happen. This is what makes the language deterministic and trustworthy — the user can read the program and know exactly what it will do, because it will do exactly and only what it says.

---

### §53 — ADDITIONAL TEST SENTENCES

The following test sentences are added to the thirty sentences test specification. They cover the gaps identified in this addendum.

**Sentence 32 — Vocabulary word in value position**
```
remember a list called items with filter and blue
```
⚠ Error: "The word 'filter' is a verb in Inscript and can't be used as a value. Try a different word."
**Tests:** §46 — vocabulary word (VERB token) in a value position (after `with`). Distinct from sentence 31 (reserved word in NAME position after `called`). The lexer tags `filter` as VERB. The parser, in a `with` clause expecting UNKNOWN or NUMBER tokens, encounters a VERB token and produces the value-position error.

**Sentence 33 — Article `an`**
```
remember an item called widget with 25
```
⊕ Symbol table: `widget` = 25 (number). No output.
**Tests:** §47 — `an` recognized as an article, equivalent to `a`. The lexer tags `an` as ARTICLE. The parser treats it identically to `a`.

**Sentence 34 — No-verb error**
```
orders total above 50
```
⚠ Error: "I don't recognize a command here. Every sentence needs a verb like 'remember', 'show', 'filter', 'count', 'gather', 'combine', or 'each'."
**Tests:** §46 typo handling — when no verb is found and no named composition matches, the error message lists available verbs. Covers the typo scenario (user meant `filter` but omitted or misspelled it).

---

## WHAT IS LOCKED

This addendum locks:

- **Vocabulary words cannot be string values.** The lexer's vocabulary tagging is authoritative. A vocabulary-tagged token in a value or field-reference position is a parse error with a specific error message. No quoting mechanism in v1. 29 words cannot be used as names or values. (§46)
- **Article `an` recognized.** `an` is an article equivalent to `a`. Added to vocabulary and reserved word list. Reserved word count corrected to 29. (§47)
- **Blank lines are skipped.** Lines producing zero tokens are silently skipped. No comment syntax in v1. (§48)
- **Iterator context for `each`.** Temporary binding separate from symbol table. Created at loop start, discarded at loop end. Field resolution order: iterator context → symbol table. Flat lists bind a scalar; record lists bind a record. Compositions called from `each` do NOT inherit the iterator context. (§49)
- **Output taxonomy.** Five outcomes: Success, Amber (precedence confirmation), Amber (reorderer ambiguity), Error (parse failure), Error (semantic failure). Complexity cap is informational in v1 text interpreter, not a gating amber. No other outcome categories. (§50)
- **Parser lookahead capability.** Non-consuming peek, consuming advance, clause-context state tracking. Enables all seven disambiguation rules in v1b §44. (§51)
- **Deterministic interpretation only.** No inference, no assumption, no guessing, no type coercion, no implicit operations, no predictive execution. The prose IS the program. (§52)
- **Three additional test sentences.** Vocabulary word in value position, article `an`, and no-verb error. (§53)

---

## RESUME PROMPT (Inscript Programming Language v1c)

*We are resuming from the Inscript Programming Language Implementation Hardening Addendum v1c (May 11, 2026), which extends v1b Design Resolutions (same date), which extends v1a Pre-Build (same date), which extends the Inception Checkpoint v1 (same date). v1c closes seven implementation-level specification gaps from a final external review: (1) Vocabulary words cannot appear as string values — lexer tagging is authoritative, parse error if vocabulary-tagged token appears in value/field position, no quoting in v1, 29 words excluded; (2) Article `an` added to vocabulary and reserved list, correcting the count from 28 to 29; (3) Blank lines silently skipped, no comment syntax in v1; (4) Iterator context for `each` — temporary binding separate from symbol table, field resolution order is iterator context then symbol table, discarded after loop, compositions do NOT inherit iterator context; (5) v1 text interpreter output taxonomy — five outcomes only: Success, Amber (precedence), Amber (reorderer ambiguity), Error (parse), Error (semantic); complexity cap is informational in text mode, not gating; (6) Parser requires non-consuming lookahead, consuming advance, and clause-context state tracking to execute the seven disambiguation rules in v1b §44; (7) Deterministic interpretation only — no inference, no assumption, no guessing, no type coercion, no implicit operations; the prose IS the program. Three additional test sentences added (32–34). Build specification is now four documents plus test suite: inception checkpoint v1, addendum v1a, addendum v1b, addendum v1c, plus the thirty sentences (now thirty-four). Build sequence: lexer → parser → semantic analyzer → interpreter. Rob is architect; Claude is builder.*

---

## PROVENANCE NOTE

This document was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - §11 vocabulary table (line 178): articles listed as `the`, `a` only — `an` absent, confirming the gap.
  - §11 examples using `an`: line 185 (`remember an order with total as 75`), line 448 (`remember an order called order1`), line 578 (`remember an order with total as 75`) — confirming inconsistency.
  - §22 unknown word handling (line 438): positional classification specifies UNKNOWN tokens in value/field positions — does NOT specify behavior for vocabulary-tagged tokens in those positions, confirming the gap.
  - §21 `and`/`or` context rule 1 (line 407): "next token = value/unknown" — explicitly expects UNKNOWN, not VERB/CONNECTIVE/OPERATOR tokens.
  - §22 whitespace normalization (line 432): "Each newline boundary is a statement separator" — blank line handling not specified, confirming the gap.
  - §17 reorderer ambiguity (line 329): "the reorderer does not guess" — amber with clarification prompt when multiple valid slot-fillings exist. Confirmed.
  - §17 slot filling (line 306): deterministic matching by category. Confirmed.
  - §21/resume prompt: `each` wraps sub-operations via recursive descent (line 500). Confirmed.
  - §24 `each` output rule (line 476). Confirmed.
  - §19 Mechanism 4 complexity cap (line 387): amber with decomposition suggestion. Confirmed.
  - §9 error mode (line 134): errors describe what's missing. Confirmed.
  - §23 semantic errors (line 460, 468): type mismatch and name-not-found messages. Confirmed.
  - Q6 error model (line 533): still open as a design question — this addendum's output taxonomy (§50) partially resolves Q6 for the v1 text interpreter.
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - §29 reserved word table: 28 words. Confirmed. Corrected to 29 by §47.
  - §29 error message for name positions: "Please choose a different name." Confirmed. Extended by §46 for value positions.
  - §30 mixed-precedence Amber Light. Confirmed. Classified as Outcome 2 in §50.
  - §33 canonical prose rendering. Confirmed. Integrated into Outcome 1 in §50.
- **`inscript_addendum_v1b_design_resolutions.md`** (May 11, 2026):
  - §37 `each` dual role (verb vs. pronoun). Confirmed. Distinguished from iterator context: pronoun is parse-time, iterator context is execution-time (§49).
  - §38 `combine` numeric-only type error. Confirmed. Classified as Outcome 5 in §50.
  - §41 named composition call fallback. Confirmed. Referenced in §50 Outcome 4 (parse failure when fallback fails).
  - §44 seven disambiguation rules. Confirmed. §51 specifies the parser capability that enables them.
- **`inscript_v1_thirty_sentences.md`** (May 11, 2026): Sentences 6, 7, 8 use `an` — confirmed, driving §47. Test coverage gaps for value-position collision, `an` article, and no-verb error addressed by §53 (sentences 32–34).
- **Gemini external review** (May 11, 2026): Five findings (Literal Leak, Implicit Each scope, Amber Light heuristics, Multi-Word Lookahead, Word Salad Safety Rail). All five dispositioned and documented in §46–§52.
- **v7.5g Inscript Resolution**: Prose-as-syntax invariant (§13 line 165: "valid inscriptions are readable as English prose") — confirms `an` must be accepted for natural prose.
- **Filename:** `inscript_addendum_v1c_implementation_hardening.md` — domain `inscript` (provisional, pre-vault), class `addendum` (per skill table), version `v1c` (third addendum to v1, following v1a and v1b), subtitle `implementation_hardening`. Verified against naming grammar in rmt-working-documents skill.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE IMPLEMENTATION HARDENING ADDENDUM v1c*

*May 11, 2026*

*The external reviewers looked for holes.*
*They found the seams between what was designed and what was specified.*
*Designed but unspecified is where rewrites live.*
*Every seam is now stitched.*
*The build specification says what the code must do — all of it, and only it.*
