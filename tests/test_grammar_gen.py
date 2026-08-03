"""Regression coverage for grammar_gen.py and the grammar/ projections it
produces (rules.json, errors.json, encodability.json). grammar/README.md
explains why these are generated rather than hand-edited (ruling D2,
ported from Planes) and .github/workflows/ci.yml's grammar-sync job runs
`python3 grammar_gen.py --check` on every push -- these tests are the
same invariant, runnable locally without a subprocess to GitHub Actions.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT))
import grammar_gen  # noqa: E402


def test_check_passes_clean_against_committed_files():
    """The invariant CI enforces on every push: what's committed under
    grammar/ must already match what the generator produces right now."""
    proc = subprocess.run(
        [sys.executable, "grammar_gen.py", "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        f"grammar/ is out of date with the source it's generated from "
        f"-- run `python3 grammar_gen.py` and commit the result.\n"
        f"{proc.stdout}\n{proc.stderr}"
    )


def test_deleting_generated_files_has_no_effect_on_the_interpreter():
    """grammar/README.md's own claim: these files are pure projections.
    Nothing under src/liminate/ should import from grammar/ at all."""
    for py_file in (REPO_ROOT / "src" / "liminate").glob("*.py"):
        text = py_file.read_text()
        assert "grammar/" not in text and "import grammar" not in text, (
            f"{py_file} references grammar/ -- these files must stay pure "
            f"projections with no code depending on them"
        )


class TestGenerateRules:
    def test_every_form_has_the_required_fields(self):
        doc = grammar_gen.generate_rules()
        assert doc["count"] == len(doc["forms"]) > 0
        for form in doc["forms"]:
            for key in ("form", "parser_method", "opens_with", "produces",
                        "calls", "source", "surface"):
                assert key in form, f"{form.get('parser_method')} is missing '{key}'"
            assert form["source"].startswith("parser.py:")

    def test_inclusion_rule_matches_bare_name_prefix(self):
        """Every form's parser_method, with at most one leading underscore
        stripped, is 'parse' or starts with 'parse_' -- the exact rule
        _is_parse_function_name implements, checked from the outside."""
        doc = grammar_gen.generate_rules()
        for form in doc["forms"]:
            bare = form["parser_method"].removeprefix("_")
            assert bare == "parse" or bare.startswith("parse_")

    def test_docstring_count_matches_forms_with_non_null_surface(self):
        doc = grammar_gen.generate_rules()
        assert doc["docstring_count"] == sum(
            1 for f in doc["forms"] if f["surface"] is not None
        )

    def test_surface_is_never_synthesized_for_undocumented_functions(self):
        """A form whose parser.py function has no docstring must carry
        surface: null -- never an invented description. Spot-checks
        _parse_number, which the inclusion rule pulls in by name despite
        taking a plain string rather than a token stream, and which has
        no docstring as of this writing."""
        doc = grammar_gen.generate_rules()
        by_method = {f["parser_method"]: f for f in doc["forms"]}
        assert "_parse_number" in by_method
        if grammar_gen.ast.get_docstring(
            next(
                n for n in grammar_gen.ast.walk(
                    grammar_gen.ast.parse(Path(grammar_gen.PARSER_PATH).read_text())
                )
                if isinstance(n, grammar_gen.ast.FunctionDef) and n.name == "_parse_number"
            )
        ) is None:
            assert by_method["_parse_number"]["surface"] is None

    def test_precedence_chains_are_named_and_never_merged(self):
        doc = grammar_gen.generate_rules()
        names = [chain["name"] for chain in doc["precedence"]]
        assert names == [c["name"] for c in grammar_gen.PRECEDENCE_CHAINS]
        assert len(names) == len(set(names)), "precedence chain names must be distinct"

    def test_emitted_chain_has_no_duplicate_forms(self):
        """A chain that IS emitted must be a genuine linear walk -- no
        form appears twice, which would mean the walk found a cycle
        _precedence_ladder should have refused instead."""
        doc = grammar_gen.generate_rules()
        for chain in doc["precedence"]:
            if chain["emitted"]:
                levels = chain["loosest_first"]
                assert len(levels) == len(set(levels))
                assert len(levels) >= 2

    def test_unemitted_chain_states_a_reason(self):
        doc = grammar_gen.generate_rules()
        for chain in doc["precedence"]:
            if not chain["emitted"]:
                assert chain.get("reason"), (
                    f"chain {chain['name']!r} was not emitted but carries no "
                    f"reason -- refusing to guess still requires saying why"
                )


class TestGenerateErrors:
    def test_every_entry_has_a_unique_id(self):
        doc = grammar_gen.generate_errors()
        ids = [e["id"] for e in doc["entries"]]
        assert len(ids) == len(set(ids)) == doc["count"]

    def test_no_entry_carries_a_tag_field(self):
        """B.2's stated absence: Liminate's errors carry no tag, and this
        generator must not invent one to mimic Planes' errors.json shape."""
        doc = grammar_gen.generate_errors()
        for e in doc["entries"]:
            assert "tag" not in e
        assert "tags" not in doc

    def test_every_entry_class_is_a_target_exception(self):
        doc = grammar_gen.generate_errors()
        for e in doc["entries"]:
            assert e["class"] in grammar_gen.TARGET_EXCEPTIONS

    def test_f_string_entries_carry_matching_slots(self):
        doc = grammar_gen.generate_errors()
        for e in doc["entries"]:
            if e["template"] is not None and "{" in e["template"]:
                assert e["slots"], (
                    f"{e['id']} ({e['source']}) has a brace in its template "
                    f"but no recorded slots"
                )


class TestGenerateEncodability:
    def test_all_eight_finding_kinds_are_present(self):
        doc = grammar_gen.generate_encodability()
        found = {k["kind"] for k in doc["finding_kinds"]}
        assert found == set(grammar_gen.FINDING_KIND_NAMES)
        assert doc["finding_kinds_missing_from_source"] == []

    def test_both_encoder_exception_classes_have_raise_sites(self):
        doc = grammar_gen.generate_encodability()
        classes = {e["class"]: e for e in doc["encoder_exceptions"]}
        assert set(classes) == set(grammar_gen.ENCODER_EXCEPTION_CLASSES)
        for cls, entry in classes.items():
            assert entry["defined_at"] is not None, f"{cls} definition not found"
            assert entry["raised_at"], f"{cls} has no recorded raise sites"

    def test_unencodable_reason_note_points_at_a_real_source_line(self):
        doc = grammar_gen.generate_encodability()
        note = doc["unencodable_reason_is_not_a_bounded_vocabulary"]
        assert note["source"] is not None
        assert note["source"].startswith("checker.py:")
        assert "not a value drawn from a fixed set" in note["explanation"] \
            or "bounded" in note["explanation"].lower()


@pytest.mark.parametrize("path_attr", ["RULES_PATH", "ERRORS_PATH", "ENCODABILITY_PATH"])
def test_generated_paths_stay_inside_grammar_dir(path_attr):
    path = getattr(grammar_gen, path_attr)
    assert Path(path).parent == Path(grammar_gen.GRAMMAR_DIR)
