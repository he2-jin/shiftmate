from app.ocr.schemas import (
    ExtractedDay,
    ExtractedPerson,
    ExtractedSchedule,
    PersonSummary,
)
from app.ocr.validate import validate_schedule_extraction


def _schedule(days, year=2026, month=6, summary=None):
    return ExtractedSchedule(
        year=year,
        month=month,
        people=[ExtractedPerson(name="홍길동", days=days, summary=summary)],
    )


def test_missing_year_warns():
    s = ExtractedSchedule(year=None, month=6, people=[])
    assert any("연도" in w for w in validate_schedule_extraction(s))


def test_month_out_of_range_warns():
    s = ExtractedSchedule(year=2026, month=13, people=[])
    assert any("월" in w for w in validate_schedule_extraction(s))


def test_day_exceeds_month_warns():
    # 6월은 30일 → 31일은 범위 초과
    s = _schedule([ExtractedDay(day=31, code="D")])
    assert any("범위를 벗어" in w for w in validate_schedule_extraction(s))


def test_unknown_code_warns():
    s = _schedule([ExtractedDay(day=1, code="ZZ")])
    assert any("근무 코드를 알 수 없" in w for w in validate_schedule_extraction(s))


def test_duplicate_day_warns():
    s = _schedule([ExtractedDay(day=1, code="D"), ExtractedDay(day=1, code="N")])
    assert any("중복" in w for w in validate_schedule_extraction(s))


def test_low_confidence_warns():
    s = _schedule([ExtractedDay(day=1, code="D", confidence=0.5)])
    assert any("불확실" in w for w in validate_schedule_extraction(s))


def test_summary_mismatch_warns():
    days = [ExtractedDay(day=1, code="OFF"), ExtractedDay(day=2, code="OFF")]
    s = _schedule(days, summary=PersonSummary(off=5))
    assert any("OFF 합계" in w for w in validate_schedule_extraction(s))


def test_valid_schedule_has_no_warnings():
    days = [ExtractedDay(day=1, code="D"), ExtractedDay(day=2, code="OFF")]
    s = _schedule(days, summary=PersonSummary(off=1, n=0, annual_leave=0))
    assert validate_schedule_extraction(s) == []
