"""Liminate domain packs.

Each module in this package contributes a concrete `DomainPack` /
`Adapter` pair built on top of the v3a §116–§120 contract defined in
`src/liminate/adapter.py`. Domain packs are loaded externally — via
the `--pack` CLI flag (JSON config, file path or inline) or via
`Session(domain_packs=...)` — not through Liminate-level syntax
(v3a §118).
"""
