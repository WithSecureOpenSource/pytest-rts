import sqlite3

DB_FILE_NAME = "mapping.db"


def get_cursor():
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    return c, conn


def get_results_cursor():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    return c, conn


def delete_ran_lines(line_ids, file_id):
    cursor, conn = get_cursor()
    for line in line_ids:
        cursor.execute(
            "DELETE FROM test_map WHERE line_id == ? AND file_id == ?", (line, file_id)
        )
    conn.commit()
    conn.close()


def update_db_from_src_mapping(line_map, file_id):
    # this should update test mapping line data of src files to new line numbers calculated from changes
    cursor, conn = get_cursor()
    tests_to_update = []
    for line_id in line_map.keys():
        db_data = cursor.execute(
            "SELECT file_id,test_function_id,line_id FROM test_map WHERE line_id == ? AND file_id == ?",
            (line_id, file_id),
        )
        for line in db_data:
            tests_to_update.append(line)
        cursor.execute(
            "DELETE FROM test_map WHERE line_id == ? AND file_id == ?",
            (line_id, file_id),
        )
    for t in tests_to_update:
        updated_t = (t[0], t[1], line_map[t[2]])
        cursor.execute(
            "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
            updated_t,
        )
    conn.commit()
    conn.close()


def update_db_from_test_mapping(line_map, file_id):
    # this should update the start and end lines of test functions with new line numbers calculated from changes
    cursor, conn = get_cursor()
    tests_to_update = []
    db_data = cursor.execute(
        """SELECT id,test_file_id,context,start,end FROM test_function
            WHERE test_file_id = ?""",
        (file_id,),
    )
    for line in db_data:
        tests_to_update.append(line)
    cursor.execute("DELETE FROM test_function WHERE test_file_id = ?", (file_id,))

    for t in tests_to_update:
        start = t[3]
        end = t[4]
        if start in line_map:
            start = line_map[start]
        if end in line_map:
            end = line_map[end]
        updated_t = (t[0], t[1], t[2], start, end)
        cursor.execute(
            "INSERT OR IGNORE INTO test_function (id,test_file_id,context,start,end) VALUES (?,?,?,?,?)",
            updated_t,
        )
    conn.commit()
    conn.close()


def query_tests_srcfile(lines_to_query, file_id):
    cursor, conn = get_cursor()
    tests = []
    for line_id in lines_to_query:
        data = cursor.execute(
            """ SELECT DISTINCT context
                FROM test_function
                JOIN test_map ON test_function.id == test_map.test_function_id
                WHERE test_map.file_id = ?
                AND test_map.line_id = ?  """,
            (file_id, line_id,),
        )
        for line in data:
            test = line[0]
            tests.append(test)
    conn.close()
    return tests


def query_tests_testfile(lines_to_query, file_id):
    cursor, conn = get_cursor()
    tests = []
    for line_id in lines_to_query:
        data = cursor.execute(
            """ SELECT DISTINCT context
                FROM test_function
                WHERE test_file_id = ? 
                AND start <= ?
                AND end >= ?""",
            (file_id, line_id, line_id),
        )
        for line in data:
            test = line[0]
            tests.append(test)
    conn.close()
    return tests


def get_testfiles_and_srcfiles():
    c, conn = get_cursor()
    test_files = [
        (x[0], x[1]) for x in c.execute("SELECT id,path FROM test_file").fetchall()
    ]
    src_files = [
        (x[0], x[1]) for x in c.execute("SELECT id,path FROM src_file").fetchall()
    ]
    conn.close()
    return test_files, src_files
