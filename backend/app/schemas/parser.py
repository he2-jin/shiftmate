import datetime as dt
from dataclasses import dataclass, field


@dataclass
class ParsedPerson:
    name: str
    row_index: int


@dataclass
class ParsedCell:
    person_row_index: int
    date: dt.date
    shift_code: str
    confidence_score: float
    original_value: str


@dataclass
class ParseResult:
    persons: list[ParsedPerson] = field(default_factory=list)
    cells: list[ParsedCell] = field(default_factory=list)
