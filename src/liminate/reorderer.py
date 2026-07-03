"""Reorderer for Liminate v1.

Sources:
- inception §17 (slot-filling architecture)
- v1d §55 (v1 reorderer scope — narrow, table-driven)
- v1c §50 (output taxonomy)

The v1 parser expects canonical word order. This module accepts a small
table of documented permutations and rejects everything else with a
canonical suggestion. The broader free-order acceptance is a target for
the tile interface, not the v1 text interpreter (v1d §55).

Acceptance table (v1d §55):

| Permutation                                  | Behavior                |
|----------------------------------------------|-------------------------|
| Canonical order                              | pass through            |
| Article + target before verb                 | move verb to front      |
| Target before verb (no article)              | move verb to front      |
| Condition elements scrambled                 | reject with hint        |
| Verb at end                                  | reject with hint        |
| Otherwise scrambled                          | reject with hint        |

The reorderer passes through silently when no VERB token is present —
the parser checks for a named-composition call (v1b §41) and otherwise
raises a no-verb error (v1c §53 sentence 34).
"""

from __future__ import annotations

from .result import LiminateResult, ResultStatus
from .vocabulary import Token, TokenType

ReorderOutput = list[Token] | LiminateResult


def reorder(tokens: list[Token]) -> ReorderOutput:
    """Reorder a token list into canonical form, or report an error."""
    if not tokens:
        return tokens

    # Temporal-Boundary Era: statement-initial `starting` and/or `until`
    # connectives are pass-through prefixes (same pattern as `inherited`).
    # Each is followed by a QUOTED_STRING date token. Strip the temporal
    # prefix, reorder the remainder, re-prepend. Placed BEFORE the
    # `inherited` check so the canonical order
    # `starting ... until ... inherited <verb> ...` is preserved.
    temporal_prefix: list[Token] = []
    rest_start = 0
    if (
        tokens[0].type is TokenType.CONNECTIVE
        and tokens[0].value == "starting"
        and len(tokens) > 1
        and tokens[1].type is TokenType.QUOTED_STRING
    ):
        temporal_prefix.extend([tokens[0], tokens[1]])
        rest_start = 2

    if (
        rest_start < len(tokens)
        and tokens[rest_start].type is TokenType.CONNECTIVE
        and tokens[rest_start].value == "until"
        and rest_start + 1 < len(tokens)
        and tokens[rest_start + 1].type is TokenType.QUOTED_STRING
    ):
        temporal_prefix.extend([tokens[rest_start], tokens[rest_start + 1]])
        rest_start = rest_start + 2

    if temporal_prefix:
        rest = reorder(tokens[rest_start:])
        if isinstance(rest, list):
            return temporal_prefix + rest
        return rest  # propagate a LiminateResult error from the remainder

    # Meta-Structural Era batch 3: a statement-initial `inherited` operator
    # is a pass-through prefix. The canonical verb statement begins after
    # it, so reorder the remainder and re-prepend `inherited` unchanged.
    if (
        tokens[0].type is TokenType.OPERATOR
        and tokens[0].value == "inherited"
    ):
        rest = reorder(tokens[1:])
        if isinstance(rest, list):
            return [tokens[0]] + rest
        return rest  # propagate a LiminateResult error from the remainder

    verb_idx = _find_first_verb(tokens)
    if verb_idx is None:
        # Defer to the parser (named-composition fallback per v1b §41,
        # or no-verb error per v1c §53 sentence 34).
        return tokens

    leading_articles_end = _skip_leading_articles(tokens)

    if verb_idx == leading_articles_end:
        # Verb is canonical (modulo a leading article); validate the
        # first `where` clause has a canonical condition head.
        return _validate_where_head(tokens)

    prefix = tokens[:verb_idx]
    if _is_valid_target_prefix(prefix):
        moved = [tokens[verb_idx]] + prefix + tokens[verb_idx + 1:]
        return _validate_where_head(moved)

    return LiminateResult(
        status=ResultStatus.ERROR_PARSE,
        message=(
            "I couldn't parse this. Try putting the verb at the front, "
            "for example: filter the orders where total is above 50."
        ),
        executed=False,
    )


def _find_first_verb(tokens: list[Token]) -> int | None:
    for i, t in enumerate(tokens):
        if t.type is TokenType.VERB:
            return i
    return None


def _skip_leading_articles(tokens: list[Token]) -> int:
    i = 0
    while i < len(tokens) and tokens[i].type is TokenType.ARTICLE:
        i += 1
    return i


def _is_valid_target_prefix(prefix: list[Token]) -> bool:
    """Prefix must be zero+ articles followed by one+ unknowns, nothing else."""
    if not prefix:
        return False
    saw_unknown = False
    for t in prefix:
        if t.type is TokenType.ARTICLE:
            continue
        if t.type is TokenType.UNKNOWN:
            saw_unknown = True
            continue
        return False
    return saw_unknown


def _validate_where_head(tokens: list[Token]) -> ReorderOutput:
    """Catch obviously-scrambled condition heads after the first `where`.

    Canonical condition shape: `[UNKNOWN | VERB(each)] OPERATOR(is) ...`
    Detailed compound-condition handling is the parser's job.
    """
    for i, t in enumerate(tokens):
        if t.type is TokenType.CONNECTIVE and t.value == "where":
            rest = tokens[i + 1:]
            if len(rest) < 2:
                return tokens  # parser reports incomplete-condition error
            head, second = rest[0], rest[1]
            if head.type is TokenType.OPERATOR and head.value in ("highest", "lowest"):
                # v25 — extrema condition head: `of <list>` or `<field> of
                # <list>` precedes the comparison operator, so the fixed
                # head/second shape below doesn't apply. Full validation
                # is the parser's job (_parse_extrema).
                return tokens
            head_ok = (
                head.type is TokenType.UNKNOWN
                or (head.type is TokenType.VERB and head.value == "each")
            )
            second_ok = (
                second.type is TokenType.OPERATOR and second.value == "is"
            )
            if not (head_ok and second_ok):
                return LiminateResult(
                    status=ResultStatus.ERROR_PARSE,
                    message=(
                        "I couldn't parse the condition after 'where'. "
                        "Conditions look like '[field] is [comparison] [value]', "
                        "for example: total is above 50."
                    ),
                    executed=False,
                )
            return tokens
    return tokens
