import re

from pydriller import GitRepository


def get_git_repo(project_folder):
    return GitRepository("./" + project_folder)


def changed_files_branch(project_folder="."):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("--name-only","master...").split()


def file_changes_between_commits(commit1, commit2, project_folder):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("--name-only", commit1, commit2).split()


def changed_files_current(project_folder="."):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("--name-only").split()


def file_diff_data_branch(filename,project_folder="."):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("-U0","master...","--",filename)


def file_diff_data_between_commits(filename, commithash1, commithash2, project_folder):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("-U0", commithash1, commithash2, "--", filename)


def file_diff_data_current(filename, project_folder="."):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("-U0", "--", filename)


def get_test_lines_and_update_lines(diff):
    regex = r"[@][@]\s+[-][0-9]+(?:,[0-9]+)?\s+[+][0-9]+(?:,[0-9]+)?\s+[@][@]"
    line_changes = re.findall(regex, diff)
    lines_to_query = []
    updates_to_lines = []
    cum_diff = 0
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

        line_diff = (
            ((int(new[0]) + int(new[1])) - int(new[0]))
            - ((int(old[0]) + int(old[1])) - int(old[0]))
            + cum_diff
        )
        cum_diff = line_diff

        update_tuple = (int(old[0]), line_diff)
        updates_to_lines.append(update_tuple)

        # example data:
        # @@ -old0,old1 +new0,new1 @@
        # old0 to old0 + old1 are now new0 to new0+new1
        # changed lines: old0 to old0 + old1
        # correct?
        if int(old[1]) == 0:
            lines_to_query.append(int(old[0]))
        else:
            for i in range(int(old[0]), int(old[0]) + int(old[1])):
                lines_to_query.append(i)

    return lines_to_query, updates_to_lines
