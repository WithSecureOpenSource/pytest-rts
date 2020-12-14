"""This module contains evaluation code for the tool"""
import logging
import os
import subprocess
from pytest_rts.utils.git import (
    changed_files_between_commits,
    file_diff_data_between_commits,
    get_current_head_hash,
    get_test_lines_and_update_lines,
)
from pytest_rts.utils.db import (
    DatabaseHelper,
    DB_FILE_NAME,
)
from pytest_rts.tests.evaluation.results_db import (
    ResultDatabase,
    RESULTS_DB_FILE_NAME,
)
from pytest_rts.tests.evaluation.eval_helpers import (
    capture_all_exit_code,
    capture_specific_exit_code,
    delete_random_line,
    full_diff_between_commits,
    print_remove_test_output,
    select_random_file,
)
from pytest_rts.tests.testhelper import (
    TestHelper,
)


def random_remove_test(iterations, deletes_per_iteration, max_wait, logger):
    """Delete random lines and evaluate tests sets and pytest exitcodes"""
    if not os.path.isfile(DB_FILE_NAME):
        logger.info("Running mapping database initialization...")
        subprocess.run(["pytest", "--rts"], check=False)

    results_db = ResultDatabase()
    results_db.init_conn()
    results_db.init_results_db()

    mapping_db = DatabaseHelper()
    mapping_db.init_conn()

    test_suite_size = mapping_db.get_test_suite_size()
    project_name = os.getcwd()
    init_hash = mapping_db.get_last_update_hash()
    db_size = os.path.getsize("./mapping.db")
    project_id = results_db.store_results_project(
        project_name, init_hash, test_suite_size, db_size
    )

    _, src_files = mapping_db.get_testfiles_and_srcfiles()

    testhelper = TestHelper()

    for i in range(iterations):

        # Remove random lines
        testhelper.checkout_new_branch()
        for j in range(deletes_per_iteration):
            random_file = select_random_file(src_files)
            filename = random_file[1]
            delete_random_line(filename)
            testhelper.commit_change(filename, str(j + 1))

        # Gets tests based on line-level and file-level change
        current_git_hash = get_current_head_hash()
        changed_files = changed_files_between_commits(init_hash, current_git_hash)
        tests_line_level = set()
        tests_file_level = set()
        for filename in changed_files:
            diff = file_diff_data_between_commits(filename, init_hash, current_git_hash)
            test_lines, _, _ = get_test_lines_and_update_lines(diff)
            file_id = mapping_db.save_src_file(filename)
            tests_line = mapping_db.query_tests_srcfile(test_lines, file_id)
            tests_file = mapping_db.query_all_tests_srcfile(file_id)
            for testfunc_line in tests_line:
                tests_line_level.add(testfunc_line)
            for testfunc_file in tests_file:
                tests_file_level.add(testfunc_file)

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
        testhelper.checkout_branch("master")
        testhelper.delete_branch("new-branch")

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
