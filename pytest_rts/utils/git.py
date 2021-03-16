"""This module contains code for git operations"""
import re
import subprocess
from pydriller import GitRepository


def get_git_repo(project_folder):
    """Return a GitRepository"""
    if not project_folder:
        res = subprocess.check_output(
            "git rev-parse --show-toplevel".split(),
            stderr=subprocess.DEVNULL,
        )
        project_folder = res.decode().strip()
    return GitRepository(project_folder)


def is_git_repo():
    """Check if current directory or any parent directory is a git repo"""
    try:
        subprocess.check_output(
            "git rev-parse --show-toplevel".split(),
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def repo_has_commits():
    """Check if current repository has commits"""
    try:
        subprocess.check_output(
            ["git", "log"],
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def changed_files_between_commits(commit1, commit2, project_folder=None):
    """Get changed files between two commits"""
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("--name-only", commit1, commit2).split()


def changed_files_current(project_folder=None):
    """Get changed files in git working directory"""
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("--name-only").split()


def file_diff_data_between_commits(
    filename, commithash1, commithash2, project_folder=None
):
    """Get git diff for a file from changes between two commits"""
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("-U0", commithash1, commithash2, "--", filename)


def file_diff_data_current(filename, project_folder=None):
    """Get git diff for a file in git working directory"""
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("-U0", "--", filename)


def get_changed_lines(diff):
    """Parse changed lines, line number updates and new lines from git diff -U0 output"""
    regex = r"[@][@]\s+[-][0-9]+(?:,[0-9]+)?\s+[+][0-9]+(?:,[0-9]+)?\s+[@][@]"
    line_changes = re.findall(regex, diff)
    changed_lines = []
    for change in line_changes:
        changed_line = change.strip("@").split()
        if "," not in changed_line[0]:
            changed_line[0] += ",1"
        if "," not in changed_line[1]:
            changed_line[1] += ",1"
        old = changed_line[0].split(",")
        old[0] = old[0].strip("-")
        new = changed_line[1].split(",")
        new[0] = new[0].strip("+")

        # example data:
        # @@ -old0,old1 +new0,new1 @@
        # old0 to old0 + old1 are now new0 to new0+new1
        # changed lines: old0 to old0 + old1
        # correct?
        if int(old[1]) == 0:
            changed_lines.append(int(old[0]))
        else:
            for i in range(int(old[0]), int(old[0]) + int(old[1])):
                changed_lines.append(i)

    return changed_lines


def get_current_head_hash():
    """Return current git HEAD hash"""
    return get_git_repo(None).repo.head.object.hexsha
