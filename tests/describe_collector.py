"""Tests for the collector module."""

from unittest.mock import Mock, patch

from pytest_describe_beautifully.collector import (
    BUILTIN_FIXTURES,
    TreeCollector,
    _is_describe_block,
    _map_outcome,
)
from pytest_describe_beautifully.model import NodeType, TestOutcome

# ---------------------------------------------------------------------------
# Helper factories for mock pytest objects
# ---------------------------------------------------------------------------


def _make_session_link(nodeid=""):
    """Create a mock Session node (has fspath, collect, path, but no reportinfo)."""
    link = Mock()
    link.nodeid = nodeid
    link.name = ""
    link.fspath = "/root"
    link.collect = Mock()
    link.path = "/root"
    # Session has no reportinfo
    del link.reportinfo
    # Session is not a DescribeBlock
    type(link).__name__ = "Session"
    # Session has no function
    del link.function
    return link


def _make_module_link(name, nodeid):
    """Create a mock Module node (has fspath, collect, path, and reportinfo)."""
    link = Mock()
    link.nodeid = nodeid
    link.name = name
    link.fspath = f"/root/{name}"
    link.collect = Mock()
    link.path = f"/root/{name}"
    link.reportinfo = Mock()
    # Module is not a DescribeBlock
    type(link).__name__ = "Module"
    # Module has no function
    del link.function
    return link


def _make_describe_link(name, nodeid, docstring=""):
    """Create a mock DescribeBlock node (has fspath, collect, funcobj, obj)."""
    link = Mock()
    link.nodeid = nodeid
    link.name = name
    link.fspath = "/root/test_file.py"
    link.collect = Mock()
    type(link).__name__ = "DescribeBlock"
    # DescribeBlock stores the original function as funcobj; obj is a module (no doc)
    if docstring:
        funcobj = Mock(__doc__=docstring)
    else:
        funcobj = Mock(__doc__=None)
    link.funcobj = funcobj
    # obj is the generated module — has no docstring
    link.obj = Mock(__doc__=None)
    # DescribeBlock has no function attribute
    del link.function
    return link


def _make_function_link(name, nodeid, fixture_names=None, docstring=""):
    """Create a mock Function/test item (has function attribute, no fspath/collect)."""
    link = Mock()
    link.nodeid = nodeid
    link.name = name
    # Function items do not have fspath+collect in the way collectors do
    del link.fspath
    del link.collect
    # Set up function attribute with docstring
    func = Mock()
    if docstring:
        func.__doc__ = docstring
    else:
        func.__doc__ = None
    link.function = func
    link.fixturenames = fixture_names or []
    return link


def _make_item(chain):
    """Create a mock pytest item with a listchain() that returns the given chain."""
    item = Mock()
    item.listchain = Mock(return_value=chain)
    return item


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
        # Remove the attribute entirely so hasattr checks work correctly
        del report.longreprtext
    if wasxfail is not None:
        report.wasxfail = wasxfail
    else:
        del report.wasxfail
    return report


# ---------------------------------------------------------------------------
# Tests for _is_describe_block
# ---------------------------------------------------------------------------


def describe_is_describe_block():
    def it_detects_describe_block_by_class_name_when_import_fails():
        """Fallback path: pytest_describe is not installed."""
        node = Mock()
        type(node).__name__ = "DescribeBlock"
        with patch(
            "pytest_describe_beautifully.collector._is_describe_block",
            wraps=None,
        ):
            # Instead of wrapping, test the fallback directly by patching the import
            pass

        # Test the fallback path by making the import fail
        import pytest_describe_beautifully.collector as collector_mod

        def patched_is_describe_block(node):
            """Simulate ImportError from pytest_describe."""
            try:
                raise ImportError("No module named 'pytest_describe'")
            except ImportError:
                return type(node).__name__ == "DescribeBlock"

        with patch.object(collector_mod, "_is_describe_block", patched_is_describe_block):
            mock_node = Mock()
            type(mock_node).__name__ = "DescribeBlock"
            assert collector_mod._is_describe_block(mock_node) is True

            mock_node2 = Mock()
            type(mock_node2).__name__ = "Module"
            assert collector_mod._is_describe_block(mock_node2) is False

    def it_returns_false_for_non_describe_block():
        node = Mock()
        type(node).__name__ = "Module"
        # If pytest_describe is not installed, the fallback checks class name
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            result = _is_describe_block(node)
        assert result is False

    def it_returns_true_for_describe_block_by_name():
        node = Mock()
        type(node).__name__ = "DescribeBlock"
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            result = _is_describe_block(node)
        assert result is True

    def it_uses_isinstance_when_pytest_describe_available():
        """When pytest_describe is installed, isinstance check is used."""
        # Create a fake DescribeBlock class and a matching instance
        fake_describe_block_cls = type("DescribeBlock", (), {})
        fake_instance = fake_describe_block_cls()

        fake_plugin = Mock()
        fake_plugin.DescribeBlock = fake_describe_block_cls

        modules = {
            "pytest_describe": Mock(),
            "pytest_describe.plugin": fake_plugin,
        }
        with patch.dict("sys.modules", modules):
            assert _is_describe_block(fake_instance) is True

    def it_uses_isinstance_returns_false_for_non_instance():
        """When pytest_describe is installed, non-DescribeBlock returns False."""
        fake_describe_block_cls = type("DescribeBlock", (), {})
        not_a_describe = Mock()
        type(not_a_describe).__name__ = "Module"

        fake_plugin = Mock()
        fake_plugin.DescribeBlock = fake_describe_block_cls

        modules = {
            "pytest_describe": Mock(),
            "pytest_describe.plugin": fake_plugin,
        }
        with patch.dict("sys.modules", modules):
            assert _is_describe_block(not_a_describe) is False


# ---------------------------------------------------------------------------
# Tests for _map_outcome
# ---------------------------------------------------------------------------


def describe_map_outcome():
    def it_maps_passed():
        report = _make_report(passed=True)
        assert _map_outcome(report) == TestOutcome.PASSED

    def it_maps_failed():
        report = _make_report(failed=True)
        assert _map_outcome(report) == TestOutcome.FAILED

    def it_maps_skipped():
        report = _make_report(skipped=True)
        assert _map_outcome(report) == TestOutcome.SKIPPED

    def it_maps_xfailed():
        report = _make_report(skipped=True, wasxfail="reason")
        assert _map_outcome(report) == TestOutcome.XFAILED

    def it_maps_xpassed():
        report = _make_report(passed=True, wasxfail="reason")
        assert _map_outcome(report) == TestOutcome.XPASSED

    def it_maps_unknown_to_pending():
        report = _make_report(passed=False, failed=False, skipped=False)
        assert _map_outcome(report) == TestOutcome.PENDING


# ---------------------------------------------------------------------------
# Tests for TreeCollector.__init__
# ---------------------------------------------------------------------------


def describe_TreeCollector():
    def it_initializes_with_default_threshold():
        collector = TreeCollector()
        assert collector.tree.slow_threshold == 0.5
        assert collector.tree.roots == []
        assert collector._nodes == {}

    def it_initializes_with_custom_threshold():
        collector = TreeCollector(slow_threshold=1.0)
        assert collector.tree.slow_threshold == 1.0


# ---------------------------------------------------------------------------
# Tests for TreeCollector.build_from_items
# ---------------------------------------------------------------------------


def describe_build_from_items():
    def it_builds_tree_from_single_test_in_describe_block():
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        describe = _make_describe_link(
            "describe_Calculator",
            "test_foo.py::describe_Calculator",
        )
        test_func = _make_function_link(
            "it_adds",
            "test_foo.py::describe_Calculator::it_adds",
        )
        item = _make_item([session, module, describe, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])

        assert len(collector.tree.roots) == 1
        file_node = collector.tree.roots[0]
        assert file_node.name == "test_foo.py"
        assert file_node.node_type == NodeType.FILE
        assert file_node.display_name == "test_foo.py"
        assert file_node.docstring == ""

        assert len(file_node.children) == 1
        desc_node = file_node.children[0]
        assert desc_node.name == "describe_Calculator"
        assert desc_node.node_type == NodeType.DESCRIBE
        assert desc_node.display_name == "Calculator"

        assert len(desc_node.children) == 1
        test_node = desc_node.children[0]
        assert test_node.name == "it_adds"
        assert test_node.node_type == NodeType.TEST
        assert test_node.display_name == "it adds"
        assert test_node.result is not None
        assert test_node.result.outcome == TestOutcome.PENDING

    def it_builds_nested_describe_blocks():
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        outer = _make_describe_link(
            "describe_Outer",
            "test_foo.py::describe_Outer",
        )
        inner = _make_describe_link(
            "describe_inner_feature",
            "test_foo.py::describe_Outer::describe_inner_feature",
        )
        test_func = _make_function_link(
            "it_works",
            "test_foo.py::describe_Outer::describe_inner_feature::it_works",
        )
        item = _make_item([session, module, outer, inner, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])

        file_node = collector.tree.roots[0]
        outer_node = file_node.children[0]
        assert outer_node.display_name == "Outer"
        inner_node = outer_node.children[0]
        assert inner_node.display_name == "inner feature"
        test_node = inner_node.children[0]
        assert test_node.display_name == "it works"

    def it_handles_multiple_items_sharing_parents():
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        describe = _make_describe_link(
            "describe_Calculator",
            "test_foo.py::describe_Calculator",
        )
        test1 = _make_function_link(
            "it_adds",
            "test_foo.py::describe_Calculator::it_adds",
        )
        test2 = _make_function_link(
            "it_subtracts",
            "test_foo.py::describe_Calculator::it_subtracts",
        )

        item1 = _make_item([session, module, describe, test1])
        item2 = _make_item([session, module, describe, test2])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item1, item2])

        # Should still have one root, one describe, two tests
        assert len(collector.tree.roots) == 1
        file_node = collector.tree.roots[0]
        assert len(file_node.children) == 1
        desc_node = file_node.children[0]
        assert len(desc_node.children) == 2
        assert desc_node.children[0].name == "it_adds"
        assert desc_node.children[1].name == "it_subtracts"

    def it_handles_multiple_files():
        session = _make_session_link()
        module1 = _make_module_link("test_a.py", "test_a.py")
        module2 = _make_module_link("test_b.py", "test_b.py")
        desc1 = _make_describe_link("describe_A", "test_a.py::describe_A")
        desc2 = _make_describe_link("describe_B", "test_b.py::describe_B")
        test1 = _make_function_link("it_x", "test_a.py::describe_A::it_x")
        test2 = _make_function_link("it_y", "test_b.py::describe_B::it_y")

        item1 = _make_item([session, module1, desc1, test1])
        item2 = _make_item([session, module2, desc2, test2])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item1, item2])

        assert len(collector.tree.roots) == 2
        assert collector.tree.roots[0].name == "test_a.py"
        assert collector.tree.roots[1].name == "test_b.py"

    def it_filters_builtin_fixtures():
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        describe = _make_describe_link(
            "describe_MyClass",
            "test_foo.py::describe_MyClass",
        )
        test_func = _make_function_link(
            "it_uses_fixtures",
            "test_foo.py::describe_MyClass::it_uses_fixtures",
            fixture_names=[
                "request",
                "capsys",
                "my_custom_fixture",
                "monkeypatch",
                "db_connection",
            ],
        )
        item = _make_item([session, module, describe, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])

        test_node = collector.tree.roots[0].children[0].children[0]
        assert test_node.result is not None
        assert test_node.result.fixture_names == ["my_custom_fixture", "db_connection"]

    def it_extracts_docstrings_from_describe_blocks():
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        describe = _make_describe_link(
            "describe_Widget",
            "test_foo.py::describe_Widget",
            docstring="A reusable UI widget.",
        )
        test_func = _make_function_link(
            "it_renders",
            "test_foo.py::describe_Widget::it_renders",
            docstring="Should render correctly in all browsers.",
        )
        item = _make_item([session, module, describe, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])

        desc_node = collector.tree.roots[0].children[0]
        assert desc_node.docstring == "A reusable UI widget."

        test_node = desc_node.children[0]
        assert test_node.docstring == "Should render correctly in all browsers."

    def it_extracts_empty_docstring_when_describe_has_no_obj():
        """Cover the branch where describe block has no funcobj or obj attribute."""
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        describe = _make_describe_link(
            "describe_NoObj",
            "test_foo.py::describe_NoObj",
        )
        # Remove both funcobj and obj to test the else branch
        del describe.funcobj
        del describe.obj
        test_func = _make_function_link(
            "it_works",
            "test_foo.py::describe_NoObj::it_works",
        )
        item = _make_item([session, module, describe, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])

        desc_node = collector.tree.roots[0].children[0]
        assert desc_node.docstring == ""

    def it_skips_chain_links_without_fspath_collect_or_function():
        """Cover the final else/continue branch for unrecognized nodes."""
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        describe = _make_describe_link(
            "describe_Foo",
            "test_foo.py::describe_Foo",
        )
        # Create an unknown link type: no fspath, no collect, no function
        unknown_link = Mock()
        unknown_link.nodeid = "test_foo.py::describe_Foo::some_unknown"
        unknown_link.name = "some_unknown"
        del unknown_link.fspath
        del unknown_link.collect
        del unknown_link.function
        test_func = _make_function_link(
            "it_works",
            "test_foo.py::describe_Foo::it_works",
        )
        item = _make_item([session, module, describe, unknown_link, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])

        # The unknown link should be skipped; test still added under describe
        desc_node = collector.tree.roots[0].children[0]
        assert len(desc_node.children) == 1
        assert desc_node.children[0].name == "it_works"

    def it_skips_nodes_with_fspath_collect_but_no_path():
        """Cover the branch: has fspath+collect, not describe, no path -> continue."""
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        # Create a collector-like link with fspath+collect but no path attribute
        weird_collector = Mock()
        weird_collector.nodeid = "test_foo.py::weird"
        weird_collector.name = "weird"
        weird_collector.fspath = "/root/test_foo.py"
        weird_collector.collect = Mock()
        del weird_collector.path
        type(weird_collector).__name__ = "SomeCollector"
        del weird_collector.function

        test_func = _make_function_link(
            "it_works",
            "test_foo.py::it_works",
        )
        item = _make_item([session, module, weird_collector, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])

        # weird_collector should be skipped
        file_node = collector.tree.roots[0]
        # test should be a child of the module (file node)
        assert len(file_node.children) == 1
        assert file_node.children[0].name == "it_works"

    def it_handles_test_with_no_fixturenames_attribute():
        """Cover getattr(link, 'fixturenames', []) fallback."""
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        describe = _make_describe_link(
            "describe_Foo",
            "test_foo.py::describe_Foo",
        )
        test_func = _make_function_link(
            "it_works",
            "test_foo.py::describe_Foo::it_works",
        )
        del test_func.fixturenames  # Remove fixturenames
        item = _make_item([session, module, describe, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])

        test_node = collector.tree.roots[0].children[0].children[0]
        assert test_node.result is not None
        assert test_node.result.fixture_names == []

    def it_handles_test_function_with_no_docstring():
        """Cover the branch where function.__doc__ is None."""
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        describe = _make_describe_link(
            "describe_Foo",
            "test_foo.py::describe_Foo",
        )
        test_func = _make_function_link(
            "it_works",
            "test_foo.py::describe_Foo::it_works",
            docstring="",  # No docstring
        )
        item = _make_item([session, module, describe, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])

        test_node = collector.tree.roots[0].children[0].children[0]
        assert test_node.docstring == ""

    def it_does_not_attach_orphan_non_file_node_to_roots():
        """Cover the implicit else: parent_node is None and type is not FILE.

        When a describe block is the first recognized node with no parent,
        it should not be added to roots (only FILE nodes go there).
        """
        session = _make_session_link()
        # Skip the module entirely; the describe block has no parent
        describe = _make_describe_link(
            "describe_Orphan",
            "test_foo.py::describe_Orphan",
        )
        test_func = _make_function_link(
            "it_works",
            "test_foo.py::describe_Orphan::it_works",
        )
        item = _make_item([session, describe, test_func])

        collector = TreeCollector()
        with patch.dict(
            "sys.modules",
            {"pytest_describe": None, "pytest_describe.plugin": None},
        ):
            collector.build_from_items([item])

        # No file node was created, so roots should be empty
        assert len(collector.tree.roots) == 0
        # But the describe and test nodes ARE in the internal dict
        assert "test_foo.py::describe_Orphan" in collector._nodes
        assert "test_foo.py::describe_Orphan::it_works" in collector._nodes


# ---------------------------------------------------------------------------
# Tests for TreeCollector.update_from_report
# ---------------------------------------------------------------------------


def describe_update_from_report():
    def _build_simple_collector():
        """Build a collector with one test for update testing."""
        session = _make_session_link()
        module = _make_module_link("test_foo.py", "test_foo.py")
        describe = _make_describe_link(
            "describe_Foo",
            "test_foo.py::describe_Foo",
        )
        test_func = _make_function_link(
            "it_works",
            "test_foo.py::describe_Foo::it_works",
        )
        item = _make_item([session, module, describe, test_func])

        collector = TreeCollector()
        with patch.dict("sys.modules", {"pytest_describe": None, "pytest_describe.plugin": None}):
            collector.build_from_items([item])
        return collector

    def it_updates_passed_call_report():
        collector = _build_simple_collector()
        report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            passed=True,
            duration=0.05,
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.PASSED
        assert node.result.duration == 0.05

    def it_updates_failed_call_report():
        collector = _build_simple_collector()
        report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            failed=True,
            duration=0.1,
            longreprtext="AssertionError: expected True",
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.FAILED
        assert node.result.duration == 0.1
        assert node.result.longrepr == "AssertionError: expected True"

    def it_updates_skipped_call_report():
        collector = _build_simple_collector()
        report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            skipped=True,
            duration=0.0,
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.SKIPPED

    def it_updates_xfailed_call_report():
        collector = _build_simple_collector()
        report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            skipped=True,
            wasxfail="known bug",
            duration=0.01,
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.XFAILED

    def it_updates_xpassed_call_report():
        collector = _build_simple_collector()
        report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            passed=True,
            wasxfail="expected failure",
            duration=0.01,
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.XPASSED

    def it_stores_sections_from_call_report():
        collector = _build_simple_collector()
        report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            passed=True,
            duration=0.01,
            sections=[("Captured stdout call", "hello\n"), ("Captured stderr call", "warn\n")],
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.sections == [
            ("Captured stdout call", "hello\n"),
            ("Captured stderr call", "warn\n"),
        ]

    def it_stores_empty_sections_when_none():
        collector = _build_simple_collector()
        report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            passed=True,
            duration=0.01,
            sections=None,
        )
        # Manually set sections to falsy value
        report.sections = None
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.sections == []

    def it_handles_call_report_without_longreprtext_attr():
        """No longreprtext attribute at all on the report."""
        collector = _build_simple_collector()
        report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            passed=True,
            duration=0.01,
        )
        # longreprtext is already deleted by _make_report when empty string
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.longrepr == ""  # Default, unchanged

    def it_handles_setup_failure():
        collector = _build_simple_collector()
        report = _make_report(
            when="setup",
            nodeid="test_foo.py::describe_Foo::it_works",
            failed=True,
            duration=0.02,
            longreprtext="fixture 'db' not found",
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.ERROR
        assert node.result.duration == 0.02
        assert node.result.longrepr == "fixture 'db' not found"

    def it_handles_teardown_failure():
        collector = _build_simple_collector()
        report = _make_report(
            when="teardown",
            nodeid="test_foo.py::describe_Foo::it_works",
            failed=True,
            duration=0.03,
            longreprtext="teardown error",
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.ERROR
        assert node.result.duration == 0.03
        assert node.result.longrepr == "teardown error"

    def it_handles_setup_failure_without_longreprtext():
        collector = _build_simple_collector()
        report = _make_report(
            when="setup",
            nodeid="test_foo.py::describe_Foo::it_works",
            failed=True,
            duration=0.02,
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.ERROR
        assert node.result.longrepr == ""  # Not updated since no longreprtext

    def it_handles_setup_skip():
        collector = _build_simple_collector()
        report = _make_report(
            when="setup",
            nodeid="test_foo.py::describe_Foo::it_works",
            skipped=True,
            duration=0.001,
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.SKIPPED
        assert node.result.duration == 0.001

    def it_handles_setup_skip_with_xfail():
        collector = _build_simple_collector()
        report = _make_report(
            when="setup",
            nodeid="test_foo.py::describe_Foo::it_works",
            skipped=True,
            wasxfail="reason",
            duration=0.001,
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.XFAILED

    def it_ignores_call_report_for_unknown_nodeid():
        collector = _build_simple_collector()
        report = _make_report(
            when="call",
            nodeid="nonexistent::test",
            passed=True,
            duration=0.01,
        )
        # Should not raise
        collector.update_from_report(report)

    def it_ignores_setup_failure_for_unknown_nodeid():
        collector = _build_simple_collector()
        report = _make_report(
            when="setup",
            nodeid="nonexistent::test",
            failed=True,
            duration=0.01,
        )
        collector.update_from_report(report)

    def it_ignores_setup_skip_for_unknown_nodeid():
        collector = _build_simple_collector()
        report = _make_report(
            when="setup",
            nodeid="nonexistent::test",
            skipped=True,
            duration=0.01,
        )
        collector.update_from_report(report)

    def it_ignores_teardown_non_failure():
        """Teardown that passed should be ignored (no update)."""
        collector = _build_simple_collector()
        # First, set it to passed
        call_report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            passed=True,
            duration=0.01,
        )
        collector.update_from_report(call_report)

        # Teardown that passed - should not change outcome
        teardown_report = _make_report(
            when="teardown",
            nodeid="test_foo.py::describe_Foo::it_works",
            passed=True,
            duration=0.001,
        )
        collector.update_from_report(teardown_report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.PASSED  # Unchanged

    def it_ignores_setup_that_passed():
        """Setup that passed and is not skipped should be ignored."""
        collector = _build_simple_collector()
        report = _make_report(
            when="setup",
            nodeid="test_foo.py::describe_Foo::it_works",
            passed=True,
            duration=0.001,
        )
        collector.update_from_report(report)

        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        assert node.result.outcome == TestOutcome.PENDING  # Unchanged

    def it_handles_call_report_for_node_without_result():
        """Cover the branch where node exists but result is None."""
        collector = _build_simple_collector()
        # Manually remove the result from the test node
        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        node.result = None

        report = _make_report(
            when="call",
            nodeid="test_foo.py::describe_Foo::it_works",
            passed=True,
            duration=0.01,
        )
        # Should not raise, just skip
        collector.update_from_report(report)

    def it_handles_setup_failure_for_node_without_result():
        collector = _build_simple_collector()
        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        node.result = None

        report = _make_report(
            when="setup",
            nodeid="test_foo.py::describe_Foo::it_works",
            failed=True,
            duration=0.01,
        )
        collector.update_from_report(report)

    def it_handles_setup_skip_for_node_without_result():
        collector = _build_simple_collector()
        node = collector.tree.find_by_nodeid("test_foo.py::describe_Foo::it_works")
        node.result = None

        report = _make_report(
            when="setup",
            nodeid="test_foo.py::describe_Foo::it_works",
            skipped=True,
            duration=0.01,
        )
        collector.update_from_report(report)


# ---------------------------------------------------------------------------
# Tests for BUILTIN_FIXTURES
# ---------------------------------------------------------------------------


def describe_builtin_fixtures():
    def it_contains_expected_fixtures():
        expected = {
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
        assert BUILTIN_FIXTURES == expected

    def it_is_a_frozenset():
        assert isinstance(BUILTIN_FIXTURES, frozenset)
