import csv
import io
import sqlite3
import sys
from types import ModuleType

import pytest

from app.common.db2_query import MAX_ROWS, QueryError, QueryResult, execute_query, query_html_filename, query_statement
from app.common.query_markdown import titled_queries

FACTORY = 'test_local_db2:connect'
SERIES = """
WITH numbers(n) AS (
    VALUES (1) UNION ALL SELECT n + 1 FROM numbers WHERE n < {}
)
SELECT n FROM numbers ORDER BY n
"""


@pytest.fixture
def local_db2(monkeypatch):
    class ExhaustionClosingCursor(sqlite3.Cursor):
        exhausted = False

        def fetchone(self):
            if self.exhausted:
                raise sqlite3.ProgrammingError('Result set is closed. ERRORCODE=-4470')
            row = super().fetchone()
            self.exhausted = row is None
            return row

        def fetchmany(self, size):
            # Mirror adapters that implement fetchmany by repeatedly calling next().
            rows = []
            for _ in range(size):
                row = self.fetchone()
                if row is None:
                    break
                rows.append(row)
            return rows

    class TrackedConnection(sqlite3.Connection):
        closed = False

        def cursor(self):
            return super().cursor(factory=ExhaustionClosingCursor)

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


@pytest.mark.parametrize('row_count', [0, 1, 512, 513, MAX_ROWS, MAX_ROWS + 2])
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


def test_markdown_queries_use_the_heading_immediately_above_each_sql_fence():
    markdown = '''---
title: 쿼리 모음
### Frontmatter heading
---
### 점검 목록 ###

  ````SQL
  SELECT '```' AS value
    FROM checks
  ````
```sql
SELECT 'no heading'
```
### 설명이 끼어 있는 블록
아래는 예시입니다.
```sql
SELECT 'not adjacent'
```
````markdown
### 문서 예제 내부
```sql
SELECT 'example'
```
````
### 점검 목록
~~~sql
VALUES (2)
~~~
### 닫히지 않은 블록
```sql
VALUES (3)
'''
    assert titled_queries('\ufeff' + markdown.replace('\n', '\r\n')) == [
        ('점검 목록', "SELECT '```' AS value\n  FROM checks"),
        ('점검 목록', 'VALUES (2)'),
    ]


def test_html_export_escapes_content_and_preserves_column_positions():
    result = QueryResult(('A&B', 'A&B'), [('<script>\n한국어', None)], True)
    html = result.html('결과 <2026>')
    assert html.startswith('<!doctype html>')
    assert '<title>결과 &lt;2026&gt;</title>' in html
    assert '<meta charset="utf-8">' in html
    assert html.count('<th scope="col">A&amp;B</th>') == 2
    assert '<tr><td>&lt;script&gt;\n한국어</td><td></td></tr>' in html
    assert '1건 · 조회 한도 초과' in html
    assert '조회 결과가 없습니다.' in QueryResult(('A',), [], False).html('결과')
    assert query_html_filename('완료/미완료: 조회') == '완료_미완료_조회.html'
    assert query_html_filename('CON.txt') == '_CON.txt.html'
