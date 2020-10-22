import sqlite3
from tests_selector.utils.db import DatabaseHelper

db_name = "mapping.db"


def test_delete_ran_lines():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    file_id = 1
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert line_ids == [4, 5, 6, 9, 12]

    db = DatabaseHelper()
    db.init_conn()
    db.delete_ran_lines(line_ids, file_id)
    db.close_conn()

    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert line_ids == []


def test_update_db_from_src_mapping():
    # shift all lines +5 and compare old and new lines in db
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    file_id = 1
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert line_ids == [4, 5, 6, 9, 12]
    line_map = {x: x + 5 for x in line_ids}

    db = DatabaseHelper()
    db.init_conn()
    db.update_db_from_src_mapping(line_map, file_id)
    db.close_conn()

    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert line_ids == [9, 10, 11, 14, 17]


def test_update_db_from_test_mapping():
    # shift all lines +5 and compare old and new lines in db
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    file_id = 2
    sql = "SELECT id,start,end FROM test_function WHERE test_file_id = ?"
    func_line_dict = {x[0]: (x[1], x[2]) for x in c.execute(sql, (file_id,)).fetchall()}
    conn.close()

    line_count = sum(1 for line in open("tests/test_some_methods.py"))
    line_map = {x: x + 5 for x in range(1, line_count + 1)}

    db = DatabaseHelper()
    db.init_conn()
    db.update_db_from_test_mapping(line_map, file_id)
    db.close_conn()

    conn = sqlite3.connect(db_name)
    c = conn.cursor()
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
