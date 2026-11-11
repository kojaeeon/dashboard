"""Mind-map workspace with SQLite persistence and local editor assets."""
from pathlib import Path
from nicegui import ui
from app.common.mindmap import MindMapEditor
from app.mindmap.model import example_graph, new_graph
from app.mindmap.store import MindMapStore
from app.mindmap.formats import import_graph, export_graph


def render(db):
    store = MindMapStore(db)
    state = {'id': None, 'revision': None, 'title': '고객 관리 서비스'}
    ui.add_css((Path(__file__).parents[1] / 'common/mindmap.css').read_text(encoding='utf-8-sig'))
    with ui.column().classes('w-full gap-3'):
        with ui.row().classes('w-full items-center gap-3'):
            ui.icon('account_tree').classes('text-2xl')
            title = ui.input('맵 제목', value='고객 관리 서비스').props('outlined dense').classes('w-72')
            ui.button('저장', icon='save', on_click=lambda: save())
            ui.button('가져오기', icon='upload', on_click=lambda: import_dialog()).props('outline')
            ui.button('내보내기', icon='download', on_click=lambda: export_dialog()).props('outline')
            status = ui.label('새 맵 · SQLite에 저장하세요').classes('text-xs opacity-60')
        with ui.row().classes('w-full flex-nowrap items-start gap-3'):
            with ui.column().classes('w-52 shrink-0 gap-2'):
                ui.label('MIND MAP LIBRARY').classes('text-xs tracking-widest opacity-60')
                ui.button('새 마인드맵', icon='add', on_click=lambda: replace(new_graph(), '새 마인드맵')).props('outline').classes('w-full')
                ui.button('서비스 예시', icon='schema', on_click=lambda: replace(example_graph(), '고객 관리 서비스')).props('flat').classes('w-full')
                library = ui.column().classes('w-full gap-1')
            editor = MindMapEditor(example_graph(), store.types()).classes('flex-1 min-w-0')
    editor.on('save_request', lambda: save())
    editor.on('type_save', lambda e: save_type(e.args))
    editor.on('load_error', lambda e: ui.notify(f'마인드맵 로딩 실패: {e.args}', type='negative'))

    async def confirm(message):
        with ui.dialog() as dialog, ui.card():
            ui.label(message)
            with ui.row():
                ui.button('취소', on_click=lambda: dialog.submit(False)).props('flat')
                ui.button('계속', on_click=lambda: dialog.submit(True))
        return await dialog

    async def discard():
        snapshot = await editor.run_method('getSnapshot')
        return (not snapshot['dirty'] and title.value == state['title']) or await confirm('저장하지 않은 변경을 버리고 다른 맵을 여시겠습니까?')

    async def replace(graph, name, item=None):
        if not await discard():
            return
        state.update(id=item['id'] if item else None, revision=item['revision'] if item else None)
        state['title'] = name
        title.value = name
        editor.load(graph)
        status.text = f'저장된 맵 #{item["id"]}' if item else '새 맵 · SQLite에 저장하세요'

    async def open_map(item_id):
        try:
            item = store.get(item_id)
            await replace(item['graph'], item['title'], item)
        except ValueError as exc:
            ui.notify(str(exc), type='negative')

    def refresh_library():
        library.clear()
        with library:
            for item in store.list():
                with ui.row().classes('w-full items-center flex-nowrap gap-0'):
                    ui.button(item['title'], on_click=lambda _, key=item['id']: open_map(key)).props('flat no-caps align=left').classes('flex-1 min-w-0')
                    ui.button(icon='delete_outline', on_click=lambda _, key=item['id']: delete_map(key)).props('flat round dense').tooltip('저장된 맵 삭제')
            if not store.list():
                ui.label('저장한 맵이 없습니다.').classes('text-xs opacity-50 p-2')

    async def save():
        try:
            snapshot = await editor.run_method('getSnapshot')
            state['id'], state['revision'] = store.save(title.value, snapshot['graph'], state['id'], state['revision'])
            state['title'] = title.value
            await editor.run_method('markSaved')
            status.text = f'SQLite 저장 완료 · #{state["id"]} · v{state["revision"]}'
            refresh_library()
            ui.notify('마인드맵을 저장했습니다.', type='positive')
        except (ValueError, TimeoutError) as exc:
            ui.notify(str(exc), type='negative')

    async def delete_map(key):
        item = store.get(key)
        if not await confirm(f'“{item["title"]}” 맵을 삭제하시겠습니까?'):
            return
        try:
            store.delete(key, item['revision'])
            if state['id'] == key:
                state.update(id=None, revision=None)
                status.text = '저장본 삭제됨 · 현재 편집 내용은 새 맵으로 저장 가능'
            refresh_library()
        except ValueError as exc:
            ui.notify(str(exc), type='negative')

    async def save_type(value):
        try:
            store.save_type(value)
            await editor.run_method('updateTypes', store.types())
            ui.notify('유형 기본 스타일을 저장했습니다.', type='positive')
        except ValueError as exc:
            ui.notify(str(exc), type='negative')

    def import_dialog():
        with ui.dialog() as dialog, ui.card().classes('w-[850px] max-w-full'):
            ui.label('맵 가져오기').classes('text-lg')
            kind = ui.select({'dot': 'DOT', 'mermaid': 'Mermaid mindmap / flowchart', 'json': 'KJA JSON'}, value='dot', label='입력 형식')
            source = ui.textarea('소스 코드').props('outlined').classes('w-full').style('min-height:280px')
            async def upload(e):
                content = await e.file.read()
                if len(content) > 2 * 1024 * 1024:
                    ui.notify('2MB 이하 파일만 지원합니다.', type='negative')
                    return
                try:
                    source.value = content.decode('utf-8-sig')
                    extension = Path(e.file.name).suffix.lower()
                    kind.value = 'dot' if extension in {'.dot', '.gv'} else 'json' if extension == '.json' else 'mermaid'
                except UnicodeError:
                    ui.notify('UTF-8 파일로 준비하세요.', type='negative')
            ui.upload(on_upload=upload, auto_upload=True, max_file_size=2*1024*1024).props('accept=.dot,.gv,.mmd,.md,.txt,.json').classes('w-full')
            async def apply():
                try:
                    graph, warnings = import_graph(source.value or '', kind.value)
                    if not await discard():
                        return
                    state.update(id=None, revision=None)
                    state['title'] = '가져온 마인드맵'
                    title.value = '가져온 마인드맵'
                    editor.load(graph)
                    status.text = '가져오기 완료 · 저장하면 새 맵으로 등록'
                    dialog.close()
                    for message in warnings:
                        ui.notify(message, timeout=8000)
                except ValueError as exc:
                    ui.notify(str(exc), type='negative')
            ui.label('순환·다중 부모는 계층과 추가 관계로 변환합니다. 스크립트·클릭 동작은 실행하지 않습니다.').classes('text-xs opacity-60')
            with ui.row():
                ui.button('취소', on_click=dialog.close).props('flat')
                ui.button('가져오기 적용', on_click=apply)
        dialog.open()

    async def export_dialog():
        snapshot = await editor.run_method('getSnapshot')
        with ui.dialog() as dialog, ui.card().classes('w-[850px] max-w-full'):
            ui.label('마인드맵 내보내기').classes('text-lg')
            kind = ui.select({'dot': 'DOT', 'flowchart': 'Mermaid flowchart', 'mindmap': 'Mermaid mindmap', 'json': 'KJA JSON'}, value='dot', label='출력 형식')
            source = ui.textarea('출력 코드', value=export_graph(snapshot['graph'], 'dot')).props('readonly outlined').classes('w-full').style('min-height:330px')
            kind.on_value_change(lambda e: source.set_value(export_graph(snapshot['graph'], e.value)))
            ui.label('KJA 메타데이터 주석으로 유형·스타일·관계를 보존합니다. Mermaid mindmap의 추가 관계는 다른 뷰어에 표시되지 않습니다.').classes('text-xs opacity-60')
            with ui.row():
                ui.button('코드 복사', icon='content_copy', on_click=lambda: ui.clipboard.write(source.value))
                ui.button('다운로드', icon='download', on_click=lambda: ui.download.content(source.value, f'mindmap.{"dot" if kind.value == "dot" else "json" if kind.value == "json" else "mmd"}'))
                ui.button('닫기', on_click=dialog.close).props('flat')
        dialog.open()

    refresh_library()
    return editor
