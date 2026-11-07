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
    user.find('배포/백업').click()
    await user.should_see('프론트메터 설정')
    user.find('계획 만들기').click()
    await user.should_see('계획 확인 완료 · 위 실행 버튼으로 이 파일들을 처리합니다.')


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
