"""This module contains code for initializing the mapping database"""
import os

import coverage

from pytest_rts.pytest.mapper_plugin import MapperPlugin
from pytest_rts.utils.common import calculate_func_lines
from pytest_rts.utils.git import get_current_head_hash


class InitPhasePlugin(MapperPlugin):
    """Class to handle mapping database initialization"""

    def __init__(self, mappinghelper):
        """"Constructor calls database and Coverage.py initialization"""
        super().__init__(mappinghelper)
        self.mappinghelper.set_last_update_hash(get_current_head_hash())

    def pytest_collection_modifyitems(self, session, config, items):
        """Calculate function start and end line numbers from testfiles"""
        del session, config
        self.testfiles = {os.path.relpath(item.location[0]) for item in items}
        self.test_func_lines = {
            testfile_path: calculate_func_lines(
                coverage.python.get_python_source(testfile_path)
            )
            for testfile_path in self.testfiles
        }
