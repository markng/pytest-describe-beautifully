"""Data model for the describe tree structure."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class TestOutcome(enum.Enum):
    """Possible outcomes for a test."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    XFAILED = "xfailed"
    XPASSED = "xpassed"
    ERROR = "error"
    PENDING = "pending"


class NodeType(enum.Enum):
    """Type of node in the describe tree."""

    FILE = "file"
    DESCRIBE = "describe"
    TEST = "test"


@dataclass
class TestResult:
    """Result of a single test execution."""

    outcome: TestOutcome = TestOutcome.PENDING
    duration: float = 0.0
    longrepr: str = ""
    sections: list[tuple[str, str]] = field(default_factory=list)
    fixture_names: list[str] = field(default_factory=list)


@dataclass
class DescribeNode:
    """A node in the describe tree (file, describe block, or test)."""

    name: str
    display_name: str
    node_type: NodeType
    nodeid: str
    docstring: str = ""
    children: list[DescribeNode] = field(default_factory=list)
    result: TestResult | None = None

    @property
    def is_test(self) -> bool:
        return self.node_type == NodeType.TEST

    @property
    def is_describe(self) -> bool:
        return self.node_type == NodeType.DESCRIBE

    @property
    def is_file(self) -> bool:
        return self.node_type == NodeType.FILE

    @property
    def test_count(self) -> int:
        if self.is_test:
            return 1
        return sum(child.test_count for child in self.children)

    @property
    def passed_count(self) -> int:
        if self.is_test:
            return 1 if self.result and self.result.outcome == TestOutcome.PASSED else 0
        return sum(child.passed_count for child in self.children)

    @property
    def failed_count(self) -> int:
        if self.is_test:
            if self.result and self.result.outcome in (TestOutcome.FAILED, TestOutcome.ERROR):
                return 1
            return 0
        return sum(child.failed_count for child in self.children)

    @property
    def skipped_count(self) -> int:
        if self.is_test:
            return 1 if self.result and self.result.outcome == TestOutcome.SKIPPED else 0
        return sum(child.skipped_count for child in self.children)

    @property
    def aggregate_duration(self) -> float:
        if self.is_test:
            return self.result.duration if self.result else 0.0
        return sum(child.aggregate_duration for child in self.children)

    @property
    def overall_outcome(self) -> TestOutcome:
        if self.is_test:
            return self.result.outcome if self.result else TestOutcome.PENDING

        outcomes = [child.overall_outcome for child in self.children]
        if not outcomes:
            return TestOutcome.PENDING
        if any(o in (TestOutcome.FAILED, TestOutcome.ERROR) for o in outcomes):
            return TestOutcome.FAILED
        if any(o == TestOutcome.XPASSED for o in outcomes):
            return TestOutcome.XPASSED
        if all(o == TestOutcome.SKIPPED for o in outcomes):
            return TestOutcome.SKIPPED
        if all(o == TestOutcome.PENDING for o in outcomes):
            return TestOutcome.PENDING
        return TestOutcome.PASSED

    def find_by_nodeid(self, nodeid: str) -> DescribeNode | None:
        if self.nodeid == nodeid:
            return self
        for child in self.children:
            found = child.find_by_nodeid(nodeid)
            if found:
                return found
        return None


@dataclass
class DescribeTree:
    """Root container for the describe tree."""

    roots: list[DescribeNode] = field(default_factory=list)
    slow_threshold: float = 0.5

    def find_by_nodeid(self, nodeid: str) -> DescribeNode | None:
        for root in self.roots:
            found = root.find_by_nodeid(nodeid)
            if found:
                return found
        return None

    @property
    def total_tests(self) -> int:
        return sum(root.test_count for root in self.roots)

    @property
    def total_passed(self) -> int:
        return sum(root.passed_count for root in self.roots)

    @property
    def total_failed(self) -> int:
        return sum(root.failed_count for root in self.roots)

    @property
    def total_skipped(self) -> int:
        return sum(root.skipped_count for root in self.roots)

    @property
    def total_duration(self) -> float:
        return sum(root.aggregate_duration for root in self.roots)
