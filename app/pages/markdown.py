"""MD menu: local library, editor, preview, index and navigation."""
from pathlib import Path
from nicegui import ui
from app.common.database import Database
from app.common.markdown_viewer import MarkdownViewer, MermaidRenderer
from app.common.local_library import local_library
from app.common.document_index import headings

SAMPLE_PATH = Path(__file__).resolve().parents[2] / 'examples' / 'main-test.md'
SAMPLE = SAMPLE_PATH.read_text(encoding='utf-8')


def render(db: Database):
    state = {'mode': 'render', 'document_id': None, 'theme': db.setting('mermaid_theme', 'default')}
    if state['theme'] not in MermaidRenderer.THEMES:
        state['theme'] = 'default'
    dark = ui.dark_mode(db.setting('app_theme', 'light') == 'dark')

    @ui.refreshable
    def preview():
        MarkdownViewer.render(editor.value or '', state['theme'])

    def change_theme(e):
        state['theme'] = e.value
        db.set_setting('mermaid_theme', e.value)
        preview.refresh()

    def change_app_theme(e):
        dark.set_value(e.value == 'dark')
        editor.set_theme('vscodeDark' if e.value == 'dark' else 'vscodeLight')
        db.set_setting('app_theme', e.value)

    ui.label('YOUR PRIVATE STUDIO').classes('eyebrow')
    ui.label('Markdown Workspace').classes('page-title')
    ui.label('문서와 다이어그램을 한 곳에서 관리하세요.').classes('text-gray-500')
    with ui.row().classes('w-full items-start gap-6 flex-wrap lg:flex-nowrap'):
        with ui.card().classes('w-full lg:w-64 shrink-0') as library_panel:
            ui.label('문서').classes('text-lg font-semibold')
            @ui.refreshable
            def document_list():
                for doc in db.list('documents'):
                    ui.button(doc['title'], on_click=lambda d=doc: open_document(d)).props('flat no-caps').classes('w-full justify-start')
            document_list()
            def new_document():
                state['document_id'] = None
                title.set_value('새 문서')
                editor.set_value('')
                preview.refresh()
            def open_local_file(path):
                try:
                    if path.stat().st_size > 2 * 1024 * 1024:
                        raise ValueError('2MB 이하 파일만 지원합니다.')
                    content = path.read_text(encoding='utf-8-sig')
                except (OSError, UnicodeError, ValueError) as exc:
                    ui.notify(f'파일을 읽을 수 없습니다: {exc}', type='warning')
                    return
                state['document_id'] = None
                title.set_value(path.stem)
                editor.set_value(content)
                preview.refresh()

            local_library(db, open_local_file)
            async def upload(e):
                if e.file.size() > 2 * 1024 * 1024:
                    ui.notify('2MB 이하 파일을 선택하세요.', type='warning'); return
                try:
                    content = (await e.file.read()).decode('utf-8-sig')
                except UnicodeDecodeError:
                    ui.notify('UTF-8 형식의 MD 파일이 필요합니다.', type='warning'); return
                state['document_id'] = None
                title.set_value(Path(e.file.name).stem)
                editor.set_value(content)
                preview.refresh()
            ui.upload(label='MD 불러오기', on_upload=upload, auto_upload=True,
                      max_file_size=2 * 1024 * 1024).props('accept=.md,.markdown,text/markdown').classes('w-full')
        with ui.column().classes('w-full min-w-0 gap-4'):
            with ui.row().classes('w-full items-center'):
                title = ui.input('문서 제목', value='시작하기').classes('grow')
                def save_document():
                    try:
                        state['document_id'] = db.save_document(title.value, editor.value or '', state['document_id'])
                        document_list.refresh()
                        ui.notify('문서를 저장했습니다.', type='positive')
                    except ValueError as exc:
                        ui.notify(str(exc), type='warning')
                ui.button('저장', icon='save', on_click=save_document)
                async def delete_document():
                    if state['document_id'] is None:
                        return
                    with ui.dialog() as dialog, ui.card():
                        ui.label('이 문서를 삭제할까요?')
                        with ui.row():
                            ui.button('취소', on_click=lambda: dialog.submit(False))
                            ui.button('삭제', color='negative', on_click=lambda: dialog.submit(True))
                    if await dialog:
                        db.delete('documents', state['document_id'])
                        new_document()
                        document_list.refresh()
                ui.button(icon='delete', on_click=delete_document).props('flat color=negative')
            def set_mode(mode):
                state['mode'] = mode
                text_panel.set_visibility(mode == 'text')
                render_panel.set_visibility(mode == 'render')
                text_button.props('unelevated' if mode == 'text' else 'flat')
                render_button.props('unelevated' if mode == 'render' else 'flat')
                if mode == 'render':
                    preview.refresh()
                else:
                    ui.run_javascript(f"setTimeout(() => document.querySelector('#c{editor.id} .cm-content')?.focus(), 100)")

            async def jump_heading(ordinal, line):
                index_dialog.close()
                if state['mode'] == 'text':
                    editor.reveal_line(line)
                    await ui.run_javascript(f"""
                        const view = getElement({editor.id}).editor;
                        const line = view.state.doc.line({line});
                        view.dispatch({{selection: {{anchor: line.from}}}});
                        view.focus();
                    """)
                else:
                    preview.refresh()
                    await ui.run_javascript(f"""
                        await new Promise(resolve => setTimeout(resolve, 200));
                        const root = document.getElementById('c{render_panel.id}');
                        const heading = root?.querySelectorAll('.nicegui-markdown h1, .nicegui-markdown h2, .nicegui-markdown h3, .nicegui-markdown h4, .nicegui-markdown h5, .nicegui-markdown h6')[{ordinal}];
                        if (heading) {{
                            heading.style.scrollMarginTop = '150px';
                            heading.setAttribute('tabindex', '-1');
                            heading.scrollIntoView({{behavior: 'instant', block: 'start'}});
                            heading.focus({{preventScroll: true}});
                        }}
                    """)

            def show_index():
                index_entries.clear()
                entries = headings(editor.value or '')
                with index_entries:
                    if not entries:
                        ui.label('문서에 제목이 없습니다.')
                    for ordinal, (level, label, line) in enumerate(entries):
                        ui.button(f'H{level} · {label}', color=None,
                                  on_click=lambda n=ordinal, l=line: jump_heading(n, l)).props(
                            'flat no-caps align=left').classes(f'w-full text-left toc-entry toc-level-{level}').style(
                                f'padding-left: {12 + (level - 1) * 16}px').tooltip(f'{line}행으로 이동')
                index_dialog.open()

            with ui.dialog() as index_dialog, ui.card().classes('w-full max-w-xl'):
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label('문서 목차 · Index').classes('text-lg font-semibold')
                    ui.button(icon='close', on_click=index_dialog.close).props('flat round aria-label="목차 닫기"')
                index_entries = ui.column().classes('w-full gap-1 overflow-auto').style('max-height: 65vh')

            def toggle_library():
                visible = not library_panel.visible
                library_panel.set_visibility(visible)
                library_toggle.props(
                    f'icon={"menu_open" if visible else "menu"} '
                    f'aria-expanded={str(visible).lower()} '
                    f'aria-label="왼쪽 목록 {"접기" if visible else "펼치기"}"')
                library_toggle.set_text('')

            with ui.row().classes('w-full items-center gap-2'):
                library_toggle = ui.button(icon='menu_open', on_click=toggle_library).props(
                    f'flat round aria-label="왼쪽 목록 접기" aria-expanded=true aria-controls="c{library_panel.id}"')
                text_button = ui.button(icon='code', on_click=lambda: set_mode('text')).props(
                    'flat round aria-label="텍스트 모드"').mark('text-mode')
                text_button.tooltip('텍스트 모드')
                render_button = ui.button(icon='visibility', on_click=lambda: set_mode('render')).props(
                    'unelevated round aria-label="렌더 모드"').mark('render-mode')
                render_button.tooltip('렌더 모드')
                ui.button(icon='format_list_bulleted', on_click=show_index).props(
                    'flat round aria-label="문서 목차 열기" aria-haspopup="dialog"').tooltip('Index · 제목으로 이동')

                ui.space()
                ui.button(icon='refresh', on_click=preview.refresh).props(
                    'flat round aria-label="미리보기 새로고침"').tooltip('미리보기 새로고침')
            with ui.card().classes('w-full min-w-0') as text_panel:
                ui.label('Ctrl+F 찾기 · F3 다음 · Shift+F3 이전 · Esc 닫기').classes('text-xs text-gray-500')
                editor = ui.codemirror(
                    value=SAMPLE, language='Markdown',
                    theme='vscodeDark' if db.setting('app_theme', 'light') == 'dark' else 'vscodeLight',
                    line_wrapping=True,
                ).classes('w-full').style('height: 65vh; min-height: 480px')
                search_script = (Path(__file__).resolve().parent.parent / 'common' / 'search_overview.js').read_text(encoding='utf-8')
                ui.timer(0.5, lambda: ui.run_javascript(
                    search_script.replace('EDITOR_ID', str(editor.id))), once=True)

            with ui.card().classes('w-full min-w-0 overflow-auto') as render_panel:
                preview()
            text_panel.set_visibility(False)

            async def jump_document(end=False):
                if state['mode'] == 'text':
                    await ui.run_javascript(f"""
                        const view = getElement({editor.id}).editor;
                        const position = {'view.state.doc.length' if end else '0'};
                        const CM = await import('nicegui-codemirror');
                        view.dispatch({{selection: {{anchor: position}},
                            effects: CM.EditorView.scrollIntoView(position, {{y: '{'end' if end else 'start'}'}})}});
                        view.focus();
                    """)
                else:
                    await ui.run_javascript(f"""
                        const root = document.getElementById('c{render_panel.id}');
                        if (!root) return;
                        const target = {'root.lastElementChild?.lastElementChild || root' if end else 'root'};
                        target.style.scrollMarginTop = '140px';
                        target.style.scrollMarginBottom = '24px';
                        target.setAttribute('tabindex', '-1');
                        target.scrollIntoView({{behavior: 'instant', block: '{'end' if end else 'start'}'}});
                        target.focus({{preventScroll: true}});
                    """)

            with ui.column().classes('document-jump-widget gap-1').props(
                    'role="navigation" aria-label="문서 처음과 끝으로 이동"'):
                ui.button(icon='vertical_align_top', on_click=lambda: jump_document()).props(
                    'flat round aria-label="문서 맨 위로 이동"').tooltip('문서 맨 위로')
                ui.separator()
                ui.button(icon='vertical_align_bottom', on_click=lambda: jump_document(True)).props(
                    'flat round aria-label="문서 맨 아래로 이동"').tooltip('문서 맨 아래로')

            def open_document(doc):
                state['document_id'] = doc['id']
                title.set_value(doc['title'])
                editor.set_value(doc['content'])
                preview.refresh()


    return {'app_theme': change_app_theme, 'mermaid_theme': change_theme}
