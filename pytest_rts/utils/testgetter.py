"""Module for TestGetter class"""
from typing import Dict, List, Set, Tuple

from pytest_rts.models.test_function import TestFunction
from pytest_rts.models.test_map import TestMap
from pytest_rts.models.new_tests import NewTests
from pytest_rts.utils.common import line_mapping
from pytest_rts.utils.git import get_test_lines_and_update_lines


class TestGetter:
    """Class to query tests and information from the mapping database"""

    def __init__(self, session):
        """Set the connection"""
        self.session = session

    @property
    def existing_tests(self) -> Set[str]:
        """Test function names that exist in the mapping database"""
        return {
            testfunction.name for testfunction in self.session.query(TestFunction.name)
        }

    @property
    def newly_added_tests(self) -> Set[str]:
        """New tests collected but not yet mapped"""
        return {testfunction.name for testfunction in self.session.query(NewTests.name)}

    @property
    def test_function_runtimes(self) -> Dict[str, float]:
        """Dictionary with saved runtimes for each test function"""
        return {
            row.name: row.duration
            for row in self.session.query(TestFunction.name, TestFunction.duration)
        }

    def _get_tests_from_srcfiles(self, changed_lines, file_id) -> List[str]:
        """Query tests from source code files based on changed line numbers"""
        return [
            testfunction.name
            for testfunction in self.session.query(TestFunction.name)
            .join(TestMap)
            .filter(TestMap.line_number.in_(changed_lines), TestMap.file_id == file_id)
        ]

    def _get_tests_from_testfiles(self, changed_lines, file_id) -> List[str]:
        """Query tests from changed test code files based on changed line numbers"""
        tests = []
        for line in changed_lines:
            tests.extend(
                [
                    testfunction.name
                    for testfunction in self.session.query(TestFunction.name)
                    .distinct(TestFunction.name)
                    .filter(
                        TestFunction.test_file_id == file_id,
                        TestFunction.start <= line,
                        TestFunction.end >= line,
                    )
                ]
            )
        return tests

    def tests_from_changed_testfiles(
        self, diff_dict, files
    ) -> Tuple[Set[str], Dict[int, List[int]], Dict[int, Dict[int, int]]]:
        """Calculate test set and update data from changes to a testfile"""
        test_set: Set[str] = set()
        changed_lines_map: Dict[int, List[int]] = {}
        new_line_map: Dict[int, Dict[int, int]] = {}
        for testfile in files:
            changed_lines, updates_to_lines, _ = get_test_lines_and_update_lines(
                diff_dict[testfile.id]
            )

            changed_lines_map[testfile.id] = changed_lines
            new_line_map[testfile.id] = line_mapping(updates_to_lines, testfile.path)

            test_set.update(self._get_tests_from_testfiles(changed_lines, testfile.id))

        return test_set, changed_lines_map, new_line_map

    def tests_from_changed_srcfiles(
        self, diff_dict, files, mappinghelper
    ) -> Tuple[Set[str], Dict[int, List[int]], Dict[int, Dict[int, int]], List[str]]:
        """
        Calculate test set,
        update data
        and warning for untested new lines from changes to a source code file
        """

        test_set: Set[str] = set()
        changed_lines_map: Dict[int, List[int]] = {}
        new_line_map: Dict[int, Dict[int, int]] = {}
        files_to_warn: List[str] = []
        for srcfile in files:
            (
                changed_lines,
                updates_to_lines,
                new_lines,
            ) = get_test_lines_and_update_lines(diff_dict[srcfile.id])

            changed_lines_map[srcfile.id] = changed_lines
            new_line_map[srcfile.id] = line_mapping(updates_to_lines, srcfile.path)

            if not all(
                [
                    mappinghelper.line_exists(srcfile.id, line_number)
                    for line_number in new_lines
                ]
            ):
                files_to_warn.append(srcfile.path)

            test_set.update(self._get_tests_from_srcfiles(changed_lines, srcfile.id))

        return test_set, changed_lines_map, new_line_map, files_to_warn

    def set_newly_added_tests(self, test_set):
        """Store the newly added and collected tests"""
        self.session.bulk_save_objects(
            [NewTests(name=testname) for testname in test_set]
        )

    def delete_newly_added_tests(self):
        """Clear the new tests table"""
        self.session.query(NewTests).delete()
