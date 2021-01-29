import sqlite3
import subprocess
from pytest_rts.plugin import DB_FILE_NAME
from pytest_rts.utils.common import run_new_test_collection
from pytest_rts.utils.selection import (
    get_tests_and_data_committed,
    get_tests_and_data_current,
)
from pytest_rts.utils.mappinghelper import MappingHelper
from pytest_rts.utils.testgetter import TestGetter


class TestHelper:
    def get_mapping_id_from_filename(self, filename, is_srcfile):
        if is_srcfile:
            sql = "SELECT id FROM src_file WHERE path = ?"
        else:
            sql = "SELECT id from test_file WHERE path = ?"

        conn = sqlite3.connect(DB_FILE_NAME)
        file_id = conn.execute(sql, (filename,)).fetchone()[0]
        conn.close()
        return file_id

    def get_mapping_lines_for_srcfile(self, src_file_id):
        conn = sqlite3.connect(DB_FILE_NAME)
        lines = [
            x[0]
            for x in conn.execute(
                "SELECT line_id FROM test_map WHERE file_id = ?", (src_file_id,)
            ).fetchall()
        ]
        conn.close()
        return lines

    def get_tests_from_tool_current(self):
        conn = sqlite3.connect(DB_FILE_NAME)
        mappinghelper = MappingHelper(conn)
        testgetter = TestGetter(conn)
        change_data = get_tests_and_data_current(mappinghelper, testgetter)
        conn.close()
        return change_data.test_set

    def get_tests_from_tool_committed(self):
        conn = sqlite3.connect(DB_FILE_NAME)
        mappinghelper = MappingHelper(conn)
        testgetter = TestGetter(conn)
        change_data = get_tests_and_data_committed(
            mappinghelper,
            testgetter,
        )
        conn.close()
        return change_data.test_set

    def get_newly_added_tests_from_tool(self):
        run_new_test_collection()
        conn = sqlite3.connect(DB_FILE_NAME)
        testgetter = TestGetter(conn)
        new_tests = testgetter.newly_added_tests
        conn.close()
        return new_tests

    def new_test_exists_in_mapping_db(self, testname):
        conn = sqlite3.connect(DB_FILE_NAME)
        sql = "SELECT EXISTS(SELECT id FROM test_function WHERE context = ?)"
        exists = bool(conn.execute(sql, (testname,)).fetchone()[0])
        conn.close()
        return exists

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
