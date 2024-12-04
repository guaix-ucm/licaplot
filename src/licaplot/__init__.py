from lica import StrEnum

class TBCOL(StrEnum):
    """Additiona columns names for data produced by Scan.exe or TestBench"""

    INDEX = "Index"  # Index number 1, 2, etc produced in the CSV file
    CURRENT = "Electrical Current"  #
    READ_NOISE = "Read Noise"

