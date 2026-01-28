"""Shared fixtures for pytest-describe-beautifully tests."""

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
def sample_tree():
    """Create a sample DescribeTree for testing."""
    from pytest_describe_beautifully.model import (
        DescribeNode,
        DescribeTree,
        NodeType,
        TestOutcome,
        TestResult,
    )

    # Build a sample tree: File > Describe > Tests
    test1 = DescribeNode(
        name="it_adds_numbers",
        display_name="it adds numbers",
        node_type=NodeType.TEST,
        nodeid="test_math.py::describe_Calculator::describe_add::it_adds_numbers",
        result=TestResult(outcome=TestOutcome.PASSED, duration=0.002),
    )
    test2 = DescribeNode(
        name="it_handles_negatives",
        display_name="it handles negatives",
        node_type=NodeType.TEST,
        nodeid="test_math.py::describe_Calculator::describe_add::it_handles_negatives",
        result=TestResult(outcome=TestOutcome.PASSED, duration=0.001),
    )
    test3 = DescribeNode(
        name="it_raises_on_zero",
        display_name="it raises on zero",
        node_type=NodeType.TEST,
        nodeid="test_math.py::describe_Calculator::describe_divide::it_raises_on_zero",
        result=TestResult(outcome=TestOutcome.FAILED, duration=0.003, longrepr="ZeroDivisionError"),
    )

    add_block = DescribeNode(
        name="describe_add",
        display_name="add",
        docstring="Addition operations.",
        node_type=NodeType.DESCRIBE,
        nodeid="test_math.py::describe_Calculator::describe_add",
        children=[test1, test2],
    )
    divide_block = DescribeNode(
        name="describe_divide",
        display_name="divide",
        node_type=NodeType.DESCRIBE,
        nodeid="test_math.py::describe_Calculator::describe_divide",
        children=[test3],
    )
    calculator_block = DescribeNode(
        name="describe_Calculator",
        display_name="Calculator",
        node_type=NodeType.DESCRIBE,
        nodeid="test_math.py::describe_Calculator",
        children=[add_block, divide_block],
    )
    file_node = DescribeNode(
        name="test_math.py",
        display_name="test_math.py",
        node_type=NodeType.FILE,
        nodeid="test_math.py",
        children=[calculator_block],
    )

    return DescribeTree(roots=[file_node])
