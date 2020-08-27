import pytest
import os
import subprocess
import shutil


@pytest.fixture(scope="session")
def temp_project_repo(tmpdir_factory):
    temp_folder = tmpdir_factory.mktemp("temp")
    shutil.copytree(
        "./tests_selector/tests/helper_project", str(temp_folder), dirs_exist_ok=True
    )
    os.chdir(temp_folder)

    with open(".gitignore", "w") as f:
        lines = ["*.db\n", ".coverage\n", "*__pycache__*\n"]
        for line in lines:
            f.write(line)

    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "1"])
    subprocess.run(["tests_selector_init"])
    return temp_folder
