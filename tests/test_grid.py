import json

import httpx
import pytest
from nicegui import ui

from app.common.ado_client import AdoClient, AdoConfig
from app.common.database import Database
from app.common.grid import CommonGrid, GridColumn
from app.common.wiql import wiql_columns, wiql_rows


def test_wiql_metadata_and_values():
    columns = wiql_columns({'columns': [
        {'referenceName': 'Custom.BankCode', 'name': '은행 코드'},
        {'referenceName': 'System.Id', 'name': 'ID'},
        {'referenceName': 'System.AssignedTo', 'name': '담당자'},
        {'referenceName': 'System.Description', 'name': '설명'},
    ]})
    assert [c.key for c in columns] == ['Custom.BankCode', 'System.Id', 'System.AssignedTo', 'System.Description']
    assert columns[1].definition()['filter'] == 'agNumberColumnFilter'
    assert columns[2].value({'displayName': '재언', 'uniqueName': 'user@example.com'}) == '재언'
    assert columns[3].value('<p>A &amp; B</p><div>다음</div>') == 'A & B 다음'
    assert GridColumn('x', 'X').value(None) is None
    assert wiql_rows([{'id': 42, 'fields': {'Custom.BankCode': '001'}}]) == [
        {'System.Id': 42, 'Custom.BankCode': '001'}]


@pytest.mark.asyncio
async def test_batch_uses_selected_fields_and_snapshot():
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={'value': []})

    async with AdoClient(AdoConfig('https://ado.example', 'Project', 'secret'),
                         transport=httpx.MockTransport(handle)) as client:
        await client.get_work_items(list(range(201)), fields=['Custom.BankCode'], as_of='2026-11-08T00:00:00Z')
        await client.get_work_items([], fields=['Custom.BankCode'])
    assert [len(b['ids']) for b in bodies] == [200, 1]
    assert all(b['fields'] == ['Custom.BankCode'] for b in bodies)
    assert all(b['asOf'] == '2026-11-08T00:00:00Z' for b in bodies)


@pytest.mark.asyncio
async def test_wiql_page_dynamic_columns_empty_and_error(user, tmp_path, monkeypatch):
    from app.pages import work
    requests = []
    mode = {'value': 'rows'}

    class FakeAdo:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def query_wiql(self, query):
            if mode['value'] == 'error':
                raise RuntimeError('ADO 요청 실패 (HTTP 401)')
            if mode['value'] == 'tree':
                return {'queryType': 'tree'}
            return {'queryType': 'flat', 'columns': [
                {'referenceName': 'Custom.Code', 'name': '코드'},
                {'referenceName': 'System.AssignedTo', 'name': '담당자'},
            ], 'workItems': [{'id': i} for i in range(205)] if mode['value'] == 'rows' else [],
                'asOf': '2026-11-08T00:00:00Z'}

        async def get_work_items(self, ids, **kwargs):
            requests.append((ids, kwargs))
            return [{'id': i, 'fields': {'Custom.Code': f'C{i}',
                    'System.AssignedTo': {'displayName': '재언'}}} for i in reversed(ids)]

    monkeypatch.setattr(work, 'AdoClient', FakeAdo)

    @ui.page('/wiql-test')
    def page():
        work.render(Database(str(tmp_path / 'db.sqlite')))

    await user.open('/wiql-test')
    user.find('ADO · WIQL 조회').click()
    user.find('WIQL 실행').click()
    await user.should_see('205건 중 200건 표시 (최대 200건)')
    grid = next(iter(user.find(kind=ui.aggrid).elements))
    assert [c['field'] for c in grid.options['columnDefs']] == ['Custom.Code', 'System.AssignedTo']
    assert grid.options['suppressFieldDotNotation'] is True
    assert grid.options['rowData'][0]['System.AssignedTo'] == '재언'
    assert grid.options['rowData'][0]['System.Id'] == 0
    user.find(kind=ui.aggrid).trigger('rowDoubleClicked', {'data': grid.options['rowData'][0]})
    await user.should_see('작업 항목 #0')
    await user.should_see('C0')
    user.find('닫기').click()
    assert len(requests[0][0]) == 200
    assert requests[0][1]['fields'] == ['Custom.Code', 'System.AssignedTo']
    for value, message in [('tree', '현재 화면은 Flat WIQL 쿼리를 지원합니다.'),
                           ('error', 'ADO 요청 실패 (HTTP 401)'),
                           ('empty', '0건 중 0건 표시 (최대 200건)')]:
        mode['value'] = value
        user.find('WIQL 실행').click()
        await user.should_see(message)
    assert grid.options['rowData'] == []
    assert next(iter(user.find('WIQL 실행').elements)).enabled


@pytest.mark.asyncio
async def test_shared_grid_replaces_schema_and_clears(user):
    grids = []

    @ui.page('/grid-test')
    def page():
        grids.append(CommonGrid('test', [GridColumn('a', 'A')]))

    await user.open('/grid-test')
    grid = grids[0]
    grid.set_rows([{'a': 1}])
    grid.set_columns([GridColumn('b', 'B')])
    assert grid.rows == []
    grid.set_rows([{'b': False}])
    assert grid.element.options['rowData'] == [{'b': False}]
    grid.clear()
    assert grid.element.options['rowData'] == []
