import sqlite3

DB_FILE_NAME = "mapping.db"
NEW_DB_FILE_NAME = "new_mapping.db"
RESULTS_DB_FILE_NAME = "results.db"


class DatabaseHelper:
    def __init__(self):
        self.db_conn = None
        self.db_cursor = None

    def init_conn(self, new=False):
        dbname = NEW_DB_FILE_NAME if new else DB_FILE_NAME
        self.db_conn = sqlite3.connect(dbname)
        self.db_cursor = self.db_conn.cursor()

    def swap_cursor(self):
        self.close_conn()
        self.init_conn(True)

    def copy_db(self):
        conn_old = sqlite3.connect(DB_FILE_NAME)
        conn_new = sqlite3.connect(NEW_DB_FILE_NAME)
        conn_old.backup(conn_new)
        conn_old.close()
        conn_new.close()

    def close_conn(self):
        self.db_conn.close()
        self.db_conn = None
        self.db_cursor = None

    def delete_ran_lines(self, line_ids, file_id):
        for line in line_ids:
            self.db_cursor.execute(
                "DELETE FROM test_map WHERE line_id == ? AND file_id == ?",
                (line, file_id),
            )
        self.db_conn.commit()

    def update_db_from_src_mapping(self, line_map, file_id):
        # this should update test mapping line data of src files to new line numbers calculated from changes
        tests_to_update = []
        for line_id in line_map.keys():
            db_data = self.db_cursor.execute(
                "SELECT file_id,test_function_id,line_id FROM test_map WHERE line_id == ? AND file_id == ?",
                (line_id, file_id),
            )
            for line in db_data:
                tests_to_update.append(line)
            self.db_cursor.execute(
                "DELETE FROM test_map WHERE line_id == ? AND file_id == ?",
                (line_id, file_id),
            )
        for t in tests_to_update:
            updated_t = (t[0], t[1], line_map[t[2]])
            self.db_cursor.execute(
                "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
                updated_t,
            )
        self.db_conn.commit()

    def update_db_from_test_mapping(self, line_map, file_id):
        # this should update the start and end lines of test functions with new line numbers calculated from changes
        tests_to_update = []
        db_data = self.db_cursor.execute(
            """SELECT id,test_file_id,context,start,end FROM test_function
                WHERE test_file_id = ?""",
            (file_id,),
        )
        for line in db_data:
            tests_to_update.append(line)
        self.db_cursor.execute(
            "DELETE FROM test_function WHERE test_file_id = ?", (file_id,)
        )

        for t in tests_to_update:
            start = t[3]
            end = t[4]
            if start in line_map:
                start = line_map[start]
            if end in line_map:
                end = line_map[end]
            updated_t = (t[0], t[1], t[2], start, end)
            self.db_cursor.execute(
                "INSERT OR IGNORE INTO test_function (id,test_file_id,context,start,end) VALUES (?,?,?,?,?)",
                updated_t,
            )
        self.db_conn.commit()

    def query_tests_srcfile(self, lines_to_query, file_id):
        tests = []
        for line_id in lines_to_query:
            data = self.db_cursor.execute(
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
        return tests

    def query_all_tests_srcfile(self, file_id):
        tests = []
        data = self.db_cursor.execute(
            """ SELECT DISTINCT context
                FROM test_function
                JOIN test_map ON test_function.id == test_map.test_function_id
                WHERE test_map.file_id = ? """,
            (file_id,),
        )
        for line in data:
            test = line[0]
            tests.append(test)
        return tests

    def query_tests_testfile(self, lines_to_query, file_id):
        tests = []
        for line_id in lines_to_query:
            data = self.db_cursor.execute(
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
        return tests

    def get_testfiles_and_srcfiles(self):
        test_files = [
            (x[0], x[1])
            for x in self.db_cursor.execute("SELECT id,path FROM test_file").fetchall()
        ]
        src_files = [
            (x[0], x[1])
            for x in self.db_cursor.execute("SELECT id,path FROM src_file").fetchall()
        ]
        return test_files, src_files

    def get_test_suite_size(self):
        size = int(
            self.db_cursor.execute("SELECT count() FROM test_function").fetchone()[0]
        )
        return size

    def init_mapping_db(self):
        self.db_cursor.execute("DROP TABLE IF EXISTS test_map")
        self.db_cursor.execute("DROP TABLE IF EXISTS src_file")
        self.db_cursor.execute("DROP TABLE IF EXISTS test_file")
        self.db_cursor.execute("DROP TABLE IF EXISTS test_function")
        self.db_cursor.execute("DROP TABLE IF EXISTS new_tests")
        self.db_cursor.execute(
            "CREATE TABLE test_map (file_id INTEGER, test_function_id INTEGER, line_id INTEGER, UNIQUE(file_id,test_function_id,line_id))"
        )
        self.db_cursor.execute(
            "CREATE TABLE src_file (id INTEGER PRIMARY KEY, path TEXT, UNIQUE (path))"
        )
        self.db_cursor.execute(
            "CREATE TABLE test_file (id INTEGER PRIMARY KEY, path TEXT, UNIQUE (path))"
        )
        self.db_cursor.execute(
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
        self.db_cursor.execute("CREATE TABLE new_tests (context TEXT)")
        self.db_conn.commit()

    def save_mapping_lines(self, src_id, test_function_id, lines):
        for l in lines:
            self.db_cursor.execute(
                "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
                (src_id, test_function_id, l),
            )
        self.db_conn.commit()

    def save_src_file(self, src_file):
        self.db_cursor.execute(
            "INSERT OR IGNORE INTO src_file (path) VALUES (?)", (src_file,)
        )
        src_id = self.db_cursor.execute(
            "SELECT id FROM src_file WHERE path == ?", (src_file,)
        ).fetchone()[0]
        self.db_conn.commit()
        return src_id

    def save_testfile_and_func(
        self, testfile, testname, func_name, start, end, elapsed
    ):
        self.db_cursor.execute(
            "INSERT OR IGNORE INTO test_file (path) VALUES (?)", (testfile,)
        )
        test_file_id = self.db_cursor.execute(
            "SELECT id FROM test_file WHERE path == ?", (testfile,)
        ).fetchone()[0]
        self.db_cursor.execute(
            "INSERT OR IGNORE INTO test_function (test_file_id,context,start,end,duration) VALUES (?,?,?,?,?)",
            (test_file_id, testname, start, end, elapsed),
        )
        test_function_id = self.db_cursor.execute(
            "SELECT id FROM test_function WHERE context == ?", (testname,)
        ).fetchone()[0]
        self.db_conn.commit()
        return test_file_id, test_function_id

    def get_test_duration(self, testname):
        data = self.db_cursor.execute(
            "SELECT duration FROM test_function WHERE context = ?", (testname,)
        ).fetchone()
        if data == None or data == (None,):
            duration = 99999
        else:
            duration = data[0]
        return duration

    def save_last_hash(self, lasthash):
        self.db_cursor.execute("DELETE FROM last_hash")
        self.db_cursor.execute("INSERT INTO last_hash (hash) VALUES (?)", (lasthash,))
        self.db_conn.commit()

    def get_last_hash(self):
        lasthash = self.db_cursor.execute("SELECT hash FROM last_hash").fetchone()
        if lasthash == None:
            return None
        else:
            return lasthash[0]

    def read_newly_added_tests(self):
        new_tests = set()
        for t in [
            x[0]
            for x in self.db_cursor.execute("SELECT context FROM new_tests").fetchall()
        ]:
            new_tests.add(t)
        return new_tests


class ResultDatabaseHelper:
    def __init__(self):
        self.db_conn = None
        self.db_cursor = None

    def init_conn(self):
        self.db_conn = sqlite3.connect(RESULTS_DB_FILE_NAME)
        self.db_cursor = self.db_conn.cursor()

    def close_conn(self):
        self.db_conn.close()
        self.db_conn = None
        self.db_cursor = None

    def init_results_db(self):
        self.db_cursor.execute(
            """ CREATE TABLE IF NOT EXISTS project (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        commithash TEXT,
                        test_suite_size INTEGER,
                        database_size INTEGER,
                        UNIQUE (name,commithash))"""
        )
        self.db_cursor.execute(
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
        self.db_conn.commit()

    def store_results_project(self, project_name, commithash, suite_size, db_size):
        self.db_cursor.execute(
            " INSERT OR IGNORE INTO project (name,commithash,test_suite_size,database_size) VALUES (?,?,?,?)",
            (project_name, commithash, suite_size, db_size),
        )
        self.db_conn.commit()
        project_id = int(
            self.db_cursor.execute(
                "SELECT id FROM project WHERE name = ? AND commithash = ?",
                (project_name, commithash),
            ).fetchone()[0]
        )
        return project_id

    def store_results_data(
        self,
        project_id,
        specific_exit_line,
        specific_exit_file,
        all_exit,
        suite_size_line,
        suite_size_file,
        diff,
    ):
        self.db_cursor.execute(
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
        self.db_conn.commit()
