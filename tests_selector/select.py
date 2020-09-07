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
    COVERAGE_CONF_FILE_NAME,
    DB_FILE_NAME,
)
from tests_selector.utils.git import (
    changed_files_current,
    changed_files_branch,
    get_current_hash,
)
from tests_selector.utils.db import (
    save_last_hash,
    get_last_hash,
)


def get_tests_from_changes(diff_dict_test, diff_dict_src, testfiles, srcfiles):
    (
        src_test_set,
        src_changed_lines_dict,
        src_new_line_map_dict,
    ) = tests_from_changed_srcfiles(diff_dict_src, srcfiles)

    (
        test_test_set,
        test_changed_lines_dict,
        test_new_line_map_dict,
    ) = tests_from_changed_testfiles(diff_dict_test, testfiles)

    test_set = test_test_set.union(src_test_set)

    update_tuple = (
        test_changed_lines_dict,
        test_new_line_map_dict,
        src_changed_lines_dict,
        src_new_line_map_dict,
    )
    return test_set, update_tuple


def main():
    if not os.path.isfile(COVERAGE_CONF_FILE_NAME) or not os.path.isfile(DB_FILE_NAME):
        print("Run tests_selector_init first")
        exit(1)

    print("Checking for changes in working directory...")
    # Check changes that are not added or committed
    changed_files = changed_files_current()
    changed_test_files, changed_src_files = split_changes(changed_files)

    if len(changed_test_files) > 0 or len(changed_src_files) > 0:
        print(f"Found {len(changed_test_files)} changed test files")
        print(f"Found {len(changed_src_files)} changed src files")

        # Get tests from changes in the working directory
        diff_dict_src = file_diff_dict_current(changed_src_files)
        diff_dict_test = file_diff_dict_current(changed_test_files)
        test_set, update_tuple = get_tests_from_changes(
            diff_dict_test, diff_dict_src, changed_test_files, changed_src_files
        )
        # Update tuple (lines to delete and new lines) not used here

        print(f"Found {len(test_set)} tests to execute")
        if len(test_set) > 0:
            # Run the selected tests without updating database with new line numbers
            print("Running selected tests without updating database...")
            subprocess.run(["tests_selector_run"] + list(test_set))
    else:
        # Check committed changes
        print("Found no changed src files or test files in the working directory")
        print("Comparing current branch to master...")

        if get_last_hash() == get_current_hash():
            print("Tests already ran and database updated for this comparison")
            exit()

        changed_files = changed_files_branch()
        changed_test_files, changed_src_files = split_changes(changed_files)
        diff_dict_src = file_diff_dict_branch(changed_src_files)
        diff_dict_test = file_diff_dict_branch(changed_test_files)

        # Newly added tests checked only here
        new_tests = read_newly_added_tests()

        print(f"Found {len(changed_test_files)} changed test files")
        print(f"Found {len(changed_src_files)} changed src files")
        print(f"Found {len(new_tests)} newly added tests")

        changes_test_set, update_tuple = get_tests_from_changes(
            diff_dict_test, diff_dict_src, changed_test_files, changed_src_files
        )
        final_test_set = changes_test_set.union(new_tests)

        print(f"Found {len(final_test_set)} tests to execute")
        if len(final_test_set) > 0:
            print("Running selected tests and updating database...")
            save_last_hash(get_current_hash())
            run_tests_and_update_db(final_test_set, update_tuple)


if __name__ == "__main__":
    main()
