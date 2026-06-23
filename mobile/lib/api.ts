/**
 * axios HTTP 클라이언트 설정
 *
 * 이 파일이 하는 일:
 * 1. 모든 API 요청에 자동으로 JWT 토큰을 헤더에 붙임
 * 2. 토큰이 만료되어 401 에러가 오면 자동으로 refresh하고 재시도
 * 3. refresh도 실패하면 로그아웃 처리
 *
 * 왜 `10.0.2.2`인가?
 * - Android 에뮬레이터는 가상 기기라 `localhost`가 에뮬레이터 자신을 가리킴
 * - 개발 PC의 localhost에 접근하려면 `10.0.2.2`라는 특수 IP를 써야 함
 */

import axios from 'axios';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// SecureStore에 토큰을 저장할 때 사용하는 키 이름
export const ACCESS_TOKEN_KEY = 'shiftmate_access_token';
export const REFRESH_TOKEN_KEY = 'shiftmate_refresh_token';

// 플랫폼에 따라 백엔드 주소를 다르게 설정
const BASE_URL =
  Platform.OS === 'android'
    ? 'http://10.0.2.2:8000/api' // Android 에뮬레이터 → 개발 PC의 8000 포트
    : 'http://localhost:8000/api'; // iOS 시뮬레이터 / 웹

// axios 인스턴스 생성 — baseURL을 설정하면 api.get('/users/me') 처럼 짧게 쓸 수 있음
export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000, // 15초 이내 응답 없으면 에러 처리
  headers: { 'Content-Type': 'application/json' },
});

// ── 로그아웃 콜백 주입 ────────────────────────────────────
// auth.ts에서 직접 import하면 순환 참조(api → auth → api) 오류가 발생함
// 대신 앱 시작 시 _layout.tsx에서 이 함수로 로그아웃 함수를 등록해둠
let _logoutCallback: (() => Promise<void>) | null = null;

/** 앱 시작 시 한 번 호출 — refresh 실패 시 사용할 로그아웃 함수 등록 */
export function setLogoutCallback(fn: () => Promise<void>) {
  _logoutCallback = fn;
}

// ── Request 인터셉터 ──────────────────────────────────────
// 모든 요청이 나가기 전에 실행됨 — SecureStore에서 토큰을 읽어 헤더에 첨부
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
  if (token) {
    // `Authorization: Bearer <토큰>` 형식이 백엔드가 기대하는 인증 헤더
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response 인터셉터 ─────────────────────────────────────
// 모든 응답이 들어올 때 실행됨 — 401이면 토큰 갱신 후 재시도
api.interceptors.response.use(
  // 정상 응답은 그대로 통과
  (response) => response,

  // 에러 응답 처리
  async (error) => {
    const originalRequest = error.config;

    // 401(인증 만료)이고 아직 재시도 안 한 요청인 경우만 처리
    // _retry 플래그로 무한 루프 방지
    if (error.response?.status === 401 && !originalRequest._retry) {
      // refresh, login 요청 자체가 401이면 로그아웃 (무한 루프 방지)
      const url: string = originalRequest.url ?? '';
      if (url.includes('/auth/refresh') || url.includes('/auth/login')) {
        return Promise.reject(error);
      }

      originalRequest._retry = true; // 재시도 표시

      try {
        const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
        if (!refreshToken) throw new Error('refresh token 없음');

        // refresh 요청 — api 인스턴스 대신 axios 직접 사용 (인터셉터 우회)
        const { data } = await axios.post<{ access_token: string }>(
          `${BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken },
        );

        // 새 access_token 저장 후 원래 요청 재시도
        await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch {
        // refresh도 실패 → 토큰 삭제 후 로그아웃
        await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
        await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
        if (_logoutCallback) await _logoutCallback();
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

// ── 에러 메시지 추출 헬퍼 ─────────────────────────────────
/** axios 에러에서 백엔드 detail 메시지 추출. 실패 시 기본 메시지 반환 */
export function extractErrorMessage(error: unknown): string {
  if (
    error &&
    typeof error === 'object' &&
    'response' in error &&
    (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
  ) {
    return String((error as { response: { data: { detail: string } } }).response.data.detail);
  }
  return '네트워크 오류가 발생했습니다. 다시 시도해 주세요.';
}
