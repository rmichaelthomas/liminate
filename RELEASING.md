# Releasing Liminate

Liminate ships as a Python package on PyPI **and** as standalone binaries on
GitHub Releases. This document covers the binary release flow. A binary
release is triggered by pushing a `v*` tag; the
`.github/workflows/release.yml` workflow builds three platform binaries
(macOS arm64, Linux x64, Windows x64), signs and notarizes the macOS
binary, and attaches all three to a new GitHub Release.

---

## Release checklist

1. **Bump the version.** Edit `version` in `pyproject.toml`. Match the
   tag you are about to create (no leading `v` in `pyproject.toml`).
2. **Commit and tag.**
   ```bash
   git add pyproject.toml
   git commit -m "Release v0.x.x"
   git tag v0.x.x
   git push origin main
   git push origin v0.x.x
   ```
3. **Wait for CI.** The `Release` workflow runs three platform build
   jobs in parallel, then a `release` job that creates the GitHub
   Release and attaches all three binaries. Expect ~10–15 minutes.
4. **Verify the release page.** Visit
   <https://github.com/rmichaelthomas/liminate/releases/tag/v0.x.x>
   and confirm all three assets are attached:
   - `liminate-macos-arm64`
   - `liminate-linux-x64`
   - `liminate-windows-x64.exe`
5. **Smoke-test each binary** on a clean machine for its platform:
   ```bash
   chmod +x liminate-macos-arm64        # macOS / Linux
   ./liminate-macos-arm64 --version
   ./liminate-macos-arm64 examples/program1_basics.limn
   ```
   On macOS, confirm Gatekeeper accepts the notarized binary on first
   launch (right-click → Open if not). On Windows, confirm SmartScreen
   shows the unsigned-binary warning (expected) and that "Run anyway"
   works.

---

## GitHub Actions secrets

The macOS signing + notarization step needs five secrets, configured at
**Settings → Secrets and variables → Actions** on the GitHub repo:

| Secret | Purpose |
| --- | --- |
| `APPLE_CERTIFICATE_P12` | Base64-encoded Developer ID Application certificate (`.p12`). |
| `APPLE_CERTIFICATE_PASSWORD` | Password used when the `.p12` was exported. |
| `APPLE_TEAM_ID` | Apple Developer Team ID (10-character alphanumeric). |
| `APPLE_ID` | Apple ID email used for notarization. |
| `APPLE_APP_SPECIFIC_PASSWORD` | App-specific password generated at <https://appleid.apple.com/account/manage> (Security → App-Specific Passwords). |

Without these secrets the macOS build will fail at the import-certificate
step. The Linux and Windows builds have no secret dependencies.

---

## Exporting the Developer ID certificate as `.p12`

1. Open **Keychain Access** → **login** → **My Certificates**.
2. Right-click the `Developer ID Application: <Your Name> (<TEAM_ID>)`
   certificate and choose **Export**.
3. Choose `.p12` as the format, set a strong password, save the file.
4. Base64-encode it for the secret:
   ```bash
   base64 -i DeveloperID.p12 | pbcopy
   ```
   Paste the result into the `APPLE_CERTIFICATE_P12` secret. Paste the
   export password into `APPLE_CERTIFICATE_PASSWORD`.

---

## Local binary builds

To produce a binary on your dev machine for the current platform:

```bash
./build/build_binary.sh
```

The script installs the `[build]` extra (PyInstaller) and runs:

```bash
pyinstaller --onefile --name liminate --collect-all liminate build/entry.py
```

The binary lands at `dist/liminate`. The `--collect-all liminate` flag
is required by the src/ layout — without it PyInstaller misses
submodules like `packs/timer.py`.

---

## Homebrew tap (manual, future)

Distribution via a Homebrew tap is **not automated** by this workflow.
When you want to publish to Homebrew:

1. Create the tap repo `rmichaelthomas/homebrew-liminate`.
2. Add a formula that downloads the `liminate-macos-arm64` asset from
   the latest GitHub Release, verifies the SHA-256, and installs it as
   `liminate` on the user's `PATH`.
3. Update the formula's `url`, `sha256`, and `version` fields each
   release.

Chocolatey and winget are not planned.

---

## What this workflow does NOT do

- It does not publish to PyPI. PyPI publishing is a separate flow
  (handled by Phase A of Branch G).
- It does not code-sign the Windows `.exe`. The Windows binary ships
  unsigned; SmartScreen warnings are expected on first launch.
- It does not staple the macOS notarization ticket. Stapling is not
  supported for bare Mach-O binaries; Gatekeeper resolves the ticket
  online at first launch instead.
