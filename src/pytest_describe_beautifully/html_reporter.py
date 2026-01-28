"""HTML report generator for pytest-describe test suites."""

from __future__ import annotations

import html
import string
from pathlib import Path

from pytest_describe_beautifully.model import DescribeNode, DescribeTree, TestOutcome
from pytest_describe_beautifully.naming import format_duration

OUTCOME_SYMBOLS = {
    TestOutcome.PASSED: ("✓", "passed"),
    TestOutcome.FAILED: ("✗", "failed"),
    TestOutcome.SKIPPED: ("○", "skipped"),
    TestOutcome.XFAILED: ("⊘", "xfailed"),
    TestOutcome.XPASSED: ("✗!", "xpassed"),
    TestOutcome.ERROR: ("☠", "error"),
    TestOutcome.PENDING: ("?", "pending"),
}

HTML_TEMPLATE = string.Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Test Report - pytest-describe-beautifully</title>
<style>
:root {
    --bg: #1a1a2e;
    --fg: #e0e0e0;
    --card-bg: #16213e;
    --border: #2a2a4a;
    --passed: #4ade80;
    --failed: #f87171;
    --skipped: #fbbf24;
    --xfailed: #fbbf24;
    --xpassed: #f87171;
    --error: #f87171;
    --pending: #94a3b8;
    --slow: #f59e0b;
    --fixture: #60a5fa;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
    background: var(--bg);
    color: var(--fg);
    padding: 20px;
    line-height: 1.6;
}
.header {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    margin-bottom: 20px;
    padding: 16px;
    background: var(--card-bg);
    border-radius: 8px;
    border: 1px solid var(--border);
}
.header h1 { font-size: 1.2em; margin-right: auto; }
.badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: bold;
}
.badge-total { background: var(--border); }
.badge-passed { background: var(--passed); color: #000; }
.badge-failed { background: var(--failed); color: #000; }
.badge-skipped { background: var(--skipped); color: #000; }
.badge-duration { background: var(--border); }
.controls {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}
.controls button {
    padding: 6px 14px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--card-bg);
    color: var(--fg);
    cursor: pointer;
    font-size: 0.85em;
}
.controls button:hover { border-color: var(--fg); }
.controls button.active { border-color: var(--failed); color: var(--failed); }
.tree { padding-left: 0; }
details {
    margin-left: 20px;
    border-left: 2px solid var(--border);
    padding-left: 12px;
    margin-bottom: 4px;
}
details.root { margin-left: 0; }
summary {
    cursor: pointer;
    padding: 4px 0;
    font-weight: bold;
    list-style: none;
}
summary::-webkit-details-marker { display: none; }
summary::before {
    content: "▶ ";
    display: inline-block;
    transition: transform 0.2s;
}
details[open] > summary::before {
    transform: rotate(90deg);
}
.test-item {
    margin-left: 20px;
    padding: 3px 0;
    font-family: monospace;
}
.test-item .symbol { font-weight: bold; margin-right: 6px; }
.test-item .duration { color: var(--pending); margin-left: 8px; font-size: 0.85em; }
.test-item .slow { color: var(--slow); }
.test-item .docstring { color: var(--pending); font-style: italic; margin-left: 8px; }
.test-item .fixtures { color: var(--fixture); margin-left: 8px; font-size: 0.85em; }
.passed .symbol { color: var(--passed); }
.failed .symbol { color: var(--failed); }
.skipped .symbol { color: var(--skipped); }
.xfailed .symbol { color: var(--xfailed); }
.xpassed .symbol { color: var(--xpassed); }
.error .symbol { color: var(--error); }
.pending .symbol { color: var(--pending); }
.failure-block {
    margin: 4px 0 8px 40px;
    padding: 10px;
    background: #2d1515;
    border: 1px solid var(--failed);
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.85em;
    white-space: pre-wrap;
    color: var(--failed);
    overflow-x: auto;
}
.describe-stats {
    font-size: 0.8em;
    color: var(--pending);
    font-weight: normal;
    margin-left: 8px;
}
.hidden { display: none !important; }
</style>
</head>
<body>
<div class="header">
    <h1>Test Report</h1>
    <span class="badge badge-total">${total} tests</span>
    <span class="badge badge-passed">${passed} passed</span>
    <span class="badge badge-failed">${failed} failed</span>
    <span class="badge badge-skipped">${skipped} skipped</span>
    <span class="badge badge-duration">${duration}</span>
</div>
<div class="controls">
    <button onclick="expandAll()">Expand All</button>
    <button onclick="collapseAll()">Collapse All</button>
    <button id="failedOnlyBtn" onclick="toggleFailedOnly()">Show Failed Only</button>
</div>
<div class="tree">
${tree_html}
</div>
<script>
function expandAll() {
    document.querySelectorAll('details').forEach(d => d.open = true);
}
function collapseAll() {
    document.querySelectorAll('details').forEach(d => d.open = false);
}
let failedOnly = false;
function toggleFailedOnly() {
    failedOnly = !failedOnly;
    const btn = document.getElementById('failedOnlyBtn');
    btn.classList.toggle('active', failedOnly);
    btn.textContent = failedOnly ? 'Show All' : 'Show Failed Only';
    document.querySelectorAll('.test-item').forEach(el => {
        if (failedOnly && !el.classList.contains('failed') && !el.classList.contains('error')) {
            el.classList.add('hidden');
        } else {
            el.classList.remove('hidden');
        }
    });
    document.querySelectorAll('.failure-block').forEach(el => {
        el.classList.remove('hidden');
    });
    if (failedOnly) {
        document.querySelectorAll('details').forEach(d => {
            const hasFailure = d.querySelector('.failed, .error');
            if (hasFailure) {
                d.open = true;
                d.classList.remove('hidden');
            } else {
                d.classList.add('hidden');
            }
        });
    } else {
        document.querySelectorAll('details').forEach(d => {
            d.classList.remove('hidden');
        });
    }
}
</script>
</body>
</html>
""")


class HtmlReporter:
    """Generates a self-contained HTML test report."""

    def __init__(self, slow_threshold: float = 0.5) -> None:
        self.slow_threshold = slow_threshold

    def generate_report(self, tree: DescribeTree, output_path: str) -> None:
        """Generate the HTML report file."""
        tree_html = self._render_tree(tree)
        html_content = HTML_TEMPLATE.substitute(
            total=tree.total_tests,
            passed=tree.total_passed,
            failed=tree.total_failed,
            skipped=tree.total_skipped,
            duration=format_duration(tree.total_duration),
            tree_html=tree_html,
        )
        Path(output_path).write_text(html_content, encoding="utf-8")

    def _render_tree(self, tree: DescribeTree) -> str:
        """Render the full tree as HTML."""
        parts = [
            self._render_node(child, is_root=True) for root in tree.roots for child in root.children
        ]
        return "\n".join(parts)

    def _render_node(self, node: DescribeNode, is_root: bool = False) -> str:
        """Render a single node and its children."""
        if node.is_test:
            return self._render_test(node)

        # Describe block - render as collapsible <details>
        has_failure = node.overall_outcome in (TestOutcome.FAILED, TestOutcome.ERROR)
        open_attr = " open" if has_failure else ""
        root_class = " root" if is_root else ""

        stats = f"{node.passed_count}/{node.test_count} passed"
        duration_str = format_duration(node.aggregate_duration)

        children_html = [self._render_node(child) for child in node.children]

        docstring_html = ""
        if node.docstring:
            docstring_html = f' <span class="docstring">-- {html.escape(node.docstring)}</span>'

        return (
            f'<details class="{root_class.strip()}"{open_attr}>'
            f"<summary>{html.escape(node.display_name)}{docstring_html}"
            f'<span class="describe-stats">({stats}, {duration_str})</span>'
            f"</summary>\n"
            f"{''.join(children_html)}"
            f"</details>\n"
        )

    def _render_test(self, node: DescribeNode) -> str:
        """Render a test item."""
        if not node.result:
            return ""

        outcome = node.result.outcome
        symbol, css_class = OUTCOME_SYMBOLS.get(outcome, ("?", "pending"))

        duration_str = format_duration(node.result.duration)
        is_slow = node.result.duration > self.slow_threshold
        slow_class = " slow" if is_slow else ""
        slow_marker = " ⏱" if is_slow else ""

        docstring_html = ""
        if node.docstring:
            docstring_html = f'<span class="docstring">-- {html.escape(node.docstring)}</span>'

        fixtures_html = ""
        if node.result.fixture_names:
            fixtures = ", ".join(node.result.fixture_names)
            fixtures_html = f'<span class="fixtures">\U0001f527 {html.escape(fixtures)}</span>'

        test_html = (
            f'<div class="test-item {css_class}">'
            f'<span class="symbol">{symbol}</span>'
            f"{html.escape(node.display_name)}"
            f"{docstring_html}"
            f'<span class="duration{slow_class}">'
            f"({duration_str}){slow_marker}</span>"
            f"{fixtures_html}"
            f"</div>\n"
        )

        # Add failure block
        if outcome in (TestOutcome.FAILED, TestOutcome.ERROR) and node.result.longrepr:
            test_html += f'<div class="failure-block">{html.escape(node.result.longrepr)}</div>\n'

        return test_html
