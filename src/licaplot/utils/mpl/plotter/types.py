from typing import Sequence

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
Titles = Sequence[str]
Legends = Sequence[str]
MarkerSeq = Sequence[StrEnum]
LegendsGroup = Sequence[Legends]
MarkersGroup = Sequence[MarkerSeq]
