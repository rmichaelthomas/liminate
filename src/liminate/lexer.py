"""Lexer for Liminate v1 + v2c + v3a.

Sources:
- inception §22 (lexer specification)
- v1c §47 (article `an` recognized)
- v1c §48 (blank lines produce zero tokens)
- v1d §57 (lexer lowercases — symbol table names are lowercase as a consequence)
- v2c §86 (quote-state accumulation: `"…"` produces a single QUOTED_STRING)
- v2c §89 (QUOTED_STRING bypasses vocabulary lookup)
- v2c §91 (case normalization stops at the quote delimiter — quoted
  content is preserved verbatim so external identifiers and labels
  survive round-trip)
- v2c §92 (empty quotes `""` are a parse error)
- v3a §110 (leading-space indentation tracked for `when` action blocks;
  tabs in leading indentation are rejected with a clear LexError)

Pipeline per BUILD_PLAN Phase 2, extended for v2c:
1. Empty / whitespace-only line → return [] (v1c §48).
2. Scan the line character-by-character (v2c §86): on `"`, accumulate
   the quoted phrase until the matching `"`. Outside quotes, split on
   whitespace and isolate `:` as its own token (§22 line 434).
3. Strip decorative punctuation `, . ? !` from each UNQUOTED word's
   edges (§22 line 430). Quoted content preserves its punctuation
   verbatim (v2c §86).
4. Lowercase each UNQUOTED word (§22). Quoted content is left
   untouched so case is preserved across the lexer.
5. Combine `equal` + `to` into a single OPERATOR token `equal_to` via
   one-word lookahead (§22 line 426). Same one-word lookahead pattern
   produces `multiplied_by` and `divided_by` for the Infrastructure
   Era arithmetic operators. Quoted `"equal"` / `"multiplied"` /
   `"divided"` do NOT combine (they are value tokens, not vocabulary
   lookups).
6. Classify unquoted words against the vocabulary tables; quoted words
   always emit QUOTED_STRING (v2c §89). Bare unquoted unknowns fall
   back to NUMBER (digits + optional decimal point, §22 line 428) or
   UNKNOWN.

Indentation (v3a §110):
- `leading_indent(line)` returns the count of leading space characters.
- A tab in the leading-whitespace run is rejected with LexError. Tabs
  later in the line continue to be treated as ordinary whitespace by the
  tokenizer (existing v1 behavior unchanged).
- Blank / whitespace-only lines have no meaningful indentation — they
  return 0 and the v3a block parser skips them per v1c §48.

Errors raised:
- LexError for unclosed quotes (v2c §86), empty quotes (v2c §92), and
  tab-indented lines (v3a §110). The CLI wrapper converts these into
  ERROR_PARSE results so the five-outcome taxonomy (v1c §50) is preserved.
"""

from __future__ import annotations

import re

from .vocabulary import (
    ARTICLES,
    CONNECTIVES,
    DECLARATIONS,
    OPERATORS,
    Token,
    TokenType,
    VERBS,
    active_pack_verb_words,
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
    stripped = line.lstrip()
    if not stripped:
        return []
    # Comment line: `--` at the start of a line (after optional leading
    # whitespace) marks the line as marginalia — handled identically to
    # a blank line (v1c §48). The check fires before _split_raw so the
    # hyphens are never interpreted as token content.
    if stripped.startswith("--"):
        return []

    raw: list[tuple[str, int, bool]] = _split_raw(line)
    cleaned: list[tuple[str, int, bool]] = _strip_and_lower(raw)
    return _classify(cleaned)


def leading_indent(line: str) -> int:
    """Return the count of leading-space characters on `line` (v3a §110).

    Tabs in the leading-whitespace run are rejected with LexError so the
    user gets a clear message rather than the silent visual ambiguity of
    mixed tabs and spaces. Blank lines return 0 — the v3a block parser
    skips them rather than treating them as block boundaries (v1c §48).
    """
    if not line.strip():
        return 0
    count = 0
    for c in line:
        if c == " ":
            count += 1
            continue
        if c == "\t":
            raise LexError(
                "Indented lines must use spaces, not tabs. v3a §110 — "
                "each line in an action block uses the same number of "
                "leading spaces."
            )
        break
    return count


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
    """Lowercase every unquoted token (§22). Quoted tokens preserve their
    content verbatim — case and punctuation — so external identifiers
    and human-readable labels survive round-trip. Empty residues are
    dropped only when they arose from punctuation stripping; quoted
    tokens already passed the §92 empty-content check upstream.
    """
    out: list[tuple[str, int, bool]] = []
    for word, pos, is_quoted in raw:
        if is_quoted:
            out.append((word, pos, True))
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

        # Multi-word lookahead: `multiplied` + `by` -> `multiplied_by` operator.
        if (
            word == "multiplied"
            and j + 1 < len(cleaned)
            and cleaned[j + 1][0] == "by"
            and not cleaned[j + 1][2]
        ):
            tokens.append(Token(TokenType.OPERATOR, "multiplied_by", pos))
            j += 2
            continue

        # Multi-word lookahead: `divided` + `by` -> `divided_by` operator.
        if (
            word == "divided"
            and j + 1 < len(cleaned)
            and cleaned[j + 1][0] == "by"
            and not cleaned[j + 1][2]
        ):
            tokens.append(Token(TokenType.OPERATOR, "divided_by", pos))
            j += 2
            continue

        if word in VERBS:
            tokens.append(Token(TokenType.VERB, word, pos))
        elif word in active_pack_verb_words():
            # v4a §137: pack-defined verbs are classified as VERB tokens
            # while the pack is loaded. The parser dispatches them after
            # the base verbs.
            tokens.append(Token(TokenType.VERB, word, pos))
        elif word in CONNECTIVES:
            tokens.append(Token(TokenType.CONNECTIVE, word, pos))
        elif word in OPERATORS:
            tokens.append(Token(TokenType.OPERATOR, word, pos))
        elif word in ARTICLES:
            tokens.append(Token(TokenType.ARTICLE, word, pos))
        elif word in DECLARATIONS:
            # Meta-Structural Era: declarations are a new grammatical
            # category. `about` is handled by the CLI before the normal
            # parse pipeline (first-line-only, MS-Q1).
            tokens.append(Token(TokenType.DECLARATION, word, pos))
        elif _NUMBER_RE.match(word):
            tokens.append(Token(TokenType.NUMBER, word, pos))
        else:
            tokens.append(Token(TokenType.UNKNOWN, word, pos))
        j += 1
    return tokens
