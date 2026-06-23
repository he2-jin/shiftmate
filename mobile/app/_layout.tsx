/**
 * 루트 레이아웃 — 앱의 모든 화면을 감싸는 최상위 컴포넌트
 *
 * 역할:
 * 1. 앱 시작 시 저장된 토큰으로 인증 상태 복원
 * 2. 인증 상태에 따라 로그인 화면 ↔ 메인 화면 분기
 * 3. api.ts에 로그아웃 콜백 등록 (토큰 만료 시 자동 로그아웃)
 *
 * 왜 여기서 분기하는가?
 * - 모든 화면 이동이 이 파일을 통해 이루어짐
 * - 미인증 사용자가 메인 화면 URL로 직접 접근해도 로그인 화면으로 보낼 수 있음
 */

import { useEffect } from 'react';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import { Stack, useRouter, useSegments } from 'expo-router';
import { useAuthStore } from '@/lib/auth';
import { setLogoutCallback } from '@/lib/api';

export default function RootLayout() {
  const router = useRouter();
  const segments = useSegments(); // 현재 URL 경로 세그먼트 배열

  // useAuthStore에서 필요한 값/함수를 꺼냄
  // 구조 분해 할당: `const { a, b } = obj` → obj.a, obj.b를 변수로
  const { isAuthenticated, isLoading, logout, loadUserFromStorage } = useAuthStore();

  // useEffect: 컴포넌트가 화면에 처음 나타날 때 한 번 실행
  // [] 빈 배열 = 의존성 없음 = 마운트 시 한 번만 실행
  useEffect(() => {
    // api.ts가 refresh 실패 시 호출할 로그아웃 함수 등록 (순환 참조 우회)
    setLogoutCallback(logout);
    // 저장된 토큰으로 인증 상태 복원
    loadUserFromStorage();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // isAuthenticated 또는 isLoading이 변경될 때마다 화면 분기
  useEffect(() => {
    if (isLoading) return; // 토큰 확인 중엔 이동하지 않음 (스플래시 깜빡임 방지)

    const inAuthGroup = segments[0] === '(auth)';

    if (!isAuthenticated && !inAuthGroup) {
      // 비로그인 상태인데 메인 화면 → 로그인 화면으로
      router.replace('/(auth)/login');
    } else if (isAuthenticated && inAuthGroup) {
      // 로그인 상태인데 로그인 화면 → 메인 화면으로
      router.replace('/(app)');
    }
  }, [isAuthenticated, isLoading, segments]);

  // 토큰 확인 중: 로딩 스피너 표시
  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  // Stack: 화면을 스택으로 쌓는 기본 네비게이터 (뒤로가기 지원)
  // headerShown: false — 각 화면 그룹의 _layout.tsx에서 개별 처리
  return <Stack screenOptions={{ headerShown: false }} />;
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
  },
});
