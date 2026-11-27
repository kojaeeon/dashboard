"""Read titled SQL snippets from saved Markdown documents."""
import re

from app.common.document_index import headings
from app.common.markdown_file import normalize_newlines

SQL_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})[ \t]*sql[ \t]*$', re.IGNORECASE)


def titled_queries(content: str) -> list[tuple[str, str]]:
    content = normalize_newlines(content.lstrip('\ufeff'))
    lines = content.splitlines(keepends=True)
    queries = []
    for level, title, heading_line in headings(content):
        if level != 3:
            continue
        start = heading_line  # Heading positions are one-based.
        while start < len(lines) and not lines[start].strip():
            start += 1
        if start == len(lines) or not (match := SQL_FENCE.fullmatch(lines[start].removesuffix('\n'))):
            continue
        fence = match[1]
        closing = re.compile(rf'^ {{0,3}}{fence[0]}{{{len(fence)},}}[ \t]*$')
        end = start + 1
        while end < len(lines) and not closing.match(lines[end]):
            end += 1
        if end == len(lines):
            continue
        # Match Markdown's removal of the opening fence's indentation.
        indent = match.start(1)
        sql = ''.join(line[min(indent, len(line) - len(line.lstrip(' '))):]
                      for line in lines[start + 1:end]).removesuffix('\n')
        if sql.strip():
            queries.append((title, sql))
    return queries
