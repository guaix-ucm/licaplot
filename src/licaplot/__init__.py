from lica import StrEnum
from lica.photodiode import COL


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
    NORM = "Normalized Response" # Not used in textual-spectess
