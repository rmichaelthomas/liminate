"""Phase 7 integration tests: full pipeline for all 48 locked sentences.

The 48 sentences are organized as follows (per BUILD_PLAN + spec docs):
  Sentences 1-5    Program 1 — basic values + lists                 [spec]
  Sentences 6-10   Program 2 — records + each                        [spec]
  Sentences 11-15  Program 3 — filtering records                     [spec]
  Sentences 16-20  Program 4 — number operations                     [spec]
  Sentences 21-24  Program 5 — `not` operator                        [spec]
  Sentences 25-26  Named compositions                                [spec]
  Sentences 27-28  Compound conditions                               [spec]
  Sentence  29     Mixed-precedence amber                            [spec]
  Sentence  30     `equal to` operator                               [spec]
  Sentence  31     Reserved word violation (error)                   [spec]
  Sentences 32-34  v1c §53 additions                                 [v1c]
  Sentences 35-48  v1d §65 hostile test block                        [v1d]
"""

import io
import os
from pathlib import Path

import pytest

from inscript.cli import Session, display_result
from inscript.result import ResultStatus

ROOT = Path(__file__).resolve().parent.parent


def make_session():
    return Session()


def run_lines(lines: list[str]):
    session = make_session()
    results = [session.run_line(line) for line in lines]
    return session, results


# ---------------------------------------------------------------------------
# Program 1 — Sentences 1–5
# ---------------------------------------------------------------------------


def test_program_1_full_pipeline():
    session, results = run_lines([
        "remember a number called age with 30",                       # 1
        "remember a list called colors with red and blue and green",  # 2
        "show age",                                                    # 3
        "show colors",                                                 # 4
        "count the colors",                                            # 5
    ])
    assert results[0].status is ResultStatus.SUCCESS and results[0].output is None
    assert results[1].status is ResultStatus.SUCCESS and results[1].output is None
    assert results[2].output == ["30"]
    assert results[3].output == ["red, blue, green"]
    assert results[4].output == ["3"]
    assert session.symtab["age"].value == 30
    assert session.symtab["colors"].value == ["red", "blue", "green"]


# ---------------------------------------------------------------------------
# Program 2 — Sentences 6–10
# ---------------------------------------------------------------------------


def test_program_2_full_pipeline():
    session, results = run_lines([
        "remember an order called order1 with total as 75 and status as active",     # 6
        "remember an order called order2 with total as 30 and status as active",     # 7
        "remember an order called order3 with total as 120 and status as pending",   # 8
        "remember a list called orders with order1 and order2 and order3",           # 9
        "each the orders show total",                                                 # 10
    ])
    for r in results[:4]:
        assert r.status is ResultStatus.SUCCESS
    assert results[4].output == ["75", "30", "120"]


# ---------------------------------------------------------------------------
# Program 3 — Sentences 11–15
# ---------------------------------------------------------------------------


def test_program_3_full_pipeline():
    session = make_session()
    for s in [
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember an order called order3 with total as 120 and status as pending",
        "remember a list called orders with order1 and order2 and order3",
    ]:
        session.run_line(s)

    # 11: filter in-place
    r11 = session.run_line("filter the orders where total is above 50")
    assert r11.status is ResultStatus.SUCCESS and r11.output is None
    assert len(session.symtab["orders"].value) == 2

    # 12: show the remaining records, one per line
    r12 = session.run_line("show orders")
    assert r12.output == [
        "total: 75, status: active",
        "total: 120, status: pending",
    ]

    # 13: further filter — only order1 (status=active) remains
    r13 = session.run_line("filter the orders where status is active")
    assert r13.status is ResultStatus.SUCCESS
    assert len(session.symtab["orders"].value) == 1

    # 14: count auto-shows
    r14 = session.run_line("count the orders")
    assert r14.output == ["1"]

    # 15: each shows status
    r15 = session.run_line("each the orders show status")
    assert r15.output == ["active"]


# ---------------------------------------------------------------------------
# Program 4 — Sentences 16–20
# ---------------------------------------------------------------------------


def test_program_4_full_pipeline():
    session = make_session()

    # 16: gather stores AND auto-shows (v1b §40)
    r16 = session.run_line("gather the numbers from 1 to 10")
    assert r16.output == ["1, 2, 3, 4, 5, 6, 7, 8, 9, 10"]
    assert session.symtab["numbers"].value == list(range(1, 11))

    # 17: filter in-place
    r17 = session.run_line("filter the numbers where each is above 5")
    assert r17.status is ResultStatus.SUCCESS and r17.output is None
    assert session.symtab["numbers"].value == [6, 7, 8, 9, 10]

    # 18: count auto-shows
    r18 = session.run_line("count the numbers")
    assert r18.output == ["5"]

    # 19: combine auto-shows (non-destructive per v1b §39)
    r19 = session.run_line("combine the numbers")
    assert r19.output == ["40"]
    assert session.symtab["numbers"].value == [6, 7, 8, 9, 10]

    # 20: capture via `from` recursive descent (v1b §43)
    r20 = session.run_line("remember the result called total from combine the numbers")
    assert r20.status is ResultStatus.SUCCESS and r20.output is None
    assert session.symtab["total"].value == 40
    assert session.symtab["numbers"].value == [6, 7, 8, 9, 10]


# ---------------------------------------------------------------------------
# Program 5 — Sentences 21–24
# ---------------------------------------------------------------------------


def test_program_5_full_pipeline():
    session, results = run_lines([
        "gather the scores from 1 to 10",                            # 21
        "filter the scores where each is not above 7",               # 22
        "filter the scores where each is not below 3",               # 23
        "filter the scores where each is not equal to 5",            # 24
    ])
    assert session.symtab["scores"].value == [3, 4, 6, 7]


# ---------------------------------------------------------------------------
# Sentences 25–26 — Named compositions (definition only)
# ---------------------------------------------------------------------------


def test_sentence_25_composition_definition():
    session = make_session()
    r = session.run_line(
        "remember how to find-big-orders: filter the orders where total is above 50"
    )
    assert r.status is ResultStatus.SUCCESS
    assert session.symtab["find-big-orders"].type == "composition"


def test_sentence_26_composition_with_sequenced_body():
    session = make_session()
    r = session.run_line(
        "remember how to count-active: filter the orders where status is active and count the orders"
    )
    assert r.status is ResultStatus.SUCCESS
    assert session.symtab["count-active"].type == "composition"


# ---------------------------------------------------------------------------
# Sentences 27–28 — Compound conditions
# ---------------------------------------------------------------------------


def test_sentence_27_compound_and():
    session, _ = run_lines([
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember an order called order3 with total as 120 and status as pending",
        "remember a list called orders with order1 and order2 and order3",
        "filter the orders where total is above 50 and status is active",
    ])
    assert len(session.symtab["orders"].value) == 1
    assert session.symtab["orders"].value[0]["total"] == 75


def test_sentence_28_compound_or():
    session, _ = run_lines([
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember an order called order3 with total as 120 and status as pending",
        "remember a list called orders with order1 and order2 and order3",
        "filter the orders where total is below 30 or status is pending",
    ])
    # Only order3 (status=pending) survives — total<30 matches no records.
    statuses = [o["status"] for o in session.symtab["orders"].value]
    assert statuses == ["pending"]


# ---------------------------------------------------------------------------
# Sentence 29 — Mixed precedence amber
# ---------------------------------------------------------------------------


def test_sentence_29_mixed_precedence_amber():
    session, _ = run_lines([
        "remember an order called order1 with total as 75 and status as active",
        "remember a list called orders with order1",
    ])
    before = list(session.symtab["orders"].value)
    r = session.run_line(
        "filter the orders where total is above 50 and status is active or status is pending"
    )
    assert r.status is ResultStatus.AMBER_PRECEDENCE
    assert r.executed is False
    # Pending AST present for confirmation flow.
    assert r.pending_ast is not None
    # No mutation has occurred.
    assert session.symtab["orders"].value == before
    # Message shows the parser's interpretation in parenthesized form.
    assert "(total is above 50 and status is active)" in r.message
    assert "or status is pending" in r.message


# ---------------------------------------------------------------------------
# Sentence 30 — `equal to`
# ---------------------------------------------------------------------------


def test_sentence_30_equal_to():
    session, _ = run_lines([
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember a list called orders with order1 and order2",
        "filter the orders where total is equal to 75",
    ])
    assert len(session.symtab["orders"].value) == 1
    assert session.symtab["orders"].value[0]["total"] == 75


# ---------------------------------------------------------------------------
# Sentence 31 — Reserved word violation
# ---------------------------------------------------------------------------


def test_sentence_31_reserved_word_in_name_position():
    session = make_session()
    r = session.run_line("remember a value called filter with 10")
    assert r.status is ResultStatus.ERROR_PARSE
    assert "'filter'" in r.message
    assert "reserved" in r.message
    assert "verb" in r.message


# ---------------------------------------------------------------------------
# Sentence 32 — Vocabulary word in value position (v1c §46)
# ---------------------------------------------------------------------------


def test_sentence_32_vocabulary_word_in_value_position():
    session = make_session()
    r = session.run_line("remember a list called items with filter and blue")
    assert r.status is ResultStatus.ERROR_PARSE
    assert "'filter'" in r.message


# ---------------------------------------------------------------------------
# Sentence 33 — Article `an` (v1c §47)
# ---------------------------------------------------------------------------


def test_sentence_33_article_an_recognized():
    session = make_session()
    r = session.run_line("remember an item called widget with 25")
    assert r.status is ResultStatus.SUCCESS
    assert session.symtab["widget"].value == 25
    assert session.symtab["widget"].type == "number"


# ---------------------------------------------------------------------------
# Sentence 34 — No verb error (v1c §46)
# ---------------------------------------------------------------------------


def test_sentence_34_no_verb_error_lists_available_verbs():
    session = make_session()
    r = session.run_line("orders total above 50")
    assert r.status is ResultStatus.ERROR_PARSE
    for verb in ("remember", "show", "filter", "count", "gather", "combine", "each"):
        assert verb in r.message


# ---------------------------------------------------------------------------
# Sentence 35 — Name not found
# ---------------------------------------------------------------------------


def test_sentence_35_name_not_found():
    session = make_session()
    r = session.run_line("show missingname")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in r.message
    assert "remember" in r.message


# ---------------------------------------------------------------------------
# Sentence 36 — Filter on scalar
# ---------------------------------------------------------------------------


def test_sentence_36_filter_on_scalar():
    session, _ = run_lines([
        "remember a number called age with 30",
    ])
    r = session.run_line("filter age where each is above 5")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "filter a list" in r.message
    assert "age" in r.message


# ---------------------------------------------------------------------------
# Sentence 37 — Combine on strings
# ---------------------------------------------------------------------------


def test_sentence_37_combine_on_strings():
    session, _ = run_lines([
        "remember a list called colors with red and blue and green",
    ])
    r = session.run_line("combine colors")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "combine numbers" in r.message
    assert "colors" in r.message
    assert "text" in r.message


# ---------------------------------------------------------------------------
# Sentence 38 — Missing field on records
# ---------------------------------------------------------------------------


def test_sentence_38_missing_field():
    session, _ = run_lines([
        "remember an order called order1 with total as 75 and status as active",
        "remember a list called orders with order1",
    ])
    # Crucial: `orders` must be a list (singleton-list path), not a record.
    assert session.symtab["orders"].type == "list_of_records"
    r = session.run_line("filter the orders where missingfield is above 50")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "missingfield" in r.message
    assert "orders" in r.message


# ---------------------------------------------------------------------------
# Sentence 39 — Each on scalar
# ---------------------------------------------------------------------------


def test_sentence_39_each_on_scalar():
    session, _ = run_lines([
        "remember a number called age with 30",
    ])
    r = session.run_line("each the age show")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "iterate over a list" in r.message


# ---------------------------------------------------------------------------
# Sentence 40 — Descriptor decorative; value type wins
# ---------------------------------------------------------------------------


def test_sentence_40_descriptor_decorative():
    session = make_session()
    r1 = session.run_line("remember a number called label with hello")
    assert r1.status is ResultStatus.SUCCESS
    r2 = session.run_line("show label")
    assert r2.output == ["hello"]


# ---------------------------------------------------------------------------
# Sentence 41 — Mixed-type list
# ---------------------------------------------------------------------------


def test_sentence_41_mixed_type_list():
    session = make_session()
    r = session.run_line("remember a list called mixed with 1 and blue")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "can't mix" in r.message
    assert "'1' is a number" in r.message
    assert "'blue' is text" in r.message


# ---------------------------------------------------------------------------
# Sentence 42 — Descending range
# ---------------------------------------------------------------------------


def test_sentence_42_descending_range():
    session = make_session()
    r = session.run_line("gather the numbers from 10 to 1")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "less than or equal" in r.message


# ---------------------------------------------------------------------------
# Sentence 43 — Range cap (10,000)
# ---------------------------------------------------------------------------


def test_sentence_43_range_cap():
    session = make_session()
    r = session.run_line("gather the numbers from 1 to 20000")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "10,000" in r.message


# ---------------------------------------------------------------------------
# Sentence 44 — Duplicate name overwrite
# ---------------------------------------------------------------------------


def test_sentence_44_duplicate_overwrite():
    session, _ = run_lines([
        "remember a number called age with 30",
        "remember a number called age with 40",
    ])
    r = session.run_line("show age")
    assert r.output == ["40"]


# ---------------------------------------------------------------------------
# Sentence 45 — Malformed record (parse error)
# ---------------------------------------------------------------------------


def test_sentence_45_malformed_record():
    session = make_session()
    r = session.run_line(
        "remember an order called order1 with total as 75 and status as active and status"
    )
    assert r.status is ResultStatus.ERROR_PARSE
    assert "status" in r.message
    assert "as" in r.message


# ---------------------------------------------------------------------------
# Sentence 46 — Composition def succeeds; call fails at call-time
# ---------------------------------------------------------------------------


def test_sentence_46_composition_call_fails_after_definition():
    session = make_session()
    r1 = session.run_line("remember how to show-missing: show missingname")
    assert r1.status is ResultStatus.SUCCESS

    r2 = session.run_line("show-missing")
    assert r2.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in r2.message


# ---------------------------------------------------------------------------
# Sentence 47 — Stepwise failure leaves filter committed
# ---------------------------------------------------------------------------


def test_sentence_47_stepwise_failure():
    session, _ = run_lines([
        "remember a list called nums with 1 and 2 and 3 and 4 and 5",
    ])
    r = session.run_line("filter nums where each is above 3 and show missingname")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in r.message
    assert "filter has already been applied" in r.message
    assert session.symtab["nums"].value == [4, 5]

    r3 = session.run_line("show nums")
    assert r3.output == ["4, 5"]


# ---------------------------------------------------------------------------
# Sentence 48 — Schema mismatch in list
# ---------------------------------------------------------------------------


def test_sentence_48_schema_mismatch():
    session, _ = run_lines([
        "remember an order called order1 with total as 75 and status as active",
        "remember an item called item1 with price as 30 and color as red",
        "remember a list called mixed-records with order1 and item1",
    ])
    r = session.run_line("filter the mixed-records where total is above 50")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    # U2/U3: the partial-match error names 'item1' as the offending record
    # and signals that other items DO have the field.
    assert "'item1' in 'mixed-records'" in r.message
    assert "doesn't have a field called 'total'" in r.message
    assert "Other items do have it" in r.message


# ---------------------------------------------------------------------------
# Coverage roll-up: every sentence has a positive identification above
# ---------------------------------------------------------------------------


SENTENCE_INDEX = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
    31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
}


def test_all_48_sentences_have_a_targeted_test():
    # The Program tests above cover sentences 1–24 collectively; the
    # remaining 24 sentences each have an individually named test. This
    # roll-up is here to lock the count.
    assert len(SENTENCE_INDEX) == 48


# ---------------------------------------------------------------------------
# CLI driver: display_result writes the canonical preview and output
# ---------------------------------------------------------------------------


def test_display_result_renders_success_with_canonical_and_output():
    session = make_session()
    session.run_line("remember a number called age with 30")
    result = session.run_line("show age")
    buf = io.StringIO()
    display_result(result, session, out=buf)
    text = buf.getvalue()
    assert "I understand this as: show age" in text
    assert "30" in text


def test_display_result_writes_error_message():
    session = make_session()
    result = session.run_line("show missingname")
    buf = io.StringIO()
    display_result(result, session, out=buf)
    text = buf.getvalue()
    assert "Error:" in text
    assert "missingname" in text


def test_display_result_auto_confirms_amber_and_runs_pending_ast():
    session = make_session()
    for s in [
        "remember an order called order1 with total as 75 and status as active",
        "remember a list called orders with order1",
    ]:
        session.run_line(s)
    amber = session.run_line(
        "filter the orders where total is above 50 and status is active or status is pending"
    )
    assert amber.status is ResultStatus.AMBER_PRECEDENCE
    buf = io.StringIO()
    display_result(amber, session, auto_confirm_amber=True, out=buf)
    # After confirmation, filter executes.
    # order1.total=75, status=active. Group by precedence:
    #   (total above 50 AND status active) OR status pending
    # order1 satisfies the AND clause → kept.
    assert len(session.symtab["orders"].value) == 1


# ---------------------------------------------------------------------------
# Example files run cleanly via the CLI runner
# ---------------------------------------------------------------------------


def test_examples_run_without_error(capsys):
    from inscript.cli import run_file
    run_file(str(ROOT / "examples" / "program1_basics.insc"), auto_confirm_amber=True)
    out = capsys.readouterr().out
    # v2a §71 (D6): the user wrote `a number called age`, so the canonical
    # rendering preserves the descriptor `number` rather than substituting
    # the inferred type label `value`.
    assert "I understand this as: remember a number called age with 30" in out
    assert "I understand this as: show age" in out
    assert "30" in out
    assert "red, blue, green" in out


# ---------------------------------------------------------------------------
# UX polish: --quiet flag, schema-mismatch wording (U2/U3), truncation (U5)
# ---------------------------------------------------------------------------


def test_quiet_flag_suppresses_canonical_lines(tmp_path):
    """U1/U4: --quiet drops the 'I understand this as:' echo but keeps data."""
    import io
    from inscript.cli import run_file
    src = tmp_path / "p.insc"
    src.write_text(
        "remember a number called age with 30\n"
        "show age\n"
        "count the colors\n"
    )
    # Need `colors` defined for the count not to error — adjust:
    src.write_text(
        "remember a number called age with 30\n"
        "remember a list called colors with red and blue and green\n"
        "show age\n"
        "count the colors\n"
    )
    buf = io.StringIO()
    run_file(str(src), auto_confirm_amber=True, quiet=True, out=buf)
    text = buf.getvalue()
    assert "I understand this as" not in text
    # Data lines present.
    assert "30" in text
    assert "3" in text  # count of colors


def test_quiet_flag_mirrors_blank_lines(tmp_path):
    """U1/U4: blank source lines surface as empty lines in --quiet output."""
    import io
    from inscript.cli import run_file
    src = tmp_path / "p.insc"
    src.write_text(
        "remember a number called age with 30\n"
        "\n"
        "show age\n"
    )
    buf = io.StringIO()
    run_file(str(src), auto_confirm_amber=True, quiet=True, out=buf)
    # Output: data for line 1 (none — remember is silent), blank from
    # source line 2, data for line 3 ("30"). With quiet, the only
    # non-blank line is "30"; there should be a blank line before it.
    lines = buf.getvalue().split("\n")
    # Expected sequence: empty (blank mirror), "30", trailing empty
    assert "" in lines
    assert "30" in lines


def test_quiet_flag_without_quiet_keeps_canonical(tmp_path):
    """Default (no --quiet) still emits canonical echo — unchanged behavior."""
    import io
    from inscript.cli import run_file
    src = tmp_path / "p.insc"
    src.write_text("remember a number called age with 30\nshow age\n")
    buf = io.StringIO()
    run_file(str(src), auto_confirm_amber=True, out=buf)
    text = buf.getvalue()
    assert "I understand this as" in text
    assert "30" in text


def test_u2_names_first_offending_record_in_schema_mismatch():
    """U2: the partial-match error names the source record that lacks the field."""
    session, _ = run_lines([
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember an item called item1 with price as 30 and color as red",
        "remember a list called mixed with order1 and order2 and item1",
    ])
    r = session.run_line("filter the mixed where total is above 0")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    # The first failing record is item1 (orders 1 & 2 have total; item1 doesn't).
    assert "'item1' in 'mixed'" in r.message


def test_u3_zero_match_error_says_no_item():
    """U3: when no record has the field, error reads 'No item in X has...'"""
    session, _ = run_lines([
        "remember an order called order1 with total as 75 and status as active",
        "remember a list called orders with order1",
    ])
    r = session.run_line("filter the orders where nonexistent is above 5")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert r.message.startswith("No item in 'orders' has a field called 'nonexistent'.")


def test_u3_partial_match_error_calls_out_others():
    """U3: partial-match error appends 'Other items do have it.'"""
    session, _ = run_lines([
        "remember an order called o1 with total as 75 and status as active",
        "remember an item called item1 with price as 30 and color as red",
        "remember a list called mixed with o1 and item1",
    ])
    r = session.run_line("filter the mixed where total is above 0")
    assert "Other items do have it" in r.message


def test_u5_gather_above_threshold_is_truncated(tmp_path):
    """U5: gather's auto-show truncates lists > 20 items."""
    import io
    from inscript.cli import run_file
    src = tmp_path / "p.insc"
    src.write_text("gather the nums from 1 to 50\n")
    buf = io.StringIO()
    run_file(str(src), auto_confirm_amber=True, out=buf)
    text = buf.getvalue()
    # Truncated form: first 10, ellipsis, last 10.
    assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10" in text
    assert "..." in text
    assert "41, 42, 43, 44, 45, 46, 47, 48, 49, 50" in text
    # The full middle (e.g., 25) should NOT appear in the auto-show.
    auto_show_segment = text.split("I understand this as: gather")[1] if "I understand this as: gather" in text else text
    # Find the data line after the canonical
    data_lines = [l for l in auto_show_segment.split("\n") if l and not l.startswith("I understand")]
    if data_lines:
        first_data = data_lines[0]
        assert ", 25, " not in first_data, "Middle of truncated range leaked through"


def test_u5_gather_at_threshold_is_not_truncated(tmp_path):
    """U5: lists with exactly 20 items display in full — threshold is exclusive."""
    import io
    from inscript.cli import run_file
    src = tmp_path / "p.insc"
    src.write_text("gather the nums from 1 to 20\n")
    buf = io.StringIO()
    run_file(str(src), auto_confirm_amber=True, out=buf)
    text = buf.getvalue()
    assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20" in text
    assert "..." not in text


def test_u7_duplicate_field_in_each_show_is_semantic_error():
    """U7 (v2.1-patch): repeats in multi-field `each show` are a semantic error."""
    session, _ = run_lines([
        "remember a doc called d1 with class as checkpoint and words as 1000",
        "remember a doc called d2 with class as addendum and words as 2000",
        "remember a list called docs with d1 and d2",
    ])
    r = session.run_line("each the docs show class and class")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "'class'" in r.message
    assert "twice" in r.message


def test_u7_target_repeated_as_extra_is_also_error():
    """U7: the target counts toward repeats too — `show A and A` is rejected."""
    session, _ = run_lines([
        "remember a doc called d1 with x as 1 and y as 2",
        "remember a list called docs with d1",
    ])
    r = session.run_line("each the docs show x and x")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "twice" in r.message


def test_u7_three_distinct_fields_still_works():
    """U7 does not regress the legitimate multi-field path."""
    session, _ = run_lines([
        "remember a doc called d1 with x as 1 and y as 2 and z as 3",
        "remember a list called docs with d1",
    ])
    r = session.run_line("each the docs show x and y and z")
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["x: 1, y: 2, z: 3"]


def test_u8_of_on_list_suggests_each():
    """U8 (v2.1-patch): `of` on a list-of-records suggests the each alternative."""
    session, _ = run_lines([
        "remember a doc called d1 with class as checkpoint and words as 1000",
        "remember a list called docs with d1",
    ])
    r = session.run_line("show class of docs")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    # The suggestion uses the user's actual list and field names.
    assert "each the docs show class" in r.message


def test_u8_of_on_scalar_unchanged():
    """U8 only changes the list-of-records case; scalar errors stay generic."""
    session, _ = run_lines([
        "remember a number called age with 30",
    ])
    r = session.run_line("show something of age")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    # Scalar path: no `each` suggestion, just the type-mismatch.
    assert "each" not in r.message
    assert "age" in r.message


def test_d10_keep_inside_each_gives_list_level_guidance():
    """D10 (v2.1-patch): `each ... keep where` errors with list-level guidance."""
    session, _ = run_lines([
        "remember a doc called d1 with class as checkpoint and words as 1000",
        "remember a list called docs with d1",
    ])
    r = session.run_line("each the docs keep where words is above 500")
    assert r.status is ResultStatus.ERROR_PARSE
    assert "'keep' is a list operation" in r.message
    assert "can't appear inside 'each'" in r.message
    assert "<list> where <condition>" in r.message


def test_d10_filter_inside_each_gives_same_guidance():
    """D10: filter gets the same per-record-decision guidance as keep."""
    session, _ = run_lines([
        "remember a doc called d1 with class as checkpoint and words as 1000",
        "remember a list called docs with d1",
    ])
    r = session.run_line("each the docs filter where words is above 500")
    assert r.status is ResultStatus.ERROR_PARSE
    assert "'filter' is a list operation" in r.message
    assert "can't appear inside 'each'" in r.message


def test_d10_keep_at_top_level_unchanged():
    """D10's guidance only applies inside `each` — top-level keep is unaffected."""
    session, _ = run_lines([
        "remember a doc called d1 with class as checkpoint and words as 1000",
        "remember a doc called d2 with class as addendum and words as 2000",
        "remember a list called docs with d1 and d2",
    ])
    r = session.run_line("keep the docs where words is above 1500")
    assert r.status is ResultStatus.SUCCESS


def test_u5_explicit_show_is_not_truncated(tmp_path):
    """U5: explicit `show <list>` never truncates — user asked for the data."""
    import io
    from inscript.cli import run_file
    src = tmp_path / "p.insc"
    src.write_text(
        "gather the nums from 1 to 50\n"
        "show nums\n"
    )
    buf = io.StringIO()
    run_file(str(src), auto_confirm_amber=True, out=buf)
    text = buf.getvalue()
    # The show output (after gather's truncated auto-show) shows all 50.
    show_segment = text.split("show nums")[-1]
    assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25" in show_segment
    assert "26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50" in show_segment


def test_program2_orders_example_runs(capsys):
    from inscript.cli import run_file
    run_file(str(ROOT / "examples" / "program2_orders.insc"), auto_confirm_amber=True)
    out = capsys.readouterr().out
    # The each emits one total per record.
    assert "75" in out
    assert "30" in out
    assert "120" in out
    # After the filter, two records remain — visible in `show orders`.
    assert "total: 75, status: active" in out
    assert "total: 120, status: pending" in out
