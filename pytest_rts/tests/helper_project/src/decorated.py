"""
Decorated function, to test that changes in the decorator code switch on tests
using the function itself.
"""

from .decorators import decrement, modify_by

@decrement
def decremented_square(num: int) -> int:
    """Square the number and decrement the result."""
    return num * num


@modify_by(3)
def modified_double(num: int) -> int:
    """Double the number and and three to the result."""
    return 2 * num
