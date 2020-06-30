import coverage
import pytest
import sqlite3
import os

def run_tests_and_cov():
    cov = coverage.Coverage()
    cov.erase()
    cov.start()
    pytest.main()
    cov.stop()
    cov.save()

def fill_db():
    if os.path.exists("example.db"):
        os.remove("example.db")
    new_db = sqlite3.connect('example.db') #own database
    old_db = sqlite3.connect('.coverage') #created by coverage.py

    c1 = new_db.cursor()
    c2 = old_db.cursor()

    c1.execute('CREATE TABLE tests (file_id INTEGER, context_id INTEGER, line_id INTEGER, UNIQUE(file_id,context_id,line_id))')
    c1.execute('CREATE TABLE file (id INTEGER PRIMARY KEY, path TEXT, UNIQUE (path))')
    c1.execute('CREATE TABLE context (id INTEGER PRIMARY KEY, context TEXT, UNIQUE (context))')

    old_db_files = c2.execute('SELECT * FROM file')
    for l in old_db_files:
        c1.execute('INSERT INTO file (id,path) VALUES (?,?)',l)
    old_db_context = c2.execute('SELECT * FROM context WHERE context != ""')
    for l in old_db_context:
        c1.execute('INSERT INTO context (id,context) VALUES (?,?)',l)
    
    coverage_data = c2.execute('''SELECT file_id, context_id, numbits FROM line_bits 
                                JOIN context ON context.id == line_bits.context_id 
                                WHERE context != "" ''')
    for l in coverage_data:
        file_id = l[0]
        context_id = l[1]
        line_ids = coverage.numbits.numbits_to_nums(l[2])
        for line_id in line_ids:
            c1.execute('INSERT INTO tests (file_id,context_id,line_id) VALUES (?,?,?)',(file_id,context_id,line_id))
    
    new_db.commit()
    new_db.close()
    old_db.close()

def main():
    run_tests_and_cov()
    fill_db()
    print('database created and filled')

if __name__ == "__main__":
    main()
