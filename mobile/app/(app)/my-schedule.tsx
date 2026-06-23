/**
 * 내근무 화면 (Phase 10-C에서 구현 예정)
 *
 * 역할: 내 월별 근무 조회 + 공유 링크 생성·삭제
 */

import { View, Text, StyleSheet } from 'react-native';

export default function MyScheduleScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>👤 내근무</Text>
      <Text style={styles.sub}>Phase 10-C에서 구현됩니다.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAFC' },
  text: { fontSize: 20, fontWeight: '600', color: '#1E293B', marginBottom: 8 },
  sub: { fontSize: 14, color: '#94A3B8' },
});
