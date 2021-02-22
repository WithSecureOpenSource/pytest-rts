"""Module for MappingHelper class"""
import os
from typing import Dict, List, NamedTuple, Set, Tuple

from coverage import CoverageData
from sqlalchemy.sql import select
from _pytest.python import Function

from pytest_rts.utils.tables import (
    src_file_table,
    test_file_table,
    test_function_table,
    test_map_table,
    last_update_hash_table,
    metadata,
)

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

    def __init__(self, engine):
        """Set the connection"""
        self.engine = engine
        self.connection = self.engine.connect()
        self.transaction = None
        self.insert_prefix = "OR IGNORE"

        metadata.create_all(self.engine)

        self.saved_testfiles = {x[1]: x[0] for x in self.testfiles}
        self.saved_srcfiles = {x[1]: x[0] for x in self.srcfiles}
        self.saved_testfunctions = self._saved_testfunctions()

    @property
    def srcfiles(self) -> List[Tuple[int, str]]:
        """List of source code files (id, path) in the mapping database"""
        return [
            (x[0], x[1])
            for x in self.connection.execute(
                select([src_file_table.c.id, src_file_table.c.path])
            )
        ]

    @property
    def testfiles(self) -> List[Tuple[int, str]]:
        """List of test code files (id, path) in the mapping database"""
        return [
            (x[0], x[1])
            for x in self.connection.execute(
                select([test_file_table.c.id, test_file_table.c.path])
            )
        ]

    @property
    def last_update_hash(self) -> str:
        """Git commit hash of latest database update"""
        return self.connection.execute(
            select([last_update_hash_table.c.hash])
        ).fetchone()[0]

    def save_testrun_data(
        self,
        testrun_data,
    ):
        """Save the coverage information of running a single test function"""

        testfile_path = os.path.relpath(testrun_data.pytest_item.location[0])
        if testfile_path not in self.saved_testfiles:
            self._add_testfile(testfile_path)

        testfile_id = self.saved_testfiles[testfile_path]

        testname = testrun_data.pytest_item.nodeid
        if testname not in self.saved_testfunctions:
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
        test_function_id = self.saved_testfunctions[testname]

        for filename in testrun_data.coverage_data.measured_files():
            if not testrun_data.coverage_data.lines(filename):
                continue
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

            if src_file_path not in self.saved_srcfiles:
                self._add_srcfile(src_file_path)
            src_id = self.saved_srcfiles[src_file_path]
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

    def split_changes(
        self, changed_files
    ) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]]]:
        """Split given changed files into
        changed testfiles and source code files by comparing paths
        """
        changed_testfiles = [x for x in self.testfiles if x[1] in changed_files]
        changed_srcfiles = [x for x in self.srcfiles if x[1] in changed_files]
        return changed_testfiles, changed_srcfiles

    def start_transaction(self):
        """Start a transaction for adding testrun data"""
        self.transaction = self.connection.begin()

    def end_transaction(self):
        """Commit and end a transaction"""
        self.transaction.commit()
        self.transaction = None

    def set_last_update_hash(self, commithash):
        """Set the latest database update Git commit hash"""
        self.connection.execute(last_update_hash_table.delete(None))
        self.connection.execute(
            last_update_hash_table.insert(None).values(hash=commithash)
        )

    def line_exists(self, file_id, line_number) -> bool:
        """Check whether a specific line number is covered for a source code file"""
        existing_line = self.connection.execute(
            select([test_map_table])
            .where(test_map_table.c.file_id == file_id)
            .where(test_map_table.c.line_id == line_number)
        ).fetchone()
        return not existing_line is None

    def _saved_testfunctions(self) -> Dict[str, int]:
        """Dictionary for test function id's based on test function name"""
        return {
            x[0]: x[1]
            for x in self.connection.execute(
                select([test_function_table.c.context, test_function_table.c.id])
            )
        }

    def _delete_lines(self, line_ids, file_id):
        """Remove entries from covered line mapping"""
        with self.connection.begin():
            for line in line_ids:
                self.connection.execute(
                    test_map_table.delete(None)
                    .where(test_map_table.c.line_id == line)
                    .where(test_map_table.c.file_id == file_id)
                )

    def _add_lines(self, src_id, test_function_id, lines):
        """Add entries to covered line mapping"""
        self.connection.execute(
            test_map_table.insert(None).prefix_with(self.insert_prefix),
            [
                {
                    "file_id": src_id,
                    "test_function_id": test_function_id,
                    "line_id": line,
                }
                for line in lines
            ],
        )

    def _add_srcfile(self, path):
        """Add a covered source code file to mapping"""
        result = self.connection.execute(
            src_file_table.insert(None)
            .values(path=path)
            .prefix_with(self.insert_prefix)
        )
        self.saved_srcfiles[path] = result.inserted_primary_key[0]

    def _add_testfile(self, path):
        """Add a test file to mapping"""
        result = self.connection.execute(
            test_file_table.insert(None)
            .values(path=path)
            .prefix_with(self.insert_prefix)
        )
        self.saved_testfiles[path] = result.inserted_primary_key[0]

    def _add_test_function(self, test_function_data):
        """Add a test function to mapping"""
        result = self.connection.execute(
            test_function_table.insert(None)
            .values(
                test_file_id=test_function_data.testfile_id,
                context=test_function_data.testname,
                start=test_function_data.start_line_number,
                end=test_function_data.end_line_number,
                duration=test_function_data.elapsed_time,
            )
            .prefix_with(self.insert_prefix)
        )
        self.saved_testfunctions[
            test_function_data.testname
        ] = result.inserted_primary_key[0]

    def _update_test_function_mapping(self, line_map, file_id):
        """Update test function entries in the mapping database
        by shifting their start and end line numbers
        """
        with self.connection.begin():
            entries_to_update = [
                {
                    "id": x[0],
                    "test_file_id": x[1],
                    "name": x[2],
                    "start": line_map[x[3]] if x[3] in line_map else x[3],
                    "end": line_map[x[4]] if x[4] in line_map else x[4],
                    "duration": x[5],
                }
                for x in self.connection.execute(
                    select(
                        [
                            test_function_table.c.id,
                            test_function_table.c.test_file_id,
                            test_function_table.c.context,
                            test_function_table.c.start,
                            test_function_table.c.end,
                            test_function_table.c.duration,
                        ]
                    ).where(test_function_table.c.id == file_id)
                )
            ]

            self.connection.execute(
                test_function_table.delete(None).where(
                    test_function_table.c.id == file_id
                )
            )

            self.connection.execute(
                test_function_table.insert(None).prefix_with(self.insert_prefix),
                entries_to_update,
            )

    def _update_line_mapping(self, line_map, file_id):
        """Update source code mapping
        by changing the covered line numbers
        according to a new line mapping
        """
        with self.connection.begin():
            entries_to_update = []
            for line in line_map.keys():
                entries_to_update.extend(
                    {
                        "file_id": x[0],
                        "test_function_id": x[1],
                        "line_id": line_map[x[2]],
                    }
                    for x in self.connection.execute(
                        select(
                            [
                                test_map_table.c.file_id,
                                test_map_table.c.test_function_id,
                                test_map_table.c.line_id,
                            ]
                        )
                        .where(test_map_table.c.file_id == file_id)
                        .where(test_map_table.c.line_id == line)
                    )
                )

            for line in line_map.keys():
                self.connection.execute(
                    test_map_table.delete(None)
                    .where(test_map_table.c.file_id == file_id)
                    .where(test_map_table.c.line_id == line)
                )

            self.connection.execute(
                test_map_table.insert(None).prefix_with(self.insert_prefix),
                entries_to_update,
            )
