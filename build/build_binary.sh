#!/usr/bin/env bash
set -euo pipefail
pip install -e ".[build]"
pyinstaller --onefile --name liminate --collect-all liminate build/entry.py
echo "Binary at dist/liminate"
