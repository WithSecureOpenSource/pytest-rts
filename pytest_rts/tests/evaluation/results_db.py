"""This module contains a class for using evaluation results database"""
import sqlite3

RESULTS_DB_FILE_NAME = "results.db"


class ResultDatabase:
    """Class for handling evaluation results database"""

    def __init__(self):
        self.db_conn = None
        self.db_cursor = None

    def init_conn(self):
        """Connect sqlite3 and set cursor"""
        self.db_conn = sqlite3.connect(RESULTS_DB_FILE_NAME)
        self.db_cursor = self.db_conn.cursor()

    def close_conn(self):
        """Disconnect sqlite3"""
        self.db_conn.close()
        self.db_conn = None
        self.db_cursor = None

    def init_results_db(self):
        """Create tables"""
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
                        lines_removed INTEGER,
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
        """Store evaluation project data and return its database id"""
        self.db_cursor.execute(
            """INSERT OR IGNORE INTO project (
                  name,commithash,test_suite_size,database_size
                ) VALUES (?,?,?,?)""",
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
        lines_removed,
        specific_exit_line,
        specific_exit_file,
        all_exit,
        suite_size_line,
        suite_size_file,
        diff,
    ):
        """Store evaluation data from random remove test"""
        self.db_cursor.execute(
            """ INSERT INTO data (
                project_id,
                lines_removed,
                specific_exit_line,
                specific_exit_file,
                all_exit,
                suite_size_line,
                suite_size_file,
                diff)
                VALUES (?,?,?,?,?,?,?,?)""",
            (
                project_id,
                lines_removed,
                specific_exit_line,
                specific_exit_file,
                all_exit,
                suite_size_line,
                suite_size_file,
                diff,
            ),
        )
        self.db_conn.commit()
