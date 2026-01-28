"""Tests for the HTML reporter."""


from pytest_describe_beautifully.html_reporter import OUTCOME_SYMBOLS, HtmlReporter
from pytest_describe_beautifully.model import (
    DescribeNode,
    DescribeTree,
    NodeType,
    TestOutcome,
    TestResult,
)


def describe_HtmlReporter():
    def describe_generate_report():
        def it_creates_html_file(tmp_path):
            tree = DescribeTree()
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            assert output.exists()
            content = output.read_text()
            assert "<!DOCTYPE html>" in content

        def it_is_self_contained(tmp_path):
            tree = DescribeTree()
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            content = output.read_text()
            # No external resources
            assert "href=" not in content or 'href="http' not in content
            assert "<style>" in content
            assert "<script>" in content

        def it_shows_summary_badges(tmp_path, sample_tree):
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(sample_tree, str(output))
            content = output.read_text()
            assert "3 tests" in content
            assert "2 passed" in content
            assert "1 failed" in content
            assert "0 skipped" in content

        def it_renders_all_outcome_types(tmp_path):
            # Create a tree with every outcome type
            outcomes = [
                TestOutcome.PASSED, TestOutcome.FAILED, TestOutcome.SKIPPED,
                TestOutcome.XFAILED, TestOutcome.XPASSED, TestOutcome.ERROR,
            ]
            children = []
            for i, outcome in enumerate(outcomes):
                is_err = outcome in (TestOutcome.FAILED, TestOutcome.ERROR)
                longrepr = "error text" if is_err else ""
                children.append(DescribeNode(
                    name=f"it_test_{i}", display_name=f"it test {i}",
                    node_type=NodeType.TEST, nodeid=f"t{i}",
                    result=TestResult(outcome=outcome, duration=0.01, longrepr=longrepr),
                ))
            describe = DescribeNode(
                name="describe_All", display_name="All",
                node_type=NodeType.DESCRIBE, nodeid="d",
                children=children,
            )
            file_node = DescribeNode(
                name="test.py", display_name="test.py",
                node_type=NodeType.FILE, nodeid="test.py",
                children=[describe],
            )
            tree = DescribeTree(roots=[file_node])
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            content = output.read_text()
            for outcome in outcomes:
                symbol, css_class = OUTCOME_SYMBOLS[outcome]
                assert symbol in content
                assert css_class in content

        def it_auto_opens_failed_blocks(tmp_path, sample_tree):
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(sample_tree, str(output))
            content = output.read_text()
            # The Calculator block has failures, should be open
            assert "open" in content

        def it_collapses_passing_blocks(tmp_path):
            child = DescribeNode(
                name="it_works", display_name="it works",
                node_type=NodeType.TEST, nodeid="t",
                result=TestResult(outcome=TestOutcome.PASSED, duration=0.001),
            )
            describe = DescribeNode(
                name="describe_Good", display_name="Good",
                node_type=NodeType.DESCRIBE, nodeid="d",
                children=[child],
            )
            file_node = DescribeNode(
                name="test.py", display_name="test.py",
                node_type=NodeType.FILE, nodeid="test.py",
                children=[describe],
            )
            tree = DescribeTree(roots=[file_node])
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            content = output.read_text()
            # Passing block should not have 'open' attr
            assert '<details class="root">' in content

        def it_shows_docstrings(tmp_path):
            child = DescribeNode(
                name="it_works", display_name="it works",
                node_type=NodeType.TEST, nodeid="t",
                docstring="Test that it works.",
                result=TestResult(outcome=TestOutcome.PASSED, duration=0.001),
            )
            describe = DescribeNode(
                name="describe_Foo", display_name="Foo",
                docstring="Foo operations.",
                node_type=NodeType.DESCRIBE, nodeid="d",
                children=[child],
            )
            file_node = DescribeNode(
                name="test.py", display_name="test.py",
                node_type=NodeType.FILE, nodeid="test.py",
                children=[describe],
            )
            tree = DescribeTree(roots=[file_node])
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            content = output.read_text()
            assert "Foo operations." in content
            assert "Test that it works." in content

        def it_shows_fixtures(tmp_path):
            child = DescribeNode(
                name="it_works", display_name="it works",
                node_type=NodeType.TEST, nodeid="t",
                result=TestResult(
                    outcome=TestOutcome.PASSED, duration=0.001,
                    fixture_names=["my_fixture", "other_fixture"],
                ),
            )
            describe = DescribeNode(
                name="describe_Foo", display_name="Foo",
                node_type=NodeType.DESCRIBE, nodeid="d",
                children=[child],
            )
            file_node = DescribeNode(
                name="test.py", display_name="test.py",
                node_type=NodeType.FILE, nodeid="test.py",
                children=[describe],
            )
            tree = DescribeTree(roots=[file_node])
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            content = output.read_text()
            assert "my_fixture" in content
            assert "other_fixture" in content
            assert "\U0001f527" in content

        def it_marks_slow_tests(tmp_path):
            child = DescribeNode(
                name="it_is_slow", display_name="it is slow",
                node_type=NodeType.TEST, nodeid="t",
                result=TestResult(outcome=TestOutcome.PASSED, duration=1.5),
            )
            describe = DescribeNode(
                name="describe_Foo", display_name="Foo",
                node_type=NodeType.DESCRIBE, nodeid="d",
                children=[child],
            )
            file_node = DescribeNode(
                name="test.py", display_name="test.py",
                node_type=NodeType.FILE, nodeid="test.py",
                children=[describe],
            )
            tree = DescribeTree(roots=[file_node])
            reporter = HtmlReporter(slow_threshold=0.5)
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            content = output.read_text()
            assert "\u23f1" in content
            assert "slow" in content

        def it_shows_failure_blocks(tmp_path):
            child = DescribeNode(
                name="it_fails", display_name="it fails",
                node_type=NodeType.TEST, nodeid="t",
                result=TestResult(
                    outcome=TestOutcome.FAILED, duration=0.01,
                    longrepr="AssertionError: expected True",
                ),
            )
            describe = DescribeNode(
                name="describe_Foo", display_name="Foo",
                node_type=NodeType.DESCRIBE, nodeid="d",
                children=[child],
            )
            file_node = DescribeNode(
                name="test.py", display_name="test.py",
                node_type=NodeType.FILE, nodeid="test.py",
                children=[describe],
            )
            tree = DescribeTree(roots=[file_node])
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            content = output.read_text()
            assert "failure-block" in content
            assert "AssertionError: expected True" in content

        def it_renders_test_without_result(tmp_path):
            child = DescribeNode(
                name="it_pending", display_name="it pending",
                node_type=NodeType.TEST, nodeid="t",
            )
            describe = DescribeNode(
                name="describe_Foo", display_name="Foo",
                node_type=NodeType.DESCRIBE, nodeid="d",
                children=[child],
            )
            file_node = DescribeNode(
                name="test.py", display_name="test.py",
                node_type=NodeType.FILE, nodeid="test.py",
                children=[describe],
            )
            tree = DescribeTree(roots=[file_node])
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            content = output.read_text()
            # Test without result should render empty string (no test-item div)
            assert "it pending" not in content

        def it_escapes_html_in_names(tmp_path):
            child = DescribeNode(
                name="it_handles_angle_brackets",
                display_name="it handles <angle> brackets",
                node_type=NodeType.TEST, nodeid="t",
                result=TestResult(outcome=TestOutcome.PASSED, duration=0.001),
            )
            describe = DescribeNode(
                name="describe_HtmlEscape",
                display_name="<HtmlEscape>",
                node_type=NodeType.DESCRIBE, nodeid="d",
                children=[child],
            )
            file_node = DescribeNode(
                name="test.py", display_name="test.py",
                node_type=NodeType.FILE, nodeid="test.py",
                children=[describe],
            )
            tree = DescribeTree(roots=[file_node])
            reporter = HtmlReporter()
            output = tmp_path / "report.html"
            reporter.generate_report(tree, str(output))
            content = output.read_text()
            assert "&lt;HtmlEscape&gt;" in content
            assert "&lt;angle&gt;" in content

    def describe_outcome_symbols():
        def it_has_all_outcomes():
            for outcome in TestOutcome:
                assert outcome in OUTCOME_SYMBOLS
