"""This module contains fuctions for test selecting operations"""
from typing import List, Set

from coverage import CoverageData
from _pytest.nodes import Item


def filter_pytest_items(
    pytest_items: List[Item], existing_tests: Set[str]
) -> List[Item]:
    """Select pytest items if they are new and not marked as skipped"""
    return list(
        filter(
            lambda item: item.nodeid not in existing_tests
            and not item.get_closest_marker("skipif")
            and not item.get_closest_marker("skip"),
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


def strip_pytest_cov_testname(testname: str) -> str:
    """Strip ends of pytest-cov produced testnames"""
    if testname.endswith("|teardown"):
        return testname[:-9]
    if testname.endswith("|setup"):
        return testname[:-6]
    if testname.endswith("|run"):
        return testname[:-4]
    return testname
