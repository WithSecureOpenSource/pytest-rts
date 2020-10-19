import os
import subprocess
from tests_selector.utils.common import (
    split_changes,
    tests_from_changed_srcfiles,
    tests_from_changed_testfiles,
    read_newly_added_tests,
    file_diff_dict_current,
    file_diff_dict_between_commits,
    run_tests_and_update_db,
)
from tests_selector.utils.git import (
    changed_files_current,
    changed_files_between_commits,
    get_current_head_hash,
)

from tests_selector.utils.db import (
    DB_FILE_NAME,
    DatabaseHelper,
)


def get_tests_from_changes(diff_dict_test, diff_dict_src, testfiles, srcfiles, db):
    """Returns the test set and data required for line shifting"""
    (
        src_test_set,
        src_changed_lines_dict,
        src_new_line_map_dict,
        files_to_warn,
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
    return test_set, update_tuple, files_to_warn


def get_tests_and_data_current(db):
    """Returns the test set from working directory changes and data for printing statistics"""
    changed_files = changed_files_current()
    changed_test_files, changed_src_files = split_changes(changed_files, db)

    diff_dict_src = file_diff_dict_current(changed_src_files)
    diff_dict_test = file_diff_dict_current(changed_test_files)

    test_set, update_tuple, _ = get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files, db
    )

    return test_set, len(changed_test_files), len(changed_src_files)


def get_tests_and_data_committed(db):
    """Compares current git HEAD has to previous update state commit hash
    Returns the test set and data required for line-shifting and printing statistics
    """
    current_hash = get_current_head_hash()
    previous_hash = db.get_last_update_hash()

    changed_files = changed_files_between_commits(previous_hash, current_hash)
    changed_test_files, changed_src_files = split_changes(changed_files, db)

    diff_dict_src = file_diff_dict_between_commits(
        changed_src_files, previous_hash, current_hash
    )
    diff_dict_test = file_diff_dict_between_commits(
        changed_test_files, previous_hash, current_hash
    )

    new_tests = read_newly_added_tests(db)
    changes_test_set, update_tuple, files_to_warn = get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files, db
    )
    test_set = changes_test_set.union(new_tests)

    warning_needed = (len(new_tests) == 0) and (len(files_to_warn) > 0)

    return (
        test_set,
        update_tuple,
        len(changed_test_files),
        len(changed_src_files),
        len(new_tests),
        warning_needed,
        files_to_warn,
    )


def main():
    if not os.path.isfile(DB_FILE_NAME):
        print("Run tests_selector_init first")
        exit(1)

    db = DatabaseHelper()
    db.init_conn()

    (
        workdir_test_set,
        workdir_changed_test_files_amount,
        workdir_changed_src_files_amount,
    ) = get_tests_and_data_current(db)

    print("WORKING DIRECTORY CHANGES")
    print(f"Found {workdir_changed_test_files_amount} changed test files")
    print(f"Found {workdir_changed_src_files_amount} changed src files")
    print(f"Found {len(workdir_test_set)} tests to execute", end="\n\n")

    if len(workdir_test_set) > 0:
        print("Running WORKING DIRECTORY test set and exiting without updating...")
        subprocess.run(["tests_selector_run"] + list(workdir_test_set))
        exit()

    print("No WORKING DIRECTORY tests to run, checking COMMITTED changes...")
    current_hash = get_current_head_hash()
    if db.is_last_update_hash(current_hash):
        print("Database is updated to the current commit state")
        print("=> Skipping test discovery, execution and updating")
        exit()

    previous_hash = db.get_last_update_hash()
    print(f"Comparison: {current_hash} => {previous_hash}", end="\n\n")

    (
        commit_test_set,
        commit_update_tuple,
        commit_changed_test_files_amount,
        commit_changed_src_files_amount,
        new_tests_amount,
        warning_needed,
        files_to_warn,
    ) = get_tests_and_data_committed(db)

    print("COMMITTED CHANGES")
    print(f"Found {commit_changed_test_files_amount} changed test files")
    print(f"Found {commit_changed_src_files_amount} changed src files")
    print(f"Found {new_tests_amount} newly added tests")
    print(f"Found {len(commit_test_set)} tests to execute", end="\n\n")
    if warning_needed:
        print(
            "WARNING: New lines were added to the following files but no new tests discovered:"
        )
        print(*files_to_warn, sep="\n", end="\n\n")

    print("=> Executing tests (if any) and updating database")
    db.save_last_update_hash(current_hash)
    run_tests_and_update_db(commit_test_set, commit_update_tuple, db)

    db.close_conn()


if __name__ == "__main__":
    main()
