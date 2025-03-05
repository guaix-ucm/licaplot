from lica import StrEnum
from lica.lab import COL

from ._version import __version__ as __version__

class TBCOL(StrEnum):
    """
    TestBench Columns.
    Additiona columns names for data produced by Scan.exe or TestBench
    """

    INDEX = "Index"  # Index number 1, 2, etc produced in the CSV file
    CURRENT = "Electrical Current"  #
    READ_NOISE = "Read Noise"


class PROCOL(StrEnum):
    """
    Processing Columns.
    Additional columns added by processing
    """

    SPECTRAL = "Spectral Response"
    PHOTOD_QE = "Photodiode " + COL.QE
    PHOTOD_CURRENT = "Photodiode " + TBCOL.CURRENT


class PROMETA(StrEnum):
    """
    Processing Metadata.
    Metadata values added by processing
    """

    PHOTOD = "photodiode"
    FILTER = "filter"
    SENSOR = "sensor"


class TWCOL(StrEnum):
    """
    TESS-W Columns
    TESS-W columns as exported
    """

    TIME = "Timestamp"
    SEQ = "Seq. Number"
    FREQ = "Frequency"
    FILT = "Filter"
    NORM = "Normalized Responsivity"

class META(StrEnum):
    """
    Photodiode Metadata
    """
    PHAREA = "Photosensitive area"
    REF_WAVE = "Reference wavelenght"
    REF_RESP = "Reference responsivity"
    GAIN = "Gain"
