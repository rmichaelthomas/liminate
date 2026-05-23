# Versioning Policy

This document states what version numbers mean for the Liminate interpreter and what guarantees they carry for contract replay.

## Semantic versioning

Liminate follows [semantic versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

**Patch versions (0.10.x)** fix bugs without changing grammar or execution semantics. A contract that parses and runs under `0.10.0` will produce identical results under `0.10.1`. No new reserved words, no changed execution types, no altered parse behavior.

**Minor versions (0.x.0)** may add reserved words, execution types, or pack capabilities. They do not change the behavior of existing statements — a contract written for `0.9.0` will parse and run identically under `0.10.0`. However, a new reserved word may collide with a user-defined name in an existing contract. When this happens, the interpreter emits a clear error naming the collision. The migration path is to rename the user-defined variable.

**Major version (1.0.0)** is the stability boundary. Before 1.0, minor versions may occasionally make breaking changes to grammar or semantics, documented in the changelog. After 1.0, breaking changes require a major version bump and a migration guide.

## Contract replay guarantee

A contract is replay-safe when it produces identical results given the same interpreter version, pack version, and contract source text. The interpreter is deterministic — no randomness, no model calls, no external state, no network dependency.

**Within a patch version:** replay is guaranteed. `0.10.0` and `0.10.1` produce the same output for the same input.

**Within a minor version:** replay is guaranteed for contracts that do not use names that collide with newly added reserved words.

**Across minor versions:** replay is expected but not guaranteed. A new reserved word or execution type may change how a contract parses if it uses a name that became reserved. Pin the interpreter version in your project's dependencies to prevent unexpected upgrades.

## How to pin

In your project:

```
# requirements.txt
liminate==0.10.0

# pyproject.toml
dependencies = ["liminate==0.10.0"]
```

The Receipts server at `receipts.liminate.dev` pins its interpreter dependency and records `liminate_version` and `pack_version` on every saved contract. These values are the replay coordinates — given the same versions and the same source, the result is identical.

## Session pack versioning

The session pack (`session_pack.json`) follows the same scheme. Pack version `0.3.0` defines `cite`, `verify`, and `measure` with specific slot signatures and execution types. A pack version bump means the pack's vocabulary or execution behavior changed. The pack version is recorded alongside the interpreter version on every saved contract.

Three copies of the session pack exist across the repo family:

- `liminate/examples/pack_session.json` (canonical)
- `liminate-session-contracts/references/session_pack.json`
- `liminate-receipts/packs/session_pack.json`

All three must have the same version and content. A CI check enforces this — see the `liminate` repo's GitHub Actions workflow.
