import subprocess
import sqlite3
import pytest
import re
import coverage
import json

import ast

PIPE = subprocess.PIPE

def top_level_functions(body):
    return (f for f in body if isinstance(f, ast.FunctionDef))

def parse_ast(filename):
    with open(filename, "rt") as file:
        return ast.parse(file.read(), filename=filename)

def git_add_changes(filename):
    subprocess.run(['git','add',filename])

def git_changed_src_files():
    git_data = subprocess.run(['git','diff','--name-only','src/'],stdout=PIPE, stderr=PIPE).stdout
    files = str(git_data,'utf-8').strip().split()
    return files

def git_changed_test_files():
    git_data = subprocess.run(['git','diff','--name-only','tests/'],stdout=PIPE, stderr=PIPE).stdout
    files = str(git_data,'utf-8').strip().split()
    return files

def git_changed_lines(filename):

    git_data = str(subprocess.run(['git','diff','-U0',filename],stdout=PIPE, stderr=PIPE).stdout)
    line_changes = re.findall(r'[@@].{1,20}[@@]',git_data)
    return line_changes

def get_test_lines_and_update_lines(line_changes):
    lines_to_query = []
    updates_to_lines = []

    cum_diff = 0
    for change in line_changes:
        changed_line = change.strip('@').split()
        if ',' not in changed_line[0]:
            changed_line[0] += ',1'
        if ',' not in changed_line[1]:
            changed_line[1] += ',1'
        old = changed_line[0].split(',')
        old[0] = old[0].strip('-')
        new = changed_line[1].split(',')
        new[0] = new[0].strip('+')
        
        line_diff = ((int(new[0]) + int(new[1])) - int(new[0])) - ((int(old[0]) + int(old[1])) - int(old[0])) + cum_diff
        cum_diff = line_diff

        update_tuple = (int(old[0]),line_diff)
        updates_to_lines.append(update_tuple)

        for i in range(int(old[0]),int(old[0])+int(old[1])):
            lines_to_query.append(i)

    return lines_to_query,updates_to_lines

def line_mapping(updates_to_lines,filename):
    line_count = sum(1 for line in open(filename)) - 1
    line_mapping = {}
    for i in range(len(updates_to_lines)):
        if i+1 >= len(updates_to_lines):
            next_point = line_count
        else:
            next_point = updates_to_lines[i+1][0]

        current = updates_to_lines[i][0]
        diff = updates_to_lines[i][1]

        if diff == 0: continue
        for k in range(current+1,next_point+1):
            line_mapping[k] = k + diff
        
    return line_mapping

def query_tests(lines_to_query,filename):
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    sql = 'SELECT * from Tests WHERE src_file = ? AND line_id IN ({0})'.format(', '.join('?' for _ in lines_to_query))
    data = c.execute(sql,(filename, *lines_to_query))
    tests_names_to_run = {t[0] for t in data}
    conn.close()

    return tests_names_to_run

def delete_ran_test_lines(line_ids,filename):
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    sql = 'DELETE from Tests WHERE src_file = ? AND line_id IN ({0})'.format(', '.join('?' for _ in line_ids))
    c.execute(sql,(filename, *line_ids))
    conn.commit()
    conn.close()

def update_db_lines_from_mapping(line_map,filename):
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    tests_to_update = []
    for line_id in line_map.keys():
        db_data = c.execute('SELECT * FROM Tests WHERE line_id = ? AND src_file = ?',(line_id,filename))
        for line in db_data:
            tests_to_update.append(line)
        c.execute('DELETE FROM Tests WHERE line_id = ? AND src_file = ?',(line_id,filename))

    for t in tests_to_update:
        updated_t = (t[0],t[1],line_map[t[2]])
        c.execute('INSERT INTO Tests VALUES (?,?,?)',updated_t)
 
    conn.commit()        
    conn.close()
    
def run_tests_and_cov(test_names_to_run):

    #tests = [t.split('.')[0] + '/' + t.split('.')[1] + '.py::' + t.split('.')[2] for t in test_names_to_run]
    tests = []
    for t in test_names_to_run:
        jtn = t.split('.')
        test = 'tests/'+jtn[0]+'.py::'+'::'.join(jtn[1:])
        tests.append(test)
    
    if len(tests) > 0:
        cov = coverage.Coverage()
        cov.erase()
        cov.start()
        pytest.main(tests)
        cov.stop()
        cov.save()
        cov.html_report(show_contexts=True)
        cov.json_report(show_contexts=True)

def update_db_from_json():
    with open('coverage.json') as json_file:
        data = json.load(json_file)

    conn = sqlite3.connect('example.db')
    c = conn.cursor()

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
                    line_id = str(line)
                    sql = 'INSERT OR IGNORE INTO tests VALUES (?,?,?)'
                    c.execute(sql, (test_name,src_file,line_id))

    conn.commit()
    conn.close()

def get_test_file_functions(filename):
    tree = parse_ast(filename)
    test_funcs = [func.name for func in top_level_functions(tree.body)]
    return test_funcs

def main():

    test_set = set()
    
    #Add all methods from changed test file to test_set
    changed_test_files = git_changed_test_files()
    for f in changed_test_files:
        test_funcs = get_test_file_functions(f)
        for t in test_funcs:
            new_f = f.replace('/','.').replace('.py','').split('.')
            #testname = new_f + '.' + t
            test_set.add(new_f[1]+'.'+t)
    changed_src_files = git_changed_src_files()
    lines_to_delete = {}
    lines_to_map = {}

    #Get information about changed src files
    for f in changed_src_files:
        changed_lines = git_changed_lines(f)
        lines_to_query,updates_to_lines = get_test_lines_and_update_lines(changed_lines)
        line_map = line_mapping(updates_to_lines,f)
        tests = query_tests(lines_to_query,f)
        for t in tests:
            test_set.add(t)

        lines_to_delete[f] = lines_to_query
        lines_to_map[f] = line_map

    print('lines changed:',lines_to_delete)
    print('lines to remap:',lines_to_map)
    print('changed test files:', changed_test_files)
    print('changed src files:', changed_src_files)
    if (len(test_set)>0):
        print('test set found:',test_set)
        ans = input('run these tests? [y/n]')
        if ans == 'y':
            for f in lines_to_delete.keys():
                delete_ran_test_lines(lines_to_delete[f],f)
                update_db_lines_from_mapping(lines_to_map[f],f)
                git_add_changes(f)
            for t in changed_test_files:
                git_add_changes(t)
            run_tests_and_cov(test_set)
            update_db_from_json()
    else:
        print('no tests found')


if __name__ == "__main__":
    main()


