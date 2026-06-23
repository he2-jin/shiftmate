/**
 * OCR 검토 화면 (Phase 10-B에서 구현 예정)
 *
 * 역할: 업로드된 근무표 OCR 결과 검토·수정·확정
 * [id]: Expo Router의 동적 경로 — version_id가 URL에 들어옴
 *       예: /review/42 → id = "42"
 */

import { View, Text, StyleSheet } from 'react-native';
import { useLocalSearchParams } from 'expo-router';

export default function ReviewScreen() {
  // useLocalSearchParams: URL의 동적 파라미터를 가져오는 Expo Router 훅
  // /review/42 로 진입하면 params.id === "42"
  const { id } = useLocalSearchParams<{ id: string }>();

  return (
    <View style={styles.container}>
      <Text style={styles.text}>검토 화면 #{id}</Text>
      <Text style={styles.sub}>Phase 10-B에서 구현됩니다.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAFC' },
  text: { fontSize: 20, fontWeight: '600', color: '#1E293B', marginBottom: 8 },
  sub: { fontSize: 14, color: '#94A3B8' },
});
