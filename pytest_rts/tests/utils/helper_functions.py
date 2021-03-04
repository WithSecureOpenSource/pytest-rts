"""Helper code for test cases"""
import subprocess

from sqlalchemy.sql import select

from pytest_rts.utils.common import run_new_test_collection
from pytest_rts.utils.mappinghelper import MappingHelper
from pytest_rts.utils.selection import (
    get_tests_and_data_committed,
    get_tests_and_data_current,
)
from pytest_rts.tests.engine_wrapper import with_engine
from pytest_rts.utils.testgetter import TestGetter
from pytest_rts.utils.tables import test_function_table, test_map_table


@with_engine
def get_mapping_id_for_srcfile(path, engine=None):
    """Mapping database id for a source code file"""
    return MappingHelper(engine).saved_srcfiles[path]


@with_engine
def get_mapping_id_for_testfile(path, engine=None):
    """Mapping database id for a test code file"""
    return MappingHelper(engine).saved_testfiles[path]


@with_engine
def get_mapping_lines_for_srcfile(src_file_id, engine=None):
    """All mapped line numbers for a source code file"""
    return [
        x[0]
        for x in engine.execute(
            select([test_map_table.c.line_id]).where(
                test_map_table.c.file_id == src_file_id
            )
        )
    ]


@with_engine
def get_tests_from_tool_current(engine=None):
    """Tests from Git working directory changes"""
    mappinghelper = MappingHelper(engine)
    testgetter = TestGetter(engine)
    change_data = get_tests_and_data_current(mappinghelper, testgetter)
    return change_data.test_set


@with_engine
def get_tests_from_tool_committed(engine=None):
    """Tests from Git committed changes"""
    mappinghelper = MappingHelper(engine)
    testgetter = TestGetter(engine)
    change_data = get_tests_and_data_committed(
        mappinghelper,
        testgetter,
    )
    return change_data.test_set


@with_engine
def get_newly_added_tests_from_tool(engine=None):
    """Tests that are not yet mapped"""
    run_new_test_collection()
    return TestGetter(engine).newly_added_tests


@with_engine
def new_test_exists_in_mapping_db(testname, engine=None):
    """Check whether a test function is mapped"""
    existing_test = engine.execute(
        select([test_function_table]).where(test_function_table.c.context == testname)
    ).fetchone()
    return not existing_test is None


def change_file(change_path, file_path):
    """Change a file with path"""
    subprocess.run(
        ["cp", "-f", change_path, file_path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def commit_change(filename, message):
    """Git commit"""
    subprocess.run(
        ["git", "add", filename],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "commit", "-m", message],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_tool():
    """Run pytest-rts"""
    subprocess.run(["pytest", "--rts"], check=True)


def squash_commits(number_of_commits, new_message):
    """Merge number_of_commits commits into one"""
    subprocess.run(["git", "reset", "--soft", f"HEAD~{number_of_commits}"], check=True)
    subprocess.run(["git", "commit", "-m", new_message], check=True)


def checkout_new_branch(branchname="new-branch"):
    """Git checkout new branch"""
    subprocess.run(
        ["git", "checkout", "-b", branchname],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def checkout_branch(branchname):
    """Git checkout existing branch"""
    subprocess.run(
        ["git", "checkout", branchname],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def delete_branch(branchname):
    """Remove Git branch"""
    subprocess.run(
        ["git", "branch", "-D", branchname],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@with_engine
def get_test_function_runtimes(engine=None):
    """Get runtimes for every test function in the mapping database"""
    return TestGetter(engine).test_function_runtimes
