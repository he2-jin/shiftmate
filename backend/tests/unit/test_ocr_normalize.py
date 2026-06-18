import pytest

from app.ocr.normalize import normalize_shift_code


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("0FF", "OFF"),   # 숫자 0 오인식
        ("OF", "OFF"),    # F 누락
        ("OFFF", "OFF"),  # F 중복
        ("O F F", "OFF"), # 공백 끼임
        ("off", "OFF"),   # 소문자
        ("OFF", "OFF"),
        ("D", "D"),
        ("d", "D"),
        ("E", "E"),
        ("N", "N"),
        ("연차", "연차"),
        ("연자", "연차"),  # 오인식
        ("언차", "연차"),
        ("년차", "연차"),
        ("휴무", "휴무"),
        ("", "빈칸"),
        ("   ", "빈칸"),
    ],
)
def test_normalize_shift_code(raw, expected):
    assert normalize_shift_code(raw) == expected


def test_normalize_none_input_is_blank():
    assert normalize_shift_code(None) == "빈칸"


def test_normalize_unknown_returns_none():
    assert normalize_shift_code("XYZ") is None
    assert normalize_shift_code("123") is None
