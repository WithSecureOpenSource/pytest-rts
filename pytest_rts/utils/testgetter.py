"""Module for TestGetter class"""
from typing import Dict, List, Set, Tuple

from sqlalchemy.sql import select

from pytest_rts.utils.tables import (
    test_function_table,
    test_map_table,
    new_tests_table,
)
from pytest_rts.utils.common import line_mapping
from pytest_rts.utils.git import get_test_lines_and_update_lines


class TestGetter:
    """Class to query tests and information from the mapping database"""

    def __init__(self, engine):
        """Set the connection"""
        self.engine = engine
        self.connection = self.engine.connect()

    @property
    def existing_tests(self) -> Set[str]:
        """Test function names that exist in the mapping database"""
        return {
            x[0]
            for x in self.connection.execute(select([test_function_table.c.context]))
        }

    @property
    def newly_added_tests(self) -> Set[str]:
        """New tests collected but not yet mapped"""
        return {
            x[0] for x in self.connection.execute(select([new_tests_table.c.context]))
        }

    @property
    def test_function_runtimes(self) -> Dict[str, float]:
        """Dictionary with saved runtimes for each test function"""
        return {
            x[0]: x[1]
            for x in self.connection.execute(
                select([test_function_table.c.context, test_function_table.c.duration])
            )
        }

    def tests_from_changed_testfiles(
        self, diff_dict, files
    ) -> Tuple[Set[str], Dict[int, List[int]], Dict[int, Dict[int, int]]]:
        """Calculate test set and update data from changes to a testfile"""

        test_set: Set[str] = set()
        changed_lines_map: Dict[int, List[int]] = {}
        new_line_map: Dict[int, Dict[int, int]] = {}
        for testfile in files:
            file_id = testfile[0]
            filename = testfile[1]
            changed_lines, updates_to_lines, _ = get_test_lines_and_update_lines(
                diff_dict[file_id]
            )

            changed_lines_map[file_id] = changed_lines
            new_line_map[file_id] = line_mapping(updates_to_lines, filename)

            test_set.update(self._get_tests_from_testfiles(changed_lines, file_id))

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
            file_id = srcfile[0]
            filename = srcfile[1]
            (
                changed_lines,
                updates_to_lines,
                new_lines,
            ) = get_test_lines_and_update_lines(diff_dict[file_id])

            changed_lines_map[file_id] = changed_lines
            new_line_map[file_id] = line_mapping(updates_to_lines, filename)

            if not all(
                mappinghelper.line_exists(file_id, line_number)
                for line_number in new_lines
            ):
                files_to_warn.append(filename)

            test_set.update(self._get_tests_from_srcfiles(changed_lines, file_id))

        return test_set, changed_lines_map, new_line_map, files_to_warn

    def set_newly_added_tests(self, test_set):
        """Store the newly added and collected tests"""
        if not test_set:
            return
        self.connection.execute(
            new_tests_table.insert(None), [{"context": x} for x in test_set]
        )

    def delete_newly_added_tests(self):
        """Clear the new tests table"""
        self.connection.execute(new_tests_table.delete(None))

    def _get_tests_from_srcfiles(self, changed_lines, file_id) -> List[str]:
        """Query tests from source code files based on changed line numbers"""
        tests: List[str] = []
        for line in changed_lines:
            tests.extend(
                x[0]
                for x in self.connection.execute(
                    select([test_function_table.c.context])
                    .where(test_map_table.c.line_id == line)
                    .where(test_map_table.c.file_id == file_id)
                    .select_from(test_function_table.join(test_map_table))
                )
            )

        return tests

    def _get_tests_from_testfiles(self, changed_lines, file_id) -> List[str]:
        """Query tests from changed test code files based on changed line numbers"""
        tests: List[str] = []
        for line in changed_lines:
            tests.extend(
                x[0]
                for x in self.connection.execute(
                    select([test_function_table.c.context])
                    .where(test_function_table.c.id == file_id)
                    .where(test_function_table.c.start <= line)
                    .where(test_function_table.c.end >= line)
                )
            )
        return tests
