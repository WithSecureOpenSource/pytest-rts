import pytest
import os
import subprocess
import sqlite3


def test_branch_updating():
    db_name = "mapping.db"
    # get test_map lines for car.py
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    sql = "SELECT id FROM src_file WHERE path = ?"
    file_id_car = c.execute(sql, ("src/car.py",)).fetchone()[0]
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    old_line_ids_car = [x[0] for x in c.execute(sql, (file_id_car,)).fetchall()]
    conn.close()

    # Make new branch
    subprocess.run(["git", "checkout", "-b", "new-branch"])

    # Add two new lines at the start of car.py -> shifts others forward by 2
    with open("./src/car.py", "r") as f:
        content = f.read()

    with open("./src/car.py", "w") as f:
        f.write("empty_variable = 0\nanother = 0\n")

    with open("./src/car.py", "a") as f:
        f.write(content)

    # Also add a change that triggers test running and db updating
    # Perhaps it should update lines also without running tests
    with open("./src/car.py", "r") as f:
        lines = f.readlines()

    lines[13] = lines[13].strip()
    lines[13] = "        " + lines[13] + "+1-1\n"

    with open("./src/car.py", "w") as f:
        for line in lines:
            f.write(line)

    # Commit changes
    subprocess.run(["git", "add", "src/car.py"])
    subprocess.run(["git", "commit", "-m", "car_changes"])

    # Run test selector, should update db
    subprocess.run(["tests_selector"])

    # Get updated line_ids for car.py
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    new_line_ids_car = [x[0] for x in c.execute(sql, (file_id_car,)).fetchall()]
    conn.close()

    # All car mapping lines should be old + 2
    assert [x + 2 for x in old_line_ids_car] == new_line_ids_car

    # Get all line mapping lines for shop.py
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    sql = "SELECT id FROM src_file WHERE path = ?"
    file_id_shop = c.execute(sql, ("src/shop.py",)).fetchone()[0]
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    old_line_ids_shop = [x[0] for x in c.execute(sql, (file_id_shop,)).fetchall()]
    conn.close()

    # Add two new lines at the start of shop.py -> shifts others forward by 2
    with open("./src/shop.py", "r") as f:
        content = f.read()

    with open("./src/shop.py", "w") as f:
        f.write("empty_variable = 0\nanother = 0\n")

    with open("./src/shop.py", "a") as f:
        f.write(content)

    # Also add a change that triggers test running and db updating
    # Perhaps it should update lines also without running tests
    with open("./src/shop.py", "r") as f:
        lines = f.readlines()

    lines[12] = lines[12].strip()
    lines[12] = "            " + lines[12] + "+1-1\n"

    with open("./src/shop.py", "w") as f:
        for line in lines:
            f.write(line)

    # Commit changes
    subprocess.run(["git", "add", "src/shop.py"])
    subprocess.run(["git", "commit", "-m", "shop_changes"])

    # Run test selector, should update db
    subprocess.run(["tests_selector"])

    # Get updated line_ids for shop.py
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    new_line_ids_shop = [x[0] for x in c.execute(sql, (file_id_shop,)).fetchall()]
    conn.close()

    # All shop mapping lines should be old + 2
    assert [x + 2 for x in old_line_ids_shop] == new_line_ids_shop

    # Get updated line_ids for car.py
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    new_line_ids_car = [x[0] for x in c.execute(sql, (file_id_car,)).fetchall()]
    conn.close()

    # All car mapping lines should be old + 2 and not updated twice
    assert [x + 2 for x in old_line_ids_car] == new_line_ids_car
