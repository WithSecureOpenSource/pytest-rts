import pytest
import os
import subprocess

from tests_selector.utils import db


def test_delete_ran_lines(temp_project_repo):
    c, conn = db.get_cursor()
    file_id = 1
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert line_ids == [4, 5, 6, 9, 12]

    db.delete_ran_lines(line_ids, file_id)
    c, conn = db.get_cursor()
    line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert line_ids == []
    subprocess.run(["tests_selector_init"])


def test_update_db_from_src_mapping(temp_project_repo):
    # shift all lines +5 and compare old and new lines in db
    c, conn = db.get_cursor()
    file_id = 1
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert line_ids == [4, 5, 6, 9, 12]

    line_map = {x: x + 5 for x in line_ids}
    db.update_db_from_src_mapping(line_map, file_id)
    c, conn = db.get_cursor()
    line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert line_ids == [9, 10, 11, 14, 17]
    subprocess.run(["tests_selector_init"])


def test_update_db_from_test_mapping(temp_project_repo):
    # shift all lines +5 and compare old and new lines in db
    c, conn = db.get_cursor()
    file_id = 2
    sql = "SELECT id,start,end FROM test_function WHERE test_file_id = ?"
    func_line_dict = {x[0]: (x[1], x[2]) for x in c.execute(sql, (file_id,)).fetchall()}
    conn.close()

    line_count = sum(1 for line in open("tests/test_some_methods.py"))
    line_map = {x: x + 5 for x in range(1, line_count + 1)}
    db.update_db_from_test_mapping(line_map, file_id)

    c, conn = db.get_cursor()
    func_line_dict2 = {
        x[0]: (x[1], x[2]) for x in c.execute(sql, (file_id,)).fetchall()
    }
    conn.close()

    assert len(func_line_dict) == len(func_line_dict2)
    for key in func_line_dict.keys():
        old_tuple = func_line_dict[key]
        new_tuple = func_line_dict2[key]
        assert old_tuple[0] + 5 == new_tuple[0]
        assert old_tuple[1] + 5 == new_tuple[1]

    subprocess.run(["tests_selector_init"])
