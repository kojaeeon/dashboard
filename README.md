# Dashboard

NiceGUI 기반 개인 개발자 대시보드입니다. Python 3.11 이상을 사용합니다.

## 실행

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Windows PowerShell: Copy-Item .env.example .env
python -m app.main
```

브라우저에서 http://127.0.0.1:8080 으로 접속합니다.

## 메뉴

- **MD 보기**: 로컬 폴더의 MD 열기·편집·원본 저장, SQLite 문서 저장·삭제, UTF-8 MD 불러오기(2MB), Mermaid 포함 미리보기.
- MD 화면에 저장 위치를 표시합니다. 등록 폴더에서 연 파일은 원본 MD에 저장하며 UTF-8 BOM과 기존 줄바꿈을 유지합니다. 업로드로 불러온 문서와 기본 문서는 SQLite에 저장합니다. 원본이 외부에서 변경되면 덮어쓰지 않고 다시 열도록 안내합니다.
- Mermaid의 전체화면 아이콘으로 크게 볼 수 있습니다. 확대·축소(10~800%), 100% 초기화, 화면 맞춤은 전체화면 안에서만 제공합니다. 큰 다이어그램은 마우스 왼쪽 버튼으로 잡아 끌어 이동하며, 휠·스크롤바·키보드 스크롤도 사용할 수 있습니다. Ctrl+휠은 확대·축소, Esc 또는 닫기는 문서 복귀입니다.
- **Work**: 작업 추가·수정·삭제, 할 일/진행 중/완료 상태와 메모 관리. 업무 작업 보드를 제공합니다. UI 테스트는 별도 UI_TEST 메뉴에서 실행합니다.
- **쿼리조회** — DB2 조회 SQL 입력, 최대 9,999행을 한 그리드에 표시, Markdown 표·CSV 클립보드 복사.
- **ADO WIQL**: Work 작업 보드 위의 접기/펼치기 영역에서 Flat WIQL 실행 및 공통 AG Grid로 동적 컬럼 표시(화면 최대 200건).
- 화면 테마(light/dark)와 Mermaid 테마(default/dark/forest/neutral/base)는 별도로 선택하고 SQLite에 저장합니다. MD 수정 후 '미리보기 갱신'을 누르세요.

## 쿼리조회 · 기존 DB2 연결 클래스 연동

기존 클래스가 DB-API 연결을 반환하도록 로컬 어댑터를 추가합니다. 아래 모듈명과
클래스·메서드 이름은 실제 환경에 맞게 바꾸세요.

```python
# local_db2.py
from your_db2_module import Db2Client


def connect():
    return Db2Client().connect()
```

```dotenv
DASHBOARD_DB2_CONNECT=local_db2:connect
```

대시보드를 재시작한 뒤 **쿼리조회 → 조회 실행**을 누릅니다. 연결 함수는 인자 없이
호출되며 조회용 계정으로 새 DB-API 연결을 반환해야 합니다. 대시보드는 조회가 끝나면
커서와 연결을 닫습니다. 어댑터에서 기존 JDBC 드라이버와 연결 설정을 그대로 사용하세요.

한 번에 SELECT, WITH, VALUES 조회문 한 개를 실행할 수 있습니다. 페이징 없이 최대
9,999행을 표시하며 결과가 더 있으면 건수 옆에 표시합니다. **MD 표 복사**와 **CSV 복사**는
컬럼 헤더와 화면에 표시된 행을 복사합니다. 클립보드는 localhost 또는 HTTPS 접속에서
사용할 수 있습니다.

## 공통 구조

```text
app/main.py                    메뉴와 화면
app/common/markdown_viewer.py   MarkdownViewer / MermaidRenderer
app/common/ado_client.py        AdoConfig / AdoClient
app/common/database.py          SQLite 연결·스키마·CRUD
```

`MermaidRenderer`는 NiceGUI에 번들된 Mermaid JS를 래핑합니다. CDN, 별도 JS 서버 없이 동작하며 MD 코드 펜스에서 공통 클래스를 호출합니다. 다이어그램은 strict 보안 모드로 표시합니다.

```python
from app.common.markdown_viewer import MarkdownViewer, MermaidRenderer
MarkdownViewer.render(markdown_text, theme='dark')
MermaidRenderer.render('flowchart TD\n A --> B', theme='forest')
```

ADO 설정은 `.env` 또는 OS 환경변수에서 읽습니다. `ADO_BASE_URL`은 조직 URL 또는 온프레미스 collection URL, `ADO_PROJECT`는 프로젝트명입니다. Server 버전에 맞춰 `ADO_API_VERSION`을 지정하세요. PAT에는 사용하는 조회 API의 읽기 권한이 필요합니다. PAT와 `.env`는 커밋하거나 SQLite에 저장하지 않습니다.

```python
from app.common.ado_client import AdoClient

async def load_work():
    async with AdoClient() as ado:
        result = await ado.query_wiql('SELECT [System.Id] FROM WorkItems')
        return await ado.get_work_items([w['id'] for w in result['workItems']])
```

추가 공통 메서드: `list_repositories()`, `compare_commits(repository, base, target)` (커밋 SHA 비교). 화면에서의 네트워크 호출은 비동기이며 타임아웃과 오류 처리를 공통화합니다.
WIQL과 작업 항목 상세 조회는 `requests`를 `asyncio.to_thread()`로 실행합니다.
두 조회의 URL은 `ADO_BASE_URL + /_apis/wit/...`이며 프로젝트 경로를 자동으로 붙이지 않습니다. `ADO_BASE_URL`에 정상 동작하는 경로를 지정하세요.
이 두 조회는 사내 환경에 맞춰 인증서 검증을 비활성화(`verify=False`)하며 요청 제한시간은 30초입니다.
상세 조회는 200건씩 나누며 `fields`, `asOf`, 설정된 API 버전을 전달합니다.

SQLite 기본 경로는 `data/dashboard.db`이며 문서 본문, 작업, 전역 테마 설정을 저장합니다. 재시작해도 유지됩니다. 단일 사용자용이며 인증은 포함하지 않습니다. 기본 바인딩은 로컬(127.0.0.1)입니다. 다른 PC 접속이 필요하면 인증 프록시 등 접근 제어를 구성한 뒤 바인딩을 변경하세요. 백업은 앱 종료 후 DB 파일을 복사하세요.

## 폐쇄망 설치

인터넷 연결 환경에서 대상 OS/Python과 같은 환경으로 wheel을 준비합니다.

```bash
pip download . -d wheels
# 대상 PC에서 소스 폴더와 wheels를 함께 복사한 후
pip install --no-index --find-links=wheels .
```

## 검증

```bash
pytest -q
```

ADO는 MockTransport로 테스트하며 실제 사내 ADO 연결은 `.env` 구성 후 검증해야 합니다.


## UI_TEST · 프론트메터 기반 테스트

메뉴별 화면은 `app/pages/markdown.py`, `app/pages/work.py`, `app/pages/ui_test.py`에 있습니다.
`app/menu.py`는 메뉴 구성을, `app/main.py`는 화면 연결을 담당합니다.

최초 설치 때 Chromium을 준비합니다. 이후 실행에는 CDN이나 인터넷 패키지 다운로드가 필요하지 않습니다.
대상 웹사이트 자체의 네트워크 접근은 별개입니다.

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

UI_TEST에서 등록 폴더의 MD를 선택하거나 업로드하고 **단계 확인 → 테스트 실행**을 누르세요.
실행 전 시작 URL과 브라우저 표시 여부를 변경할 수 있습니다.
이 화면에서 수정한 시나리오는 실행 복사본에 저장하며 원본 MD를 덮어쓰지 않습니다.

기본 예시는 `examples/ui-test-smoke.md`입니다. 기존 `workItem` / `step` 형식을 사용합니다.

```yaml
---
workItem:
  serviceNm: 고객 조회
browser:
  base_url: http://127.0.0.1:8080
  timeout: 10000
  headless: false
step:
  - action: menu
    role: tab
    name: Work
  - action: assert_visible
    role: button
    name: 작업 추가
  - action: screenshot
---
```

지원 동작과 요소 찾기 규칙은 예시 MD 본문에 설명되어 있습니다.
`text`는 입력, `menu`는 클릭의 별칭입니다. 실행 가능한 동작만 허용하며 임의 Python/JS 실행은 지원하지 않습니다.
명시적인 selector/id/attr/syscode/role을 먼저 사용하고, 그렇지 않으면 label/텍스트로 찾습니다.
보이는 대상이 여러 개면 정확한 selector 또는 `nth`를 지정하세요.

공통 클래스 `app/common/ui_accelerator.py::PlaywrightAccelerator`가 페이지와 프레임 조작을 담당합니다.
`app/testing/scenario.py`는 프론트메터 검증, `runner.py`는 실행 프로세스 관리,
`worker.py`는 순서대로 실행·중지·캡처·추적을 담당합니다. Windows에서도 대시보드 이벤트 루프와 독립적으로 동작합니다.

결과는 `data/ui_tests/<실행 ID>/`에 보관합니다.
`result.json`에 단계 결과, 실패 이유, 소요 시간, 요소 찾기 방식이 기록됩니다.
실패하면 후속 단계를 건너뛰고 `failure.png`를 남깁니다.
성공 시 `final.png`, screenshot 단계에는 별도 PNG를 남기며 `trace.zip`도 저장합니다.
화면에서 결과 파일을 다운로드할 수 있고 중지 버튼은 실행 브라우저를 정리합니다.

```powershell
# UI 없이 같은 공통 엔진으로 실행
.\.venv\Scripts\python.exe -m app.testing.worker --scenario examples/ui-test-smoke.md --output data/ui_tests/manual --headless
# 로컬 추적 보기
.\.venv\Scripts\python.exe -m playwright show-trace data/ui_tests/manual/trace.zip
```

폐쇄망 배포 시에는 wheel뿐 아니라 같은 OS용 Playwright 브라우저 캐시도 함께 준비해야 합니다.


## 백업 · 프로젝트별 프론트메터

화면은 `app/pages/backup.py`, 공통 엔진은 `app/backup/`에 있습니다.
설정 예시는 `examples/backup.md`를 확인하세요.

1. MD를 선택하거나 불러오고 **설정 기준 폴더**를 확인합니다.
2. 프론트메터 수정 후 **설정 적용**을 누릅니다.
3. 프로젝트 전체·지정 파일·유형별 전체 중 백업 범위를 선택합니다.
4. **계획 만들기**에서 파일 목록, 크기, SHA256과 백업 폴더를 확인합니다.
5. **ZIP 백업 실행**을 누르고 백업 ZIP과 실행 결과 JSON을 받습니다.

모든 범위에서 프로젝트 상대 경로를 유지합니다. 지정 파일은 `files.source`,
유형별은 선택한 `rules`의 root/include/exclude로 파일을 수집합니다.
기존 MD의 `deploy` 및 target 설정은 무시하므로 문서를 그대로 불러와 백업할 수 있습니다.
**FTP COPY** 버튼은 프론트메터의 `sftp` 접속 정보로 연결하여
`files.source`를 `files.target` 원격 경로에 복사합니다. 백업 범위와 관계없이 지정 파일만 전송하며
원격 상위 폴더를 자동 생성하고 기존 파일은 덮어씁니다. 오류 시 후속 파일 전송을 중단합니다.
비밀번호·개인 키 인증과 known_hosts 검증을 지원합니다. 설정 예시는 `examples/backup.md` 본문을 참고하세요.

각 실행은 한국 시간 기준 `title_YYYYMMDD_HHMMSS_ffffff.zip`을 생성하며 기존 ZIP을 덮어쓰지 않습니다.
계획 이후 원본이 바뀌면 실패한 ZIP을 삭제하므로 계획을 다시 만들어야 합니다.
백업 폴더와 실행 결과 폴더는 수집에서 제외하며 프로젝트 밖으로 연결되는 링크는 수집하지 않습니다.
완료·실패 결과는 `data/backup_runs/<실행 ID>/result.json`에 저장됩니다.

## 공통 그리드 · WIQL 결과

`app/common/grid.py`의 `GridColumn`, `CommonGrid`를 여러 화면에서 재사용합니다.
데이터 조회는 호출하는 화면이 담당하며, 공통 그리드는 표시와 사용자 조작을 담당합니다.

```python
from app.common.grid import CommonGrid, GridColumn

grid = CommonGrid(
    grid_id='tasks',
    columns=[
        GridColumn('id', 'ID', width=100, type='number'),
        GridColumn('title', '제목', width=400),
    ],
    selection='multiple',  # 또는 single
    on_row_double_click=lambda row: print(row),
)
grid.set_rows([{'id': 1, 'title': '정기점검 화면 개발'}])
selected = await grid.get_selected_rows()  # async 이벤트 함수 안에서 호출
```

- 정렬, 컬럼별 필터, 결과 내 검색, 페이지 이동, 컬럼 이동·너비 조절을 지원합니다.
- 체크박스 행 선택, 선택 건수, 선택 해제, 필터 초기화, CSV 다운로드를 제공합니다.
- CSV는 현재 필터·정렬을 반영한 전체 페이지를 내보냅니다. 선택한 행만 내보내는 방식은 아닙니다.
- CSV의 수식으로 해석될 수 있는 문자열 앞에는 작은따옴표를 붙입니다.
- `on_row_click`, `on_row_double_click` 콜백에는 행 데이터 dict를 전달합니다. 비동기 콜백도 지원합니다.
- `set_columns(columns)`는 컬럼을 교체하고 기존 데이터를 지웁니다. 이어서 `set_rows(rows)`를 호출하세요.
- `clear()`는 행만 지웁니다. 편집과 SQLite 컬럼 설정 저장은 포함하지 않습니다.

WIQL 화면은 응답의 `columns`에서 `referenceName`, `name`과 순서를 읽습니다.
`SELECT`에 사용자 정의 필드를 추가하면 해당 컬럼도 표시합니다.
기본은 접힌 상태이며 헤더 클릭으로 입력창과 결과를 펼칩니다. 실행 버튼은 펼친 영역 오른쪽 위에 있습니다.
상세 조회는 `GET wit/workitems?ids=...`를 사용합니다. 선택 필드와 WIQL 응답의 `asOf`를 전달하고, WIQL의 ID 순서로 행을 배치합니다.
사용자 객체는 표시명으로, 설명·인수 조건·재현 단계 HTML은 일반 텍스트로 표시합니다.
행을 더블클릭하면 조회한 컬럼의 상세 내용이 열립니다.
Flat 쿼리만 지원하며, 최대 200건 표시 제한과 환경변수 기반 ADO 설정은 유지합니다.


## 일정

`일정` 메뉴에서 월·주·일 달력을 볼 수 있습니다.

- 날짜 클릭 또는 **일정 추가**: 제목, 분류, 날짜/시간, 종일 여부, 메모 등록
- 일정 클릭: 수정 및 확인 후 삭제
- 드래그 이동 및 크기 조절: 변경된 시작·종료 시간을 SQLite에 저장
- 업무·개인·회의·마감 분류별 색상, 현재 조회 기간의 일정 목록
- **새로고침**: 다른 브라우저에서 변경한 일정 다시 조회

시간은 브라우저·서버의 시간대와 무관하게 `Asia/Seoul` 기준입니다.
종일 일정의 입력 종료일은 마지막 일정일이며, DB/FullCalendar 이벤트의
`end`는 그 다음 날짜(포함하지 않는 경계)입니다. 예: 11월 9일 하루 일정은
`start=2026-11-09`, `end=2026-11-10`으로 저장됩니다.

기존 `DASHBOARD_DB_PATH` DB에 `schedule_events` 테이블을 자동 생성합니다.
일정은 이 대시보드 DB를 사용하는 사용자끼리 공유됩니다.
FullCalendar Standard 6.1.19와 Luxon은 로컬에 포함되므로 일정표를 위해
CDN 연결이나 npm 설치를 할 필요가 없습니다. 기본 CRUD에는 추가 Python
의존성도 필요 없습니다. 반복 일정·외부 캘린더 동기화·알림은 포함하지 않습니다.

공통 캘린더는 `app/common/calendar.py` / `calendar.js`, 데이터 처리는
`app/scheduling/repository.py` / `service.py`, 화면은 `app/pages/schedule.py`에 있습니다.

### 마인드맵

마인드맵 메뉴에서 노드·관계·사용자 정의 유형을 편집하고 SQLite에 저장합니다. 전체화면, 확대·축소, 마우스 이동과 DOT·Mermaid·JSON 가져오기/내보내기를 지원합니다. 변환 범위와 단축키는 [마인드맵 안내](docs/mindmap-design.md)를 참고하세요.
