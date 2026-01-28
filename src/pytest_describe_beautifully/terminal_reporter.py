"""Beautiful terminal reporter for pytest-describe test suites."""

from __future__ import annotations

from pytest_describe_beautifully.collector import TreeCollector
from pytest_describe_beautifully.model import DescribeNode, TestOutcome
from pytest_describe_beautifully.naming import format_duration

# Outcome display configuration
OUTCOME_SYMBOLS = {
    TestOutcome.PASSED: ("\u2713", "green"),
    TestOutcome.FAILED: ("\u2717", "red"),
    TestOutcome.SKIPPED: ("\u25cb", "yellow"),
    TestOutcome.XFAILED: ("\u2298", "yellow"),
    TestOutcome.XPASSED: ("\u2717!", "red"),
    TestOutcome.ERROR: ("\u2620", "red"),
    TestOutcome.PENDING: ("?", "white"),
}


class BeautifulTerminalReporter:
    """Beautiful terminal output for pytest-describe test suites."""

    def __init__(self, config) -> None:
        self.config = config
        self.collector = TreeCollector(
            slow_threshold=config.getoption("describe_slow", 0.5),
        )
        self.expand_all = config.getoption("describe_expand_all", False)
        self.no_fixtures = config.getoption("describe_no_fixtures", False)
        self._tw = None
        self._current_stack: list[str] = []

    @property
    def tw(self):
        if self._tw is None:
            self._tw = self.config.get_terminal_writer()
        return self._tw

    def pytest_collection_modifyitems(self, items: list) -> None:
        """Build the describe tree from collected items."""
        self.collector.build_from_items(items)

    def pytest_runtest_logreport(self, report) -> None:
        """Handle test reports - render results as tests complete."""
        self.collector.update_from_report(report)

        if report.when != "call" and not (
            report.when == "setup" and (report.failed or report.skipped)
        ):
            return

        node = self.collector.tree.find_by_nodeid(report.nodeid)
        if not node:
            return

        # Print describe block headers for new blocks
        self._print_headers_for(report.nodeid)

        # Print the test result line
        self._print_test_line(node)

    def _print_headers_for(self, nodeid: str) -> None:
        """Print describe block headers for blocks we haven't entered yet."""
        parts = nodeid.split("::")
        # Build the path of describe blocks (skip file and test name)
        block_ids = []
        for i in range(1, len(parts)):
            block_id = "::".join(parts[: i + 1])
            block_node = self.collector.tree.find_by_nodeid(block_id)
            if block_node and not block_node.is_test:
                block_ids.append(block_id)

        # Find which blocks are new
        for i, block_id in enumerate(block_ids):
            if block_id not in self._current_stack:
                block_node = self.collector.tree.find_by_nodeid(block_id)
                if block_node:
                    indent = "  " * i
                    header = f"{indent}{block_node.display_name}"
                    if self.expand_all and block_node.docstring:
                        header += f" -- {block_node.docstring}"
                    self.tw.line(header)

        self._current_stack = block_ids

    def _print_test_line(self, node: DescribeNode) -> None:
        """Print a single test result line."""
        if not node.result:
            return

        indent = "  " * len(self._current_stack)
        symbol, color = OUTCOME_SYMBOLS.get(node.result.outcome, ("?", "white"))
        duration_str = format_duration(node.result.duration)

        # Build the line
        line_parts = [f"{indent}{symbol} {node.display_name}"]

        # Add docstring in expand mode
        if self.expand_all and node.docstring:
            line_parts.append(f" -- {node.docstring}")

        line_parts.append(f" ({duration_str})")

        # Mark slow tests
        if node.result.duration > self.collector.tree.slow_threshold:
            line_parts.append(" \u23f1")

        # Add fixtures in expand mode
        if self.expand_all and not self.no_fixtures and node.result.fixture_names:
            fixtures = ", ".join(node.result.fixture_names)
            line_parts.append(f" \U0001f527 {fixtures}")

        # Write the line with color
        markup = {color: True}
        self.tw.line("".join(line_parts), **markup)

        # Print failure details inline
        if node.result.outcome in (TestOutcome.FAILED, TestOutcome.ERROR) and node.result.longrepr:
            for longrepr_line in node.result.longrepr.splitlines():
                self.tw.line(f"{indent}    {longrepr_line}", red=True)

    def pytest_terminal_summary(self, terminalreporter) -> None:
        """Print summary tree at the end of the test session."""
        tree = self.collector.tree
        if not tree.roots:
            return

        self.tw.line()
        self.tw.line("Test Summary", bold=True)
        for root in tree.roots:
            for child in root.children:
                self._print_summary_node(child, prefix="", is_last=True)

    def _print_summary_node(self, node: DescribeNode, prefix: str, is_last: bool) -> None:
        """Recursively print summary tree nodes."""
        connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
        symbol, color = OUTCOME_SYMBOLS.get(node.overall_outcome, ("?", "white"))

        if node.is_test:
            duration_str = format_duration(node.result.duration) if node.result else "0ms"
            line = f"{prefix}{connector}{symbol} {node.display_name} ({duration_str})"
        else:
            passed = node.passed_count
            total = node.test_count
            duration_str = format_duration(node.aggregate_duration)
            stats = f"{passed}/{total} passed, {duration_str}"
            line = f"{prefix}{connector}{symbol} {node.display_name} ({stats})"

        markup = {color: True}
        self.tw.line(line, **markup)

        # Print children
        child_prefix = prefix + ("    " if is_last else "\u2502   ")
        describe_children = [c for c in node.children if not c.is_test]
        test_children = [c for c in node.children if c.is_test]
        all_children = describe_children + test_children

        for i, child in enumerate(all_children):
            child_is_last = i == len(all_children) - 1
            self._print_summary_node(child, child_prefix, child_is_last)
