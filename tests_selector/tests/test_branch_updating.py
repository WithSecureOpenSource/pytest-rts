import pytest
import os
import subprocess
import sqlite3

from tests_selector.utils.db import DB_FILE_NAME, DatabaseHelper
from tests_selector import select


@pytest.mark.parametrize(
    "change_list",
    [
        (
            "changes/car/shift_2_forward.txt",
            "changes/shop/shift_2_forward.txt",
        ),
    ],
)
def test_updating_only_once(change_list):
    # get test_map lines for car.py
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    sql = "SELECT id FROM src_file WHERE path = ?"
    file_id_car = c.execute(sql, ("src/car.py",)).fetchone()[0]
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    old_line_ids_car = [x[0] for x in c.execute(sql, (file_id_car,)).fetchall()]
    conn.close()

    # Make new branch
    subprocess.run(["git", "checkout", "-b", "new-branch"])

    # Add two new lines at the start of car.py -> shifts others forward by 2
    # And commit
    subprocess.run(["cp", "-f", change_list[0], "src/car.py"])
    subprocess.run(["git", "add", "src/car.py"])
    subprocess.run(["git", "commit", "-m", "commit1"])

    # Run test selector, should update db
    subprocess.run(["tests_selector"])

    # Get updated line_ids for car.py
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    new_line_ids_car = [x[0] for x in c.execute(sql, (file_id_car,)).fetchall()]
    conn.close()

    # All car mapping lines should be old + 2
    assert [x + 2 for x in old_line_ids_car] == new_line_ids_car

    # Get all line mapping lines for shop.py
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    sql = "SELECT id FROM src_file WHERE path = ?"
    file_id_shop = c.execute(sql, ("src/shop.py",)).fetchone()[0]
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    old_line_ids_shop = [x[0] for x in c.execute(sql, (file_id_shop,)).fetchall()]
    conn.close()

    # Add two new lines at the start of shop.py -> shifts others forward by 2
    # And commit
    subprocess.run(["cp", "-f", change_list[1], "src/shop.py"])
    subprocess.run(["git", "add", "src/shop.py"])
    subprocess.run(["git", "commit", "-m", "commit2"])

    # Run test selector, should update db
    subprocess.run(["tests_selector"])

    # Get updated line_ids for shop.py
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    new_line_ids_shop = [x[0] for x in c.execute(sql, (file_id_shop,)).fetchall()]
    conn.close()

    # All shop mapping lines should be old + 2
    assert [x + 2 for x in old_line_ids_shop] == new_line_ids_shop

    # Get updated line_ids for car.py
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    new_line_ids_car = [x[0] for x in c.execute(sql, (file_id_car,)).fetchall()]
    conn.close()

    # All car mapping lines should be old + 2 and not updated twice
    assert [x + 2 for x in old_line_ids_car] == new_line_ids_car


@pytest.mark.parametrize(
    "change_list,expected",
    [
        (
            [
                "changes/car/change_accelerate.txt",
                "changes/shop/change_get_price.txt",
                "changes/test_car/add_test_passengers.txt",
            ],
            {
                "tests/test_some_methods.py::test_normal_shop_purchase2",
                "tests/test_some_methods.py::test_normal_shop_purchase",
                "tests/test_car.py::test_passengers",
            },
        )
    ],
)
def test_skipping_commit(change_list, expected):
    # Checkout a new branch
    subprocess.run(["git", "checkout", "-b", "new-branch"])

    # Change car.py from changes folder and commit changes
    subprocess.run(["cp", "-f", change_list[0], "src/car.py"])
    subprocess.run(["git", "add", "src/car.py"])
    subprocess.run(["git", "commit", "-m", "commit1"])

    # Run tests selector and db should update
    subprocess.run(["tests_selector"])

    # Change shop.py from changes folder and commit changes
    subprocess.run(["cp", "-f", change_list[1], "src/shop.py"])
    subprocess.run(["git", "add", "src/shop.py"])
    subprocess.run(["git", "commit", "-m", "commit2"])

    # Change test_car.py from changes folder and commit changes
    subprocess.run(["cp", "-f", change_list[2], "tests/test_car.py"])
    subprocess.run(["git", "add", "tests/test_car.py"])
    subprocess.run(["git", "commit", "-m", "commit3"])

    # Tests selectors functions should find tests from changes:
    # Commit1 -> Commit2 AND Commit2 -> Commit3
    # DB required to use the function
    db = DatabaseHelper()
    db.init_conn()
    (
        test_set,
        update_tuple,
        changed_test_files_amount,
        changed_src_files_amount,
        new_tests_amount,
    ) = select.get_tests_and_data_committed(db)
    db.close_conn()

    assert test_set == expected
