import json
from app.mindmap.model import Graph, NodeType, default_types


class MindMapStore:
    def __init__(self, db):
        self.db = db
        with db.connect() as con:
            con.executescript('''
                CREATE TABLE IF NOT EXISTS mind_maps (
                    id INTEGER PRIMARY KEY, title TEXT NOT NULL, graph_json TEXT NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS mindmap_types (
                    name TEXT PRIMARY KEY, style_json TEXT NOT NULL);
            ''')
            for node_type in default_types():
                con.execute('INSERT OR IGNORE INTO mindmap_types VALUES (?,?)',
                            (node_type['name'], json.dumps(node_type['style'], ensure_ascii=False)))

    def list(self):
        with self.db.connect() as con:
            return [dict(row) for row in con.execute('SELECT id,title,revision,updated_at FROM mind_maps ORDER BY updated_at DESC,id DESC')]

    def get(self, item_id):
        with self.db.connect() as con:
            row = con.execute('SELECT * FROM mind_maps WHERE id=?', (item_id,)).fetchone()
        if row is None:
            raise ValueError('저장된 맵이 없습니다.')
        result = dict(row)
        result['graph'] = json.loads(result.pop('graph_json'))
        return result

    def save(self, title, graph, item_id=None, revision=None):
        if not title.strip():
            raise ValueError('맵 제목을 입력하세요.')
        payload = Graph.model_validate(graph).model_dump_json()
        with self.db.connect() as con:
            if item_id is None:
                item_id = con.execute('INSERT INTO mind_maps(title,graph_json) VALUES (?,?)', (title.strip(), payload)).lastrowid
                return item_id, 1
            updated = con.execute('UPDATE mind_maps SET title=?,graph_json=?,revision=revision+1,updated_at=CURRENT_TIMESTAMP WHERE id=? AND revision=?',
                                  (title.strip(), payload, item_id, revision))
            if updated.rowcount != 1:
                raise ValueError('다른 화면에서 맵이 변경되거나 삭제되었습니다. 다시 열어 확인하세요.')
        return item_id, revision + 1

    def delete(self, item_id, revision):
        with self.db.connect() as con:
            result = con.execute('DELETE FROM mind_maps WHERE id=? AND revision=?', (item_id, revision))
            if result.rowcount != 1:
                raise ValueError('맵이 변경되거나 삭제되었습니다. 목록을 다시 확인하세요.')

    def types(self):
        with self.db.connect() as con:
            return [{'name': row['name'], 'style': json.loads(row['style_json'])}
                    for row in con.execute('SELECT * FROM mindmap_types ORDER BY name')]

    def save_type(self, value):
        node_type = NodeType.model_validate(value)
        if not node_type.name.strip():
            raise ValueError('유형 이름을 입력하세요.')
        with self.db.connect() as con:
            con.execute('INSERT INTO mindmap_types VALUES (?,?) ON CONFLICT(name) DO UPDATE SET style_json=excluded.style_json',
                        (node_type.name.strip(), node_type.style.model_dump_json()))
