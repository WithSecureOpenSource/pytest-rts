import os
import subprocess
import sys
import random
import ntpath

from tests_selector.utils.git import (
    get_git_repo,
    file_diff_data_current,
    get_test_lines_and_update_lines,
    changed_files_branch,
    file_diff_data_branch,
)
from tests_selector.evaluation.eval_helper import (
    select_random_file,
    delete_random_line,
    capture_specific_exit_code,
    capture_all_exit_code,
    print_remove_test_output,
    install_dependencies,
)

from tests_selector.utils.db import (
    DatabaseHelper,
    ResultDatabaseHelper,
    DB_FILE_NAME,
    RESULTS_DB_FILE_NAME,
)

PROJECT_FOLDER = sys.argv[1]


def random_remove_test(iterations):

    ans = input("init mapping db? [y/n]: ")
    if ans == "y":
        subprocess.run(["tests_selector_init"])

    if not os.path.isfile(DB_FILE_NAME):
        print("No mapping.db found")
        exit(1)

    deletes = 1
    max_wait = int(input("max wait time for tests? in seconds "))
    repo = get_git_repo(PROJECT_FOLDER)
    git_helper = repo.repo.git

    results_db = ResultDatabaseHelper()
    results_db.init_conn()
    results_db.init_results_db()

    mapping_db = DatabaseHelper()
    mapping_db.init_conn()

    test_suite_size = mapping_db.get_test_suite_size()
    project_name = ntpath.basename(PROJECT_FOLDER)
    commithash = repo.get_head().hash
    db_size = os.path.getsize("./mapping.db")
    project_id = results_db.store_results_project(
        project_name, commithash, test_suite_size, db_size
    )

    test_files, src_files = mapping_db.get_testfiles_and_srcfiles()

    for i in range(iterations):
        random_file = select_random_file(src_files)
        file_id = random_file[0]
        filename = random_file[1]

        delete_random_line(filename, PROJECT_FOLDER)

        diff = file_diff_data_current(filename, PROJECT_FOLDER)
        test_lines, updates_to_lines = get_test_lines_and_update_lines(diff)
        tests_line_level = mapping_db.query_tests_srcfile(test_lines, file_id)
        tests_file_level = mapping_db.query_all_tests_srcfile(file_id)

        if len(tests_line_level) == 0:
            exitcode_line = 5  # pytest exitcode for no tests collected
        else:
            exitcode_line = capture_specific_exit_code(
                tests_line_level, PROJECT_FOLDER, max_wait
            )
        if len(tests_file_level) == 0:
            exitcode_file = 5
        else:
            exitcode_file = capture_specific_exit_code(
                tests_file_level, PROJECT_FOLDER, max_wait
            )
        exitcode_all = capture_all_exit_code(PROJECT_FOLDER, max_wait)

        git_helper.restore(filename)

        results_db.store_results_data(
            project_id,
            deletes,
            exitcode_line,
            exitcode_file,
            exitcode_all,
            len(tests_line_level),
            len(tests_file_level),
            diff,
        )

        print_remove_test_output(
            i,
            project_name,
            commithash,
            deletes,
            test_suite_size,
            len(tests_line_level),
            len(tests_file_level),
            exitcode_line,
            exitcode_file,
            exitcode_all,
            RESULTS_DB_FILE_NAME,
        )


def random_remove_test_multiple(iterations):
    # remove random lines, commit changes and use branch detection
    ans = input("init mapping db? [y/n]: ")
    if ans == "y":
        subprocess.run(["tests_selector_init"])

    if not os.path.isfile(DB_FILE_NAME):
        print("No mapping.db found")
        exit(1)

    deletes = int(input("how many random deletes per iteration?: "))
    max_wait = int(input("max wait time for tests? in seconds "))
    install_cmd = input(
        "install command to run tests (new branch transition might break test running, empty if not needed) "
    )
    install_required = install_cmd != ""
    repo = get_git_repo(PROJECT_FOLDER)
    git_helper = repo.repo.git

    results_db = ResultDatabaseHelper()
    results_db.init_conn()
    results_db.init_results_db()
    mapping_db = DatabaseHelper()
    mapping_db.init_conn()

    test_suite_size = mapping_db.get_test_suite_size()
    project_name = ntpath.basename(PROJECT_FOLDER)
    commithash = repo.get_head().hash
    db_size = os.path.getsize("./mapping.db")
    project_id = results_db.store_results_project(
        project_name, commithash, test_suite_size, db_size
    )

    test_files, src_files = mapping_db.get_testfiles_and_srcfiles()

    for i in range(iterations):
        git_helper.checkout("HEAD", b="eval-test-branch")
        for j in range(deletes):
            random_file = select_random_file(src_files)
            file_id = random_file[0]
            filename = random_file[1]

            delete_random_line(filename, PROJECT_FOLDER)
            git_helper.add(filename)
            git_helper.commit("-m", str(j + 1))

        changed_files = changed_files_branch(PROJECT_FOLDER)
        tests_line_level = set()
        tests_file_level = set()
        for f in changed_files:
            diff = file_diff_data_branch(f, PROJECT_FOLDER)
            test_lines, updates_to_lines = get_test_lines_and_update_lines(diff)
            tests_line = mapping_db.query_tests_srcfile(test_lines, file_id)
            tests_file = mapping_db.query_all_tests_srcfile(file_id)
            for tl in tests_line:
                tests_line_level.add(tl)
            for tf in tests_file:
                tests_file_level.add(tf)

        full_diff = git_helper.diff("-U0", "master...")

        if install_required:
            install_dependencies(install_cmd)

        if len(tests_line_level) == 0:
            exitcode_line = 5  # pytest exitcode for no tests collected
        else:
            exitcode_line = capture_specific_exit_code(
                list(tests_line_level), PROJECT_FOLDER, max_wait
            )
        if len(tests_file_level) == 0:
            exitcode_file = 5
        else:
            exitcode_file = capture_specific_exit_code(
                list(tests_file_level), PROJECT_FOLDER, max_wait
            )
        exitcode_all = capture_all_exit_code(PROJECT_FOLDER, max_wait)

        git_helper.checkout("master", "--force")
        git_helper.branch("-D", "eval-test-branch")

        results_db.store_results_data(
            project_id,
            deletes,
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
            commithash,
            deletes,
            test_suite_size,
            len(tests_line_level),
            len(tests_file_level),
            exitcode_line,
            exitcode_file,
            exitcode_all,
            RESULTS_DB_FILE_NAME,
        )


def main():

    print("Options:")
    print("Remove random line, run tests and compare results [1]")
    print("Remove multiple random lines, run tests and compare results [2]")
    print(
        "[2] is slower than [1] for 1 line removal because changes are made in a new branch and pip install required for some projects"
    )
    ans = input("Choose option 1 or 2: ")

    if ans == "1":
        ans = input("how many iterations? ")
        iters = int(ans)
        random_remove_test(iters)
    elif ans == "2":
        ans = input("how many iterations? ")
        iters = int(ans)
        random_remove_test_multiple(iters)


if __name__ == "__main__":
    main()
