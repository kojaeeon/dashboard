"""Source positions for Markdown heading navigation."""
import re


def headings(content):
    lines = content.lstrip('\ufeff').splitlines()
    result = []
    fence = None
    frontmatter_end = -1
    if lines and lines[0].strip() == '---':
        frontmatter_end = next((i for i in range(1, len(lines))
                                if lines[i].strip() in {'---', '...'}), -1)
    for i, line in enumerate(lines):
        if i <= frontmatter_end:
            continue
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if re.match(r'^ {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*$', line):
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        match = re.match(r'^ {0,3}(#{1,6})(?:\s+|$)(.*)$', line)
        if match:
            title = re.sub(r'\s+#+\s*$', '', match[2]).strip()
            result.append((len(match[1]), title or '(빈 제목)', i + 1))
        elif line.strip() and i + 1 < len(lines) and re.match(r'^ {0,3}(=+|-+)\s*$', lines[i + 1]):
            result.append((1 if lines[i + 1].lstrip().startswith('=') else 2, line.strip(), i + 1))
    return result
