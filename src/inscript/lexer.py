"""Lexer for Inscript v1 + v2c.

Sources:
- inception §22 (lexer specification)
- v1c §47 (article `an` recognized)
- v1c §48 (blank lines produce zero tokens)
- v1d §57 (lexer lowercases — symbol table names are lowercase as a consequence)
- v2c §86 (quote-state accumulation: `"…"` produces a single QUOTED_STRING)
- v2c §89 (QUOTED_STRING bypasses vocabulary lookup)
- v2c §91 (quoted content is lowercased, consistent with the rest of the language)
- v2c §92 (empty quotes `""` are a parse error)

Pipeline per BUILD_PLAN Phase 2, extended for v2c:
1. Empty / whitespace-only line → return [] (v1c §48).
2. Scan the line character-by-character (v2c §86): on `"`, accumulate
   the quoted phrase until the matching `"`. Outside quotes, split on
   whitespace and isolate `:` as its own token (§22 line 434).
3. Strip decorative punctuation `, . ? !` from each UNQUOTED word's
   edges (§22 line 430). Quoted content preserves its punctuation
   verbatim (v2c §86).
4. Lowercase each word — quoted and unquoted alike (v2c §91 + §22).
5. Combine `equal` + `to` into a single OPERATOR token `equal_to` via
   one-word lookahead (§22 line 426). Quoted `"equal"` does NOT combine
   (it is a value token, not a vocabulary lookup).
6. Classify unquoted words against the vocabulary tables; quoted words
   always emit QUOTED_STRING (v2c §89). Bare unquoted unknowns fall
   back to NUMBER (digits + optional decimal point, §22 line 428) or
   UNKNOWN.

Errors raised:
- LexError for unclosed quotes (v2c §86) and empty quotes (v2c §92).
  The CLI wrapper converts these into ERROR_PARSE results so the
  five-outcome taxonomy (v1c §50) is preserved.
"""

from __future__ import annotations

import re

from .vocabulary import (
    ARTICLES,
    CONNECTIVES,
    OPERATORS,
    Token,
    TokenType,
    VERBS,
)

_DECORATIVE = ",.?!"
_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?$")


class LexError(Exception):
    """v2c §86 / §92 — surfaced as ERROR_PARSE by the CLI wrapper."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def tokenize(line: str) -> list[Token]:
    """Lex a single source line into tokens.

    Returns an empty list for blank or whitespace-only lines (v1c §48).
    Raises LexError for unclosed or empty quoted strings (v2c §86/§92).
    Positions are character offsets into the original input line.
    """
    if not line.strip():
        return []

    raw: list[tuple[str, int, bool]] = _split_raw(line)
    cleaned: list[tuple[str, int, bool]] = _strip_and_lower(raw)
    return _classify(cleaned)


def _split_raw(line: str) -> list[tuple[str, int, bool]]:
    """Split the line into raw words, isolating `:` and `"..."` runs.

    Each tuple is (text, position, is_quoted). The text of quoted runs
    is the content between the quotes (without the quote characters
    themselves); for unquoted runs it is the raw word as written.
    """
    out: list[tuple[str, int, bool]] = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c.isspace():
            i += 1
            continue
        if c == ":":
            out.append((":", i, False))
            i += 1
            continue
        if c == '"':
            quote_start = i
            i += 1
            content_start = i
            while i < n and line[i] != '"':
                i += 1
            if i >= n:
                # v2c §86: unclosed quote — no line-spanning.
                raise LexError(
                    "I see an opening quote mark but no closing one on "
                    "this line. Each quoted phrase needs both opening "
                    "and closing marks."
                )
            content = line[content_start:i]
            if not content:
                # v2c §92: `""` rejected.
                raise LexError(
                    "There's nothing between these quote marks. If you "
                    "want to store a value, put it between the quotes."
                )
            out.append((content, quote_start, True))
            i += 1  # skip closing "
            continue
        start = i
        while i < n and not line[i].isspace() and line[i] != ":" and line[i] != '"':
            i += 1
        out.append((line[start:i], start, False))
    return out


def _strip_and_lower(
    raw: list[tuple[str, int, bool]],
) -> list[tuple[str, int, bool]]:
    """Lowercase every token (v2c §91 + §22). For unquoted tokens, also
    strip decorative punctuation from the edges. Quoted tokens preserve
    their punctuation verbatim per v2c §86. Empty residues are dropped
    only when they arose from punctuation stripping; quoted tokens
    already passed the §92 empty-content check upstream.
    """
    out: list[tuple[str, int, bool]] = []
    for word, pos, is_quoted in raw:
        if is_quoted:
            out.append((word.lower(), pos, True))
            continue
        left = 0
        while left < len(word) and word[left] in _DECORATIVE:
            left += 1
        right = len(word)
        while right > left and word[right - 1] in _DECORATIVE:
            right -= 1
        if left == right:
            continue
        out.append((word[left:right].lower(), pos + left, False))
    return out


def _classify(cleaned: list[tuple[str, int, bool]]) -> list[Token]:
    tokens: list[Token] = []
    j = 0
    while j < len(cleaned):
        word, pos, is_quoted = cleaned[j]

        if is_quoted:
            # v2c §89: quoted strings bypass vocabulary lookup entirely.
            tokens.append(Token(TokenType.QUOTED_STRING, word, pos))
            j += 1
            continue

        if word == ":":
            tokens.append(Token(TokenType.DELIMITER, ":", pos))
            j += 1
            continue

        # Multi-word lookahead: `equal` + `to` -> `equal_to` operator (§22).
        # Only applies to unquoted tokens — quoted `"equal"` is data.
        if (
            word == "equal"
            and j + 1 < len(cleaned)
            and cleaned[j + 1][0] == "to"
            and not cleaned[j + 1][2]
        ):
            tokens.append(Token(TokenType.OPERATOR, "equal_to", pos))
            j += 2
            continue

        if word in VERBS:
            tokens.append(Token(TokenType.VERB, word, pos))
        elif word in CONNECTIVES:
            tokens.append(Token(TokenType.CONNECTIVE, word, pos))
        elif word in OPERATORS:
            tokens.append(Token(TokenType.OPERATOR, word, pos))
        elif word in ARTICLES:
            tokens.append(Token(TokenType.ARTICLE, word, pos))
        elif _NUMBER_RE.match(word):
            tokens.append(Token(TokenType.NUMBER, word, pos))
        else:
            tokens.append(Token(TokenType.UNKNOWN, word, pos))
        j += 1
    return tokens
