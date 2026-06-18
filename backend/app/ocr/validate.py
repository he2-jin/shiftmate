"""추출한 근무표에서 이상한 점을 찾아 경고 목록을 만드는 모듈."""

from calendar import monthrange

from app.ocr.normalize import ALLOWED_SHIFT_CODES
from app.ocr.schemas import ExtractedSchedule

LOW_CONFIDENCE_THRESHOLD = 0.8


def validate_schedule_extraction(schedule: ExtractedSchedule) -> list[str]:
    """근무표를 검사해 경고 문구 목록을 돌려준다(문제 없으면 빈 목록)."""
    warnings: list[str] = []

    if schedule.year is None:
        warnings.append("연도(year)를 읽지 못했습니다.")
    if schedule.month is None:
        warnings.append("월(month)을 읽지 못했습니다.")
    elif not 1 <= schedule.month <= 12:
        warnings.append(f"월(month) 값이 1~12 범위를 벗어났습니다: {schedule.month}")

    days_in_month: int | None = None
    if schedule.year is not None and schedule.month is not None and 1 <= schedule.month <= 12:
        days_in_month = monthrange(schedule.year, schedule.month)[1]

    for person in schedule.people:
        seen_days: set[int] = set()
        counts = {"OFF": 0, "N": 0, "연차": 0}

        for entry in person.days:
            if days_in_month is not None and not 1 <= entry.day <= days_in_month:
                warnings.append(f"{person.name}: {entry.day}일은 해당 월 범위를 벗어납니다.")

            if entry.day in seen_days:
                warnings.append(f"{person.name}: {entry.day}일이 중복됩니다.")
            seen_days.add(entry.day)

            if entry.code is None or entry.code not in ALLOWED_SHIFT_CODES:
                warnings.append(
                    f"{person.name}: {entry.day}일의 근무 코드를 알 수 없습니다 ({entry.code})."
                )
            elif entry.code in counts:
                counts[entry.code] += 1

            if entry.confidence is not None and entry.confidence < LOW_CONFIDENCE_THRESHOLD:
                warnings.append(
                    f"{person.name}: {entry.day}일 인식이 불확실합니다 (신뢰도 {entry.confidence})."
                )

        summary = person.summary
        if summary is not None:
            if summary.off is not None and summary.off != counts["OFF"]:
                warnings.append(
                    f"{person.name}: OFF 합계가 맞지 않습니다 (합계 {summary.off}, 실제 {counts['OFF']})."
                )
            if summary.n is not None and summary.n != counts["N"]:
                warnings.append(
                    f"{person.name}: N 합계가 맞지 않습니다 (합계 {summary.n}, 실제 {counts['N']})."
                )
            if summary.annual_leave is not None and summary.annual_leave != counts["연차"]:
                warnings.append(
                    f"{person.name}: 연차 합계가 맞지 않습니다 "
                    f"(합계 {summary.annual_leave}, 실제 {counts['연차']})."
                )

    return warnings
