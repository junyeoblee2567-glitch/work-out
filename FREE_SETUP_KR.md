# 갤럭시 워치 운동일지 — 0원 동기화 서버 설치

## 반드시 먼저
- 휴대폰 운동일지에서 **JSON 백업 파일 저장** (기록 탭)
- Render Web Service는 **Free** 유지, Persistent Disk 없음
- GitHub Pages 기존 웹앱 변경 전 백업
- Supabase Free가 장기 미사용 시 일시 정지될 수 있고, Render Free는 절전으로 초기 연결이 지연될 수 있음. 자동 백업 서비스가 아니므로 휴대폰 JSON 백업을 정기적으로 보관.

## 1. Supabase
1. https://supabase.com/dashboard → New Project → Free 플랜
2. 프로젝트 이름 workout-sync, DB 비밀번호 저장, 지역 Singapore(선택 가능한 경우)
3. 프로젝트 화면 상단 **Connect** → **Session pooler** 선택. `postgresql://...:5432/postgres` 형태의 **전체 connection string** 확보.
4. `[YOUR-PASSWORD]` 같은 표기가 있으면 실제 DB 비밀번호로 대체. 비밀번호에 `@`, `:`, `/`, `#`, `%` 등이 있으면 URL 인코딩이 필요하므로 간단한 영숫자 비밀번호를 사용하거나 URL 인코딩한다.
5. 연결 문자열과 DB 비밀번호는 **절대 GitHub 업로드 금지**.

## 2. GitHub
기존 `workout-sync` 저장소 최상위의 파일 세 개를 이 ZIP의 `server` 폴더 안에 있는 것으로 교체:
- `app.py`
- `requirements.txt`
- `Dockerfile`
기존 파일과 교체할 때 GitHub Commit changes를 누른다.

## 3. Render
New Web Service → Repository workout-sync → Docker → main → Free.
Environment Variables:
- `DATABASE_URL` : Supabase **Session pooler** 연결 문자열 (비밀)
- `WORKOUT_TOKEN` : 길이 24자 이상의 임의 비밀 문자열. 워치/휴대폰에서 같은 값을 사용.
- `WORKOUT_ORIGINS` : 예: `https://your-id.github.io` (기존 웹앱 주소에서 `/workout/` 등 경로를 빼고 origin만 입력)
- `WORKOUT_DB` : 사용하지 않음. 기존에 추가했다면 삭제.
Root Directory 빈 칸 (저장소 루트에 3개 파일이 있을 때).
영구 디스크 필요 없음. Deploy Web Service 실행.
배포 완료 후 Render URL 뒤에 `/api/health`를 붙여 `{"status":"ok"}`가 뜨는지 확인.

## 4. 휴대폰
기존 PWA의 JSON 기록 백업을 확보한 뒤, 원래 GitHub Pages 저장소에 `web` 폴더 **내용물**(web 폴더 자체가 아님)을 업로드한다.
기존 홈 화면 앱은 삭제하지 않는다. 업데이트가 보이지 않으면 앱을 닫고 다시 연다.
운동일지에서 `갤럭시 워치 동기화` → Render URL + `WORKOUT_TOKEN` 입력 → `연결 / 새로고침`.
서버가 비어 있을 때만 기존 휴대폰 기록을 최초 업로드하는 과정을 확인한다.

## 5. 워치
기존 설치한 워치 앱 재설치 필요 없음.
워치 앱의 `서버 연결 설정`에서 동일한 Render HTTPS URL과 `WORKOUT_TOKEN` 입력.
운동 종목 표시, 세트 저장, 휴대폰 반영 확인.

## 상태/제약
- 기존 HTTP API 경로/데이터 구조를 유지한 서버 교체본입니다.
- Python 구문 검사 통과. 실제 Supabase 접속 및 Render 배포는 이 환경에서 검증하지 못했습니다.
- Supabase Free/Render Free의 이용 조건과 한도는 바뀔 수 있습니다.
- Render가 절전 상태에서 깨어나면 첫 요청이 지연되거나 타임아웃이 발생할 수 있어 앱에서 다시 연결해야 할 수 있습니다.
- 초기 업로드 전 기존 운동기록 백업 필수. 워치 오프라인 저장은 아직 지원하지 않습니다.
