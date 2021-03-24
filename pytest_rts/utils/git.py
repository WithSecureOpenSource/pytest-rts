"""This module contains code for git operations"""
import re
import subprocess
from typing import List, Set

from pydriller import GitRepository


def commit_exists(commithash: str) -> bool:
    """Check if a given commithash exists in the Git repository"""
    return commithash in [commit.hash for commit in get_git_repo().get_list_commits()]


def get_changed_files_current(repo: GitRepository) -> List[str]:
    """Get changed files in git working directory"""
    return repo.repo.git.diff("--name-only").split()


def get_changed_files_between_commits(
    repo: GitRepository, commithash1: str, commithash2: str
) -> List[str]:
    """Get changed files between two commits"""
    return repo.repo.git.diff("--name-only", commithash1, commithash2).split()


def get_file_diff_data_current(repo: GitRepository, file_path: str) -> str:
    """Get git diff for a file in git working directory"""
    return repo.repo.git.diff("-U0", "--", file_path)


def get_file_diff_data_between_commits(
    repo: GitRepository, file_path: str, commithash1: str, commithash2: str
) -> str:
    """Get git diff for a file from changes between two commits"""
    return repo.repo.git.diff("-U0", commithash1, commithash2, "--", file_path)


def get_changed_lines(diff: str) -> Set[int]:
    """Parse changed lines from git diff -U0 output.
    - Change data according to git diff output:
    - @@ -old0,old1 +new0,new1 @@
    - old0 to old0 + old1 are now new0 to new0 + new1
    - changed lines = old0 to old0 + old1 (last not included)
    """
    regex = r"[@][@]\s+[-][0-9]+(?:,[0-9]+)?\s+[+][0-9]+(?:,[0-9]+)?\s+[@][@]"
    line_changes = re.findall(regex, diff)
    changed_lines: Set[int] = set()
    for change in line_changes:
        changed_line = change.strip("@").split()

        # Add , for parsing when it's omitted in the default case of 1
        if "," not in changed_line[0]:
            changed_line[0] += ",1"

        # Split the change to old0 and old1
        old = changed_line[0].split(",")
        old[0] = old[0].strip("-")

        if int(old[1]) == 0:
            changed_lines.add(int(old[0]))
        else:
            changed_lines.update(range(int(old[0]), int(old[0]) + int(old[1])))

    return changed_lines


def get_current_head_hash(repo: GitRepository) -> str:
    """Return current git HEAD hash"""
    return repo.repo.head.object.hexsha


def get_git_repo() -> GitRepository:
    """Return a GitRepository"""
    res = subprocess.check_output(
        "git rev-parse --show-toplevel".split(),
        stderr=subprocess.DEVNULL,
    )
    project_folder = res.decode().strip()
    return GitRepository(project_folder)


def is_git_repo() -> bool:
    """Check if current directory or any parent directory is a git repo"""
    try:
        get_git_repo()
        return True
    except subprocess.CalledProcessError:
        return False
