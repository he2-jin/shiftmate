/**
 * 홈 화면 — 이번 달 근무표 (Phase 10-A 임시 버전)
 *
 * 현재: 로그인한 사용자 이름과 이번 달 정보만 표시
 * Phase 10-B에서 실제 격자 근무표로 교체 예정
 */

import { View, Text, StyleSheet } from 'react-native';
import { useAuthStore } from '@/lib/auth';

export default function HomeScreen() {
  const user = useAuthStore((s) => s.user);

  // 현재 연/월 계산
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1; // getMonth()는 0부터 시작하므로 +1

  return (
    <View style={styles.container}>
      <Text style={styles.greeting}>
        안녕하세요{user ? `, ${user.email.split('@')[0]}` : ''}님
      </Text>
      <Text style={styles.month}>{year}년 {month}월</Text>
      <Text style={styles.placeholder}>근무표를 준비 중입니다.</Text>
      <Text style={styles.sub}>Phase 10-B에서 구현됩니다.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    padding: 24,
    paddingTop: 60,
  },
  greeting: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 4,
  },
  month: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1E40AF',
    marginBottom: 32,
  },
  placeholder: {
    fontSize: 16,
    color: '#64748B',
    textAlign: 'center',
    marginTop: 60,
  },
  sub: {
    fontSize: 13,
    color: '#94A3B8',
    textAlign: 'center',
    marginTop: 8,
  },
});
