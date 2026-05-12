"""Vocabulary tables and token types for Inscript v1 / v2a.

Sources:
- inception §11 (vocabulary table), §17 (verb signatures), §22 (lexer rules)
- v1a §29 (reserved words, 28-word total — superseded)
- v1c §47 (article `an`, reserved word count corrected to 29)
- v2a §67 (`keep` verb — non-destructive filter)
- v2a §68 (`of` connective — single-record field access)
- v2a §73 (updated vocabulary: 8 verbs, 10 connectives, 31 reserved words)

D7_DEFERRED: Multi-word string values are deferred to a dedicated v2
checkpoint per v2a §72. The lexer's whitespace-splitting rule (§22, §46)
remains authoritative; multi-word concepts in v1/v2a are expressed via
hyphenation (e.g. `gap-inventory`). Three candidate approaches (quoting,
hyphenation convention, multi-word phrase spans) are catalogued in the
v2 Design Triage (May 12, 2026) §5.
"""

from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    VERB = "VERB"
    CONNECTIVE = "CONNECTIVE"
    OPERATOR = "OPERATOR"
    ARTICLE = "ARTICLE"
    DELIMITER = "DELIMITER"
    NUMBER = "NUMBER"
    UNKNOWN = "UNKNOWN"
    # v2c §86: a quoted string emitted by the lexer as a single token,
    # bypasses vocabulary lookup (§89) and is valid only in value
    # positions per §87.
    QUOTED_STRING = "QUOTED_STRING"


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


# v1 / v2a verbs (inception §11; `keep` added in v2a §67).
VERBS: frozenset[str] = frozenset({
    "remember", "show", "filter", "keep",
    "count", "gather", "combine", "each",
})

# v1 / v2a connectives (inception §11; `of` added in v2a §68).
CONNECTIVES: frozenset[str] = frozenset({
    "where", "and", "or", "from", "with", "called", "to", "how", "as", "of",
})

# v1 single-word operators (inception §11). `equal to` is a multi-word
# operator combined by the lexer (inception §22) into a single OPERATOR
# token whose value is "equal_to" — see lexer.
OPERATORS: frozenset[str] = frozenset({
    "is", "above", "below", "not",
})

# v1 articles. `an` added in v1c §47 (previously the table listed `the`, `a`).
ARTICLES: frozenset[str] = frozenset({
    "the", "a", "an",
})

# Lone delimiter (inception §22)
DELIMITERS: frozenset[str] = frozenset({":"})

# v2 deferred words — designed but not executable in v1. Reserved now so
# user programs that use them as names will not silently break when v2 ships
# (v1a §29).
V2_RESERVED: frozenset[str] = frozenset({
    "transform", "choose", "compare", "when", "unless",
})

# `equal` is the multi-word lookahead trigger for `equal to`. Reserved
# independently — allowing it as a name would make the lexer's behavior
# dependent on what word follows (v1a §29, v1c §47).
MULTI_WORD_RESERVED: frozenset[str] = frozenset({"equal"})

# All 31 reserved words (v2a §73: was 29 in v1c §47; +1 for `keep`, +1 for `of`).
ALL_RESERVED: frozenset[str] = (
    VERBS | CONNECTIVES | OPERATORS | ARTICLES | V2_RESERVED | MULTI_WORD_RESERVED
)


def reserved_category(word: str) -> str | None:
    """Return the user-facing category name for a reserved word.

    Used by the parser to produce the v1a §29 reserved-word error message:
    "The word '[word]' is reserved in Inscript — it's used as a [category]."
    Returns None if the word is not reserved.
    """
    if word in VERBS:
        return "verb"
    if word in CONNECTIVES:
        return "connective"
    if word in OPERATORS or word in MULTI_WORD_RESERVED:
        return "operator"
    if word in ARTICLES:
        return "article"
    if word in V2_RESERVED:
        return "reserved word"
    return None


# Verb signatures (inception §17, refined by v1b/v1c/v1d). Each verb maps
# to the ordered list of slot names the parser must fill. Detailed parsing
# rules live in parser.py — this dict is the index of slots used by the
# reorderer and by tests as a structural reference.
VERB_SIGNATURES: dict[str, list[str]] = {
    "remember": ["name", "value"],
    "show":     ["target"],
    "filter":   ["target", "condition"],
    # v2a §67: `keep` shares filter's slots; only the interpreter differs
    # (filter mutates in place; keep returns a new list, source unchanged).
    "keep":     ["target", "condition"],
    "count":    ["target"],
    "gather":   ["name", "from", "to"],
    "combine":  ["target"],
    "each":     ["collection", "action"],
}
