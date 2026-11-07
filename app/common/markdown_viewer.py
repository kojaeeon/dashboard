import re
from nicegui import ui


class MermaidRenderer:
    """Single entry point for NiceGUI's locally bundled Mermaid JS."""
    THEMES = ('default', 'dark', 'forest', 'neutral', 'base')

    @classmethod
    def render(cls, source: str, theme='default'):
        if theme not in cls.THEMES:
            raise ValueError('Unsupported Mermaid theme')
        return ui.mermaid(source, config={
            'theme': theme, 'securityLevel': 'strict', 'startOnLoad': False,
            'secure': ['secure', 'securityLevel', 'startOnLoad', 'maxTextSize', 'theme'],
        }).classes('w-full overflow-auto').style('min-height: 120px')


class MarkdownViewer:
    """Keep ordinary code fences intact and route Mermaid fences to one wrapper."""
    @staticmethod
    def blocks(content):
        markdown = []
        lines = content.splitlines(keepends=True)
        i = 0
        while i < len(lines):
            match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)\r?\n?$', lines[i])
            if not match:
                markdown.append(lines[i]); i += 1; continue
            fence, info = match.groups()
            end = i + 1
            closing = re.compile(r'^ {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*$')
            while end < len(lines) and not closing.match(lines[end]):
                end += 1
            if info.strip().lower() == 'mermaid' and end < len(lines):
                if markdown:
                    yield 'markdown', ''.join(markdown)
                    markdown = []
                yield 'mermaid', ''.join(lines[i + 1:end])
            else:
                markdown.extend(lines[i:min(end + 1, len(lines))])
            i = end + 1
        if markdown:
            yield 'markdown', ''.join(markdown)

    @classmethod
    def render(cls, content, theme='default'):
        with ui.column().classes('w-full gap-4') as container:
            for kind, source in cls.blocks(content):
                if kind == 'mermaid':
                    MermaidRenderer.render(source, theme)
                else:
                    ui.markdown(source, extras=['fenced-code-blocks', 'tables', 'strike']).classes('w-full')
        return container
