"""Code for pytest-rts plugin logic"""
import os

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser

from pytest_rts.pytest.runner_plugin import RunnerPlugin
from pytest_rts.utils.common import get_existing_tests


def pytest_addoption(parser: Parser) -> None:
    """Register pytest flags"""
    group = parser.getgroup("pytest-rts")
    group.addoption("--rts", action="store_true", default=False, help="Run pytest-rts")
    group.addoption(
        "--rts-coverage-db",
        action="store",
        default="",
        help="Coverage file pytest-rts",
    )


def pytest_configure(config: Config) -> None:
    """Register RTS plugins based on state"""
    if not config.option.rts:
        return

    if not config.option.rts_coverage_db:
        pytest.exit("No coverage file provided", 2)

    if not os.path.exists(config.option.rts_coverage_db):
        pytest.exit("Provided coverage file does not exist", 2)

    existing_tests = get_existing_tests(config.option.rts_coverage_db)
    config.pluginmanager.register(RunnerPlugin(existing_tests))
