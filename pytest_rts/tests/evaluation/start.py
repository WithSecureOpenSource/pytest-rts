"""This module contains evaluation code for the tool"""
import logging
import os
import subprocess

from pytest_rts.plugin import DB_FILE_NAME
from pytest_rts.utils.git import (
    get_current_head_hash,
)
from pytest_rts.tests.evaluation.results_db import (
    ResultDatabase,
    RESULTS_DB_FILE_NAME,
)
from pytest_rts.tests.evaluation.evaluation_utils import (
    capture_all_exit_code,
    capture_specific_exit_code,
    delete_random_line,
    get_all_tests_for_srcfile,
    get_file_level_tests_between_commits,
    full_diff_between_commits,
    get_mapping_init_hash,
    get_mapping_srcfiles,
    get_srcfile_id,
    get_test_suite_size,
    print_remove_test_output,
    select_random_file,
)
from pytest_rts.tests.testhelper import TestHelper


EVALUATION_BRANCH = "evaluation-branch"
MAIN_BRANCH = "master"


def random_remove_test(iterations, deletes_per_iteration, max_wait, logger):
    """Delete random lines and evaluate tests sets and pytest exitcodes"""
    if not os.path.isfile(DB_FILE_NAME):
        subprocess.run(["pytest", "--rts"], check=False)

    results_db = ResultDatabase()
    results_db.init_conn()
    results_db.init_results_db()

    test_suite_size = get_test_suite_size()
    project_name = os.getcwd()
    init_hash = get_mapping_init_hash()
    db_size = os.path.getsize(DB_FILE_NAME)
    project_id = results_db.store_results_project(
        project_name, init_hash, test_suite_size, db_size
    )

    src_files = get_mapping_srcfiles()

    testhelper = TestHelper()

    for i in range(iterations):

        # Remove random lines
        testhelper.checkout_new_branch(EVALUATION_BRANCH)
        for j in range(deletes_per_iteration):
            random_filepath = select_random_file(src_files)
            delete_random_line(random_filepath)
            testhelper.commit_change(random_filepath, str(j + 1))

        current_git_hash = get_current_head_hash()

        # Get tests based on line-level and file-level changes
        tests_line_level = testhelper.get_tests_from_tool_committed()
        tests_file_level = get_file_level_tests_between_commits(
            init_hash, current_git_hash
        )

        # Get full git diff for analysis
        full_diff = full_diff_between_commits(init_hash, current_git_hash)

        # Pytest exitcodes for running different test sets
        exitcode_line = (
            capture_specific_exit_code(list(tests_line_level), max_wait)
            if tests_line_level
            else 5
        )
        exitcode_file = (
            capture_specific_exit_code(list(tests_file_level), max_wait)
            if tests_file_level
            else 5
        )
        exitcode_all = capture_all_exit_code(max_wait)

        # Clear removal
        testhelper.checkout_branch(MAIN_BRANCH)
        testhelper.delete_branch(EVALUATION_BRANCH)

        # Store and print data
        results_db.store_results_data(
            project_id,
            deletes_per_iteration,
            exitcode_line,
            exitcode_file,
            exitcode_all,
            len(tests_line_level),
            len(tests_file_level),
            full_diff,
        )
        print_remove_test_output(
            i,
            project_name,
            init_hash,
            deletes_per_iteration,
            test_suite_size,
            len(tests_line_level),
            len(tests_file_level),
            exitcode_line,
            exitcode_file,
            exitcode_all,
            RESULTS_DB_FILE_NAME,
            logger,
        )


def main():
    """Evaluation script entrypoint"""
    logger = logging.getLogger()
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    logger.info("RANDOM LINE REMOVE TESTING")
    iterations = int(input("How many iterations? "))
    deletes_per_iteration = int(input("How many line removals per iteration? "))
    max_wait = int(input("Max wait time for test set running (in seconds)? "))
    random_remove_test(iterations, deletes_per_iteration, max_wait, logger)


if __name__ == "__main__":
    main()
