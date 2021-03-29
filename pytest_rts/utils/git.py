"""This module contains code for git operations"""
import logging
import re
import subprocess
from typing import List, Set

from gitdb.exc import BadName
from pydriller import GitRepository


def commit_exists(commithash: str, repo: GitRepository) -> bool:
    """Check if a given commithash exists in the Git repository"""
    if not commithash:
        return False
    try:
        repo.get_commit(commithash)
        return True
    except BadName:
        logging.info("Git commithash was provided but it was not found in history.")
        return False


def get_changed_files_workdir(repo: GitRepository) -> List[str]:
    """Get changed files in git working directory"""
    return repo.repo.git.diff("--name-only").split()


def get_changed_files_committed_and_workdir(
    repo: GitRepository, commithash_to_compare: str
) -> List[str]:
    """Get changed files between given commit and the working copy"""
    return repo.repo.git.diff("--name-only", commithash_to_compare).split()


def get_file_diff_data_workdir(repo: GitRepository, file_path: str) -> str:
    """Get git diff for a file in git working directory"""
    return repo.repo.git.diff("-U0", "--", file_path)


def get_file_diff_data_committed_and_workdir(
    repo: GitRepository, file_path: str, commithash_to_compare: str
) -> str:
    """Get git diff for a file from changes between given commit and the working copy"""
    return repo.repo.git.diff("-U0", commithash_to_compare, "--", file_path)


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
