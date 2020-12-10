"""
Decorated function, to test that changes in the decorator code switch on tests
using the function itself.
"""

from .decorators import decrement

@decrement
def decremented_square(num: int) -> int:
    """Square the number and decrement the result."""
    return num * num
