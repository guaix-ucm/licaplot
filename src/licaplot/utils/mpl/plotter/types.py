from typing import Sequence, Union

from astropy.table import Table
from lica import StrEnum

# --------------
# Types and such
# --------------

class Markers(StrEnum):
    Circle = "o"
    Square = "s"
    Star = "*"
    Diamond = "d"
    TriUp = "2"
    TriDown = "1"
    Point = "."
    X = "x"
    Plus = "+"

# Types shorhands

ColNum = int
ColNums = Sequence[int]
Tables = Sequence[Table]
Title = Union[str, Sequence[str]] # for space separated words from the command line
Titles = Sequence[Title]
Legend = str
Legends = Sequence[Legend]
MarkerSeq = Sequence[StrEnum]
LegendsGroup = Sequence[Legends]
MarkersGroup = Sequence[MarkerSeq]

Element = Union[ColNum, ColNums, Tables, Titles, LegendsGroup, MarkersGroup]
Elements = Sequence[Element]
