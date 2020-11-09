"""This module contains code for database actions"""
import sqlite3

DB_FILE_NAME = "mapping.db"


class DatabaseHelper:
    """Class for database actions"""

    def __init__(self):
        self.db_conn = None
        self.db_cursor = None

    def init_conn(self):
        """Connect to sqlite database and set cursor"""
        self.db_conn = sqlite3.connect(DB_FILE_NAME)
        self.db_cursor = self.db_conn.cursor()

    def close_conn(self):
        """Disconnect sqlite and remove cursor"""
        self.db_conn.close()
        self.db_conn = None
        self.db_cursor = None

    def delete_ran_lines(self, line_ids, file_id):
        """Delete all test_map rows for given lines and file"""
        for line in line_ids:
            self.db_cursor.execute(
                "DELETE FROM test_map WHERE line_id == ? AND file_id == ?",
                (line, file_id),
            )
        self.db_conn.commit()

    def update_db_from_src_mapping(self, line_map, file_id):
        """Delete old source code file mapping data and insert updated"""
        tests_to_update = []
        for line_id in line_map.keys():
            db_data = self.db_cursor.execute(
                """
                SELECT file_id,test_function_id,line_id
                FROM test_map WHERE line_id == ? AND file_id == ?
                """,
                (line_id, file_id),
            )
            for line in db_data:
                tests_to_update.append(line)
            self.db_cursor.execute(
                "DELETE FROM test_map WHERE line_id == ? AND file_id == ?",
                (line_id, file_id),
            )
        for test in tests_to_update:
            updated_test = (test[0], test[1], line_map[test[2]])
            self.db_cursor.execute(
                "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
                updated_test,
            )
        self.db_conn.commit()

    def update_db_from_test_mapping(self, line_map, file_id):
        """Delete old test file mapping data and insert updated"""
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

        for test in tests_to_update:
            start = test[3]
            end = test[4]
            if start in line_map:
                start = line_map[start]
            if end in line_map:
                end = line_map[end]
            updated_test = (test[0], test[1], test[2], start, end)
            self.db_cursor.execute(
                """
                INSERT OR IGNORE
                INTO test_function (id,test_file_id,context,start,end)
                VALUES (?,?,?,?,?)""",
                updated_test,
            )
        self.db_conn.commit()

    def query_tests_srcfile(self, lines_to_query, file_id):
        """Query tests for a source code file based on line numbers"""
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
        """Query all tests for a source code file"""
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
        """Query tests for a test file based on line numbers"""
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
        """Query all source code and test files from database"""
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
        """Query how many tests are in mapping database"""
        size = int(
            self.db_cursor.execute("SELECT count() FROM test_function").fetchone()[0]
        )
        return size

    def init_mapping_db(self):
        """Initialize mapping database tables"""
        self.db_cursor.execute("DROP TABLE IF EXISTS test_map")
        self.db_cursor.execute("DROP TABLE IF EXISTS src_file")
        self.db_cursor.execute("DROP TABLE IF EXISTS test_file")
        self.db_cursor.execute("DROP TABLE IF EXISTS test_function")
        self.db_cursor.execute("DROP TABLE IF EXISTS new_tests")
        self.db_cursor.execute("DROP TABLE IF EXISTS last_update_hash")
        self.db_cursor.execute(
            """CREATE TABLE test_map (
                file_id INTEGER,
                test_function_id INTEGER,
                line_id INTEGER,
                UNIQUE(file_id,test_function_id,line_id))"""
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
        self.db_cursor.execute("CREATE TABLE last_update_hash (hash TEXT)")
        self.db_conn.commit()

    def save_mapping_lines(self, src_id, test_function_id, lines):
        """Save a test_map row"""
        for line in lines:
            self.db_cursor.execute(
                "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
                (src_id, test_function_id, line),
            )
        self.db_conn.commit()

    def save_src_file(self, src_file):
        """Save a source code row"""
        self.db_cursor.execute(
            "INSERT OR IGNORE INTO src_file (path) VALUES (?)", (src_file,)
        )
        src_id = self.db_cursor.execute(
            "SELECT id FROM src_file WHERE path == ?", (src_file,)
        ).fetchone()[0]
        self.db_conn.commit()
        return src_id

    def save_testfile_and_func(self, testfile, testname, func_lines, elapsed):
        """Save a test_file row and a test_function row"""
        self.db_cursor.execute(
            "INSERT OR IGNORE INTO test_file (path) VALUES (?)", (testfile,)
        )
        test_file_id = self.db_cursor.execute(
            "SELECT id FROM test_file WHERE path == ?", (testfile,)
        ).fetchone()[0]
        self.db_cursor.execute(
            """INSERT OR IGNORE
            INTO test_function
            (test_file_id,context,start,end,duration)
            VALUES (?,?,?,?,?)""",
            (test_file_id, testname, func_lines[0], func_lines[1], elapsed),
        )
        test_function_id = self.db_cursor.execute(
            "SELECT id FROM test_function WHERE context == ?", (testname,)
        ).fetchone()[0]
        self.db_conn.commit()
        return test_file_id, test_function_id

    def get_test_duration(self, testname):
        """Query run time duration for a test function"""
        data = self.db_cursor.execute(
            "SELECT duration FROM test_function WHERE context = ?", (testname,)
        ).fetchone()
        if data in (None, (None,)):
            duration = 99999
        else:
            duration = data[0]
        return duration

    def read_newly_added_tests(self):
        """Query new tests from database"""
        new_tests = set()
        for test in [
            x[0]
            for x in self.db_cursor.execute("SELECT context FROM new_tests").fetchall()
        ]:
            new_tests.add(test)
        return new_tests

    def mapping_line_exists(self, file_id, line_id):
        """Return whether a specific file has a specific line covered"""
        return bool(
            self.db_cursor.execute(
                "SELECT EXISTS(SELECT file_id FROM test_map WHERE file_id = ? AND line_id = ?)",
                (
                    file_id,
                    line_id,
                ),
            ).fetchone()[0]
        )

    def save_last_update_hash(self, commithash):
        """Save commit hash as last updated hash"""
        self.db_cursor.execute("DELETE FROM last_update_hash")
        self.db_cursor.execute("INSERT INTO last_update_hash VALUES (?)", (commithash,))
        self.db_conn.commit()

    def is_last_update_hash(self, commithash):
        """Return whether a given commit hash is the last update hash"""
        db_hash = self.db_cursor.execute(
            "SELECT hash FROM last_update_hash"
        ).fetchone()[0]
        return db_hash == commithash

    def get_last_update_hash(self):
        """Return latest update hash"""
        return self.db_cursor.execute("SELECT hash FROM last_update_hash").fetchone()[0]
