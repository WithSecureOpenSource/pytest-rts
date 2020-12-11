"""
Test for decorated function.
"""
from src import decorated


def test_decorated():
    """
    Test that decremented square of 3 is 8.
    """
    assert decorated.decremented_square(3) == 8
