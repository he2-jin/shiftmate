from app.ocr.parse import parse_grid, parse_schedule
from app.ocr.schemas import BoundingBox, OcrResult, OcrWord


def _w(text: str, x: int, y: int, w: int = 20, h: int = 20, conf: float = 0.9) -> OcrWord:
    return OcrWord(text=text, confidence=conf, bbox=BoundingBox(x=x, y=y, width=w, height=h))


def test_parse_extracts_year_month():
    result = parse_schedule(OcrResult(raw_text="2026년 6월 근무표", words=[]))
    assert result.year == 2026
    assert result.month == 6


def test_parse_maps_person_and_days():
    words = [
        # 날짜 헤더 (y=100)
        _w("1", 100, 100),
        _w("2", 200, 100),
        _w("3", 300, 100),
        # 데이터 행: 홍길동 (y=150)
        _w("홍길동", 10, 150),
        _w("D", 100, 150),
        _w("N", 200, 150),
        _w("OFF", 300, 150),
    ]
    result = parse_schedule(OcrResult(raw_text="2026년 6월", words=words))

    assert len(result.people) == 1
    person = result.people[0]
    assert "홍길동" in person.name

    codes = {d.day: d.code for d in person.days}
    assert codes[1] == "D"
    assert codes[2] == "N"
    assert codes[3] == "OFF"


def test_parse_empty_words_gives_no_people():
    result = parse_schedule(OcrResult(raw_text="", words=[]))
    assert result.people == []


# --- parse_grid: 셀 분할 격자를 좌표 재계산 없이 바로 매핑 ---


def test_parse_grid_maps_name_and_days():
    grid = [
        ["이름", "1", "2", "3"],  # 헤더: 이름 칸 + 날짜
        ["홍길동", "D", "N", "0FF"],  # 0FF는 normalize로 OFF 보정
        ["김영희", "연자", "", "E"],  # 연자→연차, 빈칸→빈칸
    ]
    schedule = parse_grid(grid, raw_text="2026년 6월 근무표")

    assert schedule.year == 2026
    assert schedule.month == 6
    assert len(schedule.people) == 2

    hong = schedule.people[0]
    assert hong.name == "홍길동"
    hong_codes = {d.day: d.code for d in hong.days}
    assert hong_codes == {1: "D", 2: "N", 3: "OFF"}

    kim = schedule.people[1]
    assert kim.name == "김영희"
    kim_codes = {d.day: d.code for d in kim.days}
    assert kim_codes == {1: "연차", 2: "빈칸", 3: "E"}


def test_parse_grid_handles_multi_column_name():
    # 이름 앞에 직책 칸이 따로 있어 날짜 시작 전 열이 2개
    grid = [
        ["직책", "이름", "1", "2"],
        ["NA", "박철수", "D", "OFF"],
    ]
    schedule = parse_grid(grid, raw_text="2026년 5월")

    assert len(schedule.people) == 1
    person = schedule.people[0]
    assert "박철수" in person.name
    codes = {d.day: d.code for d in person.days}
    assert codes == {1: "D", 2: "OFF"}


def test_parse_grid_no_header_gives_no_people():
    grid = [["가", "나", "다"], ["라", "마", "바"]]
    schedule = parse_grid(grid, raw_text="")
    assert schedule.people == []


def test_parse_schedule_uses_grid_when_present():
    # OcrResult.grid가 있으면 좌표(words) 클러스터 대신 격자를 직접 쓴다
    ocr = OcrResult(
        raw_text="2026년 6월",
        grid=[["이름", "1", "2"], ["홍길동", "D", "N"]],
    )
    schedule = parse_schedule(ocr)
    assert len(schedule.people) == 1
    codes = {d.day: d.code for d in schedule.people[0].days}
    assert codes == {1: "D", 2: "N"}
