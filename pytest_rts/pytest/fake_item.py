"""This module contains a fake pytest item class"""
from _pytest.config import Config


class FakeItem:  # pylint: disable=too-few-public-methods
    """Fake class"""

    def __init__(self, config: Config) -> None:
        self.config = config
