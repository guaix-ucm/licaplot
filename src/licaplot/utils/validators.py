from typing import Iterable, Sequence, Any

def vsequences(limit: int, *args: Iterable[Sequence[Any]]):
    bounded = tuple(len(arg) <= limit for arg in args)
    if not all(bounded):
        raise ValueError(f"An input argument list exceeds {n}: {bounded}")
    same_length = tuple(len(arg) == len(args[0]) for arg in args)
    if not all(same_length):
        raise ValueError(f"Not all input argument lists have the same length ({same_length}")
