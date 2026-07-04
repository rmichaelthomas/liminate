"""Branch G Phase C — `liminate build` and the embedded `--inspect` surface.

Compiles a Liminate source file (plus optional domain packs) into a single-
file standalone executable via PyInstaller. The resulting binary embeds:
- The original `.limn` source text.
- Each `--pack` JSON config, verbatim.
- A precomputed inspection manifest (source, canonical rendering, packs,
  vocabulary in use, Liminate version).

The binary's argv handler checks for `--inspect` first and, if present,
prints the manifest and exits without executing the program. Otherwise it
writes the embedded source to a temp file and invokes `liminate.cli.run_file`
with the embedded packs.

Design decisions (Distribution and Executables Inception Checkpoint v1):
- Q1 §10: JSON-only pack bundling. No user-supplied Python pack code.
- Q2 §11: All three program flavors (sequential / reactive-with-adapter /
  reactive-without-adapter) build. When `when` handlers are present but no
  pack was passed, stderr emits a build-time notice; the build proceeds.
- Q3 §12: `--inspect` surfaces four sections in order — source, canonical
  rendering, packs bundled, vocabulary in use. Plain text default; `--json`
  available. Reachable on the binary itself AND via `liminate inspect
  <binary>` (which shells out to the binary's own --inspect handler).

Build-time validation runs lex → reorder → parse for every statement
(including `when` blocks) and tracks composition names as it goes so later
references resolve. Analyzer-level checks are skipped intentionally: they
require a populated symbol table, which only comes from executing the
program. Build is validation only — no interpreter invocation.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Any

from .lexer import LexError, leading_indent, tokenize
from .parser import (
    DefineNode,
    RememberCompositionNode,
    SequenceNode,
    WhenNode,
    _ParseError,
    parse,
    parse_about,
    parse_when_block,
)
from .renderer import render
from .reorderer import reorder
from .result import LiminateResult, ResultStatus
from .vocabulary import TokenType


# ---------------------------------------------------------------------------
# Manifest dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PackManifest:
    name: str
    vocabulary: list[list[str]] = field(default_factory=list)  # [[word, category], ...]
    verbs: list[dict[str, Any]] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)  # full JSON for `--inspect --json`

    def as_summary(self) -> dict[str, Any]:
        """Shape surfaced by `--inspect --json` (no full config — kept
        retrievable on demand per §12)."""
        return {
            "name": self.name,
            "vocabulary": [list(pair) for pair in self.vocabulary],
            "verbs": self.verbs,
        }


@dataclass
class BuildManifest:
    liminate_version: str
    source_filename: str
    source_text: str
    canonical: list[str]
    packs: list[PackManifest]
    vocabulary_in_use: dict[str, list[str]]  # {"verbs": [...], "connectives": [...], "operators": [...]}
    # Meta-Structural Era: the `about` declaration's topic, or None when
    # the program has no `about` line. Inert metadata, surfaced by
    # `--inspect` and the JSON manifest.
    topic: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "liminate_version": self.liminate_version,
            "source_filename": self.source_filename,
            "topic": self.topic,
            "source_text": self.source_text,
            "canonical": list(self.canonical),
            "packs": [p.as_summary() for p in self.packs],
            "vocabulary_in_use": {
                "verbs": list(self.vocabulary_in_use.get("verbs", [])),
                "connectives": list(self.vocabulary_in_use.get("connectives", [])),
                "operators": list(self.vocabulary_in_use.get("operators", [])),
            },
        }


# ---------------------------------------------------------------------------
# Validation + canonical rendering
# ---------------------------------------------------------------------------


class BuildError(Exception):
    """Raised when build-time validation fails. Caller surfaces .message
    to stderr and exits non-zero."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _validate_and_render(source: str) -> tuple[list[str], list[Any], str | None]:
    """Run lex → reorder → parse over each top-level statement (and each
    `when` block) and accumulate canonical renderings + parsed ASTs.

    Returns:
        canonical_lines: one rendered string per parsed statement (blank
            source lines are mirrored as empty strings so the canonical
            output preserves paragraph structure).
        asts: the parsed AST for each non-blank statement (used by the
            caller for the Q2 reactive-without-adapter check).
        topic: the `about` declaration's topic string, or None. Meta-
            Structural Era — `about` is consumed before the normal
            pipeline (first-line-only, MS-Q1) and surfaced as metadata.

    Raises:
        BuildError on any ERROR_PARSE / ERROR_SEMANTIC / unresolved AMBER
        outcome. Build is validation-only — failures abort.
    """
    lines = source.splitlines()
    canonical: list[str] = []
    asts: list[Any] = []
    composition_names: set[str] = set()
    predicate_names: set[str] = set()
    topic: str | None = None
    first_eligible_seen = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("--"):
            canonical.append("")
            i += 1
            continue

        # Meta-Structural Era: an `about` declaration is consumed as
        # metadata before the normal pipeline. It must be the first
        # eligible (non-blank, non-comment) line and may appear at most
        # once (MS-Q1). Definitional Era (v31): `define` also lexes as
        # TokenType.DECLARATION but is NOT first-line-only — it's a
        # normal program statement, so this check is narrowed to `about`
        # specifically and `define` falls through to the regular
        # tokenize/reorder/parse pipeline below (mirrors run.py's
        # identical first-line dispatch).
        try:
            decl_tokens = tokenize(line)
        except LexError as e:
            raise BuildError(f"line {i + 1}: {e.message}") from None
        if (
            decl_tokens
            and decl_tokens[0].type is TokenType.DECLARATION
            and decl_tokens[0].value == "about"
        ):
            if first_eligible_seen or topic is not None:
                raise BuildError(
                    f"line {i + 1}: 'about' is a declaration that must be "
                    f"the first line of the program (after any comments). "
                    f"Only one 'about' declaration is allowed."
                )
            try:
                node = parse_about(decl_tokens)
            except _ParseError as e:
                raise BuildError(f"line {i + 1}: {e.message}") from None
            topic = node.topic
            first_eligible_seen = True
            i += 1
            continue
        first_eligible_seen = True

        try:
            indent = leading_indent(line)
        except LexError as e:
            raise BuildError(f"line {i + 1}: {e.message}") from None

        # When-block header at top level.
        is_when_header = False
        if indent == 0:
            try:
                header_tokens = tokenize(line)
            except LexError as e:
                raise BuildError(f"line {i + 1}: {e.message}") from None
            if (
                header_tokens
                and header_tokens[0].type is TokenType.CONNECTIVE
                and header_tokens[0].value == "when"
            ):
                is_when_header = True
            # Meta-Structural Era batch 3 — detect `inherited when` so
            # `liminate build` accepts every program `liminate run` does
            # (§7 invariant 4). Detection mirrors run.py exactly.
            elif (
                header_tokens
                and header_tokens[0].type is TokenType.OPERATOR
                and header_tokens[0].value == "inherited"
                and len(header_tokens) > 1
                and header_tokens[1].type is TokenType.CONNECTIVE
                and header_tokens[1].value == "when"
            ):
                is_when_header = True

        if is_when_header:
            action_lines, next_i = _collect_when_block(lines, i)
            ast = _parse_when_block_from_source(
                line, action_lines, composition_names, predicate_names,
                line_no=i + 1,
            )
            asts.append(ast)
            try:
                canonical.append(render(ast))
            except Exception as e:  # pragma: no cover — defensive
                raise BuildError(
                    f"line {i + 1}: failed to render canonical form ({e})"
                ) from None
            _collect_composition_names(ast, composition_names)
            _collect_predicate_names(ast, predicate_names)
            i = next_i
            continue

        # Regular statement.
        ast = _parse_line(line, composition_names, predicate_names, line_no=i + 1)
        asts.append(ast)
        try:
            canonical.append(render(ast))
        except Exception as e:  # pragma: no cover — defensive
            raise BuildError(
                f"line {i + 1}: failed to render canonical form ({e})"
            ) from None
        _collect_composition_names(ast, composition_names)
        _collect_predicate_names(ast, predicate_names)
        i += 1

    return canonical, asts, topic


def _parse_line(
    line: str, comp_names: set[str], pred_names: set[str], *, line_no: int,
) -> Any:
    try:
        tokens = tokenize(line)
    except LexError as e:
        raise BuildError(f"line {line_no}: {e.message}") from None
    reordered = reorder(tokens)
    if isinstance(reordered, LiminateResult):
        raise BuildError(_fmt_result(reordered, line_no))
    ast = parse(reordered, composition_names=comp_names, predicate_names=pred_names)
    if isinstance(ast, LiminateResult):
        raise BuildError(_fmt_result(ast, line_no))
    return ast


def _parse_when_block_from_source(
    header_line: str,
    action_lines: list[str],
    comp_names: set[str],
    pred_names: set[str],
    *,
    line_no: int,
) -> Any:
    try:
        header_tokens = tokenize(header_line)
    except LexError as e:
        raise BuildError(f"line {line_no}: {e.message}") from None
    header_reordered = reorder(header_tokens)
    if isinstance(header_reordered, LiminateResult):
        raise BuildError(_fmt_result(header_reordered, line_no))

    action_token_lists: list = []
    for offset, raw in enumerate(action_lines, start=1):
        try:
            toks = tokenize(raw)
        except LexError as e:
            raise BuildError(f"line {line_no + offset}: {e.message}") from None
        if not toks:
            continue
        re_ordered = reorder(toks)
        if isinstance(re_ordered, LiminateResult):
            raise BuildError(_fmt_result(re_ordered, line_no + offset))
        action_token_lists.append(re_ordered)

    ast = parse_when_block(
        header_reordered, action_token_lists,
        composition_names=comp_names,
        predicate_names=pred_names,
    )
    if isinstance(ast, LiminateResult):
        raise BuildError(_fmt_result(ast, line_no))
    return ast


def _collect_when_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """Mirror cli._consume_when_block's collection logic for validation.

    Returns the de-indented action lines and the index of the next line
    not consumed by this block. Indentation errors are surfaced as
    BuildErrors.
    """
    action: list[str] = []
    block_depth: int | None = None
    j = start + 1
    while j < len(lines):
        nl = lines[j]
        stripped = nl.lstrip()
        if not stripped or stripped.startswith("--"):
            j += 1
            continue
        try:
            indent = leading_indent(nl)
        except LexError as e:
            raise BuildError(f"line {j + 1}: {e.message}") from None
        if indent == 0:
            break
        if block_depth is None:
            block_depth = indent
        elif indent > block_depth:
            raise BuildError(
                f"line {j + 1}: This line is indented {indent} spaces, "
                f"deeper than the action block's first indented line "
                f"({block_depth} spaces). v3a §110 — all action lines in "
                f"a 'when' block must use the same indentation depth."
            )
        elif indent < block_depth:
            break
        action.append(nl.lstrip(" "))
        j += 1
    return action, j


def _fmt_result(result: LiminateResult, line_no: int) -> str:
    label = "amber" if result.status.name.startswith("AMBER") else "error"
    return f"line {line_no}: {label}: {result.message}"


def _collect_composition_names(ast: Any, sink: set[str]) -> None:
    """Walk an AST collecting RememberCompositionNode.name values so later
    statements that call those compositions parse successfully."""
    if isinstance(ast, RememberCompositionNode):
        sink.add(ast.name)
    elif isinstance(ast, SequenceNode):
        for op in ast.operations:
            _collect_composition_names(op, sink)
    elif isinstance(ast, WhenNode):
        _collect_composition_names(ast.action, sink)


def _collect_predicate_names(ast: Any, sink: set[str]) -> None:
    """Definitional Era (v31) — walk an AST collecting DefineNode.name
    values so later statements that apply those predicates parse
    successfully. Mirrors _collect_composition_names exactly."""
    if isinstance(ast, DefineNode):
        sink.add(ast.name)
    elif isinstance(ast, SequenceNode):
        for op in ast.operations:
            _collect_predicate_names(op, sink)
    elif isinstance(ast, WhenNode):
        _collect_predicate_names(ast.action, sink)


def _contains_when(asts: list[Any]) -> bool:
    return any(isinstance(a, WhenNode) for a in asts)


# ---------------------------------------------------------------------------
# Vocabulary-in-use
# ---------------------------------------------------------------------------


def _compute_vocabulary_in_use(source: str) -> dict[str, list[str]]:
    """Tokenize the source and collect every VERB / CONNECTIVE / OPERATOR
    token value the program actually invokes. Deduplicated, sorted for
    stable output. Lex errors are silently skipped at this stage — the
    validation pass already surfaced them; here we only care about what
    tokens were used in the parts that did lex."""
    verbs: set[str] = set()
    connectives: set[str] = set()
    operators: set[str] = set()
    for line in source.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("--"):
            continue
        try:
            tokens = tokenize(line)
        except LexError:
            continue
        for t in tokens:
            if t.type is TokenType.VERB:
                verbs.add(t.value)
            elif t.type is TokenType.CONNECTIVE:
                connectives.add(t.value)
            elif t.type is TokenType.OPERATOR:
                operators.add(t.value)
    return {
        "verbs": sorted(verbs),
        "connectives": sorted(connectives),
        "operators": sorted(operators),
    }


# ---------------------------------------------------------------------------
# Pack loading (build-time)
# ---------------------------------------------------------------------------


def _load_pack_manifests(pack_args: list[str]) -> list[PackManifest]:
    """Read each --pack argument (file path or inline JSON) and capture
    enough of its shape to populate the inspection manifest. Build-time
    pack loading does NOT instantiate the pack — that happens inside the
    bundled binary at run time. We only need the JSON config (which is
    embedded verbatim) and a summary of its declared vocabulary/verbs."""
    from .cli import load_pack_from_arg  # late import to avoid cycle

    manifests: list[PackManifest] = []
    for arg in pack_args:
        try:
            config = _read_pack_json(arg)
            # Instantiate to validate the config + collect vocabulary/verbs.
            pack = load_pack_from_arg(arg)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            raise BuildError(f"pack '{arg}': {e}") from None
        manifests.append(
            PackManifest(
                name=pack.name(),
                vocabulary=[list(p) for p in pack.vocabulary()],
                verbs=[_verb_to_dict(v) for v in pack.verbs()],
                config=config,
            )
        )
    return manifests


def _read_pack_json(arg: str) -> dict[str, Any]:
    stripped = arg.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    return json.loads(Path(arg).read_text(encoding="utf-8"))


_EXECUTION_TYPE_NAMES = {
    "SetValueExecution": "set_value",
    "SubstringCheckExecution": "substring_check",
    "AppendToListExecution": "append_to_list",
    "SetFieldExecution": "set_field",
    "CompareValuesExecution": "compare_values",
    "NumericExtractCompareExecution": "numeric_extract_compare",
    "RangeCheckExecution": "range_check",
    "ConformanceCheckExecution": "conformance_check",
}


def _execution_to_dict(execution: Any) -> dict[str, Any]:
    """v2: serialize any execution dataclass to its JSON form. Strips None
    fields and prepends the canonical type string."""
    type_str = _EXECUTION_TYPE_NAMES.get(
        type(execution).__name__, "unknown"
    )
    out: dict[str, Any] = {"type": type_str}
    for f in execution.__dataclass_fields__:
        v = getattr(execution, f)
        if v is not None:
            out[f] = v
    return out


def _verb_to_dict(sig: Any) -> dict[str, Any]:
    return {
        "word": sig.word,
        "slots": [
            {
                "name": s.name,
                "connective": s.connective,
                "required": s.required,
                "type_constraint": s.type_constraint,
                "value_type": s.value_type,
            }
            for s in sig.slots
        ],
        "execution": _execution_to_dict(sig.execution),
    }


# ---------------------------------------------------------------------------
# Entry script generation
# ---------------------------------------------------------------------------


_ENTRY_TEMPLATE = '''\
"""Auto-generated entry script for a Liminate standalone executable.

Embeds the original Liminate source, each domain pack's JSON config, and
a precomputed inspection manifest. On startup, scans argv for `--inspect`;
if present, formats and prints the manifest and exits. Otherwise, writes
the source to a temp file and invokes liminate.cli.run_file with the
bundled packs.
"""

import json
import sys
import tempfile
import os
from pathlib import Path


EMBEDDED_SOURCE = {source_literal}
EMBEDDED_PACK_CONFIGS = {packs_literal}
EMBEDDED_MANIFEST = {manifest_literal}


def _run_inspect(argv):
    from liminate.inspect_cmd import format_manifest
    as_json = "--json" in argv
    sys.stdout.write(format_manifest(EMBEDDED_MANIFEST, as_json=as_json))
    if not as_json:
        sys.stdout.write("\\n")
    return 0


def _run_program(argv):
    from liminate.cli import run_file, load_pack_from_arg
    domain_packs = []
    for cfg in EMBEDDED_PACK_CONFIGS:
        domain_packs.append(load_pack_from_arg(json.dumps(cfg)))

    auto = "--test" in argv
    quiet = "--quiet" in argv
    # Strip recognized flags; reject any unknown extras to mirror the
    # primary CLI's flag discipline.
    leftovers = [a for a in argv if a not in ("--test", "--quiet")]
    if leftovers:
        sys.stderr.write(f"Error: unknown argument(s): {{', '.join(leftovers)}}\\n")
        return 2

    fname = EMBEDDED_MANIFEST.get("source_filename") or "program.limn"
    with tempfile.TemporaryDirectory() as td:
        src_path = os.path.join(td, fname)
        Path(src_path).write_text(EMBEDDED_SOURCE, encoding="utf-8")
        run_file(
            src_path,
            auto_confirm_amber=auto,
            quiet=quiet,
            domain_packs=domain_packs or None,
        )
    return 0


def main():
    argv = sys.argv[1:]
    if "--inspect" in argv:
        return _run_inspect(argv)
    return _run_program(argv)


if __name__ == "__main__":
    sys.exit(main())
'''


def _generate_entry_script(manifest: BuildManifest) -> str:
    pack_configs = [p.config for p in manifest.packs]
    return _ENTRY_TEMPLATE.format(
        source_literal=repr(manifest.source_text),
        packs_literal=repr(pack_configs),
        manifest_literal=repr(manifest.as_dict()),
    )


# ---------------------------------------------------------------------------
# Top-level build()
# ---------------------------------------------------------------------------


def build(
    source_path: str,
    pack_args: list[str],
    output: str,
    *,
    stderr=None,
    stdout=None,
) -> int:
    """Build a Liminate source file into a single-file executable.

    Returns the process exit code (0 success, non-zero failure).
    """
    err = stderr if stderr is not None else sys.stderr
    out = stdout if stdout is not None else sys.stdout

    src_path = Path(source_path)
    if not src_path.exists():
        err.write(f"Error: source file not found: {source_path}\n")
        return 2
    source_text = src_path.read_text(encoding="utf-8")

    try:
        packs = _load_pack_manifests(pack_args)
    except BuildError as e:
        err.write(f"Error: {e.message}\n")
        return 2

    try:
        canonical, asts, topic = _validate_and_render(source_text)
    except BuildError as e:
        err.write(f"Error: {e.message}\n")
        return 1

    # Q2 §11 — reactive code without an adapter still builds; emit notice.
    if _contains_when(asts) and not packs:
        err.write(
            "Note: this program uses 'when' handlers but no adapter is "
            "bundled. It will run an initial evaluation against current "
            "state, then exit. To enable continuous reactive behavior, "
            "bundle a pack with --pack.\n"
        )

    manifest = BuildManifest(
        liminate_version=_pkg_version("liminate"),
        source_filename=src_path.name,
        source_text=source_text,
        canonical=canonical,
        packs=packs,
        vocabulary_in_use=_compute_vocabulary_in_use(source_text),
        topic=topic,
    )

    # Generate entry script + invoke PyInstaller.
    output_path = Path(output)
    out_dir = output_path.parent if output_path.parent != Path("") else Path.cwd()
    out_dir = out_dir if out_dir != Path("") else Path.cwd()
    out_name = output_path.name or src_path.stem

    with tempfile.TemporaryDirectory(prefix="liminate-build-") as td:
        td_path = Path(td)
        entry_path = td_path / "entry.py"
        entry_path.write_text(_generate_entry_script(manifest), encoding="utf-8")

        pyi_workdir = td_path / "pyi"
        pyi_workdir.mkdir()
        dist_dir = pyi_workdir / "dist"
        build_dir = pyi_workdir / "build"
        spec_dir = pyi_workdir

        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--name", out_name,
            "--collect-all", "liminate",
            "--distpath", str(dist_dir),
            "--workpath", str(build_dir),
            "--specpath", str(spec_dir),
            "--noconfirm",
            "--clean",
            "--log-level", "ERROR",
            str(entry_path),
        ]
        out.write(f"Building {out_name} (PyInstaller)...\n")
        # Propagate the parent process's sys.path entries via PYTHONPATH
        # so PyInstaller's hook for `--collect-all liminate` can locate
        # the package even when it isn't pip-installed (e.g., when running
        # from a src-layout checkout with PYTHONPATH=src). Without this,
        # the PyInstaller subprocess inherits only os.environ['PYTHONPATH']
        # which may not include the package's actual location.
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        parent_paths = [p for p in sys.path if p and p not in existing.split(os.pathsep)]
        if parent_paths:
            extra = os.pathsep.join(parent_paths)
            env["PYTHONPATH"] = (
                extra if not existing else f"{extra}{os.pathsep}{existing}"
            )
        try:
            proc = subprocess.run(
                cmd, check=False, capture_output=True, text=True, env=env,
            )
        except FileNotFoundError:
            err.write(
                "Error: PyInstaller is not available. Install it with "
                "`pip install -e \".[build]\"`.\n"
            )
            return 2
        if proc.returncode != 0:
            err.write("Error: PyInstaller failed.\n")
            if proc.stderr:
                err.write(proc.stderr)
            if proc.stdout:
                err.write(proc.stdout)
            return proc.returncode

        # PyInstaller emits dist/<name>[.exe]. Locate it and copy out.
        produced = _find_produced_binary(dist_dir, out_name)
        if produced is None:
            err.write(
                f"Error: PyInstaller did not produce an expected binary "
                f"at {dist_dir}.\n"
            )
            return 1

        out_dir.mkdir(parents=True, exist_ok=True)
        final_path = out_dir / produced.name
        shutil.copy2(produced, final_path)
        try:
            final_path.chmod(0o755)
        except OSError:
            pass

    out.write(f"Built: {final_path}\n")
    return 0


def _find_produced_binary(dist_dir: Path, name: str) -> Path | None:
    candidates = [dist_dir / name, dist_dir / f"{name}.exe"]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    # Fallback: any file in dist_dir matching the name prefix.
    if dist_dir.exists():
        for entry in dist_dir.iterdir():
            if entry.is_file() and entry.stem == name:
                return entry
    return None
