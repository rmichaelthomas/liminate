"""Phase 1 gate tests: vocabulary tables and verb signatures."""

from liminate.vocabulary import (
    ALL_RESERVED,
    ARTICLES,
    CONNECTIVES,
    DELIMITERS,
    MULTI_WORD_RESERVED,
    OPERATORS,
    Token,
    TokenType,
    V2_RESERVED,
    VERB_SIGNATURES,
    VERBS,
    reserved_category,
)


def test_verb_count():
    # 17 verbs: 16 + 1 (`sort` — Infrastructure Era batch 2 in-place
    # list reordering by field).
    assert len(VERBS) == 17
    assert VERBS == {
        "remember", "show", "filter", "keep", "count",
        "gather", "combine", "each", "choose", "finish",
        "add", "remove", "weakens", "require",
        "assign", "expect", "sort",
    }


def test_connective_count():
    # 19 connectives: 18 + 1 (`by` — Infrastructure Era; introduces the
    # second operand of `multiplied by` / `divided by` and is reserved
    # standalone for future use by `transform`).
    assert len(CONNECTIVES) == 19
    assert CONNECTIVES == {
        "where", "and", "or", "from", "with",
        "called", "to", "how", "as", "of",
        "if", "otherwise",
        "when", "unless", "includes", "within", "over", "then",
        "by",
    }


def test_operator_count():
    # 7 single-word operators (was 6); Infrastructure Era batch 2 added
    # `reverse` as the descending-sort modifier. `equal to` /
    # `multiplied by` / `divided by` are multi-word lexer tokens
    # combined from MULTI_WORD_RESERVED triggers.
    assert len(OPERATORS) == 7
    assert OPERATORS == {
        "is", "above", "below", "not", "plus", "minus", "reverse",
    }


def test_article_count():
    # v1c §47 corrected: `an` is an article.
    assert len(ARTICLES) == 3
    assert ARTICLES == {"the", "a", "an"}


def test_delimiter_count():
    assert DELIMITERS == {":"}


def test_v2_reserved():
    # v3a §124: 2 deferred verbs remaining. `when` and `unless` moved
    # to CONNECTIVES in v3a §108/§109; `transform` and `compare`
    # continue to be deferred per v2d §103 / v3a §124.
    assert len(V2_RESERVED) == 2
    assert V2_RESERVED == {"transform", "compare"}


def test_multi_word_reserved():
    # Infrastructure Era: `multiplied` and `divided` added as multi-word
    # lookahead triggers (paired with `by` to form arithmetic operators).
    assert MULTI_WORD_RESERVED == {"equal", "multiplied", "divided"}


def test_total_reserved_count_is_51():
    # 51 reserved words total (Infrastructure Era batch 2). 17 verbs +
    # 19 connectives + 7 operators + 3 multi-word + 3 articles +
    # 2 v2-deferred verbs = 51.
    assert len(ALL_RESERVED) == 51


def test_reserved_sets_are_disjoint():
    # No word should appear in more than one category.
    sets = [VERBS, CONNECTIVES, OPERATORS, ARTICLES, V2_RESERVED, MULTI_WORD_RESERVED]
    total = sum(len(s) for s in sets)
    assert total == len(ALL_RESERVED)


def test_reserved_category_for_each_word():
    for w in VERBS:
        assert reserved_category(w) == "verb"
    for w in CONNECTIVES:
        assert reserved_category(w) == "connective"
    for w in OPERATORS:
        assert reserved_category(w) == "operator"
    for w in MULTI_WORD_RESERVED:
        assert reserved_category(w) == "operator"
    for w in ARTICLES:
        assert reserved_category(w) == "article"
    for w in V2_RESERVED:
        assert reserved_category(w) == "reserved word"


def test_reserved_category_returns_none_for_unknown():
    assert reserved_category("orders") is None
    assert reserved_category("widget") is None
    assert reserved_category("") is None


def test_verb_signatures_cover_all_verbs():
    assert set(VERB_SIGNATURES.keys()) == VERBS


def test_verb_signature_slot_shapes():
    # Sanity-check slot lists from inception §17, refined per v1b/v1d/v2a/v2d/v3a.
    assert VERB_SIGNATURES["show"] == ["target"]
    assert VERB_SIGNATURES["count"] == ["target"]
    assert VERB_SIGNATURES["combine"] == ["target"]
    assert VERB_SIGNATURES["filter"] == ["target", "condition"]
    # v2a §67: keep has the same slots as filter.
    assert VERB_SIGNATURES["keep"] == ["target", "condition"]
    assert VERB_SIGNATURES["gather"] == ["name", "from", "to"]
    assert VERB_SIGNATURES["each"] == ["collection", "action"]
    assert VERB_SIGNATURES["remember"] == ["name", "value"]
    # v2d §99: choose has three slots (alternative optional at use sites).
    assert VERB_SIGNATURES["choose"] == [
        "condition", "consequence", "alternative",
    ]
    # v3a §112: finish is slot-less — exits listener mode immediately.
    assert VERB_SIGNATURES["finish"] == []
    # Liminate `add` v1 §2: append an item to an existing list.
    assert VERB_SIGNATURES["add"] == ["item", "target"]
    # `remove` — retract an item from an existing list (same slot shape).
    assert VERB_SIGNATURES["remove"] == ["item", "target"]
    # Metabolic Era batch 1: `weakens <subject> over <period>`.
    assert VERB_SIGNATURES["weakens"] == ["subject", "schedule"]
    # Normative Era batch 2: `require <condition>`.
    assert VERB_SIGNATURES["require"] == ["condition"]
    # Delegated Era batch 3: `assign <item> to <recipient>`.
    assert VERB_SIGNATURES["assign"] == ["item", "recipient"]
    # Epistemic Era batch 3: `expect <condition>`.
    assert VERB_SIGNATURES["expect"] == ["condition"]
    # Infrastructure Era batch 2: `sort <target> by <field>`.
    assert VERB_SIGNATURES["sort"] == ["target", "field"]


def test_add_is_classified_as_verb():
    # Liminate `add` v1 §9: `add` is a base verb.
    assert reserved_category("add") == "verb"
    assert "add" in VERBS


def test_finish_is_classified_as_verb():
    # v3a §112: `finish` is a verb, not a connective. Used as a leaf
    # statement inside `when` action blocks.
    assert reserved_category("finish") == "verb"
    assert "finish" in VERBS


def test_when_and_unless_are_classified_as_connectives():
    # v3a §108/§109: `when` registers a reactive handler; `unless` is a
    # guard clause on `when`. They are connectives (statement-introducing
    # in `when`'s case), not verbs.
    assert reserved_category("when") == "connective"
    assert reserved_category("unless") == "connective"
    assert "when" in CONNECTIVES
    assert "unless" in CONNECTIVES
    assert "when" not in V2_RESERVED
    assert "unless" not in V2_RESERVED


def test_token_type_enum_members():
    members = {m.name for m in TokenType}
    assert members == {
        "VERB", "CONNECTIVE", "OPERATOR", "ARTICLE",
        "DELIMITER", "NUMBER", "UNKNOWN",
        # v2c §86: quoted strings emitted as a single token.
        "QUOTED_STRING",
    }


def test_token_dataclass_construction():
    t = Token(type=TokenType.VERB, value="filter", position=0)
    assert t.type is TokenType.VERB
    assert t.value == "filter"
    assert t.position == 0
