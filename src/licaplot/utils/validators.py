
import os
import functools

from typing import Iterable, Sequence, Any


def vextension(path: str, extension: str) -> str:
    _, ext = os.path.splitext(path)
    if ext != extension:
        # Can't use ValueError inside a functools.partial function
        raise Exception(f"Path does not end with {extension} extension")
    return path

vecsv = functools.partial(vextension, extension=".ecsv")
vcsv = functools.partial(vextension, extension=".csv")

def vsequences(limit: int, *args: Iterable[Sequence[Any]]):
    bounded = tuple(len(arg) <= limit for arg in args)
    if not all(bounded):
        raise ValueError(f"An input argument list exceeds {len(bounded)}: {bounded}")
    same_length = tuple(len(arg) == len(args[0]) for arg in args)
    if not all(same_length):
        raise ValueError(f"Not all input argument lists have the same length ({same_length}")
