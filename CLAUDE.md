# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A pytest plugin that transforms pytest-describe's hierarchical test output into formatted terminal and HTML reports. Registered via the `pytest11` entry point as `describe_beautifully`.

## Commands

```bash
# Run all tests (coverage is enforced at 100% with branch coverage via addopts)
python -m pytest

# Run a single test file
python -m pytest tests/describe_model.py

# Run a single test
python -m pytest tests/describe_model.py::describe_DescribeNode::it_identifies_test_nodes

# Lint
python -m ruff check src/ tests/

# Format
python -m ruff format src/ tests/

# Mutation testing
mutmut run
```

## Architecture

The plugin activates only when `--describe-beautifully` (or `--db`) is passed. The data flow is:

1. **plugin.py** — Entry point. Registers CLI options via `pytest_addoption`, creates the reporter and collector in `pytest_configure`, and wires up session finish/unconfigure hooks.

2. **collector.py** (`TreeCollector`) — Walks each pytest item's `listchain()` during `pytest_collection_modifyitems` to build a `DescribeTree`. Classifies each link as FILE, DESCRIBE, or TEST. Caches nodes by `nodeid` for O(1) lookup when updating results from `pytest_runtest_logreport`.

3. **model.py** — Immutable dataclasses (`DescribeTree`, `DescribeNode`, `TestResult`, `TestOutcome`, `NodeType`). `DescribeNode` is recursive: describe blocks contain children (tests or nested describes). Aggregate properties like `test_count`, `overall_outcome`, and `aggregate_duration` are computed recursively from children.

4. **naming.py** — Converts `describe_my_feature` → "my feature" and `it_does_something` → "it does something". Preserves CamelCase in describe names.

5. **terminal_reporter.py** (`BeautifulTerminalReporter`) — Prints results in real-time as tests complete, then prints a tree summary with box-drawing characters at session end.

6. **html_reporter.py** (`HtmlReporter`) — Generates a self-contained HTML file (embedded CSS/JS, no external deps) with collapsible describe blocks, summary badges, and interactive controls.

## Test Conventions

- Test files are named `describe_*.py`, not `test_*.py`
- Test functions use `it_*` or `they_*` prefixes, not `test_*`
- Describe blocks use `describe_` prefix functions for grouping
- Tests use mock factories (e.g., `_make_item()`, `_make_report()`, `_make_config()`) defined locally in each test file — not shared fixtures
- The `sample_tree` fixture in `conftest.py` provides a pre-built tree for reporter tests

## Code Style

- Python 3.12+, line length 100
- Ruff with rules: E, F, I, N, W, UP, C901, S, B, PERF
- Max cyclomatic complexity: 10
- Security rules (S) relaxed in test files
