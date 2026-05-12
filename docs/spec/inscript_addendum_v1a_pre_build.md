# ADDENDUM
## Inscript Programming Language — Pre-Build Resolution
### v1a — Closing Gaps Before the Lexer

**Status:** LOCKED — EXTENDS `inscript_inception_checkpoint_v1.md`
**Date:** May 11, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Addendum — closes open threads identified by external stress testing; no new architecture
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_inception_checkpoint_v1.md` (May 11, 2026). Continues from §27 (Branches for Future Sessions). All decisions in the inception checkpoint remain locked and unchanged. This addendum closes one gap (reserved word exclusion), locks one implicit decision (mixed-operator precedence disambiguation), and establishes three design principles (AST-state-filtered tray, authorization as compositional act, canonical prose rendering) that were latent in the inception checkpoint but not explicitly locked. No new vocabulary, no new pipeline stages, no changes to the v1/v2 scope split.

---

## HOW TO READ THIS DOCUMENT

- This addendum was prompted by a five-persona stress test (Gemini, May 11, 2026) that interrogated the inception checkpoint from compiler theory, Freirean pedagogy, UX, domain utility, and security perspectives.
- Each finding from the stress test is dispositioned: closed (gap resolved here), confirmed (already locked in the inception checkpoint), logged (noted for future sessions), or rejected (not applicable).
- §28–§34 continue the inception checkpoint's section numbering.
- This document plus the inception checkpoint form the build specification for the v1 interpreter.

---

### §28 — SESSION CONTEXT

The inception checkpoint was subjected to external review via a structured stress test assembling five simulated subject-matter experts: a programming language theory specialist, a Freirean pedagogy critic, an interaction architect, a domain sentinel (business/healthcare), and a red-team security analyst. Each persona produced one offensive critique (structural weakness) and one defensive recommendation (reinforcement).

The stress test surfaced one genuine gap in the inception checkpoint (reserved word collision — the lexer and parser have no rule preventing a user-provided name from colliding with a vocabulary word), one implicit decision that needed explicit locking (boolean precedence in mixed `and`/`or` chains), and three design principles that were structurally present but not named as lockable decisions (AST-state-filtered tile tray, authorization as compositional act, canonical prose rendering as logic preview). The remaining findings were either already addressed by the inception checkpoint's locked decisions or were correctly scoped as future-session concerns.

This addendum closes all five items and dispositions every stress test finding against the inception checkpoint.

---

### §29 — RESERVED WORD EXCLUSION RULE

**Decision: No user-provided name — variable name, field name, or named composition name — may match any word in the base vocabulary, the v2 designed vocabulary, or any active domain pack. LOCKED as lexer/parser enforcement rule.**

The gap: the inception checkpoint §22 specifies that the lexer tags vocabulary words by category and passes unknown words to the parser for positional classification. But it does not address what happens when a user attempts to use a vocabulary word as a name. For example: `remember a value called filter` — the lexer tags `filter` as a verb, the parser expects a name after `called`, encounters a verb token, and produces a confusing structural error rather than a clear reserved-word message.

The resolution has two parts:

**Part 1 — The reserved word list.** All words in the designed vocabulary are reserved, including v2 deferred words. Reserving deferred words prevents the breakage scenario where a user names something `when` in v1 and their programs fail when v2 introduces `when` as a temporal connective. The v1 reserved word list:

| Source | Words | Count |
|---|---|---|
| v1 verbs (§11) | `remember`, `show`, `filter`, `count`, `gather`, `combine`, `each` | 7 |
| v1 connectives (§11) | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as` | 9 |
| v1 operators (§11) | `is`, `above`, `below`, `not` | 4 |
| v1 multi-word component (§22) | `equal` (reserved because it initiates the `equal to` lookahead; allowing it as a name creates lexer ambiguity) | 1 |
| v1 articles (§11) | `the`, `a` | 2 |
| v2 deferred verbs (§11, §21) | `transform`, `choose`, `compare` | 3 |
| v2 deferred connectives (§11) | `when`, `unless` | 2 |
| **Total** | | **28** |

Note: `equal to` is a multi-word operator token. The word `to` is already reserved as a connective. The word `equal` must be independently reserved because a name `equal` followed by `to` would trigger the multi-word lookahead and produce an operator token instead of a name reference — a silent misparse. `equal` alone (not followed by `to`) would otherwise fall through as unknown, making the behavior dependent on what word follows, which violates the principle that reserved words fail consistently.

**Part 2 — Enforcement point and error message.** The enforcement is a parser-level check, not a lexer-level check. The lexer correctly tags vocabulary words by their vocabulary category. The parser, when it expects a name (after `called`, as a field name in a `with...as` clause, as a named composition name after `how to`), checks whether the token it received is a vocabulary word rather than an unknown word. If so, it produces a specific error:

> "The word '[word]' is reserved in Inscript — it's used as a [category]. Please choose a different name."

This error fires before the structural parse fails, so the user sees a clear explanation rather than a confusing grammar error. The error message names the collision category (verb, connective, operator) so the user understands why their choice was rejected.

**Domain pack extension:** When a domain pack is active, its vocabulary words are added to the reserved list for the duration of that session. A name that was valid without a domain pack may become invalid when the pack is activated. This is surfaced during pack activation: "Activating the Healthcare pack. Note: you have a variable named 'patient', which is now a reserved word in this pack. You'll need to rename it." This is a known UX pressure point but it is the correct behavior — the alternative (silently reinterpreting the user's variable as a domain verb) is worse.

---

### §30 — MIXED-OPERATOR PRECEDENCE DISAMBIGUATION

**Decision: When a `where` clause contains both `and` and `or`, the validity indicator goes amber with a disambiguation prompt showing the parser's interpretation. The parser applies standard boolean precedence (`and` binds tighter than `or`), but the user must confirm or restructure. LOCKED as mixed-precedence interaction rule.**

The inception checkpoint §21 locks compound condition behavior and gives an example: `where A and B or C` produces a tree with `or` at the root and `and(A, B)` as one child. This is standard boolean precedence — `and` binds tighter than `or` — and it is the correct parse. The gap was not in the parser logic but in the interaction: a non-programmer reading `where status is active and age is above 18 or role is admin` cannot reliably predict whether the `or` applies to the entire preceding clause or only to the last condition. The parser knows the answer; the user may not.

The resolution applies the authorize-don't-author principle (v7.5g §19) to precedence itself. When the parser encounters a `where` clause with mixed `and`/`or`, it parses deterministically using standard precedence, then presents its interpretation for confirmation:

> "I'll read this as: (status is active AND age is above 18) OR role is admin. Is that what you mean? If not, split it into two statements."

This is not a parser failure — the parse succeeds. It is a semantic confirmation step, analogous to the Amber Light validity indicator (v8.11 §283) showing structural incompleteness. The difference: structural incompleteness means the sentence cannot parse; mixed-precedence means the sentence parses but the intent may differ from the parse.

The Sentence Complexity Cap (§19, Mechanism 4) already provides a structural hook — mixed `and`/`or` in a `where` clause is a specific instance of complexity that the cap is designed to surface. This disambiguation fires alongside the cap, not instead of it: a mixed-precedence clause that also exceeds the complexity threshold gets both the precedence prompt and the decomposition suggestion.

Single-operator `where` clauses (`where A and B and C` or `where A or B or C`) do not trigger this disambiguation — their meaning is unambiguous regardless of grouping because `and` chains and `or` chains are associative.

---

### §31 — AST-STATE-FILTERED TILE TRAY

**Decision: When a tile is placed in the composition strip, the tile tray shows only tiles that can legally fill the current verb's remaining slots. Tiles that cannot appear in any valid next position are hidden, not grayed out. LOCKED as tile-tray interaction principle.**

This principle was structurally present in the inception checkpoint but not named as a lockable decision. The slot-filling reorderer (§17) defines each verb's signature as a set of expected slots with typed expectations. The tile tray is the visual surface of the vocabulary (§11). Combining these: when a verb tile is placed, the verb's signature defines which slot types remain unfilled, and only tiles matching those types illuminate in the tray.

Example: the user places the `filter` tile. The `filter` signature (§17) expects: target (name/collection) + condition (field + operator + value). The tray now shows: articles (`the`, `a`), any user-defined names (to fill the target slot), and the `where` connective (to introduce the condition). Verb tiles, `how`, `called`, `as`, and other connectives that cannot appear in a `filter` signature are hidden. As the user fills slots, the tray narrows further: once the target is filled and `where` is placed, the tray shows field references, operators, and values.

This is the stress test's "Dynamic Tray" recommendation (Interaction Architect) mapped onto the inception checkpoint's existing architecture. It directly addresses the scannability concern: even with a domain pack adding 15 terms, the visible tray at any given moment shows only the terms that can legally appear next. The tray IS the grammar, rendered as available choices.

Hidden rather than grayed out: grayed-out tiles are visual noise that adds cognitive load without adding information. The user does not need to see what they can't do — they need to see what they can do. This follows the inception checkpoint's principle that "the DSL constraint is experienced as the shape of the instrument, not as an error message" (§7, Property 2).

This principle is locked here for the tile interface design (Branch C). It does not affect the v1 interpreter build, which operates on text input.

---

### §32 — AUTHORIZATION REQUIRES COMPOSITIONAL ACT

**Decision: In the authorize-don't-author interaction model, the user must perform at least one deliberate compositional act — placing, removing, or modifying a tile or prose element — before a system-proposed program can be committed. Passive acceptance (a single "confirm" button with no modification) is not authorization. LOCKED as authorize-don't-author interaction constraint.**

The stress test's Freirean pedagogy critique identified a real risk: if authorize-don't-author degenerates into "click Yes to the machine's proposal," it becomes consumption rather than authorship. The system proposes; the user clicks confirm; the user has authored nothing. This is the "ChatGPT Trap" — it feels like agency but the human never named their own world.

The resolution: the authorization flow requires at least one compositional act. The system proposes a working program based on observed intent. The user must then touch the composition — place a tile, modify a value, reorder an element, change a name — before the "commit" action becomes available. The modification can be trivial (changing a threshold value from 50 to 75), but it must be deliberate. The user's fingerprint must be on the artifact.

This is not a v1 interpreter concern — it is a tile-interface and proposal-engine design constraint (Branches C and E). It is locked here because it is a design invariant that must be present from the first implementation of authorize-don't-author, not retrofitted after passive acceptance patterns have been established.

The stress test suggested "Reflection Prompts" during authorization ("Why is this rule being set?"). This is logged but not locked — reflection prompts are a pedagogical design choice that belongs in the Narratia integration (Branch E), not in the language specification.

---

### §33 — CANONICAL PROSE RENDERING

**Decision: The parser produces a canonical prose rendering of every successfully parsed program — a plain-English sentence reconstructed from the AST in canonical slot order. This rendering is the "Logic Preview" and serves as the round-trip verification that the parser's interpretation matches the user's intent. LOCKED as parser output requirement.**

The stress test's security analyst recommended a "Logic Preview" to prevent obfuscated prose. The inception checkpoint already contains the architectural basis: the reorderer (§17) maps free-order input to canonical slot order, and the InscriptionPreview (v8.11 §283, confirmed in the Möbius Inscript tile architecture) renders the reordered arrangement as a prose sentence in real-time.

For the Inscript Programming Language, the canonical prose rendering is a parser output, not just a tile-interface feature. When the parser successfully builds an AST from input text, it also produces the canonical prose form of that AST. This serves three purposes:

1. **Intent verification.** The user typed `the orders filter where above 50 total is`. The parser reordered and parsed it. The canonical rendering shows: `filter the orders where total is above 50`. The user can verify that the parser understood their intent.

2. **Obfuscation prevention.** A malicious or confused input that produces a syntactically valid but semantically surprising parse is surfaced by the canonical rendering. The user sees what the program will actually do, not what they thought they typed.

3. **Round-trip fidelity test.** The canonical rendering is the AST-to-prose direction of the same translation the parser performs in the prose-to-AST direction. If the round trip loses meaning, the AST is wrong. This is a structural test, not just a display feature.

In the v1 interpreter (text-based, no tile interface), the canonical rendering is displayed after parsing and before execution: "I understand this as: [canonical prose]. Running now." In the tile interface (Branch C), it is the InscriptionPreview, already specified in v8.11 §283.

---

### §34 — STRESS TEST DISPOSITION TABLE

Every finding from the external stress test is dispositioned against the inception checkpoint.

| Persona | Offensive Critique | Disposition | Reference |
|---|---|---|---|
| PLT Specialist | `and`/`or` precedence ambiguity in compound conditions | **Closed (§30).** Precedence is deterministic (§21); mixed `and`/`or` now triggers Amber Light disambiguation. | Inception §21, this addendum §30 |
| Freirean Pedagogy | Authorize-don't-author risks passive consumption ("ChatGPT Trap") | **Closed (§32).** Authorization now requires at least one compositional act before commit. | v7.5g §19, this addendum §32 |
| Interaction Architect | Tile tray becomes unscannable with domain packs (50+ tiles) | **Closed (§31).** Tray is AST-state-filtered — only legal-next tiles are visible. Slot filling (§17) provides the filtering logic. | Inception §17, §19, this addendum §31 |
| Domain Sentinel | v1 "dead on arrival" without event-driven execution | **Confirmed already addressed.** Inception §13 explicitly splits v1/v2 use cases. v1 beachhead (business rules, compliance, data filtering) is viable without event-driven execution. Sequential execution is a strength for the v1 target domains, not a limitation. | Inception §13, §25 |
| Red Team | Prose injection via reserved word collision in user-provided names | **Closed (§29).** Reserved word list of 28 words locked. Parser-level enforcement with clear error messages. Domain pack words added to reserved list during activation. | Inception §22, this addendum §29 |

| Persona | Defensive Recommendation | Disposition | Reference |
|---|---|---|---|
| PLT Specialist | "Precedence-by-Prose" — use Amber Light to force disambiguation | **Adopted (§30).** Mixed `and`/`or` triggers Amber Light with the parser's interpretation shown for confirmation. | This addendum §30 |
| Freirean Pedagogy | "Final Snap" — require manual tile placement to commit | **Adopted as principle (§32).** Generalized: at least one compositional act required, not limited to a specific snap gesture. | This addendum §32 |
| Freirean Pedagogy | "Reflection Prompts" during authorization | **Logged for Branch E (Narratia Integration).** Pedagogical design choice, not a language specification decision. | — |
| Interaction Architect | "Contextual Tray" — filter tiles based on AST state | **Adopted (§31).** Mapped onto slot-filling architecture. Hidden, not grayed out. | This addendum §31 |
| Interaction Architect | "Tile Taxonomy" defining which tiles illuminate by AST state | **Subsumed by §31.** The verb signature table (§17) IS the tile taxonomy — each signature defines legal-next tile categories. | Inception §17 |
| Domain Sentinel | "Batch Listener" — run v1 scripts on a loop to simulate events | **Logged, not adopted.** A deployment strategy, not a language specification. The v1 interpreter is sequential by design (§16). A runner that loops execution is an external tool. Worth exploring as a v1.5 deployment option, but not a pre-build decision. | — |
| Red Team | Reserved word collision enforcement | **Adopted (§29).** | This addendum §29 |
| Red Team | "Logic Preview" — AST-to-prose rendering for obfuscation prevention | **Adopted (§33).** Canonical prose rendering is a parser output requirement. | This addendum §33, v8.11 §283 |

---

### §35 — PRE-BUILD PLAN

The inception checkpoint (§16) locks the build sequence: vocabulary design → lexer → parser → interpreter → tile interface. This addendum does not change the sequence. It specifies the concrete deliverables that must exist before the first line of Python is written, and the acceptance criteria for each build stage.

**Pre-code deliverable: The Thirty Sentences.**

Branch A (§27) specifies: "Write the thirty example sentences using only v1 vocabulary. Discover the grammar. Test readability with non-programmers." These sentences are the language's test suite, grammar discovery tool, and design validation in one artifact. They must:

- Use only v1 vocabulary (§11): seven verbs, nine connectives, five operators, two articles, one delimiter.
- Cover every verb at least twice — once in its simplest form, once with a condition or modifier.
- Include at least three sentences using structured records (the `as` connective, §23).
- Include at least two named compositions (`remember how to`, §19 Mechanism 3).
- Include at least two sentences with compound conditions (`and`/`or` in a `where` clause, §21).
- Include at least one sentence that triggers the mixed-precedence Amber Light (§30).
- Include at least one sentence that would violate the reserved word rule (§29) — to test the error path.
- Include at least one multi-statement program (a sequence of sentences that build on each other).

The thirty sentences are not throwaway examples. Each sentence is a test case: it will be fed to the lexer, parser, and interpreter as they are built, and the expected output at each stage must be specified alongside the sentence. The sentences are the specification made concrete.

**Build stage acceptance criteria:**

| Stage | Deliverable | Acceptance criterion |
|---|---|---|
| **Lexer** | Python module (~40 lines per §16) | All thirty sentences tokenize correctly. Reserved words produce reserved-word errors when used as names. `equal to` combines into a single token. Case insensitivity confirmed. Decorative punctuation stripped. Numbers recognized. |
| **Parser** | Python module (~200 lines per §16) | All thirty sentences parse into correct ASTs. Slot filling produces canonical order from free-order input. `and`/`or` disambiguation produces correct trees for all four context cases (§21). `is` dual role resolves correctly. `not` produces correct comparison semantics. Mixed `and`/`or` triggers Amber Light output. Compound conditions nest correctly. |
| **Semantic Analyzer** | Python module (size TBD) | Symbol table tracks types correctly. Field references resolve against record schemas. Type mismatches produce clear errors. Named composition grammar validates at definition time, name resolution at call time (§23). |
| **Interpreter** | Python module (~200 lines per §16) | All thirty sentences execute with correct output. Auto-show for standalone expressions. In-place `filter` modification. Inline `gather` naming. Copy semantics confirmed. Sequential execution confirmed. Canonical prose rendering displayed before execution (§33). |

**Build roles:**

- **Rob (Architect):** Designed the language. Approves all design decisions. Writes the thirty sentences. Reviews and approves each build stage. Thought partner on ambiguities the build surfaces.
- **Claude (Builder):** Writes the Python. Proposes solutions for implementation ambiguities. Flags when a build-stage discovery conflicts with a locked decision. Produces each module with tests against the thirty sentences.

**Build sequence after this addendum:**

1. Rob writes the thirty sentences (or we co-produce them in session).
2. Builder produces the lexer. Rob approves against sentence test cases.
3. Builder produces the parser. Rob approves against AST expectations.
4. Builder produces the semantic analyzer. Rob approves against type-checking expectations.
5. Builder produces the interpreter. Rob approves against execution expectations.
6. Each stage is tested against all thirty sentences before the next stage begins.

---

## WHAT IS LOCKED

This addendum locks:

- **Reserved word exclusion rule:** 28 reserved words (23 v1 + 5 v2 deferred). No user-provided name may match a reserved word or an active domain pack word. Enforcement at the parser level with clear error messages. (§29)
- **Mixed-operator precedence disambiguation:** Mixed `and`/`or` in a `where` clause triggers the Amber Light showing the parser's interpretation (standard boolean precedence: `and` binds tighter than `or`). User confirms or restructures. Single-operator chains do not trigger. (§30)
- **AST-state-filtered tile tray:** The tile tray shows only tiles that can legally fill the current verb's remaining slots. Hidden, not grayed out. The verb signature table (§17) is the filtering logic. (§31)
- **Authorization requires compositional act:** Authorize-don't-author requires at least one deliberate compositional act before a system-proposed program can be committed. Passive acceptance is not authorization. (§32)
- **Canonical prose rendering:** The parser produces a canonical prose form of every successfully parsed AST. Displayed before execution in the v1 interpreter. Serves as intent verification, obfuscation prevention, and round-trip fidelity test. (§33)

This addendum does NOT lock:

- Any changes to the v1 vocabulary (§11 unchanged)
- Any changes to the pipeline architecture (§8–§9 unchanged)
- Any changes to the v1/v2 scope split (§25 unchanged)
- The thirty example sentences (pre-code deliverable, not yet produced)
- Any tile interface design beyond the filtering principle
- Any Narratia integration decisions (Branch E)
- Any deployment target decisions (Q7)

---

## RESUME PROMPT (Inscript Programming Language v1a)

*We are resuming from the Inscript Programming Language Pre-Build Addendum v1a (May 11, 2026), which extends the Inception Checkpoint v1 (same date). The addendum closed five items before the build begins: (1) Reserved word exclusion — 28 reserved words (23 v1 + 5 v2 deferred), parser-level enforcement, clear error messages, domain pack words added during activation. (2) Mixed-operator precedence disambiguation — mixed `and`/`or` in a `where` clause triggers Amber Light showing parser's interpretation (standard boolean precedence, `and` tighter than `or`); user confirms or restructures. (3) AST-state-filtered tile tray — only legal-next tiles visible, hidden not grayed, verb signatures (§17) provide the filtering logic. (4) Authorization requires compositional act — at least one deliberate modification before commit; passive acceptance is not authorization. (5) Canonical prose rendering — parser produces canonical prose form of every AST, displayed before execution in v1 interpreter. All five stress test critiques dispositioned. Build roles: Rob is architect and language designer; Claude is builder. Build sequence: thirty example sentences (pre-code, not yet produced) → lexer → parser → semantic analyzer → interpreter. Each stage tested against all thirty sentences. Tile interface is a separate layer after the interpreter works. The inception checkpoint + this addendum are the build specification.*

---

## PROVENANCE NOTE

This document was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - v1 vocabulary table confirmed at §11 (lines 171–179): 7 verbs, 9 connectives, 5 operators, 2 articles, 1 delimiter.
  - v2 deferred vocabulary confirmed at §11 (lines 189–198): `when`, `unless` (temporal connectives), `transform`, `choose`, `compare` (deferred verbs).
  - `and`/`or` four-meaning disambiguation confirmed at §21 (lines 403–411), with compound condition tree construction (`where A and B or C` → `or` at root, `and(A,B)` as child) confirmed at §21 (line 418).
  - `equal to` multi-word lookahead confirmed at §22 (lines 426–427).
  - Unknown word handling (parser classifies by position) confirmed at §22 (lines 437–438).
  - Slot-filling reorderer with verb signatures confirmed at §17 (lines 306–327).
  - Sentence Complexity Cap ("approximately three clauses or fifteen content words") confirmed at §19 (line 387).
  - Build sequence confirmed at §16 (lines 291–296).
  - Valid name characters (letters, digits, hyphens, must start with a letter) confirmed at §22 (line 436).
  - v1/v2 use case split confirmed at §13 (lines 240–258).
- **`mobius_paradigm_checkpoint_v7_5g_inscript_resolution.md`**: "Authorize, Don't Author" as on-ramp confirmed at §19 (line 260). Authorization of observed behavior, not authorship from a blank editor, confirmed at line 264.
- **`mobius_checkpoint_v8_11_inscript_grammar.md`**: Validity indicator (green check / amber with description) confirmed at §283 (line 360). InscriptionPreview (renders reordered arrangement as prose sentence in real-time) confirmed at §283 (line 362).
- **Gemini stress test document** (uploaded May 11, 2026): Five personas, five offensive critiques, five defensive recommendations, five synthesized learnings. All ten findings dispositioned in §34.
- **Filename:** `inscript_addendum_v1a_pre_build.md` — domain `inscript` (provisional, pre-vault), class `addendum` (per skill table), version `v1a` (first addendum to v1 inception checkpoint), subtitle `pre_build`. Verified against naming grammar in rmt-working-documents skill.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE PRE-BUILD ADDENDUM v1a*

*May 11, 2026*

*The stress test asked five experts to break the design.*
*The design held. The gaps were at the seams — where the lexer meets names, where precedence meets prose, where proposal meets authorship.*
*Those seams are now closed.*
*Build.*
