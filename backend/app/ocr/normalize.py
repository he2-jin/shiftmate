"""OCR이 잘못 읽은 근무 코드를 바로잡는 모듈."""

# 허용 근무 코드
ALLOWED_SHIFT_CODES = {"D", "E", "N", "OFF", "연차", "휴무", "빈칸"}

# 한글 오인식 보정표
_ANNUAL_LEAVE_VARIANTS = {"연차", "연자", "언차", "년차"}
_OFF_LEAVE_VARIANTS = {"휴무", "휴우"}


def normalize_shift_code(raw: str | None) -> str | None:
    """OCR 원문을 허용 근무 코드 중 하나로 바로잡는다.

    바로잡을 수 없으면 None을 반환한다(호출부에서 경고 처리).
    빈 입력은 "빈칸"으로 본다.
    """
    if raw is None:
        return "빈칸"

    text = raw.strip()
    if text == "":
        return "빈칸"

    # 공백 제거 후 대문자화 (영문 코드 판정용)
    compact = "".join(text.split())
    upper = compact.upper()

    # OFF 류: 숫자 0을 O로 본 뒤, O/F 로만 이뤄지고 F가 하나라도 있으면 OFF
    off_candidate = upper.replace("0", "O")
    if off_candidate and set(off_candidate) <= {"O", "F"} and "F" in off_candidate:
        return "OFF"

    # 단일 글자 코드
    if upper in ("D", "E", "N"):
        return upper

    # 한글 보정 (원문 그대로 비교)
    if compact in _ANNUAL_LEAVE_VARIANTS:
        return "연차"
    if compact in _OFF_LEAVE_VARIANTS:
        return "휴무"
    if compact == "빈칸":
        return "빈칸"

    return None
