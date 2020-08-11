from pydriller import GitRepository


def get_git_repo(project_folder):
    return GitRepository("./" + project_folder)


def file_changes_between_commits(commit1, commit2, project_folder):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("--name-only", commit1, commit2).split()


def changed_files_current(project_folder="."):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("--name-only").split()


def file_diff_data_between_commits(filename, commithash1, commithash2, project_folder):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("-U0", commithash1, commithash2, "--", filename)


def file_diff_data_current(filename, project_folder):
    repo = get_git_repo(project_folder)
    return repo.repo.git.diff("-U0", "--", filename)
