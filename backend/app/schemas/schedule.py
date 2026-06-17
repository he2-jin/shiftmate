import datetime as dt
from typing import Annotated

from pydantic import BaseModel, Field

CONFIDENCE_REVIEW_THRESHOLD = 0.8


class ScheduleMonthOut(BaseModel):
    id: Annotated[int, Field(description="근무표 월(月) 레코드 고유 ID")]
    year: Annotated[int, Field(description="근무표 연도")]
    month: Annotated[int, Field(description="근무표 월 (1~12)")]

    model_config = {"from_attributes": True}


class PersonOut(BaseModel):
    id: Annotated[int, Field(description="근무자 고유 ID")]
    name: Annotated[str, Field(description="근무자 이름")]
    row_index: Annotated[int, Field(description="근무표 내 행 순서 (0부터 시작)")]

    model_config = {"from_attributes": True}


class CellOut(BaseModel):
    cell_id: Annotated[int, Field(description="셀 고유 ID")]
    person_id: Annotated[int, Field(description="이 셀이 속한 근무자 ID")]
    date: Annotated[dt.date, Field(description="근무 날짜")]
    shift_code: Annotated[
        str,
        Field(
            description=(
                "근무 코드 (D=주간/E=저녁/N=야간/OFF=휴무/LEAVE=휴가). "
                "수정된 셀은 보정값을 반환"
            )
        ),
    ]
    confidence_score: Annotated[
        float | None, Field(description="OCR 인식 신뢰도 (0~1). 값이 없으면 null")
    ]
    is_user_corrected: Annotated[bool, Field(description="사용자가 직접 수정한 셀인지 여부")]
    needs_review: Annotated[
        bool, Field(description="검토 필요 여부 (신뢰도가 0.8 미만이면 true)")
    ]

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    version_id: Annotated[int, Field(description="생성된 근무표 버전 ID")]
    status: Annotated[str, Field(description="버전 상태 (draft/reviewed/applied/ignored)")]
    schedule_month: Annotated[ScheduleMonthOut, Field(description="대상 근무표 월 정보")]
    table_type: Annotated[
        str,
        Field(description="근무표 유형 (nursing_assistant=간호조무사 / support_staff=지원인력)"),
    ]
    created_at: Annotated[dt.datetime, Field(description="버전 생성 시각")]
    updated_at: Annotated[dt.datetime, Field(description="버전 최종 수정 시각")]
    persons: Annotated[list[PersonOut], Field(description="근무자 목록")]
    cells: Annotated[list[CellOut], Field(description="파싱된 근무 셀 목록")]


class VersionDetailResponse(BaseModel):
    version_id: Annotated[int, Field(description="근무표 버전 ID")]
    status: Annotated[str, Field(description="버전 상태 (draft/reviewed/applied/ignored)")]
    schedule_month: Annotated[ScheduleMonthOut, Field(description="대상 근무표 월 정보")]
    table_type: Annotated[
        str,
        Field(description="근무표 유형 (nursing_assistant=간호조무사 / support_staff=지원인력)"),
    ]
    created_at: Annotated[dt.datetime, Field(description="버전 생성 시각")]
    updated_at: Annotated[dt.datetime, Field(description="버전 최종 수정 시각")]
    persons: Annotated[list[PersonOut], Field(description="근무자 목록")]
    cells: Annotated[list[CellOut], Field(description="근무 셀 목록")]


class CellPatchRequest(BaseModel):
    shift_code: Annotated[
        str, Field(description="변경할 근무 코드 (D/E/N/OFF/LEAVE, 대소문자 무관)")
    ]


class CellPatchResponse(BaseModel):
    cell_id: Annotated[int, Field(description="셀 고유 ID")]
    person_id: Annotated[int, Field(description="이 셀이 속한 근무자 ID")]
    date: Annotated[dt.date, Field(description="근무 날짜")]
    shift_code: Annotated[str, Field(description="수정 후 적용된 근무 코드")]
    confidence_score: Annotated[
        float | None, Field(description="OCR 인식 신뢰도 (0~1). 값이 없으면 null")
    ]
    is_user_corrected: Annotated[
        bool, Field(description="사용자 수정 여부 (수정 후이므로 항상 true)")
    ]
    needs_review: Annotated[
        bool, Field(description="검토 필요 여부 (신뢰도가 0.8 미만이면 true)")
    ]


class ReviewResponse(BaseModel):
    version_id: Annotated[int, Field(description="검토 완료된 근무표 버전 ID")]
    status: Annotated[str, Field(description="검토 후 상태 (reviewed)")]
    reviewed_at: Annotated[dt.datetime, Field(description="검토 완료 처리 시각")]
    image_deleted: Annotated[bool, Field(description="원본 업로드 이미지 삭제 여부")]


class ApplyResponse(BaseModel):
    version_id: Annotated[int, Field(description="확정 처리된 근무표 버전 ID")]
    status: Annotated[str, Field(description="처리 후 상태 (applied)")]
    applied_at: Annotated[dt.datetime | None, Field(description="확정 처리 시각")]
    active_version_id: Annotated[
        int | None, Field(description="해당 월의 현재 확정본 버전 ID")
    ]
    previous_active_version_id: Annotated[
        int | None, Field(description="교체되기 전 확정본 버전 ID (없으면 null)")
    ]


class IgnoreResponse(BaseModel):
    version_id: Annotated[int, Field(description="버린(ignored) 근무표 버전 ID")]
    status: Annotated[str, Field(description="처리 후 상태 (ignored)")]


class MonthScheduleResponse(BaseModel):
    schedule_month: Annotated[ScheduleMonthOut, Field(description="대상 근무표 월 정보")]
    active_version_id: Annotated[int, Field(description="이 달의 확정본 버전 ID")]
    table_type: Annotated[
        str,
        Field(description="근무표 유형 (nursing_assistant=간호조무사 / support_staff=지원인력)"),
    ]
    persons: Annotated[list[PersonOut], Field(description="근무자 목록")]
    cells: Annotated[list[CellOut], Field(description="확정본 근무 셀 목록")]


class PersonScheduleResponse(BaseModel):
    person: Annotated[PersonOut, Field(description="대상 근무자 정보")]
    year: Annotated[int, Field(description="근무표 연도")]
    month: Annotated[int, Field(description="근무표 월 (1~12)")]
    cells: Annotated[list[CellOut], Field(description="이 근무자의 확정본 근무 셀 목록")]


class DiffCell(BaseModel):
    person_name: Annotated[str, Field(description="근무자 이름 (비교 기준 키)")]
    date: Annotated[dt.date, Field(description="근무 날짜")]
    from_shift: Annotated[str, Field(description="확정본의 근무 코드 (변경 전)")]
    to_shift: Annotated[str, Field(description="대상 버전의 근무 코드 (변경 후)")]


class DiffResponse(BaseModel):
    version_id: Annotated[int, Field(description="비교 대상(작업본) 버전 ID")]
    compared_to_version_id: Annotated[
        int | None, Field(description="비교한 확정본 버전 ID (확정본 없으면 null)")
    ]
    changes: Annotated[
        list[DiffCell], Field(description="확정본과 근무 코드가 다른 칸 목록")
    ]
