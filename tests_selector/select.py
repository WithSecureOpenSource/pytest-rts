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
from tests_selector.utils.types.namedtuples import (
    TestsAndDataFromChanges,
    UpdateTuple,
    TestsAndDataCurrent,
    TestsAndDataCommitted,
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

    update_tuple = UpdateTuple(
        test_changed_lines_dict=test_changed_lines_dict,
        test_new_line_map_dict=test_new_line_map_dict,
        src_changed_lines_dict=src_changed_lines_dict,
        src_new_line_map_dict=src_new_line_map_dict,
    )

    return TestsAndDataFromChanges(
        test_set=test_set, update_tuple=update_tuple, files_to_warn=files_to_warn
    )


def get_tests_and_data_current(db):
    """Returns the test set from working directory changes and data for printing statistics"""
    changed_files = changed_files_current()
    changed_test_files, changed_src_files = split_changes(changed_files, db)

    diff_dict_src = file_diff_dict_current(changed_src_files)
    diff_dict_test = file_diff_dict_current(changed_test_files)

    changes = get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files, db
    )

    return TestsAndDataCurrent(
        test_set=changes.test_set,
        changed_testfiles_amount=len(changed_test_files),
        changed_srcfiles_amount=len(changed_src_files),
    )


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
    changes = get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files, db
    )
    full_test_set = changes.test_set.union(new_tests)

    warning_needed = changes.files_to_warn and not new_tests

    return TestsAndDataCommitted(
        test_set=full_test_set,
        update_tuple=changes.update_tuple,
        changed_testfiles_amount=len(changed_test_files),
        changed_srcfiles_amount=len(changed_src_files),
        new_tests_amount=len(new_tests),
        warning_needed=warning_needed,
        files_to_warn=changes.files_to_warn,
    )


def main():
    if not os.path.isfile(DB_FILE_NAME):
        print("Run tests_selector_init first")
        exit(1)

    db = DatabaseHelper()
    db.init_conn()

    workdir_data = get_tests_and_data_current(db)

    print("WORKING DIRECTORY CHANGES")
    print(f"Found {workdir_data.changed_testfiles_amount} changed test files")
    print(f"Found {workdir_data.changed_srcfiles_amount} changed src files")
    print(f"Found {len(workdir_data.test_set)} tests to execute\n")

    if workdir_data.test_set:
        print("Running WORKING DIRECTORY test set and exiting without updating...")
        subprocess.run(["tests_selector_run"] + list(workdir_data.test_set))
        exit()

    print("No WORKING DIRECTORY tests to run, checking COMMITTED changes...")
    current_hash = get_current_head_hash()
    if db.is_last_update_hash(current_hash):
        print("Database is updated to the current commit state")
        print("=> Skipping test discovery, execution and updating")
        exit()

    previous_hash = db.get_last_update_hash()
    print(f"Comparison: {current_hash} => {previous_hash}\n")

    committed_data = get_tests_and_data_committed(db)
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
    print(f"Found {committed_data.changed_testfiles_amount} changed test files")
    print(f"Found {committed_data.changed_srcfiles_amount} changed src files")
    print(f"Found {committed_data.new_tests_amount} newly added tests")
    print(f"Found {len(committed_data.test_set)} tests to execute\n")
    if committed_data.warning_needed:
        print(
            "WARNING: New lines were added to the following files but no new tests discovered:"
        )
        print(*committed_data.files_to_warn, sep="\n", end="\n\n")

    print("=> Executing tests (if any) and updating database")
    db.save_last_update_hash(current_hash)
    run_tests_and_update_db(committed_data.test_set, committed_data.update_tuple, db)

    db.close_conn()


if __name__ == "__main__":
    main()
