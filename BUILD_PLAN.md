# INSCRIPT v1 BUILD PLAN
## For Execution by Claude Code

**Date:** May 11, 2026
**Architect:** Rob Thomas / R. Michael Thomas
**Builder:** Claude Code
**Goal:** A Python text interpreter that passes 48 locked test sentences with structured result objects.

---

## SPECIFICATION DOCUMENTS

All design decisions are locked in these five documents, located in `docs/spec/`. **Read all five before writing any code.** When a decision is referenced by section number, look it up — do not guess or pattern-match.

| Document | What it locks |
|---|---|
| `inscript_inception_checkpoint_v1.md` | Language design: vocabulary (§11), pipeline (§8–§9), verb signatures (§17), reorderer architecture (§17), parser rules (§21–§22), semantic analyzer (§23), interpreter behaviors (§24), v1/v2 scope (§25) |
| `inscript_addendum_v1a_pre_build.md` | Reserved words (§29), mixed-precedence amber (§30), canonical prose rendering (§33) |
| `inscript_addendum_v1b_design_resolutions.md` | Eight design resolutions: prose descriptors (§36), `each` dual role (§37), `combine` numeric-only (§38), `combine` non-destructive (§39), `gather` stores+shows (§40), composition calls (§41), display format (§42), `from` disambiguation (§43), complete disambiguation ruleset (§44) |
| `inscript_addendum_v1c_implementation_hardening.md` | Vocab words can't be values (§46), article `an` (§47), blank lines skipped (§48), iterator context (§49), output taxonomy — five outcomes (§50), parser lookahead capability (§51), deterministic interpretation only (§52) |
| `inscript_addendum_v1d_build_boundary.md` | Reorderer v1 scope (§55), stepwise execution (§56), names lowercase (§57), duplicates overwrite (§58), homogeneous lists (§59), schema homogeneity (§60), single-token strings (§61), descending ranges error (§62), gather cap 10,000 (§63), structured results (§64), hostile tests (§65), build boundary (§66) |

The test specification is in `docs/spec/inscript_v1_thirty_sentences.md` plus sentences 32–48 defined in v1c §53 and v1d §65.

---

## PROJECT STRUCTURE

```
inscript/
├── CLAUDE.md                  # Claude Code project instructions
├── BUILD_PLAN.md              # This file
├── pyproject.toml             # Python project config
├── docs/
│   └── spec/                  # The five specification documents + test spec
│       ├── inscript_inception_checkpoint_v1.md
│       ├── inscript_addendum_v1a_pre_build.md
│       ├── inscript_addendum_v1b_design_resolutions.md
│       ├── inscript_addendum_v1c_implementation_hardening.md
│       ├── inscript_addendum_v1d_build_boundary.md
│       └── inscript_v1_thirty_sentences.md
├── src/
│   └── inscript/
│       ├── __init__.py
│       ├── vocabulary.py      # Token types, reserved words, verb signatures
│       ├── lexer.py           # Tokenization
│       ├── reorderer.py       # Narrow table-driven reorderer
│       ├── parser.py          # Canonical-order slot-filling parser
│       ├── analyzer.py        # Semantic analysis
│       ├── interpreter.py     # Execution engine
│       ├── renderer.py        # Canonical prose rendering (AST → prose)
│       ├── result.py          # Structured result objects
│       └── cli.py             # CLI wrapper (display, amber prompts, file I/O)
├── tests/
│   ├── conftest.py            # Shared fixtures (symbol tables, sample data)
│   ├── test_lexer.py
│   ├── test_reorderer.py
│   ├── test_parser.py
│   ├── test_analyzer.py
│   ├── test_interpreter.py
│   ├── test_renderer.py
│   └── test_integration.py    # Full pipeline: all 48 sentences end-to-end
└── examples/
    ├── program1_basics.insc        # Programs 1–5 from the thirty sentences
    └── program2_orders.insc
```

---

## BUILD ORDER — SEVEN PHASES WITH GATES

Each phase produces a module with tests. **The gate for each phase must pass before starting the next.** Do not build ahead.

---

### PHASE 1: Foundation (`vocabulary.py`, `result.py`)

**vocabulary.py** — Shared constants used by every other module.

```python
# Token types
class TokenType(Enum):
    VERB = "VERB"
    CONNECTIVE = "CONNECTIVE"
    OPERATOR = "OPERATOR"
    ARTICLE = "ARTICLE"
    DELIMITER = "DELIMITER"
    NUMBER = "NUMBER"
    UNKNOWN = "UNKNOWN"

# Token dataclass
@dataclass
class Token:
    type: TokenType
    value: str
    position: int  # character offset in original input

# Vocabulary sets
VERBS: set           # 7: remember, show, filter, count, gather, combine, each
CONNECTIVES: set     # 9: where, and, or, from, with, called, to, how, as
OPERATORS: set       # 4: is, above, below, not (equal handled as multi-word)
ARTICLES: set        # 3: the, a, an
DELIMITERS: set      # 1: :

# V2 reserved (not executable, but reserved for future)
V2_RESERVED: set     # 5: transform, choose, compare, when, unless

# Multi-word component reserved independently
MULTI_WORD_RESERVED: set  # 1: equal

# Combined reserved word set (29 total per v1c §47)
ALL_RESERVED: set    # Union of all above

# Verb signatures — each verb's expected slots
# Source: inception §17 (lines 315–323), refined by v1b/v1c/v1d
VERB_SIGNATURES: dict  # verb → list of slot definitions
```

The verb signatures must be built from §17's table:

| Verb | Slots | Notes |
|---|---|---|
| `remember` | name (via `called`) + value (via `with` or `from`) | `with...as` for records, `how to` for compositions |
| `show` | target | Single name or field (inside `each` iterator context) |
| `filter` | target + condition (via `where`) | Condition = field/each + operator + value |
| `count` | target | |
| `gather` | name (from article+noun) + range (via `from`...`to`) | Always stores + shows (v1b §40) |
| `combine` | target | Numeric only (v1b §38), non-destructive (v1b §39) |
| `each` | collection + action (sub-operation via recursive descent) | |

**result.py** — Structured result objects per v1d §64.

```python
class ResultStatus(Enum):
    SUCCESS = "success"
    AMBER_PRECEDENCE = "amber_precedence"
    AMBER_AMBIGUITY = "amber_ambiguity"
    ERROR_PARSE = "error_parse"
    ERROR_SEMANTIC = "error_semantic"

@dataclass
class InscriptResult:
    status: ResultStatus
    canonical: str | None       # Canonical prose rendering (None if parse failed)
    output: list[str] | None    # Display lines (None if no output)
    message: str | None         # Error or amber message (None if success)
    executed: bool              # Whether the statement was executed
```

**Gate:** Unit tests confirm vocabulary sets contain the correct words and counts (29 reserved), verb signatures contain all 7 verbs, result objects can be constructed with all five statuses.

---

### PHASE 2: Lexer (`lexer.py`)

**Input:** A single line of raw text.
**Output:** A list of `Token` objects, or an empty list for blank lines.

**Algorithm** (from inception §22, v1c §47–§48):

1. Strip trailing newline/whitespace.
2. If line is empty or whitespace-only, return empty list (v1c §48).
3. Lowercase the entire line (§22 line 424).
4. Strip decorative punctuation: `,`, `.`, `?`, `!` (§22 line 430). Do NOT strip `:`.
5. Normalize whitespace: collapse multiple spaces/tabs to single spaces (§22 line 432).
6. Handle colon: if a word ends with `:`, split into word + delimiter token (§22 line 434).
7. Split on spaces into words.
8. Process each word:
   - If word is `:` → DELIMITER token
   - If word is `equal` AND next word is `to` → consume both, produce single OPERATOR token with value `equal_to` (§22 line 426)
   - If word is in VERBS → VERB token
   - If word is in CONNECTIVES → CONNECTIVE token
   - If word is in OPERATORS → OPERATOR token
   - If word is in ARTICLES → ARTICLE token
   - If word matches number pattern (digits, optional single decimal point) → NUMBER token (§22 line 428)
   - Otherwise → UNKNOWN token
9. Return token list.

**Key behaviors:**
- `equal` NOT followed by `to` → UNKNOWN (it's reserved but not independently in the vocabulary; the parser catches reserved-word violations)
- `an` → ARTICLE (v1c §47)
- Numbers: `30`, `3.14`, `100` are numbers. No negatives in v1 (§25).
- Hyphens in names: `find-big-orders` stays as one token (§22 line 436). Split on spaces, not on hyphens.
- Colon attached to word: `find-big-orders:` → two tokens: UNKNOWN(`find-big-orders`) + DELIMITER(`:`)

**Gate:** Test all 48 sentences tokenize correctly. Test that `equal to` combines, case insensitivity works, punctuation is stripped, blank lines produce empty token lists, colons are split from adjacent words.

---

### PHASE 3: Reorderer (`reorderer.py`)

**Input:** List of tokens from lexer.
**Output:** Canonically-ordered token list, or an InscriptResult with amber/error status.

**Algorithm** (from v1d §55):

1. Find the verb token. If no VERB token exists:
   - Check if the first UNKNOWN token could be a named composition (this requires access to the symbol table — pass it in or defer to parser). For Phase 3, if no verb is found, return error result.
2. If verb is already the first non-ARTICLE token, pass through unchanged (canonical order).
3. If an ARTICLE+UNKNOWN sequence appears before the verb, move the verb to the front (target-before-verb reordering).
4. Check that tokens after `where` (if present) are in canonical condition order: field/each → `is` → operator → value. If scrambled, return error result with canonical suggestion.
5. For all other non-canonical arrangements, return error result: "I couldn't parse this. Try: [canonical suggestion]."

**The reorderer is narrow.** It handles exactly the permutations in v1d §55's acceptance table. It does NOT attempt to solve general free-order parsing.

**Gate:** Test canonical sentences pass through unchanged, `the orders filter where total is above 50` reorders to `filter the orders where total is above 50`, deeply scrambled sentences produce error with suggestion.

---

### PHASE 4: Parser + Renderer (`parser.py`, `renderer.py`)

**Input:** Canonically-ordered token list.
**Output:** AST node, or an InscriptResult with error/amber status.

This is the largest module. Build it verb by verb.

**Token stream:** Implement a `TokenStream` class with `peek()`, `consume()`, and clause-context tracking per v1c §51.

**AST node types** — one per verb plus supporting nodes:

```
RememberValueNode     — name, value, type descriptor (ignored)
RememberListNode      — name, items
RememberRecordNode    — name, fields [{name, value}]
RememberCompositionNode — name, body (sub-AST)
ShowNode              — target (name or field)
FilterNode            — target, condition
CountNode             — target
GatherNode            — name, from_val, to_val
CombineNode           — target
EachNode              — collection, action (sub-AST)
CompositionCallNode   — name
SequenceNode          — list of operation nodes (for and-chained operations)

ConditionNode         — field, operator, value
CompoundConditionNode — left, right, connector (and/or)
```

**Parser logic — build in this order:**

1. **Statement entry:** Consume verb (or check for composition call per v1b §41). Dispatch to verb-specific parser.

2. **`show`:** Consume target (UNKNOWN token = name). Simplest verb.

3. **`count`:** Same as show — consume target.

4. **`combine`:** Same — consume target.

5. **`remember`:** Most complex verb. Branch on what follows:
   - `how to [name] : [body]` → composition definition. Parse body recursively.
   - `[descriptor] called [name] with [field] as [value] and ...` → record
   - `[descriptor] called [name] with [value] and [value] ...` → list
   - `[descriptor] called [name] with [value]` → flat value
   - `[descriptor] called [name] from [verb-phrase]` → result capture (v1b §43, DQ8). Parse sub-expression recursively.
   - Prose descriptors between article and `called` are ignored (v1b §36).

6. **`gather`:** `[name] from [NUMBER] to [NUMBER]`. Name from article+noun (§24 line 484).

7. **`filter`:** `[target] where [condition]`. Parse condition:
   - Field/each (v1b §37: `each` inside `where` = pronoun) + `is` + operator + value
   - Handle `is` dual role (§21 line 414): peek at next token — if operator → comparison introducer; if value/unknown → equality.
   - Handle `not` modifier (§21 line 416): `not above` = ≤, `not below` = ≥, `not equal_to` = ≠.
   - Handle compound conditions with `and`/`or` (§21 line 418): recursive nesting. `and` binds tighter than `or`.
   - Handle mixed `and`/`or` → return amber_precedence result (v1a §30).

8. **`each`:** `[collection] [sub-operation]`. Parse sub-operation recursively (§21: recursive descent).

9. **Operation sequencing:** `and` between complete verb phrases (§21 line 409) → SequenceNode.

**Seven disambiguation rules** (v1b §44) — implement all:

| Word | Rule | Implementation |
|---|---|---|
| `and`/`or` | Four meanings by parser state + lookahead | Check clause context + next token type |
| `is` | Two meanings by lookahead | Peek next: operator → introducer; value/unknown → equality |
| `not` | Operator modifier | Always modifies following operator |
| `to` | Range vs. `equal_to` | Context: after `from`+number → range; after `equal` → multi-word (handled by lexer) |
| `from` | Two v1 meanings | Context: in `gather` → range; in `remember` + next=verb → recursive descent; next=name → reference |
| `each` | Verb vs. pronoun | Context: inside `where` → pronoun; verb position → iteration verb |
| Mixed `and`/`or` | Amber | `where` clause has both `and` and `or` → amber_precedence |

**renderer.py** — AST → canonical prose string:

Walk the AST and produce the canonical English sentence. This is the inverse of parsing. Every AST node type has a rendering rule. The renderer is used for:
- Canonical prose rendering displayed before execution (v1a §33)
- Canonical suggestion in reorderer error messages
- Round-trip verification in tests

**Gate:** All 48 sentences parse correctly (success sentences produce correct ASTs; hostile sentences produce correct error results). Canonical renderer round-trips every successful parse.

---

### PHASE 5: Semantic Analyzer (`analyzer.py`)

**Input:** AST node + symbol table.
**Output:** Validated AST (unchanged) or InscriptResult with error_semantic status.

**Checks** (from §23, v1b, v1c, v1d):

1. **Name resolution.** Every name reference must exist in the symbol table. Error: "I can't find '[name]'. You might need to 'remember' it first."

2. **Type checking for operations.**
   - `filter` requires target to be a list. Error: "I can only filter a list. '[name]' is a [type]."
   - `each` requires target to be a list. Error: "I can only iterate over a list. '[name]' is a [type]."
   - `combine` requires target to be a list of numbers (v1b §38). Error: "I can only combine numbers. '[name]' contains [type]."
   - `count` requires target to be a list. Error: "I can only count a list. '[name]' is a [type]."

3. **Field resolution.** Field references in `where` clauses must exist on all records in the target list (v1d §60). Error: "Not every item in '[name]' has a field called '[field]'."

4. **Type checking for comparisons.** `above`/`below`/`not above`/`not below` require numeric fields and values. Error: "'above' requires numbers, but '[field]' is text."

5. **List homogeneity.** Lists created by `remember...with` must contain all the same type (v1d §59). Error: "A list can't mix numbers and text."

6. **Gather range validation.**
   - `from` must be ≤ `to` (v1d §62). Error with suggestion.
   - Range size must be ≤ 10,000 (v1d §63). Error: "That range is too large. The maximum is 10,000 items."

7. **Composition grammar validation.** At definition time, the body must be a well-formed sentence. Name references are NOT checked (§23 line 466).

8. **Reserved word enforcement.** Already handled by parser for name positions (v1a §29) and by parser for value positions (v1c §46). The analyzer does not re-check these.

**The symbol table** is a dict mapping lowercase names to entries:

```python
@dataclass
class SymbolEntry:
    name: str               # Lowercase
    value: Any              # Python value (int, float, str, list, dict, AST)
    type: str               # "number", "string", "list_of_numbers", "list_of_strings",
                            # "list_of_records", "record", "composition"
    schema: dict | None     # For records: {field_name: type_string}
```

**Gate:** All 48 sentences validate correctly. Hostile sentences (35–48) produce correct semantic errors. Test name-not-found, type mismatches, field-not-found, mixed lists, range violations.

---

### PHASE 6: Interpreter (`interpreter.py`)

**Input:** Validated AST + symbol table (mutable).
**Output:** InscriptResult with success status + any output + side effects on symbol table.

**Behaviors** (from §24, v1b, v1c, v1d):

1. **`remember`** — Add or overwrite entry in symbol table (v1d §58). No output. Type inferred from value.

2. **`show`** — Read from symbol table, format per v1b §42, return as output lines.

3. **`filter`** — Modify target list in-place (§24 line 478). Remove items that don't match condition. No output.

4. **`count`** — Return count of items in target list. Auto-show (§24 line 472).

5. **`gather`** — Create list from range, store in symbol table with parsed name, auto-show (v1b §40).

6. **`combine`** — Sum all numbers in target list. Return sum. Auto-show. Do NOT modify source (v1b §39).

7. **`each`** — Iterate over collection. For each item, create iterator context (v1c §49), execute sub-operation, discard context after loop. Collect output from all iterations.

8. **Sequence execution** — For SequenceNode (and-chained operations), execute each operation in order. If one fails, earlier side effects remain (v1d §56). Return error with context message.

9. **Composition call** — Look up composition in symbol table, execute its stored AST body against current symbol table (v1b §41).

10. **Copy semantics** — All data operations copy values (§24 line 486). `remember a list called copy from the-data` copies, doesn't alias.

**Display formatting** (v1b §42):

| Type | Format |
|---|---|
| Number | As-is: `30`, `3.14` |
| String | As-is, no quotes: `active` |
| List of numbers | Comma-separated: `1, 2, 3` |
| List of strings | Comma-separated: `red, blue, green` |
| Record | Field: value pairs: `total: 75, status: active` |
| List of records | One record per line |
| `each...show field` | One value per line |

**Gate:** All 48 sentences execute correctly (or fail correctly for hostile tests). Verify auto-show, in-place filter, gather store+show, combine non-destructive, overwrite on duplicate names, stepwise failure, iterator context cleanup.

---

### PHASE 7: Integration (`cli.py`, `test_integration.py`)

**cli.py** — Thin wrapper. The interpreter never calls `input()` or `print()` (v1d §64). The CLI does.

```
Usage:
  python -m inscript <file.insc>      # Execute a file
  python -m inscript                  # Interactive REPL
  python -m inscript --test <file>    # Test mode (auto-confirm amber)
```

**REPL loop:**
1. Read a line.
2. Tokenize → reorder → parse → analyze → execute (full pipeline).
3. Display canonical rendering: "I understand this as: [canonical]"
4. If result is amber, display message and prompt for confirmation (y/n).
5. If result is error, display error message.
6. If result is success with output, display output.

**test_integration.py** — Full pipeline tests for all 48 sentences. Each test:
1. Feeds the sentence(s) through the full pipeline.
2. Checks the result status matches expected outcome.
3. Checks the output matches expected output (for success cases).
4. Checks the error message contains expected keywords (for error cases).
5. Checks symbol table state after execution (for multi-statement programs).

**Gate:** All 48 sentences pass end-to-end. The CLI runs the example programs from `examples/` directory.

---

## CRITICAL BUILD CONSTRAINTS

These apply to EVERY phase. Violating any one is a build failure.

1. **No pattern matching from memory.** Every design decision is in the spec documents. If you're unsure, read the document — don't guess. (Memory: "every architectural claim is load-bearing")

2. **No invented behavior.** If the spec doesn't say what to do, produce an error. Do not add implicit intelligence, type coercion, data source inference, or "helpful" guessing. The prose IS the program. (v1c §52)

3. **No direct I/O in the core.** The interpreter, parser, analyzer, and lexer return data. Only `cli.py` calls `input()` or `print()`. (v1d §64)

4. **Test before advancing.** Each phase's gate must pass before starting the next phase. Do not build the parser before the lexer tests pass.

5. **Structured results everywhere.** Every function that can fail returns an InscriptResult. No bare exceptions, no print-and-exit, no silent failures.

6. **The vocabulary is the boundary.** 29 reserved words. 7 verbs. 9 connectives. 5 operators (including multi-word `equal to`). 3 articles. 1 delimiter. Nothing else enters the language in v1.

---

## INITIAL CLAUDE CODE PROMPT

Copy this as the first message to Claude Code after setup:

```
Read BUILD_PLAN.md and all files in docs/spec/ before writing any code. This is the
Inscript Programming Language v1 interpreter — a prose-as-syntax language designed by
the project architect (Rob). You are the builder. All design decisions are locked in the
five spec documents. Do not invent behavior the spec doesn't define. Do not guess — read.

Start with Phase 1 (vocabulary.py and result.py). After each phase, run the tests and
show me the results before moving to the next phase.
```

---

*This build plan translates five specification documents and 48 test sentences into seven phases of concrete Python implementation. Build exactly what the documents say. Build less than they inspire you to build.*
