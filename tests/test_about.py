"""Tests for the `about` declaration — Meta-Structural Era (MS-Q1).

`about` is a declaration (TokenType.DECLARATION), a new grammatical
category distinct from verbs and connectives. It declares the program's
topic as inert metadata: single, first-line-only, stored on the manifest
(not the symbol table) and never executed.
"""

import io
import json

import pytest

from liminate.build import BuildManifest, _validate_and_render
from liminate.cli import Session, run_file
from liminate.inspect_cmd import format_manifest
from liminate.lexer import tokenize
from liminate.parser import AboutNode, _ParseError, parse, parse_about
from liminate.renderer import render
from liminate.result import ResultStatus
from liminate.vocabulary import (
    ALL_RESERVED,
    DECLARATIONS,
    TOMBSTONES,
    TokenType,
    reserved_category,
)


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


def test_about_tokenizes_as_declaration():
    tokens = tokenize("about")
    assert len(tokens) == 1
    assert tokens[0].type is TokenType.DECLARATION
    assert tokens[0].value == "about"


def test_about_full_line_tokenizes_with_trailing_tokens():
    tokens = tokenize("about expense authorization")
    assert [(t.type, t.value, t.position) for t in tokens] == [
        (TokenType.DECLARATION, "about", 0),
        (TokenType.UNKNOWN, "expense", 6),
        (TokenType.UNKNOWN, "authorization", 14),
    ]


def test_about_with_quoted_string_tokenizes():
    tokens = tokenize('about "expense authorization"')
    assert tokens[0].type is TokenType.DECLARATION
    assert tokens[1].type is TokenType.QUOTED_STRING
    assert tokens[1].value == "expense authorization"
    assert len(tokens) == 2


def test_about_is_case_insensitive():
    # The lexer lowercases words before classification.
    tokens = tokenize("ABOUT expense")
    assert tokens[0].type is TokenType.DECLARATION
    assert tokens[0].value == "about"


# ---------------------------------------------------------------------------
# parse_about
# ---------------------------------------------------------------------------


def test_parse_about_quoted_topic():
    node = parse_about(tokenize('about "expense authorization"'))
    assert node == AboutNode(topic="expense authorization")


def test_parse_about_bare_word_topic():
    node = parse_about(tokenize("about expense-authorization"))
    assert node == AboutNode(topic="expense-authorization")


def test_parse_about_multi_word_bare_topic():
    node = parse_about(tokenize("about expense authorization policy"))
    assert node == AboutNode(topic="expense authorization policy")


def test_parse_about_empty_raises():
    with pytest.raises(_ParseError):
        parse_about(tokenize("about"))


def test_parse_about_quoted_with_trailing_raises():
    with pytest.raises(_ParseError):
        parse_about(tokenize('about "expense" extra'))


def test_parse_about_non_about_line_returns_none():
    assert parse_about(tokenize("remember a string called x with 5")) is None


def test_parse_about_empty_token_list_returns_none():
    assert parse_about([]) is None


def test_parse_about_number_in_topic():
    node = parse_about(tokenize("about version 2"))
    assert node == AboutNode(topic="version 2")


# ---------------------------------------------------------------------------
# Rejection in the normal parse pipeline
# ---------------------------------------------------------------------------


def test_about_rejected_in_normal_parse_pipeline():
    result = parse(tokenize("about expense authorization"))
    assert result.status is ResultStatus.ERROR_PARSE
    assert "declaration" in result.message
    assert "first line" in result.message


def test_about_as_midprogram_statement_errors():
    # Reaching _parse_one_operation with a DECLARATION token must error.
    result = parse(tokenize("about something"))
    assert result.status is ResultStatus.ERROR_PARSE


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


def test_about_in_all_reserved():
    assert "about" in ALL_RESERVED


def test_about_in_declarations():
    # Definitional Era (v31) added `define` as the second declaration.
    assert DECLARATIONS == frozenset({"about", "define"})


def test_reserved_category_about_is_declaration():
    assert reserved_category("about") == "declaration"


def test_all_reserved_count_is_58():
    # Meta-Structural Era batch 3 added the `inherited` operator (53 → 54).
    # Deontic Era added the `forbid` verb (54 → 55).
    # Deontic Era batch 2 added the `permit` verb (55 → 56).
    # Temporal-Boundary Era added `starting`/`until` (56 → 58).
    # v25 added `highest`/`lowest` operators (58 → 60 counted) plus the
    # tombstoned `combine` (+1 uncounted).
    # Definitional Era (v31) added the `define` declaration (60 → 61
    # counted). Raw ALL_RESERVED (including the uncounted tombstone) is
    # 62 — use len(ALL_RESERVED) - len(TOMBSTONES) for the public count.
    assert len(ALL_RESERVED) - len(TOMBSTONES) == 61


def test_about_cannot_be_used_as_variable_name():
    session = Session()
    result = session.run_line("remember a string called about with 5")
    assert result.status is ResultStatus.ERROR_PARSE
    assert "reserved" in result.message
    assert "declaration" in result.message


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


def test_render_about_quotes_multi_word_topic():
    assert render(AboutNode(topic="expense authorization")) == (
        'about "expense authorization"'
    )


def test_render_about_bare_single_word_topic():
    assert render(AboutNode(topic="expense-authorization")) == (
        "about expense-authorization"
    )


# ---------------------------------------------------------------------------
# Integration — run_file
# ---------------------------------------------------------------------------


def _run(tmp_path, source, **kwargs):
    p = tmp_path / "prog.limn"
    p.write_text(source, encoding="utf-8")
    out = io.StringIO()
    run_file(str(p), out=out, **kwargs)
    return out.getvalue()


def test_program_with_about_first_line_executes(tmp_path):
    source = (
        'about "expense authorization"\n'
        "remember a number called budget with 50000\n"
        "show budget\n"
    )
    output = _run(tmp_path, source, quiet=True)
    assert "50000" in output
    # The topic is not stored as a symbol and never shown as data.
    assert "expense authorization" not in output


def test_program_without_about_executes(tmp_path):
    source = (
        "remember a number called budget with 50000\n"
        "show budget\n"
    )
    output = _run(tmp_path, source, quiet=True)
    assert "50000" in output


def test_program_with_duplicate_about_errors(tmp_path):
    source = (
        'about "first topic"\n'
        "remember a number called budget with 50000\n"
        "show budget\n"
        'about "second topic"\n'
    )
    output = _run(tmp_path, source, quiet=True)
    assert "Error:" in output
    assert "Only one 'about' declaration is allowed" in output


def test_about_after_comment_works(tmp_path):
    source = (
        "-- a leading comment\n"
        "-- another comment\n"
        'about "expense authorization"\n'
        "remember a number called budget with 50000\n"
        "show budget\n"
    )
    output = _run(tmp_path, source, quiet=True)
    assert "50000" in output
    assert "Error:" not in output


def test_about_on_non_first_statement_line_errors(tmp_path):
    source = (
        "remember a number called budget with 50000\n"
        'about "too late"\n'
    )
    output = _run(tmp_path, source, quiet=True)
    assert "Error:" in output


def test_topic_not_stored_in_symbol_table(tmp_path):
    # Invariant §9.4 — the `about` topic is metadata, never a symbol.
    # Drive run_file end-to-end, then confirm a `show` of the topic
    # words errors (no symbol of that name exists).
    source = (
        'about "expense authorization"\n'
        "remember a number called budget with 50000\n"
        "show budget\n"
        "show expense\n"
    )
    output = _run(tmp_path, source, quiet=True)
    # `budget` resolves; `expense` does not — it was never stored.
    assert "50000" in output
    assert "I can't find 'expense'" in output


# ---------------------------------------------------------------------------
# Inspect / manifest
# ---------------------------------------------------------------------------


def _manifest_for(source):
    canonical, _, topic = _validate_and_render(source)
    return BuildManifest(
        liminate_version="0.5.0",
        source_filename="prog.limn",
        source_text=source,
        canonical=canonical,
        packs=[],
        vocabulary_in_use={"verbs": [], "connectives": [], "operators": []},
        topic=topic,
    ).as_dict()


def test_manifest_includes_topic_when_about_present():
    m = _manifest_for(
        'about "expense authorization"\n'
        "remember a number called budget with 50000\n"
    )
    assert m["topic"] == "expense authorization"
    plain = format_manifest(m)
    assert "Topic: expense authorization" in plain
    assert json.loads(format_manifest(m, as_json=True))["topic"] == (
        "expense authorization"
    )


def test_manifest_omits_topic_when_about_absent():
    m = _manifest_for("remember a number called budget with 50000\n")
    assert m["topic"] is None
    plain = format_manifest(m)
    assert "Topic:" not in plain
    assert json.loads(format_manifest(m, as_json=True))["topic"] is None


def test_build_validate_extracts_topic():
    canonical, asts, topic = _validate_and_render(
        'about "expense authorization"\n'
        "remember a number called budget with 50000\n"
    )
    assert topic == "expense authorization"
    # The `about` line is consumed, not rendered as a statement.
    assert "remember a number called budget with 50000" in canonical


def test_build_validate_duplicate_about_raises():
    from liminate.build import BuildError

    with pytest.raises(BuildError):
        _validate_and_render(
            'about "first"\n'
            "remember a number called b with 1\n"
            'about "second"\n'
        )


# ---------------------------------------------------------------------------
# Failure-mode guard: `about` inside a when action block is rejected
# ---------------------------------------------------------------------------


def test_about_in_when_action_block_errors(tmp_path):
    source = (
        "remember a number called level with 100\n"
        "when level is above 50\n"
        '  about "nope"\n'
    )
    output = _run(tmp_path, source, quiet=True)
    assert "Error:" in output
