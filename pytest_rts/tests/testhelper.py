import sqlite3
import subprocess
from pytest_rts.utils.db import DatabaseHelper, DB_FILE_NAME
from pytest_rts.select import (
    get_tests_and_data_committed,
    get_tests_and_data_current,
)
from pytest_rts.utils.common import read_newly_added_tests


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
        db = DatabaseHelper()
        db.init_conn()
        change_data = get_tests_and_data_current(db)
        db.close_conn()
        return change_data.test_set

    def get_tests_from_tool_committed(self):
        db = DatabaseHelper()
        db.init_conn()
        change_data = get_tests_and_data_committed(db)
        db.close_conn()
        return change_data.test_set

    def get_all_tests_for_srcfile(self, src_file_id):
        db = DatabaseHelper()
        db.init_conn()
        all_tests = db.query_all_tests_srcfile(src_file_id)
        db.close_conn()
        return all_tests

    def get_newly_added_tests_from_tool(self):
        db = DatabaseHelper()
        db.init_conn()
        new_tests = read_newly_added_tests(db)
        db.close_conn()
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
