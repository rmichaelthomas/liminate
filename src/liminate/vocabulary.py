"""Vocabulary tables and token types for Liminate v1 / v2a / v2d / v3a.

Sources:
- inception §11 (vocabulary table), §17 (verb signatures), §22 (lexer rules)
- v1a §29 (reserved words, 28-word total — superseded)
- v1c §47 (article `an`, reserved word count corrected to 29)
- v2a §67 (`keep` verb — non-destructive filter)
- v2a §68 (`of` connective — single-record field access)
- v2a §73 (updated vocabulary: 8 verbs, 10 connectives, 31 reserved words)
- v2d §99 (`choose` promoted from deferred to active verb)
- v2d §99 (`if` and `otherwise` connectives added)
- v2d §104 (updated vocabulary: 9 verbs, 12 connectives, 33 reserved words)
- v3a §112 (`finish` verb — exits listener mode immediately)
- v3a §108/§109 (`when`/`unless` connectives — promoted from V2_RESERVED)
- v3a §124 (updated vocabulary: 10 verbs, 14 connectives, 34 reserved words)
- v4a §137 (general-purpose pack verb contract — packs register verbs with
  slot signatures via JSON; pack words add to the active vocabulary on
  activation and are removed on deactivation; the base vocabulary stays
  permanently at 34 reserved words.)
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


# v1 / v2a / v2d / v3a verbs. v2a §67 added `keep`. v2d §99 promoted
# `choose` from the v2-deferred table to an active verb. v3a §112 adds
# `finish` — exits listener mode immediately and totally.
VERBS: frozenset[str] = frozenset({
    "remember", "show", "filter", "keep",
    "count", "gather", "combine", "each",
    "choose", "finish", "add",
})

# v1 / v2a / v2d / v3a connectives. v2a §68 added `of`. v2d §99 added
# `if` (introduces a `choose` condition) and `otherwise` (introduces a
# `choose` alternative branch). v3a §108/§109 promotes `when` (registers
# a reactive handler) and `unless` (guard clause on `when`) from
# V2_RESERVED to active connectives.
CONNECTIVES: frozenset[str] = frozenset({
    "where", "and", "or", "from", "with", "called", "to", "how", "as", "of",
    "if", "otherwise", "when", "unless",
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

# v2 deferred words — designed but not executable in v1. Reserved so
# user programs that use them as names will not silently break when v2
# ships (v1a §29). v2d §99 promoted `choose` to an active verb. v3a §108
# promoted `when` and `unless` to active connectives. `transform` and
# `compare` continue to be deferred per v2d §103 / v3a §124.
V2_RESERVED: frozenset[str] = frozenset({
    "transform", "compare",
})

# `equal` is the multi-word lookahead trigger for `equal to`. Reserved
# independently — allowing it as a name would make the lexer's behavior
# dependent on what word follows (v1a §29, v1c §47).
MULTI_WORD_RESERVED: frozenset[str] = frozenset({"equal"})

# All 35 reserved words. v3a §124 was 34 (+1 for `finish`). Liminate
# `add` verb addendum v1 §9: +1 for `add` (appends an item to a list).
ALL_RESERVED: frozenset[str] = (
    VERBS | CONNECTIVES | OPERATORS | ARTICLES | V2_RESERVED | MULTI_WORD_RESERVED
)


def reserved_category(word: str) -> str | None:
    """Return the user-facing category name for a reserved word.

    Used by the parser to produce the v1a §29 reserved-word error message:
    "The word '[word]' is reserved in Liminate — it's used as a [category]."
    Returns None if the word is not reserved.

    v4a §137: active pack verbs report as "verb"; active pack nouns
    report as "noun". Pack words are only reserved while the pack that
    declared them is loaded — the base vocabulary stays permanently at
    34 words.
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
    if word in _ACTIVE_PACK_VERBS:
        return "verb"
    if word in _ACTIVE_PACK_NOUNS:
        return "noun"
    return None


# ---------------------------------------------------------------------------
# v4a §137 — pack verb contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PackVerbSlot:
    """One slot in a pack-defined verb's signature.

    - `name` is the slot's internal identifier (used by execution definitions
      and in error messages).
    - `connective` is the connective word that introduces this slot at a
      call site (e.g. "to" in `navigate to <screen>`).
    - `required` is True when the slot must be filled.
    - `type_constraint`, when present, is the descriptor (or type label)
      the slot's resolved value must match — the semantic analyzer enforces
      it case-insensitively against the target record's descriptor.
    """
    name: str
    connective: str
    required: bool
    type_constraint: str | None = None


@dataclass(frozen=True)
class PackVerbExecution:
    """v4a §137 execution definition. v4a defines exactly one execution
    type — `set_value` — which sets `target_name` in the symbol table to
    the resolved value of `source_slot`."""
    type: str
    target_name: str | None = None
    source_slot: str | None = None


@dataclass(frozen=True)
class PackVerbSignature:
    word: str
    slots: tuple[PackVerbSlot, ...]
    execution: PackVerbExecution


# Active pack vocabulary, populated by `activate_pack_words` when a Session
# registers its domain packs. Mutating module state mirrors how the base
# VERBS/CONNECTIVES tables work — there's at most one active Session at a
# time in the CLI driver, and `Session.__init__` resets these tables before
# (re-)activating its own packs so test runs don't leak state between
# Sessions.
_ACTIVE_PACK_VERBS: dict[str, PackVerbSignature] = {}
_ACTIVE_PACK_NOUNS: set[str] = set()


def get_active_pack_verb(word: str) -> PackVerbSignature | None:
    """Return the signature for `word` if it's an active pack verb."""
    return _ACTIVE_PACK_VERBS.get(word)


def active_pack_verb_words() -> frozenset[str]:
    return frozenset(_ACTIVE_PACK_VERBS.keys())


def active_pack_nouns() -> frozenset[str]:
    return frozenset(_ACTIVE_PACK_NOUNS)


def activate_pack_words(
    verbs: list[PackVerbSignature] | None = None,
    nouns: list[str] | None = None,
) -> None:
    """Add the given pack verbs and nouns to the active vocabulary
    (v4a §137 / v1a §29). Each pack contributes additively; the caller
    decides when to reset via `deactivate_all_pack_words`. Duplicate
    pack verb registrations (same word) overwrite — packs are vetted
    by the Session, not by this table."""
    for sig in verbs or ():
        _ACTIVE_PACK_VERBS[sig.word] = sig
    for word in nouns or ():
        _ACTIVE_PACK_NOUNS.add(word)


def deactivate_all_pack_words() -> None:
    """Clear all pack-contributed vocabulary. Called by `Session.__init__`
    before (re-)activating its own packs so the active set always reflects
    the current Session's pack list."""
    _ACTIVE_PACK_VERBS.clear()
    _ACTIVE_PACK_NOUNS.clear()


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
    # v2d §99: condition (after `if`), consequence (after `:`), and
    # alternative (after `otherwise`, optional).
    "choose":   ["condition", "consequence", "alternative"],
    # v3a §112: `finish` is a slot-less verb — it takes no target,
    # condition, or value. It exits listener mode immediately and totally.
    "finish":   [],
    # Liminate `add` v1 §2: append an item to an existing list.
    "add":      ["item", "target"],
}
