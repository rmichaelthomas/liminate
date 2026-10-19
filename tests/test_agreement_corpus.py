"""The agreement test set is generated, never typed.

`tests/fixtures/agreement-<version>.json` is what the reference interpreter did
with each program in `agreement_corpus.txt`. The TypeScript and Swift
evaluators are held to that file, so a stale or hand-edited copy would let them
agree with something the reference never said. These tests regenerate it and
diff.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "gen_agreement_corpus.py"
CORPUS = ROOT / "tests" / "fixtures" / "agreement_corpus.txt"


def _version() -> str:
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError("pyproject.toml states no version")


def _committed() -> dict:
    path = ROOT / "tests" / "fixtures" / f"agreement-{_version()}.json"
    assert path.exists(), f"{path.name} is missing: run {GENERATOR.name} > {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _regenerated() -> dict:
    done = subprocess.run(
        [sys.executable, str(GENERATOR)], capture_output=True, text=True, check=True
    )
    return json.loads(done.stdout)


def test_the_committed_file_is_what_the_reference_produces_now():
    assert _regenerated() == _committed()


def test_the_corpus_is_large_enough_to_mean_something():
    assert len(_committed()["cases"]) >= 60


def test_it_covers_every_outcome_and_every_verb():
    cases = _committed()["cases"]
    assert {c["outcome"] for c in cases} == {"pass", "crossed", "error"}
    verbs = {x["verb"] for c in cases for x in c["crossed"]}
    assert verbs == {"forbid", "require"}
    programs = "\n".join(c["program"] for c in cases)
    for word in ("permit", "unless", "within", " and ", " or ", "about"):
        assert word in programs, f"no case exercises {word.strip()!r}"


def test_an_error_never_carries_crossed_rules():
    for case in _committed()["cases"]:
        if case["outcome"] == "error":
            assert case["crossed"] == [], case["id"]
        if case["outcome"] == "pass":
            assert case["exit"] == 0, case["id"]


def test_case_ids_are_unique():
    ids = [c["id"] for c in _committed()["cases"]]
    assert len(ids) == len(set(ids))


def test_every_case_is_in_the_corpus_file():
    names = {
        ln[2:].strip()
        for ln in CORPUS.read_text(encoding="utf-8").splitlines()
        if ln.startswith("# ")
    }
    assert {c["id"] for c in _committed()["cases"]} == names
