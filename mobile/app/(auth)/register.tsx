/**
 * 회원가입 화면
 *
 * 흐름: 이메일·비밀번호·확인 입력 → 클라이언트 검사 → API 가입 → 자동 로그인 → 홈
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

export default function RegisterScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const register = useAuthStore((s) => s.register);

  const handleRegister = async () => {
    setErrorMsg('');

    // 클라이언트 유효성 검사 — 서버 요청 전 빠른 피드백
    if (!email.trim()) {
      setErrorMsg('이메일을 입력해 주세요.');
      return;
    }
    // 간단한 이메일 형식 검사 (@와 . 포함 여부)
    if (!email.includes('@') || !email.includes('.')) {
      setErrorMsg('올바른 이메일 형식을 입력해 주세요.');
      return;
    }
    if (password.length < 8) {
      setErrorMsg('비밀번호는 8자 이상이어야 합니다.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMsg('비밀번호가 일치하지 않습니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      await register(email.trim(), password);
      // 가입 성공 → auth.ts의 register()가 자동 로그인 처리
      // → _layout.tsx가 isAuthenticated 변화 감지 → 홈으로 이동
    } catch (error) {
      setErrorMsg(extractErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>회원가입</Text>
        <Text style={styles.subtitle}>ShiftMate 계정을 만들어 보세요</Text>

        {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}

        <TextInput
          style={styles.input}
          placeholder="이메일"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
          editable={!isSubmitting}
        />

        <TextInput
          style={styles.input}
          placeholder="비밀번호 (8자 이상)"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          editable={!isSubmitting}
        />

        <TextInput
          style={styles.input}
          placeholder="비밀번호 확인"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry
          editable={!isSubmitting}
        />

        <TouchableOpacity
          style={[styles.button, isSubmitting && styles.buttonDisabled]}
          onPress={handleRegister}
          disabled={isSubmitting}
        >
          {isSubmitting
            ? <ActivityIndicator color="#FFFFFF" />
            : <Text style={styles.buttonText}>가입하기</Text>
          }
        </TouchableOpacity>

        <Link href="/(auth)/login" style={styles.link}>
          이미 계정이 있으신가요? <Text style={styles.linkBold}>로그인</Text>
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
    fontSize: 28,
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
