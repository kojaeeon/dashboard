"""Schedule menu: calendar, event editor and period list."""
from datetime import date, datetime, timedelta
import sqlite3
from nicegui import ui
from app.common.calendar import Calendar
from app.common.database import Database
from app.scheduling.repository import ScheduleRepository
from app.scheduling.service import CATEGORIES, COLORS, SEOUL, ScheduleService, seoul_datetime


def render(db: Database):
    service = ScheduleService(ScheduleRepository(db))
    visible = {'start': None, 'end': None, 'events': []}
    ui.label('PLAN YOUR DAY').classes('eyebrow')
    ui.label('일정').classes('page-title')
    ui.label('날짜를 눌러 등록하고, 일정을 눌러 수정하세요. 시간은 한국 시간 기준입니다.').classes('text-gray-500')

    def notify_error(exc):
        ui.notify(str(exc) if isinstance(exc, ValueError) else '일정을 저장하거나 불러오지 못했습니다. 다시 시도해 주세요.', type='negative')

    def refresh():
        try:
            if visible['start']:
                visible['events'] = service.find_by_period(visible['start'], visible['end'])
            calendar.set_events(visible['events'])
            event_list.refresh()
        except (ValueError, sqlite3.Error) as exc:
            notify_error(exc)
            calendar.set_events(visible['events'])

    def period_changed(e):
        visible.update(start=e.args['start'], end=e.args['end'])
        refresh()

    def edit_event(event_id):
        try:
            editor(service.get(event_id))
        except (ValueError, sqlite3.Error) as exc:
            notify_error(exc)
            refresh()

    def event_changed(e):
        try:
            service.move(e.args['id'], e.args['start'], e.args['end'], e.args['allDay'])
        except (ValueError, sqlite3.Error) as exc:
            notify_error(exc)
        finally:
            # Always replace optimistic drag/resize data with persisted events.
            refresh()

    def editor(item=None, *, start=None, all_day=True):
        if item:
            all_day = bool(item['all_day'])
            start_value = item['start']
            end_value = item['end']
        else:
            start_value = start or datetime.now(SEOUL).date().isoformat()
            end_value = ((date.fromisoformat(start_value) + timedelta(days=1)).isoformat() if all_day
                         else (seoul_datetime(start_value) + timedelta(hours=1)).isoformat())
        if all_day:
            start_date = date.fromisoformat(start_value)
            end_date = date.fromisoformat(end_value) - timedelta(days=1)
            start_time, end_time = '09:00', '10:00'
        else:
            start_dt, end_dt = seoul_datetime(start_value), seoul_datetime(end_value)
            start_date, end_date = start_dt.date(), end_dt.date()
            start_time, end_time = start_dt.strftime('%H:%M'), end_dt.strftime('%H:%M')
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
            def close_editor():
                dialog.close()
                dialog.delete()

            dialog.on('hide', lambda: dialog.delete() if not dialog.is_deleted else None)
            ui.label('일정 수정' if item else '새 일정').classes('text-lg font-bold')
            title = ui.input('일정 제목', value=item['title'] if item else '').classes('w-full').mark('schedule-title')
            category = ui.select(CATEGORIES, value=item['category'] if item else 'work', label='분류').classes('w-full')
            whole_day = ui.checkbox('종일', value=all_day).mark('schedule-all-day')
            with ui.row().classes('w-full'):
                start_input = ui.input('시작 날짜', value=start_date.isoformat()).props('type=date').classes('flex-1').mark('schedule-start-date')
                end_input = ui.input('종료 날짜', value=end_date.isoformat()).props('type=date').classes('flex-1').mark('schedule-end-date')
            with ui.row().classes('w-full') as times:
                start_clock = ui.input('시작 시간', value=start_time).props('type=time').classes('flex-1').mark('schedule-start-time')
                end_clock = ui.input('종료 시간', value=end_time).props('type=time').classes('flex-1').mark('schedule-end-time')
            times.bind_visibility_from(whole_day, 'value', backward=lambda value: not value)
            ui.label('종일 일정의 종료 날짜는 마지막 일정일입니다.').classes('text-sm text-gray-500')
            notes = ui.textarea('일정 메모', value=item['notes'] if item else '').classes('w-full')

            def save():
                try:
                    if whole_day.value:
                        begin = date.fromisoformat(start_input.value).isoformat()
                        finish = (date.fromisoformat(end_input.value) + timedelta(days=1)).isoformat()
                    else:
                        begin = f'{start_input.value}T{start_clock.value}'
                        finish = f'{end_input.value}T{end_clock.value}'
                    service.save(title.value, begin, finish, all_day=whole_day.value,
                                 category=category.value, notes=notes.value,
                                 event_id=item['id'] if item else None)
                except (ValueError, TypeError, sqlite3.Error) as exc:
                    notify_error(ValueError('올바른 날짜와 시간을 입력하세요.') if isinstance(exc, TypeError) else exc)
                    return
                refresh()
                ui.notify('일정을 저장했습니다.', type='positive')
                close_editor()

            async def delete():
                with ui.dialog() as confirmation, ui.card():
                    ui.label('이 일정을 삭제할까요?')
                    ui.label(item['title'])
                    with ui.row():
                        ui.button('취소', on_click=lambda: confirmation.submit(False)).props('flat')
                        ui.button('삭제', color='negative', on_click=lambda: confirmation.submit(True)).mark('schedule-confirm-delete')
                if await confirmation:
                    try:
                        service.delete(item['id'])
                    except (ValueError, sqlite3.Error) as exc:
                        notify_error(exc)
                        return
                    refresh()
                    ui.notify('일정을 삭제했습니다.', type='positive')
                    close_editor()

            with ui.row().classes('w-full justify-end'):
                if item:
                    ui.button('삭제', icon='delete', color='negative', on_click=delete).props('flat').mark('schedule-delete')
                ui.button('취소', on_click=close_editor).props('flat')
                ui.button('저장', on_click=save).mark('schedule-save')
        dialog.open()

    with ui.row().classes('w-full items-center gap-3'):
        ui.button('일정 추가', icon='add', on_click=lambda: editor()).mark('schedule-add')
        ui.button('새로고침', icon='refresh', on_click=refresh).props('flat')
        for key, label in CATEGORIES.items():
            with ui.row().classes('items-center gap-1'):
                ui.icon('circle', color=COLORS[key]).classes('text-xs')
                ui.label(label).classes('text-sm')
    with ui.card().classes('w-full'):
        calendar = Calendar(
            on_date_click=lambda e: editor(start=e.args['start'], all_day=e.args['allDay']),
            on_event_click=lambda e: edit_event(e.args['id']),
            on_event_change=event_changed, on_period_change=period_changed)

    @ui.refreshable
    def event_list():
        with ui.expansion('현재 기간의 일정 목록', icon='event_note').classes('w-full'):
            if not visible['events']:
                ui.label('표시할 일정이 없습니다.').classes('text-gray-500')
            for event in visible['events']:
                text = event['start'] if event['allDay'] else seoul_datetime(event['start']).strftime('%Y-%m-%d %H:%M')
                ui.button(f"{text} · {event['title']}",
                          on_click=lambda event_id=event['id']: edit_event(event_id)).props('flat no-caps').classes('w-full justify-start')
    event_list()
