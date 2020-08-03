import os
import sys
import pytest
import sqlite3

PROJECT_FOLDER = sys.argv[1]


def newly_added_tests(existing_tests):
    class CollectPlugin:
        def __init__(self):
            self.collected = []

        def pytest_collection_modifyitems(self, items):
            for item in items:
                if item.nodeid not in existing_tests:
                    self.collected.append(item.nodeid)

    coll_plugin = CollectPlugin()
    os.chdir(os.getcwd() + "/" + PROJECT_FOLDER)
    pytest.main(["--collect-only", "-p", "no:terminal"], plugins=[coll_plugin])
    os.chdir("..")

    test_set = set()
    for t in coll_plugin.collected:
        test_set.add(t)
    return test_set


def main():
    conn = sqlite3.connect("example.db")
    c = conn.cursor()
    existing_tests = set()
    for t in [x[0] for x in c.execute("SELECT context FROM test_function").fetchall()]:
        existing_tests.add(t)

    test_set = newly_added_tests(existing_tests)
    c.execute("DROP TABLE IF EXISTS new_tests")
    c.execute("CREATE TABLE new_tests (context TEXT)")
    for t in test_set:
        c.execute("INSERT INTO new_tests (context) VALUES (?)", (t,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
