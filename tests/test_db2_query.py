import csv
import io
import json
import re
import sqlite3
import sys
from types import ModuleType

import pytest
from nicegui import ui

from app.common.db2_query import MAX_ROWS, QueryError, execute_query, query_statement

FACTORY = 'test_local_db2:connect'
SERIES = """
WITH numbers(n) AS (
    VALUES (1) UNION ALL SELECT n + 1 FROM numbers WHERE n < {}
)
SELECT n FROM numbers ORDER BY n
"""


@pytest.fixture
def local_db2(monkeypatch):
    class TrackedConnection(sqlite3.Connection):
        closed = False

        def close(self):
            self.closed = True
            super().close()

    connections = []
    module = ModuleType('test_local_db2')

    def connect():
        connection = sqlite3.connect(':memory:', factory=TrackedConnection)
        connections.append(connection)
        return connection

    module.connect = connect
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return connections


@pytest.mark.parametrize('row_count', [0, MAX_ROWS, MAX_ROWS + 2])
def test_result_cap_preserves_columns_and_closes_connection(local_db2, row_count):
    sql = SERIES.format(row_count) if row_count else 'SELECT 1 AS n WHERE 1 = 0'
    result = execute_query(sql, FACTORY)
    assert result.columns == ('n',)
    assert len(result.rows) == min(MAX_ROWS, row_count)
    assert result.truncated is (row_count > MAX_ROWS)
    assert local_db2[0].closed


def test_copy_formats_preserve_column_positions_and_escape_values(local_db2):
    result = execute_query("""SELECT 'a|"b",c' AS dup, '첫째' || char(10) || '둘째' AS dup,
                                     NULL AS empty, '=1+1' AS formula, -42 AS number""", FACTORY)
    assert list(csv.reader(io.StringIO(result.csv()))) == [
        ['dup', 'dup', 'empty', 'formula', 'number'],
        ['a|"b",c', '첫째\n둘째', '', "'=1+1", '-42'],
    ]
    assert result.markdown() == (
        '| dup | dup | empty | formula | number |\n'
        '| --- | --- | --- | --- | --- |\n'
        '| a&#124;"b",c | 첫째<br>둘째 |  | =1+1 | -42 |'
    )


@pytest.mark.parametrize('sql', [
    'UPDATE T SET N = 1',
    'SELECT 1; DELETE FROM T',
    'SELECT * FROM FINAL /* comment */ TABLE (INSERT INTO T VALUES (1))',
    'WITH Q AS (SELECT 1) DELETE FROM T',
])
def test_non_query_statements_are_rejected_before_connect(local_db2, sql):
    with pytest.raises(QueryError):
        execute_query(sql, FACTORY)
    assert not local_db2


def test_sql_strings_identifiers_and_comments_can_contain_semicolons():
    sql = """/* outer /* inner */ */ SELECT 'it''s;fine' AS "a;""b" """
    assert query_statement(sql + '; -- trailing comment') == sql.strip()


async def test_query_menu_displays_grid_and_sends_clipboard_text(user, local_db2, monkeypatch, tmp_path):
    from app import main
    from app.common.database import Database

    monkeypatch.setenv('DASHBOARD_DB2_CONNECT', FACTORY)
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
