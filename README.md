# 3분할 운동일지 (웹앱)

아이폰 홈 화면에 앱처럼 설치해서 쓰는 운동일지입니다. 한 번 열고 나면 인터넷이 없어도 열려요.
기록은 **그 휴대폰 안에만** 저장되니, 가끔 앱 아래쪽 "기록 백업 파일 저장"으로 백업해 두세요.

## 올리는 방법 (GitHub Pages, 무료, 약 10분)

1. https://github.com 에 가입하고 로그인합니다.
2. 오른쪽 위 **+ → New repository**를 누릅니다.
   - Repository name: `workout` (원하는 이름, 영어로)
   - **Public** 선택 → **Create repository**
3. 새 저장소 화면에서 **uploading an existing file** 링크를 누릅니다.
4. 압축을 푼 폴더 안의 내용을 **그대로** 끌어다 놓습니다.
   (`index.html`, `manifest.webmanifest`, `sw.js`, `README.md`, `icons` 폴더)
   → 아래 **Commit changes**를 누릅니다.
5. 저장소 위쪽 **Settings → 왼쪽 Pages** 메뉴로 갑니다.
   - Source: **Deploy from a branch**
   - Branch: **main**, 폴더 **/(root)** → **Save**
6. 1~2분 기다린 뒤 Pages 화면을 새로고침하면 주소가 나옵니다.
   예) `https://아이디.github.io/workout/`

## 아이폰에 설치

1. 위 주소를 **Safari**로 엽니다. (Chrome에서도 공유 → 홈 화면에 추가로 됩니다)
2. 공유 버튼 → **홈 화면에 추가** → **추가**
3. 이제 홈 화면의 빨간 원판 아이콘으로 실행하면 주소창 없이 앱처럼 열립니다.

## 알아두면 좋은 것

- **기록 위치**: 홈 화면 앱 안에 저장됩니다. Safari로 따로 연 페이지와는 기록이 따로예요.
  홈 화면 아이콘으로만 쓰는 걸 추천해요.
- **백업**: "기록 백업 파일 저장"을 누르면 공유 창이 뜹니다. "파일에 저장"이나 메모, 카톡 나에게 보내기 등으로 보관하세요.
  휴대폰을 바꾸거나 앱을 지웠다 다시 깔았을 때 "백업 파일 불러오기"로 되살릴 수 있어요.
- **루틴 수정**: `index.html`에서 `const ROUTINE=` 아래 목록을 고치면 됩니다.
  고친 뒤 GitHub에 다시 올릴 때는 `sw.js` 맨 위의 `split3-v1`을 `split3-v2`처럼 숫자를 올려야 휴대폰에 새 버전이 반영돼요.
  (앱을 한 번 열었다 닫고 다시 열면 바뀝니다)
- 루틴 출처: 이도황 「더 큰 프레임과 사이즈를 위한 3분할 루틴」 https://www.youtube.com/watch?v=hIJhYHw7vSA
