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
