from app.ocr.calendar import convert_shift_to_calendar_events
from app.ocr.schemas import ExtractedDay, ExtractedPerson, ExtractedSchedule


def _schedule(code: str, day: int = 3) -> ExtractedSchedule:
    return ExtractedSchedule(
        year=2026,
        month=6,
        people=[ExtractedPerson(name="홍길동", days=[ExtractedDay(day=day, code=code)])],
    )


def test_night_shift_ends_next_day():
    events = convert_shift_to_calendar_events(_schedule("N", day=3))
    assert len(events) == 1
    assert events[0].start.isoformat() == "2026-06-03T22:00:00"
    assert events[0].end.isoformat() == "2026-06-04T07:00:00"


def test_day_shift_same_day():
    events = convert_shift_to_calendar_events(_schedule("D", day=1))
    assert events[0].start.hour == 7
    assert events[0].end.hour == 15
    assert events[0].start.date() == events[0].end.date()


def test_off_creates_no_event():
    assert convert_shift_to_calendar_events(_schedule("OFF")) == []
    assert convert_shift_to_calendar_events(_schedule("휴무")) == []


def test_annual_leave_is_all_day():
    events = convert_shift_to_calendar_events(_schedule("연차"))
    assert len(events) == 1
    assert events[0].all_day is True
    assert events[0].end is None


def test_missing_year_month_returns_empty():
    sched = _schedule("D")
    sched.year = None
    assert convert_shift_to_calendar_events(sched) == []
