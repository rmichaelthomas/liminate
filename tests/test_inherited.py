"""Tests for the `inherited` operator + `from` attribution — Meta-Structural
Era batch 3 (MS-Q3/Q4/Q5).

`inherited` is an operator (the 8th single-word operator) — a statement-initial
modifier marking a verb statement as carried forward from a prior context
(session, agent, contract). It is inert provenance metadata stored on the AST
node (`inherited: bool`, `inherited_from: str | None`, both `compare=False`):
visible to rendering and inspect, never executed and never in the symbol table.

Design decisions implemented:
- Overridable (MS-Q3): `inherited` is provenance, not protection — an inherited
  value can be `remove`d or overridden. The audit trail is the protection.
- Reuse `from` (MS-Q4): agent attribution reuses the existing `from` connective,
  scoped to `inherited` statements (statement-final, after any `because`).
- Timer resets (MS-Q5): `inherited weakens` creates a fresh DecayingValue
  (ticks_elapsed=0) — runtime state belongs to the session, not the statement.
"""

import io

from liminate.cli import run_file
from liminate.lexer import tokenize
from liminate.parser import (
    AddNode,
    AssignNode,
    ExpectNode,
    RememberValueNode,
    RequireNode,
    SequenceNode,
    ShowNode,
    SortNode,
    WeakensNode,
    parse,
    parse_when_block,
)
from liminate.renderer import render
from liminate.result import ResultStatus
from liminate.vocabulary import ALL_RESERVED, TokenType, reserved_category


def _ast(source):
    """Parse a single statement, asserting it succeeded (not an error)."""
    result = parse(tokenize(source))
    assert not hasattr(result, "status"), getattr(result, "message", result)
    return result


def _err(source):
    """Parse a single statement, asserting it produced an ERROR_PARSE."""
    result = parse(tokenize(source))
    assert result.status is ResultStatus.ERROR_PARSE, result
    return result


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


def test_inherited_tokenizes_as_operator():
    tokens = tokenize("inherited")
    assert len(tokens) == 1
    assert tokens[0].type is TokenType.OPERATOR
    assert tokens[0].value == "inherited"


def test_inherited_full_line_tokenizes_with_verb():
    tokens = tokenize("inherited require amount is above 50000")
    assert tokens[0].type is TokenType.OPERATOR
    assert tokens[0].value == "inherited"
    assert tokens[1].type is TokenType.VERB
    assert tokens[1].value == "require"


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


def test_inherited_in_all_reserved():
    assert "inherited" in ALL_RESERVED


def test_reserved_category_inherited_is_operator():
    assert reserved_category("inherited") == "operator"


def test_all_reserved_count_is_54():
    assert len(ALL_RESERVED) == 54


# ---------------------------------------------------------------------------
# Parser — `inherited` flag
# ---------------------------------------------------------------------------


def test_inherited_require():
    node = _ast("inherited require amount is above 50000")
    assert isinstance(node, RequireNode)
    assert node.inherited is True
    assert node.inherited_from is None


def test_inherited_remember():
    node = _ast("inherited remember a number called threshold with 1000")
    assert isinstance(node, RememberValueNode)
    assert node.inherited is True


def test_inherited_assign():
    node = _ast("inherited assign review-task to compliance-team")
    assert isinstance(node, AssignNode)
    assert node.inherited is True


def test_inherited_expect():
    node = _ast("inherited expect amount is below 100000")
    assert isinstance(node, ExpectNode)
    assert node.inherited is True


def test_inherited_show():
    node = _ast("inherited show threshold")
    assert isinstance(node, ShowNode)
    assert node.inherited is True


def test_inherited_add():
    node = _ast("inherited add 5 to sizes")
    assert isinstance(node, AddNode)
    assert node.inherited is True


def test_inherited_weakens():
    node = _ast("inherited weakens trust over 10")
    assert isinstance(node, WeakensNode)
    assert node.inherited is True


def test_inherited_sort():
    node = _ast("inherited sort orders by total")
    assert isinstance(node, SortNode)
    assert node.inherited is True


def test_non_inherited_flag_is_false():
    node = _ast("require amount is above 50000")
    assert isinstance(node, RequireNode)
    assert node.inherited is False
    assert node.inherited_from is None


def test_inherited_with_no_verb_errors():
    _err("inherited")


# ---------------------------------------------------------------------------
# Parser — `from` attribution
# ---------------------------------------------------------------------------


def test_inherited_from_attribution():
    node = _ast("inherited require amount is above 50000 from agent-compliance")
    assert node.inherited is True
    assert node.inherited_from == "agent-compliance"


def test_inherited_because_and_from():
    node = _ast(
        'inherited require amount is above 50000 because "SOX" from agent-a'
    )
    assert node.inherited is True
    assert node.rationale == "SOX"
    assert node.inherited_from == "agent-a"


def test_inherited_from_missing_agent_errors():
    _err("inherited require amount is above 50000 from")


def test_inherited_from_quoted_agent_errors():
    _err('inherited require amount is above 50000 from "multi word"')


def test_non_inherited_trailing_from_not_consumed_as_attribution():
    # A non-inherited statement with a trailing `from <name>` is not
    # attribution — the leftover tokens are unexpected and error.
    _err("require amount is above 50000 from agent-x")


def test_inherited_remember_from_is_copy_semantics_not_attribution():
    # `from y` here is the remember-copy path, consumed by the verb parser.
    node = _ast("inherited remember a string called x from y")
    assert isinstance(node, RememberValueNode)
    assert node.inherited is True
    assert node.inherited_from is None


def test_inherited_remember_double_from_copy_then_attribution():
    # First `from y` = copy-semantics (verb slot); second `from agent-a`
    # = statement-final attribution.
    node = _ast("inherited remember a string called x from y from agent-a")
    assert isinstance(node, RememberValueNode)
    assert node.inherited is True
    assert node.inherited_from == "agent-a"


def test_inherited_as_variable_name_is_reserved():
    result = parse(tokenize("remember a string called inherited with 5"))
    assert result.status is ResultStatus.ERROR_PARSE
    assert "reserved" in result.message
    assert "operator" in result.message


# ---------------------------------------------------------------------------
# Parser — sequences (inherited is per-operation)
# ---------------------------------------------------------------------------


def test_sequence_inherited_first_operation_only():
    node = _ast("inherited require amount is above 50000 and show amount")
    assert isinstance(node, SequenceNode)
    assert node.operations[0].inherited is True
    assert node.operations[1].inherited is False


def test_sequence_inherited_second_operation_only():
    node = _ast("show amount and inherited require amount is above 50000")
    assert isinstance(node, SequenceNode)
    assert node.operations[0].inherited is False
    assert node.operations[1].inherited is True


def test_sequence_both_operations_inherited():
    node = _ast("inherited show amount and inherited show threshold")
    assert isinstance(node, SequenceNode)
    assert node.operations[0].inherited is True
    assert node.operations[1].inherited is True


# ---------------------------------------------------------------------------
# Parser — `inherited` with `because`
# ---------------------------------------------------------------------------


def test_inherited_with_because_no_attribution():
    node = _ast('inherited require amount is above 50000 because "policy"')
    assert node.inherited is True
    assert node.rationale == "policy"
    assert node.inherited_from is None


def test_inherited_all_three_metadata_fields():
    node = _ast(
        'inherited require amount is above 50000 because "policy" from agent-a'
    )
    assert node.inherited is True
    assert node.rationale == "policy"
    assert node.inherited_from == "agent-a"


def test_inherited_wrong_order_from_before_because_errors():
    # Canonical order is `because` then `from`. The reverse leaves the
    # `because "..."` clause stranded after attribution → parse error.
    _err('inherited require amount is above 50000 from agent-a because "x"')


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


def test_render_inherited_without_attribution():
    node = _ast("inherited require amount is above 50000")
    assert render(node) == "inherited require amount is above 50000"


def test_render_inherited_with_attribution():
    node = _ast("inherited require amount is above 50000 from agent-a")
    assert render(node) == (
        "inherited require amount is above 50000 from agent-a"
    )


def test_render_inherited_with_rationale_and_attribution():
    node = _ast(
        'inherited require amount is above 50000 because "SOX" from agent-a'
    )
    assert render(node) == (
        'inherited require amount is above 50000 because "SOX" from agent-a'
    )


def test_render_non_inherited_has_no_prefix():
    node = _ast("require amount is above 50000")
    assert "inherited" not in render(node)


def test_round_trip_preserves_inherited_metadata():
    source = "inherited require amount is above 50000 from agent-a"
    node = _ast(source)
    rendered = render(node)
    assert rendered == source
    reparsed = _ast(rendered)
    assert reparsed.inherited is True
    assert reparsed.inherited_from == "agent-a"


# ---------------------------------------------------------------------------
# `inherited` in a `when` action block / on a `when` header
# ---------------------------------------------------------------------------


def test_inherited_inside_when_action_block():
    header = tokenize("when level is above 50")
    actions = [tokenize("inherited show level from agent-a")]
    node = parse_when_block(header, actions)
    assert not hasattr(node, "status"), getattr(node, "message", node)
    assert node.action.inherited is True
    assert node.action.inherited_from == "agent-a"


def test_inherited_when_header_is_rejected():
    # `inherited when` (an inherited reactive handler) is out of scope.
    # The `when` block parser entry rejects a leading `inherited` operator.
    result = parse(tokenize("inherited when level is above 50"))
    assert result.status is ResultStatus.ERROR_PARSE


# ---------------------------------------------------------------------------
# Integration — run_file
# ---------------------------------------------------------------------------


def _run(tmp_path, source, **kwargs):
    p = tmp_path / "prog.limn"
    p.write_text(source, encoding="utf-8")
    out = io.StringIO()
    run_file(str(p), out=out, **kwargs)
    return out.getvalue()


def test_program_with_inherited_executes(tmp_path):
    source = (
        'inherited remember a number called threshold with 1000 '
        'because "industry standard" from agent-compliance\n'
        "remember a number called amount with 75000\n"
        "inherited require amount is above threshold from agent-compliance\n"
        "show amount\n"
    )
    output = _run(tmp_path, source, quiet=True)
    assert "75000" in output
    assert "Error:" not in output
    # Provenance metadata is not echoed as program data.
    assert "agent-compliance" not in output


def test_inherited_require_enforces_identically(tmp_path):
    source = (
        "remember a number called amount with 100\n"
        "inherited require amount is above 50000 from agent-a\n"
        "show amount\n"
    )
    output = _run(tmp_path, source, quiet=True)
    # Same halt behavior as a non-inherited require.
    assert "100" not in output or "Error" in output or "require" in output.lower()


def test_inherited_weakens_starts_fresh(tmp_path):
    # MS-Q5: inherited weakens creates a fresh decaying value (tick 0).
    source = (
        "remember a number called trust with 100\n"
        "inherited weakens trust over 10 from agent-a\n"
        "show trust\n"
    )
    output = _run(tmp_path, source, quiet=True)
    # No decay has elapsed yet, so the full value shows.
    assert "100" in output
    assert "Error:" not in output


def test_remove_of_inherited_value_works(tmp_path):
    # MS-Q3: inherited values are overridable — `remove` works on them.
    source = (
        'inherited remember a list called rules with "a" and "b" '
        'from agent-a\n'
        'remove "a" from rules\n'
        "show rules\n"
    )
    output = _run(tmp_path, source, quiet=True)
    assert "Error:" not in output
    assert "b" in output


def test_about_because_inherited_together(tmp_path):
    # All three Meta-Structural Era features in one program.
    source = (
        'about "contract inheritance demo"\n'
        'inherited remember a number called threshold with 1000 '
        'because "industry standard" from agent-compliance\n'
        "remember a number called amount with 75000\n"
        'require amount is above threshold because "policy floor"\n'
        "show amount\n"
    )
    output = _run(tmp_path, source, quiet=True)
    assert "75000" in output
    assert "Error:" not in output
