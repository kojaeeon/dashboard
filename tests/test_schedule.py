from datetime import timedelta
import pytest
from app.common.database import Database
from app.scheduling.repository import ScheduleRepository
from app.scheduling.service import ScheduleService, seoul_datetime


@pytest.fixture
def service(tmp_path):
    return ScheduleService(ScheduleRepository(Database(str(tmp_path / 'schedule.db'))))


def test_all_day_crud_and_exclusive_period(service):
    event_id = service.save('정기점검', '2026-11-09', '2026-11-10', all_day=True, category='deadline')
    event = service.find_by_period('2026-11-09T00:00:00+09:00', '2026-11-10T00:00:00+09:00')[0]
    assert event['allDay'] and event['start'] == '2026-11-09' and event['end'] == '2026-11-10'
    assert not service.find_by_period('2026-11-10T00:00:00+09:00', '2026-11-11T00:00:00+09:00')
    assert not service.find_by_period('2026-11-08', '2026-11-09')
    service.save('수정', '2026-11-09', '2026-11-12', all_day=True, event_id=event_id)
    assert service.find_by_period('2026-11-10', '2026-11-11')[0]['title'] == '수정'
    service.delete(event_id)
    assert not service.find_by_period('2026-11-01', '2026-12-01')


def test_timed_events_are_seoul_even_for_utc_input(service):
    event_id = service.save('회의', '2026-11-09T00:00:00Z', '2026-11-09T01:00:00Z')
    row = service.get(event_id)
    assert row['start'] == '2026-11-09T09:00:00+09:00'
    assert seoul_datetime('2026-11-09T09:00').utcoffset() == timedelta(hours=9)
    assert not service.find_by_period('2026-11-09T10:00:00+09:00', '2026-11-10')
    assert service.find_by_period('2026-11-09T08:30:00+09:00', '2026-11-09T09:30:00+09:00')


def test_move_preserves_details_and_supports_all_day_conversion(service):
    event_id = service.save('test', '2026-11-09', '2026-11-10', all_day=True, category='personal', notes='memo')
    service.move(event_id, '2026-11-11T23:30:00+09:00', '2026-11-12T00:30:00+09:00', False)
    row = service.get(event_id)
    assert row['all_day'] == 0 and row['notes'] == 'memo' and row['category'] == 'personal'
    assert service.find_by_period('2026-11-12', '2026-11-13')
    service.move(event_id, '2026-11-15', '', True)
    assert service.get(event_id)['end'] == '2026-11-16'


@pytest.mark.parametrize('title,start,end,all_day,category', [
    (' ', '2026-11-09', '2026-11-10', True, 'work'),
    ('test', 'bad', '2026-11-10', True, 'work'),
    ('test', '2026-11-10', '2026-11-10', True, 'work'),
    ('test', '2026-11-10', '2026-11-09', True, 'work'),
    ('test', '2026-11-09T10:00', '2026-11-09T09:00', False, 'work'),
    ('test', '2026-11-09', '2026-11-10', True, 'unknown'),
])
def test_invalid_values_cannot_write(service, title, start, end, all_day, category):
    with pytest.raises(ValueError):
        service.save(title, start, end, all_day=all_day, category=category)
    assert not service.find_by_period('2026-11-01', '2026-12-01')


def test_missing_update_does_not_recreate_deleted_event(service):
    with pytest.raises(ValueError):
        service.save('test', '2026-11-09', '2026-11-10', all_day=True, event_id=999)


def test_existing_database_and_repeated_initialization(tmp_path):
    db = Database(str(tmp_path / 'old.db'))
    doc_id = db.save_document('Existing', 'Keep')
    first = ScheduleService(ScheduleRepository(db))
    event_id = first.save('persist', '2026-11-09', '2026-11-10', all_day=True)
    second = ScheduleService(ScheduleRepository(db))
    assert second.get(event_id)['title'] == 'persist'
    assert db.list('documents')[0]['id'] == doc_id


@pytest.mark.asyncio
async def test_schedule_menu_create_edit_delete(user, tmp_path, monkeypatch):
    from nicegui import ui
    import app.main as main
    monkeypatch.setattr(main, 'db', Database(str(tmp_path / 'ui.db')))
    ui.page('/')(main.index)
    await user.open('/')
    user.find('일정', kind=ui.tab).click()
    user.find(marker='schedule-add').click()
    user.find(marker='schedule-title').type('점검 일정')
    user.find(marker='schedule-save').click()
    await user.should_see('일정을 저장했습니다.')
    with main.db.connect() as con:
        row = dict(con.execute('SELECT * FROM schedule_events').fetchone())
    assert row['title'] == '점검 일정'
    from app.common.calendar import Calendar
    user.find(kind=Calendar).trigger('period_change', {'start': row['start'], 'end': row['end']})
    user.find(kind=Calendar).trigger('event_click', {'id': str(row['id'])})
    await user.should_see('일정 수정')
    user.find(marker='schedule-title').clear().type('수정 일정')
    user.find(marker='schedule-save').click()
    assert ScheduleRepository(main.db).get(row['id'])['title'] == '수정 일정'
    user.find(kind=Calendar).trigger('event_change', {
        'id': str(row['id']), 'start': '2026-11-20', 'end': '2026-11-22', 'allDay': True})
    assert ScheduleRepository(main.db).get(row['id'])['end'] == '2026-11-22'
    user.find(kind=Calendar).trigger('event_click', {'id': str(row['id'])})
    user.find(marker='schedule-delete').click()
    await user.should_see('이 일정을 삭제할까요?')
    user.find(marker='schedule-confirm-delete').click()
    await user.should_see('일정을 삭제했습니다.')
    with pytest.raises(ValueError):
        ScheduleRepository(main.db).get(row['id'])
