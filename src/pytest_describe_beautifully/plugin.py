"""Pytest plugin entry point for pytest-describe-beautifully."""

from __future__ import annotations


def pytest_addoption(parser) -> None:
    """Register command-line options for the plugin."""
    group = parser.getgroup("describe-beautifully", "Beautiful describe output")
    group.addoption(
        "--describe-beautifully",
        "--db",
        action="store_true",
        default=False,
        help="Enable beautiful terminal output for pytest-describe.",
    )
    group.addoption(
        "--describe-slow",
        type=float,
        default=0.5,
        help="Threshold in seconds for marking a test as slow (default: 0.5).",
    )
    group.addoption(
        "--describe-expand-all",
        action="store_true",
        default=False,
        help="Show docstrings and fixtures in the output.",
    )
    group.addoption(
        "--describe-no-fixtures",
        action="store_true",
        default=False,
        help="Hide fixture display in expanded mode.",
    )
    group.addoption(
        "--describe-html",
        default=None,
        help="Path to generate an HTML test report.",
    )


def _should_activate(config) -> bool:
    """Check if the plugin should activate."""
    return config.getoption("describe_beautifully", default=False)


def pytest_configure(config) -> None:
    """Register the terminal reporter and HTML reporter if activated."""
    if not _should_activate(config):
        return

    from pytest_describe_beautifully.terminal_reporter import (
        BeautifulTerminalReporter,
    )

    reporter = BeautifulTerminalReporter(config)
    config.pluginmanager.register(reporter, "describe-beautifully-reporter")

    html_path = config.getoption("describe_html", default=None)
    if html_path:
        from pytest_describe_beautifully.html_reporter import HtmlReporter

        slow = config.getoption("describe_slow", default=0.5)
        html_reporter = HtmlReporter(slow_threshold=slow)
        config._describe_html_path = html_path
        config._describe_html_reporter = html_reporter


def pytest_unconfigure(config) -> None:
    """Unregister the reporter on cleanup."""
    reporter = config.pluginmanager.get_plugin("describe-beautifully-reporter")
    if reporter is not None:
        config.pluginmanager.unregister(reporter)


def pytest_sessionfinish(session) -> None:
    """Generate the HTML report at the end of the session."""
    config = session.config
    html_path = getattr(config, "_describe_html_path", None)
    html_reporter = getattr(config, "_describe_html_reporter", None)
    if html_path and html_reporter:
        reporter = config.pluginmanager.get_plugin("describe-beautifully-reporter")
        if reporter is not None:
            html_reporter.generate_report(reporter.collector.tree, html_path)


def pytest_terminal_summary(terminalreporter) -> None:
    """Print the path to the HTML report at the end of output."""
    config = terminalreporter.config
    html_path = getattr(config, "_describe_html_path", None)
    if html_path:
        tw = config.get_terminal_writer()
        tw.line()
        tw.line(f"HTML report generated: {html_path}", bold=True)
