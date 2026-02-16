from enum import StrEnum
from .dao import engine as engine, Session as Session

class Extension(StrEnum):
    CSV = "*.csv"
    TXT = "*.txt"

class Subject(StrEnum):
    LAMP = "LAMP"

class Event(StrEnum):
    CHANGE = "CHANGE"   # Light Source Lamp Change
    ON = "ON" # Power on Light Source
    OFF = "OFF" # Power off light source

