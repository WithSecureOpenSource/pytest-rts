"""Module for MappingHelper class"""
import os
from typing import Dict, List, NamedTuple, Set, Tuple

from coverage import CoverageData
from _pytest.python import Function

from pytest_rts.models.source_file import SourceFile
from pytest_rts.models.test_file import TestFile
from pytest_rts.models.test_function import TestFunction
from pytest_rts.models.test_map import TestMap
from pytest_rts.models.last_update_hash import LastUpdateHash


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

    def __init__(self, session):
        """Set the connection"""
        self.session = session
        self.saved_srcfiles = {}
        self.saved_testfiles = {}

    @property
    def srcfiles(self) -> List[SourceFile]:
        """List of source code files (id, path) in the mapping database"""
        return self.session.query(SourceFile).all()

    @property
    def testfiles(self) -> List[TestFile]:
        """List of test code files (id, path) in the mapping database"""
        return self.session.query(TestFile).all()

    @property
    def last_update_hash(self) -> str:
        """Git commit hash of latest database update"""
        return self.session.query(LastUpdateHash).first().commithash

    def split_changes(self, changed_files) -> Tuple[List[TestFile], List[SourceFile]]:
        """Split given changed files into changed testfiles
        and source code files by comparing paths
        """
        changed_testfiles = [x for x in self.testfiles if x.path in changed_files]
        changed_srcfiles = [x for x in self.srcfiles if x.path in changed_files]
        return changed_testfiles, changed_srcfiles

    def _delete_lines(self, lines, file_id):
        """Remove entries from covered line mapping"""
        for line in lines:
            self.session.query(TestMap).filter(
                TestMap.file_id == file_id, TestMap.line_number == line
            ).delete()

    def _add_lines(self, file_id, test_function_id, lines):
        self.session.bulk_insert_mappings(
            TestMap,
            [
                dict(
                    file_id=file_id, test_function_id=test_function_id, line_number=line
                )
                for line in lines
            ],
        )

    def _add_srcfile(self, path):
        """Add a covered source code file to mapping"""
        self.session.add(SourceFile(path=path))

    def _get_srcfile(self, path) -> int:
        """Get a source code file id with path"""
        return self.session.query(SourceFile).filter_by(path=path).first().id

    def _add_testfile(self, path):
        """Add a test file to mapping"""
        self.session.add(TestFile(path=path))

    def _get_testfile(self, path) -> int:
        """Get a test code file id with path"""
        return self.session.query(TestFile).filter_by(path=path).first().id

    def _add_test_function(self, test_function_data):
        """Add a test function to mapping"""
        self.session.add(
            TestFunction(
                test_file_id=test_function_data.testfile_id,
                name=test_function_data.testname,
                start=test_function_data.start_line_number,
                end=test_function_data.end_line_number,
                duration=test_function_data.elapsed_time,
            )
        )

    def _get_test_function(self, testname) -> int:
        """Get a test function id with test name"""
        return self.session.query(TestFunction).filter_by(name=testname).first().id

    def set_last_update_hash(self, commithash):
        """Set the latest database update Git commit hash"""
        self.session.query(LastUpdateHash).delete()
        self.session.add(LastUpdateHash(commithash=commithash))

    def line_exists(self, file_id, line_number) -> bool:
        """Check whether a specific line number is covered for a source code file"""
        return bool(
            self.session.query(TestMap)
            .filter_by(file_id=file_id, line_number=line_number)
            .first()
        )

    def _update_test_function_mapping(self, line_map, file_id):
        """Update test function entries in the mapping database
        by shifting their start and end line numbers
        """
        entries_to_update = (
            self.session.query(TestFunction).filter_by(test_file_id=file_id).all()
        )
        for testfunction in entries_to_update:
            testfunction.start = (
                line_map[testfunction.start]
                if testfunction.start in line_map
                else testfunction.start
            )
            testfunction.end = (
                line_map[testfunction.end]
                if testfunction.end in line_map
                else testfunction.end
            )

    def _update_line_mapping(self, line_map, file_id):
        """Update source code mapping
        by changing the covered line numbers
        according to a new line mapping
        """
        entries_to_update = []
        for line in line_map.keys():
            entries_to_update.extend(
                self.session.query(TestMap).filter_by(file_id=file_id, line_number=line)
            )

        for entry in entries_to_update:
            entry.line_number = line_map[entry.line_number]

        self.session.expunge_all()

        for line in line_map.keys():
            self.session.query(TestMap).filter_by(
                file_id=file_id, line_number=line
            ).delete()

        self.session.bulk_insert_mappings(
            TestMap,
            [
                dict(
                    file_id=entry.file_id,
                    test_function_id=entry.test_function_id,
                    line_number=entry.line_number,
                )
                for entry in entries_to_update
            ],
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
                src_id,
                test_function_id,
                testrun_data.coverage_data.lines(filename),
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
