from lica import StrEnum
from lica.photodiode import COL

from ._version import __version__ as __version__

class TBCOL(StrEnum):
    """Additiona columns names for data produced by Scan.exe or TestBench"""

    INDEX = "Index"  # Index number 1, 2, etc produced in the CSV file
    CURRENT = "Electrical Current"  #
    READ_NOISE = "Read Noise"


class PROCOL(StrEnum):
    """Additional columns added by processing"""

    TRANS = "Transmission"
    SPECTRAL = "Spectral Response"
    PHOTOD_QE = "Photodiode " + COL.QE
    PHOTOD_CURRENT = "Photodiode " + TBCOL.CURRENT


class PROMETA(StrEnum):
    """Matedata values added by processing"""

    PHOTOD = "photodiode"
    FILTER = "filter"
    SENSOR = "sensor"


class TWCOL(StrEnum):
    """TESS-W columns as exported by textual-spectess"""

    TIME = "Timestamp"
    SEQ = "Seq. Number"
    FREQ = "Frequency"
    FILT = "Filter"
    NORM = "Normalized Responsivity" # Not used in textual-spectess
