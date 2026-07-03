"""Tests for the `because` connective — Meta-Structural Era batch 2 (MS-Q2).

`because` is a connective (the 20th) that attaches a quoted rationale to
any verb statement as inert metadata stored on the AST node. It is
statement-terminal (consumed after all verb slots are filled) and
per-statement only (MS-Q2): it does not attach to `when` blocks as a
whole. The rationale is visible in canonical rendering, `inspect`, and
Receipts, but is never executed and never enters the symbol table.
"""

import io

import pytest

from liminate.cli import Session, run_file
from liminate.lexer import tokenize
from liminate.parser import (
    AddNode,
    AssignNode,
    CompareNode,
    ExpectNode,
    FinishNode,
    NumberLiteral,
    RememberCompositionNode,
    RememberListNode,
    RememberValueNode,
    RequireNode,
    SequenceNode,
    ShowNode,
    SortNode,
    _ParseError,
    parse,
    parse_when_block,
)
from liminate.renderer import render
from liminate.result import ResultStatus
from liminate.vocabulary import ALL_RESERVED, reserved_category


def _ast(source):
    """Parse a single statement, asserting it succeeded (not an error)."""
    result = parse(tokenize(source))
    assert not hasattr(result, "status"), getattr(result, "message", result)
    return result


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


def test_because_tokenizes_as_connective():
    from liminate.vocabulary import TokenType

    tokens = tokenize("because")
    assert len(tokens) == 1
    assert tokens[0].type is TokenType.CONNECTIVE
    assert tokens[0].value == "because"


def test_because_with_quoted_rationale_tokenizes():
    from liminate.vocabulary import TokenType

    tokens = tokenize('because "SOX compliance"')
    assert [(t.type, t.value) for t in tokens] == [
        (TokenType.CONNECTIVE, "because"),
        (TokenType.QUOTED_STRING, "SOX compliance"),
    ]


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


def test_because_in_all_reserved():
    assert "because" in ALL_RESERVED


def test_reserved_category_because_is_connective():
    assert reserved_category("because") == "connective"


def test_all_reserved_count_is_58():
    # Temporal-Boundary Era added `starting`/`until` connectives (56 → 58).
    # v25 added `highest`/`lowest` operators (58 → 60 counted) plus the
    # tombstoned `combine` (+1 uncounted) → 61 raw ALL_RESERVED entries.
    assert len(ALL_RESERVED) == 61


# ---------------------------------------------------------------------------
# Parser — happy paths
# ---------------------------------------------------------------------------


def test_require_with_rationale():
    node = _ast('require amount is above 50000 because "SOX compliance"')
    assert isinstance(node, RequireNode)
    assert node.rationale == "SOX compliance"


def test_remember_value_with_rationale():
    node = _ast('remember a number called threshold with 1000 because "industry standard"')
    assert isinstance(node, RememberValueNode)
    assert node.name == "threshold"
    assert node.value == NumberLiteral(1000)
    assert node.rationale == "industry standard"


def test_remember_list_with_rationale():
    node = _ast('remember a list called sizes with 1 and 2 and 3 because "fixed set"')
    assert isinstance(node, RememberListNode)
    assert node.rationale == "fixed set"


def test_show_with_rationale():
    node = _ast('show threshold because "for the auditor"')
    assert isinstance(node, ShowNode)
    assert node.rationale == "for the auditor"


def test_add_with_rationale():
    node = _ast('add 5 to sizes because "late addition"')
    assert isinstance(node, AddNode)
    assert node.rationale == "late addition"


def test_assign_with_rationale():
    node = _ast('assign review-task to compliance-team because "regulatory requirement"')
    assert isinstance(node, AssignNode)
    assert node.rationale == "regulatory requirement"


def test_expect_with_rationale():
    node = _ast('expect amount is below 100000 because "soft ceiling"')
    assert isinstance(node, ExpectNode)
    assert node.rationale == "soft ceiling"


def test_sort_with_rationale():
    node = _ast('sort orders by total because "biggest first matters"')
    assert isinstance(node, SortNode)
    assert node.rationale == "biggest first matters"


def test_compare_with_rationale():
    node = _ast('compare draft to final because "diff review"')
    assert isinstance(node, CompareNode)
    assert node.rationale == "diff review"


def test_finish_with_rationale():
    node = _ast('finish because "emergency exit"')
    assert isinstance(node, FinishNode)
    assert node.rationale == "emergency exit"


# ---------------------------------------------------------------------------
# Parser — no rationale (backward compatibility)
# ---------------------------------------------------------------------------


def test_require_without_rationale_is_none():
    node = _ast("require amount is above 50000")
    assert isinstance(node, RequireNode)
    assert node.rationale is None


def test_remember_without_rationale_is_none():
    node = _ast("remember a number called threshold with 1000")
    assert isinstance(node, RememberValueNode)
    assert node.rationale is None


# ---------------------------------------------------------------------------
# Parser — error cases
# ---------------------------------------------------------------------------


def test_because_bare_word_rationale_errors():
    result = parse(tokenize("require amount is above 50000 because compliance"))
    assert result.status is ResultStatus.ERROR_PARSE


def test_because_missing_rationale_errors():
    result = parse(tokenize("require amount is above 50000 because"))
    assert result.status is ResultStatus.ERROR_PARSE
    assert "because" in result.message


def test_because_number_rationale_errors():
    result = parse(tokenize("require amount is above 50000 because 42"))
    assert result.status is ResultStatus.ERROR_PARSE


def test_because_as_variable_name_is_reserved():
    session = Session()
    result = session.run_line("remember a string called because with 5")
    assert result.status is ResultStatus.ERROR_PARSE
    assert "reserved" in result.message
    assert "connective" in result.message


# ---------------------------------------------------------------------------
# Parser — sequences (because attaches to the last operation)
# ---------------------------------------------------------------------------


def test_sequence_rationale_attaches_to_last_operation():
    node = _ast('show budget and require amount is above 50000 because "audit rule"')
    assert isinstance(node, SequenceNode)
    assert isinstance(node.operations[0], ShowNode)
    assert node.operations[0].rationale is None
    assert node.operations[1].rationale == "audit rule"


def test_sequence_both_operations_have_rationales():
    node = _ast('show budget because "x" and show threshold because "y"')
    assert isinstance(node, SequenceNode)
    assert node.operations[0].rationale == "x"
    assert node.operations[1].rationale == "y"


def test_sequence_rationale_on_first_only():
    node = _ast('show budget because "x" and show threshold')
    assert isinstance(node, SequenceNode)
    assert node.operations[0].rationale == "x"
    assert node.operations[1].rationale is None


def test_then_sequence_rationale_attaches_to_last():
    node = _ast('show budget then require amount is above 50000 because "ordering matters"')
    assert isinstance(node, SequenceNode)
    assert node.connectors == ["then"]
    assert node.operations[1].rationale == "ordering matters"


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


def test_render_appends_because_clause():
    node = _ast('require amount is above 50000 because "SOX compliance"')
    assert render(node) == 'require amount is above 50000 because "SOX compliance"'


def test_render_without_rationale_omits_because():
    node = _ast("require amount is above 50000")
    assert "because" not in render(node)


def test_round_trip_preserves_rationale():
    source = 'remember a number called threshold with 1000 because "industry standard"'
    node = _ast(source)
    rendered = render(node)
    assert 'because "industry standard"' in rendered
    reparsed = _ast(rendered)
    assert reparsed.rationale == "industry standard"


def test_render_sequence_with_one_rationale():
    node = _ast('show budget and require amount is above 50000 because "audit rule"')
    rendered = render(node)
    assert rendered == 'show budget and require amount is above 50000 because "audit rule"'


# ---------------------------------------------------------------------------
# Integration — run_file
# ---------------------------------------------------------------------------


def _run(tmp_path, source, **kwargs):
    p = tmp_path / "prog.limn"
    p.write_text(source, encoding="utf-8")
    out = io.StringIO()
    run_file(str(p), out=out, **kwargs)
    return out.getvalue()


def test_program_with_because_executes(tmp_path):
    source = (
        'remember a number called threshold with 50000 because "company policy minimum"\n'
        'require threshold is above 1000 because "sanity floor"\n'
        "show threshold\n"
    )
    output = _run(tmp_path, source, quiet=True)
    assert "50000" in output
    assert "Error:" not in output
    # The rationale text is metadata — it is not echoed as program data.
    assert "company policy minimum" not in output


def test_program_without_because_no_regression(tmp_path):
    source = (
        "remember a number called threshold with 50000\n"
        "show threshold\n"
    )
    output = _run(tmp_path, source, quiet=True)
    assert "50000" in output
    assert "Error:" not in output


def test_because_inside_when_action_block():
    # MS-Q2: `because` attaches to a statement *inside* the action block,
    # not to the `when` block as a whole.
    header = tokenize("when level is above 50")
    actions = [tokenize('show level because "audit trail"')]
    node = parse_when_block(header, actions)
    assert not hasattr(node, "status"), getattr(node, "message", node)
    # Single-statement action block → action is the ShowNode directly.
    assert node.action.rationale == "audit trail"


def test_because_on_when_header_is_rejected():
    # MS-Q2: a `because` on the `when` header line itself is a parse error
    # — rationales annotate statements, not whole blocks.
    header = tokenize('when level is above 50 because "block-level"')
    actions = [tokenize("show level")]
    result = parse_when_block(header, actions)
    assert result.status is ResultStatus.ERROR_PARSE


def test_because_on_composition_body_statement():
    node = _ast('remember how to report: show threshold because "definition note"')
    assert isinstance(node, RememberCompositionNode)
    # The rationale attaches to the body statement (statement-terminal).
    assert node.body.rationale == "definition note"
