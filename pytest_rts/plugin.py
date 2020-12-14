"""Code for pytest-rts plugin logic"""
import logging
import os
import pytest
from pytest_rts.pytest.init_phase_plugin import InitPhasePlugin
from pytest_rts.pytest.normal_phase_plugin import NormalPhasePlugin
from pytest_rts.pytest.update_phase_plugin import UpdatePhasePlugin
from pytest_rts.utils.common import update_mapping_db
from pytest_rts.utils.db import DatabaseHelper, DB_FILE_NAME
from pytest_rts.select import get_tests_and_data_committed, get_tests_and_data_current
from pytest_rts.utils.git import get_current_head_hash


def pytest_addoption(parser):
    """Register pytest flags"""
    parser.addoption("--rts", action="store_true", default=False, help="run rts")


def pytest_configure(config):
    """Register RTS plugins based on state"""
    logger = logging.getLogger()
    logging.basicConfig(format="%(message)s", level=logging.INFO)

    if config.option.rts:
        if not os.path.isfile(DB_FILE_NAME):
            logger.info("No mapping database detected, starting initialization...")
            config.pluginmanager.register(InitPhasePlugin())
            return

        db_helper = DatabaseHelper()
        db_helper.init_conn()

        workdir_data = get_tests_and_data_current(db_helper)

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
            config.pluginmanager.register(NormalPhasePlugin(workdir_data.test_set))
            return

        logger.info("No WORKING DIRECTORY tests to run, checking COMMITTED changes...")

        current_hash = get_current_head_hash()
        if db_helper.is_last_update_hash(current_hash):
            pytest.exit("Database is updated to the current commit state", 0)

        previous_hash = db_helper.get_last_update_hash()
        logger.info("Comparison: %s\n", " => ".join([current_hash, previous_hash]))

        committed_data = get_tests_and_data_committed(db_helper)

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
        db_helper.save_last_update_hash(current_hash)

        update_mapping_db(committed_data.update_data, db_helper)

        if committed_data.test_set:
            config.pluginmanager.register(UpdatePhasePlugin(committed_data.test_set))
            return

        pytest.exit("No tests to run", 0)
