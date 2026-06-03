from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.parser import ParseResult


class ScheduleParser(ABC):
    @abstractmethod
    def parse(self, image_path: Path, year: int, month: int) -> ParseResult:
        """이미지를 분석해서 ParseResult 반환."""
