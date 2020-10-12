import os
import subprocess
from tests_selector.utils.common import (
    split_changes,
    tests_from_changed_srcfiles,
    tests_from_changed_testfiles,
    read_newly_added_tests,
    file_diff_dict_current,
    file_diff_dict_branch,
    run_tests_and_update_db,
    file_diff_dict_since_last_commit,
)
from tests_selector.utils.git import (
    changed_files_current,
    changed_files_branch,
    changed_files_since_last_commit,
    get_head_and_previous_hash,
)

from tests_selector.utils.db import (
    DB_FILE_NAME,
    DatabaseHelper,
)


def get_tests_from_changes(diff_dict_test, diff_dict_src, testfiles, srcfiles, db):
    (
        src_test_set,
        src_changed_lines_dict,
        src_new_line_map_dict,
    ) = tests_from_changed_srcfiles(diff_dict_src, srcfiles, db)

    (
        test_test_set,
        test_changed_lines_dict,
        test_new_line_map_dict,
    ) = tests_from_changed_testfiles(diff_dict_test, testfiles, db)

    test_set = test_test_set.union(src_test_set)

    update_tuple = (
        test_changed_lines_dict,
        test_new_line_map_dict,
        src_changed_lines_dict,
        src_new_line_map_dict,
    )
    return test_set, update_tuple


def get_tests_and_data_current(db):
    changed_files = changed_files_current()
    changed_test_files, changed_src_files = split_changes(changed_files, db)
    diff_dict_src = file_diff_dict_current(changed_src_files)
    diff_dict_test = file_diff_dict_current(changed_test_files)
    test_set, update_tuple = get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files, db
    )
    # No need to return update_tuple because no updating in working directory changes
    return test_set, changed_test_files, changed_src_files


def get_tests_and_data_committed(db):
    changed_files = changed_files_since_last_commit()
    changed_test_files, changed_src_files = split_changes(changed_files, db)
    diff_dict_src = file_diff_dict_since_last_commit(changed_src_files)
    diff_dict_test = file_diff_dict_since_last_commit(changed_test_files)
    new_tests = read_newly_added_tests(db)
    changes_test_set, update_tuple = get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files, db
    )
    test_set = changes_test_set.union(new_tests)

    return test_set, update_tuple, changed_test_files, changed_src_files, len(new_tests)


def main():
    if not os.path.isfile(DB_FILE_NAME):
        print("Run tests_selector_init first")
        exit(1)

    db = DatabaseHelper()
    db.init_conn()

    (
        workdir_test_set,
        workdir_changed_test_files,
        workdir_changed_src_files,
    ) = get_tests_and_data_current(db)

    print("")
    print("WORKING DIRECTORY CHANGES")
    print(f"Found {len(workdir_changed_test_files)} changed test files")
    print(f"Found {len(workdir_changed_src_files)} changed src files")
    print(f"Found {len(workdir_test_set)} tests to execute")
    print("")

    if len(workdir_test_set) > 0:
        print("Running WORKING DIRECTORY test set and exiting without updating...")
        subprocess.run(["tests_selector_run"] + list(workdir_test_set))
        exit()

    head, previous = get_head_and_previous_hash()
    print("No WORKING DIRECTORY tests to run, checking COMMITTED changes...")
    if db.is_init_hash(head):
        print("Current commit is the initial commit where database was created")
        print("=> Skipping test discovery, execution and updating")
        exit()

    print(f"Comparison: {head} => {previous}")
    (
        commit_test_set,
        commit_update_tuple,
        commit_changed_test_files,
        commit_changed_src_files,
        new_tests_amount,
    ) = get_tests_and_data_committed(db)

    print("")
    print("COMMITTED CHANGES")
    print(f"Found {len(commit_changed_test_files)} changed test files")
    print(f"Found {len(commit_changed_src_files)} changed src files")
    print(f"Found {new_tests_amount} newly added tests")
    print(f"Found {len(commit_test_set)} tests to execute")
    print("")

    print("Checking database update status...")
    if db.comparison_exists(head, previous):
        print("Database already updated for this state")
        print("=> Skipping updating but executing tests...")
        subprocess.run(["tests_selector_run"] + list(commit_test_set))
        exit()

    print("=> Executing tests and updating database")
    db.save_comparison(head, previous)
    run_tests_and_update_db(commit_test_set, commit_update_tuple, db)

    db.close_conn()


if __name__ == "__main__":
    main()
