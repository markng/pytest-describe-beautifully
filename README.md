# pytest-describe-beautifully

[![CI](https://github.com/markng/pytest-describe-beautifully/actions/workflows/ci.yml/badge.svg)](https://github.com/markng/pytest-describe-beautifully/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pytest-describe-beautifully)](https://pypi.org/project/pytest-describe-beautifully/)
[![Python](https://img.shields.io/pypi/pyversions/pytest-describe-beautifully)](https://pypi.org/project/pytest-describe-beautifully/)

Beautiful terminal and HTML output for [pytest-describe](https://github.com/pytest-dev/pytest-describe).

Transforms pytest-describe's nested test hierarchy into formatted, readable output with real-time results, tree summaries, and self-contained HTML reports.

## Installation

```bash
pip install pytest-describe-beautifully
```

Requires Python 3.11+ and pytest-describe 2.0+.

## Quick Start

```bash
# Enable beautiful terminal output
pytest --describe-beautifully

# Short form
pytest --db

# Generate an HTML report alongside terminal output
pytest --db --describe-html report.html
```

The plugin only activates when `--describe-beautifully` (or `--db`) is passed. Without it, pytest behaves as normal.

## Terminal Output

With `--db`, test results print in real time as they complete, followed by a tree summary at the end:

```
Calculator
  add
    ✓ it adds two numbers (3ms)
    ✓ it handles negatives (1ms)
  divide
    ✓ it divides evenly (2ms)
    ✗ it raises on zero (1ms)

Summary
┌ Calculator (3/4 passed, 7ms)
├─┬ add (2/2 passed, 4ms)
│ ├── ✓ it adds two numbers (3ms)
│ └── ✓ it handles negatives (1ms)
└─┬ divide (1/2 passed, 3ms)
  ├── ✓ it divides evenly (2ms)
  └── ✗ it raises on zero (1ms)
```

### Outcome Symbols

| Symbol | Meaning |
|--------|---------|
| ✓ | Passed |
| ✗ | Failed |
| ○ | Skipped |
| ⊘ | Expected failure (xfail) |
| ✗! | Unexpected pass (xpass) |
| ☠ | Error (setup/teardown) |

### Slow Test Markers

Tests exceeding the slow threshold get a ⏱ marker:

```bash
# Default threshold is 0.5s
pytest --db --describe-slow 1.0
```

### Expanded Mode

Show docstrings and fixtures inline:

```bash
pytest --db --describe-expand-all
```

```
Calculator
  add
    ✓ it adds two numbers (3ms)
        Verifies basic addition of positive integers
        🔧 calculator, sample_data
```

Hide fixtures while keeping docstrings:

```bash
pytest --db --describe-expand-all --describe-no-fixtures
```

## HTML Reports

Generate a self-contained HTML file with no external dependencies:

```bash
pytest --db --describe-html report.html
```

The report includes:

- **Summary badges** -- total tests, passed, failed, skipped, and duration
- **Collapsible describe blocks** -- click to expand/collapse, blocks with failures open automatically
- **Interactive controls** -- Expand All, Collapse All, and Show Failed Only
- **Test details** -- outcome, duration, docstrings, fixtures, and full failure tracebacks
- **Dark theme** with semantic color coding

## All CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--describe-beautifully` / `--db` | off | Enable the plugin |
| `--describe-slow SECONDS` | 0.5 | Slow test threshold |
| `--describe-expand-all` | off | Show docstrings and fixtures inline |
| `--describe-no-fixtures` | off | Hide fixtures in expanded mode |
| `--describe-html PATH` | -- | Generate an HTML report at PATH |

## Name Formatting

The plugin humanizes pytest-describe's naming conventions:

- `describe_MyClass` becomes **MyClass** (CamelCase preserved)
- `describe_my_feature` becomes **my feature**
- `it_does_something` becomes **it does something**
- `they_are_equal` becomes **they are equal**

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests (100% branch coverage enforced)
python -m pytest

# Lint and format
python -m ruff check src/ tests/
python -m ruff format src/ tests/

# Mutation testing
mutmut run
```

## License

MIT
