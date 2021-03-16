"""This module contains fuctions for test selecting operations"""
import glob
from typing import Dict, List, Set, Tuple

from coverage import CoverageData
from _pytest.nodes import Item

from pytest_rts.utils.git import (
    changed_files_current,
    changed_files_between_commits,
    file_diff_data_between_commits,
    file_diff_data_current,
    get_current_head_hash,
    get_changed_lines,
)

DB_FILE_PREFIX = "rts-coverage-file"


def file_diff_dict_current(files) -> Dict[str, str]:
    """Returns a dictionary with file id as key and git diff as value"""
    return {file_path: file_diff_data_current(file_path) for file_path in files}


def file_diff_dict_between_commits(files, commithash1, commithash2) -> Dict[int, str]:
    """Returns a dictionary with file id as key and git diff as value"""
    return {
        file_path: file_diff_data_between_commits(file_path, commithash1, commithash2)
        for file_path in files
    }


def filter_and_sort_pytest_items(test_set, pytest_items, existing_tests) -> List[Item]:
    """Selected pytest items based on found tests
    or if they are new and not marked as skipped
    """
    return list(
        filter(
            lambda item: (item.nodeid in test_set)
            or (
                item.nodeid not in existing_tests
                and not item.get_closest_marker("skipif")
                and not item.get_closest_marker("skip")
            ),
            pytest_items,
        )
    )


def get_existing_tests():
    """Read all the test function names from the coverage file"""
    coverage_data = CoverageData(get_coverage_file_filename())
    coverage_data.read()
    return coverage_data.measured_contexts()


def get_tests_from_changes(file_diffs) -> List[str]:
    """Returns the test set from given Git diffs"""
    coverage_data = CoverageData(get_coverage_file_filename())
    coverage_data.read()

    tests = []
    for changed_file in file_diffs:
        changed_lines = get_changed_lines(file_diffs[changed_file])
        for line_number in coverage_data.contexts_by_lineno(changed_file):
            if line_number in changed_lines:
                tests.extend(
                    coverage_data.contexts_by_lineno(changed_file)[line_number]
                )
    return tests


def get_tests_current() -> List[str]:
    """Returns the test set from working directory changes"""
    changed_files = changed_files_current()
    file_diffs = file_diff_dict_current(changed_files)
    return get_tests_from_changes(file_diffs)


def get_tests_committed(previous_hash) -> List[str]:
    """Compares current git HEAD has to previous update state commit hash
    and returns the test set
    """
    current_hash = get_current_head_hash()
    changed_files = changed_files_between_commits(previous_hash, current_hash)
    file_diffs = file_diff_dict_between_commits(
        changed_files, previous_hash, current_hash
    )
    return get_tests_from_changes(file_diffs)


def get_coverage_file_filename() -> str:
    """Return the coverage file filename by matching the prefix.
    The part after the . symbol contains the commithash where it was created.
    """
    possible_files = glob.glob(f"{DB_FILE_PREFIX}.*")
    return possible_files[0] if possible_files else ""
