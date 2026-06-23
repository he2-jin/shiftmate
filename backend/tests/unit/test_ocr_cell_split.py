from app.ocr.cell_split import _merge_close_boundaries


def test_merge_removes_close_fake_boundary():
    # 137이 125에 너무 붙어 있음(글자를 선으로 오인) → 병합되어 사라짐
    result = _merge_close_boundaries([5, 44, 125, 137, 164])
    assert 137 not in result
    # 125 근처로 합쳐진 경계 하나만 남음
    assert any(120 <= b <= 135 for b in result)
    # 멀리 떨어진 진짜 경계는 그대로 유지
    assert 5 in result and 44 in result and 164 in result


def test_merge_keeps_regular_boundaries():
    # 일정 간격(25)으로 떨어진 진짜 경계는 절대 합치지 않음
    bounds = [0, 25, 50, 75, 100]
    assert _merge_close_boundaries(bounds) == bounds


def test_merge_short_input():
    assert _merge_close_boundaries([]) == []
    assert _merge_close_boundaries([10]) == [10]


def test_merge_does_not_overmerge():
    # 가짜 하나만 끼어도 진짜 경계 개수는 거의 보존돼야 함
    bounds = [0, 30, 33, 60, 90, 120]  # 33이 30에 붙은 가짜
    result = _merge_close_boundaries(bounds)
    assert 33 not in result
    assert len(result) == 5  # 30/33 합쳐 5개
