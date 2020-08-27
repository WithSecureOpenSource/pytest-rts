import os
import subprocess
import sys
import random
import ntpath

from tests_selector.utils.common import (
    tests_from_changed_testfiles,
    tests_from_changed_srcfiles,
    file_diff_dict_between_commits,
    read_newly_added_tests,
    split_changes,
)
from tests_selector.utils.db import (
    get_results_cursor,
    get_testfiles_and_srcfiles,
    init_results_db,
    DB_FILE_NAME,
    RESULTS_DB_FILE_NAME,
    get_test_suite_size,
    store_results_project,
    query_tests_srcfile,
    query_all_tests_srcfile,
    store_results_data,
)
from tests_selector.utils.git import (
    get_git_repo,
    file_changes_between_commits,
    file_diff_data_current,
    get_test_lines_and_update_lines,
)
from tests_selector.evaluation.eval_helper import (
    start_test_init,
    run_tests_and_update_db,
    select_random_file,
    delete_random_line,
    capture_specific_exit_code,
    capture_all_exit_code,
)

PROJECT_FOLDER = sys.argv[1]


def install_dependencies(install_cmd):
    old_dir = os.getcwd()
    os.chdir("./" + PROJECT_FOLDER)
    subprocess.run(install_cmd.split())
    os.chdir(old_dir)


def tests_from_changes_between_commits(commithash1, commithash2, project_folder):
    changed_files = file_changes_between_commits(
        commithash1, commithash2, project_folder
    )

    changed_test_files, changed_src_files = split_changes(changed_files)

    diff_dict_src = file_diff_dict_between_commits(
        changed_src_files, commithash1, commithash2, project_folder
    )
    diff_dict_test = file_diff_dict_between_commits(
        changed_test_files, commithash1, commithash2, project_folder
    )
    (
        test_test_set,
        test_changed_lines_dict,
        test_new_line_map_dict,
    ) = tests_from_changed_testfiles(diff_dict_test, changed_test_files)
    (
        src_test_set,
        src_changed_lines_dict,
        src_new_line_map_dict,
    ) = tests_from_changed_srcfiles(diff_dict_src, changed_src_files)

    test_set = test_test_set.union(src_test_set)
    update_tuple = (
        test_changed_lines_dict,
        test_new_line_map_dict,
        src_changed_lines_dict,
        src_new_line_map_dict,
    )

    return test_set, update_tuple


def iterate_commits_and_build_db():
    # builds database by going through commits and running specific tests
    # problem: different dependencies / changing ways of installing dependencies
    repo = get_git_repo(PROJECT_FOLDER)
    git_commits = list(repo.get_list_commits())

    print(f"repo has {len(git_commits)} commits")
    start = int(input("start commit?"))
    end = int(input("end commit?"))
    install_cmd = input(
        "command to install dependencies? (when in the tested project folder)"
    )

    hash_1 = git_commits[start].hash
    repo.checkout(hash_1)
    install_dependencies(install_cmd)
    start_test_init(PROJECT_FOLDER)

    for commit in git_commits[start + 1 : end]:
        hash_2 = commit.hash
        repo.checkout(hash_2)
        install_dependencies(install_cmd)
        change_test_set, update_tuple = tests_from_changes_between_commits(
            hash_1, hash_2, PROJECT_FOLDER
        )
        new_tests = read_newly_added_tests(PROJECT_FOLDER)
        final_test_set = change_test_set.union(new_tests)
        run_tests_and_update_db(final_test_set, update_tuple, PROJECT_FOLDER)
        hash_1 = commit.hash

    repo._delete_tmp_branch()


def random_remove_test(iterations):

    ans = input("init mapping db? [y/n]: ")
    if ans == "y":
        start_test_init(PROJECT_FOLDER)

    if not os.path.isfile(DB_FILE_NAME):
        print("no mapping db found")
        exit(1)

    max_wait = int(input("max wait time for tests? in seconds "))
    repo = get_git_repo(PROJECT_FOLDER)
    git_helper = repo.repo.git

    init_results_db()
    test_suite_size = get_test_suite_size()
    project_name = ntpath.basename(PROJECT_FOLDER)
    commithash = repo.get_head().hash
    db_size = os.path.getsize("./mapping.db")
    project_id = store_results_project(
        project_name, commithash, test_suite_size, db_size
    )

    test_files, src_files = get_testfiles_and_srcfiles()

    for i in range(iterations):
        random_file = select_random_file(src_files)
        file_id = random_file[0]
        filename = random_file[1]

        delete_random_line(filename, PROJECT_FOLDER)

        diff = file_diff_data_current(filename, PROJECT_FOLDER)
        test_lines, updates_to_lines = get_test_lines_and_update_lines(diff)
        tests_line_level = query_tests_srcfile(test_lines, file_id)
        tests_file_level = query_all_tests_srcfile(file_id)

        exitcode_line = capture_specific_exit_code(
            tests_line_level, PROJECT_FOLDER, max_wait
        )
        exitcode_file = capture_specific_exit_code(
            tests_file_level, PROJECT_FOLDER, max_wait
        )
        exitcode_all = capture_all_exit_code(PROJECT_FOLDER, max_wait)

        store_results_data(
            project_id,
            exitcode_line,
            exitcode_file,
            exitcode_all,
            len(tests_line_level),
            len(tests_file_level),
            diff,
        )

        print("============")
        print("iteration:", i + 1)
        print("project name:", project_name)
        print("commit hash:", commithash)
        print("deleted random line in file:", filename)
        print("size of full test suite:", test_suite_size)
        print("size of line level test suite:", len(tests_line_level))
        print("size of file level test suite:", len(tests_file_level))
        print(
            f"exitcodes: line-level: {exitcode_line}, file-level: {exitcode_file}, all: {exitcode_all}"
        )
        print("STORING TO DATABASE:", RESULTS_DB_FILE_NAME)
        print("============")

        git_helper.restore(filename)


def main():
    ans = input(
        "Iterate commits and build db [1] or remove random lines and run tests [2] ? "
    )
    if ans == "1":
        iterate_commits_and_build_db()
    elif ans == "2":
        ans = input("how many iterations? ")
        iters = int(ans)
        random_remove_test(iters)


if __name__ == "__main__":
    main()
