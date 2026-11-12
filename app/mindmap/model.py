from copy import deepcopy
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Style(BaseModel):
    model_config = ConfigDict(extra='forbid')
    background: str | None = None
    color: str | None = None
    border_color: str | None = None
    font_size: int | None = Field(default=None, ge=10, le=40)
    shape: Literal['rounded', 'rectangle', 'pill', 'ellipse', 'diamond', 'cylinder', 'hexagon', 'document'] | None = None
    icon: str | None = Field(default=None, max_length=12)

    @field_validator('background', 'color', 'border_color')
    @classmethod
    def color_value(cls, value):
        import re
        if value is not None and not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
            raise ValueError('색상은 #RRGGBB 형식으로 입력하세요.')
        return value

    @field_validator('icon')
    @classmethod
    def icon_value(cls, value):
        if value and any(c in value for c in '<>&"\'`'):
            raise ValueError('아이콘에는 문자 또는 이모지만 입력하세요.')
        return value


class NodeType(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=60)
    style: Style = Field(default_factory=Style)


class Node(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')
    label: str = Field(min_length=1, max_length=1000)
    type: str = Field(default='서비스', max_length=60)
    description: str = Field(default='', max_length=20000)
    file: str = Field(default='', max_length=4096)
    overrides: Style = Field(default_factory=Style)
    expanded: bool = True


class Edge(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1, max_length=100)
    source: str
    target: str
    label: str = Field(default='', max_length=1000)
    kind: str = Field(default='참조', max_length=60)
    tree: bool = False
    color: str = Field(default='#b89a60', pattern=r'^#[0-9a-fA-F]{6}$')
    dashed: bool = True
    bidirectional: bool = False


class SummaryStyle(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stroke: str = Field(default='#b89a60', pattern=r'^#[0-9a-fA-F]{6}$')
    labelColor: str = Field(default='#eee9de', pattern=r'^#[0-9a-fA-F]{6}$')


class Summary(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')
    parent: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    label: str = Field(default='요약', min_length=1, max_length=1000)
    style: SummaryStyle = Field(default_factory=SummaryStyle)


class View(BaseModel):
    direction: int = Field(default=1, ge=0, le=3)
    scale: float = Field(default=1, ge=.1, le=8, allow_inf_nan=False)
    pan_x: float = Field(default=0, allow_inf_nan=False)
    pan_y: float = Field(default=0, allow_inf_nan=False)
    scroll_left: float = Field(default=0, ge=0, allow_inf_nan=False)
    scroll_top: float = Field(default=0, ge=0, allow_inf_nan=False)


class Graph(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: Literal[1] = 1
    root: str
    nodes: list[Node] = Field(min_length=1, max_length=2000)
    edges: list[Edge] = Field(default_factory=list, max_length=5000)
    summaries: list[Summary] = Field(default_factory=list, max_length=1000)
    view: View = Field(default_factory=View)

    @model_validator(mode='after')
    def valid_structure(self):
        ids = {node.id for node in self.nodes}
        if len(ids) != len(self.nodes) or self.root not in ids:
            raise ValueError('노드 ID 중복 또는 루트 누락입니다.')
        if len({edge.id for edge in self.edges}) != len(self.edges):
            raise ValueError('관계 ID가 중복되었습니다.')
        parents = {}
        children = {key: [] for key in ids}
        for edge in self.edges:
            if edge.source not in ids or edge.target not in ids:
                raise ValueError('존재하지 않는 노드를 연결한 관계입니다.')
            if edge.tree:
                if edge.target in parents or edge.target == self.root:
                    raise ValueError('계층 노드는 하나의 부모만 가질 수 있습니다.')
                parents[edge.target] = edge.source
                children[edge.source].append(edge.target)
        visited = set()
        stack = [(self.root, 0)]
        while stack:
            node, depth = stack.pop()
            if node in visited or depth > 100:
                raise ValueError('계층 순환 또는 100단계를 초과한 깊이입니다.')
            visited.add(node)
            stack.extend((child, depth + 1) for child in children[node])
        if visited != ids:
            raise ValueError('모든 노드를 루트 계층에 연결하세요. 추가 관계는 별도로 지정할 수 있습니다.')
        if len({item.id for item in self.summaries}) != len(self.summaries):
            raise ValueError('요약 ID가 중복되었습니다.')
        for item in self.summaries:
            if item.parent not in ids or not 0 <= item.start <= item.end < len(children[item.parent]):
                raise ValueError('요약의 대상 계층 범위가 올바르지 않습니다.')
        return self


def default_types():
    result = []
    for name, icon, color in [('서비스', '◇', '#cbb788'), ('화면', '▣', '#a9c7b1'),
                              ('API', '⇄', '#abc5dc'), ('Controller', 'C', '#abc5dc'),
                              ('Service', 'S', '#b9c5a3'), ('Mapper', 'M', '#d4b9a1'),
                              ('테이블', '▤', '#c2b7d7'), ('테스트', '✓', '#a6c9c3'),
                              ('그룹', '▧', '#cbb788')]:
        result.append(NodeType(name=name, style=Style(background='#222b24', color='#eee9de',
                      border_color=color, font_size=15, shape='rounded', icon=icon)).model_dump())
    return result


def new_graph(label='새 마인드맵'):
    root = 'n_' + uuid4().hex[:12]
    return Graph(root=root, nodes=[Node(id=root, label=label)]).model_dump()


def example_graph():
    nodes = [Node(id='root', label='고객 관리 서비스'),
             Node(id='controller', label='CustomerController', type='Controller', file='src/main/java/customer/CustomerController.java'),
             Node(id='service', label='CustomerService', type='Service', description='고객 조회와 검증 로직', file='src/main/java/customer/CustomerService.java'),
             Node(id='mapper', label='CustomerMapper', type='Mapper', file='src/main/resources/mappers/CustomerMapper.xml'),
             Node(id='screen', label='CustomerSearch', type='화면', file='src/main/webapp/customer/CustomerSearch.xfdl'),
             Node(id='table', label='CUSTOMER', type='테이블'), Node(id='test', label='고객 조회 시나리오', type='테스트')]
    pairs = [('root', 'controller'), ('root', 'service'), ('root', 'mapper'),
             ('controller', 'screen'), ('mapper', 'table'), ('service', 'test')]
    edges = [Edge(id=f'e{i}', source=a, target=b, tree=True, kind='계층', dashed=False)
             for i, (a, b) in enumerate(pairs)]
    edges += [Edge(id='call1', source='controller', target='service', label='호출', kind='호출'),
              Edge(id='call2', source='service', target='mapper', label='조회', kind='조회')]
    return Graph(root='root', nodes=nodes, edges=edges).model_dump()


def graph_from_network(nodes, edges, preferred_root=None):
    """Choose a spanning hierarchy; preserve cycles/multiple parents as relations."""
    nodes = deepcopy(nodes)
    edges = deepcopy(edges)
    if not nodes:
        raise ValueError('가져올 노드가 없습니다.')
    ids = {n['id'] for n in nodes}
    incoming = {e['target'] for e in edges}
    candidates = [n['id'] for n in nodes if n['id'] not in incoming]
    root = preferred_root if preferred_root in ids else candidates[0] if len(candidates) == 1 else None
    if root is None:
        root = 'import_' + uuid4().hex[:12]
        nodes.insert(0, {'id': root, 'label': '가져온 맵', 'type': '그룹'})
    reached = {root}
    frontier = [root]
    for edge in edges:
        edge['tree'] = False
    while len(reached) < len(nodes):
        if not frontier:
            seed = next(n['id'] for n in nodes if n['id'] not in reached)
            edges.append({'id': 'join_' + uuid4().hex[:12], 'source': root, 'target': seed, 'tree': True, 'kind': '계층'})
            reached.add(seed)
            frontier.append(seed)
        current = frontier.pop(0)
        for edge in edges:
            if edge['source'] == current and edge['target'] not in reached:
                edge['tree'] = True
                reached.add(edge['target'])
                frontier.append(edge['target'])
    return Graph(root=root, nodes=nodes, edges=edges).model_dump()
