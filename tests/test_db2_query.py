import csv
import io
import sqlite3
import sys
from types import ModuleType

import pytest

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
