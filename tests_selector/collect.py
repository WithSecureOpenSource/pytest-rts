import os
import sys
import pytest
from tests_selector.pytest.collect_plugin import CollectPlugin
from tests_selector.utils.db import DatabaseHelper

PROJECT_FOLDER = sys.argv[1]


def newly_added_tests(existing_tests):
    coll_plugin = CollectPlugin(existing_tests)
    os.chdir(os.getcwd() + "/" + PROJECT_FOLDER)
    pytest.main(["--collect-only", "-p", "no:terminal"], plugins=[coll_plugin])
    os.chdir("..")

    test_set = set()
    for t in coll_plugin.collected:
        test_set.add(t)
    return test_set


def main():
    db = DatabaseHelper()
    db.init_conn()
    existing_tests = set()
    for t in [
        x[0]
        for x in db.db_cursor.execute("SELECT context FROM test_function").fetchall()
    ]:
        existing_tests.add(t)

    test_set = newly_added_tests(existing_tests)
    db.db_cursor.execute("DELETE FROM new_tests")
    for t in test_set:
        db.db_cursor.execute("INSERT INTO new_tests (context) VALUES (?)", (t,))
    db.db_conn.commit()
    db.db_conn.close()


if __name__ == "__main__":
    main()
