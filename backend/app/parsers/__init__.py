from app.parsers.base import ScheduleParser
from app.parsers.mock import MockScheduleParser


def get_parser(parser_backend: str) -> ScheduleParser:
    if parser_backend == "mock":
        return MockScheduleParser()
    raise ValueError(f"알 수 없는 파서: {parser_backend}")
