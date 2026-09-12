"""Phase 3 gate tests: reorderer (v1d §55)."""

from liminate.lexer import tokenize
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus
from liminate.vocabulary import Token, TokenType


def _values(tokens: list[Token]) -> list[str]:
    return [t.value for t in tokens]


# ---------- canonical pass-through ----------

def test_empty_token_list_passes_through():
    assert reorder([]) == []


def test_canonical_filter_passes_through():
    toks = tokenize("filter the orders where total is above 50")
    out = reorder(toks)
    assert out == toks


def test_canonical_remember_passes_through():
    toks = tokenize("remember a number called age with 30")
    out = reorder(toks)
    assert out == toks


def test_canonical_each_with_where_passes_through():
    toks = tokenize("filter the numbers where each is above 5")
    out = reorder(toks)
    assert isinstance(out, list)
    assert out == toks


def test_canonical_compound_condition_passes_through():
    toks = tokenize("filter the orders where total is above 50 and status is active")
    out = reorder(toks)
    assert out == toks


def test_canonical_equal_to_passes_through():
    toks = tokenize("filter the orders where total is equal to 75")
    out = reorder(toks)
    assert out == toks


def test_show_simple_passes_through():
    toks = tokenize("show age")
    assert reorder(toks) == toks


# ---------- target-before-verb reordering (v1d §55 row 2 & 3) ----------

def test_article_target_before_verb_reorders():
    src = tokenize("the orders filter where total is above 50")
    out = reorder(src)
    assert isinstance(out, list)
    assert _values(out) == ["filter", "the", "orders", "where", "total", "is", "above", "50"]


def test_bare_target_before_verb_reorders():
    src = tokenize("orders filter where total is above 50")
    out = reorder(src)
    assert isinstance(out, list)
    assert _values(out) == ["filter", "orders", "where", "total", "is", "above", "50"]


def test_target_before_show_reorders():
    src = tokenize("the colors show")
    out = reorder(src)
    assert isinstance(out, list)
    assert _values(out) == ["show", "the", "colors"]


# ---------- scrambled inputs reject with hint (v1d §55) ----------

def test_verb_at_end_is_rejected():
    src = tokenize("the orders where total is above 50 filter")
    out = reorder(src)
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_PARSE
    assert out.executed is False
    assert "verb" in out.message.lower() or "couldn't parse" in out.message.lower()


def test_condition_scrambled_after_reorder_is_rejected():
    # Condition elements scrambled. v1d §55 example.
    src = tokenize("filter the orders where above 50 total is")
    out = reorder(src)
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_PARSE
    assert "condition" in out.message.lower()


def test_condition_scrambled_with_target_before_verb_is_rejected():
    src = tokenize("the orders filter where above 50 total is")
    out = reorder(src)
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_PARSE


def test_all_tokens_scrambled_is_rejected():
    src = tokenize("50 above is total where orders the filter")
    out = reorder(src)
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_PARSE


# ---------- no-verb passes through for composition fallback ----------

def test_no_verb_passes_through_for_composition_fallback():
    # v1b §41: parser falls back to symbol table lookup.
    src = tokenize("find-big-orders")
    out = reorder(src)
    assert isinstance(out, list)
    assert _values(out) == ["find-big-orders"]


def test_no_verb_multi_token_passes_through():
    # Sentence 34: `orders total above 50` (no verb).
    src = tokenize("orders total above 50")
    out = reorder(src)
    assert isinstance(out, list)
    assert _values(out) == ["orders", "total", "above", "50"]


# ---------- locked sentences round-trip cleanly ----------

def test_each_iteration_verb_in_canonical_position():
    src = tokenize("each the orders show total")
    out = reorder(src)
    assert out == src


def test_gather_range_canonical():
    src = tokenize("gather the numbers from 1 to 10")
    out = reorder(src)
    assert out == src


def test_named_composition_definition_canonical():
    src = tokenize("remember how to find-big-orders: filter the orders where total is above 50")
    out = reorder(src)
    assert out == src


def test_sum_canonical():
    src = tokenize("sum the numbers")
    out = reorder(src)
    assert out == src


def test_compound_sequencing_passes_through():
    # Sentence 47: filter ... and show ... — operation sequencing.
    src = tokenize("filter nums where each is above 3 and show missingname")
    out = reorder(src)
    assert out == src


# ---------- error message quality ----------

def test_scramble_error_offers_canonical_template():
    src = tokenize("50 above is total where orders the filter")
    out = reorder(src)
    assert isinstance(out, LiminateResult)
    # Some pointer to the canonical shape should appear in the message.
    assert "filter the orders" in out.message or "verb" in out.message.lower()


def test_condition_scrambled_error_offers_canonical_condition_shape():
    src = tokenize("filter the orders where above 50 total is")
    out = reorder(src)
    assert isinstance(out, LiminateResult)
    assert "is" in out.message
    assert "field" in out.message.lower() or "comparison" in out.message.lower()


# ---------- temporal-prefix bare-date acceptance (Fix A) ----------
#
# These go through liminate.run() rather than parse(tokenize(...)) —
# the reorder() guard on QUOTED_STRING-only date tokens is what dropped
# bare dates on the floor with ERROR_PARSE, and parse(tokenize(...))
# never exercises reorder() so it could not have caught the bug.

import liminate


def _run_statuses(line: str) -> list[str]:
    source = "remember a number called x with 20\n" + line
    result = liminate.run(source)
    return [r.status.name for r in result.results]


def test_temporal_prefix_bare_both_succeeds_through_run():
    assert _run_statuses(
        "starting 2025-07-01 until 2025-12-31 require x is above 10"
    ) == ["SUCCESS", "SUCCESS"]


def test_temporal_prefix_quoted_both_succeeds_through_run():
    assert _run_statuses(
        'starting "2025-07-01" until "2025-12-31" require x is above 10'
    ) == ["SUCCESS", "SUCCESS"]


def test_temporal_prefix_bare_starting_only_succeeds_through_run():
    assert _run_statuses(
        "starting 2025-07-01 require x is above 10"
    ) == ["SUCCESS", "SUCCESS"]


def test_temporal_prefix_quoted_starting_only_succeeds_through_run():
    assert _run_statuses(
        'starting "2025-07-01" require x is above 10'
    ) == ["SUCCESS", "SUCCESS"]


def test_temporal_prefix_bare_until_only_succeeds_through_run():
    assert _run_statuses(
        "until 2025-12-31 require x is above 10"
    ) == ["SUCCESS", "SUCCESS"]


def test_temporal_prefix_quoted_until_only_succeeds_through_run():
    assert _run_statuses(
        'until "2025-12-31" require x is above 10'
    ) == ["SUCCESS", "SUCCESS"]


def test_temporal_prefix_bare_date_populates_ast_metadata():
    tokens = tokenize(
        "starting 2025-07-01 until 2025-12-31 require x is above 10"
    )
    reordered = reorder(tokens)
    assert isinstance(reordered, list)
    from liminate.parser import parse

    node = parse(reordered)
    assert node.starting_date == "2025-07-01"
    assert node.until_date == "2025-12-31"


def test_temporal_prefix_bare_dates_with_inherited_reorders():
    tokens = tokenize(
        "starting 2025-07-01 until 2025-12-31 inherited require x is above 10"
    )
    reordered = reorder(tokens)
    assert isinstance(reordered, list)
    from liminate.parser import parse

    node = parse(reordered)
    assert node.starting_date == "2025-07-01"
    assert node.until_date == "2025-12-31"
    assert node.inherited is True


# `includes` after `where` — the gate that blocked a condition every other
# layer already handled.
#
# The parser produces `op="includes"` / `op="not_includes"` for these, and the
# analyzer accepts them explicitly as list-membership. Only this two-token
# shape check stood in front, requiring the second token after `where` to be
# the operator `is`. So `title includes "ant"` was reported as an unparseable
# condition by the one stage that never tried to parse it.
#
# The gate had already been widened once, for the v25 extrema head. This is
# the same shape of change.


def test_where_includes_passes_through():
    src = tokenize('filter the orders where title includes "urgent"')
    out = reorder(src)
    assert isinstance(out, list), getattr(out, "message", out)
    assert _values(out) == [
        "filter", "the", "orders", "where", "title", "includes", "urgent",
    ]


def test_where_not_includes_passes_through():
    src = tokenize('filter the orders where title not includes "urgent"')
    out = reorder(src)
    assert isinstance(out, list), getattr(out, "message", out)


def test_keep_where_includes_passes_through():
    src = tokenize('keep the orders where title includes "urgent"')
    out = reorder(src)
    assert isinstance(out, list), getattr(out, "message", out)


def test_where_includes_reaches_the_parser_that_handles_it():
    from liminate.parser import parse

    out = reorder(tokenize('filter the orders where title includes "urgent"'))
    assert isinstance(out, list), getattr(out, "message", out)
    assert parse(out).condition.op == "includes"


def test_where_includes_filters_a_list_valued_field_correctly():
    """The reason the gate had to move: this works, and nothing could reach it.

    `includes` is a list-membership probe, so after `where` it is meaningful
    exactly when the field it names holds a list. That case filters correctly
    and was unreachable — not because any stage could not do it, but because
    the one stage that does no parsing said the condition could not be parsed.
    """
    from liminate.run import Session
    from liminate.result import ResultStatus

    session = Session()
    for line in [
        'remember a list called roof-tags with "urgent" and "roof"',
        'remember a list called lawn-tags with "routine" and "lawn"',
        "remember an order called order1 with total as 75 and tags as roof-tags",
        "remember an order called order2 with total as 30 and tags as lawn-tags",
        "remember a list called orders with order1 and order2",
    ]:
        assert session.run_line(line).status is ResultStatus.SUCCESS, line

    result = session.run_line('filter the orders where tags includes "urgent"')
    assert result.status is ResultStatus.SUCCESS, result.message
    assert len(session.symtab["orders"].value) == 1
    assert session.run_line("show orders").output == [
        "total: 75, tags: ['urgent', 'roof']"
    ]


def test_where_includes_over_scalar_items_keeps_the_documented_answer():
    """The boundary, stated rather than discovered later.

    `each` is an item, not a list, and `includes` over a non-list operand is
    false by decision — see `test_includes_with_scalar_left_operand_is_false`.
    So `where each includes "x"` empties the list rather than matching text.
    Widening the gate does not change that and must not be read as making
    `includes` a substring test; text-contains is not in the language.
    """
    from liminate.run import run

    base = (
        'remember a list called tags with "urgent-repair"\n'
        'add "routine-check" to tags\n'
    )
    result = run(base + 'filter tags where each includes "urgent"\nshow tags')
    assert result.results[-1].output == [""]


def test_a_genuinely_scrambled_condition_is_still_rejected():
    """Widening the gate must not turn it off. `includes` is admitted in the
    comparison position; a condition with nothing in that position is not."""
    src = tokenize("filter the orders where above 50 total is")
    out = reorder(src)
    assert not isinstance(out, list)
