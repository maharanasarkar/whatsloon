# Contributing to whatsloon

Thanks for your interest in contributing! This document outlines the process.

## Code of Conduct

By participating you agree to abide by our `CODE_OF_CONDUCT.md`.

## Getting Started

```sh
git clone https://github.com/maharanasarkar/whatsloon.git
cd whatsloon
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Workflow

1. Fork the repo and create a branch: `feat/<short-name>` or `fix/<short-name>`.
2. Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`).
3. Add type hints + Google-style docstrings for public APIs.
4. Add/update tests in `tests/test_<module>.py`.
5. Run checks locally:
   ```sh
   ruff check .
   black --check .
   mypy whatsloon
   pytest
   ```
6. Push and open a PR against `main` using the PR template.

## Pull Requests

- Keep PRs focused; one feature/fix per PR.
- Ensure CI is green (lint, typecheck, tests on 3.9–3.13, coverage ≥80%).
- Update `CHANGELOG.md` under `Unreleased` and docs/examples if behavior changes.

## Reporting Bugs

Use the Bug Report issue template with repro steps, expected vs actual, versions.

## License

Contributions are licensed under MIT.
