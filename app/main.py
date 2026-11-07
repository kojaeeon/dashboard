import os
from pathlib import Path
from dotenv import load_dotenv
from nicegui import ui
from app.common.database import Database
from app.common.markdown_viewer import MarkdownViewer, MermaidRenderer
from app.common.ado_client import AdoClient

load_dotenv()
db = Database(os.getenv('DASHBOARD_DB_PATH', 'data/dashboard.db'))
SAMPLE = '''# Dashboard\n\n문서를 작성하고 Mermaid 다이어그램을 함께 관리하세요.\n\n```mermaid\nflowchart TD\n    A[Markdown] --> B[공통 렌더러]\n    B --> C[Mermaid JS]\n    B --> D[문서 미리보기]\n```\n'''


@ui.page('/')
def index():
    ui.colors(primary='#2563eb')
    ui.add_css('''
        .nicegui-content { padding: 24px; max-width: 1600px; margin: auto; }
        .nicegui-markdown pre { overflow-x: auto; }
        .mermaid svg { max-width: 100%; height: auto; }
    ''')
    state = {'document_id': None, 'theme': db.setting('mermaid_theme', 'default')}
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
        db.set_setting('app_theme', e.value)

    with ui.header().classes('items-center justify-between px-6'):
        ui.label('Dashboard').classes('text-xl font-bold')
        with ui.row().classes('items-center'):
            ui.select({'light': '라이트', 'dark': '다크'}, value=db.setting('app_theme', 'light'),
                      label='화면 테마', on_change=change_app_theme).props('dense outlined dark')
            ui.select(list(MermaidRenderer.THEMES), value=state['theme'], label='Mermaid 테마',
                      on_change=change_theme).props('dense outlined dark')

    with ui.tabs().classes('w-full') as tabs:
        md_tab = ui.tab('MD 보기', icon='description')
        work_tab = ui.tab('UI Work', icon='task_alt')

    with ui.tab_panels(tabs, value=md_tab).classes('w-full bg-transparent'):
        with ui.tab_panel(md_tab).classes('p-0'):
            ui.label('Markdown Workspace').classes('text-2xl font-semibold')
            ui.label('문서와 다이어그램을 한 곳에서 관리하세요.').classes('text-gray-500')
            with ui.row().classes('w-full items-start gap-6 flex-wrap lg:flex-nowrap'):
                with ui.card().classes('w-full lg:w-64 shrink-0'):
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
                    ui.button('새 문서', icon='add', on_click=new_document).classes('w-full')
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
                        ui.button('MD 다운로드', icon='download', on_click=lambda: ui.download(
                            (editor.value or '').encode('utf-8'), filename='document.md'))
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
                    with ui.row().classes('w-full gap-4 items-start flex-wrap xl:flex-nowrap'):
                        with ui.card().classes('w-full xl:w-1/2 min-w-0'):
                            ui.label('편집').classes('font-semibold')
                            editor = ui.textarea(value=SAMPLE).props('outlined input-style="min-height: 480px; font-family: monospace"').classes('w-full')
                            ui.button('미리보기 갱신', icon='refresh', on_click=preview.refresh)
                        with ui.card().classes('w-full xl:w-1/2 min-w-0 overflow-auto'):
                            ui.label('미리보기').classes('font-semibold')
                            preview()
                    def open_document(doc):
                        state['document_id'] = doc['id']
                        title.set_value(doc['title'])
                        editor.set_value(doc['content'])
                        preview.refresh()

        with ui.tab_panel(work_tab).classes('p-0'):
            ui.label('UI Work').classes('text-2xl font-semibold')
            ui.label('작업 상태와 메모를 SQLite에 저장합니다.').classes('text-gray-500')
            def work_dialog(item=None):
                with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
                    ui.label('작업 수정' if item else '새 작업').classes('text-lg font-bold')
                    work_title = ui.input('제목', value=item['title'] if item else '').classes('w-full')
                    status = ui.select({'todo': '할 일', 'doing': '진행 중', 'done': '완료'},
                                       value=item['status'] if item else 'todo', label='상태').classes('w-full')
                    notes = ui.textarea('메모', value=item['notes'] if item else '').classes('w-full')
                    def save():
                        try:
                            db.save_work(work_title.value, status.value, notes.value or '', item['id'] if item else None)
                            dialog.close()
                            work_list.refresh()
                        except ValueError as exc:
                            ui.notify(str(exc), type='warning')
                    with ui.row():
                        ui.button('취소', on_click=dialog.close).props('flat')
                        ui.button('저장', on_click=save).mark('work-save')
                dialog.open()
            ui.button('작업 추가', icon='add', on_click=lambda: work_dialog())
            @ui.refreshable
            def work_list():
                with ui.row().classes('w-full items-start gap-4 flex-wrap lg:flex-nowrap'):
                    for value, label in [('todo', '할 일'), ('doing', '진행 중'), ('done', '완료')]:
                        with ui.card().classes('w-full lg:w-1/3'):
                            ui.label(label).classes('text-lg font-semibold')
                            matches = [w for w in db.list('work_items') if w['status'] == value]
                            if not matches:
                                ui.label('등록된 작업이 없습니다.').classes('text-gray-500')
                            for item in matches:
                                ui.button(item['title'], on_click=lambda w=item: work_dialog(w)).props('flat no-caps').classes('w-full')
                                ui.label(item['notes']).classes('whitespace-pre-wrap text-sm')
                                async def delete_work(w=item):
                                    with ui.dialog() as dialog, ui.card():
                                        ui.label('이 작업을 삭제할까요?')
                                        ui.button('취소', on_click=lambda: dialog.submit(False))
                                        ui.button('삭제', color='negative', on_click=lambda: dialog.submit(True))
                                    if await dialog:
                                        db.delete('work_items', w['id'])
                                        work_list.refresh()
                                ui.button(icon='delete', on_click=delete_work).props('flat dense color=negative')
            work_list()
            with ui.expansion('ADO · WIQL 조회', icon='cloud').classes('w-full'):
                ui.label('환경변수의 ADO 설정으로 조회합니다. PAT는 화면과 DB에 저장하지 않습니다.')
                wiql = ui.textarea('WIQL', value="SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.TeamProject] = @project ORDER BY [System.ChangedDate] DESC").classes('w-full')
                result_area = ui.column().classes('w-full')
                async def query():
                    query_button.disable()
                    try:
                        async with AdoClient() as client:
                            result = await client.query_wiql(wiql.value)
                            if result.get('queryType') != 'flat':
                                raise ValueError('현재 화면은 Flat WIQL 쿼리를 지원합니다.')
                            ids = [w['id'] for w in result.get('workItems', [])][:200]
                            items = await client.get_work_items(ids)
                        result_area.clear()
                        with result_area:
                            ui.label(f'{len(items)}건 표시 (최대 200건)')
                            ui.table(columns=[{'name': k, 'label': k, 'field': k, 'sortable': True} for k in ('id', 'title', 'state')], rows=[{
                                'id': w['id'], 'title': w['fields'].get('System.Title', ''),
                                'state': w['fields'].get('System.State', '')} for w in items], pagination=10).classes('w-full')
                    except (ValueError, RuntimeError) as exc:
                        ui.notify(str(exc), type='negative')
                    finally:
                        query_button.enable()
                query_button = ui.button('WIQL 실행', icon='play_arrow', on_click=query)


def run():
    ui.run(title='Dashboard', host=os.getenv('DASHBOARD_HOST', '127.0.0.1'),
           port=int(os.getenv('DASHBOARD_PORT', '8080')), reload=False)


if __name__ == '__main__':
    run()
