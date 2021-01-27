"""Module for MappingHelper class"""
import os
from typing import Dict, List, NamedTuple, Set, Tuple

from coverage import CoverageData
from _pytest.python import Function

TestrunData = NamedTuple(
    "TestrunData",
    [
        ("pytest_item", Function),
        ("elapsed_time", float),
        ("coverage_data", CoverageData),
        ("found_testfiles", Set[str]),
        ("test_function_lines", Dict[str, Dict[str, Tuple[int, int]]]),
    ],
)

TestFunctionData = NamedTuple(
    "TestFunctionData",
    [
        ("testfile_id", int),
        ("testname", str),
        ("start_line_number", int),
        ("end_line_number", int),
        ("elapsed_time", float),
    ],
)


class MappingHelper:
    """Class to handle mapping database initialization and updating"""

    def __init__(self, connection):
        """Set the connection"""
        self.connection = connection

    @property
    def srcfiles(self) -> List[Tuple[int, str]]:
        """List of source code files (id, path) in the mapping database"""
        return [
            (x[0], x[1])
            for x in self.connection.execute("SELECT id, path FROM src_file").fetchall()
        ]

    @property
    def testfiles(self) -> List[Tuple[int, str]]:
        """List of test code files (id, path) in the mapping database"""
        return [
            (x[0], x[1])
            for x in self.connection.execute(
                "SELECT id, path FROM test_file"
            ).fetchall()
        ]

    @property
    def last_update_hash(self) -> str:
        """Git commit hash of latest database update"""
        return self.connection.execute("SELECT hash FROM last_update_hash").fetchone()[
            0
        ]

    def _delete_lines(self, line_ids, file_id):
        """Remove entries from covered line mapping"""
        entries = [(line_id, file_id) for line_id in line_ids]
        self.connection.executemany(
            "DELETE FROM test_map WHERE line_id == ? AND file_id == ?",
            entries,
        )

    def _add_lines(self, src_id, test_function_id, lines):
        """Add entries to covered line mapping"""
        entries = [(src_id, test_function_id, line) for line in lines]
        self.connection.executemany(
            "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
            entries,
        )

    def _add_srcfile(self, path):
        """Add a covered source code file to mapping"""
        self.connection.execute(
            "INSERT OR IGNORE INTO src_file (path) VALUES (?)", (path,)
        )

    def _get_srcfile(self, path) -> int:
        """Get a source code file id with path"""
        srcfile_id = self.connection.execute(
            "SELECT id FROM src_file WHERE path == ?", (path,)
        ).fetchone()[0]
        return srcfile_id

    def _add_testfile(self, path):
        """Add a test file to mapping"""
        self.connection.execute(
            "INSERT OR IGNORE INTO test_file (path) VALUES (?)", (path,)
        )

    def _get_testfile(self, path) -> int:
        """Get a test code file id with path"""
        testfile_id = self.connection.execute(
            "SELECT id FROM test_file WHERE path == ?", (path,)
        ).fetchone()[0]
        return testfile_id

    def _add_test_function(self, test_function_data):
        """Add a test function to mapping"""
        self.connection.execute(
            """INSERT OR IGNORE
                INTO test_function
                (test_file_id,context,start,end,duration)
                VALUES (?,?,?,?,?)""",
            (
                test_function_data.testfile_id,
                test_function_data.testname,
                test_function_data.start_line_number,
                test_function_data.end_line_number,
                test_function_data.elapsed_time,
            ),
        )

    def _get_test_function(self, testname) -> int:
        """Get a test function id with test name"""
        test_function_id = self.connection.execute(
            "SELECT id FROM test_function WHERE context == ?", (testname,)
        ).fetchone()[0]
        return test_function_id

    def set_last_update_hash(self, commithash):
        """Set the latest database update Git commit hash"""
        self.connection.execute("DELETE FROM last_update_hash")
        self.connection.execute(
            "INSERT INTO last_update_hash VALUES (?)", (commithash,)
        )

    def init_mapping(self):
        """Create the mapping database tables"""
        self.connection.execute("DROP TABLE IF EXISTS test_map")
        self.connection.execute("DROP TABLE IF EXISTS src_file")
        self.connection.execute("DROP TABLE IF EXISTS test_file")
        self.connection.execute("DROP TABLE IF EXISTS test_function")
        self.connection.execute("DROP TABLE IF EXISTS new_tests")
        self.connection.execute("DROP TABLE IF EXISTS last_update_hash")
        self.connection.execute(
            """CREATE TABLE test_map (
                    file_id INTEGER,
                    test_function_id INTEGER,
                    line_id INTEGER,
                    UNIQUE(file_id,test_function_id,line_id))"""
        )
        self.connection.execute(
            "CREATE TABLE src_file (id INTEGER PRIMARY KEY, path TEXT, UNIQUE (path))"
        )
        self.connection.execute(
            "CREATE TABLE test_file (id INTEGER PRIMARY KEY, path TEXT, UNIQUE (path))"
        )
        self.connection.execute(
            """CREATE TABLE test_function (
                                    id INTEGER PRIMARY KEY,
                                    test_file_id INTEGER,
                                    context TEXT,
                                    start INTEGER,
                                    end INTEGER,
                                    duration REAL,
                                    FOREIGN KEY (test_file_id) REFERENCES test_file(id),
                                    UNIQUE (context))"""
        )
        self.connection.execute("CREATE TABLE new_tests (context TEXT)")
        self.connection.execute("CREATE TABLE last_update_hash (hash TEXT)")

    def line_exists(self, file_id, line_number) -> bool:
        """Check whether a specific line number is covered for a source code file"""
        return bool(
            self.connection.execute(
                "SELECT EXISTS(SELECT file_id FROM test_map WHERE file_id = ? AND line_id = ?)",
                (
                    file_id,
                    line_number,
                ),
            ).fetchone()[0]
        )

    def _update_test_function_mapping(self, line_map, file_id):
        """Update test function entries in the mapping database
        by shifting their start and end line numbers
        """
        entries_to_update = self.connection.execute(
            """SELECT id,test_file_id,context,start,end FROM test_function
                WHERE test_file_id = ?""",
            (file_id,),
        ).fetchall()

        self.connection.execute(
            "DELETE FROM test_function WHERE test_file_id = ?", (file_id,)
        )
        updated_entries = [
            (
                x[0],
                x[1],
                x[2],
                line_map[x[3]] if x[3] in line_map else x[3],
                line_map[x[4]] if x[4] in line_map else x[4],
            )
            for x in entries_to_update
        ]
        self.connection.executemany(
            """
                INSERT OR IGNORE
                INTO test_function (id,test_file_id,context,start,end)
                VALUES (?,?,?,?,?)""",
            updated_entries,
        )

    def _update_line_mapping(self, line_map, file_id):
        """Update source code mapping
        by changing the covered line numbers
        according to a new line mapping
        """
        lines = list(line_map.keys())
        sql_params = tuple(lines + ([file_id]))

        entries_to_update = self.connection.execute(
            f"""SELECT file_id,test_function_id,line_id
                FROM test_map WHERE line_id IN ({','.join(['?']*len(lines))}) AND file_id == ?""",
            sql_params,
        ).fetchall()

        self.connection.execute(
            f"""DELETE FROM test_map
            WHERE line_id IN ({','.join(['?']*len(lines))}) AND file_id == ?""",
            sql_params,
        )
        updated_entries = [(x[0], x[1], line_map[x[2]]) for x in entries_to_update]
        self.connection.executemany(
            "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
            updated_entries,
        )

    def save_testrun_data(
        self,
        testrun_data,
    ):
        """Save the coverage information of running a single test function"""
        testfile_path = os.path.relpath(testrun_data.pytest_item.location[0])

        self._add_testfile(testfile_path)
        testfile_id = self._get_testfile(testfile_path)

        testname = testrun_data.pytest_item.nodeid
        test_function_name = testrun_data.pytest_item.originalname

        test_function_data = TestFunctionData(
            testfile_id=testfile_id,
            testname=testname,
            start_line_number=testrun_data.test_function_lines[testfile_path][
                test_function_name
            ][0],
            end_line_number=testrun_data.test_function_lines[testfile_path][
                test_function_name
            ][1],
            elapsed_time=testrun_data.elapsed_time,
        )

        self._add_test_function(test_function_data)
        test_function_id = self._get_test_function(testname)

        for filename in testrun_data.coverage_data.measured_files():
            src_file_path = os.path.relpath(filename, os.getcwd())
            # issue: find a way to get rid of hardcoded mapping conditions
            conditions = [
                "pytest-rts" in filename,
                ("/tmp/" in filename) and ("/tmp/" not in os.getcwd()),
                "/.venv/" in filename,
                src_file_path in testrun_data.found_testfiles,
                src_file_path.endswith("conftest.py"),
                not src_file_path.endswith(".py"),
            ]
            if any(conditions):
                continue

            self._add_srcfile(src_file_path)
            src_id = self._get_srcfile(src_file_path)
            self._add_lines(
                src_id, test_function_id, testrun_data.coverage_data.lines(filename)
            )

    def update_mapping(self, update_data):
        """Remove old data from database and shift existing lines if needed"""

        line_map_test = update_data.new_line_map_test
        changed_lines_src = update_data.changed_lines_src
        line_map_src = update_data.new_line_map_src

        for testfile_id in line_map_test.keys():
            # shift test functions
            self._update_test_function_mapping(line_map_test[testfile_id], testfile_id)
        for srcfile_id in changed_lines_src.keys():
            # delete ran lines of src file mapping to be remapped by coverage collection
            # shift affected lines by correct amount
            self._delete_lines(changed_lines_src[srcfile_id], srcfile_id)
            self._update_line_mapping(line_map_src[srcfile_id], srcfile_id)
