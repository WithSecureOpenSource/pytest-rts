"""Helper functions for evaluation code"""
import subprocess
import random
from tests_selector.utils.git import (
    get_git_repo,
)


def checkout_remove_branch():
    """Create a branch to do random line delete operations in"""
    repo = get_git_repo(None).repo.git
    repo.checkout("-b", "random-delete-branch")


def clear_remove_branch():
    """Remove branch used in evaluation"""
    repo = get_git_repo(None).repo.git
    repo.checkout("master")
    repo.branch("-D", "random-delete-branch")


def full_diff_between_commits(commit1, commit2):
    """Git diff between commits"""
    repo = get_git_repo(None).repo.git
    return repo.diff(commit1, commit2)


def select_random_file(files):
    """Select a random source file from list"""
    return random.choice(files)


def delete_random_line(filename):
    """Replace a random line containing code to a newline"""
    try:
        with open(filename, "r") as randomfile:
            data = randomfile.readlines()
            while True:
                rand_line = random.randint(0, len(data) - 1)
                if data[rand_line] != "\n":
                    break
            data[rand_line] = "\n"  # replace random line with newline.

        with open(filename, "w") as randomfile:
            for line in data:
                randomfile.write(line)

    except FileNotFoundError:
        print("can't open selected random file", filename)
        exit(1)


def delete_random_lines_and_commit(deletes, src_files):
    """Delete as many random lines as wanted from the list of given src-code files"""
    repo = get_git_repo(None).repo.git
    for i in range(deletes):
        random_file = select_random_file(src_files)
        filename = random_file[1]
        delete_random_line(filename)
        repo.add(filename)
        repo.commit("-m", str(i + 1))


def capture_specific_exit_code(tests, max_wait):
    """Run pytest with a given test set and capture exit code"""
    try:
        specific_exit_code = subprocess.run(
            ["tests_selector_specific_without_remap"] + tests,
            timeout=max_wait,
            capture_output=True,
            check=False,
        ).returncode
    except subprocess.TimeoutExpired:
        specific_exit_code = -1

    return specific_exit_code


def capture_all_exit_code(max_wait):
    """Run entire pytest test suite and capture exit code"""
    try:
        all_exit_code = subprocess.run(
            ["tests_selector_all_without_remap"],
            timeout=max_wait,
            capture_output=True,
            check=False,
        ).returncode
    except subprocess.TimeoutExpired:
        all_exit_code = -1

    return all_exit_code


def print_remove_test_output(
    i,
    project_name,
    commithash,
    deletes,
    full_test_suite_size,
    line_test_suite_size,
    file_test_suite_size,
    exitcode_line,
    exitcode_file,
    exitcode_all,
    db_name,
):
    """Print random remove test statistics"""
    print("============")
    print("iteration:", i + 1)
    print("project name:", project_name)
    print("commit hash:", commithash)
    print(f"removed {deletes} random src file lines")
    print("size of full test suite:", full_test_suite_size)
    print("size of line level test suite:", line_test_suite_size)
    print("size of file level test suite:", file_test_suite_size)
    print(
        f"exitcodes: line-level: {exitcode_line}, file-level: {exitcode_file}, all: {exitcode_all}"
    )
    print("STORING TO DATABASE:", db_name)
    print("============")
