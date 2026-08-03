# grammar/

Machine-checkable projections of the parser's real surface, ported from the
Planes `grammar/` architecture (`planes:grammar/README.md`, ruling D2). Three
files live here, and they are not interchangeable:

| File | What it is | Hand-edited or generated |
|---|---|---|
| `rules.json` | A **form inventory**, not a formal grammar — one entry per function in `src/liminate/parser.py` whose bare name is `parse` or starts with `parse_`: what token/type it opens with, what AST node it produces, what other functions it calls, and the surface form from that function's own docstring. Also carries the binding-order ladder for the two expression precedence chains (conditions, values), each derived independently by walking `calls`. Deriving a true BNF from recursive-descent code is not mechanical; this is what can honestly be generated instead. | **Generated** by `grammar_gen.py`. Never hand-edit. |
| `errors.json` | Every construction of `_ParseError`, `_SemanticError`, `_RuntimeError`, `BuildError`, `LexError`, `ValueError`, `RuntimeError`, or `TypeError` under `src/liminate/`, found by walking the AST of every `.py` file there — not by regex. | **Generated** by `grammar_gen.py`. Never hand-edit. |
| `encodability.json` | What `src/liminate/checker.py`'s Z3 checker can and cannot encode: the eight finding kinds `check_source`/`check_agreement` can report, the exception classes the encoder catches when a statement fails to encode, and their raise sites. | **Generated** by `grammar_gen.py`. Never hand-edit. |

`vocabulary.py` is not projected here. It is already hand-edited source of
truth and already code — a `vocabulary.json` would be a second copy of
something with no drift problem to guard against (see "Why the split"
below).

## Why the split (ported from Planes ruling D2)

Making the grammar itself the source of truth would mean writing a parser
generator — a rewrite, not a tier. So *vocabulary* stays source-of-truth
data living in code, and *production rules, error templates, and
encodability data* are projections: generated from the actual source and
checked in CI so they cannot go stale silently. A hand-written grammar file
goes stale silently, and a stale specification is worse than none.

Deleting `rules.json`, `errors.json`, or `encodability.json` changes no
program's output, no test result, and no interpreter behavior — they are
pure projections of the real source, regenerable at any time with
`python3 grammar_gen.py`.

## What this directory does NOT cover — read this before trusting a file here

Each file answers a narrower question than "how does Liminate work," and
none of them overlap the way that phrase suggests:

- **`rules.json` describes what the parser ACCEPTS.** It says nothing
  about what a condition *means* once parsed — that is
  `src/liminate/interpreter.py`, not covered by any file in this
  directory. A form appearing here with a given `produces` node type is a
  claim about parsing, not about evaluation.
- **`encodability.json` covers the checker** (`src/liminate/checker.py`'s
  Z3-based `check_source`/`check_agreement`), a narrower, later-stage
  question than parsing: a statement the parser accepts can still be
  unencodable to the checker. `encodability.json`'s own
  `unencodable_reason_is_not_a_bounded_vocabulary` field states plainly
  that the checker's per-statement failure `reason` is a stringified
  Python exception, not a value drawn from a fixed set — this file cannot
  enumerate the possible reasons, only the exception classes and their
  raise sites.
- **`errors.json` covers what raises and what its message says** — not
  when it fires at runtime, and not whether a given raise site is
  reachable from a given program. It is a catalogue of constructions,
  not a coverage or reachability analysis.
- **Nothing in this directory covers evaluation semantics.** If you need
  to know what a parsed program *does*, read `interpreter.py` directly;
  no generated file here is a substitute for it.

## `rules.json`'s inclusion rule for "parse function"

A function belongs in the inventory iff its bare name (stripping at most
one leading underscore) is exactly `parse` or starts with `parse_` — a
name-based rule, not a semantic judgment about which helpers "really"
parse. This is why `_parse_number(s: str)` (which parses a numeric
*string*, not a token stream) is included alongside every function that
consumes a `TokenStream`: the rule is honest about being a name filter, not
an attempt to distinguish "real" parse functions from "helper" ones by
reading intent into the code. See `_is_parse_function_name` in
`grammar_gen.py` for the exact check.

## The precedence ladders, and why there are two

Liminate's parser has two independent recursive-descent precedence chains
— conditions (`_parse_or_condition` → `_parse_and_condition` →
`_parse_simple_condition`) and values (`_parse_value` → `_parse_additive` →
`_parse_multiplicative` → `_parse_atom`) — derived by walking each form's
*unconditional* calls (calls reached on every execution of the function,
not one special case among several) from a named start, following the
single-successor edge at each step. **They are two separate entries in
`rules.json`'s `precedence` array, never merged into one ladder** — a form
in one chain binding "tighter" or "looser" than a form in the other is not
a claim this file makes.

The conditions chain stops at `_parse_simple_condition` deliberately: that
function's only *unconditional* form-level successor is not itself a form
(`_finish_simple_condition`, which does not match the `parse`/`parse_*`
name rule above), and its call to `_parse_extrema` — the other form-level
call in its body — exists only inside one conditional branch (the
`highest`/`lowest` selector special case), not on every execution. A
naive walk that counted every call anywhere in the function body, ignoring
whether it sits inside a branch, would have continued the chain one level
too far, into a special case rather than a true precedence level — the
guessed ladder ruling D2 exists to refuse, reached by a different route.
If a future parser change ever makes a chain genuinely branch (more than
one unconditional form-level successor, or none), `_precedence_ladder`
emits nothing for that chain rather than a guess, with the reason stated
in `rules.json` itself.

## Regenerating

```bash
python3 grammar_gen.py            # regenerate all three files
python3 grammar_gen.py --check    # regenerate into memory, diff against the
                                   # committed files, exit non-zero on any
                                   # difference — this is the CI gate
```

`grammar_gen.py --check` never writes anything; it only reads and diffs.
