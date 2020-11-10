"""This module contains code for collecting newly added tests from pytest"""
import os
import sys
import pytest
from pytest_rts.pytest.collect_plugin import CollectPlugin
from pytest_rts.utils.db import DatabaseHelper

PROJECT_FOLDER = sys.argv[1]


def newly_added_tests(existing_tests):
    """Collect newly added tests by running pytest --collect-only"""
    coll_plugin = CollectPlugin(existing_tests)
    os.chdir(os.getcwd() + "/" + PROJECT_FOLDER)
    pytest.main(["--collect-only", "-p", "no:terminal"], plugins=[coll_plugin])
    os.chdir("..")

    test_set = set()
    for test in coll_plugin.collected:
        test_set.add(test)
    return test_set


def main():
    """Collect newly added tests and store them to database"""
    db_helper = DatabaseHelper()
    db_helper.init_conn()
    existing_tests = set()
    for test in [
        x[0]
        for x in db_helper.db_cursor.execute(
            "SELECT context FROM test_function"
        ).fetchall()
    ]:
        existing_tests.add(test)

    test_set = newly_added_tests(existing_tests)
    db_helper.db_cursor.execute("DELETE FROM new_tests")
    for test in test_set:
        db_helper.db_cursor.execute(
            "INSERT INTO new_tests (context) VALUES (?)", (test,)
        )
    db_helper.db_conn.commit()
    db_helper.db_conn.close()


if __name__ == "__main__":
    main()
