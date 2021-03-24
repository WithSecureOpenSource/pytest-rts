"""
Decorator, to check that changes in the decorator switch on tests using
decorated functions.
"""
from functools import wraps
from typing import Callable

def decrement(func: Callable[[int], int]) -> Callable[[int], int]:
    """
    Decrements the value returned by the decorated function.
    """
    @wraps(func)
    def _wrapper(num):
        return func(num) - 1

    return _wrapper


def modify_by(delta: int):
    """
    Adds delta to the value returned by the decorated function.
    """
    def decorator(func: Callable[[int], int]) -> Callable[[int], int]:
        @wraps(func)
        def _wrapper(num):
            return func(num) + delta
        return _wrapper
    return decorator

