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
- `includes` connective + `remove` verb addendum (12 verbs, 15 connectives,
  37 reserved words total).
- `within` connective addendum (12 verbs, 16 connectives, 38 reserved
  words total) — used by the session pack's `measure` verb for numeric
  tolerance.
- Metabolic Era batch 1 (13 verbs, 17 connectives, 40 reserved words
  total) — `weakens` verb (autonomous linear decay) and `over`
  connective (decay period).
- Normative Era batch 2 (14 verbs, 18 connectives, 42 reserved words
  total) — `require` verb (enforcement) and `then` connective
  (declared sequencing).
- Delegated/Epistemic Era batch 3 (16 verbs, 18 connectives, 44
  reserved words total) — `assign` verb (item-to-recipient mapping)
  and `expect` verb (non-halting tracked anticipation).
- Infrastructure Era (16 verbs, 19 connectives, 49 reserved words
  total) — `by` connective, `plus`/`minus` operators,
  `multiplied by`/`divided by` multi-word operators. Arithmetic
  expressions with PEMDAS precedence.
- Infrastructure Era batch 2 (17 verbs, 19 connectives, 51 reserved
  words total) — `sort` verb (in-place list reordering by field) and
  `reverse` operator (descending sort modifier).
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
    "choose", "finish", "add", "remove",
    # Metabolic Era batch 1: autonomous linear decay verb. Attaches
    # decay metadata to an existing numeric variable; the value falls
    # linearly to zero over a stated period (in abstract ticks).
    "weakens",
    # Normative Era batch 2: `require` evaluates a condition and halts
    # with REQUIREMENT_NOT_MET if false; silent on success.
    "require",
    # Delegated Era batch 3: `assign <item> to <recipient>` stores an
    # item-to-recipient mapping in the symbol table.
    "assign",
    # Epistemic Era batch 3: `expect <condition>` evaluates a condition
    # and emits a divergence output line on failure; never halts.
    "expect",
    # Infrastructure Era batch 2: `sort` reorders a list in place by a
    # field value. Default ascending; `reverse` modifier for descending.
    "sort",
})

# v1 / v2a / v2d / v3a connectives. v2a §68 added `of`. v2d §99 added
# `if` (introduces a `choose` condition) and `otherwise` (introduces a
# `choose` alternative branch). v3a §108/§109 promotes `when` (registers
# a reactive handler) and `unless` (guard clause on `when`) from
# V2_RESERVED to active connectives.
CONNECTIVES: frozenset[str] = frozenset({
    "where", "and", "or", "from", "with", "called", "to", "how", "as", "of",
    "if", "otherwise", "when", "unless", "includes", "within",
    # Metabolic Era batch 1: introduces the decay period in `weakens`.
    "over",
    # Normative Era batch 2: `then` sequences operations with declared
    # ordering intent. Parsed at the same level as `and` in operation
    # sequences; both produce SequenceNode, distinguished by the
    # `connectors` metadata field.
    "then",
    # Infrastructure Era: `by` introduces the second operand of the
    # multi-word arithmetic operators (`multiplied by`, `divided by`).
    # Reserved standalone for future use by the `transform` verb.
    "by",
})

# v1 single-word operators (inception §11). `equal to` is a multi-word
# operator combined by the lexer (inception §22) into a single OPERATOR
# token whose value is "equal_to" — see lexer.
OPERATORS: frozenset[str] = frozenset({
    "is", "above", "below", "not",
    # Infrastructure Era: arithmetic operators. `plus` and `minus` are
    # single-word; `multiplied by` and `divided by` are multi-word
    # (combined by the lexer; `multiplied` and `divided` live in
    # MULTI_WORD_RESERVED).
    "plus", "minus",
    # Infrastructure Era batch 2: `reverse` modifies `sort` direction
    # from ascending (default) to descending. Lives in OPERATORS so the
    # name-position check rejects it as a variable name.
    "reverse",
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
MULTI_WORD_RESERVED: frozenset[str] = frozenset({
    "equal",
    # Infrastructure Era: lookahead triggers for `multiplied by` and
    # `divided by`. Reserved independently so user programs can't name a
    # variable `multiplied` or `divided` and silently break the lexer.
    "multiplied", "divided",
})

# All 51 reserved words. 17 verbs, 19 connectives, 7 operators, 3
# articles, 2 V2-reserved, 3 multi-word reserved. v3a §124 was 34
# (+1 for `finish`). Liminate `add` verb addendum v1 §9: +1 for `add`
# (appends an item to a list). `includes` connective + `remove` verb
# addendum: +2 (list membership test in conditions, retract item from a
# list). `within` connective: +1 (numeric tolerance for the session
# pack's `measure` verb). Metabolic Era batch 1: +2 — `weakens` verb
# (autonomous linear decay) and `over` connective (introduces the decay
# period). Normative Era batch 2: +2 — `require` verb (enforcement)
# and `then` connective (declared sequencing). Delegated/Epistemic Era
# batch 3: +2 — `assign` (item-to-recipient mapping) and `expect`
# (tracked anticipation, non-halting divergence). Infrastructure Era:
# +5 — `by` connective, `plus`/`minus` operators, `multiplied` and
# `divided` multi-word lookahead triggers. Infrastructure Era batch 2:
# +2 — `sort` verb (in-place list reordering by a field) and `reverse`
# operator (descending sort modifier).
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
    declared them is loaded — the base vocabulary is the canonical
    surface (currently 51 reserved words; see module docstring).
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

    v2 (pack verb contract extension): `connective` may be None to indicate
    a positional (direct-object) slot. `value_type` selects what the parser
    accepts — "name" (UNKNOWN token only, default) or "value" (any value
    type via `_parse_value`).
    """
    name: str
    connective: str | None       # None = positional (direct object)
    required: bool
    type_constraint: str | None = None
    value_type: str = "name"     # "name" or "value"


# v2 — discriminated execution class union. Five frozen dataclasses, one
# per execution type. The interpreter dispatches with isinstance. The JSON
# `type` field is consumed only by the factory function in adapter.py.

@dataclass(frozen=True)
class SetValueExecution:
    target_name: str | None = None      # literal symbol name to store into
    target_slot: str | None = None      # resolve symbol name from this slot
    source_slot: str | None = None      # resolve value from this slot (name-vs-value special case)
    literal_value: str | None = None    # use this literal value


@dataclass(frozen=True)
class SubstringCheckExecution:
    check_slot: str
    against_slot: str


@dataclass(frozen=True)
class AppendToListExecution:
    target_name: str | None = None
    target_slot: str | None = None
    source_slot: str | None = None
    literal_value: str | None = None


@dataclass(frozen=True)
class SetFieldExecution:
    field_name: str
    target_name: str | None = None
    target_slot: str | None = None
    source_slot: str | None = None
    literal_value: str | None = None


@dataclass(frozen=True)
class CompareValuesExecution:
    left_slot: str
    right_slot: str
    comparison: str         # "equality" | "structural"
    on_mismatch: str        # "error" | "flag"
    status_target: str
    details_target: str | None  # required for "structural"


@dataclass(frozen=True)
class NumericExtractCompareExecution:
    check_slot: str          # slot name containing the claimed number
    against_slot: str        # slot name containing the source text (string)
    tolerance_slot: str      # slot name containing the tolerance number
    on_mismatch: str         # "error" | "flag"
    status_target: str       # symbol name for "within_tolerance" / "outside_tolerance"
    matched_target: str      # symbol name for the closest number found in source
    delta_target: str        # symbol name for the absolute difference


PackVerbExecution = (
    SetValueExecution
    | SubstringCheckExecution
    | AppendToListExecution
    | SetFieldExecution
    | CompareValuesExecution
    | NumericExtractCompareExecution
)


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
    # `remove` — retract an item from an existing list.
    "remove":   ["item", "target"],
    # Metabolic Era batch 1: `weakens <subject> over <period>`.
    "weakens":  ["subject", "schedule"],
    # Normative Era batch 2: `require <condition>`. Same condition
    # grammar as `choose if` / `where`.
    "require":  ["condition"],
    # Delegated Era batch 3: `assign <item> to <recipient>`.
    "assign":   ["item", "recipient"],
    # Epistemic Era batch 3: `expect <condition>`. Same condition
    # grammar as `require` / `choose if` / `where`.
    "expect":   ["condition"],
    # Infrastructure Era batch 2: `sort <target> by <field> [reverse]`.
    "sort":     ["target", "field"],
}


# ---------------------------------------------------------------------------
# Metabolic Era — autonomous linear decay value
# ---------------------------------------------------------------------------


@dataclass
class DecayingValue:
    """A numeric value with autonomous linear decay.

    Created by the `weakens` verb. The current value is computed on
    read as: max(0.0, initial_value - (initial_value / period) * ticks_elapsed).
    Floor at 0.0 — value never goes negative.

    `remember` (i.e. `_store`) on a DecayingValue with a new numeric
    value resets: ticks_elapsed → 0, initial_value → new value, period
    preserved. That is the reinforcement mechanic.
    """
    initial_value: float
    period: int | float
    ticks_elapsed: int = 0

    @property
    def current_value(self) -> float:
        if self.period <= 0:
            return 0.0
        decayed = (
            self.initial_value
            - (self.initial_value / self.period) * self.ticks_elapsed
        )
        return max(0.0, decayed)

    def tick(self) -> None:
        """Advance one tick. No-op once the value has reached the floor."""
        if self.current_value > 0.0:
            self.ticks_elapsed += 1

    def reinforce(self, new_value: float) -> None:
        """Reset decay with a new initial value. Period preserved."""
        self.initial_value = float(new_value)
        self.ticks_elapsed = 0
