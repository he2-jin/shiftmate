from app.ocr.parse import parse_schedule
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
