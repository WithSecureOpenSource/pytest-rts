import sqlite3

DB_FILE_NAME = "mapping.db"
RESULTS_DB_FILE_NAME = "results.db"


def get_cursor():
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    return c, conn


def get_results_cursor():
    conn = sqlite3.connect(RESULTS_DB_FILE_NAME)
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
            (
                file_id,
                line_id,
            ),
        )
        for line in data:
            test = line[0]
            tests.append(test)
    conn.close()
    return tests


def query_all_tests_srcfile(file_id):
    cursor, conn = get_cursor()
    tests = []
    data = cursor.execute(
        """ SELECT DISTINCT context
            FROM test_function
            JOIN test_map ON test_function.id == test_map.test_function_id
            WHERE test_map.file_id = ? """,
        (file_id,),
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


def init_results_db():
    c, conn = get_results_cursor()
    c.execute(
        """ CREATE TABLE IF NOT EXISTS project (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    commithash TEXT,
                    test_suite_size INTEGER,
                    database_size INTEGER,
                    UNIQUE (name,commithash))"""
    )
    c.execute(
        """ CREATE TABLE IF NOT EXISTS data (
                    project_id INTEGER,
                    specific_exit_line INTEGER,
                    specific_exit_file INTEGER,
                    all_exit INTEGER,
                    suite_size_line INTEGER,
                    suite_size_file INTEGER,
                    diff TEXT,
                    FOREIGN KEY (project_id) REFERENCES project(id))"""
    )
    conn.commit()
    conn.close()


def get_test_suite_size():
    c, conn = get_cursor()
    size = int(c.execute("SELECT count() FROM test_function").fetchone()[0])
    conn.close()
    return size


def store_results_project(project_name, commithash, suite_size, db_size):
    c, conn = get_results_cursor()
    c.execute(
        " INSERT OR IGNORE INTO project (name,commithash,test_suite_size,database_size) VALUES (?,?,?,?)",
        (project_name, commithash, suite_size, db_size),
    )
    conn.commit()
    project_id = int(
        c.execute(
            "SELECT id FROM project WHERE name = ? AND commithash = ?",
            (project_name, commithash),
        ).fetchone()[0]
    )
    conn.close()
    return project_id


def store_results_data(
    project_id,
    specific_exit_line,
    specific_exit_file,
    all_exit,
    suite_size_line,
    suite_size_file,
    diff,
):
    c, conn = get_results_cursor()
    c.execute(
        """ INSERT INTO data (
            project_id,
            specific_exit_line,
            specific_exit_file,
            all_exit,
            suite_size_line,
            suite_size_file,
            diff)
            VALUES (?,?,?,?,?,?,?)""",
        (
            project_id,
            specific_exit_line,
            specific_exit_file,
            all_exit,
            suite_size_line,
            suite_size_file,
            diff,
        ),
    )
    conn.commit()
    conn.close()


def init_mapping_db():
    c, conn = get_cursor()
    c.execute("DROP TABLE IF EXISTS test_map")
    c.execute("DROP TABLE IF EXISTS src_file")
    c.execute("DROP TABLE IF EXISTS test_file")
    c.execute("DROP TABLE IF EXISTS test_function")
    c.execute("DROP TABLE IF EXISTS last_hash")
    c.execute(
        "CREATE TABLE test_map (file_id INTEGER, test_function_id INTEGER, line_id INTEGER, UNIQUE(file_id,test_function_id,line_id))"
    )
    c.execute(
        "CREATE TABLE src_file (id INTEGER PRIMARY KEY, path TEXT, UNIQUE (path))"
    )
    c.execute(
        "CREATE TABLE test_file (id INTEGER PRIMARY KEY, path TEXT, UNIQUE (path))"
    )
    c.execute(
        """CREATE TABLE test_function (
                            id INTEGER PRIMARY KEY,
                            test_file_id INTEGER, 
                            context TEXT, 
                            start INTEGER, 
                            end INTEGER,
                            duration REAL,
                            FOREIGN KEY (test_file_id) REFERENCES test_file(id), 
                            UNIQUE (context))"""
    )
    c.execute("CREATE TABLE last_hash (hash TEXT)")
    conn.commit()
    conn.close()


def save_mapping_lines(src_id, test_function_id, lines):
    c, conn = get_cursor()
    for l in lines:
        c.execute(
            "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
            (src_id, test_function_id, l),
        )
    conn.commit()
    conn.close()


def save_src_file(src_file):
    c, conn = get_cursor()
    c.execute("INSERT OR IGNORE INTO src_file (path) VALUES (?)", (src_file,))
    src_id = c.execute(
        "SELECT id FROM src_file WHERE path == ?", (src_file,)
    ).fetchone()[0]
    conn.commit()
    conn.close()
    return src_id


def save_testfile_and_func(testfile, testname, func_name, start, end, elapsed):
    c, conn = get_cursor()
    c.execute("INSERT OR IGNORE INTO test_file (path) VALUES (?)", (testfile,))
    test_file_id = c.execute(
        "SELECT id FROM test_file WHERE path == ?", (testfile,)
    ).fetchone()[0]
    c.execute(
        "INSERT OR IGNORE INTO test_function (test_file_id,context,start,end,duration) VALUES (?,?,?,?,?)",
        (test_file_id, testname, start, end, elapsed),
    )
    test_function_id = c.execute(
        "SELECT id FROM test_function WHERE context == ?", (testname,)
    ).fetchone()[0]
    conn.commit()
    conn.close()
    return test_file_id, test_function_id


def get_test_duration(testname):
    c, conn = get_cursor()
    data = c.execute(
        "SELECT duration FROM test_function WHERE context = ?", (testname,)
    ).fetchone()
    if data == None:
        duration = 99999
    else:
        duration = data[0]
    conn.close()
    return duration


def save_last_hash(lasthash):
    c, conn = get_cursor()
    c.execute("DELETE FROM last_hash")
    c.execute("INSERT INTO last_hash (hash) VALUES (?)", (lasthash,))
    conn.commit()
    conn.close()


def get_last_hash():
    c, conn = get_cursor()
    lasthash = c.execute("SELECT hash FROM last_hash").fetchone()
    conn.close()
    if lasthash == None:
        return None
    else:
        return lasthash[0]
