"""This module contains code for the main functionality of the RTS tool"""
import logging
import os
import subprocess
import sys
from typing import Dict, List, NamedTuple, Set
from pytest_rts.utils.common import (
    file_diff_dict_between_commits,
    file_diff_dict_current,
    read_newly_added_tests,
    run_tests_and_update_db,
    split_changes,
    tests_from_changed_srcfiles,
    tests_from_changed_testfiles,
)
from pytest_rts.utils.git import (
    changed_files_current,
    changed_files_between_commits,
    get_current_head_hash,
)
from pytest_rts.utils.db import (
    DatabaseHelper,
    DB_FILE_NAME,
)

# https://github.com/PyCQA/pylint/issues/3876
# pylint: disable=inherit-non-class
# pylint: disable=too-few-public-methods
class UpdateData(NamedTuple):
    """NamedTuple for mapping database update data"""

    changed_lines_test: Dict[str, List[int]]
    new_line_map_test: Dict[int, int]
    changed_lines_src: Dict[str, List[int]]
    new_line_map_src: Dict[int, int]


# pylint: disable=inherit-non-class
# pylint: disable=too-few-public-methods
class TestsAndDataFromChanges(NamedTuple):
    """NamedTuple for tests and update data from changes"""

    test_set: Set[str]
    update_data: UpdateData
    files_to_warn: List[str]


# pylint: disable=inherit-non-class
# pylint: disable=too-few-public-methods
class TestsAndDataCurrent(NamedTuple):
    """NamedTuple for tests and statistics data from working directory changes"""

    test_set: Set[str]
    changed_testfiles_amount: int
    changed_srcfiles_amount: int


# pylint: disable=inherit-non-class
# pylint: disable=too-few-public-methods
class TestsAndDataCommitted(NamedTuple):
    """NamedTuple for tests, statistics and update data from committed changes"""

    test_set: Set[str]
    update_data: UpdateData
    changed_testfiles_amount: int
    changed_srcfiles_amount: int
    new_tests_amount: int
    warning_needed: bool
    files_to_warn: List[str]


def get_tests_from_changes(
    test_file_diffs, src_file_diffs, testfiles, srcfiles, db_helper
) -> TestsAndDataFromChanges:
    """Returns the test set and data required for line shifting"""
    (
        src_test_set,
        changed_lines_src,
        new_line_map_src,
        files_to_warn,
    ) = tests_from_changed_srcfiles(src_file_diffs, srcfiles, db_helper)

    (
        test_test_set,
        changed_lines_test,
        new_line_map_test,
    ) = tests_from_changed_testfiles(test_file_diffs, testfiles, db_helper)

    test_set = test_test_set.union(src_test_set)

    update_data = UpdateData(
        changed_lines_test=changed_lines_test,
        new_line_map_test=new_line_map_test,
        changed_lines_src=changed_lines_src,
        new_line_map_src=new_line_map_src,
    )

    return TestsAndDataFromChanges(
        test_set=test_set, update_data=update_data, files_to_warn=files_to_warn
    )


def get_tests_and_data_current(db_helper) -> TestsAndDataCurrent:
    """Returns the test set from working directory changes and data for printing statistics"""
    changed_files = changed_files_current()
    changed_test_files, changed_src_files = split_changes(changed_files, db_helper)

    src_file_diffs = file_diff_dict_current(changed_src_files)
    test_file_diffs = file_diff_dict_current(changed_test_files)

    changes = get_tests_from_changes(
        test_file_diffs,
        src_file_diffs,
        changed_test_files,
        changed_src_files,
        db_helper,
    )

    return TestsAndDataCurrent(
        test_set=changes.test_set,
        changed_testfiles_amount=len(changed_test_files),
        changed_srcfiles_amount=len(changed_src_files),
    )


def get_tests_and_data_committed(db_helper) -> TestsAndDataCommitted:
    """Compares current git HEAD has to previous update state commit hash
    Returns the test set and data required for line-shifting and printing statistics
    """
    current_hash = get_current_head_hash()
    previous_hash = db_helper.get_last_update_hash()

    changed_files = changed_files_between_commits(previous_hash, current_hash)
    changed_test_files, changed_src_files = split_changes(changed_files, db_helper)

    src_file_diffs = file_diff_dict_between_commits(
        changed_src_files, previous_hash, current_hash
    )
    test_file_diffs = file_diff_dict_between_commits(
        changed_test_files, previous_hash, current_hash
    )

    new_tests = read_newly_added_tests(db_helper)
    changes = get_tests_from_changes(
        test_file_diffs,
        src_file_diffs,
        changed_test_files,
        changed_src_files,
        db_helper,
    )
    full_test_set = changes.test_set.union(new_tests)

    warning_needed = bool(changes.files_to_warn and not new_tests)

    return TestsAndDataCommitted(
        test_set=full_test_set,
        update_data=changes.update_data,
        changed_testfiles_amount=len(changed_test_files),
        changed_srcfiles_amount=len(changed_src_files),
        new_tests_amount=len(new_tests),
        warning_needed=warning_needed,
        files_to_warn=changes.files_to_warn,
    )


def main():
    """Run tool by first checking git working directory changes and then committed changes"""
    logger = logging.getLogger()
    logging.basicConfig(format="%(message)s", level=logging.INFO)

    if not os.path.isfile(DB_FILE_NAME):
        logger.info("Run pytest_rts_init first")
        sys.exit()

    db_helper = DatabaseHelper()
    db_helper.init_conn()

    workdir_data = get_tests_and_data_current(db_helper)

    logger.info("WORKING DIRECTORY CHANGES")
    logger.info("Found %s changed test files", workdir_data.changed_testfiles_amount)
    logger.info("Found %s changed src files", workdir_data.changed_srcfiles_amount)
    logger.info("Found %s tests to execute\n", len(workdir_data.test_set))

    if workdir_data.test_set:
        logger.info(
            "Running WORKING DIRECTORY test set and exiting without updating..."
        )
        subprocess.run(["pytest_rts_run"] + list(workdir_data.test_set), check=True)
        sys.exit()

    logger.info("No WORKING DIRECTORY tests to run, checking COMMITTED changes...")
    current_hash = get_current_head_hash()
    if db_helper.is_last_update_hash(current_hash):
        logger.info("Database is updated to the current commit state")
        logger.info("=> Skipping test discovery, execution and updating")
        sys.exit()

    previous_hash = db_helper.get_last_update_hash()
    logger.info("Comparison: %s\n", " => ".join([current_hash, previous_hash]))

    committed_data = get_tests_and_data_committed(db_helper)

    logger.info("COMMITTED CHANGES")
    logger.info("Found %s changed test files", committed_data.changed_testfiles_amount)
    logger.info("Found %s changed src files", committed_data.changed_srcfiles_amount)
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
    run_tests_and_update_db(
        committed_data.test_set, committed_data.update_data, db_helper
    )

    db_helper.close_conn()


if __name__ == "__main__":
    main()
