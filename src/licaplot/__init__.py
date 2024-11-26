# where filters were changesd
from enum import Enum

class Markers(Enum):
    TriUp = "2"
    TriDown = "1"
    Star = "*"
    Point = '.'
    X = 'x'
    Plus = "+"
    Diamond = "d"
    Circle = "o"
    Square = "s"
 


MONOCROMATOR_FILTERS_LABELS = (
    {"label": r"$BG38 \Rightarrow OG570$", "wavelength": 570, "style": "--"},
    {"label": r"$OG570\Rightarrow RG830$", "wavelength": 860, "style": "-."},
)  
