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
)
from tests_selector.utils.git import (
    changed_files_current,
    changed_files_branch,
)

from tests_selector.utils.db import (
    DB_FILE_NAME,
    NEW_DB_FILE_NAME,
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


def main():
    if not os.path.isfile(DB_FILE_NAME):
        print("Run tests_selector_init first")
        exit(1)

    db = DatabaseHelper()
    db.init_conn()

    print("Checking for changes in working directory...")
    # Check changes that are not added or committed
    changed_files = changed_files_current()
    changed_test_files, changed_src_files = split_changes(changed_files, db)

    if len(changed_test_files) > 0 or len(changed_src_files) > 0:

        if os.path.isfile(NEW_DB_FILE_NAME):
            db.swap_cursor()

        # Should new tests be checked here?
        # If so, when to update the database for them
        # so they are not found as new tests in the working directory changes?
        print(f"Found {len(changed_test_files)} changed test files")
        print(f"Found {len(changed_src_files)} changed src files")

        # Get tests from changes in the working directory
        diff_dict_src = file_diff_dict_current(changed_src_files)
        diff_dict_test = file_diff_dict_current(changed_test_files)
        test_set, update_tuple = get_tests_from_changes(
            diff_dict_test, diff_dict_src, changed_test_files, changed_src_files, db
        )

        print(f"Found {len(test_set)} tests to execute")
        if len(test_set) > 0:
            # Run the selected tests without updating database with new line numbers
            print("Running selected tests without updating database...")
            subprocess.run(["tests_selector_run"] + list(test_set))
    else:
        # Check committed changes
        print("Found no changed src files or test files in the working directory")
        print("Comparing current branch to master...")

        changed_files = changed_files_branch()
        changed_test_files, changed_src_files = split_changes(changed_files, db)
        diff_dict_src = file_diff_dict_branch(changed_src_files)
        diff_dict_test = file_diff_dict_branch(changed_test_files)

        # Newly added tests checked only here
        new_tests = read_newly_added_tests(db)

        print(f"Found {len(changed_test_files)} changed test files")
        print(f"Found {len(changed_src_files)} changed src files")
        print(f"Found {len(new_tests)} newly added tests")

        changes_test_set, update_tuple = get_tests_from_changes(
            diff_dict_test, diff_dict_src, changed_test_files, changed_src_files, db
        )
        final_test_set = changes_test_set.union(new_tests)

        print(f"Found {len(final_test_set)} tests to execute")

        run_tests_and_update_db(final_test_set, update_tuple, db)

    db.close_conn()


if __name__ == "__main__":
    main()
