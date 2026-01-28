"""Tests for the terminal reporter."""

from __future__ import annotations

from unittest.mock import Mock

from pytest_describe_beautifully.model import (
    DescribeNode,
    DescribeTree,
    NodeType,
    TestOutcome,
    TestResult,
)
from pytest_describe_beautifully.terminal_reporter import (
    OUTCOME_SYMBOLS,
    BeautifulTerminalReporter,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    slow=0.5,
    expand_all=False,
    no_fixtures=False,
):
    """Create a mock pytest config with the necessary options and terminal writer."""
    config = Mock()
    tw = Mock()
    config.get_terminal_writer.return_value = tw

    def getoption(name, default=None):
        options = {
            "describe_slow": slow,
            "describe_expand_all": expand_all,
            "describe_no_fixtures": no_fixtures,
        }
        return options.get(name, default)

    config.getoption = getoption
    return config, tw


def _make_report(
    when="call",
    nodeid="test.py::it_works",
    passed=False,
    failed=False,
    skipped=False,
    duration=0.001,
    longreprtext="",
    sections=None,
    wasxfail=None,
):
    """Create a mock pytest report."""
    report = Mock()
    report.when = when
    report.nodeid = nodeid
    report.passed = passed
    report.failed = failed
    report.skipped = skipped
    report.duration = duration
    report.sections = sections or []
    if longreprtext:
        report.longreprtext = longreprtext
    else:
        del report.longreprtext
    if wasxfail is not None:
        report.wasxfail = wasxfail
    else:
        del report.wasxfail
    return report


# ---------------------------------------------------------------------------
# Tests for OUTCOME_SYMBOLS
# ---------------------------------------------------------------------------


def describe_OUTCOME_SYMBOLS():
    def it_has_entry_for_every_outcome():
        for outcome in TestOutcome:
            assert outcome in OUTCOME_SYMBOLS, f"Missing symbol for {outcome}"

    def it_maps_passed_to_green_check():
        symbol, color = OUTCOME_SYMBOLS[TestOutcome.PASSED]
        assert symbol == "\u2713"
        assert color == "green"

    def it_maps_failed_to_red_x():
        symbol, color = OUTCOME_SYMBOLS[TestOutcome.FAILED]
        assert symbol == "\u2717"
        assert color == "red"

    def it_maps_skipped_to_yellow_circle():
        symbol, color = OUTCOME_SYMBOLS[TestOutcome.SKIPPED]
        assert symbol == "\u25cb"
        assert color == "yellow"

    def it_maps_xfailed_to_yellow_oslash():
        symbol, color = OUTCOME_SYMBOLS[TestOutcome.XFAILED]
        assert symbol == "\u2298"
        assert color == "yellow"

    def it_maps_xpassed_to_red_x_bang():
        symbol, color = OUTCOME_SYMBOLS[TestOutcome.XPASSED]
        assert symbol == "\u2717!"
        assert color == "red"

    def it_maps_error_to_red_skull():
        symbol, color = OUTCOME_SYMBOLS[TestOutcome.ERROR]
        assert symbol == "\u2620"
        assert color == "red"

    def it_maps_pending_to_white_question():
        symbol, color = OUTCOME_SYMBOLS[TestOutcome.PENDING]
        assert symbol == "?"
        assert color == "white"


# ---------------------------------------------------------------------------
# Tests for BeautifulTerminalReporter.__init__
# ---------------------------------------------------------------------------


def describe_BeautifulTerminalReporter_init():
    def it_initializes_with_config_defaults():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        assert reporter.config is config
        assert reporter.expand_all is False
        assert reporter.no_fixtures is False
        # _tw is None initially; the tw property lazily calls get_terminal_writer()
        assert reporter._tw is None
        assert reporter.tw is tw  # triggers lazy init
        assert reporter._current_stack == []
        assert reporter.collector.tree.slow_threshold == 0.5

    def it_initializes_with_custom_options():
        config, tw = _make_config(slow=1.0, expand_all=True, no_fixtures=True)
        reporter = BeautifulTerminalReporter(config)

        assert reporter.expand_all is True
        assert reporter.no_fixtures is True
        assert reporter.collector.tree.slow_threshold == 1.0


# ---------------------------------------------------------------------------
# Tests for pytest_collection_modifyitems
# ---------------------------------------------------------------------------


def describe_pytest_collection_modifyitems():
    def it_delegates_to_collector_build_from_items():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)
        reporter.collector = Mock()

        items = [Mock(), Mock()]
        reporter.pytest_collection_modifyitems(items)

        reporter.collector.build_from_items.assert_called_once_with(items)


# ---------------------------------------------------------------------------
# Tests for pytest_runtest_logreport
# ---------------------------------------------------------------------------


def describe_pytest_runtest_logreport():
    def _setup_reporter_with_tree():
        """Set up a reporter with a pre-built tree."""
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        # Build a small tree manually
        test_node = DescribeNode(
            name="it_works",
            display_name="it works",
            node_type=NodeType.TEST,
            nodeid="test.py::describe_Foo::it_works",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )
        describe_node = DescribeNode(
            name="describe_Foo",
            display_name="Foo",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::describe_Foo",
            children=[test_node],
        )
        file_node = DescribeNode(
            name="test.py",
            display_name="test.py",
            node_type=NodeType.FILE,
            nodeid="test.py",
            children=[describe_node],
        )
        reporter.collector.tree = DescribeTree(roots=[file_node])
        return reporter, tw

    def it_processes_call_reports():
        reporter, tw = _setup_reporter_with_tree()

        report = _make_report(
            when="call",
            nodeid="test.py::describe_Foo::it_works",
            passed=True,
            duration=0.01,
        )
        reporter.pytest_runtest_logreport(report)

        # Should have printed header and test line
        assert tw.line.call_count >= 2

    def it_processes_setup_failure_reports():
        reporter, tw = _setup_reporter_with_tree()

        report = _make_report(
            when="setup",
            nodeid="test.py::describe_Foo::it_works",
            failed=True,
            duration=0.01,
        )
        reporter.pytest_runtest_logreport(report)

        # Should have printed output
        assert tw.line.call_count >= 1

    def it_processes_setup_skip_reports():
        reporter, tw = _setup_reporter_with_tree()

        report = _make_report(
            when="setup",
            nodeid="test.py::describe_Foo::it_works",
            skipped=True,
            duration=0.001,
        )
        reporter.pytest_runtest_logreport(report)

        assert tw.line.call_count >= 1

    def it_ignores_setup_passed_reports():
        reporter, tw = _setup_reporter_with_tree()

        report = _make_report(
            when="setup",
            nodeid="test.py::describe_Foo::it_works",
            passed=True,
            duration=0.001,
        )
        reporter.pytest_runtest_logreport(report)

        # No output expected for setup passed
        tw.line.assert_not_called()

    def it_ignores_teardown_reports():
        reporter, tw = _setup_reporter_with_tree()

        report = _make_report(
            when="teardown",
            nodeid="test.py::describe_Foo::it_works",
            passed=True,
            duration=0.001,
        )
        reporter.pytest_runtest_logreport(report)

        tw.line.assert_not_called()

    def it_ignores_reports_for_unknown_nodeids():
        reporter, tw = _setup_reporter_with_tree()

        report = _make_report(
            when="call",
            nodeid="nonexistent::test",
            passed=True,
            duration=0.01,
        )
        reporter.pytest_runtest_logreport(report)

        tw.line.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for _print_headers_for
# ---------------------------------------------------------------------------


def describe_print_headers_for():
    def _setup_reporter_with_nested_tree():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        test_node = DescribeNode(
            name="it_works",
            display_name="it works",
            node_type=NodeType.TEST,
            nodeid="test.py::describe_Outer::describe_inner::it_works",
        )
        inner = DescribeNode(
            name="describe_inner",
            display_name="inner",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::describe_Outer::describe_inner",
            children=[test_node],
        )
        outer = DescribeNode(
            name="describe_Outer",
            display_name="Outer",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::describe_Outer",
            children=[inner],
        )
        file_node = DescribeNode(
            name="test.py",
            display_name="test.py",
            node_type=NodeType.FILE,
            nodeid="test.py",
            children=[outer],
        )
        reporter.collector.tree = DescribeTree(roots=[file_node])
        return reporter, tw

    def it_prints_new_block_headers():
        reporter, tw = _setup_reporter_with_nested_tree()

        reporter._print_headers_for("test.py::describe_Outer::describe_inner::it_works")

        # Should print Outer and inner headers
        calls = tw.line.call_args_list
        assert any("Outer" in str(c) for c in calls)
        assert any("inner" in str(c) for c in calls)

    def it_does_not_reprint_existing_headers():
        reporter, tw = _setup_reporter_with_nested_tree()

        # First call prints headers
        reporter._print_headers_for("test.py::describe_Outer::describe_inner::it_works")
        assert tw.line.call_count > 0  # headers were printed

        # Second call for same block should not print again
        tw.reset_mock()
        reporter._print_headers_for("test.py::describe_Outer::describe_inner::it_works")
        assert tw.line.call_count == 0

    def it_prints_headers_with_docstrings_in_expand_mode():
        config, tw = _make_config(expand_all=True)
        reporter = BeautifulTerminalReporter(config)

        test_node = DescribeNode(
            name="it_works",
            display_name="it works",
            node_type=NodeType.TEST,
            nodeid="test.py::describe_Foo::it_works",
        )
        describe_node = DescribeNode(
            name="describe_Foo",
            display_name="Foo",
            docstring="Foo operations.",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::describe_Foo",
            children=[test_node],
        )
        file_node = DescribeNode(
            name="test.py",
            display_name="test.py",
            node_type=NodeType.FILE,
            nodeid="test.py",
            children=[describe_node],
        )
        reporter.collector.tree = DescribeTree(roots=[file_node])

        reporter._print_headers_for("test.py::describe_Foo::it_works")

        calls = tw.line.call_args_list
        assert any("Foo -- Foo operations." in str(c) for c in calls)

    def it_does_not_show_docstrings_when_not_expand_mode():
        config, tw = _make_config(expand_all=False)
        reporter = BeautifulTerminalReporter(config)

        describe_node = DescribeNode(
            name="describe_Foo",
            display_name="Foo",
            docstring="Should not appear.",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::describe_Foo",
            children=[
                DescribeNode(
                    name="it_works",
                    display_name="it works",
                    node_type=NodeType.TEST,
                    nodeid="test.py::describe_Foo::it_works",
                ),
            ],
        )
        file_node = DescribeNode(
            name="test.py",
            display_name="test.py",
            node_type=NodeType.FILE,
            nodeid="test.py",
            children=[describe_node],
        )
        reporter.collector.tree = DescribeTree(roots=[file_node])

        reporter._print_headers_for("test.py::describe_Foo::it_works")

        calls = tw.line.call_args_list
        assert not any("Should not appear" in str(c) for c in calls)

    def it_updates_current_stack():
        reporter, tw = _setup_reporter_with_nested_tree()

        reporter._print_headers_for("test.py::describe_Outer::describe_inner::it_works")

        assert reporter._current_stack == [
            "test.py::describe_Outer",
            "test.py::describe_Outer::describe_inner",
        ]

    def it_skips_block_ids_not_found_in_tree():
        """Cover the branch where find_by_nodeid returns None for a block_id."""
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        # Create a tree with a file node but NO describe block
        file_node = DescribeNode(
            name="test.py",
            display_name="test.py",
            node_type=NodeType.FILE,
            nodeid="test.py",
            children=[],
        )
        reporter.collector.tree = DescribeTree(roots=[file_node])

        # Pass a nodeid with a describe block that isn't in the tree
        reporter._print_headers_for("test.py::describe_Missing::it_works")

        # Should not print any header (block_node is None)
        tw.line.assert_not_called()

    def it_handles_block_removed_between_loops():
        """Cover the branch where block_node found in first loop is gone in second.

        This exercises the ``if block_node:`` guard at line 78 returning False.
        """
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        describe_node = DescribeNode(
            name="describe_Foo",
            display_name="Foo",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::describe_Foo",
            children=[],
        )
        file_node = DescribeNode(
            name="test.py",
            display_name="test.py",
            node_type=NodeType.FILE,
            nodeid="test.py",
            children=[describe_node],
        )
        tree = DescribeTree(roots=[file_node])
        reporter.collector.tree = tree

        # Patch find_by_nodeid: first call returns the node (for building
        # block_ids), second call returns None (simulating removal).
        call_count = {"n": 0}
        original_find = tree.find_by_nodeid

        def patched_find(nodeid):
            call_count["n"] += 1
            if nodeid == "test.py::describe_Foo" and call_count["n"] > 1:
                return None
            return original_find(nodeid)

        tree.find_by_nodeid = patched_find

        reporter._print_headers_for("test.py::describe_Foo::it_works")

        # No header should be printed since block_node was None
        tw.line.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for _print_test_line
# ---------------------------------------------------------------------------


def describe_print_test_line():
    def it_prints_passed_test():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_works",
            display_name="it works",
            node_type=NodeType.TEST,
            nodeid="test.py::it_works",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )

        reporter._print_test_line(node)

        tw.line.assert_called_once()
        line_text = tw.line.call_args[0][0]
        assert "\u2713" in line_text
        assert "it works" in line_text
        assert tw.line.call_args[1] == {"green": True}

    def it_prints_failed_test_with_longrepr():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_fails",
            display_name="it fails",
            node_type=NodeType.TEST,
            nodeid="test.py::it_fails",
            result=TestResult(
                outcome=TestOutcome.FAILED,
                duration=0.05,
                longrepr="AssertionError: bad\nExpected: True",
            ),
        )

        reporter._print_test_line(node)

        # Main line + 2 longrepr lines
        assert tw.line.call_count == 3
        # First call: the test line
        main_line = tw.line.call_args_list[0][0][0]
        assert "\u2717" in main_line
        assert "it fails" in main_line
        assert tw.line.call_args_list[0][1] == {"red": True}
        # Longrepr lines
        assert "AssertionError: bad" in tw.line.call_args_list[1][0][0]
        assert "Expected: True" in tw.line.call_args_list[2][0][0]
        # Longrepr lines are red
        assert tw.line.call_args_list[1][1] == {"red": True}

    def it_prints_error_test_with_longrepr():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_errors",
            display_name="it errors",
            node_type=NodeType.TEST,
            nodeid="test.py::it_errors",
            result=TestResult(
                outcome=TestOutcome.ERROR,
                duration=0.02,
                longrepr="RuntimeError: fixture broke",
            ),
        )

        reporter._print_test_line(node)

        assert tw.line.call_count == 2
        main_line = tw.line.call_args_list[0][0][0]
        assert "\u2620" in main_line
        assert tw.line.call_args_list[0][1] == {"red": True}

    def it_prints_skipped_test():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_skips",
            display_name="it skips",
            node_type=NodeType.TEST,
            nodeid="test.py::it_skips",
            result=TestResult(outcome=TestOutcome.SKIPPED, duration=0.0),
        )

        reporter._print_test_line(node)

        tw.line.assert_called_once()
        line_text = tw.line.call_args[0][0]
        assert "\u25cb" in line_text
        assert tw.line.call_args[1] == {"yellow": True}

    def it_prints_xfailed_test():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_xfails",
            display_name="it xfails",
            node_type=NodeType.TEST,
            nodeid="test.py::it_xfails",
            result=TestResult(outcome=TestOutcome.XFAILED, duration=0.01),
        )

        reporter._print_test_line(node)

        tw.line.assert_called_once()
        line_text = tw.line.call_args[0][0]
        assert "\u2298" in line_text
        assert tw.line.call_args[1] == {"yellow": True}

    def it_prints_xpassed_test():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_xpasses",
            display_name="it xpasses",
            node_type=NodeType.TEST,
            nodeid="test.py::it_xpasses",
            result=TestResult(outcome=TestOutcome.XPASSED, duration=0.01),
        )

        reporter._print_test_line(node)

        tw.line.assert_called_once()
        line_text = tw.line.call_args[0][0]
        assert "\u2717!" in line_text
        assert tw.line.call_args[1] == {"red": True}

    def it_prints_pending_test():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_pending",
            display_name="it pending",
            node_type=NodeType.TEST,
            nodeid="test.py::it_pending",
            result=TestResult(outcome=TestOutcome.PENDING, duration=0.0),
        )

        reporter._print_test_line(node)

        tw.line.assert_called_once()
        line_text = tw.line.call_args[0][0]
        assert "?" in line_text
        assert tw.line.call_args[1] == {"white": True}

    def it_skips_node_without_result():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_no_result",
            display_name="it no result",
            node_type=NodeType.TEST,
            nodeid="test.py::it_no_result",
        )

        reporter._print_test_line(node)

        tw.line.assert_not_called()

    def it_marks_slow_tests():
        config, tw = _make_config(slow=0.01)
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_is_slow",
            display_name="it is slow",
            node_type=NodeType.TEST,
            nodeid="test.py::it_is_slow",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.5),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert "\u23f1" in line_text

    def it_does_not_mark_fast_tests():
        config, tw = _make_config(slow=1.0)
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_is_fast",
            display_name="it is fast",
            node_type=NodeType.TEST,
            nodeid="test.py::it_is_fast",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert "\u23f1" not in line_text

    def it_shows_duration_in_parentheses():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_has_duration",
            display_name="it has duration",
            node_type=NodeType.TEST,
            nodeid="test.py::it_has_duration",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.123),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert "(123ms)" in line_text

    def it_shows_docstring_in_expand_mode():
        config, tw = _make_config(expand_all=True)
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_has_doc",
            display_name="it has doc",
            docstring="Detailed description.",
            node_type=NodeType.TEST,
            nodeid="test.py::it_has_doc",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert "-- Detailed description." in line_text

    def it_does_not_show_docstring_without_expand():
        config, tw = _make_config(expand_all=False)
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_has_doc",
            display_name="it has doc",
            docstring="Should not show.",
            node_type=NodeType.TEST,
            nodeid="test.py::it_has_doc",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert "Should not show" not in line_text

    def it_does_not_show_docstring_when_empty_in_expand_mode():
        config, tw = _make_config(expand_all=True)
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_no_doc",
            display_name="it no doc",
            docstring="",
            node_type=NodeType.TEST,
            nodeid="test.py::it_no_doc",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert " -- " not in line_text

    def it_shows_fixtures_in_expand_mode():
        config, tw = _make_config(expand_all=True)
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_uses_fixtures",
            display_name="it uses fixtures",
            node_type=NodeType.TEST,
            nodeid="test.py::it_uses_fixtures",
            result=TestResult(
                outcome=TestOutcome.PASSED,
                duration=0.01,
                fixture_names=["db", "client"],
            ),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert "\U0001f527 db, client" in line_text

    def it_hides_fixtures_with_no_fixtures_flag():
        config, tw = _make_config(expand_all=True, no_fixtures=True)
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_uses_fixtures",
            display_name="it uses fixtures",
            node_type=NodeType.TEST,
            nodeid="test.py::it_uses_fixtures",
            result=TestResult(
                outcome=TestOutcome.PASSED,
                duration=0.01,
                fixture_names=["db"],
            ),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert "\U0001f527" not in line_text

    def it_does_not_show_fixtures_without_expand():
        config, tw = _make_config(expand_all=False)
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_uses_fixtures",
            display_name="it uses fixtures",
            node_type=NodeType.TEST,
            nodeid="test.py::it_uses_fixtures",
            result=TestResult(
                outcome=TestOutcome.PASSED,
                duration=0.01,
                fixture_names=["db"],
            ),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert "\U0001f527" not in line_text

    def it_does_not_show_fixtures_when_empty():
        config, tw = _make_config(expand_all=True)
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_no_fix",
            display_name="it no fix",
            node_type=NodeType.TEST,
            nodeid="test.py::it_no_fix",
            result=TestResult(
                outcome=TestOutcome.PASSED,
                duration=0.01,
                fixture_names=[],
            ),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        assert "\U0001f527" not in line_text

    def it_does_not_print_longrepr_for_passed_tests():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_passes",
            display_name="it passes",
            node_type=NodeType.TEST,
            nodeid="test.py::it_passes",
            result=TestResult(
                outcome=TestOutcome.PASSED,
                duration=0.01,
                longrepr="some repr",
            ),
        )

        reporter._print_test_line(node)

        # Only one line (the test line), no longrepr lines
        tw.line.assert_called_once()

    def it_does_not_print_longrepr_when_empty():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_fails",
            display_name="it fails",
            node_type=NodeType.TEST,
            nodeid="test.py::it_fails",
            result=TestResult(outcome=TestOutcome.FAILED, duration=0.01, longrepr=""),
        )

        reporter._print_test_line(node)

        # Only one line (the test line)
        tw.line.assert_called_once()

    def it_respects_current_stack_indentation():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)
        reporter._current_stack = ["block1", "block2"]

        node = DescribeNode(
            name="it_works",
            display_name="it works",
            node_type=NodeType.TEST,
            nodeid="test.py::it_works",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )

        reporter._print_test_line(node)

        line_text = tw.line.call_args[0][0]
        # Indentation should be 2 * 2 = 4 spaces
        assert line_text.startswith("    ")


# ---------------------------------------------------------------------------
# Tests for pytest_terminal_summary
# ---------------------------------------------------------------------------


def describe_pytest_terminal_summary():
    def it_prints_summary_with_pass_counts():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        test1 = DescribeNode(
            name="it_adds",
            display_name="it adds",
            node_type=NodeType.TEST,
            nodeid="test.py::describe_Math::it_adds",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )
        test2 = DescribeNode(
            name="it_subtracts",
            display_name="it subtracts",
            node_type=NodeType.TEST,
            nodeid="test.py::describe_Math::it_subtracts",
            result=TestResult(outcome=TestOutcome.FAILED, duration=0.02),
        )
        describe_node = DescribeNode(
            name="describe_Math",
            display_name="Math",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::describe_Math",
            children=[test1, test2],
        )
        file_node = DescribeNode(
            name="test.py",
            display_name="test.py",
            node_type=NodeType.FILE,
            nodeid="test.py",
            children=[describe_node],
        )
        reporter.collector.tree = DescribeTree(roots=[file_node])

        reporter.pytest_terminal_summary(Mock())

        calls = [str(c) for c in tw.line.call_args_list]
        # Should print Test Summary header
        assert any("Test Summary" in c for c in calls)
        # Should print describe block with pass counts
        assert any("Math" in c and "1/2 passed" in c for c in calls)

    def it_does_nothing_when_tree_has_no_roots():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)
        reporter.collector.tree = DescribeTree(roots=[])

        reporter.pytest_terminal_summary(Mock())

        tw.line.assert_not_called()

    def it_prints_summary_for_multiple_files():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        test1 = DescribeNode(
            name="it_a",
            display_name="it a",
            node_type=NodeType.TEST,
            nodeid="a.py::describe_A::it_a",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )
        desc1 = DescribeNode(
            name="describe_A",
            display_name="A",
            node_type=NodeType.DESCRIBE,
            nodeid="a.py::describe_A",
            children=[test1],
        )
        file1 = DescribeNode(
            name="a.py",
            display_name="a.py",
            node_type=NodeType.FILE,
            nodeid="a.py",
            children=[desc1],
        )

        test2 = DescribeNode(
            name="it_b",
            display_name="it b",
            node_type=NodeType.TEST,
            nodeid="b.py::describe_B::it_b",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.02),
        )
        desc2 = DescribeNode(
            name="describe_B",
            display_name="B",
            node_type=NodeType.DESCRIBE,
            nodeid="b.py::describe_B",
            children=[test2],
        )
        file2 = DescribeNode(
            name="b.py",
            display_name="b.py",
            node_type=NodeType.FILE,
            nodeid="b.py",
            children=[desc2],
        )

        reporter.collector.tree = DescribeTree(roots=[file1, file2])
        reporter.pytest_terminal_summary(Mock())

        calls = [str(c) for c in tw.line.call_args_list]
        assert any("A" in c and "1/1 passed" in c for c in calls)
        assert any("B" in c and "1/1 passed" in c for c in calls)


# ---------------------------------------------------------------------------
# Tests for _print_summary_node
# ---------------------------------------------------------------------------


def describe_print_summary_node():
    def it_prints_test_node_with_result():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_works",
            display_name="it works",
            node_type=NodeType.TEST,
            nodeid="test.py::it_works",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )

        reporter._print_summary_node(node, prefix="", is_last=True)

        tw.line.assert_called_once()
        line_text = tw.line.call_args[0][0]
        assert "\u2514\u2500\u2500 " in line_text
        assert "\u2713" in line_text
        assert "it works" in line_text
        assert "10ms" in line_text

    def it_prints_test_node_without_result():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_pending",
            display_name="it pending",
            node_type=NodeType.TEST,
            nodeid="test.py::it_pending",
        )

        reporter._print_summary_node(node, prefix="", is_last=True)

        tw.line.assert_called_once()
        line_text = tw.line.call_args[0][0]
        assert "0ms" in line_text

    def it_prints_describe_node_with_counts():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        child1 = DescribeNode(
            name="it_a",
            display_name="it a",
            node_type=NodeType.TEST,
            nodeid="test.py::d::it_a",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )
        child2 = DescribeNode(
            name="it_b",
            display_name="it b",
            node_type=NodeType.TEST,
            nodeid="test.py::d::it_b",
            result=TestResult(outcome=TestOutcome.FAILED, duration=0.02),
        )
        node = DescribeNode(
            name="describe_Block",
            display_name="Block",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::d",
            children=[child1, child2],
        )

        reporter._print_summary_node(node, prefix="", is_last=True)

        calls = tw.line.call_args_list
        # First call is the describe block
        describe_line = calls[0][0][0]
        assert "Block" in describe_line
        assert "1/2 passed" in describe_line

    def it_uses_not_last_connector():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_works",
            display_name="it works",
            node_type=NodeType.TEST,
            nodeid="test.py::it_works",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )

        reporter._print_summary_node(node, prefix="", is_last=False)

        line_text = tw.line.call_args[0][0]
        assert "\u251c\u2500\u2500 " in line_text

    def it_uses_prefix_for_nesting():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        node = DescribeNode(
            name="it_works",
            display_name="it works",
            node_type=NodeType.TEST,
            nodeid="test.py::it_works",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )

        reporter._print_summary_node(node, prefix="\u2502   ", is_last=True)

        line_text = tw.line.call_args[0][0]
        assert line_text.startswith("\u2502   \u2514\u2500\u2500 ")

    def it_orders_describe_children_before_test_children():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        test_child = DescribeNode(
            name="it_a",
            display_name="it a",
            node_type=NodeType.TEST,
            nodeid="test.py::d::it_a",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )
        describe_child = DescribeNode(
            name="describe_inner",
            display_name="inner",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::d::describe_inner",
            children=[
                DescribeNode(
                    name="it_b",
                    display_name="it b",
                    node_type=NodeType.TEST,
                    nodeid="test.py::d::describe_inner::it_b",
                    result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
                ),
            ],
        )
        node = DescribeNode(
            name="describe_Block",
            display_name="Block",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::d",
            children=[test_child, describe_child],
        )

        reporter._print_summary_node(node, prefix="", is_last=True)

        calls = tw.line.call_args_list
        call_texts = [c[0][0] for c in calls]
        # describe_child "inner" should come before test_child "it a"
        inner_idx = next(i for i, t in enumerate(call_texts) if "inner" in t)
        test_idx = next(i for i, t in enumerate(call_texts) if "it a" in t)
        assert inner_idx < test_idx

    def it_uses_pipe_prefix_for_not_last_children():
        config, tw = _make_config()
        reporter = BeautifulTerminalReporter(config)

        child = DescribeNode(
            name="it_a",
            display_name="it a",
            node_type=NodeType.TEST,
            nodeid="test.py::d::it_a",
            result=TestResult(outcome=TestOutcome.PASSED, duration=0.01),
        )
        node = DescribeNode(
            name="describe_Block",
            display_name="Block",
            node_type=NodeType.DESCRIBE,
            nodeid="test.py::d",
            children=[child],
        )

        # Print with is_last=False to test pipe prefix propagation
        reporter._print_summary_node(node, prefix="", is_last=False)

        calls = tw.line.call_args_list
        child_line = calls[1][0][0]
        # When parent is not last, child prefix should have pipe
        assert "\u2502   " in child_line


# ---------------------------------------------------------------------------
# Integration-style: pytester-based tests
# ---------------------------------------------------------------------------


def describe_pytester_integration():
    def describe_basic_output():
        def it_shows_describe_block_headers_and_test_results(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_example="""
                def describe_Calculator():
                    def it_adds_numbers():
                        assert 1 + 1 == 2

                    def it_subtracts_numbers():
                        assert 3 - 1 == 2
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(
                [
                    "*Calculator*",
                    "*\u2713 it adds numbers*",
                    "*\u2713 it subtracts numbers*",
                ]
            )

        def it_shows_nested_describe_blocks(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_nested="""
                def describe_Math():
                    def describe_add():
                        def it_adds_positives():
                            assert 1 + 1 == 2
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(
                [
                    "*Math*",
                    "*add*",
                    "*\u2713 it adds positives*",
                ]
            )

    def describe_outcome_symbols():
        def it_shows_check_for_passed(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_pass="""
                def describe_Tests():
                    def it_passes():
                        assert True
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(["*\u2713 it passes*"])

        def it_shows_x_for_failed(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_fail="""
                def describe_Tests():
                    def it_fails():
                        assert False, "expected failure"
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(
                [
                    "*\u2717 it fails*",
                    "*expected failure*",
                ]
            )

        def it_shows_circle_for_skipped(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_skip="""
                import pytest
                def describe_Tests():
                    def it_is_skipped():
                        pytest.skip("reason")
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(["*\u25cb it is skipped*"])

        def it_shows_xfail_symbol(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_xfail="""
                import pytest
                def describe_Tests():
                    @pytest.mark.xfail
                    def it_is_expected_to_fail():
                        assert False
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(["*\u2298 it is expected to fail*"])

        def it_shows_xpass_symbol(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_xpass="""
                import pytest
                def describe_Tests():
                    @pytest.mark.xfail
                    def it_unexpectedly_passes():
                        assert True
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(["*\u2717! it unexpectedly passes*"])

        def it_shows_error_symbol_for_fixture_error(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_error="""
                import pytest

                @pytest.fixture
                def broken_fixture():
                    raise RuntimeError("fixture broke")

                def describe_Tests():
                    def it_has_error(broken_fixture):
                        pass
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(["*\u2620 it has error*"])

    def describe_slow_test_marker():
        def it_marks_slow_tests_with_stopwatch(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_slow="""
                import time
                def describe_Tests():
                    def it_is_slow():
                        time.sleep(0.6)
                        assert True
                """
            )
            result = pytester.runpytest(
                "--describe-beautifully", "--describe-slow=0.1", "-p", "no:cov"
            )
            result.stdout.fnmatch_lines(["*\u23f1*"])

    def describe_expand_all_mode():
        def it_shows_docstrings(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_doc='''
                def describe_Calculator():
                    """Calculator operations."""
                    def it_adds():
                        """Adds two numbers."""
                        assert 1 + 1 == 2
                '''
            )
            result = pytester.runpytest(
                "--describe-beautifully",
                "--describe-expand-all",
                "-p",
                "no:cov",
            )
            result.stdout.fnmatch_lines(
                [
                    "*Calculator -- Calculator operations.*",
                    "*\u2713 it adds -- Adds two numbers.*",
                ]
            )

        def it_shows_fixtures(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_fixtures="""
                import pytest

                @pytest.fixture
                def calculator():
                    return object()

                def describe_Calculator():
                    def it_uses_fixture(calculator):
                        assert calculator is not None
                """
            )
            result = pytester.runpytest(
                "--describe-beautifully",
                "--describe-expand-all",
                "-p",
                "no:cov",
            )
            result.stdout.fnmatch_lines(["*\U0001f527 calculator*"])

        def it_hides_fixtures_with_no_fixtures_flag(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_no_fix="""
                import pytest

                @pytest.fixture
                def calculator():
                    return object()

                def describe_Calculator():
                    def it_uses_fixture(calculator):
                        assert calculator is not None
                """
            )
            result = pytester.runpytest(
                "--describe-beautifully",
                "--describe-expand-all",
                "--describe-no-fixtures",
                "-p",
                "no:cov",
            )
            result.stdout.no_fnmatch_line("*\U0001f527*")

    def describe_summary_tree():
        def it_shows_summary_with_pass_counts(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_summary="""
                def describe_Math():
                    def describe_add():
                        def it_adds():
                            assert True

                        def it_adds_negatives():
                            assert True
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(
                [
                    "*Test Summary*",
                    "*Math*2/2 passed*",
                    "*add*2/2 passed*",
                ]
            )

        def it_shows_individual_tests_in_summary(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_summary2="""
                def describe_Tests():
                    def it_passes():
                        assert True
                """
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(
                [
                    "*Test Summary*",
                    "*it passes*",
                ]
            )

    def describe_multiple_files():
        def it_handles_tests_across_files(pytester):
            pytester.makeini(
                """
                [pytest]
                describe_prefixes = describe_
                python_files = test_*.py
                python_functions = it_* they_*
                """
            )
            pytester.makepyfile(
                test_one="""
                def describe_One():
                    def it_works():
                        assert True
                """,
                test_two="""
                def describe_Two():
                    def it_works():
                        assert True
                """,
            )
            result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
            result.stdout.fnmatch_lines(
                [
                    "*One*",
                    "*\u2713 it works*",
                    "*Two*",
                    "*\u2713 it works*",
                ]
            )
