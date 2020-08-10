import pytest


class CapturePluginAll:
    def __init__(self):
        pass

    def pytest_sessionfinish(self, session, exitstatus):
        print(int(exitstatus))
