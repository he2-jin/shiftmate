/**
 * 인증 전역 상태 (Zustand store)
 *
 * 왜 Zustand인가?
 * - React의 useState는 한 컴포넌트 안에서만 유효
 * - Zustand는 앱 어디서든 `useAuthStore()` 한 줄로 같은 상태를 읽고 쓸 수 있음
 * - Redux보다 코드가 훨씬 단순 (boilerplate 없음)
 *
 * 흐름:
 * 1. 앱 시작 → loadUserFromStorage() → SecureStore에 토큰 있으면 자동 복원
 * 2. 로그인/가입 → login() / register() → 토큰 저장 + user 설정
 * 3. 토큰 만료 → api.ts 인터셉터가 자동 refresh → 실패 시 logout() 콜백 호출
 * 4. 로그아웃 → logout() → 서버 토큰 무효화 + 로컬 삭제
 */

import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { api, ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from './api';
import type { UserMeOut, TokenResponse } from './types';

// 이 store가 가지는 상태와 함수의 TypeScript 타입 정의
// `interface`는 객체 형태를 미리 정의하는 TS 문법
interface AuthState {
  user: UserMeOut | null;   // 로그인한 사용자 정보 (미로그인 시 null)
  isAuthenticated: boolean; // 로그인 여부 (빠른 참조용)
  isLoading: boolean;       // 앱 시작 시 토큰 확인 중 여부 (스플래시 화면 처리용)

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUserFromStorage: () => Promise<void>;
}

// create<AuthState>(...)는 "AuthState 타입을 가진 store를 만든다"는 의미
// set: store 상태를 업데이트하는 함수 (React의 setState와 유사)
export const useAuthStore = create<AuthState>((set) => ({
  // 초기 상태
  user: null,
  isAuthenticated: false,
  isLoading: true, // 앱 시작 시 true → loadUserFromStorage 완료 후 false

  // 로그인: 이메일+비밀번호 → 토큰 저장 → 내 정보 가져오기
  login: async (email, password) => {
    // FormData 형식: OAuth2 표준 (백엔드 /auth/login 엔드포인트 요구사항)
    const form = new FormData();
    form.append('username', email);
    form.append('password', password);

    const { data: tokens } = await api.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    // 토큰을 암호화된 저장소에 저장
    await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, tokens.access_token);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refresh_token);

    // 내 계정 정보 조회 (이 시점엔 토큰이 저장됐으므로 인터셉터가 자동 첨부)
    const { data: user } = await api.get<UserMeOut>('/users/me');
    set({ user, isAuthenticated: true });
  },

  // 회원가입: 가입 완료 후 자동 로그인
  register: async (email, password) => {
    await api.post('/auth/register', { email, password });
    // 가입 성공 → 바로 로그인 처리 (사용자가 다시 로그인 안 해도 되게)
    const form = new FormData();
    form.append('username', email);
    form.append('password', password);

    const { data: tokens } = await api.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, tokens.access_token);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refresh_token);

    const { data: user } = await api.get<UserMeOut>('/users/me');
    set({ user, isAuthenticated: true });
  },

  // 로그아웃: 서버 토큰 무효화 → 로컬 토큰 삭제
  logout: async () => {
    try {
      // 서버에 refresh 토큰 무효화 요청 (실패해도 로컬은 반드시 삭제)
      const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
      if (refreshToken) {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch {
      // 서버 오류는 무시 — 아래 finally에서 로컬 토큰은 무조건 삭제됨
    } finally {
      // finally: try/catch 결과와 상관없이 항상 실행 → 보안 우선
      await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
      set({ user: null, isAuthenticated: false });
    }
  },

  // 앱 재시작 시 저장된 토큰으로 인증 상태 복원
  loadUserFromStorage: async () => {
    try {
      const token = await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
      if (!token) return; // 토큰 없으면 로그인 화면으로

      // /users/me 호출 — 토큰 만료 시 api.ts 인터셉터가 자동 refresh 시도
      const { data: user } = await api.get<UserMeOut>('/users/me');
      set({ user, isAuthenticated: true });
    } catch {
      // refresh도 실패한 경우 — 토큰 삭제 (인터셉터에서 이미 처리했지만 방어적으로)
      await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    } finally {
      // 성공/실패 모두 isLoading을 false로 → 스플래시 화면 해제
      set({ isLoading: false });
    }
  },
}));
