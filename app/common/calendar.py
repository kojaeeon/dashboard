"""Reusable NiceGUI FullCalendar component with locally bundled dependencies."""
from pathlib import Path
from nicegui import ui


class Calendar(ui.element, component='calendar.js'):
    def __init__(self, *, on_date_click=None, on_event_click=None,
                 on_event_change=None, on_period_change=None):
        super().__init__()
        self.add_resource(Path(__file__).parent / 'calendar_vendor')
        self._props['events'] = []
        self._update_method = 'update_calendar'
        self.classes('schedule-calendar w-full')
        for name, handler in [('date_click', on_date_click), ('event_click', on_event_click),
                              ('event_change', on_event_change), ('period_change', on_period_change)]:
            if handler is not None:
                self.on(name, handler)
        self.on('load_error', lambda: ui.notify('일정표를 불러오지 못했습니다. 페이지를 새로고침해 주세요.', type='negative'))

    def set_events(self, events):
        self._props['events'] = events
        self.update()
