"""The corpus must cover the surface it claims to.

The existing parity gate (`@liminate/ts-validator`, `tests/conformance.test.ts`)
compares the two implementations' reserved-word lists against a frozen fixture.
It stayed green while three minor versions of behaviour diverged, because the
thing that diverged changed no word: v29 added `date` to `_require_comparable`,
so date ranges became expressible and the word list did not move. Downstream,
`commongage` carried a comment recording that limit for two months after it was
gone.

A behavioural corpus only fixes that if it keeps up. These tests are what make
it keep up: a reserved word with no case is a piece of surface the corpus
cannot speak about, and adding a word to the vocabulary fails here until a
program using it exists.

Words are not enough on their own, and `require each` is the proof. Both of
its words appear in other programs, so the reserved-word gate was satisfied
while the corpus said nothing whatsoever about the construct — and the
TypeScript port, which does not implement it, showed an empty divergence list
that read as complete coverage. The same was true of the `each` verb, of field
access inside a condition, and of a named composition being called.

So there is a second gate below, over the AST node kinds the parser can
produce. A grammar is not a bag of words, and a gate over words cannot see
one.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from liminate import parser as ast_module
from liminate import vocabulary as vocab

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "fixtures" / "conformance_corpus.txt"
GENERATOR = ROOT / "scripts" / "gen_conformance_corpus.py"


def _version() -> str:
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError("pyproject.toml states no version")


def _corpus_words() -> set[str]:
    text = CORPUS.read_text(encoding="utf-8")
    programs = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("# ")]
    words: set[str] = set()
    for line in programs:
        words.update(line.replace(":", " ").replace(",", " ").split())
    return words


# Words that cannot appear in a corpus program, each with the reason. A word
# with no case and no reason is a hole; a reason that stops being true is
# checked in the other direction below.
UNREACHABLE: dict[str, str] = {
    "about": (
        "a declaration the wrapping `validate()` handles before the per-line "
        "pipeline, and which is an error anywhere the per-line pipeline can "
        "see it — a corpus case would record the refusal, not the behaviour"
    ),
    "when": (
        "a when-block header, which `validate()` buffers with its indented "
        "action lines; the per-line pipeline never sees a complete block"
    ),
}


def test_every_reserved_word_appears_in_a_corpus_program():
    reserved: set[str] = set()
    for name in ("VERBS", "CONNECTIVES", "OPERATORS", "ARTICLES",
                 "MULTI_WORD_RESERVED", "DECLARATIONS"):
        reserved |= set(getattr(vocab, name, set()))
    missing = sorted(reserved - _corpus_words() - set(UNREACHABLE))
    assert not missing, (
        f"{missing} are reserved and no corpus program uses them, so the "
        f"conformance corpus says nothing about how the port handles them"
    )


def test_no_unreachable_entry_has_stopped_being_unreachable():
    """A stale excuse is the same defect as a stale silence."""
    reached = sorted(set(UNREACHABLE) & _corpus_words())
    assert not reached, f"{reached} are excused as unreachable and appear in the corpus"


# Node kinds that no single corpus line can produce, each with the reason.
# Same contract as UNREACHABLE above: no entry without a reason, and no reason
# allowed to go stale.
UNREACHABLE_NODES: dict[str, str] = {
    "AboutNode": (
        "produced only by the `about` declaration, which `validate()` handles "
        "ahead of the per-line pipeline (see UNREACHABLE['about'])"
    ),
    "WhenNode": (
        "produced only from a complete when-block — a header plus its "
        "indented actions — which the per-line pipeline never assembles"
    ),
    "FinishNode": (
        "`finish` outside an event handler is refused by the analyzer "
        "(\'finish\' can only be used inside an event handler), and the "
        "corpus has no handler to put one inside"
    ),
    "PackVerbNode": (
        "produced only when a pack is loaded; the generator runs the bare "
        "language, so no corpus line can reach a pack verb"
    ),
}


def _parser_node_kinds() -> set[str]:
    return {
        name
        for name, obj in vars(ast_module).items()
        if inspect.isclass(obj)
        and issubclass(obj, ast_module.ASTNode)
        and obj is not ast_module.ASTNode
    }


def _corpus_node_kinds() -> set[str]:
    fixture = ROOT / "tests" / "fixtures" / f"conformance-{_version()}.json"
    if not fixture.exists():
        pytest.skip("covered by the fixture-exists test")
    seen: set[str] = set()
    for case in json.loads(fixture.read_text())["cases"]:
        for result in case["results"]:
            seen.update(result.get("nodes") or [])
    return seen


def test_every_parser_node_kind_appears_in_a_corpus_program():
    """The gate a word list cannot be.

    `require each` is why this exists: `require` and `each` both appear in
    other programs, so the word gate was green while the corpus held no case
    for the construct at all, and the port's empty divergence list looked like
    coverage. A node kind with no case is surface the corpus cannot speak
    about, however many of its words are spoken elsewhere.
    """
    missing = sorted(_parser_node_kinds() - _corpus_node_kinds() - set(UNREACHABLE_NODES))
    assert not missing, (
        f"{missing} are node kinds the parser can produce and no corpus "
        f"program produces, so the conformance corpus says nothing about how "
        f"the port handles them"
    )


def test_no_unreachable_node_has_stopped_being_unreachable():
    """A stale excuse is the same defect as a stale silence."""
    reached = sorted(set(UNREACHABLE_NODES) & _corpus_node_kinds())
    assert not reached, (
        f"{reached} are excused as unreachable and the corpus produces them"
    )


def test_every_unreachable_node_is_still_a_node_the_parser_defines():
    """An excuse for a node kind that no longer exists is dead weight that
    would silently stop guarding anything."""
    gone = sorted(set(UNREACHABLE_NODES) - _parser_node_kinds())
    assert not gone, f"{gone} are excused as unreachable but the parser defines no such node"


def test_the_generated_fixture_matches_the_version_it_was_generated_from():
    """The fixture names the version it describes, and the tree has moved
    since only if someone bumped the version without regenerating."""
    fixture = ROOT / "tests" / "fixtures" / f"conformance-{_version()}.json"
    assert fixture.exists(), (
        f"no conformance fixture for version {_version()}; regenerate with "
        f"`python3 scripts/gen_conformance_corpus.py > {fixture.relative_to(ROOT)}`"
    )
    assert json.loads(fixture.read_text())["language_version"] == _version()


def test_the_fixture_is_what_the_generator_produces_today():
    """Regenerating must be a no-op, or the committed parity file describes a
    language this tree no longer is — which is the exact failure this whole
    mechanism exists to stop."""
    fixture = ROOT / "tests" / "fixtures" / f"conformance-{_version()}.json"
    if not fixture.exists():
        pytest.skip("covered by the fixture-exists test")
    fresh = subprocess.run(
        [sys.executable, str(GENERATOR)], capture_output=True, text=True, cwd=ROOT
    )
    assert fresh.returncode == 0, fresh.stderr
    assert json.loads(fresh.stdout) == json.loads(fixture.read_text()), (
        "the committed conformance fixture is stale; regenerate it"
    )
