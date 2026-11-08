"""Schedule persistence in the existing dashboard database."""
from app.common.database import Database


class ScheduleRepository:
    def __init__(self, db: Database):
        self.db = db
        with db.connect() as con:
            con.executescript('''
                CREATE TABLE IF NOT EXISTS schedule_events (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    start TEXT NOT NULL,
                    end TEXT NOT NULL,
                    all_day INTEGER NOT NULL CHECK(all_day IN (0, 1)),
                    category TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    start_ts INTEGER NOT NULL,
                    end_ts INTEGER NOT NULL CHECK(end_ts > start_ts),
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_schedule_period
                    ON schedule_events(start_ts, end_ts);
            ''')

    def find_by_period(self, start_ts, end_ts):
        with self.db.connect() as con:
            return [dict(row) for row in con.execute('''
                SELECT * FROM schedule_events WHERE start_ts < ? AND end_ts > ?
                ORDER BY start_ts, id
            ''', (end_ts, start_ts))]

    def get(self, event_id):
        with self.db.connect() as con:
            row = con.execute('SELECT * FROM schedule_events WHERE id=?', (event_id,)).fetchone()
        if row is None:
            raise ValueError('일정을 찾을 수 없습니다. 새로고침해 주세요.')
        return dict(row)

    def save(self, event, event_id=None):
        columns = ('title', 'start', 'end', 'all_day', 'category', 'notes', 'start_ts', 'end_ts')
        values = [event[key] for key in columns]
        with self.db.connect() as con:
            if event_id is None:
                return con.execute(
                    f"INSERT INTO schedule_events({','.join(columns)}) VALUES (?,?,?,?,?,?,?,?)",
                    values).lastrowid
            cursor = con.execute(
                'UPDATE schedule_events SET ' + ','.join(f'{key}=?' for key in columns)
                + ',updated_at=CURRENT_TIMESTAMP WHERE id=?', [*values, event_id])
            if cursor.rowcount != 1:
                raise ValueError('일정을 찾을 수 없습니다. 새로고침해 주세요.')
        return event_id

    def delete(self, event_id):
        with self.db.connect() as con:
            if con.execute('DELETE FROM schedule_events WHERE id=?', (event_id,)).rowcount != 1:
                raise ValueError('일정을 찾을 수 없습니다. 새로고침해 주세요.')
