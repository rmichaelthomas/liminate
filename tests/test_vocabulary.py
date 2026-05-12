"""Phase 1 gate tests: vocabulary tables and verb signatures."""

from inscript.vocabulary import (
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
    # v2a §73: 8 verbs (was 7 in v1; `keep` added in v2a §67).
    assert len(VERBS) == 8
    assert VERBS == {
        "remember", "show", "filter", "keep", "count",
        "gather", "combine", "each",
    }


def test_connective_count():
    # v2a §73: 10 connectives (was 9 in v1; `of` added in v2a §68).
    assert len(CONNECTIVES) == 10
    assert CONNECTIVES == {
        "where", "and", "or", "from", "with",
        "called", "to", "how", "as", "of",
    }


def test_operator_count():
    # 4 single-word operators; `equal to` is a multi-word lexer token.
    assert len(OPERATORS) == 4
    assert OPERATORS == {"is", "above", "below", "not"}


def test_article_count():
    # v1c §47 corrected: `an` is an article.
    assert len(ARTICLES) == 3
    assert ARTICLES == {"the", "a", "an"}


def test_delimiter_count():
    assert DELIMITERS == {":"}


def test_v2_reserved():
    assert len(V2_RESERVED) == 5
    assert V2_RESERVED == {"transform", "choose", "compare", "when", "unless"}


def test_multi_word_reserved():
    assert MULTI_WORD_RESERVED == {"equal"}


def test_total_reserved_count_is_31():
    # v2a §73: 31 reserved words total (was 29 in v1c §47; +1 for `keep`
    # in §67, +1 for `of` in §68).
    # 8 verbs + 10 connectives + 4 operators + 1 multi-word + 3 articles
    # + 3 v2 verbs + 2 v2 connectives = 31.
    assert len(ALL_RESERVED) == 31


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
    # Sanity-check slot lists from inception §17, refined per v1b/v1d/v2a.
    assert VERB_SIGNATURES["show"] == ["target"]
    assert VERB_SIGNATURES["count"] == ["target"]
    assert VERB_SIGNATURES["combine"] == ["target"]
    assert VERB_SIGNATURES["filter"] == ["target", "condition"]
    # v2a §67: keep has the same slots as filter.
    assert VERB_SIGNATURES["keep"] == ["target", "condition"]
    assert VERB_SIGNATURES["gather"] == ["name", "from", "to"]
    assert VERB_SIGNATURES["each"] == ["collection", "action"]
    assert VERB_SIGNATURES["remember"] == ["name", "value"]


def test_token_type_enum_members():
    members = {m.name for m in TokenType}
    assert members == {
        "VERB", "CONNECTIVE", "OPERATOR", "ARTICLE",
        "DELIMITER", "NUMBER", "UNKNOWN",
    }


def test_token_dataclass_construction():
    t = Token(type=TokenType.VERB, value="filter", position=0)
    assert t.type is TokenType.VERB
    assert t.value == "filter"
    assert t.position == 0
