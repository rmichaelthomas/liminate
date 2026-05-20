# Versioned git hooks

Shared hooks for this repo. Git does not auto-enable a committed hooks
directory, so enable it **once per clone**:

```
git config core.hooksPath .githooks
```

## `pre-commit`

Blocks the following from entering a commit:

- `.DS_Store`, `Thumbs.db`
- Python caches (`__pycache__/`, `*.pyc`, `*.pyo`)
- env / credential files (`.env*`, `*.pem`, `*.key`, `*.p12`, `id_rsa`, `credentials.*`)
- any staged file larger than 5 MB

Bypass intentionally with `git commit --no-verify`.
