"""Db2 query editor, saved Markdown snippets and result exports."""
import json
import os
from sqlite3 import Error as SQLiteError

from nicegui import run, ui

from app.common.database import Database
from app.common.db2_query import FACTORY_ENV, MAX_ROWS, execute_query, query_html_filename
from app.common.query_markdown import titled_queries


def render(db: Database):
    factory_path = os.getenv(FACTORY_ENV, '').strip()
    result = None
    result_title = '쿼리조회 결과'
    selected_document_id = None
    snippets = []

    def set_document(document):
        nonlocal selected_document_id, snippets
        selected_document_id = document['id']
        document_label.set_text(document['title'])
        snippets = titled_queries(document['content'])
        query_select.set_options({index: title for index, (title, _) in enumerate(snippets)}, value=None)
        query_select.set_enabled(bool(snippets))
        if not snippets:
            ui.notify('이 문서에 ### 제목이 붙은 SQL 코드 블록이 없습니다.', type='info')

    def load_snippet(event):
        if event.value in query_select.options:
            _, statement = snippets[event.value]
            sql.set_value(statement)

    def preview_document(document_id):
        document = db.document(document_id) if document_id is not None else None
        document_preview.set_value(document['content'] if document else '')
        use_document_button.set_enabled(document is not None)

    def open_documents():
        options = {doc['id']: doc['title'] for doc in db.list('documents')}
        doc_id = selected_document_id if selected_document_id in options else next(iter(options), None)
        if document_picker.value == doc_id:
            preview_document(doc_id)
        document_picker.set_options(options, value=doc_id)
        document_picker.set_enabled(bool(options))
        empty_documents.set_visibility(not options)
        document_dialog.open()

    def choose_document():
        document = db.document(document_picker.value)
        if document is None:
            ui.notify('문서를 찾을 수 없습니다.', type='warning')
            open_documents()
            return
        set_document(document)
        document_dialog.close()

    def register_document():
        title = registration_title.value or ''
        content = registration_content.value or ''
        if not title.strip() or not content.strip():
            ui.notify('문서 제목과 Markdown 본문을 입력하세요.', type='warning')
            return
        try:
            document_id = db.save_document(title, content)
        except SQLiteError as exc:
            ui.notify(f'MD 저장 실패 · {exc}', type='negative')
            return
        set_document({'id': document_id, 'title': title.strip(), 'content': content})
        registration_dialog.close()
        registration_title.set_value('')
        registration_content.set_value('')
        ui.notify('MD를 저장했습니다.', type='positive')

    async def execute():
        nonlocal result, result_title
        if not execute_button.enabled:
            return
        statement = sql.value or ''
        selected_query = query_select.value
        result_title = snippets[selected_query][0] if selected_query is not None else '쿼리조회 결과'
        execute_button.disable()
        md_button.disable()
        csv_button.disable()
        html_button.disable()
        result = None
        grid.set_visibility(False)
        grid.options.update(columnDefs=[], rowData=[])
        grid.update()
        status.set_text('조회 중…')
        try:
            result = await run.io_bound(execute_query, statement, factory_path)
            if result is None:
                status.set_text('조회가 취소되었습니다.')
                return
            keys = [f'col_{index}' for index in range(len(result.columns))]
            grid.options.update(
                columnDefs=[{'field': key, 'headerName': title} for key, title in zip(keys, result.columns)],
                rowData=[dict(zip(keys, (None if value is None else str(value) for value in row)))
                         for row in result.rows],
            )
            grid.update()
            grid.set_visibility(True)
            status.set_text(f'{len(result.rows):,}건' + (' · 조회 한도 초과' if result.truncated else ''))
            md_button.enable()
            csv_button.enable()
            html_button.enable()
        except Exception as exc:
            status.set_text('조회 실패 · ' + str(exc)[:1500])
        finally:
            execute_button.enable()

    async def copy(format_name):
        if result is None:
            return
        formatter = result.markdown if format_name == 'MD 표' else result.csv
        content = await run.io_bound(formatter)
        if content is None:
            return
        try:
            copied = await ui.run_javascript(f'''
                try {{
                    await navigator.clipboard.writeText({json.dumps(content)});
                    return true;
                }} catch {{
                    return false;
                }}
            ''')
        except TimeoutError:
            copied = False
        if copied:
            ui.notify(f'{format_name} 복사 완료', type='positive')
        else:
            ui.notify('클립보드 복사에 실패했습니다. 브라우저 권한과 접속 주소를 확인하세요.', type='negative')

    async def download_html():
        if result is None:
            return
        title = result_title
        content = await run.io_bound(result.html, title)
        if content is not None:
            ui.download.content(content, filename=query_html_filename(title), media_type='text/html; charset=utf-8')

    with ui.column().classes('w-full gap-3'):
        with ui.row().classes('w-full items-center gap-2'):
            ui.button('저장된 MD 보기', icon='description', on_click=open_documents).props('outline')
            ui.button('MD 등록', icon='add', on_click=lambda: registration_dialog.open()).props('outline')
            document_label = ui.label('선택한 MD 없음').classes('text-sm break-all')
            query_select = ui.select({}, label='쿼리 선택', on_change=load_snippet).props(
                'dense outlined').classes('w-full sm:w-72')
            query_select.disable()
        sql = ui.textarea('DB2 SQL', placeholder='SELECT ...').props('outlined rows=8').classes('w-full')
        with ui.row().classes('items-center gap-2'):
            execute_button = ui.button('조회 실행', icon='play_arrow', on_click=execute)
            md_button = ui.button('MD 표 복사', icon='content_copy', on_click=lambda: copy('MD 표'))
            csv_button = ui.button('CSV 복사', icon='content_copy', on_click=lambda: copy('CSV'))
            html_button = ui.button('HTML 다운로드', icon='download', on_click=download_html)
        status = ui.label(f'최대 {MAX_ROWS:,}건')
        grid = ui.aggrid({
            'columnDefs': [],
            'rowData': [],
            'defaultColDef': {'resizable': True, 'sortable': False, 'editable': False},
            'enableCellTextSelection': True,
            'pagination': False,
            'overlayNoRowsTemplate': '조회 결과가 없습니다.',
        }, auto_size_columns=False).classes('w-full h-[55vh]').mark('db2-query-result')
        grid.set_visibility(False)
        md_button.disable()
        csv_button.disable()
        html_button.disable()
        if not factory_path:
            execute_button.disable()
            status.set_text(f'.env에 {FACTORY_ENV}을 설정한 뒤 대시보드를 재시작하세요.')

    with ui.dialog() as document_dialog, ui.card().classes('w-full max-w-3xl'):
        ui.label('저장된 MD 보기').classes('text-lg font-semibold')
        document_picker = ui.select({}, label='저장 문서', on_change=lambda e: preview_document(e.value)).props(
            'outlined').classes('w-full')
        empty_documents = ui.label('저장된 MD가 없습니다.')
        document_preview = ui.textarea('MD 본문 미리보기').props('outlined readonly rows=12').classes('w-full font-mono')
        with ui.row().classes('w-full justify-end'):
            ui.button('닫기', on_click=document_dialog.close).props('flat')
            use_document_button = ui.button('이 문서 선택', on_click=choose_document)
            use_document_button.disable()

    with ui.dialog() as registration_dialog, ui.card().classes('w-full max-w-3xl'):
        ui.label('MD 등록').classes('text-lg font-semibold')
        registration_title = ui.input('문서 제목').props('outlined').classes('w-full')
        registration_content = ui.textarea('Markdown 본문', placeholder='### 쿼리 제목\n```sql\nSELECT ...\n```').props(
            'outlined rows=12').classes('w-full font-mono')
        with ui.row().classes('w-full justify-end'):
            ui.button('취소', on_click=registration_dialog.close).props('flat')
            ui.button('MD 저장', icon='save', on_click=register_document)
