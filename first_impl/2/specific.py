import subprocess
import sqlite3
import pytest
import re
import coverage

PIPE = subprocess.PIPE
conn = sqlite3.connect('example.db')
coverage.numbits.register_sqlite_functions(conn)
cursor = conn.cursor()

def git_add_changes(filename):
    subprocess.run(['git','add',filename])

def git_changed_src_files():
    git_data = subprocess.run(['git','diff','--name-only'],stdout=PIPE, stderr=PIPE).stdout
    git_diff_files = str(git_data,'utf-8').strip().split()
    db_files = cursor.execute('SELECT path FROM file')
    files_changed = []
    for f in db_files:
        path = f[0]
        for filename in git_diff_files:
            if filename in path: files_changed.append(filename)

    return files_changed

def tests_from_changed_test_files():

    # trouble mapping the contexts from Coverage to actual testnames to collect with pytest
    '''
    git_data = subprocess.run(['git','diff','--name-only'],stdout=PIPE, stderr=PIPE).stdout
    files_changed = str(git_data,'utf-8').strip().split()
    tests_changed = set()
    test_filenames_changed = set()
    for f in files_changed:
        filename = re.search(r"[\w-]+\.",f).group(0).strip('.')
        tests = cursor.execute('SELECT context.context FROM context JOIN tests ON tests.context_id = context.id WHERE context LIKE ?',('%'+filename+'%',))
        for t in tests:
            tests_changed.add(t[0])
            test_filenames_changed.add(f)

    return (tests_changed,list(test_filenames_changed))
    '''
    
    return set(),list()

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
    tests = []
    for line_id in lines_to_query:
        data = cursor.execute('''SELECT context FROM context 
                                JOIN tests ON context.id == tests.context_id 
                                JOIN file ON tests.file_id == file.id 
                                WHERE line_id == ?
                                AND path LIKE ?''',(line_id,'%'+filename))
        for line in data:
            test = line[0]
            tests.append(test)

    return tests

def delete_ran_test_lines(line_ids,filename):
    file_id = cursor.execute('SELECT id FROM file WHERE path LIKE ?',('%'+filename,)).fetchone()[0]
    for line in line_ids:
        cursor.execute('DELETE FROM tests WHERE line_id == ? and file_id == ?',(line,file_id))
    conn.commit()

def update_db_lines_from_mapping(line_map,filename):
    file_id = cursor.execute('SELECT id FROM file WHERE path LIKE ?',('%'+filename,)).fetchone()[0]
    tests_to_update = []
    for line_id in line_map.keys():
        db_data = cursor.execute('SELECT * FROM tests WHERE Line_id == ? AND file_id == ?',(line_id,file_id))
        for line in db_data:
            tests_to_update.append(line)
        cursor.execute('DELETE FROM Tests WHERE line_id == ? AND file_id == ?',(line_id,file_id))
    for t in tests_to_update:
        updated_t = (t[0],t[1],line_map[t[2]])
        cursor.execute('INSERT INTO Tests VALUES (?,?,?)',updated_t)     
    conn.commit()

def update_db_from_coverage():
    coverage_conn = sqlite3.connect('.coverage')
    c = coverage_conn.cursor()
    coverage_data = c.execute('''SELECT path, context, numbits FROM file
                                JOIN line_bits ON file.id = line_bits.file_id
                                JOIN context ON line_bits.context_id = context.id
                                WHERE context != "" ''')
    context_data = cursor.execute('SELECT id, context FROM context')
    for l in coverage_data:
        filename = l[0]
        test_context = l[1]

        #test_context_split = test_context.split('.')
        #test_func = test_context_split[-1]
        #test_class_or_file = test_context_split[-2]
        
        numbits = l[2]
        coverage_lines = coverage.numbits.numbits_to_nums(numbits)

        real_file_id = cursor.execute('SELECT id FROM file WHERE path == ?',(filename,)).fetchone()[0]
        real_context_id = cursor.execute('SELECT id FROM context WHERE context LIKE ?',(test_context,)).fetchone()[0]

        for i in coverage_lines:
            new_db_entry = (real_file_id,real_context_id,i)
            cursor.execute('INSERT OR IGNORE INTO tests (file_id,context_id,line_id) VALUES (?,?,?)',new_db_entry)
        
    conn.commit()
    coverage_conn.close()
  
def run_tests_and_cov(test_names_to_run):

    class PytestCollectPlugin:

        def __init__(self):
            self.selected = []

        #Collect tests and select only the ones that match a context
        def pytest_collection_modifyitems(self,session,config,items):
            for item in items:
                for test in test_names_to_run:
                    test_func = test.split('.')[-1]
                    if test_func in item.name:
                        self.selected.append(item)
            items[:] = self.selected
    
    my_plugin = PytestCollectPlugin()

    cov = coverage.Coverage()
    cov.erase()
    cov.start()
    pytest.main([],plugins=[my_plugin])
    cov.stop()
    cov.save()

def main():
    test_set,changed_test_files = tests_from_changed_test_files()
    changed_src_files = git_changed_src_files()
    lines_to_delete = {}
    lines_to_map = {}
    for f in changed_src_files:
        changed_lines = git_changed_lines(f)
        lines_to_query,updates_to_lines = get_test_lines_and_update_lines(changed_lines)
        line_map = line_mapping(updates_to_lines,f)   
        lines_to_delete[f] = lines_to_query
        lines_to_map[f] = line_map  
        tests = query_tests(lines_to_query,f)
        for t in tests:
            test_set.add(t)

    print('lines changed in src files:',lines_to_delete)
    print('lines to remap in src files:',lines_to_map)
    #print('changed test files:', changed_test_files)
    print('changed src files:', changed_src_files)

    if (len(test_set)>0):
        print('test set found:',test_set)
        ans = input('run these tests? [y/n]')
        if ans == 'y':
            for f in lines_to_delete.keys():
                delete_ran_test_lines(lines_to_delete[f],f)
                update_db_lines_from_mapping(lines_to_map[f],f)
                git_add_changes(f)

            #for t in changed_test_files:
            #    git_add_changes(t)

            run_tests_and_cov(test_set)
            update_db_from_coverage()

            print('db updated with new coverage data')
            print('changes added to git')
    else:
        print('no tests found')
    
    conn.close()

if __name__ == "__main__":
    main()


