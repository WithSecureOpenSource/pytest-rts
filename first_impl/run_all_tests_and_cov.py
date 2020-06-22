import coverage
import pytest
import json
import sqlite3
import re

def run_tests_and_cov():
    cov = coverage.Coverage()
    cov.erase()
    cov.start()
    pytest.main()
    cov.stop()
    cov.save()
    #cov.html_report(show_contexts=True)
    cov.json_report(show_contexts=True)

def create_db_and_fill():
    with open('coverage.json') as json_file:
        data = json.load(json_file)
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS tests;')
    c.execute('CREATE TABLE tests (test_name text, src_file text, line_id INTEGER, UNIQUE(test_name,src_file,line_id))')
    tested_files = data['files']

    for filename in tested_files.keys():
        file_test_results = tested_files[filename]
        executed_lines = file_test_results['executed_lines']
        for line in executed_lines:
            context = file_test_results['contexts'][str(line)]
            if len(context) == 1 and context[0] == '': continue
            for con in context:
                test_name = con
                if test_name != '':
                    src_file = filename
                    line_id = int(line)
                    sql = 'INSERT INTO tests VALUES (?,?,?)'
                    c.execute(sql, (test_name,src_file,line_id))
    conn.commit()
    conn.close()

def main():
    run_tests_and_cov()
    create_db_and_fill()
    print('database created and filled')


if __name__ == "__main__":
    main()
