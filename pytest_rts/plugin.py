"""Code for pytest-rts plugin logic"""
import logging
import os

import pytest

from pytest_rts.pytest.init_phase_plugin import InitPhasePlugin
from pytest_rts.pytest.run_phase_plugin import RunPhasePlugin
from pytest_rts.utils.common import (
    DB_FILE_PREFIX,
    get_coverage_file_filename,
    get_existing_tests,
    get_tests_committed,
    get_tests_current,
)
from pytest_rts.utils.git import (
    get_current_head_hash,
    is_git_repo,
    repo_has_commits,
)


def pytest_addoption(parser):
    """Register pytest flags"""
    group = parser.getgroup("pytest-rts")
    group.addoption("--rts", action="store_true", default=False, help="run rts")
    group.addoption(
        "--committed",
        action="store_true",
        default=False,
        help="Check committed changes",
    )


def pytest_configure(config):
    """Register RTS plugins based on state"""
    logger = logging.getLogger()
    logging.basicConfig(format="%(message)s", level=logging.INFO)

    if not config.option.rts:
        return

    if not is_git_repo():
        logger.info(
            "Not a git repository! pytest-rts is disabled. Run git init before using pytest-rts."
        )
        return

    if not repo_has_commits():
        logger.info(
            "No commits yet! pytest-rts is disabled. Create a git commit before using pytest-rts."
        )
        return

    init_required = not os.path.isfile(get_coverage_file_filename())

    if init_required:
        logger.info("No mapping database detected, starting initialization...")
        config.pluginmanager.register(InitPhasePlugin(), "rts-init-plugin")
        return

    workdir_changes = not config.option.committed
    existing_tests = get_existing_tests()

    if workdir_changes:
        logger.info("Checking working directory changes.")
        workdir_tests = get_tests_current()
        config.pluginmanager.register(
            RunPhasePlugin(workdir_tests, existing_tests), "rts-workdir-plugin"
        )
        return

    logger.info("Checking committed changes.")
    previous_hash = get_coverage_file_filename().split(".")[1]
    if previous_hash == get_current_head_hash():
        pytest.exit(0, "Database was initialized at this commit. No changes detected.")

    committed_tests = get_tests_committed(previous_hash)

    config.pluginmanager.register(
        RunPhasePlugin(committed_tests, existing_tests), "rts-committed-plugin"
    )
    return


def pytest_unconfigure(config):
    """Cleanup after pytest run"""
    if config.option.rts:
        if config.pluginmanager.hasplugin("rts-init-plugin"):
            os.rename(".coverage", f"{DB_FILE_PREFIX}.{get_current_head_hash()}")
