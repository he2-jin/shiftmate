/**
 * 메인 앱 레이아웃 — 하단 탭 네비게이션
 *
 * 탭 4개: 근무표(홈) · 업로드 · 내근무 · 설정
 * review/[id] 화면은 탭바에서 숨김 (업로드 후 자동으로 진입하는 화면)
 *
 * 왜 Tabs인가?
 * - 사용자가 화면 하단 탭을 눌러 주요 기능을 빠르게 전환
 * - `(app)/_layout.tsx`에서 한 번 정의하면 하위 모든 화면에 탭이 자동으로 표시됨
 */

import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

// Ionicons: Expo 기본 제공 아이콘 모음 (이름 목록: https://ionic.io/ionicons)
// `name` prop에 아이콘 이름을 문자열로 넘김
type IoniconsName = React.ComponentProps<typeof Ionicons>['name'];

interface TabConfig {
  name: string;     // Expo Router 파일 이름 (확장자 없이)
  title: string;    // 탭 하단에 표시될 텍스트
  icon: IoniconsName;
}

const TABS: TabConfig[] = [
  { name: 'index',       title: '근무표',  icon: 'calendar-outline' },
  { name: 'upload',      title: '업로드',  icon: 'camera-outline' },
  { name: 'my-schedule', title: '내근무',  icon: 'person-outline' },
  { name: 'settings',    title: '설정',    icon: 'settings-outline' },
];

export default function AppLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#3B82F6',   // 선택된 탭 색상
        tabBarInactiveTintColor: '#94A3B8', // 비선택 탭 색상
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#E2E8F0',
        },
      }}
    >
      {TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.title,
            // tabBarIcon: 탭 아이콘 렌더 함수 — focused(선택 여부), color, size를 받음
            tabBarIcon: ({ focused, color, size }) => (
              <Ionicons
                // focused 시 채워진 아이콘, 아닐 때 outline 아이콘
                name={(focused ? tab.icon.replace('-outline', '') : tab.icon) as IoniconsName}
                size={size}
                color={color}
              />
            ),
          }}
        />
      ))}

      {/* review/[id] — 탭바에서 숨김, 업로드 후 코드로 직접 이동 */}
      <Tabs.Screen
        name="review/[id]"
        options={{ href: null }} // href: null → 탭에 표시하지 않음
      />
    </Tabs>
  );
}
