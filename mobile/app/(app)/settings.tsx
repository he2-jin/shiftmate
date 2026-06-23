/**
 * 설정 화면 (Phase 10-C에서 구현 예정)
 *
 * 역할: 근무자 연결 + 로그아웃
 */

import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useAuthStore } from '@/lib/auth';

export default function SettingsScreen() {
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    // Alert: iOS/Android 기본 확인 다이얼로그
    Alert.alert('로그아웃', '정말 로그아웃 하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '로그아웃',
        style: 'destructive',
        onPress: logout,
      },
    ]);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>설정</Text>
      {user && <Text style={styles.email}>{user.email}</Text>}

      <Text style={styles.sub}>근무자 연결 기능은 Phase 10-C에서 구현됩니다.</Text>

      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>로그아웃</Text>
      </TouchableOpacity>
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
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1E293B',
    marginBottom: 8,
  },
  email: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 32,
  },
  sub: {
    fontSize: 14,
    color: '#94A3B8',
    marginBottom: 32,
  },
  logoutBtn: {
    backgroundColor: '#FEE2E2',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
  },
  logoutText: { color: '#DC2626', fontSize: 16, fontWeight: '600' },
});
