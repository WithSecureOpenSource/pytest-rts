"""Code for pytest-rts plugin logic"""
import logging
import os
import sqlite3
import pytest
from pytest_rts.pytest.init_phase_plugin import InitPhasePlugin
from pytest_rts.pytest.normal_phase_plugin import NormalPhasePlugin
from pytest_rts.pytest.update_phase_plugin import UpdatePhasePlugin
from pytest_rts.utils.git import get_current_head_hash
from pytest_rts.utils.selection import (
    get_tests_and_data_committed,
    get_tests_and_data_current,
)
from pytest_rts.utils.mappinghelper import MappingHelper
from pytest_rts.utils.testgetter import TestGetter

DB_FILE_NAME = "mapping.db"
INIT_REQUIRED = not os.path.isfile(DB_FILE_NAME)
CONN = None
MAPPING_HELPER = None
TEST_GETTER = None


def pytest_addoption(parser):
    """Register pytest flags"""
    parser.addoption("--rts", action="store_true", default=False, help="run rts")


def pytest_configure(config):
    """Register RTS plugins based on state"""
    logger = logging.getLogger()
    logging.basicConfig(format="%(message)s", level=logging.INFO)

    if config.option.rts:
        global CONN, MAPPING_HELPER, TEST_GETTER  # pylint: disable=global-statement
        CONN = sqlite3.connect(DB_FILE_NAME)
        MAPPING_HELPER = MappingHelper(CONN)
        TEST_GETTER = TestGetter(CONN)

        if INIT_REQUIRED:
            logger.info("No mapping database detected, starting initialization...")
            config.pluginmanager.register(
                InitPhasePlugin(MAPPING_HELPER), "rts-init-plugin"
            )
            return

        workdir_data = get_tests_and_data_current(MAPPING_HELPER, TEST_GETTER)

        logger.info("WORKING DIRECTORY CHANGES")
        logger.info(
            "Found %s changed test files", workdir_data.changed_testfiles_amount
        )
        logger.info("Found %s changed src files", workdir_data.changed_srcfiles_amount)
        logger.info("Found %s tests to execute\n", len(workdir_data.test_set))

        if workdir_data.test_set:
            logger.info(
                "Running WORKING DIRECTORY test set and exiting without updating..."
            )
            config.pluginmanager.register(
                NormalPhasePlugin(workdir_data.test_set, TEST_GETTER)
            )
            return

        logger.info("No WORKING DIRECTORY tests to run, checking COMMITTED changes...")

        current_hash = get_current_head_hash()
        previous_hash = MAPPING_HELPER.last_update_hash
        if current_hash == previous_hash:
            pytest.exit("Database is updated to the current commit state", 0)

        logger.info("Comparison: %s\n", " => ".join([current_hash, previous_hash]))

        committed_data = get_tests_and_data_committed(MAPPING_HELPER, TEST_GETTER)

        logger.info("COMMITTED CHANGES")
        logger.info(
            "Found %s changed test files", committed_data.changed_testfiles_amount
        )
        logger.info(
            "Found %s changed src files", committed_data.changed_srcfiles_amount
        )
        logger.info(
            "Found %s newly added tests",
            committed_data.new_tests_amount,
        )
        logger.info("Found %s tests to execute\n", len(committed_data.test_set))

        if committed_data.warning_needed:
            logger.info(
                "WARNING: New lines were added to the following files but no new tests discovered:"
            )
            logger.info("\n".join(committed_data.files_to_warn))

        logger.info("=> Executing tests (if any) and updating database")
        MAPPING_HELPER.set_last_update_hash(current_hash)

        MAPPING_HELPER.update_mapping(committed_data.update_data)

        if committed_data.test_set:
            config.pluginmanager.register(
                UpdatePhasePlugin(committed_data.test_set, MAPPING_HELPER, TEST_GETTER)
            )
            return

        pytest.exit("No tests to run", 0)


def pytest_unconfigure(config):
    """Cleanup after pytest run"""
    if config.option.rts:
        CONN.commit()
        CONN.close()
