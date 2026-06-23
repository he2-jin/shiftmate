/**
 * 인증 화면 그룹 레이아웃 (로그인, 회원가입)
 *
 * 왜 (auth) 폴더인가?
 * - Expo Router에서 `(폴더명)`은 URL에 나타나지 않는 그룹
 * - 로그인(/login), 회원가입(/register)처럼 인증 전 화면들을 묶어서 관리
 * - URL은 `/(auth)/login` 대신 `/login`으로 표시됨
 */

import { Stack } from 'expo-router';

export default function AuthLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,        // 헤더(뒤로가기 버튼 등) 숨김 — 화면에서 직접 처리
        animation: 'slide_from_right', // 화면 전환 애니메이션
      }}
    />
  );
}
