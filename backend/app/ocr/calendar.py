"""근무 코드를 캘린더 미리보기 일정으로 바꾸는 모듈.

근무 시간은 코드에 박지 않고 설정값(DEFAULT_SHIFT_TIME_SETTINGS)으로 분리한다.
실제 캘린더 등록은 하지 않고, 미리보기용 이벤트 데이터까지만 만든다.
"""

import datetime as dt

from app.ocr.schemas import CalendarEvent, ExtractedSchedule

# 근무 코드별 시간 설정 (호출 시 주입해 덮어쓸 수 있음)
DEFAULT_SHIFT_TIME_SETTINGS: dict[str, dict] = {
    "D": {"title": "데이 근무", "start_time": "07:00", "end_time": "15:00"},
    "E": {"title": "이브닝 근무", "start_time": "14:30", "end_time": "22:30"},
    "N": {
        "title": "나이트 근무",
        "start_time": "22:00",
        "end_time": "07:00",
        "ends_next_day": True,
    },
    "OFF": {"create_event": False},
    "휴무": {"create_event": False},
    "빈칸": {"create_event": False},
    "연차": {"title": "연차", "all_day": True},
}


def _parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)


def convert_shift_to_calendar_events(
    schedule: ExtractedSchedule,
    shift_time_settings: dict[str, dict] | None = None,
) -> list[CalendarEvent]:
    """근무표에서 캘린더 미리보기 일정 목록을 만든다.

    - OFF/휴무/빈칸 등 create_event=False 인 코드는 일정 생성 안 함
    - all_day=True(연차)는 종일 일정
    - ends_next_day=True(야간 N)는 종료 시각이 다음 날
    - 연/월이 없거나 날짜가 잘못되면 해당 일정은 건너뜀(검증에서 경고 처리)
    """
    settings = shift_time_settings or DEFAULT_SHIFT_TIME_SETTINGS
    events: list[CalendarEvent] = []

    if schedule.year is None or schedule.month is None:
        return events

    year, month = schedule.year, schedule.month

    for person in schedule.people:
        for entry in person.days:
            conf = settings.get(entry.code) if entry.code else None
            if not conf or conf.get("create_event") is False:
                continue

            try:
                base_date = dt.date(year, month, entry.day)
            except ValueError:
                continue  # 잘못된 날짜는 건너뜀

            if conf.get("all_day"):
                events.append(
                    CalendarEvent(
                        title=conf["title"],
                        start=dt.datetime(year, month, entry.day, 0, 0),
                        end=None,
                        all_day=True,
                    )
                )
                continue

            sh, sm = _parse_hhmm(conf["start_time"])
            eh, em = _parse_hhmm(conf["end_time"])
            end_date = base_date + dt.timedelta(days=1) if conf.get("ends_next_day") else base_date

            events.append(
                CalendarEvent(
                    title=conf["title"],
                    start=dt.datetime(year, month, entry.day, sh, sm),
                    end=dt.datetime(end_date.year, end_date.month, end_date.day, eh, em),
                )
            )

    return events
