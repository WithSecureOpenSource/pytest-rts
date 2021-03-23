"""This module contains fuctions for test selecting operations"""
from typing import Dict, List, Set

from coverage import CoverageData
from _pytest.nodes import Item

from pytest_rts.utils.git import (
    get_git_repo,
    get_changed_lines,
    get_changed_files_current,
    get_file_diff_dict_current,
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
    file_diffs: Dict[str, str], coverage_file_path: str
) -> Set[str]:
    """Returns the test set from given Git diffs"""
    coverage_data = CoverageData(coverage_file_path)
    coverage_data.read()

    tests: Set[str] = set()
    for changed_file in file_diffs:

        contexts = coverage_data.contexts_by_lineno(changed_file)
        if not contexts:
            continue

        changed_lines_with_tests = get_changed_lines(
            file_diffs[changed_file]
        ).intersection(contexts.keys())

        tests.update(
            strip_pytest_cov_testname(testname)
            for line in changed_lines_with_tests
            for testname in contexts[line]
        )

    return tests


def get_tests_current(coverage_file_path: str) -> Set[str]:
    """Returns the test set from working directory changes"""
    repo = get_git_repo()
    changed_files = get_changed_files_current(repo)
    file_diffs = get_file_diff_dict_current(repo, changed_files)
    return get_tests_from_changes(file_diffs, coverage_file_path)


def strip_pytest_cov_testname(testname: str) -> str:
    """Strip ends of pytest-cov produced testnames"""
    if testname.endswith("|teardown"):
        return testname[:-9]
    if testname.endswith("|setup"):
        return testname[:-6]
    if testname.endswith("|run"):
        return testname[:-4]
    return testname
