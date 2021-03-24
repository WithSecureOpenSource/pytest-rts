"""This module contains code for git operations"""
import re
import subprocess
from typing import Dict, List, Set

from pydriller import GitRepository


def get_changed_files_current(repo: GitRepository) -> List[str]:
    """Get changed files in git working directory"""
    return repo.repo.git.diff("--name-only").split()


def get_file_diff_data_current(repo: GitRepository, filename: str) -> str:
    """Get git diff for a file in git working directory"""
    return repo.repo.git.diff("-U0", "--", filename)


def get_file_diff_dict_current(repo: GitRepository, files: List[str]) -> Dict[str, str]:
    """Returns a dictionary with file id as key and git diff as value"""
    return {
        file_path: get_file_diff_data_current(repo, file_path) for file_path in files
    }


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
