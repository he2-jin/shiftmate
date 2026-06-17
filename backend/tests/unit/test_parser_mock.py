import io

import pytest
from PIL import Image

from app.parsers.mock import MockScheduleParser
from app.db.models.schedule_cell import SHIFT_D, SHIFT_E, SHIFT_N, SHIFT_OFF, SHIFT_LEAVE


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color=(255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def png_file(tmp_path):
    path = tmp_path / "test.png"
    path.write_bytes(_make_png_bytes())
    return path


def test_mock_parser_returns_3_persons(png_file):
    parser = MockScheduleParser()
    result = parser.parse(png_file, year=2026, month=6)
    assert len(result.persons) == 3


def test_mock_parser_returns_15_cells(png_file):
    parser = MockScheduleParser()
    result = parser.parse(png_file, year=2026, month=6)
    assert len(result.cells) == 15


def test_mock_parser_shift_codes_are_valid(png_file):
    valid = {SHIFT_D, SHIFT_E, SHIFT_N, SHIFT_OFF, SHIFT_LEAVE}
    parser = MockScheduleParser()
    result = parser.parse(png_file, year=2026, month=6)
    for cell in result.cells:
        assert cell.shift_code in valid


def test_mock_parser_dates_in_correct_month(png_file):
    parser = MockScheduleParser()
    result = parser.parse(png_file, year=2026, month=6)
    for cell in result.cells:
        assert cell.date.year == 2026
        assert cell.date.month == 6


def test_mock_parser_confidence_score_range(png_file):
    parser = MockScheduleParser()
    result = parser.parse(png_file, year=2026, month=6)
    for cell in result.cells:
        assert 0.0 <= cell.confidence_score <= 1.0


def test_mock_parser_person_names(png_file):
    parser = MockScheduleParser()
    result = parser.parse(png_file, year=2026, month=6)
    names = [p.name for p in result.persons]
    assert "김간호" in names
    assert "이지원" in names
    assert "박조무" in names
