from contextlib import contextmanager
from pathlib import Path
import sqlite3


class Database:
    """One short-lived connection per operation; safe across UI clients."""
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY, path TEXT NOT NULL UNIQUE);
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY, title TEXT NOT NULL,
                    content TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS work_items (
                    id INTEGER PRIMARY KEY, title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'todo'
                        CHECK(status IN ('todo','doing','done')),
                    notes TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            ''')

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    def setting(self, key, default=''):
        with self.connect() as con:
            row = con.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return row['value'] if row else default

    def set_setting(self, key, value):
        with self.connect() as con:
            con.execute('INSERT INTO settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, value))

    @staticmethod
    def _table(table):
        if table not in {'documents', 'work_items'}:
            raise ValueError('Unsupported table')
        return table

    def list(self, table):
        table = self._table(table)
        with self.connect() as con:
            return [dict(row) for row in con.execute(f'SELECT * FROM {table} ORDER BY updated_at DESC, id DESC')]

    def save_document(self, title, content, item_id=None):
        if not title.strip():
            raise ValueError('Title is required')
        with self.connect() as con:
            if item_id is None:
                return con.execute('INSERT INTO documents(title,content) VALUES (?,?)', (title.strip(), content)).lastrowid
            con.execute('UPDATE documents SET title=?,content=?,updated_at=CURRENT_TIMESTAMP WHERE id=?', (title.strip(), content, item_id))
            return item_id

    def save_work(self, title, status='todo', notes='', item_id=None):
        if not title.strip() or status not in {'todo', 'doing', 'done'}:
            raise ValueError('Valid title and status are required')
        with self.connect() as con:
            if item_id is None:
                return con.execute('INSERT INTO work_items(title,status,notes) VALUES (?,?,?)', (title.strip(), status, notes)).lastrowid
            con.execute('UPDATE work_items SET title=?,status=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?', (title.strip(), status, notes, item_id))
            return item_id

    def delete(self, table, item_id):
        table = self._table(table)
        with self.connect() as con:
            con.execute(f'DELETE FROM {table} WHERE id=?', (item_id,))

    def folders(self):
        with self.connect() as con:
            return [dict(row) for row in con.execute('SELECT id, path FROM folders ORDER BY path')]

    def add_folder(self, path):
        if not path.strip():
            raise ValueError('폴더 경로를 입력하세요.')
        folder = Path(path.strip()).expanduser().resolve(strict=True)
        if not folder.is_dir():
            raise ValueError('폴더 경로를 선택하세요.')
        with self.connect() as con:
            con.execute('INSERT OR IGNORE INTO folders(path) VALUES (?)', (str(folder),))

    def remove_folder(self, folder_id):
        with self.connect() as con:
            con.execute('DELETE FROM folders WHERE id=?', (folder_id,))
