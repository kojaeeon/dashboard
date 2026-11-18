"""Db2 query textarea, result grid and clipboard actions."""
import json
import os

from nicegui import run, ui

from app.common.db2_query import FACTORY_ENV, MAX_ROWS, execute_query


def render():
    factory_path = os.getenv(FACTORY_ENV, '').strip()
    result = None

    async def execute():
        nonlocal result
        if not execute_button.enabled:
            return
        execute_button.disable()
        md_button.disable()
        csv_button.disable()
        result = None
        grid.set_visibility(False)
        grid.options.update(columnDefs=[], rowData=[])
        grid.update()
        status.set_text('조회 중…')
        try:
            result = await run.io_bound(execute_query, sql.value or '', factory_path)
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

    with ui.column().classes('w-full gap-3'):
        sql = ui.textarea('DB2 SQL', placeholder='SELECT ...').props('outlined rows=8').classes('w-full')
        with ui.row().classes('items-center gap-2'):
            execute_button = ui.button('조회 실행', icon='play_arrow', on_click=execute)
            md_button = ui.button('MD 표 복사', icon='content_copy', on_click=lambda: copy('MD 표'))
            csv_button = ui.button('CSV 복사', icon='content_copy', on_click=lambda: copy('CSV'))
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
        if not factory_path:
            execute_button.disable()
            status.set_text(f'.env에 {FACTORY_ENV}을 설정한 뒤 대시보드를 재시작하세요.')
