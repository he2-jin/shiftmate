/**
 * 로그인 화면
 *
 * 흐름: 이메일·비밀번호 입력 → 유효성 검사 → API 호출 → 홈으로 이동
 * 실패 시: 백엔드 에러 메시지를 화면 상단에 표시
 */

import { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { Link } from 'expo-router';
import { useAuthStore } from '@/lib/auth';
import { extractErrorMessage } from '@/lib/api';

export default function LoginScreen() {
  // useState: 컴포넌트 내부 상태. [값, 값을 바꾸는 함수] 형태
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const login = useAuthStore((s) => s.login); // store에서 login 함수만 꺼냄

  const handleLogin = async () => {
    setErrorMsg('');

    // 클라이언트 유효성 검사 — 서버 요청 전에 먼저 확인
    if (!email.trim()) {
      setErrorMsg('이메일을 입력해 주세요.');
      return;
    }
    if (!password) {
      setErrorMsg('비밀번호를 입력해 주세요.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email.trim(), password);
      // 로그인 성공 → _layout.tsx가 isAuthenticated 변화 감지 후 자동 이동
    } catch (error) {
      setErrorMsg(extractErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    // KeyboardAvoidingView: 키보드가 올라올 때 입력창이 가려지지 않게 화면을 밀어줌
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled" // 키보드 열린 상태에서 버튼 탭 허용
      >
        <Text style={styles.title}>ShiftMate</Text>
        <Text style={styles.subtitle}>근무표를 스마트하게 관리하세요</Text>

        {/* 에러 메시지 — errorMsg 있을 때만 표시 */}
        {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}

        <TextInput
          style={styles.input}
          placeholder="이메일"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address" // 이메일 키보드 표시
          autoCapitalize="none"        // 첫 글자 대문자 자동 변환 끄기
          autoCorrect={false}
          editable={!isSubmitting}
        />

        <TextInput
          style={styles.input}
          placeholder="비밀번호"
          value={password}
          onChangeText={setPassword}
          secureTextEntry // 비밀번호 가리기
          editable={!isSubmitting}
        />

        <TouchableOpacity
          style={[styles.button, isSubmitting && styles.buttonDisabled]}
          onPress={handleLogin}
          disabled={isSubmitting}
        >
          {isSubmitting
            ? <ActivityIndicator color="#FFFFFF" />
            : <Text style={styles.buttonText}>로그인</Text>
          }
        </TouchableOpacity>

        {/* Link: Expo Router의 화면 전환 컴포넌트 */}
        <Link href="/(auth)/register" style={styles.link}>
          계정이 없으신가요? <Text style={styles.linkBold}>회원가입</Text>
        </Link>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  scroll: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1E40AF',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
    marginBottom: 32,
  },
  error: {
    backgroundColor: '#FEE2E2',
    color: '#DC2626',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    fontSize: 14,
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    marginBottom: 12,
  },
  button: {
    backgroundColor: '#3B82F6',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 20,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '600' },
  link: { textAlign: 'center', color: '#64748B', fontSize: 14 },
  linkBold: { color: '#3B82F6', fontWeight: '600' },
});
