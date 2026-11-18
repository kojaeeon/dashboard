import json
import re
import pytest
from nicegui import ui
from app.common.database import Database


@pytest.mark.asyncio
async def test_document_and_work_flow(user, tmp_path, monkeypatch):
    import app.main as main
    monkeypatch.setattr(main, 'db', Database(str(tmp_path / 'ui.db')))
    # NiceGUI's fixture resets routes; register the page for this test.
    ui.page('/')(main.index)
    await user.open('/')
    await user.should_see('Markdown Workspace')
    user.javascript_rules[re.compile(r'.*markdown-save-snapshot.*')] = lambda _: main.markdown.SAMPLE
    user.find(kind=ui.select, content='Mermaid 테마').click()
    user.find('forest').click()
    assert main.db.setting('mermaid_theme') == 'forest'
    user.find(kind=ui.select, content='화면 테마').click()
    user.find('다크').click()
    assert main.db.setting('app_theme') == 'dark'
    user.find('저장').click()
    await user.should_see('문서를 저장했습니다.')
    assert main.db.list('documents')[0]['title'] == '시작하기'
    user.find('Work').click()
    user.find('작업 추가').click()
    user.find(kind=ui.input, content='제목').type('첫 작업')
    user.find(marker='work-save').click()
    assert main.db.list('work_items')[0]['title'] == '첫 작업'
    user.find('UI_TEST').click()
    await user.should_see('프론트메터로 정의하는 UI 테스트')
    await user.should_see('9단계 · 프론트메터 검증 완료')
    user.find(kind=ui.tab, content='백업').click()
    await user.should_see('프론트메터 설정')
    await user.should_not_see('배포 타깃 루트')
    await user.should_not_see('배포 실행')
    user.find(kind=ui.button, content='계획 만들기').click()
    await user.should_see('계획 확인 완료 · 위 실행 버튼으로 이 파일들을 처리합니다.', retries=30)


@pytest.mark.asyncio
async def test_mixed_markdown(user):
    from app.common.markdown_viewer import MarkdownViewer

    @ui.page('/mixed')
    def mixed():
        MarkdownViewer.render('---\ntitle: Example\ntags: [docs, code]\n---\n# Mixed document\n```python\nprint("hello")\n```\n```mermaid\nflowchart TD\n A --> B\n```\nAfter diagram')

    await user.open('/mixed')
    await user.should_see('Frontmatter')
    await user.should_see('Mixed document')
    await user.should_see('After diagram')
    assert len(user.find(kind=ui.mermaid).elements) == 1
    assert len(user.find(kind=ui.code).elements) == 2


@pytest.mark.asyncio
async def test_local_edit_saves_original_file_from_live_editor(user, tmp_path):
    from app.pages.markdown import render
    folder = tmp_path / 'docs'
    folder.mkdir()
    path = folder / 'local.md'
    path.write_bytes(b'\xef\xbb\xbf# Original\r\n')
    db = Database(str(tmp_path / 'local.db'))
    db.add_folder(str(folder))

    @ui.page('/local-save')
    def local_page():
        render(db)

    latest = '# 최신 수정\n```java\nString value = "한글 😀";\n```\n'
    user.javascript_rules[re.compile(r'.*markdown-save-snapshot.*')] = lambda _: latest
    await user.open('/local-save')
    user.find('docs').click()
    user.find('local.md').click()
    # Simulate a browser snapshot newer than the Python editor value.
    user.find('저장').click()
    await user.should_see('원본 MD 파일을 저장했습니다.')
    assert path.read_bytes() == b'\xef\xbb\xbf' + latest.replace('\n', '\r\n').encode('utf-8')
    assert db.list('documents') == []
    user.find('local.md').click()
    user.find(marker='text-mode').click()
    assert next(iter(user.find(kind=ui.codemirror).elements)).value == latest


@pytest.mark.asyncio
async def test_sqlite_save_uses_latest_browser_content(user, tmp_path):
    from app.pages.markdown import render
    db = Database(str(tmp_path / 'sqlite.db'))

    @ui.page('/sqlite-save')
    def sqlite_page():
        render(db)

    latest = {'content': '# First edit\n```python\nprint("😀")\n```'}
    user.javascript_rules[re.compile(r'.*markdown-save-snapshot.*')] = lambda _: latest['content']
    await user.open('/sqlite-save')
    user.find('저장').click()
    await user.should_see('문서를 저장했습니다.')
    assert db.list('documents')[0]['content'] == latest['content']
    latest['content'] = '# Second edit\n```java\nString s = "한글";\n```'
    user.find('저장').click()
    # Wait for the asynchronous click handler, not an earlier notification.
    import asyncio
    for _ in range(50):
        if db.list('documents')[0]['content'] == latest['content']:
            break
        await asyncio.sleep(.01)
    assert len(db.list('documents')) == 1
    assert db.list('documents')[0]['content'] == latest['content']


@pytest.mark.asyncio
async def test_backup_page_creates_zip_and_requires_new_plan(user, tmp_path, monkeypatch):
    import yaml
    from zipfile import ZipFile
    from app.pages import backup
    from app.backup import executor

    project = tmp_path / 'project'
    project.mkdir()
    (project / 'hello.txt').write_text('백업 내용', encoding='utf-8')
    sample = tmp_path / 'backup.md'
    sample.write_text('---\n' + yaml.safe_dump({
        'title': 'UI 백업', 'project': {'root': str(project)},
        'backup': {'directory': str(tmp_path / 'archives')},
        'deploy': {'method': 'ftp'},
    }) + '---\n', encoding='utf-8')
    monkeypatch.setattr(backup, 'SAMPLE_PATH', sample)
    monkeypatch.setattr(executor, 'ROOT', tmp_path)
    db = Database(str(tmp_path / 'backup.db'))

    @ui.page('/backup-only')
    def backup_page():
        backup.render(db)

    await user.open('/backup-only')
    user.find(kind=ui.button, content='계획 만들기').click()
    await user.should_see('계획 확인 완료 · 위 실행 버튼으로 이 파일들을 처리합니다.', retries=30)
    user.find(kind=ui.button, content='ZIP 백업 실행').click()
    await user.should_see('성공 · 1/1개 완료', retries=30)
    await user.should_see('백업 ZIP')
    button = next(iter(user.find(kind=ui.button, content='ZIP 백업 실행').elements))
    assert not button.enabled
    with ZipFile(next((tmp_path / 'archives').glob('*.zip'))) as archive:
        assert archive.read('hello.txt').decode('utf-8') == '백업 내용'
    assert list((tmp_path / 'data/backup_runs').glob('*/result.json'))


@pytest.mark.asyncio
async def test_query_menu_displays_grid_and_sends_clipboard_text(user, monkeypatch, tmp_path):
    from app import main
    from app.common.database import Database

    from app.common.db2_query import QueryResult

    def execute_query(sql, factory_path):
        assert sql == "SELECT '한글' AS dup, 20 AS dup;"
        assert factory_path == 'local_db2:connect'
        return QueryResult(('dup', 'dup'), [('한글', 20)], False)

    monkeypatch.setenv('DASHBOARD_DB2_CONNECT', 'local_db2:connect')
    monkeypatch.setattr(main.query, 'execute_query', execute_query)
    monkeypatch.setattr(main, 'db', Database(str(tmp_path / 'ui.db')))
    ui.page('/')(main.index)
    copied = []

    def clipboard(match):
        copied.append(json.loads(match[1]))
        return True

    user.javascript_rules[re.compile(r'.*navigator\.clipboard\.writeText\((.*?)\);', re.DOTALL)] = clipboard
    await user.open('/')
    user.find(kind=ui.tab, content='쿼리조회').click()
    user.find(kind=ui.textarea, content='DB2 SQL').type("SELECT '한글' AS dup, 20 AS dup;")
    user.find('조회 실행').click()
    await user.should_see('1건', retries=30)

    grid = next(iter(user.find(marker='db2-query-result').elements))
    assert grid.options['pagination'] is False
    assert [column['headerName'] for column in grid.options['columnDefs']] == ['dup', 'dup']
    assert grid.options['rowData'] == [{'col_0': '한글', 'col_1': '20'}]

    user.find('MD 표 복사').click()
    await user.should_see('MD 표 복사 완료', retries=30)
    user.find('CSV 복사').click()
    await user.should_see('CSV 복사 완료', retries=30)
    assert copied == ['| dup | dup |\n| --- | --- |\n| 한글 | 20 |', 'dup,dup\r\n한글,20\r\n']
