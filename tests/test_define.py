"""Definitional Era (v31) — tests for the `define` declaration.

`define <name>: <condition>` registers a named, reusable domain predicate.
Anywhere the unified condition grammar accepts a test, `is <name>` (or
`is not <name>`) applies that predicate to the subject instead of doing
string equality — provided `<name>` is a predicate already defined on an
earlier line (forward-declaration only, mirroring named compositions).

Covers: parsing (name/colon/body, hyphenated names, reserved-word
rejection, `define-body` field elision), collision resolution against
plain string equality, every condition-consuming construct, end-to-end
execution (including negation, record subjects, composition of
predicates, and live redefinition), canonical rendering + round-trip,
the vocabulary count, and contradiction pre-pass safety.
"""

from __future__ import annotations

from liminate.analyzer import SymbolEntry, analyze
from liminate.cli import Session
from liminate.interpreter import execute as _execute
from liminate.lexer import tokenize
from liminate.parser import (
    BareWord,
    ChooseNode,
    ConditionNode,
    DefineNode,
    EachPronoun,
    ForbidNode,
    KeepNode,
    NameRef,
    PredicateApplicationNode,
    QuotedString,
    RequireEachNode,
    RequireNode,
    WhenNode,
    parse,
    parse_when_block,
)
from liminate.renderer import render
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus
from liminate.run import run as run_program
from liminate.vocabulary import ALL_RESERVED, DECLARATIONS, TOMBSTONES, reserved_category


def _parse(source: str, preds=None):
    """Parse directly (no reorderer) so parser-level rejection paths — a
    reserved word as a predicate name, a missing colon — are reached as
    units, matching tests/test_composition_param_literals.py. The
    reorderer's narrow permutation table has no rule for a DECLARATION
    token followed by a VERB-category word with no other verb in the
    line, which is irrelevant to the grammar under test here."""
    return parse(tokenize(source), predicate_names=preds or set())


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_define_parses_basic():
    ast = _parse("define overdue: due-date is below cutoff")
    assert isinstance(ast, DefineNode)
    assert ast.name == "overdue"
    assert isinstance(ast.condition, ConditionNode)
    assert ast.condition.op == "below"


def test_define_parses_hyphenated_name():
    ast = _parse("define high-risk: total is above 10000")
    assert isinstance(ast, DefineNode)
    assert ast.name == "high-risk"


def test_define_missing_colon_is_parse_error():
    r = _parse("define overdue")
    assert r.status is ResultStatus.ERROR_PARSE
    assert "':'" in r.message


def test_define_reserved_word_name_is_parse_error():
    r = _parse("define require: total is above 1")
    assert r.status is ResultStatus.ERROR_PARSE
    assert "reserved" in r.message
    assert "verb" in r.message


def test_define_body_field_elision():
    # v31 §90: inside a `define` body, a leading `is`/`includes` binds to
    # an implicit `each` pronoun, exactly like `require each`.
    ast = _parse("define big: is above 100")
    assert isinstance(ast, DefineNode)
    assert isinstance(ast.condition, ConditionNode)
    assert isinstance(ast.condition.field, EachPronoun)
    assert ast.condition.op == "above"


# ---------------------------------------------------------------------------
# Collision resolution
# ---------------------------------------------------------------------------


def test_is_predicate_produces_application_node():
    ast = _parse("keep the orders where each is overdue", {"overdue"})
    assert isinstance(ast, KeepNode)
    assert isinstance(ast.condition, PredicateApplicationNode)
    assert ast.condition.predicate_name == "overdue"
    assert isinstance(ast.condition.subject, EachPronoun)
    assert ast.condition.negated is False


def test_is_not_predicate_produces_negated_application_node():
    ast = _parse("keep the orders where each is not overdue", {"overdue"})
    assert isinstance(ast.condition, PredicateApplicationNode)
    assert ast.condition.negated is True


def test_empty_predicate_names_falls_back_to_equality():
    # No predicates in scope — `is overdue` is legacy string equality.
    ast = _parse("keep the orders where each is overdue")
    assert isinstance(ast.condition, ConditionNode)
    assert ast.condition.op == "is"
    assert isinstance(ast.condition.value, BareWord)
    assert ast.condition.value.word == "overdue"


def test_quoted_string_forces_equality_even_if_predicate_name_matches():
    ast = _parse('keep the orders where status is "overdue"', {"overdue"})
    assert isinstance(ast.condition, ConditionNode)
    assert ast.condition.op == "is"
    assert isinstance(ast.condition.value, QuotedString)
    assert ast.condition.value.content == "overdue"


# ---------------------------------------------------------------------------
# Every condition consumer accepts `is <predicate>`
# ---------------------------------------------------------------------------


def test_predicate_in_filter():
    ast = _parse("filter the orders where each is overdue", {"overdue"})
    assert isinstance(ast.condition, PredicateApplicationNode)


def test_predicate_in_keep():
    ast = _parse("keep the orders where each is overdue", {"overdue"})
    assert isinstance(ast.condition, PredicateApplicationNode)


def test_predicate_in_require():
    ast = _parse("require order1 is overdue", {"overdue"})
    assert isinstance(ast, RequireNode)
    assert isinstance(ast.condition, PredicateApplicationNode)
    assert isinstance(ast.condition.subject, NameRef)
    assert ast.condition.subject.name == "order1"


def test_predicate_in_require_each():
    ast = _parse("require each item in orders is overdue", {"overdue"})
    assert isinstance(ast, RequireEachNode)
    assert isinstance(ast.condition, PredicateApplicationNode)
    assert isinstance(ast.condition.subject, EachPronoun)


def test_predicate_in_forbid():
    ast = _parse("forbid total is high-risk", {"high-risk"})
    assert isinstance(ast, ForbidNode)
    assert isinstance(ast.condition, PredicateApplicationNode)


def test_predicate_in_permit():
    ast = _parse("permit order1 is overdue", {"overdue"})
    assert isinstance(ast.condition, PredicateApplicationNode)


def test_predicate_in_expect():
    ast = _parse("expect order1 is overdue", {"overdue"})
    assert isinstance(ast.condition, PredicateApplicationNode)


def test_predicate_in_choose_if():
    ast = _parse("choose if order1 is overdue: show order1", {"overdue"})
    assert isinstance(ast, ChooseNode)
    assert isinstance(ast.branches[0].condition, PredicateApplicationNode)


def test_predicate_in_when():
    header = reorder(tokenize("when order1 is overdue"))
    action = reorder(tokenize("show order1"))
    ast = parse_when_block(header, [action], predicate_names={"overdue"})
    assert isinstance(ast, WhenNode)
    assert isinstance(ast.condition, PredicateApplicationNode)


def test_predicate_in_unless_guard():
    header = reorder(tokenize("when order1 is overdue unless order1 is overdue"))
    action = reorder(tokenize("show order1"))
    ast = parse_when_block(header, [action], predicate_names={"overdue"})
    assert isinstance(ast.condition, PredicateApplicationNode)
    assert isinstance(ast.unless, PredicateApplicationNode)


# ---------------------------------------------------------------------------
# Interpreter (via Session / run) — end-to-end execution
# ---------------------------------------------------------------------------


def test_keep_by_predicate_returns_correct_subset():
    s = Session()
    s.run_line("define overdue: days-late is above 30")
    s.run_line("remember an order called o1 with days-late as 45")
    s.run_line("remember an order called o2 with days-late as 10")
    s.run_line("remember a list called orders with o1 and o2")
    r = s.run_line("keep the orders where each is overdue")
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["days-late: 45"]


def test_is_not_predicate_returns_complement():
    s = Session()
    s.run_line("define overdue: days-late is above 30")
    s.run_line("remember an order called o1 with days-late as 45")
    s.run_line("remember an order called o2 with days-late as 10")
    s.run_line("remember a list called orders with o1 and o2")
    r = s.run_line("keep the orders where each is not overdue")
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["days-late: 10"]


def test_predicate_on_named_record_subject():
    s = Session()
    s.run_line("define overdue: days-late is above 30")
    s.run_line("remember an order called o1 with days-late as 45")
    r = s.run_line("require o1 is overdue")
    assert r.status is ResultStatus.SUCCESS


def test_predicate_on_named_record_subject_fails_when_false():
    s = Session()
    s.run_line("define overdue: days-late is above 30")
    s.run_line("remember an order called o1 with days-late as 10")
    r = s.run_line("require o1 is overdue")
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET


def test_composed_predicate_evaluates_correctly():
    # v31 §84 — a predicate body may reference another predicate.
    s = Session()
    s.run_line("define overdue: days-late is above 30")
    s.run_line("define high-risk: is overdue")
    s.run_line("remember an order called o1 with days-late as 45")
    s.run_line("remember an order called o2 with days-late as 10")
    s.run_line("remember a list called orders with o1 and o2")
    r = s.run_line("keep the orders where each is high-risk")
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["days-late: 45"]


def test_live_redefinition_of_referenced_value_changes_verdict():
    # v31 §85 — the predicate body is re-evaluated on every application,
    # never cached: redefining `cutoff` changes a later verdict.
    s = Session()
    s.run_line("remember a number called cutoff with 30")
    s.run_line("define overdue: days-late is above cutoff")
    s.run_line("remember an order called o1 with days-late as 45")
    first = s.run_line("require o1 is overdue")
    assert first.status is ResultStatus.SUCCESS

    s.run_line("remember a number called cutoff with 100")
    second = s.run_line("require o1 is overdue")
    assert second.status is ResultStatus.REQUIREMENT_NOT_MET


def test_redefining_a_predicate_emits_a_warning_and_overwrites():
    s = Session()
    s.run_line("define overdue: days-late is above 30")
    r = s.run_line("define overdue: days-late is above 60")
    assert r.status is ResultStatus.SUCCESS
    assert r.output and "redefined" in r.output[0]
    s.run_line("remember an order called o1 with days-late as 45")
    # 45 is above 30 but not above 60 — confirms the second definition won.
    verdict = s.run_line("require o1 is overdue")
    assert verdict.status is ResultStatus.REQUIREMENT_NOT_MET


def test_undefined_predicate_reference_raises_clear_error():
    # Analyzer-path existence check (see PR description for why this
    # layer was chosen). In the normal Session/run() flow, `predicate_names`
    # is always derived live from the symbol table, so the parser can only
    # ever produce a PredicateApplicationNode for a name that genuinely
    # exists at that moment — this check guards the decoupled case where
    # an AST is parsed with a predicate name and then executed against a
    # symbol table that never actually defined it (exactly how a caller
    # could misuse the parse()/execute() split).
    ast = parse(tokenize("require order1 is overdue"), predicate_names={"overdue"})
    symtab = {"order1": SymbolEntry(name="order1", value={"x": 1}, type="record",
                                     schema={"x": "number"})}
    result = _execute(ast, symtab)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "overdue" in result.message
    assert "define overdue" in result.message


# ---------------------------------------------------------------------------
# Renderer / round-trip
# ---------------------------------------------------------------------------


def test_render_define_node():
    ast = _parse("define overdue: due-date is below cutoff")
    assert render(ast) == "define overdue: due-date is below cutoff"


def test_render_predicate_condition_round_trip():
    ast = _parse("keep the orders where each is overdue", {"overdue"})
    rendered = render(ast)
    assert rendered == "keep the orders where each is overdue"
    again = _parse(rendered, {"overdue"})
    assert again == ast


def test_define_with_because_round_trips():
    ast = _parse('define overdue: days-late is above 30 because "policy 4.2"')
    rendered = render(ast)
    assert rendered == 'define overdue: days-late is above 30 because "policy 4.2"'
    again = _parse(rendered)
    assert again == ast


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


def test_define_is_declaration():
    assert "define" in DECLARATIONS
    assert reserved_category("define") == "declaration"


def test_public_vocabulary_count_is_61():
    assert len(ALL_RESERVED) - len(TOMBSTONES) == 61


# ---------------------------------------------------------------------------
# Contradiction pre-pass safety
# ---------------------------------------------------------------------------


def test_predicate_containing_forbid_does_not_crash_prepass():
    # The contradiction pre-pass parses `require`/`forbid` without
    # predicate names (v31 §87 authorized skip-with-fallback), so
    # `is high-risk` reads as harmless string equality there — it must
    # never crash, even though the real pipeline treats it as a predicate.
    source = "\n".join([
        "define high-risk: total is above 10000",
        "remember a number called total with 50",
        "forbid total is high-risk",
    ])
    contract = run_program(source, enter_phase2=False)
    assert contract.results[-1].status is ResultStatus.SUCCESS


# ---------------------------------------------------------------------------
# Cyclic predicate rejection
#
# A predicate body may reference another predicate (§84 composition), and
# redefinition overwrites in place (v1d §58). Together, those two rules let
# a redefinition introduce a cycle a later `define` never sees coming:
# `define q: is p` only checks that `p` exists *right now* — it says
# nothing about what `p` itself might later be redefined to. Evaluating a
# cyclic predicate chain recurses forever, so this must be caught before
# it ever reaches evaluation.
# ---------------------------------------------------------------------------


def test_cyclic_redefinition_two_hop_is_rejected_not_a_recursion_error():
    s = Session()
    s.run_line("remember a number called x with 5")
    s.run_line("define p: is above 1")
    s.run_line("define q: is p")
    r = s.run_line("define p: is q")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert r.message == (
        "Definition 'p' refers back to itself through 'q'. "
        "A definition can't depend on itself."
    )
    # The rejected redefinition must not have overwritten `p` — the
    # earlier, non-cyclic definition stays live and evaluates normally.
    verdict = s.run_line("require x is p")
    assert verdict.status is ResultStatus.SUCCESS


def test_three_way_cycle_is_rejected():
    s = Session()
    s.run_line("define p: is above 1")
    s.run_line("define q: is p")
    s.run_line("define r: is q")
    result = s.run_line("define p: is r")
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "Definition 'p' refers back to itself through" in result.message
    assert "'r'" in result.message
    assert "'q'" in result.message


def test_direct_self_reference_on_first_definition_hits_forward_declaration_check():
    # Mirrors test_undefined_predicate_reference_raises_clear_error: the
    # decoupled parse()/analyze() path with an explicit predicate_names
    # set produces a PredicateApplicationNode even though `p` has never
    # actually been defined. In the normal Session/run() flow this can't
    # happen — predicate_names is always derived live from the symbol
    # table, so a first-ever `define p: is p` parses as harmless string
    # equality instead. This decoupled construction is what exercises the
    # forward-declaration path directly: it must still raise the
    # ORIGINAL "I don't know a definition" error, not the new
    # cycle-rejection error — the cycle check must never shadow it.
    ast = parse(tokenize("define p: is p"), predicate_names={"p"})
    result = analyze(ast, {})
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "I don't know a definition for 'p'" in result.message


def test_legal_redefinition_without_a_cycle_still_works():
    s = Session()
    s.run_line("define p: is above 1")
    r = s.run_line("define p: is above 2")
    assert r.status is ResultStatus.SUCCESS


def test_legal_composition_still_works():
    s = Session()
    r1 = s.run_line("define adult: age is above 17")
    assert r1.status is ResultStatus.SUCCESS
    r2 = s.run_line("define eligible: is adult")
    assert r2.status is ResultStatus.SUCCESS


def test_depth_guard_catches_a_hand_constructed_cyclic_symbol_table():
    # Belt-and-braces: the analyzer's cycle check makes this unreachable
    # through normal `define` usage, but a symbol table built directly —
    # bypassing analysis entirely, exactly the way a caller could misuse
    # the parse()/execute() split — must still surface a structured
    # ERROR_SEMANTIC instead of a bare RecursionError.
    symtab = {
        "x": SymbolEntry(name="x", value=5, type="number"),
        "p": SymbolEntry(
            name="p",
            value=PredicateApplicationNode(subject=EachPronoun(), predicate_name="q"),
            type="predicate",
        ),
        "q": SymbolEntry(
            name="q",
            value=PredicateApplicationNode(subject=EachPronoun(), predicate_name="p"),
            type="predicate",
        ),
    }
    ast = RequireNode(
        condition=PredicateApplicationNode(subject=NameRef(name="x"), predicate_name="p"),
    )
    result = _execute(ast, symtab)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "nested more than 64 levels deep" in result.message


def test_legal_ten_deep_predicate_chain_still_passes():
    s = Session()
    s.run_line("define p0: is above 1")
    for i in range(1, 11):
        r = s.run_line(f"define p{i}: is p{i - 1}")
        assert r.status is ResultStatus.SUCCESS
    s.run_line("remember a number called x with 5")
    verdict = s.run_line("require x is p10")
    assert verdict.status is ResultStatus.SUCCESS


# ---------------------------------------------------------------------------
# Self-referential define on a first-ever definition (no prior `p`).
#
# `_find_predicate_cycle` above only ever sees a PredicateApplicationNode —
# it cannot catch this case, because when `p` has never been defined, `is p`
# parses to a BareWord-equality ConditionNode instead (see
# test_direct_self_reference_on_first_definition_hits_forward_declaration_check
# for the decoupled construction that demonstrates why). Real `Session` usage
# hits string equality, not a predicate reference — so it needs its own
# surface-form check, `_check_self_referential_define`, run unconditionally
# in `_check_define` regardless of whether `p` is already known.
# ---------------------------------------------------------------------------


def test_self_reference_on_first_definition_is_rejected():
    s = Session()
    r = s.run_line("define p: is p")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert r.message == "Definition 'p' can't refer to itself."


def test_self_reference_in_field_position_is_rejected():
    s = Session()
    r = s.run_line("define p: p is above 1")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert r.message == "Definition 'p' can't refer to itself."


def test_self_reference_in_compound_and_branch_is_rejected():
    s = Session()
    r = s.run_line("define p: is above 1 and is p")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert r.message == "Definition 'p' can't refer to itself."


def test_self_reference_in_compound_or_branch_is_rejected():
    s = Session()
    r = s.run_line("define p: is p or is above 1")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert r.message == "Definition 'p' can't refer to itself."


def test_is_not_self_reference_is_a_pre_existing_parse_error_not_semantic():
    # `is not <bareword>` never parses when the word isn't already a known
    # predicate name — this is pre-existing, unrelated grammar behavior
    # (identical for any unknown word, e.g. `define p: is not grownup`),
    # not something this fix introduces or can reach. It is out of scope:
    # the fix is analyzer-only and must not touch parsing (see
    # `_check_self_referential_define`'s docstring). Documented here so the
    # self-reference test group doesn't imply this line is unhandled.
    s = Session()
    r = s.run_line("define p: is not p")
    assert r.status is ResultStatus.ERROR_PARSE
    assert r.message == "After 'not' I expected 'above', 'below', or 'equal to'."


def test_bareword_differing_from_defined_name_stays_string_equality():
    s = Session()
    s.run_line("define p: is above 1")
    r = s.run_line("define q: is p")
    assert r.status is ResultStatus.SUCCESS


def test_predicate_named_after_an_unrelated_fact_still_works():
    s = Session()
    s.run_line('remember a string called status with "p"')
    r = s.run_line("define matches-p: is p")
    assert r.status is ResultStatus.SUCCESS
