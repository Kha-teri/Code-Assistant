from collections.abc import Iterable, Iterator
from itertools import islice


def chunked(items: Iterable[int], size: int) -> Iterator[list[int]]:
    """Yield consecutive lists of at most `size` items."""
    if size <= 0:
        raise ValueError("size must be positive")
    iterator = iter(items)
    while batch := list(islice(iterator, size)):
        yield batch


def clamp(value: float, low: float, high: float) -> float:
    """Limit `value` to the closed range [low, high]."""
    if low > high:
        raise ValueError("low must not exceed high")
    return max(low, min(value, high))
