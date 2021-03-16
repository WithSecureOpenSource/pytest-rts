"""This module contains code for the first run of pytest-rts"""


class InitPhasePlugin:
    """Class to handle mapping database initialization"""

    def __init__(self):
        """"Coverage.py object placeholder set to None"""
        self.cov = None

    def pytest_collection_modifyitems(
        self, session, config, items
    ):  # pylint: disable=unused-argument
        """Set the Coverage object from pytest-cov"""
        self.cov = config.pluginmanager.getplugin("_cov").cov_controller.cov

    def pytest_runtest_logstart(self, nodeid, location):
        """Switch test function name in Coverage.py when a test starts running"""
        self.cov.switch_context(nodeid)
