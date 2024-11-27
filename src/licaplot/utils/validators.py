from typing import Iterable, Sequence, Any

def vsequences(n: int, *args: Iterable[Sequence[Any]]):
    bounded = all(len(arg) <= n for arg in args)
    if not bounded:
        raise ValueError(f"An input argument list exceeds {n}")
    same_length = all(len(arg) == len(args[0]) for arg in args)
    if not same_length:
        raise ValueError("Not all input argument lists have the same length")
