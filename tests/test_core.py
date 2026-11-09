import asyncio
import base64
import httpx
import pytest
from app.common.database import Database
from app.common.markdown_viewer import MarkdownViewer
from app.common.ado_client import AdoClient, AdoConfig


def test_persistence_and_crud(tmp_path):
    path = str(tmp_path / 'test.db')
    db = Database(path)
    item = db.save_document('문서', '# hello')
    work = db.save_work('테스트', notes='memo')
    db.set_setting('mermaid_theme', 'dark')
    restored = Database(path)
    assert restored.list('documents')[0]['content'] == '# hello'
    assert restored.setting('mermaid_theme') == 'dark'
    restored.save_document('수정', '# changed', item)
    restored.save_work('테스트', 'done', item_id=work)
    assert restored.list('work_items')[0]['status'] == 'done'
    assert restored.list('documents')[0]['content'] == '# changed'
    restored.delete('documents', item)
    assert restored.list('documents') == []
    with pytest.raises(ValueError):
        restored.list('documents; DROP TABLE settings')


def test_markdown_fences():
    source = '# A\n```python\nx = 1\n```\n```mermaid\nA --> B\n```\ntext\n~~~mermaid\nB --> C\n~~~\n'
    blocks = list(MarkdownViewer.blocks(source))
    assert [kind for kind, _ in blocks] == ['markdown', 'mermaid', 'markdown', 'mermaid']
    assert '```python' in blocks[0][1]
    assert list(MarkdownViewer.blocks('````text\n```mermaid\nA --> B\n```\n````'))[0][0] == 'markdown'
    assert list(MarkdownViewer.blocks('```mermaid\nunclosed'))[0][0] == 'markdown'


def test_ado_env(monkeypatch):
    for key in ('ADO_BASE_URL', 'ADO_PROJECT', 'ADO_PAT'):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError):
        AdoConfig.from_env()
    monkeypatch.setenv('ADO_BASE_URL', 'https://ado.example/tfs/Collection')
    monkeypatch.setenv('ADO_PROJECT', 'My Project')
    monkeypatch.setenv('ADO_PAT', 'secret')
    config = AdoConfig.from_env()
    assert config.project == 'My Project'
    assert 'secret' not in repr(config)


def test_ado_wiql_workitems_and_error():
    seen = []
    def handle(request):
        seen.append(request)
        if request.url.path.endswith('/wiql'):
            return httpx.Response(200, json={'queryType': 'flat', 'workItems': [{'id': 42}]})
        if request.url.path.endswith('/workitems'):
            return httpx.Response(200, json={'value': [{'id': 42, 'fields': {}}]})
        return httpx.Response(401, json={'message': 'private response'})
    async def run():
        config = AdoConfig('https://ado.example/tfs/Collection', 'My Project', 'secret')
        async with AdoClient(config, transport=httpx.MockTransport(handle)) as ado:
            result = await ado.query_wiql('SELECT [System.Id] FROM WorkItems')
            assert result['workItems'][0]['id'] == 42
            await ado.get_work_items(list(range(201)))
            assert len(seen) == 3
            with pytest.raises(RuntimeError, match='401'):
                await ado.list_repositories()
    asyncio.run(run())
    assert seen[0].url.path == '/tfs/Collection/My Project/_apis/wit/wiql'
    assert seen[0].url.params['api-version'] == '7.1'
    assert seen[0].headers['authorization'] == 'Basic ' + base64.b64encode(b':secret').decode()


def test_local_folder_library(tmp_path):
    from app.common.local_library import markdown_files
    root = tmp_path / 'docs'
    nested = root / 'nested'
    nested.mkdir(parents=True)
    (root / 'one.md').write_text('# One', encoding='utf-8')
    (nested / 'two.MD').write_text('# Two', encoding='utf-8')
    (root / 'ignore.txt').write_text('ignore', encoding='utf-8')
    database = Database(str(tmp_path / 'folders.db'))
    database.add_folder(str(root))
    database.add_folder(str(root / '.'))
    restored = Database(str(tmp_path / 'folders.db'))
    assert len(restored.folders()) == 1
    assert [p.name for p in markdown_files(restored.folders()[0]['path'])] == ['one.md']
    with pytest.raises(ValueError):
        restored.add_folder('')
    with pytest.raises(ValueError):
        restored.add_folder(str(root / 'one.md'))
    restored.remove_folder(restored.folders()[0]['id'])
    assert restored.folders() == []
    assert (root / 'one.md').exists()


def test_document_index_ignores_metadata_and_code():
    from app.common.document_index import headings
    source = '---\ntitle: example\n---\n# First\n```python\n## Not a heading\n```\n## Second\n### Third ###\n'
    assert headings(source) == [(1, 'First', 4), (2, 'Second', 8), (3, 'Third', 9)]
