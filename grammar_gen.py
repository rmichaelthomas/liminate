#!/usr/bin/env python3
"""grammar_gen.py — generates grammar/rules.json, grammar/errors.json, and
grammar/encodability.json from the actual source under src/liminate/.

Ported from the Planes `grammar/` architecture (planes:grammar/README.md,
ruling D2: "A hand-written grammar file goes stale silently, and a stale
specification is worse than none"). vocabulary.py is not projected here —
it is already hand-edited source of truth and already code, so a
vocabulary.json would be a second copy of something with no drift problem
(see grammar/README.md).

  python3 grammar_gen.py            regenerate all three files
  python3 grammar_gen.py --check    regenerate into memory, diff against
                                     the committed files, print the diff,
                                     exit non-zero on any difference

Never writes to grammar/vocabulary.py or anything outside grammar/rules.json,
grammar/errors.json, and grammar/encodability.json.
"""
from __future__ import annotations

import ast
import difflib
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO, "src", "liminate")
GRAMMAR_DIR = os.path.join(REPO, "grammar")
RULES_PATH = os.path.join(GRAMMAR_DIR, "rules.json")
ERRORS_PATH = os.path.join(GRAMMAR_DIR, "errors.json")
ENCODABILITY_PATH = os.path.join(GRAMMAR_DIR, "encodability.json")
PARSER_PATH = os.path.join(SRC_DIR, "parser.py")
CHECKER_PATH = os.path.join(SRC_DIR, "checker.py")


# ================================================================ shared helpers

def _string_template(node):
    """From a string-producing AST node, a (template, slots) pair:
    `template` has each f-string interpolation rendered as `{expr text}`,
    `slots` is the list of those expr texts in order. (None, []) if `node`
    is not a literal string or an f-string this can read."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, []
    if isinstance(node, ast.JoinedStr):
        parts, slots = [], []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(str(v.value))
            elif isinstance(v, ast.FormattedValue):
                expr_text = ast.unparse(v.value)
                slots.append(expr_text)
                parts.append("{" + expr_text + "}")
        return "".join(parts), slots
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        lt, ls = _string_template(node.left)
        rt, rs = _string_template(node.right)
        if lt is not None and rt is not None:
            return lt + rt, ls + rs
    return None, []


def _enclosing_function(tree, lineno):
    """Name of the innermost function/method containing source line
    `lineno`, or None at module level."""
    best = None
    best_span = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            if node.lineno <= lineno <= end:
                span = end - node.lineno
                if best_span is None or span < best_span:
                    best, best_span = node.name, span
    return best


def repo_src_files():
    """Every .py file directly under src/liminate/, in a stable order —
    mechanical, not a hand-picked subset. Confirmed empirically while
    writing this generator that only 9 of these files contain any raise
    site of the target error classes (parser.py, analyzer.py,
    interpreter.py, adapter.py, build.py, cli.py, lexer.py, listener.py,
    renderer.py) — run.py, reorderer.py, result.py, vocabulary.py,
    inspect_cmd.py, checker.py, __init__.py, and __main__.py have none —
    but the scan itself makes no assumption about which files those are."""
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(SRC_DIR, "*.py")))


# ================================================================ B.2: grammar/errors.json
#
# The inclusion rule: an entry is every construction of one of the classes
# below, found by walking the AST of every .py file directly under
# src/liminate/ — not by regex, and not by a hand-picked file list (see
# repo_src_files above). Every one of these classes takes its message as a
# single positional argument (confirmed against each class's __init__ /
# each builtin's usage in this repo) — unlike Planes' PlanesError, none of
# them carry a tag or a fix clause, and Liminate's raise sites never pass
# the message as a keyword (grepped `message=` against every target class
# across src/liminate/*.py: zero matches). That absence is real, not an
# oversight in this generator, and is recorded in errors.json's own header
# rather than inventing a tag index Liminate's errors do not have.
TARGET_EXCEPTIONS = (
    "_ParseError",
    "_SemanticError",
    "_RuntimeError",
    "BuildError",
    "LexError",
    "ValueError",
    "RuntimeError",
    "TypeError",
)

_ERRORS_NOTE = (
    "Every construction of _ParseError, _SemanticError, _RuntimeError, "
    "BuildError, LexError, ValueError, RuntimeError, or TypeError found by "
    "walking the AST of every .py file directly under src/liminate/. "
    "Liminate's errors carry no tag field -- unlike Planes' errors.json, "
    "there is no tags index here grouping entries by a shared identifier, "
    "because there is no shared identifier to group by. An id is assigned "
    "per entry (file.class.function[-N]) purely so a reader has something "
    "stable to point at; it is not a tag the source declares."
)


def _extract_error_entries(fname, tree):
    entries = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id in TARGET_EXCEPTIONS):
            continue
        cls = node.func.id
        args = node.args
        message_node = args[0] if args else None
        if message_node is None:
            kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            message_node = kwargs.get("message")

        raised_in = _enclosing_function(tree, node.lineno)
        template, slots = (None, []) if message_node is None else _string_template(message_node)

        entry = {
            "id": f"{fname[:-3]}.{cls}",
            "class": cls,
            "source": f"{fname}:{node.lineno}",
            "raised_in": raised_in,
            "template": template,
            "slots": slots,
        }
        if template is None:
            entry["note"] = (
                "message is not a literal string or f-string at the call "
                "site (built elsewhere, or no message argument found)"
            )
        entries.append(entry)
    return entries


def _entry_line(entry):
    return int(entry["source"].rsplit(":", 1)[1])


def generate_errors():
    all_entries = []
    for fname in repo_src_files():
        path = os.path.join(SRC_DIR, fname)
        with open(path, encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src, filename=fname)
        per_file = _extract_error_entries(fname, tree)
        per_file.sort(key=_entry_line)
        all_entries.extend(per_file)

    # Disambiguate ids: file.class first, then the enclosing function
    # (promoting data the entry already carries, `raised_in`, rather than
    # inventing a key), and only then a running count assigned in the
    # source-order the entries were already collected in above -- so a
    # later raise site sharing the same (file, class, function) gets a
    # stable suffix rather than one that shifts if an earlier site is
    # edited. Mirrors Planes' grammar_gen.py's own id-collision reasoning.
    for e in all_entries:
        if e.get("raised_in"):
            e["id"] = f"{e['id']}.{e['raised_in']}"
    counters = {}
    for e in all_entries:
        counters[e["id"]] = counters.get(e["id"], 0) + 1
    seen = {}
    for e in all_entries:
        base = e["id"]
        if counters[base] > 1:
            seen[base] = seen.get(base, 0) + 1
            e["id"] = f"{base}-{seen[base]}"

    literal_count = sum(1 for e in all_entries if e["template"] is not None and not e["slots"])
    return {
        "format": 1,
        "generated_by": "grammar_gen.py",
        "note": _ERRORS_NOTE,
        "count": len(all_entries),
        "literal_message_count": literal_count,
        "entries": all_entries,
    }


# ================================================================ B.3: grammar/encodability.json

FINDING_KIND_NAMES = (
    "always_deny",
    "constant_predicate",
    "dead_forbid",
    "dead_permit",
    "inconclusive",
    "redundant_forbid",
    "require_forbid_conflict",
    "unless_swallows_rule",
)

ENCODER_EXCEPTION_CLASSES = ("UnencodableConstruct", "NonlinearArithmetic")

_ENCODABILITY_NOTE = (
    "What src/liminate/checker.py's Z3 satisfiability checker (check_source / "
    "check_agreement) can and cannot encode. rules.json describes what the "
    "parser ACCEPTS; this file describes what the checker can ENCODE -- a "
    "narrower, later-stage question. Neither file says anything about what a "
    "condition MEANS at runtime (that is interpreter.py, not covered by any "
    "file in grammar/)."
)

_UNENCODABLE_REASON_NOTE = (
    "checker.py's own UnencodableStatement.reason field is declared "
    "`reason: str  # str(exc) from the caught exception` -- the reason "
    "recorded for a statement the checker could not encode is a "
    "stringified Python exception message, not a value drawn from a fixed "
    "set. This file cannot enumerate the possible reasons because the "
    "source does not define a bounded set of them: every `raised_at` site "
    "below constructs its message from an f-string built at the point of "
    "failure (interpolating the actual node, name, or operator involved), "
    "so the same raise site produces a different reason string for every "
    "different unencodable construct it sees. An agent consuming this file "
    "should treat `reason` as free text to display, never as a value to "
    "match against a known list."
)


def _extract_finding_kinds(tree):
    kinds = []
    seen_sites = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "Finding"):
            continue
        kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
        kind_node = kwargs.get("kind")
        if not (isinstance(kind_node, ast.Constant) and isinstance(kind_node.value, str)):
            continue
        kind = kind_node.value
        if kind not in FINDING_KIND_NAMES:
            continue
        site = ("checker.py", node.lineno)
        if site in seen_sites:
            continue
        seen_sites.add(site)
        kinds.append({"kind": kind, "source": f"checker.py:{node.lineno}", "_line": node.lineno})
    kinds.sort(key=lambda k: k["_line"])
    for k in kinds:
        del k["_line"]
    return kinds


def _extract_encoder_exceptions(tree):
    class_defs = {}
    raise_sites = {cls: [] for cls in ENCODER_EXCEPTION_CLASSES}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in ENCODER_EXCEPTION_CLASSES:
            class_defs[node.name] = f"checker.py:{node.lineno}"
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in ENCODER_EXCEPTION_CLASSES):
            raise_sites[node.func.id].append(node.lineno)
    out = []
    for cls in ENCODER_EXCEPTION_CLASSES:
        out.append({
            "class": cls,
            "defined_at": class_defs.get(cls),
            "raised_at": [f"checker.py:{ln}" for ln in sorted(raise_sites[cls])],
        })
    return out


def _extract_unencodable_reason_source(tree):
    """The exact `checker.py:<line>` pointer for UnencodableStatement's
    `reason` field declaration, so the honesty note above is checkable
    against the real source rather than just asserted."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "UnencodableStatement":
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) \
                        and stmt.target.id == "reason":
                    return f"checker.py:{stmt.lineno}"
    return None


def generate_encodability():
    with open(CHECKER_PATH, encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src, filename="checker.py")

    finding_kinds = _extract_finding_kinds(tree)
    found_kind_names = {k["kind"] for k in finding_kinds}
    missing = [k for k in FINDING_KIND_NAMES if k not in found_kind_names]

    return {
        "format": 1,
        "generated_by": "grammar_gen.py",
        "note": _ENCODABILITY_NOTE,
        "finding_kinds": finding_kinds,
        "finding_kinds_missing_from_source": missing,
        "encoder_exceptions": _extract_encoder_exceptions(tree),
        "unencodable_reason_is_not_a_bounded_vocabulary": {
            "source": _extract_unencodable_reason_source(tree),
            "explanation": _UNENCODABLE_REASON_NOTE,
        },
    }


# ================================================================ B.1 / B.4: grammar/rules.json

def _all_top_level_function_names(tree):
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def _is_parse_function_name(name):
    """The inclusion rule for B.1's 'one entry per parse function': the
    bare name (stripping at most one leading underscore) is exactly
    'parse' or starts with 'parse_'. A plain prefix rule, not a semantic
    judgment about which helpers 'really' parse -- e.g. _parse_number(s:
    str) matches by name despite taking a plain string, not a token
    stream, and is included for that reason: this is a name-based
    inventory, not a hand-curated one. Verified against the installed
    parser.py: this rule yields exactly 48 functions, 28 with a
    docstring, matching this build's own provenance figures."""
    bare = name[1:] if name.startswith("_") else name
    return bare == "parse" or bare.startswith("parse_")


def _parse_function_docstring_surface(node):
    """The function's own first paragraph (up to the first blank line),
    joined onto one line. None (never invented) when there is no
    docstring at all -- e.g. _parse_simple_condition at the time this
    generator was written (parser.py:3117 in the 0.18.1 line), the exact
    function Build C exists to fix."""
    doc = ast.get_docstring(node)
    if not doc:
        return None
    doc = doc.strip()
    paragraph = doc.split("\n\n", 1)[0]
    joined = " ".join(line.strip() for line in paragraph.split("\n")).strip()
    return joined or None


def _calls_within(node, known_names):
    """Names of other module-level functions this function calls directly
    (bare-name calls -- parser.py's parse functions are plain module-level
    functions taking `stream: TokenStream` explicitly, not `self.X()`
    methods the way Planes' class-based parser is), restricted to names
    this module actually defines, in first-seen order, excluding
    self-calls. Every call anywhere in the body, conditional or not --
    the full picture for a form's own rules.json entry."""
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            name = n.func.id
            if name in known_names and name != node.name and name not in out:
                out.append(name)
    return out


def _unconditional_calls_within(node, known_names):
    """Like _calls_within, but only calls reached on EVERY execution of
    the function -- skips entirely into any `if`/`elif`/`else` branch, so
    a call that exists only as one special case among several (e.g.
    _parse_simple_condition's call to _parse_extrema, reached only when
    the field is a `highest`/`lowest` selector) is not mistaken for the
    function's one true successor.

    This distinction is precedence-ladder-specific (used only by
    _precedence_ladder, never for a form's own `calls` field): the ladder
    asks "which single form does this one always hand off to," and a
    conditional special case is a fork, not a hand-off, even when it is
    the only OTHER form-level call the function happens to make. Skipping
    is why this is necessary: _parse_simple_condition's fallthrough call
    to _finish_simple_condition (itself not a form, filtered out
    downstream in _precedence_ladder's successors()) sits after all of
    its if/elif/else branches at the function's own body level and so
    still counts as unconditional; _parse_extrema, nested inside one of
    those branches, does not -- which is exactly what makes the
    conditions chain stop at _parse_simple_condition rather than walking
    one level further into a special case that only sometimes fires."""
    out = []

    def walk(n):
        for child in ast.iter_child_nodes(n):
            if isinstance(child, ast.If):
                continue
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                name = child.func.id
                if name in known_names and name != node.name and name not in out:
                    out.append(name)
            walk(child)

    walk(node)
    return out


def _opens_with_tokens(node):
    """Token/type names this function's own body tests for at its start
    (`stream.at("X")` / `peek.type is TokenType.X` / `stream.expect("X")`),
    best-effort -- a form inventory (B.1), not a formal FIRST-set
    derivation."""
    out = []
    for n in ast.walk(node):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("at", "accept", "expect")
                and n.args and isinstance(n.args[0], ast.Constant)
                and isinstance(n.args[0].value, str)):
            kind = n.args[0].value
            if kind not in out:
                out.append(kind)
        if (isinstance(n, ast.Compare) and isinstance(n.left, ast.Attribute)
                and n.left.attr == "type" and len(n.ops) == 1
                and isinstance(n.ops[0], ast.Is)):
            comparator = n.comparators[0]
            if (isinstance(comparator, ast.Attribute)
                    and isinstance(comparator.value, ast.Name)
                    and comparator.value.id == "TokenType"):
                kind = comparator.attr
                if kind not in out:
                    out.append(kind)
    return out


def _produces_node_type(node):
    """The AST node type constructed on this function's own `return`
    statements, when it is a single, direct `return SomeNode(...)` shape --
    best-effort; a function with several possible return shapes (or one
    that returns a sub-call's result, or a bare value) reports what it can
    and no more, never a guess."""
    types = []
    for n in ast.walk(node):
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Call) \
                and isinstance(n.value.func, ast.Name):
            name = n.value.func.id
            if name[:1].isupper() and name not in types:
                types.append(name)
    return types


_RULES_NOTE = (
    "A form inventory, not a formal grammar -- deriving a true BNF from "
    "recursive-descent code is not mechanical. One entry per function in "
    "src/liminate/parser.py whose bare name (stripping at most one leading "
    "underscore) is 'parse' or starts with 'parse_' -- see "
    "_is_parse_function_name in this generator for the exact rule and why "
    "_parse_number is included despite taking a plain string, not a token "
    "stream."
)

_PRECEDENCE_NOTE = (
    "The binding order of one chain of forms, loosest first, derived by "
    "walking `calls` from the named start and following the single-"
    "successor edge at each step -- the one structure an agent needs that "
    "an unordered call graph does not carry. It is not a grammar: it says "
    "which level binds tighter than which, and nothing about what either "
    "level accepts. The walk stops where a form's successors stop being "
    "exactly one, so the last level named is the tightest one on a linear "
    "chain, not necessarily the last form the parser has. If a chain ever "
    "branches this entire ladder is ABSENT rather than wrong, with the "
    "reason stated -- a guessed ladder would be the hand-written grammar "
    "ruling D2 declined, reached by a different route. Liminate has two "
    "independent chains (conditions, values); they are two separate "
    "entries below, never merged into one ladder."
)

PRECEDENCE_CHAINS = [
    {"name": "conditions", "start": "_parse_or_condition"},
    {"name": "values", "start": "_parse_value"},
]


def _precedence_ladder(forms, start, unconditional_calls):
    """(levels, why_not) for one chain starting at `start` -- the linear
    walk through each form's UNCONDITIONAL calls only (see
    _unconditional_calls_within), restricted to successors that are
    themselves forms in this inventory. Returns (None, reason) the
    instant the walk is not linear, so the caller emits nothing for that
    chain rather than guessing."""
    by_method = {f["parser_method"]: f for f in forms}
    if start not in by_method:
        return None, f"`{start}` is not among the parser's forms, so there is no chain to walk from"

    def successors(method):
        return [c for c in unconditional_calls[method] if c in by_method]

    chain = [start]
    seen = {start}
    while True:
        here = chain[-1]
        nxt = successors(here)
        if len(nxt) != 1:
            break
        if nxt[0] in seen:
            return None, f"the walk from `{start}` revisits `{nxt[0]}`, so the chain is a cycle rather than a ladder"
        chain.append(nxt[0])
        seen.add(nxt[0])

    if len(chain) < 2:
        return None, f"`{start}` does not have exactly one form-level successor, so no ladder starts there"
    return [by_method[m]["form"] for m in chain], None


def generate_rules():
    with open(PARSER_PATH, encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src, filename="parser.py")

    all_names = _all_top_level_function_names(tree)

    forms = []
    unconditional_calls = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if not _is_parse_function_name(node.name):
            continue
        bare = node.name[1:] if node.name.startswith("_") else node.name
        produces = _produces_node_type(node)
        forms.append({
            "form": bare,
            "parser_method": node.name,
            "opens_with": _opens_with_tokens(node),
            "produces": produces[0] if len(produces) == 1 else produces,
            "calls": _calls_within(node, all_names),
            "source": f"parser.py:{node.lineno}",
            "surface": _parse_function_docstring_surface(node),
        })
        unconditional_calls[node.name] = _unconditional_calls_within(node, all_names)

    forms.sort(key=lambda f: int(f["source"].split(":")[1]))

    precedence = []
    for chain in PRECEDENCE_CHAINS:
        levels, why_not = _precedence_ladder(forms, chain["start"], unconditional_calls)
        if levels is None:
            precedence.append({
                "name": chain["name"],
                "start": chain["start"],
                "emitted": False,
                "reason": why_not,
            })
        else:
            precedence.append({
                "name": chain["name"],
                "derived_from": "calls",
                "start": chain["start"],
                "loosest_first": levels,
                "emitted": True,
            })

    doc = {
        "format": 1,
        "generated_by": "grammar_gen.py",
        "note": _RULES_NOTE,
        "count": len(forms),
        "docstring_count": sum(1 for f in forms if f["surface"] is not None),
        "precedence_note": _PRECEDENCE_NOTE,
        "precedence": precedence,
        "forms": forms,
    }
    return doc


# ================================================================ CLI

def _write(path, doc):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=False)
        f.write("\n")


def _read_existing(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def main():
    check = "--check" in sys.argv

    rules_doc = generate_rules()
    errors_doc = generate_errors()
    encodability_doc = generate_encodability()

    rules_text = json.dumps(rules_doc, indent=2) + "\n"
    errors_text = json.dumps(errors_doc, indent=2) + "\n"
    encodability_text = json.dumps(encodability_doc, indent=2) + "\n"

    if not check:
        os.makedirs(GRAMMAR_DIR, exist_ok=True)
        _write(RULES_PATH, rules_doc)
        _write(ERRORS_PATH, errors_doc)
        _write(ENCODABILITY_PATH, encodability_doc)
        print(f"wrote {RULES_PATH} ({rules_doc['count']} forms, "
              f"{rules_doc['docstring_count']} with a docstring)")
        print(f"wrote {ERRORS_PATH} ({errors_doc['count']} entries)")
        print(f"wrote {ENCODABILITY_PATH} "
              f"({len(encodability_doc['finding_kinds'])} finding kinds, "
              f"{len(encodability_doc['encoder_exceptions'])} encoder exception classes)")
        return 0

    diffs = 0
    for path, generated, label in (
            (RULES_PATH, rules_text, "grammar/rules.json"),
            (ERRORS_PATH, errors_text, "grammar/errors.json"),
            (ENCODABILITY_PATH, encodability_text, "grammar/encodability.json")):
        existing = _read_existing(path)
        if existing == generated:
            print(f"{label}: up to date")
            continue
        diffs += 1
        print(f"{label}: OUT OF DATE — regenerate with python3 grammar_gen.py")
        existing_lines = (existing or "").splitlines(keepends=True)
        generated_lines = generated.splitlines(keepends=True)
        diff = difflib.unified_diff(
            existing_lines, generated_lines,
            fromfile=f"{label} (committed)", tofile=f"{label} (generated)",
        )
        sys.stdout.writelines(diff)

    if diffs:
        print(f"\n{diffs} check(s) failed.")
    return diffs


if __name__ == "__main__":
    sys.exit(main())
