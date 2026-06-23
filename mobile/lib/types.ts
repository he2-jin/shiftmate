/**
 * 백엔드 API 응답 타입 정의
 *
 * TypeScript에서 `interface`란?
 * - 객체의 "형태"를 미리 정의하는 문법
 * - 예: UserMeOut 타입의 변수는 반드시 id, email, is_active, created_at을 가져야 함
 * - `export`를 붙이면 다른 파일에서 import해서 사용 가능
 *
 * TypeScript에서 `: 타입`이란?
 * - 변수나 프로퍼티의 타입을 지정하는 문법
 * - `id: number` → id는 숫자여야 함
 * - `email: string` → email은 문자열이어야 함
 * - `is_active: boolean` → is_active는 true/false여야 함
 *
 * `| null`이란?
 * - "이 값은 null일 수도 있다"는 의미
 * - 예: `confidence_score: number | null` → 숫자이거나 null
 *
 * `'D' | 'E' | 'N'`이란?
 * - "이 문자열들 중 하나만 허용"이라는 의미 (Union Type)
 */

// ── 인증 관련 ─────────────────────────────────────────────

/** 로그인 성공 응답 — access_token + refresh_token */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** 토큰 갱신 성공 응답 — 새 access_token만 반환 */
export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

// ── 사용자 관련 ───────────────────────────────────────────

/** 내 계정 정보 응답 */
export interface UserMeOut {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string; // ISO 날짜 문자열 (예: "2026-06-23T00:00:00Z")
}

// ── 근무표 공통 ───────────────────────────────────────────

/** 근무표 월 정보 */
export interface ScheduleMonthOut {
  id: number;
  year: number;
  month: number;
}

/** 근무자 정보 */
export interface PersonOut {
  id: number;
  name: string;
  row_index: number; // 근무표에서 몇 번째 행인지
}

/** 근무 코드 — D(낮), E(저녁), N(밤), OFF(휴무), LEAVE(연차) */
export type ShiftCode = 'D' | 'E' | 'N' | 'OFF' | 'LEAVE' | string;

/** 근무표 버전 상태 — draft(초안), reviewed(검토완료), applied(확정), ignored(폐기) */
export type VersionStatus = 'draft' | 'reviewed' | 'applied' | 'ignored';

/** 셀 하나의 근무 정보 */
export interface CellOut {
  cell_id: number;
  person_id: number;
  date: string;             // "YYYY-MM-DD" 형식
  shift_code: ShiftCode;
  confidence_score: number | null; // OCR 인식 신뢰도 (사용자 직접 입력 시 null)
  is_user_corrected: boolean;      // 사용자가 직접 수정했는지
  needs_review: boolean;           // 재검토 필요 여부 (낮은 신뢰도 등)
}

// ── 근무표 버전 ───────────────────────────────────────────

/** 사진 업로드 후 생성된 버전 응답 */
export interface VersionDetailResponse {
  version_id: number;
  status: VersionStatus;
  schedule_month: ScheduleMonthOut;
  table_type: string;
  persons: PersonOut[];  // `[]`는 배열을 의미 — PersonOut 객체 여러 개
  cells: CellOut[];
}

/** 월별 확정 근무표 응답 */
export interface MonthScheduleResponse {
  schedule_month: ScheduleMonthOut;
  active_version_id: number;
  table_type: string;
  persons: PersonOut[];
  cells: CellOut[];
}

/** 내 근무 조회 응답 */
export interface PersonScheduleResponse {
  person: PersonOut;
  year: number;
  month: number;
  cells: CellOut[];
}

// ── 공유 링크 ─────────────────────────────────────────────

/** 공유 링크 생성/조회 응답 */
export interface ShareOut {
  token: string;
  year: number;
  month: number;
  expires_at: string; // ISO 날짜 문자열
}

/** 공유 링크로 조회한 근무 응답 */
export interface SharedScheduleResponse {
  person: PersonOut;
  year: number;
  month: number;
  cells: CellOut[];
  expires_at: string;
}
