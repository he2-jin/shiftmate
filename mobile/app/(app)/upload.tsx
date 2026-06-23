/**
 * 업로드 화면 (Phase 10-B에서 구현 예정)
 *
 * 역할: 근무표 사진 촬영/선택 → OCR 업로드 → review/[id]로 이동
 */

import { View, Text, StyleSheet } from 'react-native';

export default function UploadScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>📷 업로드</Text>
      <Text style={styles.sub}>Phase 10-B에서 구현됩니다.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAFC' },
  text: { fontSize: 20, fontWeight: '600', color: '#1E293B', marginBottom: 8 },
  sub: { fontSize: 14, color: '#94A3B8' },
});
