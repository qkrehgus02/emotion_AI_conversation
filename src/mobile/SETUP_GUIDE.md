# 모바일 앱 설정 가이드

## 빠른 시작

### 1. 백엔드 서버 IP 주소 확인

먼저 백엔드 서버가 실행 중인 컴퓨터의 로컬 네트워크 IP 주소를 확인합니다:

**Mac/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```bash
ipconfig
```

예: `192.168.1.100`

### 2. API URL 설정

[mobile/src/constants/config.js](src/constants/config.js) 파일을 열고 IP 주소를 업데이트하세요:

```javascript
export const API_BASE_URL = __DEV__
  ? 'http://192.168.1.100:8000'  // 여기에 실제 IP 주소 입력!
  : 'https://your-production-backend.com';
```

**중요**:
- `localhost`나 `127.0.0.1`은 작동하지 않습니다!
- 실제 로컬 네트워크 IP 주소를 사용해야 합니다
- 백엔드 서버의 포트 번호도 확인하세요 (기본값: 8000)

### 3. 백엔드 서버 실행

모바일 앱을 실행하기 전에 백엔드 서버를 먼저 실행하세요:

```bash
cd ../backend
# 백엔드 실행 명령어
```

### 4. 모바일 앱 실행

#### 방법 1: Expo Go 앱 사용 (가장 간단)

1. 스마트폰에 Expo Go 앱 설치:
   - iOS: App Store에서 "Expo Go" 검색
   - Android: Play Store에서 "Expo Go" 검색

2. 모바일 앱 디렉토리로 이동:
```bash
cd mobile
```

3. 개발 서버 시작:
```bash
npm start
```

4. 스마트폰으로 QR 코드 스캔:
   - iOS: 카메라 앱으로 스캔
   - Android: Expo Go 앱에서 스캔

**주의**: 스마트폰과 컴퓨터가 같은 WiFi 네트워크에 연결되어 있어야 합니다!

#### 방법 2: Android 에뮬레이터 사용

1. Android Studio 설치 및 에뮬레이터 생성
2. 에뮬레이터 실행
3. 다음 명령어 실행:
```bash
npm run android
```

#### 방법 3: iOS 시뮬레이터 사용 (Mac만 가능)

1. Xcode 설치
2. 다음 명령어 실행:
```bash
npm run ios
```

## 문제 해결

### "Network request failed" 에러

**원인**: 앱이 백엔드 서버에 연결할 수 없음

**해결 방법**:
1. 백엔드 서버가 실행 중인지 확인
2. `config.js`의 IP 주소가 올바른지 확인
3. 스마트폰과 컴퓨터가 같은 WiFi에 연결되어 있는지 확인
4. 방화벽이 8000번 포트를 차단하고 있지 않은지 확인

테스트 방법:
```bash
# 스마트폰의 브라우저에서 다음 URL 접속
http://YOUR_IP:8000/docs
```

접속이 되면 백엔드는 정상이고, 앱 설정에 문제가 있는 것입니다.

### 마이크 권한 에러

**해결 방법**:
- iOS: 설정 > 개인정보 보호 > 마이크 > Expo Go 허용
- Android: 설정 > 앱 > Expo Go > 권한 > 마이크 허용

### 음성 녹음이 작동하지 않음

**원인**: 에뮬레이터는 마이크 지원이 제한적

**해결 방법**:
- 실제 기기에서 테스트 (Expo Go 앱 사용)
- 또는 텍스트 입력으로 먼저 테스트

### Expo Go 앱에서 앱이 로드되지 않음

**해결 방법**:
1. Expo Go 앱을 최신 버전으로 업데이트
2. 개발 서버를 재시작 (Ctrl+C 후 `npm start`)
3. Expo 캐시 삭제:
```bash
npx expo start --clear
```

## 개발 팁

### 빠른 새로고침

코드를 수정하면 자동으로 앱이 새로고침됩니다. 수동으로 새로고침하려면:
- iOS: Cmd+R
- Android: R 키 2번 빠르게 누르기
- 또는 앱을 흔들기 (실제 기기)

### 디버그 메뉴

- iOS: Cmd+D
- Android: Cmd+M (Mac) 또는 Ctrl+M (Windows/Linux)
- 또는 앱을 흔들기 (실제 기기)

### 로그 확인

터미널에서 실시간 로그를 확인할 수 있습니다:
```bash
npm start
# 그리고 터미널에서 로그 확인
```

또는 디버그 메뉴에서 "Remote JS Debugging" 활성화

### 성능 모니터 표시

디버그 메뉴 > "Show Performance Monitor"

## 배포 준비

### 1. 프로덕션 API URL 설정

`config.js`에서 프로덕션 URL 업데이트:

```javascript
export const API_BASE_URL = __DEV__
  ? 'http://192.168.1.100:8000'
  : 'https://your-actual-backend.com';  // 실제 배포된 백엔드 URL
```

### 2. 앱 정보 업데이트

`app.json`에서 앱 정보 수정:
- `name`: 앱 이름
- `bundleIdentifier` (iOS): 고유 식별자 (예: com.yourcompany.chatbot)
- `package` (Android): 패키지 이름

### 3. 아이콘 및 스플래시 이미지 교체

다음 파일들을 교체하세요:
- `assets/icon.png` (1024x1024)
- `assets/adaptive-icon.png` (1024x1024, Android)
- `assets/splash-icon.png` (1242x2436)

### 4. EAS 빌드 (권장)

```bash
# EAS CLI 설치
npm install -g eas-cli

# 로그인
eas login

# 빌드 설정
eas build:configure

# Android APK 빌드
eas build --platform android --profile production

# iOS 빌드 (Apple Developer 계정 필요)
eas build --platform ios --profile production
```

## 자주 묻는 질문

**Q: 왜 localhost가 작동하지 않나요?**
A: 모바일 기기와 컴퓨터는 서로 다른 네트워크 호스트입니다. localhost는 각 기기 자신을 가리키므로, 로컬 네트워크 IP를 사용해야 합니다.

**Q: WiFi가 없으면 어떻게 하나요?**
A: USB 케이블로 연결하고 USB 디버깅을 활성화하거나, 컴퓨터를 핫스팟으로 사용할 수 있습니다.

**Q: 앱 크기가 얼마나 되나요?**
A: Expo Go로 개발할 때는 작지만, 독립 앱으로 빌드하면 ~50-100MB 정도 됩니다.

**Q: 네이티브 코드를 추가할 수 있나요?**
A: 네, `npx expo prebuild`로 네이티브 프로젝트를 생성할 수 있습니다. 하지만 그 후에는 Expo Go를 사용할 수 없고 네이티브 빌드가 필요합니다.

## 추가 리소스

- [Expo 공식 문서](https://docs.expo.dev/)
- [React Native 공식 문서](https://reactnative.dev/)
- [React Navigation 문서](https://reactnavigation.org/)
- [Expo AV 문서](https://docs.expo.dev/versions/latest/sdk/av/)
