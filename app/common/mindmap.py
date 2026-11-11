"""Local Mind Elixir editor; snapshots are read directly before saving."""
from pathlib import Path
from nicegui import ui


class MindMapEditor(ui.element, component='mindmap.js'):
    def __init__(self, graph, types):
        super().__init__()
        self.add_resource(Path(__file__).parent / 'mindmap_vendor')
        self._props.update(graph=graph, types=types)
        self._update_method = 'loadGraphFromProps'
        self.classes('w-full')

    def load(self, graph):
        self._props['graph'] = graph
        self.update()
