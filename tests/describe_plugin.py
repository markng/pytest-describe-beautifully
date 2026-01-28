"""Tests for the plugin entry point."""

from __future__ import annotations

import importlib
from unittest.mock import Mock

import pytest_describe_beautifully
import pytest_describe_beautifully.plugin as _plugin_mod

# Reload the modules so coverage can track their module-level lines
# (they are pre-imported by pytest before coverage starts)
importlib.reload(pytest_describe_beautifully)
importlib.reload(_plugin_mod)

from pytest_describe_beautifully.plugin import (  # noqa: E402
    _should_activate,
    pytest_addoption,
    pytest_configure,
    pytest_sessionfinish,
    pytest_terminal_summary,
    pytest_unconfigure,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    describe_beautifully=False,
    describe_slow=0.5,
    describe_html=None,
):
    """Create a mock config with the given options."""
    config = Mock()
    tw = Mock()
    config.get_terminal_writer.return_value = tw

    def getoption(name, default=None):
        options = {
            "describe_beautifully": describe_beautifully,
            "describe_slow": describe_slow,
            "describe_expand_all": False,
            "describe_no_fixtures": False,
            "describe_html": describe_html,
        }
        return options.get(name, default)

    config.getoption = getoption
    return config, tw


# ---------------------------------------------------------------------------
# Tests for _should_activate
# ---------------------------------------------------------------------------


def describe_should_activate():
    def it_returns_true_when_describe_beautifully_is_set():
        config, _ = _make_config(describe_beautifully=True)
        assert _should_activate(config) is True

    def it_returns_false_when_not_set():
        config, _ = _make_config(describe_beautifully=False)
        assert _should_activate(config) is False


# ---------------------------------------------------------------------------
# Tests for pytest_addoption
# ---------------------------------------------------------------------------


def describe_pytest_addoption():
    def it_registers_all_options():
        parser = Mock()
        group = Mock()
        parser.getgroup.return_value = group

        pytest_addoption(parser)

        parser.getgroup.assert_called_once_with("describe-beautifully", "Beautiful describe output")
        # Should register 5 options
        assert group.addoption.call_count == 5

        # Extract all option names
        option_names = []
        for call in group.addoption.call_args_list:
            option_names.extend(arg for arg in call[0] if arg.startswith("--"))
        assert "--describe-beautifully" in option_names
        assert "--db" in option_names
        assert "--describe-slow" in option_names
        assert "--describe-expand-all" in option_names
        assert "--describe-no-fixtures" in option_names
        assert "--describe-html" in option_names


# ---------------------------------------------------------------------------
# Tests for pytest_configure
# ---------------------------------------------------------------------------


def describe_pytest_configure():
    def it_registers_reporter_when_activated():
        config, _ = _make_config(describe_beautifully=True)
        pytest_configure(config)
        config.pluginmanager.register.assert_called_once()
        name = config.pluginmanager.register.call_args[0][1]
        assert name == "describe-beautifully-reporter"

    def it_does_not_register_when_not_activated():
        config, _ = _make_config(describe_beautifully=False)
        pytest_configure(config)
        config.pluginmanager.register.assert_not_called()

    def it_sets_up_html_reporter_when_path_given():
        config, _ = _make_config(describe_beautifully=True, describe_html="/tmp/report.html")
        pytest_configure(config)
        assert config._describe_html_path == "/tmp/report.html"
        assert config._describe_html_reporter is not None

    def it_does_not_set_up_html_when_no_path():
        config, _ = _make_config(describe_beautifully=True)
        # Ensure _describe_html_path is not set before calling configure
        del config._describe_html_path
        del config._describe_html_reporter
        pytest_configure(config)
        # Should not have set the html attributes
        assert not hasattr(config, "_describe_html_path")


# ---------------------------------------------------------------------------
# Tests for pytest_unconfigure
# ---------------------------------------------------------------------------


def describe_pytest_unconfigure():
    def it_unregisters_reporter_if_present():
        config = Mock()
        reporter = Mock()
        config.pluginmanager.get_plugin.return_value = reporter
        pytest_unconfigure(config)
        config.pluginmanager.get_plugin.assert_called_once_with("describe-beautifully-reporter")
        config.pluginmanager.unregister.assert_called_once_with(reporter)

    def it_does_nothing_if_no_reporter():
        config = Mock()
        config.pluginmanager.get_plugin.return_value = None
        pytest_unconfigure(config)
        config.pluginmanager.unregister.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for pytest_sessionfinish
# ---------------------------------------------------------------------------


def describe_pytest_sessionfinish():
    def it_generates_html_report_when_configured():
        config = Mock()
        config._describe_html_path = "/tmp/report.html"
        config._describe_html_reporter = Mock()
        reporter = Mock()
        config.pluginmanager.get_plugin.return_value = reporter

        session = Mock()
        session.config = config

        pytest_sessionfinish(session)

        config._describe_html_reporter.generate_report.assert_called_once_with(
            reporter.collector.tree, "/tmp/report.html"
        )

    def it_skips_when_no_html_path():
        config = Mock(spec=[])
        session = Mock()
        session.config = config
        pytest_sessionfinish(session)
        # No error, no report generated

    def it_skips_when_no_html_reporter():
        config = Mock(spec=[])
        config._describe_html_path = "/tmp/report.html"
        session = Mock()
        session.config = config
        pytest_sessionfinish(session)

    def it_skips_when_no_terminal_reporter_plugin():
        config = Mock()
        config._describe_html_path = "/tmp/report.html"
        config._describe_html_reporter = Mock()
        config.pluginmanager.get_plugin.return_value = None

        session = Mock()
        session.config = config

        pytest_sessionfinish(session)
        config._describe_html_reporter.generate_report.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for pytest_terminal_summary
# ---------------------------------------------------------------------------


def describe_pytest_terminal_summary():
    def it_prints_html_path_when_configured():
        config = Mock()
        tw = Mock()
        config.get_terminal_writer.return_value = tw
        config._describe_html_path = "/tmp/report.html"

        terminalreporter = Mock()
        terminalreporter.config = config

        pytest_terminal_summary(terminalreporter)

        calls = tw.line.call_args_list
        assert any("HTML report generated: /tmp/report.html" in str(c) for c in calls)

    def it_does_nothing_when_no_html_path():
        config = Mock(spec=[])
        terminalreporter = Mock()
        terminalreporter.config = config

        pytest_terminal_summary(terminalreporter)
        # No error, no output


# ---------------------------------------------------------------------------
# Integration tests via pytester
# ---------------------------------------------------------------------------


def describe_pytester_plugin_integration():
    def it_activates_with_describe_beautifully_flag(pytester):
        pytester.makeini(
            """
            [pytest]
            describe_prefixes = describe_
            python_files = test_*.py
            python_functions = it_* they_*
            """
        )
        pytester.makepyfile(
            test_simple="""
            def describe_Simple():
                def it_works():
                    assert True
            """
        )
        result = pytester.runpytest("--describe-beautifully", "-p", "no:cov")
        result.stdout.fnmatch_lines(["*Simple*", "*\u2713 it works*"])

    def it_activates_with_db_flag(pytester):
        pytester.makeini(
            """
            [pytest]
            describe_prefixes = describe_
            python_files = test_*.py
            python_functions = it_* they_*
            """
        )
        pytester.makepyfile(
            test_db="""
            def describe_DbAlias():
                def it_works():
                    assert True
            """
        )
        result = pytester.runpytest("--db", "-p", "no:cov")
        result.stdout.fnmatch_lines(["*DbAlias*", "*\u2713 it works*"])

    def it_does_not_activate_without_flag(pytester):
        pytester.makeini(
            """
            [pytest]
            describe_prefixes = describe_
            python_files = test_*.py
            python_functions = it_* they_*
            """
        )
        pytester.makepyfile(
            test_noactivate="""
            def describe_NoActivate():
                def it_works():
                    assert True
            """
        )
        result = pytester.runpytest("-p", "no:cov")
        # Without the flag, the beautiful reporter should not be active
        # Standard output shows dots, not check marks
        result.stdout.no_fnmatch_line("*\u2713 it works*")

    def it_generates_html_report(pytester):
        pytester.makeini(
            """
            [pytest]
            describe_prefixes = describe_
            python_files = test_*.py
            python_functions = it_* they_*
            """
        )
        pytester.makepyfile(
            test_html="""
            def describe_HtmlTest():
                def it_generates_report():
                    assert True
            """
        )
        html_path = str(pytester.path / "report.html")
        result = pytester.runpytest(
            "--describe-beautifully",
            f"--describe-html={html_path}",
            "-p",
            "no:cov",
        )
        result.stdout.fnmatch_lines(["*HTML report generated*"])
        assert (pytester.path / "report.html").exists()
        content = (pytester.path / "report.html").read_text()
        assert "<!DOCTYPE html>" in content
        assert "1 tests" in content
        assert "1 passed" in content

    def it_all_cli_options_accepted(pytester):
        pytester.makeini(
            """
            [pytest]
            describe_prefixes = describe_
            python_files = test_*.py
            python_functions = it_* they_*
            """
        )
        pytester.makepyfile(
            test_opts="""
            def describe_Opts():
                def it_works():
                    assert True
            """
        )
        result = pytester.runpytest(
            "--describe-beautifully",
            "--describe-slow=1.0",
            "--describe-expand-all",
            "--describe-no-fixtures",
            "-p",
            "no:cov",
        )
        assert result.ret == 0
