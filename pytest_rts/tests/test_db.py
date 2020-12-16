import sqlite3
import pytest
from pytest_rts.utils.db import DatabaseHelper, DB_FILE_NAME


def test_delete_ran_lines():
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    file_id = 1
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    old_line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    db = DatabaseHelper()
    db.init_conn()
    db.delete_ran_lines(old_line_ids, file_id)
    db.close_conn()

    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    new_line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert not new_line_ids


def test_update_db_from_src_mapping():
    # shift all lines and compare old and new lines in db
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    file_id = 1
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    old_line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    shift = 5
    line_map = {x: x + shift for x in old_line_ids}

    db = DatabaseHelper()
    db.init_conn()
    db.update_db_from_src_mapping(line_map, file_id)
    db.close_conn()

    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    new_line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert new_line_ids == [k + shift for k in old_line_ids]


def test_update_db_from_test_mapping():
    # shift all lines and compare old and new lines in db
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    testfile_id = 2
    funclines_sql = "SELECT id,start,end FROM test_function WHERE test_file_id = ?"
    filename_sql = "SELECT path FROM test_file WHERE id = ?"

    testfile_name = c.execute(filename_sql, (testfile_id,)).fetchone()[0]
    old_func_line_dict = {
        x[0]: (x[1], x[2]) for x in c.execute(funclines_sql, (testfile_id,)).fetchall()
    }

    conn.close()

    shift = 5
    line_count = sum(1 for line in open(testfile_name))
    line_map = {x: x + shift for x in range(1, line_count + 1)}

    db = DatabaseHelper()
    db.init_conn()
    db.update_db_from_test_mapping(line_map, testfile_id)
    db.close_conn()

    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    new_func_line_dict = {
        x[0]: (x[1], x[2]) for x in c.execute(funclines_sql, (testfile_id,)).fetchall()
    }
    conn.close()

    assert len(old_func_line_dict) == len(new_func_line_dict)
    for key in old_func_line_dict.keys():
        old_func_linenumbers = old_func_line_dict[key]
        new_func_linenumbers = new_func_line_dict[key]
        assert old_func_linenumbers[0] + shift == new_func_linenumbers[0]
        assert old_func_linenumbers[1] + shift == new_func_linenumbers[1]


def test_tool_files_not_mapped():
    conn = sqlite3.connect(DB_FILE_NAME)
    tool_files_mapped = bool(
        conn.execute(
            """SELECT EXISTS(
                SELECT * FROM src_file 
                  WHERE 
                    path LIKE '%/init_phase_plugin.py' 
                    OR 
                    path LIKE '%/update_phase_plugin.py'
               )
            """
        ).fetchone()[0]
    )
    conn.close()

    assert not tool_files_mapped
