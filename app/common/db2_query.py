"""Run a single Db2 query through a locally configured DB-API connection."""
import csv
import io
import re
from contextlib import closing
from dataclasses import dataclass
from decimal import Decimal
from importlib import import_module

MAX_ROWS = 9_999
FACTORY_ENV = 'DASHBOARD_DB2_CONNECT'
SQL_TOKEN = re.compile(r"""--[^\r\n]*|/\*|'(?:''|[^'])*'|"(?:""|[^"])*"|[\w$#@]+|\S""")
COMMENT_BOUNDARY = re.compile(r'/\*|\*/')
MD_SPECIAL = re.compile(r'[&<>\\|`*_~\[\]]')
READ_STATEMENTS = {'SELECT', 'WITH', 'VALUES'}
CTE_STATEMENTS = {'SELECT', 'VALUES', 'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'CALL'}
CSV_FORMULA = re.compile(r'^(?:\s*[=+@-]|[\t\r\n])')


class QueryError(ValueError):
    pass


def query_statement(sql: str) -> str:
    tokens = []
    offset = 0
    terminator = None
    while match := SQL_TOKEN.search(sql, offset):
        token = match.group()
        offset = match.end()
        if token.startswith('--'):
            continue
        if token == '/*':
            depth = 1
            while depth:
                boundary = COMMENT_BOUNDARY.search(sql, offset)
                if boundary is None:
                    raise QueryError('닫히지 않은 SQL 주석이 있습니다.')
                offset = boundary.end()
                depth += 1 if boundary.group() == '/*' else -1
            continue
        if terminator is not None:
            raise QueryError('한 번에 쿼리 한 문장만 실행할 수 있습니다.')
        if token == ';':
            terminator = match.start()
        elif token in {"'", '"'}:
            raise QueryError('닫히지 않은 SQL 문자열 또는 식별자가 있습니다.')
        else:
            tokens.append(token.upper())

    if not tokens or tokens[0] not in READ_STATEMENTS:
        raise QueryError('SELECT, WITH, VALUES 조회문을 입력하세요.')
    if tokens[0] == 'WITH':
        depth = 0
        for token in tokens[1:]:
            if token == '(':
                depth += 1
            elif token == ')':
                depth -= 1
            elif depth == 0 and token in CTE_STATEMENTS:
                if token not in READ_STATEMENTS:
                    raise QueryError('WITH 절 뒤에는 조회문이 필요합니다.')
                break
        else:
            raise QueryError('WITH 절 뒤에는 조회문이 필요합니다.')

    for word, next_word, following in zip(tokens, tokens[1:], tokens[2:]):
        if word in {'FINAL', 'NEW', 'OLD'} and next_word == 'TABLE' and following == '(':
            raise QueryError('데이터 변경 결과를 반환하는 쿼리는 실행할 수 없습니다.')
    return sql[:terminator].strip()


def _connect(factory_path: str):
    module, separator, name = factory_path.partition(':')
    if not separator or not module or not name:
        raise QueryError(f'{FACTORY_ENV}을 module:함수 형식으로 설정하세요.')
    try:
        connect = getattr(import_module(module), name)
    except (ImportError, AttributeError) as exc:
        raise QueryError(f'{FACTORY_ENV}에 지정한 연결 함수를 가져올 수 없습니다.') from exc
    if not callable(connect):
        raise QueryError(f'{FACTORY_ENV}에 호출 가능한 연결 함수를 지정하세요.')
    try:
        return connect()
    except Exception as exc:
        raise QueryError('DB2 연결에 실패했습니다. 로컬 연결 설정을 확인하세요.') from exc


def _cell(value):
    if value is None or isinstance(value, (str, int, float, Decimal)):
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        return '0x' + bytes(value).hex()
    return str(value)


def _markdown_cell(value) -> str:
    text = '' if value is None else str(value)
    text = MD_SPECIAL.sub(lambda match: f'&#{ord(match.group())};', text)
    return text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')


def _csv_cell(value):
    if isinstance(value, str) and CSV_FORMULA.match(value):
        return "'" + value
    return value


@dataclass
class QueryResult:
    columns: tuple[str, ...]
    rows: list[tuple]
    truncated: bool

    def markdown(self) -> str:
        header = '| ' + ' | '.join(map(_markdown_cell, self.columns)) + ' |'
        separator = '| ' + ' | '.join('---' for _ in self.columns) + ' |'
        rows = ('| ' + ' | '.join(map(_markdown_cell, row)) + ' |' for row in self.rows)
        return '\n'.join((header, separator, *rows))

    def csv(self) -> str:
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(map(_csv_cell, self.columns))
        writer.writerows(map(_csv_cell, row) for row in self.rows)
        return output.getvalue()


def execute_query(sql: str, factory_path: str) -> QueryResult:
    statement = query_statement(sql)
    with closing(_connect(factory_path)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(statement)
        if not cursor.description:
            raise QueryError('조회 결과 컬럼을 가져올 수 없습니다.')
        columns = tuple(str(column[0]) for column in cursor.description)
        rows = []
        # The Db2 driver can close the result set when fetchone first reaches EOF.
        for _ in range(MAX_ROWS):
            row = cursor.fetchone()
            if row is None:
                return QueryResult(columns, rows, False)
            rows.append(tuple(map(_cell, row)))
        return QueryResult(columns, rows, cursor.fetchone() is not None)
