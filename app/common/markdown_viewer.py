import re
from pathlib import Path
from nicegui import ui

FULLSCREEN_SCRIPT = (Path(__file__).parent / 'mermaid_fullscreen.js').read_text(encoding='utf-8')


class MermaidRenderer:
    """Single entry point for NiceGUI's locally bundled Mermaid JS."""
    THEMES = ('default', 'dark', 'forest', 'neutral', 'base')

    @classmethod
    def render(cls, source: str, theme='default'):
        if theme not in cls.THEMES:
            raise ValueError('Unsupported Mermaid theme')
        with ui.column().classes('w-full gap-1'):
            with ui.row().classes('w-full justify-end'):
                fullscreen_button = ui.button(icon='fullscreen').props(
                    'flat round dense aria-label="Mermaid 전체화면"').tooltip('전체화면으로 보기')
                with ui.button(icon='ios_share').props(
                        'flat round dense aria-label="Mermaid 출력"').tooltip('Mermaid 출력'):
                    with ui.menu():
                        ui.menu_item('SVG 다운로드', on_click=lambda: cls.export(diagram, 'svg'))
                        ui.menu_item('HTML 다운로드', on_click=lambda: cls.export(diagram, 'html'))
                        ui.menu_item('코드 복사', on_click=lambda: ui.clipboard.write(source))
            diagram = ui.mermaid(source, config={
                'theme': theme, 'securityLevel': 'strict', 'startOnLoad': False,
                'secure': ['secure', 'securityLevel', 'startOnLoad', 'maxTextSize', 'theme'],
            }).classes('w-full overflow-auto').style('min-height: 120px')
            fullscreen_button.on('click', js_handler=FULLSCREEN_SCRIPT.replace('DIAGRAM_ID', str(diagram.id)))
        return diagram

    @staticmethod
    async def export(diagram, format):
        result = await ui.run_javascript("""
            const root = document.getElementById('cELEMENT_ID');
            const original = root?.querySelector('svg');
            if (!original) return false;
            const clone = original.cloneNode(true);
            const originals = [original, ...original.querySelectorAll('*')];
            const copies = [clone, ...clone.querySelectorAll('*')];
            const properties = ['fill', 'stroke', 'stroke-width', 'stroke-dasharray',
                'font-family', 'font-size', 'font-weight', 'color', 'background-color',
                'text-anchor', 'dominant-baseline', 'opacity', 'display'];
            originals.forEach((node, i) => {
                const computed = getComputedStyle(node);
                properties.forEach(p => copies[i].style.setProperty(p, computed.getPropertyValue(p)));
            });
            clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            const bounds = original.getBoundingClientRect();
            clone.setAttribute('width', bounds.width);
            clone.setAttribute('height', bounds.height);
            const svg = new XMLSerializer().serializeToString(clone);
            const format = 'EXPORT_FORMAT';
            const content = format === 'svg' ? svg :
                '<!doctype html><html lang="ko"><head><meta charset="utf-8">' +
                '<meta name="viewport" content="width=device-width,initial-scale=1">' +
                '<title>Mermaid diagram</title><style>body{margin:24px}svg{max-width:100%;height:auto}</style>' +
                '</head><body>' + svg + '</body></html>';
            const url = URL.createObjectURL(new Blob([content], {
                type: format === 'svg' ? 'image/svg+xml;charset=utf-8' : 'text/html;charset=utf-8'
            }));
            const link = document.createElement('a');
            link.href = url;
            link.download = 'mermaid-' + 'ELEMENT_ID' + '.' + format;
            document.body.appendChild(link);
            link.click();
            link.remove();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
            return true;
        """.replace('ELEMENT_ID', str(diagram.id)).replace('EXPORT_FORMAT', format), timeout=10)
        if not result:
            ui.notify('다이어그램 렌더링 후 다시 출력해 주세요.', type='warning')



class MarkdownViewer:
    """Keep ordinary code fences intact and route Mermaid fences to one wrapper."""
    @staticmethod
    def blocks(content, split_code=False):
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
            elif split_code and end < len(lines):
                if markdown:
                    yield 'markdown', ''.join(markdown)
                    markdown = []
                yield 'code', (info.strip().split()[0] if info.strip() else '', ''.join(lines[i + 1:end]))
            else:
                markdown.extend(lines[i:min(end + 1, len(lines))])
            i = end + 1
        if markdown:
            yield 'markdown', ''.join(markdown)

    @classmethod
    def render(cls, content, theme='default'):
        with ui.column().classes('w-full gap-4') as container:
            content = content.lstrip('\ufeff')
            frontmatter = re.match(r'\A---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)', content, re.S)
            if frontmatter:
                with ui.expansion('Frontmatter', icon='data_object').classes('w-full'):
                    cls.code_block(frontmatter.group(1), 'yaml')
                content = content[frontmatter.end():]
            for kind, source in cls.blocks(content, split_code=True):
                if kind == 'mermaid':
                    MermaidRenderer.render(source, theme)
                elif kind == 'code':
                    language, code = source
                    cls.code_block(code, language)
                else:
                    ui.markdown(source, extras=['fenced-code-blocks', 'tables', 'strike']).classes('w-full')
        return container

    @staticmethod
    def code_block(source, language=''):
        with ui.column().classes('w-full gap-0'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label(language or 'text').classes('text-xs text-gray-500')
                ui.button(icon='content_copy', on_click=lambda: ui.clipboard.write(source)).props(
                    'flat round dense aria-label="코드 복사"').tooltip('코드 복사')
            code = ui.code(source, language=language or None).classes('w-full')
            code.copy_button.delete()
