"""Module for TestGetter class"""
from typing import Dict, List, Set


class TestGetter:
    """Class to query tests and information from the mapping database"""

    def __init__(self, connection):
        """Set the connection"""
        self.connection = connection

    @property
    def existing_tests(self) -> Set[str]:
        """Test function names that exist in the mapping database"""
        return {
            x[0]
            for x in self.connection.execute(
                "SELECT context FROM test_function"
            ).fetchall()
        }

    @property
    def newly_added_tests(self) -> Set[str]:
        """New tests collected but not yet mapped"""
        return {
            x[0]
            for x in self.connection.execute("SELECT context FROM new_tests").fetchall()
        }

    @property
    def test_function_runtimes(self) -> Dict[str, float]:
        """Dictionary with saved runtimes for each test function"""
        return {
            x[0]: x[1]
            for x in self.connection.execute(
                "SELECT context, duration FROM test_function"
            ).fetchall()
        }

    def get_tests_from_srcfiles(self, changed_lines, file_id) -> List[str]:
        """Query tests from source code files based on changed line numbers"""
        return [
            line[0]
            for line in self.connection.execute(
                f""" SELECT DISTINCT context
                    FROM test_function
                    JOIN test_map ON test_function.id == test_map.test_function_id
                    WHERE test_map.line_id IN ({','.join(['?']*len(changed_lines))})
                    AND test_map.file_id = ?  """,
                changed_lines + [file_id],
            )
        ]

    def get_tests_from_testfiles(self, changed_lines, file_id) -> List[str]:
        """Query tests from changed test code files based on changed line numbers"""
        tests = []
        for line_number in changed_lines:
            tests.extend(
                [
                    line[0]
                    for line in self.connection.execute(
                        """ SELECT DISTINCT context
                            FROM test_function
                            WHERE test_file_id = ?
                            AND start <= ?
                            AND end >= ?""",
                        (file_id, line_number, line_number),
                    )
                ]
            )

        return tests

    def set_newly_added_tests(self, test_set):
        """Store the newly added and collected tests"""
        self.connection.executemany(
            "INSERT INTO new_tests (context) VALUES (?)", [(test,) for test in test_set]
        )

    def delete_newly_added_tests(self):
        """Clear the new tests table"""
        self.connection.execute("DELETE FROM new_tests")
