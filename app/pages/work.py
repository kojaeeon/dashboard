"""Work menu: task board and Azure DevOps queries."""
from nicegui import ui
from app.common.database import Database
from app.common.ado_client import AdoClient


def render(db: Database):
    ui.label('MAKE ROOM FOR GREAT WORK').classes('eyebrow')
    ui.label('Work').classes('page-title')
    ui.label('아이디어에서 완성까지, 중요한 작업에 집중하세요.').classes('text-gray-500')
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
