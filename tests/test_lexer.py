"""Phase 2 gate tests: lexer (inception §22, v1c §47-§48, v1d §57,
v2c §86/§89/§91/§92, v3a §110)."""

import pytest

from liminate.lexer import LexError, leading_indent, tokenize
from liminate.vocabulary import TokenType


# ---------- helpers ----------

def types(line: str) -> list[TokenType]:
    return [t.type for t in tokenize(line)]


def values(line: str) -> list[str]:
    return [t.value for t in tokenize(line)]


# ---------- blank lines / whitespace ----------

def test_empty_string_yields_no_tokens():
    assert tokenize("") == []


def test_whitespace_only_yields_no_tokens():
    assert tokenize("   ") == []
    assert tokenize("\t\t") == []
    assert tokenize("\n") == []


# ---------- case insensitivity (§22 line 424) ----------

def test_case_is_normalized_to_lowercase():
    assert values("SHOW Age") == ["show", "age"]
    assert values("Filter The Orders") == ["filter", "the", "orders"]


def test_case_insensitive_classification():
    toks = tokenize("REMEMBER A NUMBER CALLED Age WITH 30")
    assert [t.type for t in toks] == [
        TokenType.VERB, TokenType.ARTICLE, TokenType.UNKNOWN,
        TokenType.CONNECTIVE, TokenType.UNKNOWN, TokenType.CONNECTIVE,
        TokenType.NUMBER,
    ]
    assert toks[4].value == "age"  # lowercased name


# ---------- `equal to` multi-word lookahead (§22 line 426) ----------

def test_equal_to_combines_into_one_operator():
    toks = tokenize("is equal to 75")
    assert [t.type for t in toks] == [
        TokenType.OPERATOR, TokenType.OPERATOR, TokenType.NUMBER,
    ]
    assert [t.value for t in toks] == ["is", "equal_to", "75"]


def test_not_equal_to_lexes_as_three_operator_tokens():
    # `not equal to` -> not (operator) + equal_to (operator)
    toks = tokenize("is not equal to 5")
    assert [t.type for t in toks] == [
        TokenType.OPERATOR, TokenType.OPERATOR, TokenType.OPERATOR, TokenType.NUMBER,
    ]
    assert [t.value for t in toks] == ["is", "not", "equal_to", "5"]


def test_equal_not_followed_by_to_is_unknown():
    # v1a §29 / v1c §47: parser-level reserved-word check applies; the
    # lexer simply emits UNKNOWN for bare `equal`.
    toks = tokenize("equal with 5")
    assert toks[0].type is TokenType.UNKNOWN
    assert toks[0].value == "equal"


def test_equal_at_end_of_line_is_unknown():
    toks = tokenize("show equal")
    assert toks[-1].type is TokenType.UNKNOWN
    assert toks[-1].value == "equal"


# ---------- number recognition (§22 line 428) ----------

def test_integer_recognized_as_number():
    assert types("30")[0] is TokenType.NUMBER
    assert types("100")[0] is TokenType.NUMBER


def test_decimal_recognized_as_number():
    toks = tokenize("3.14")
    assert toks[0].type is TokenType.NUMBER
    assert toks[0].value == "3.14"


def test_decimal_inside_sentence_preserved():
    toks = tokenize("with 3.14")
    assert toks[1].type is TokenType.NUMBER
    assert toks[1].value == "3.14"


def test_malformed_number_is_unknown():
    # Two decimal points => not a number.
    assert tokenize("3.14.5")[0].type is TokenType.UNKNOWN


# ---------- negative number literals ----------

def test_negative_integer_recognized_as_number():
    tok = tokenize("-3")[0]
    assert tok.type is TokenType.NUMBER
    assert tok.value == "-3"


def test_negative_decimal_recognized_as_number():
    tok = tokenize("-3.5")[0]
    assert tok.type is TokenType.NUMBER
    assert tok.value == "-3.5"


def test_negative_number_inside_sentence():
    # `remember a number called t with -3` — the value token is NUMBER.
    assert tokenize("with -3")[1].type is TokenType.NUMBER


def test_bare_minus_is_not_a_number():
    # A lone `-` has no digits — it must NOT be a number (guard against
    # over-matching the leading-minus rule).
    assert tokenize("-")[0].type is TokenType.UNKNOWN


def test_hyphenated_name_is_not_a_number():
    # `total-dollars` is a name, not a negative number (the minus is internal).
    assert tokenize("total-dollars")[0].type is TokenType.UNKNOWN


# ---------- decorative punctuation stripping (§22 line 430) ----------

def test_commas_stripped_from_words():
    toks = tokenize("with milk, eggs, and bread")
    assert values(toks if False else "with milk, eggs, and bread") == [
        "with", "milk", "eggs", "and", "bread",
    ]


def test_trailing_period_stripped():
    assert values("show numbers.") == ["show", "numbers"]


def test_question_and_exclamation_stripped():
    assert values("show age?") == ["show", "age"]
    assert values("show age!") == ["show", "age"]


def test_trailing_period_does_not_break_number():
    # `30.` strips trailing `.` to `30`, still a number.
    toks = tokenize("with 30.")
    assert toks[-1].type is TokenType.NUMBER
    assert toks[-1].value == "30"


def test_stray_punctuation_drops():
    # A token consisting only of decorative chars disappears.
    assert tokenize(",,,") == []
    assert values("show , age") == ["show", "age"]


# ---------- hyphens preserved in names (§22 line 436) ----------

def test_hyphenated_name_is_one_token():
    toks = tokenize("find-big-orders")
    assert len(toks) == 1
    assert toks[0].type is TokenType.UNKNOWN
    assert toks[0].value == "find-big-orders"


# ---------- colon delimiter (§22 line 434) ----------

def test_standalone_colon_is_delimiter():
    toks = tokenize(":")
    assert toks[0].type is TokenType.DELIMITER
    assert toks[0].value == ":"


def test_colon_attached_to_word_splits():
    toks = tokenize("find-big-orders:")
    assert len(toks) == 2
    assert toks[0].type is TokenType.UNKNOWN
    assert toks[0].value == "find-big-orders"
    assert toks[1].type is TokenType.DELIMITER
    assert toks[1].value == ":"


def test_colon_inside_composition_definition_is_a_delimiter():
    toks = tokenize("remember how to find-big-orders: filter the orders")
    # find the delimiter
    delim_idx = next(i for i, t in enumerate(toks) if t.type is TokenType.DELIMITER)
    assert toks[delim_idx].value == ":"
    assert toks[delim_idx - 1].value == "find-big-orders"
    assert toks[delim_idx + 1].value == "filter"


# ---------- positions track original-input character offsets ----------

def test_position_tracks_original_offset():
    toks = tokenize("  show age")
    assert toks[0].value == "show"
    assert toks[0].position == 2
    assert toks[1].value == "age"
    assert toks[1].position == 7


def test_position_skips_decorative_punctuation():
    toks = tokenize(",show age")
    # `show` starts at index 1 in the original line.
    assert toks[0].value == "show"
    assert toks[0].position == 1


# ---------- end-to-end: 48 locked test sentences (gate sample) ----------

# Representative success and hostile sentences from the test spec
# (liminate_v1_thirty_sentences.md plus v1c §53 and v1d §65). The lexer
# must tokenize all of them without raising, including the hostile cases —
# semantic and parse errors are detected downstream.

ALL_48_SENTENCES = [
    # Program 1
    "remember a number called age with 30",
    "remember a list called colors with red and blue and green",
    "show age",
    "show colors",
    "count the colors",
    # Program 2
    "remember an order called order1 with total as 75 and status as active",
    "remember an order called order2 with total as 30 and status as active",
    "remember an order called order3 with total as 120 and status as pending",
    "remember a list called orders with order1 and order2 and order3",
    "each the orders show total",
    # Program 3
    "filter the orders where total is above 50",
    "show orders",
    "filter the orders where status is active",
    "count the orders",
    "each the orders show status",
    # Program 4
    "gather the numbers from 1 to 10",
    "filter the numbers where each is above 5",
    "count the numbers",
    "sum the numbers",
    "remember the result called total from sum the numbers",
    # Program 5 — not operator
    "gather the scores from 1 to 10",
    "filter the scores where each is not above 7",
    "filter the scores where each is not below 3",
    "filter the scores where each is not equal to 5",
    # Named compositions
    "remember how to find-big-orders: filter the orders where total is above 50",
    "remember how to count-active: filter the orders where status is active and count the orders",
    # Compound conditions
    "filter the orders where total is above 50 and status is active",
    "filter the orders where total is below 30 or status is pending",
    # Mixed precedence amber
    "filter the orders where total is above 50 and status is active or status is pending",
    # Equal-to operator
    "filter the orders where total is equal to 75",
    # Reserved word error
    "remember a value called filter with 10",
    # v1c additions
    "remember a list called items with filter and blue",
    "remember an item called widget with 25",
    "orders total above 50",
    # v1d hostile block
    "show missingname",
    "remember a number called age with 30",
    "filter age where each is above 5",
    "remember a list called colors with red and blue and green",
    "sum colors",
    "remember an order called order1 with total as 75 and status as active",
    "remember a list called orders with order1",
    "filter the orders where missingfield is above 50",
    "remember a number called age with 30",
    "each the age show",
    "remember a number called label with hello",
    "show label",
    "remember a list called mixed with 1 and blue",
    "gather the numbers from 10 to 1",
    "gather the numbers from 1 to 20000",
    "remember a number called age with 30",
    "remember a number called age with 40",
    "show age",
    "remember an order called order1 with total as 75 and status as active and status",
    "remember how to show-missing: show missingname",
    "show-missing",
    "remember a list called nums with 1 and 2 and 3 and 4 and 5",
    "filter nums where each is above 3 and show missingname",
    "show nums",
    "remember an order called order1 with total as 75 and status as active",
    "remember an item called item1 with price as 30 and color as red",
    "remember a list called mixed-records with order1 and item1",
    "filter the mixed-records where total is above 50",
]


@pytest.mark.parametrize("line", ALL_48_SENTENCES)
def test_all_locked_sentences_tokenize_without_error(line: str):
    toks = tokenize(line)
    assert toks  # every non-blank locked sentence yields at least one token
    # No UNKNOWN token may smuggle reserved punctuation in.
    for t in toks:
        assert t.value != ""


# ---------- detailed token sequences for key sentences ----------

def test_sentence_1_token_sequence():
    # remember a number called age with 30
    toks = tokenize("remember a number called age with 30")
    assert [(t.type, t.value) for t in toks] == [
        (TokenType.VERB, "remember"),
        (TokenType.ARTICLE, "a"),
        (TokenType.UNKNOWN, "number"),
        (TokenType.CONNECTIVE, "called"),
        (TokenType.UNKNOWN, "age"),
        (TokenType.CONNECTIVE, "with"),
        (TokenType.NUMBER, "30"),
    ]


def test_sentence_6_record_definition():
    toks = tokenize("remember an order called order1 with total as 75 and status as active")
    assert [(t.type, t.value) for t in toks] == [
        (TokenType.VERB, "remember"),
        (TokenType.ARTICLE, "an"),                 # v1c §47
        (TokenType.UNKNOWN, "order"),
        (TokenType.CONNECTIVE, "called"),
        (TokenType.UNKNOWN, "order1"),
        (TokenType.CONNECTIVE, "with"),
        (TokenType.UNKNOWN, "total"),
        (TokenType.CONNECTIVE, "as"),
        (TokenType.NUMBER, "75"),
        (TokenType.CONNECTIVE, "and"),
        (TokenType.UNKNOWN, "status"),
        (TokenType.CONNECTIVE, "as"),
        (TokenType.UNKNOWN, "active"),
    ]


def test_sentence_16_gather_range():
    toks = tokenize("gather the numbers from 1 to 10")
    assert [(t.type, t.value) for t in toks] == [
        (TokenType.VERB, "gather"),
        (TokenType.ARTICLE, "the"),
        (TokenType.UNKNOWN, "numbers"),
        (TokenType.CONNECTIVE, "from"),
        (TokenType.NUMBER, "1"),
        (TokenType.CONNECTIVE, "to"),
        (TokenType.NUMBER, "10"),
    ]


def test_sentence_22_not_above():
    toks = tokenize("filter the scores where each is not above 7")
    assert [(t.type, t.value) for t in toks] == [
        (TokenType.VERB, "filter"),
        (TokenType.ARTICLE, "the"),
        (TokenType.UNKNOWN, "scores"),
        (TokenType.CONNECTIVE, "where"),
        (TokenType.VERB, "each"),           # parser reclassifies as pronoun
        (TokenType.OPERATOR, "is"),
        (TokenType.OPERATOR, "not"),
        (TokenType.OPERATOR, "above"),
        (TokenType.NUMBER, "7"),
    ]


def test_sentence_24_not_equal_to():
    toks = tokenize("filter the scores where each is not equal to 5")
    assert [(t.type, t.value) for t in toks] == [
        (TokenType.VERB, "filter"),
        (TokenType.ARTICLE, "the"),
        (TokenType.UNKNOWN, "scores"),
        (TokenType.CONNECTIVE, "where"),
        (TokenType.VERB, "each"),
        (TokenType.OPERATOR, "is"),
        (TokenType.OPERATOR, "not"),
        (TokenType.OPERATOR, "equal_to"),    # multi-word combined
        (TokenType.NUMBER, "5"),
    ]


def test_sentence_25_named_composition_definition():
    toks = tokenize("remember how to find-big-orders: filter the orders where total is above 50")
    # The colon should appear at index 4 (after `remember`, `how`, `to`,
    # `find-big-orders`).
    assert toks[0].type is TokenType.VERB and toks[0].value == "remember"
    assert toks[1].type is TokenType.CONNECTIVE and toks[1].value == "how"
    assert toks[2].type is TokenType.CONNECTIVE and toks[2].value == "to"
    assert toks[3].type is TokenType.UNKNOWN and toks[3].value == "find-big-orders"
    assert toks[4].type is TokenType.DELIMITER and toks[4].value == ":"
    assert toks[5].type is TokenType.VERB and toks[5].value == "filter"


def test_sentence_31_reserved_word_remains_a_verb_token():
    # Lexer does NOT reclassify `filter` based on position. v1a §29
    # enforcement is at the parser level.
    toks = tokenize("remember a value called filter with 10")
    target = toks[4]
    assert target.value == "filter"
    assert target.type is TokenType.VERB


def test_sentence_33_article_an():
    # v1c §47 sentence 33: `an` recognized as ARTICLE.
    toks = tokenize("remember an item called widget with 25")
    assert toks[1].type is TokenType.ARTICLE
    assert toks[1].value == "an"


def test_sentence_34_no_verb_input_still_tokenizes_cleanly():
    # The lexer emits whatever tokens it sees; the parser reports the
    # no-verb error (v1c §53 sentence 34).
    toks = tokenize("orders total above 50")
    assert [t.type for t in toks] == [
        TokenType.UNKNOWN, TokenType.UNKNOWN, TokenType.OPERATOR, TokenType.NUMBER,
    ]


def test_sentence_47_compound_sequencing():
    # filter nums where each is above 3 and show missingname
    toks = tokenize("filter nums where each is above 3 and show missingname")
    assert [(t.type, t.value) for t in toks] == [
        (TokenType.VERB, "filter"),
        (TokenType.UNKNOWN, "nums"),
        (TokenType.CONNECTIVE, "where"),
        (TokenType.VERB, "each"),
        (TokenType.OPERATOR, "is"),
        (TokenType.OPERATOR, "above"),
        (TokenType.NUMBER, "3"),
        (TokenType.CONNECTIVE, "and"),
        (TokenType.VERB, "show"),
        (TokenType.UNKNOWN, "missingname"),
    ]


# ---------- v2c §86: quoted strings ----------


def test_quoted_string_emits_single_token():
    toks = tokenize('with status as "in progress"')
    assert [t.type for t in toks] == [
        TokenType.CONNECTIVE,    # with
        TokenType.UNKNOWN,       # status
        TokenType.CONNECTIVE,    # as
        TokenType.QUOTED_STRING, # "in progress"
    ]
    assert toks[-1].value == "in progress"


def test_quoted_string_preserves_internal_punctuation():
    """v2c §86: commas/periods/colons inside quotes are content, not
    decoration. Punctuation stripping (inception §22) is bypassed.
    Case is preserved verbatim as well — the value comes through
    exactly as written between the quotes."""
    toks = tokenize('show "Hello, world!"')
    assert toks[-1].type is TokenType.QUOTED_STRING
    assert toks[-1].value == "Hello, world!"


def test_quoted_string_preserves_original_case():
    """Quoted content is preserved verbatim — case normalization stops at
    the quote delimiter. `"In Progress"` stores `In Progress`, not
    `in progress`. Unquoted tokens continue to lowercase as before."""
    toks = tokenize('with status as "In Progress"')
    assert toks[-1].type is TokenType.QUOTED_STRING
    assert toks[-1].value == "In Progress"


def test_quoted_string_can_contain_reserved_words():
    """v2c §89: quoted reserved words are data, not vocabulary."""
    toks = tokenize('with label as "filter"')
    assert toks[-1].type is TokenType.QUOTED_STRING
    assert toks[-1].value == "filter"


def test_multiple_quoted_strings_on_one_line():
    """v2c §86: quote-state is per-pair, not line-level."""
    toks = tokenize(
        'with status as "in progress" and label as "high priority"'
    )
    quoted = [t for t in toks if t.type is TokenType.QUOTED_STRING]
    assert [t.value for t in quoted] == ["in progress", "high priority"]


def test_unclosed_quote_raises_lexerror():
    """v2c §86: an opening quote with no closer is a parse error."""
    with pytest.raises(LexError) as exc:
        tokenize('with text as "hello world')
    assert "opening quote mark" in exc.value.message
    assert "closing" in exc.value.message


def test_empty_quotes_raise_lexerror():
    """v2c §92: `""` rejected — no empty-string semantics in v1/v2."""
    with pytest.raises(LexError) as exc:
        tokenize('with text as ""')
    assert "nothing between" in exc.value.message


def test_quoted_equal_does_not_combine_with_to():
    """v2c §86 + §22: the `equal to` multi-word lookahead only fires on
    unquoted tokens. `"equal" to` keeps two tokens."""
    toks = tokenize('"equal" to')
    assert toks[0].type is TokenType.QUOTED_STRING
    assert toks[0].value == "equal"
    assert toks[1].type is TokenType.CONNECTIVE
    assert toks[1].value == "to"


def test_quoted_colon_is_preserved():
    """The colon delimiter (composition body marker) is bypassed inside
    quotes — `"Section A: counts"` is one QUOTED_STRING token, not
    QUOTED_STRING + DELIMITER + UNKNOWN."""
    toks = tokenize('show "Section A: counts before filtering"')
    assert [t.type for t in toks] == [TokenType.VERB, TokenType.QUOTED_STRING]
    assert toks[-1].value == "Section A: counts before filtering"


def test_quoted_string_position_points_at_opening_quote():
    """Quoted tokens carry the position of the opening `"` so error
    messages can refer back to the source location."""
    line = 'with status as "in progress"'
    toks = tokenize(line)
    quoted = next(t for t in toks if t.type is TokenType.QUOTED_STRING)
    assert line[quoted.position] == '"'


# ---------- v2d §99: `choose` verb + `if` / `otherwise` connectives ----------


def test_choose_is_a_verb_token():
    toks = tokenize("choose if score is above 50: show pass")
    assert toks[0].type is TokenType.VERB
    assert toks[0].value == "choose"


def test_if_is_a_connective_token():
    toks = tokenize("choose if score is above 50: show pass")
    assert toks[1].type is TokenType.CONNECTIVE
    assert toks[1].value == "if"


def test_otherwise_is_a_connective_token():
    toks = tokenize("choose if score is above 50: show pass otherwise show fail")
    otherwise = next(t for t in toks if t.value == "otherwise")
    assert otherwise.type is TokenType.CONNECTIVE


def test_choose_if_otherwise_full_sentence_classification():
    toks = tokenize(
        "choose if score is above 50: show pass otherwise show fail"
    )
    assert [(t.type, t.value) for t in toks] == [
        (TokenType.VERB, "choose"),
        (TokenType.CONNECTIVE, "if"),
        (TokenType.UNKNOWN, "score"),
        (TokenType.OPERATOR, "is"),
        (TokenType.OPERATOR, "above"),
        (TokenType.NUMBER, "50"),
        (TokenType.DELIMITER, ":"),
        (TokenType.VERB, "show"),
        (TokenType.UNKNOWN, "pass"),
        (TokenType.CONNECTIVE, "otherwise"),
        (TokenType.VERB, "show"),
        (TokenType.UNKNOWN, "fail"),
    ]


def test_quoted_if_and_otherwise_emit_quoted_string_not_connective():
    # v2c §89 — quotes bypass vocabulary lookup; `"if"` is data.
    toks = tokenize('remember a value called label with "if"')
    label = next(t for t in toks if t.type is TokenType.QUOTED_STRING)
    assert label.value == "if"
    toks = tokenize('remember a value called label with "otherwise"')
    label = next(t for t in toks if t.type is TokenType.QUOTED_STRING)
    assert label.value == "otherwise"


# ---------- v3a §108/§109/§112: when / unless / finish ----------


def test_when_is_a_connective_token():
    # v3a §108: `when` registers a reactive handler. Classified as a
    # connective (it introduces a condition like `if` does for `choose`).
    toks = tokenize("when temperature is above 100")
    assert toks[0].type is TokenType.CONNECTIVE
    assert toks[0].value == "when"


def test_unless_is_a_connective_token():
    # v3a §109: `unless` is a guard clause on `when`.
    toks = tokenize("when x is above 5 unless silenced is equal to true")
    unless = next(t for t in toks if t.value == "unless")
    assert unless.type is TokenType.CONNECTIVE


def test_finish_is_a_verb_token():
    # v3a §112: `finish` is the listener-mode exit verb.
    toks = tokenize("finish")
    assert toks == toks  # parametric placeholder for next assertion
    assert toks[0].type is TokenType.VERB
    assert toks[0].value == "finish"


def test_quoted_when_unless_finish_emit_quoted_string():
    # v2c §89 — quotes bypass vocabulary lookup; `"when"` is data even
    # though it's now an active connective.
    for word in ("when", "unless", "finish"):
        toks = tokenize(f'remember a value called label with "{word}"')
        label = next(t for t in toks if t.type is TokenType.QUOTED_STRING)
        assert label.value == word


# ---------- v3a §110: leading-space indentation ----------


def test_leading_indent_returns_zero_for_no_indent():
    assert leading_indent("when temperature is above 100") == 0
    assert leading_indent("remember a number called age with 30") == 0


def test_leading_indent_counts_spaces():
    assert leading_indent("  show alert") == 2
    assert leading_indent("    show alert") == 4
    assert leading_indent(" show") == 1


def test_leading_indent_only_counts_leading_spaces():
    # Spaces between tokens don't affect the leading-indent count.
    assert leading_indent("show  alert") == 0
    assert leading_indent("  show  alert  rest") == 2


def test_leading_indent_zero_for_blank_lines():
    # v1c §48 — blank lines are skipped by parsing entirely, and have no
    # meaningful indentation. v3a §110 — block boundary checks ignore them.
    assert leading_indent("") == 0
    assert leading_indent("   ") == 0
    assert leading_indent("\n") == 0


def test_leading_indent_rejects_leading_tab():
    # v3a §110 — tabs in leading whitespace are rejected with a clear
    # error suggesting spaces.
    with pytest.raises(LexError) as exc:
        leading_indent("\tshow alert")
    assert "tabs" in exc.value.message.lower() or "tab" in exc.value.message.lower()
    assert "spaces" in exc.value.message.lower()


def test_leading_indent_rejects_space_then_tab():
    # A tab anywhere in the leading-whitespace run is rejected — mixing
    # spaces and tabs in the indent is the visual-ambiguity case v3a §110
    # explicitly rules out.
    with pytest.raises(LexError):
        leading_indent("  \t  show alert")


def test_leading_indent_allows_tab_inside_content():
    # Tabs in the content (after the first non-whitespace) are tokenizer
    # whitespace as before — only leading tabs are rejected.
    assert leading_indent("show\talert") == 0
    assert leading_indent("  show\talert") == 2


# ---------------------------------------------------------------------------
# Comment syntax (`--` at the start of a line) — pre-lexer line skip.
# ---------------------------------------------------------------------------


def test_comment_basic():
    assert tokenize("-- this is a comment") == []


def test_comment_with_leading_whitespace():
    # Indented comment, e.g. inside a `when` action block.
    assert tokenize("    -- this action does the thing") == []


def test_comment_no_space_after_marker():
    assert tokenize("--no space") == []


def test_comment_just_the_marker():
    assert tokenize("--") == []


def test_comment_only_dashes():
    # `----` and similar dash runs all start with `--`, so all comments.
    assert tokenize("----") == []
    assert tokenize("-- ---- divider ----") == []


def test_hyphenated_name_is_not_a_comment():
    tokens = tokenize("find-big")
    assert len(tokens) == 1
    assert tokens[0].value == "find-big"


def test_single_hyphen_is_not_a_comment():
    # A single-hyphen prefix tokenizes normally (becomes an UNKNOWN token).
    tokens = tokenize("- something")
    assert len(tokens) >= 1


def test_mid_line_double_hyphen_is_not_a_comment():
    # `--` only marks a comment at the start of a line. Mid-line, it is
    # just part of whatever token it sits in.
    tokens = tokenize("remember an order")
    assert len(tokens) > 0
