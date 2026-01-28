"""Builds a DescribeTree from pytest items and reports."""

from __future__ import annotations

import inspect

from pytest_describe_beautifully.model import (
    DescribeNode,
    DescribeTree,
    NodeType,
    TestOutcome,
    TestResult,
)
from pytest_describe_beautifully.naming import humanize_describe_name, humanize_test_name

# Builtin fixtures that should be filtered out from display
BUILTIN_FIXTURES = frozenset(
    {
        "request",
        "pytestconfig",
        "tmp_path",
        "tmp_path_factory",
        "capsys",
        "capfd",
        "capsysbinary",
        "capfdbinary",
        "caplog",
        "monkeypatch",
        "recwarn",
        "doctest_namespace",
        "cache",
        "record_property",
        "record_testsuite_property",
        "record_xml_attribute",
        "pytester",
        "testdir",
    }
)


def _is_describe_block(node) -> bool:
    """Check if a pytest node is a describe block."""
    try:
        from pytest_describe.plugin import DescribeBlock

        return isinstance(node, DescribeBlock)
    except ImportError:
        return type(node).__name__ == "DescribeBlock"


class TreeCollector:
    """Collects pytest items and reports into a DescribeTree."""

    def __init__(self, slow_threshold: float = 0.5) -> None:
        self.tree = DescribeTree(slow_threshold=slow_threshold)
        self._nodes: dict[str, DescribeNode] = {}

    def build_from_items(self, items: list) -> None:
        """Build tree structure from collected pytest items."""
        for item in items:
            chain = item.listchain()
            # chain is [Session, Module, (DescribeBlock...), Function]
            parent_node = None
            for link in chain:
                nodeid = link.nodeid
                if nodeid in self._nodes:
                    parent_node = self._nodes[nodeid]
                    continue

                result = self._classify_link(link)
                if result is None:
                    continue

                node_type, display_name, docstring, fixture_names = result

                node = DescribeNode(
                    name=link.name,
                    display_name=display_name,
                    docstring=docstring,
                    node_type=node_type,
                    nodeid=nodeid,
                )

                if node_type == NodeType.TEST:
                    node.result = TestResult(fixture_names=fixture_names)

                self._nodes[nodeid] = node

                if parent_node is not None:
                    parent_node.children.append(node)
                elif node_type == NodeType.FILE:
                    self.tree.roots.append(node)

                parent_node = node

    @staticmethod
    def _classify_link(link):
        """Classify a chain link and return (node_type, display_name, docstring, fixture_names).

        Returns None if the link should be skipped.
        """
        fixture_names: list[str] = []

        if hasattr(link, "fspath") and hasattr(link, "collect"):
            if _is_describe_block(link):
                node_type = NodeType.DESCRIBE
                display_name = humanize_describe_name(link.name)
                # DescribeBlock.obj is a module; the docstring lives on funcobj
                doc_src = getattr(link, "funcobj", None) or getattr(link, "obj", None)
                docstring = (inspect.getdoc(doc_src) or "") if doc_src else ""
            elif hasattr(link, "path") and not hasattr(link, "reportinfo"):
                # Skip Session node
                return None
            elif hasattr(link, "path"):
                # Module node
                node_type = NodeType.FILE
                display_name = link.name
                docstring = ""
            else:
                return None
        elif hasattr(link, "function"):
            # Function/test item
            node_type = NodeType.TEST
            display_name = humanize_test_name(link.name)
            docstring = inspect.getdoc(link.function) or ""
            fixture_names = [
                f for f in getattr(link, "fixturenames", []) if f not in BUILTIN_FIXTURES
            ]
        else:
            return None

        return node_type, display_name, docstring, fixture_names

    def update_from_report(self, report) -> None:
        """Update tree with test report results."""
        if report.when == "call":
            node = self.tree.find_by_nodeid(report.nodeid)
            if node and node.result:
                node.result.outcome = _map_outcome(report)
                node.result.duration = report.duration
                if hasattr(report, "longreprtext") and report.longreprtext:
                    node.result.longrepr = report.longreprtext
                node.result.sections = list(report.sections) if report.sections else []
        elif report.when in ("setup", "teardown") and report.failed:
            node = self.tree.find_by_nodeid(report.nodeid)
            if node and node.result:
                node.result.outcome = TestOutcome.ERROR
                node.result.duration = report.duration
                if hasattr(report, "longreprtext") and report.longreprtext:
                    node.result.longrepr = report.longreprtext
        elif report.when == "setup" and report.skipped:
            node = self.tree.find_by_nodeid(report.nodeid)
            if node and node.result:
                node.result.outcome = _map_outcome(report)
                node.result.duration = report.duration


def _map_outcome(report) -> TestOutcome:
    """Convert a pytest report to a TestOutcome."""
    if hasattr(report, "wasxfail"):
        if report.passed:
            return TestOutcome.XPASSED
        return TestOutcome.XFAILED
    if report.passed:
        return TestOutcome.PASSED
    if report.failed:
        return TestOutcome.FAILED
    if report.skipped:
        return TestOutcome.SKIPPED
    return TestOutcome.PENDING
