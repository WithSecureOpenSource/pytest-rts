import subprocess

from pytest_rts.utils.common import run_new_test_collection
from pytest_rts.utils.mappinghelper import MappingHelper
from pytest_rts.utils.selection import (
    get_tests_and_data_committed,
    get_tests_and_data_current,
)
from pytest_rts.tests.session_wrapper import with_session
from pytest_rts.utils.testgetter import TestGetter
from pytest_rts.models.test_map import TestMap
from pytest_rts.models.test_function import TestFunction


class TestHelper:
    @with_session
    def get_mapping_id_for_srcfile(self, path, session=None):
        return MappingHelper(session)._get_srcfile(path)

    @with_session
    def get_mapping_id_for_test(self, path, session=None):
        return MappingHelper(session)._get_testfile(path)

    @with_session
    def get_mapping_lines_for_srcfile(self, src_file_id, session=None):
        return [
            line_map.line_number
            for line_map in session.query(TestMap.line_number).filter(
                TestMap.file_id == src_file_id
            )
        ]

    @with_session
    def get_tests_from_tool_current(self, session=None):
        mappinghelper = MappingHelper(session)
        testgetter = TestGetter(session)
        change_data = get_tests_and_data_current(mappinghelper, testgetter)
        return change_data.test_set

    @with_session
    def get_tests_from_tool_committed(self, session=None):
        mappinghelper = MappingHelper(session)
        testgetter = TestGetter(session)
        change_data = get_tests_and_data_committed(
            mappinghelper,
            testgetter,
        )
        return change_data.test_set

    @with_session
    def get_newly_added_tests_from_tool(self, session=None):
        run_new_test_collection()
        testgetter = TestGetter(session)
        new_tests = testgetter.newly_added_tests
        return new_tests

    @with_session
    def new_test_exists_in_mapping_db(self, testname, session=None):
        return bool(
            session.query(TestFunction).filter(TestFunction.name == testname).first()
        )

    def change_file(self, change_path, file_path):
        subprocess.run(
            ["cp", "-f", change_path, file_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def commit_change(self, filename, message):
        subprocess.run(
            ["git", "add", filename],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def run_tool(self):
        subprocess.run(["pytest", "--rts"], check=True)

    def squash_commits(self, n, new_message):
        subprocess.run(["git", "reset", "--soft", f"HEAD~{n}"], check=True)
        subprocess.run(["git", "commit", "-m", new_message], check=True)

    def checkout_new_branch(self, branchname="new-branch"):
        subprocess.run(
            ["git", "checkout", "-b", branchname],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def checkout_branch(self, branchname):
        subprocess.run(
            ["git", "checkout", branchname],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def delete_branch(self, branchname):
        subprocess.run(
            ["git", "branch", "-D", branchname],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
