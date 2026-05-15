"""Make the src/ layout importable for pytest without an editable install."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest


@pytest.fixture(autouse=True)
def _reset_pack_vocabulary():
    """v4a §137: active pack verbs/nouns are module-level state. Reset
    between tests so a Session that loads a UI pack in one test doesn't
    leak its vocabulary into the next test."""
    from liminate.vocabulary import deactivate_all_pack_words
    deactivate_all_pack_words()
    yield
    deactivate_all_pack_words()
