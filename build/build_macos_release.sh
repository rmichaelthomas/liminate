#!/usr/bin/env bash
# The macOS release binary: build, sign, and run it. release.yml calls this,
# and so does a local release when Actions can't run, so both produce the
# binary the same way. Needs SIGNING_IDENTITY (a Developer ID Application
# identity) and the [build] extra installed. Notarization is a separate step.
set -euo pipefail
: "${SIGNING_IDENTITY:?set SIGNING_IDENTITY to a Developer ID Application identity}"

# --codesign-identity signs every binary PyInstaller collects with our
# identity, above all the Python.framework a one-file build unpacks at launch.
# Without it that framework keeps its original team's signature, and the
# hardened runtime's library validation refuses to load it into a process
# signed by ours: the binary exits before running a line. 0.18.2's did.
pyinstaller --noconfirm --onefile --name liminate --collect-all liminate \
  --codesign-identity "$SIGNING_IDENTITY" build/entry.py

codesign --force --options runtime --timestamp --sign "$SIGNING_IDENTITY" dist/liminate
codesign --verify --strict --verbose dist/liminate

# Run it the way a user does. 0.18.2 passed codesign --verify and still
# could not start.
dist/liminate --version
dist/liminate --quiet --test examples/program1_basics.limn > /dev/null
