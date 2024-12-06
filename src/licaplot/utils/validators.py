
import os
import functools

from typing import Iterable, Sequence, Any

from lica.validators import vfile
from lica.photodiode import BENCH

def vextension(path: str, extension: str) -> str:
    _, ext = os.path.splitext(path)
    if ext != extension:
        # Can't use ValueError inside a functools.partial function
        raise Exception(f"Path does not end with {extension} extension")
    return path

vecsv = functools.partial(vextension, extension=".ecsv")

def vecsvfile(path: str):
    path = vfile(path)
    return vecsv(path)

def vsequences(limit: int, *args: Iterable[Sequence[Any]]):
    bounded = tuple(len(arg) <= limit for arg in args)
    if not all(bounded):
        raise ValueError(f"An input argument list exceeds {len(bounded)}: {bounded}")
    same_length = tuple(len(arg) == len(args[0]) for arg in args)
    if not all(same_length):
        raise ValueError(f"Not all input argument lists have the same length ({same_length}")

def vbench(value: str) -> int:
    value = int(value)
    if not (BENCH.WAVE_START <= value <= BENCH.WAVE_END):
        raise ValueError(f"Wavelength {value} outside Optical Bench limits [{BENCH.WAVE_START}-{BENCH.WAVE_END}]")


