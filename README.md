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

- **MD 보기**: 문서 생성·편집·저장·삭제, UTF-8 MD 불러오기(2MB), 다운로드, Mermaid 포함 미리보기.
- **UI Work**: 작업 추가·수정·삭제, 할 일/진행 중/완료 상태와 메모 관리. 초기 버전은 작업 보드이며 UI 테스트 실행기는 아직 포함하지 않습니다.
- **ADO WIQL**: UI Work 하단에서 Flat WIQL 실행 및 Work Item 조회(화면 최대 200건).
- 화면 테마(light/dark)와 Mermaid 테마(default/dark/forest/neutral/base)는 별도로 선택하고 SQLite에 저장합니다. MD 수정 후 '미리보기 갱신'을 누르세요.

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

추가 공통 메서드: `list_repositories()`, `compare_commits(repository, base, target)` (커밋 SHA 비교). 모든 네트워크 호출은 비동기이며 타임아웃과 오류 처리를 공통화합니다.

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
