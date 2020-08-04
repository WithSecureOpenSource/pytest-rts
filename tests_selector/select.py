import subprocess
from tests_selector.helper import (
    changed_files_current,
    split_changes,
    tests_from_changed_sourcefiles_current,
    tests_from_changed_testfiles_current,
    read_newly_added_tests,
)

PROJECT_FOLDER = "."


def get_tests_from_current_changes(changed_test_files, changed_src_files):
    (
        src_test_set,
        src_changed_lines_dict,
        src_new_line_map_dict,
    ) = tests_from_changed_sourcefiles_current(changed_src_files, PROJECT_FOLDER)

    (
        test_test_set,
        test_changed_lines_dict,
        test_new_line_map_dict,
    ) = tests_from_changed_testfiles_current(changed_test_files, PROJECT_FOLDER)

    test_set = test_test_set.union(src_test_set)

    update_tuple = (
        test_changed_lines_dict,
        test_new_line_map_dict,
        src_changed_lines_dict,
        src_new_line_map_dict,
    )
    return test_set, update_tuple


def run():
    changed_files = changed_files_current(PROJECT_FOLDER)
    changed_test_files, changed_src_files = split_changes(changed_files)
    new_tests = read_newly_added_tests(PROJECT_FOLDER)
    print(f"found {len(changed_test_files)} changed test files")
    print(f"found {len(changed_src_files)} changed src files")
    print(f"found {len(new_tests)} newly added tests")

    changes_test_set, update_tuple = get_tests_from_current_changes(
        changed_test_files, changed_src_files
    )
    final_test_set = changes_test_set.union(new_tests)
    print(f"found {len(final_test_set)} tests")

    if len(final_test_set) > 0:
        # run_tests_and_update_db(final_test_set, update_tuple,PROJECT_FOLDER)
        # now the database is updated with new mapping but git diff still remains the same
        # whats the best way to handle that?
        subprocess.run(["tests_selector_run", "."] + list(final_test_set))


def main():
    run()


if __name__ == "__main__":
    main()
