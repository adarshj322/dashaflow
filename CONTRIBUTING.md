# Contributing to DashaFlow

## Getting Started

1. Fork the repo and clone your fork
2. Create a virtual environment: `python -m venv .venv && .venv\Scripts\activate` (or `source .venv/bin/activate` on Linux/Mac)
3. Install in dev mode: `pip install -e . && pip install pytest`
4. Run tests: `pytest tests/ -q`

## Making Changes

1. Create a branch from `main`: `git checkout -b feature/your-feature`
2. Make your changes
3. Add/update tests for any new functionality
4. Ensure all tests pass: `pytest tests/ -q`
5. Commit with a clear message (e.g. `feat: add D45 varga support`)
6. Push and open a Pull Request against `main`

## Code Style

- Follow existing patterns in the codebase
- All astronomical calculations must use Swiss Ephemeris (Sidereal Lahiri)
- Add tests for new features in `tests/`

## What We're Looking For

- New varga calculations
- Additional yoga detections
- Bug fixes with test cases
- Documentation improvements

## Reporting Issues

Open a GitHub issue with:
- What you expected vs what happened
- Birth data that reproduces the issue (use test data, not real personal data)
- Python version and OS
