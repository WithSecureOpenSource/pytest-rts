"""This module contains fuctions for test selecting operations"""
from typing import List, Set

from coverage import CoverageData
from _pytest.nodes import Item

from pytest_rts.utils.git import (
    commit_exists,
    get_git_repo,
    get_changed_lines,
    get_changed_files_workdir,
    get_changed_files_committed_and_workdir,
    get_file_diff_data_workdir,
    get_file_diff_data_committed_and_workdir,
)


def filter_pytest_items(
    pytest_items: List[Item], existing_tests: Set[str], tests_from_changes: Set[str]
) -> List[Item]:
    """Select pytest items if they are new and not marked as skipped"""
    return list(
        filter(
            lambda item: (item.nodeid in tests_from_changes)
            or (
                item.nodeid not in existing_tests
                and not item.get_closest_marker("skipif")
                and not item.get_closest_marker("skip")
            ),
            pytest_items,
        )
    )


def get_existing_tests(coverage_file_path: str) -> Set[str]:
    """Read all the test function names from the coverage file.
    pytest-cov creates the coverage file and adds a section at the
    end of each testname which need to be stripped.
    """
    coverage_data = CoverageData(coverage_file_path)
    coverage_data.read()
    return {
        strip_pytest_cov_testname(testname)
        for testname in coverage_data.measured_contexts()
    }


def get_tests_from_changes(
    commithash_to_compare: str, coverage_file_path: str
) -> Set[str]:
    """Returns the test set from Git changes.
    The given commithash is compared to the current working copy
    to extract Git diffs, if the provided commithash exists in the repo.
    Otherwise only changes in the git working directory are considered.
    """
    repo = get_git_repo()
    if commit_exists(commithash_to_compare, repo):
        file_diffs = {
            file_path: get_file_diff_data_committed_and_workdir(
                repo, file_path, commithash_to_compare
            )
            for file_path in get_changed_files_committed_and_workdir(
                repo, commithash_to_compare
            )
        }
    else:
        file_diffs = {
            file_path: get_file_diff_data_workdir(repo, file_path)
            for file_path in get_changed_files_workdir(repo)
        }
    coverage_data = CoverageData(coverage_file_path)
    coverage_data.read()

    tests: Set[str] = set()
    for changed_file in file_diffs:

        contexts = coverage_data.contexts_by_lineno(changed_file)
        if not contexts:
            continue

        changed_lines_with_tests = intersect_with_surroundings(
            get_changed_lines(file_diffs[changed_file]),
            contexts.keys()
        )

        tests.update(
            strip_pytest_cov_testname(testname)
            for line in changed_lines_with_tests
            for testname in contexts[line]
        )

    return tests


def intersect_with_surroundings(changed_lines: Set[int], mapped_lines: Set[int]) -> Set[int]:
    """
    Finds lines existing in both changed_lines and mapped_lines.
    For lines that exist in changed_lines but not in mapped_lines
    looks for the closest mapped lines from left and right
    hand sides - mapped lines which surround changed line.

    Example:
        changed_lines | 1       5             21    30
        mapped_lines  |    2 3    10 11 12 20 21 22
        result        |    2 3    10          21 22

    Algorithm could be improved. See conversation:
    https://github.com/F-Secure/pytest-rts/pull/103#pullrequestreview-625312058
    """
    mapped = changed_lines.intersection(mapped_lines)
    unmapped = changed_lines.difference(mapped)

    mapped_lines_sorted = sorted(mapped_lines)
    for line in unmapped:
        left = None
        right = None
        for mapped_line in mapped_lines_sorted:
            if mapped_line < line:
                left = mapped_line
            if mapped_line > line:
                right = mapped_line
                break
        if left is not None:
            mapped.add(left)
        if right is not None:
            mapped.add(right)
    return mapped


def strip_pytest_cov_testname(testname: str) -> str:
    """Strip ends of pytest-cov produced testnames"""
    if testname.endswith("|teardown"):
        return testname[:-9]
    if testname.endswith("|setup"):
        return testname[:-6]
    if testname.endswith("|run"):
        return testname[:-4]
    return testname
