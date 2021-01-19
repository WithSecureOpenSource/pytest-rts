"""This module contains temporary Git repository initialization and teardown for tests"""
import os
import subprocess
import shutil
import pytest
from pytest_rts.plugin import DB_FILE_NAME
from testhelper import TestHelper


@pytest.fixture(scope="session", autouse=True)
def temp_project_repo(tmpdir_factory):
    """Create a temporary Git repository and initialize the tool there"""
    temp_folder = tmpdir_factory.mktemp("temp").join("testrepo")
    shutil.copytree("./pytest_rts/tests/helper_project", temp_folder)
    os.chdir(temp_folder)

    with open(".gitignore", "w") as gitignore:
        lines = ["*.db\n", ".coverage\n", "*__pycache__*\n"]
        for line in lines:
            gitignore.write(line)

    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.name", "pytest"], check=True)
    subprocess.run(["git", "config", "user.email", "pytest@example.com"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "1"], check=True)
    subprocess.run(["pytest", "--rts"], check=True)
    return temp_folder


@pytest.fixture(scope="function", autouse=True)
def teardown_method():
    """Reset state of temporary git repository"""
    yield
    subprocess.run(["git", "restore", "."], check=True)
    subprocess.run(["git", "checkout", "master"], check=True)
    subprocess.run(["git", "branch", "-D", "new-branch"], check=False)
    os.remove(DB_FILE_NAME)
    subprocess.run(["pytest", "--rts"], check=True)


@pytest.fixture
def helper():
    """TestHelper as a fixture for tests"""
    return TestHelper()
