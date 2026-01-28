"""Tests for the model module."""

import pytest

from pytest_describe_beautifully.model import (
    DescribeNode,
    DescribeTree,
    NodeType,
    TestOutcome,
    TestResult,
)


def describe_TestResult():
    def it_has_default_values():
        result = TestResult()
        assert result.outcome == TestOutcome.PENDING
        assert result.duration == 0.0
        assert result.longrepr == ""
        assert result.sections == []
        assert result.fixture_names == []

    def it_stores_values():
        result = TestResult(
            outcome=TestOutcome.FAILED,
            duration=1.5,
            longrepr="AssertionError",
            sections=[("stdout", "output")],
            fixture_names=["my_fixture"],
        )
        assert result.outcome == TestOutcome.FAILED
        assert result.duration == 1.5
        assert result.longrepr == "AssertionError"
        assert result.sections == [("stdout", "output")]
        assert result.fixture_names == ["my_fixture"]


def describe_TestOutcome():
    def it_has_all_expected_values():
        assert TestOutcome.PASSED.value == "passed"
        assert TestOutcome.FAILED.value == "failed"
        assert TestOutcome.SKIPPED.value == "skipped"
        assert TestOutcome.XFAILED.value == "xfailed"
        assert TestOutcome.XPASSED.value == "xpassed"
        assert TestOutcome.ERROR.value == "error"
        assert TestOutcome.PENDING.value == "pending"


def describe_NodeType():
    def it_has_all_expected_values():
        assert NodeType.FILE.value == "file"
        assert NodeType.DESCRIBE.value == "describe"
        assert NodeType.TEST.value == "test"


def describe_DescribeNode():
    def it_identifies_test_nodes():
        node = DescribeNode(
            name="it_works",
            display_name="it works",
            node_type=NodeType.TEST,
            nodeid="test::it_works",
        )
        assert node.is_test is True
        assert node.is_describe is False
        assert node.is_file is False

    def it_identifies_describe_nodes():
        node = DescribeNode(
            name="describe_Foo",
            display_name="Foo",
            node_type=NodeType.DESCRIBE,
            nodeid="test::describe_Foo",
        )
        assert node.is_test is False
        assert node.is_describe is True
        assert node.is_file is False

    def it_identifies_file_nodes():
        node = DescribeNode(
            name="test.py",
            display_name="test.py",
            node_type=NodeType.FILE,
            nodeid="test.py",
        )
        assert node.is_test is False
        assert node.is_describe is False
        assert node.is_file is True

    def describe_test_count():
        def it_returns_1_for_test_node():
            node = DescribeNode(
                name="it_works",
                display_name="it works",
                node_type=NodeType.TEST,
                nodeid="x",
            )
            assert node.test_count == 1

        def it_counts_children_recursively():
            child1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
            )
            child2 = DescribeNode(
                name="t2",
                display_name="t2",
                node_type=NodeType.TEST,
                nodeid="t2",
            )
            inner = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[child2],
            )
            parent = DescribeNode(
                name="p",
                display_name="p",
                node_type=NodeType.DESCRIBE,
                nodeid="p",
                children=[child1, inner],
            )
            assert parent.test_count == 2

        def it_returns_0_for_empty_describe():
            node = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
            )
            assert node.test_count == 0

    def describe_passed_count():
        def it_returns_1_for_passed_test():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            assert node.passed_count == 1

        def it_returns_0_for_failed_test():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
                result=TestResult(outcome=TestOutcome.FAILED),
            )
            assert node.passed_count == 0

        def it_returns_0_for_test_without_result():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
            )
            assert node.passed_count == 0

        def it_counts_children():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            c2 = DescribeNode(
                name="t2",
                display_name="t2",
                node_type=NodeType.TEST,
                nodeid="t2",
                result=TestResult(outcome=TestOutcome.FAILED),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1, c2],
            )
            assert parent.passed_count == 1

    def describe_failed_count():
        def it_counts_failed():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
                result=TestResult(outcome=TestOutcome.FAILED),
            )
            assert node.failed_count == 1

        def it_counts_error():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
                result=TestResult(outcome=TestOutcome.ERROR),
            )
            assert node.failed_count == 1

        def it_returns_0_for_passed():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            assert node.failed_count == 0

        def it_returns_0_for_no_result():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
            )
            assert node.failed_count == 0

        def it_counts_children():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(outcome=TestOutcome.FAILED),
            )
            c2 = DescribeNode(
                name="t2",
                display_name="t2",
                node_type=NodeType.TEST,
                nodeid="t2",
                result=TestResult(outcome=TestOutcome.ERROR),
            )
            c3 = DescribeNode(
                name="t3",
                display_name="t3",
                node_type=NodeType.TEST,
                nodeid="t3",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1, c2, c3],
            )
            assert parent.failed_count == 2

    def describe_skipped_count():
        def it_counts_skipped():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
                result=TestResult(outcome=TestOutcome.SKIPPED),
            )
            assert node.skipped_count == 1

        def it_returns_0_for_passed():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            assert node.skipped_count == 0

        def it_returns_0_for_no_result():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
            )
            assert node.skipped_count == 0

    def describe_aggregate_duration():
        def it_returns_duration_for_test():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
                result=TestResult(duration=1.5),
            )
            assert node.aggregate_duration == 1.5

        def it_returns_0_for_test_without_result():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
            )
            assert node.aggregate_duration == 0.0

        def it_sums_children():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(duration=1.0),
            )
            c2 = DescribeNode(
                name="t2",
                display_name="t2",
                node_type=NodeType.TEST,
                nodeid="t2",
                result=TestResult(duration=2.0),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1, c2],
            )
            assert parent.aggregate_duration == 3.0

    def describe_overall_outcome():
        def it_returns_outcome_for_test_with_result():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            assert node.overall_outcome == TestOutcome.PASSED

        def it_returns_pending_for_test_without_result():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="t",
            )
            assert node.overall_outcome == TestOutcome.PENDING

        def it_returns_failed_if_any_child_failed():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            c2 = DescribeNode(
                name="t2",
                display_name="t2",
                node_type=NodeType.TEST,
                nodeid="t2",
                result=TestResult(outcome=TestOutcome.FAILED),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1, c2],
            )
            assert parent.overall_outcome == TestOutcome.FAILED

        def it_returns_failed_if_any_child_has_error():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(outcome=TestOutcome.ERROR),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1],
            )
            assert parent.overall_outcome == TestOutcome.FAILED

        def it_returns_passed_if_all_passed():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            c2 = DescribeNode(
                name="t2",
                display_name="t2",
                node_type=NodeType.TEST,
                nodeid="t2",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1, c2],
            )
            assert parent.overall_outcome == TestOutcome.PASSED

        def it_returns_skipped_if_all_skipped():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(outcome=TestOutcome.SKIPPED),
            )
            c2 = DescribeNode(
                name="t2",
                display_name="t2",
                node_type=NodeType.TEST,
                nodeid="t2",
                result=TestResult(outcome=TestOutcome.SKIPPED),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1, c2],
            )
            assert parent.overall_outcome == TestOutcome.SKIPPED

        def it_returns_passed_for_mix_of_passed_and_skipped():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            c2 = DescribeNode(
                name="t2",
                display_name="t2",
                node_type=NodeType.TEST,
                nodeid="t2",
                result=TestResult(outcome=TestOutcome.SKIPPED),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1, c2],
            )
            assert parent.overall_outcome == TestOutcome.PASSED

        def it_returns_pending_for_empty_describe():
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
            )
            assert parent.overall_outcome == TestOutcome.PENDING

        def it_returns_pending_if_all_pending():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1],
            )
            assert parent.overall_outcome == TestOutcome.PENDING

        def it_returns_xpassed_if_any_xpassed_and_no_failures():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(outcome=TestOutcome.XPASSED),
            )
            c2 = DescribeNode(
                name="t2",
                display_name="t2",
                node_type=NodeType.TEST,
                nodeid="t2",
                result=TestResult(outcome=TestOutcome.PASSED),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1, c2],
            )
            assert parent.overall_outcome == TestOutcome.XPASSED

        def it_returns_passed_for_xfailed():
            c1 = DescribeNode(
                name="t1",
                display_name="t1",
                node_type=NodeType.TEST,
                nodeid="t1",
                result=TestResult(outcome=TestOutcome.XFAILED),
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="d",
                children=[c1],
            )
            assert parent.overall_outcome == TestOutcome.PASSED

    def describe_find_by_nodeid():
        def it_finds_self():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="target",
            )
            assert node.find_by_nodeid("target") is node

        def it_finds_child():
            child = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="child",
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="parent",
                children=[child],
            )
            assert parent.find_by_nodeid("child") is child

        def it_finds_deeply_nested():
            grandchild = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="gc",
            )
            child = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="c",
                children=[grandchild],
            )
            parent = DescribeNode(
                name="d",
                display_name="d",
                node_type=NodeType.DESCRIBE,
                nodeid="p",
                children=[child],
            )
            assert parent.find_by_nodeid("gc") is grandchild

        def it_returns_none_if_not_found():
            node = DescribeNode(
                name="t",
                display_name="t",
                node_type=NodeType.TEST,
                nodeid="x",
            )
            assert node.find_by_nodeid("missing") is None


def describe_DescribeTree():
    def it_has_default_values():
        tree = DescribeTree()
        assert tree.roots == []
        assert tree.slow_threshold == 0.5
        assert tree.total_tests == 0
        assert tree.total_duration == 0.0

    def it_counts_total_tests(sample_tree):
        assert sample_tree.total_tests == 3

    def it_counts_total_passed(sample_tree):
        assert sample_tree.total_passed == 2

    def it_counts_total_failed(sample_tree):
        assert sample_tree.total_failed == 1

    def it_counts_total_skipped(sample_tree):
        assert sample_tree.total_skipped == 0

    def it_calculates_total_duration(sample_tree):
        assert sample_tree.total_duration == pytest.approx(0.006)

    def describe_find_by_nodeid():
        def it_finds_in_roots(sample_tree):
            found = sample_tree.find_by_nodeid("test_math.py")
            assert found is not None
            assert found.name == "test_math.py"

        def it_finds_nested_node(sample_tree):
            found = sample_tree.find_by_nodeid(
                "test_math.py::describe_Calculator::describe_add::it_adds_numbers"
            )
            assert found is not None
            assert found.name == "it_adds_numbers"

        def it_returns_none_for_missing(sample_tree):
            assert sample_tree.find_by_nodeid("nonexistent") is None
