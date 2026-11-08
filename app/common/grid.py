"""Reusable, read-only AG Grid. Data loading stays with the calling page."""
from dataclasses import dataclass
from html.parser import HTMLParser
import json
from typing import Callable, Literal

from nicegui import ui
from nicegui.events import handle_event


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {'br', 'p', 'div', 'li'}:
            self.parts.append(' ')


@dataclass(frozen=True)
class GridColumn:
    key: str
    label: str
    width: int = 180
    type: str = 'text'

    def definition(self):
        definition = {'field': self.key, 'colId': self.key,
                      'headerName': self.label, 'width': self.width,
                      'filter': 'agNumberColumnFilter' if self.type == 'number' else 'agTextColumnFilter'}
        if self.type == 'number':
            definition['type'] = 'numericColumn'
        return definition

    def value(self, value):
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get('displayName') or value.get('name') or json.dumps(value, ensure_ascii=False)
        if isinstance(value, list):
            return '; '.join(str(self.value(item)) for item in value)
        if self.type == 'html':
            parser = _PlainText()
            parser.feed(str(value))
            return ' '.join(''.join(parser.parts).split())
        return value


class CommonGrid:
    def __init__(self, grid_id: str, columns: list[GridColumn] | None = None, *,
                 selection: Literal['single', 'multiple'] = 'multiple', page_size: int = 20,
                 on_row_click: Callable | None = None,
                 on_row_double_click: Callable | None = None):
        if selection not in {'single', 'multiple'}:
            raise ValueError('selection must be single or multiple')
        self.grid_id = grid_id
        self.columns = list(columns or [])
        self.rows = []
        with ui.column().classes('w-full gap-2') as self.container:
            with ui.row().classes('w-full items-center gap-2'):
                self.count = ui.label('0건')
                self.selected_count = ui.label('선택 0건')
                self.search = ui.input('결과 내 검색', on_change=self._search).props('clearable dense')
                ui.button('필터 초기화', on_click=self.reset_filters).props('flat dense')
                ui.button('선택 해제', on_click=self.deselect_all).props('flat dense')
                ui.button('CSV 다운로드', icon='download', on_click=self.export_csv).props('flat dense')
            self.element = ui.aggrid({
                'columnDefs': [c.definition() for c in self.columns],
                'rowData': [],
                # ADO reference names contain literal dots, not nested object paths.
                'suppressFieldDotNotation': True,
                'defaultColDef': {'sortable': True, 'resizable': True, 'filter': True,
                                  'minWidth': 90, 'editable': False},
                'rowSelection': {'mode': 'multiRow' if selection == 'multiple' else 'singleRow',
                                 'enableClickSelection': True},
                'pagination': True, 'paginationPageSize': page_size,
                'paginationPageSizeSelector': sorted({10, 20, 50, 100, page_size}),
                'enableCellTextSelection': True,
                'overlayNoRowsTemplate': '조회 결과가 없습니다.',
            }, auto_size_columns=False).classes('w-full h-96').mark(grid_id)
            self.element.on('selectionChanged', self._selection_changed)
            if on_row_click:
                self.element.on('rowClicked', lambda e: handle_event(on_row_click, e.args.get('data', {})))
            if on_row_double_click:
                self.element.on('rowDoubleClicked', lambda e: handle_event(on_row_double_click, e.args.get('data', {})))

    def set_columns(self, columns: list[GridColumn]):
        self.columns = list(columns)
        self.element.options['columnDefs'] = [c.definition() for c in self.columns]
        self.set_rows([])

    def set_rows(self, rows: list[dict]):
        self.rows = [{**row, **{c.key: c.value(row.get(c.key)) for c in self.columns}} for row in rows]
        self.element.options['rowData'] = self.rows
        self.element.update()
        self.count.set_text(f'{len(self.rows)}건')
        self.selected_count.set_text('선택 0건')

    def clear(self):
        self.set_rows([])

    async def get_selected_rows(self):
        return await self.element.get_selected_rows()

    async def _selection_changed(self):
        self.selected_count.set_text(f'선택 {len(await self.get_selected_rows())}건')

    def _search(self, event):
        self.element.run_grid_method('setGridOption', 'quickFilterText', event.value or '')

    def reset_filters(self):
        self.search.set_value('')
        self.element.run_grid_method('setFilterModel', None)

    def deselect_all(self):
        self.element.run_grid_method('deselectAll')

    def export_csv(self):
        # Export current filtered/sorted rows; neutralize spreadsheet formulas.
        self.element.run_grid_method('exportDataAsCsv', {
            'fileName': f'{self.grid_id}.csv',
            ':processCellCallback': r'''params => {
                const value = params.value == null ? '' : String(params.value);
                return /^[\s]*[=+@-]/.test(value) ? "'" + value : value;
            }''',
        })
