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
    user.find('UI Work').click()
    user.find('작업 추가').click()
    user.find(kind=ui.input, content='제목').type('첫 작업')
    user.find(marker='work-save').click()
    assert main.db.list('work_items')[0]['title'] == '첫 작업'
