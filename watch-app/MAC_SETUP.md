# Apple Silicon 맥북 — 워치 앱 설치 빠른 안내

이 폴더는 기존 운동일지와 연결되는 Wear OS **개발 소스**이며, APK가 아닙니다.

## 가장 쉬운 빌드 경로

1. Android Studio(Apple Silicon용)와 Android SDK Platform 35를 설치합니다.
2. macOS Finder에서 `watch-app` 폴더를 엽니다.
3. Terminal 앱을 실행하고 `cd ` 뒤에 `watch-app` 폴더를 끌어다 놓고 Enter를 누릅니다.
4. 아래 명령어를 실행합니다.

   ```bash
   bash ./setup-mac.command
   ```

5. 스크립트는 공식 Gradle 8.9를 다운로드하고, **빠져 있던 Gradle Wrapper 파일을 공식 도구로 생성**한 뒤 `app-debug.apk` 빌드를 시도합니다.
6. 성공하면 다음 위치에 APK가 생깁니다.

   `watch-app/app/build/outputs/apk/debug/app-debug.apk`

7. Android Studio에서 `watch-app`을 열고, 갤럭시 워치를 Wi-Fi 디버깅으로 연결한 뒤 Run으로 설치하세요.

## 왜 이런 방식인가요?

이 프로젝트의 Android Gradle Plugin 버전은 **8.7.3**, 호환되는 Gradle 버전은 **8.9**, JDK는 **17 이상**입니다. 이전에 알려드린 `8.9.2` 플러그인 변경은 적용하지 마세요. 기존 `build.gradle`을 유지하세요.

이 작업 환경은 Android SDK와 Gradle을 다운로드할 수 없어서 **실제 APK 빌드 성공 여부를 확인하지 못했습니다.** 스크립트는 맥북의 인터넷 연결과 Android Studio 설치를 이용합니다. 오류가 나오면 Terminal 창의 마지막 오류 메시지를 전달해 주세요.

**기록 안전:** 서버 연결 전에 휴대폰 PWA의 `기록 백업 파일 저장` 기능으로 JSON 백업하세요. 서버에 영구 저장소가 없으면 데이터 손실 위험이 있습니다.
