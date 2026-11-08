"""Seoul wall time for timed events; date-only, exclusive end for all-day events."""
from datetime import date, datetime, time, timedelta, timezone
from app.scheduling.repository import ScheduleRepository

# Seoul has no daylight-saving transitions in the dates supported by this UI.
# A fixed offset also works on Windows without a system IANA timezone database.
SEOUL = timezone(timedelta(hours=9), 'Asia/Seoul')
CATEGORIES = {'work': '업무', 'personal': '개인', 'meeting': '회의', 'deadline': '마감'}
COLORS = {'work': '#51786b', 'personal': '#647eae', 'meeting': '#9b78ab', 'deadline': '#be6654'}


def seoul_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.replace(tzinfo=SEOUL) if parsed.tzinfo is None else parsed.astimezone(SEOUL)
    except (TypeError, ValueError) as exc:
        raise ValueError('올바른 날짜와 시간을 입력하세요.') from exc


class ScheduleService:
    def __init__(self, repository: ScheduleRepository):
        self.repository = repository

    def save(self, title, start, end, *, all_day=False, category='work', notes='', event_id=None):
        if not isinstance(title, str) or not title.strip():
            raise ValueError('일정 제목을 입력하세요.')
        if category not in CATEGORIES:
            raise ValueError('일정 분류를 선택하세요.')
        if all_day:
            try:
                start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
            except (TypeError, ValueError) as exc:
                raise ValueError('올바른 날짜를 입력하세요.') from exc
            start_dt = datetime.combine(start_date, time(), SEOUL)
            end_dt = datetime.combine(end_date, time(), SEOUL)
            start_value, end_value = start_date.isoformat(), end_date.isoformat()
        else:
            start_dt, end_dt = seoul_datetime(start), seoul_datetime(end)
            start_value, end_value = start_dt.isoformat(), end_dt.isoformat()
        if end_dt <= start_dt:
            raise ValueError('종료는 시작보다 늦어야 합니다.')
        return self.repository.save({
            'title': title.strip(), 'start': start_value, 'end': end_value,
            'all_day': int(all_day), 'category': category, 'notes': notes or '',
            'start_ts': int(start_dt.timestamp()), 'end_ts': int(end_dt.timestamp()),
        }, event_id)

    def find_by_period(self, start, end):
        start_dt, end_dt = seoul_datetime(start), seoul_datetime(end)
        if end_dt <= start_dt:
            raise ValueError('조회 기간이 올바르지 않습니다.')
        return [self.to_event(row) for row in self.repository.find_by_period(
            int(start_dt.timestamp()), int(end_dt.timestamp()))]

    @staticmethod
    def to_event(row):
        return {'id': str(row['id']), 'title': row['title'], 'start': row['start'],
                'end': row['end'], 'allDay': bool(row['all_day']),
                'backgroundColor': COLORS[row['category']], 'borderColor': COLORS[row['category']],
                'extendedProps': {'category': row['category'], 'notes': row['notes']}}

    def get(self, event_id):
        return self.repository.get(int(event_id))

    def move(self, event_id, start, end, all_day):
        row = self.get(event_id)
        if not end:
            end = ((date.fromisoformat(start) + timedelta(days=1)).isoformat() if all_day
                   else (seoul_datetime(start) + timedelta(hours=1)).isoformat())
        return self.save(row['title'], start, end, all_day=all_day,
                         category=row['category'], notes=row['notes'], event_id=row['id'])

    def delete(self, event_id):
        self.repository.delete(int(event_id))
