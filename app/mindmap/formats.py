"""DOT and a documented Mermaid subset, with metadata for our own round trips."""
import base64
from collections import defaultdict
import json
import re

from app.mindmap.model import Graph, graph_from_network


def encode(value):
    return base64.urlsafe_b64encode(json.dumps(value, ensure_ascii=False).encode()).decode()


def decode(value):
    return json.loads(base64.urlsafe_b64decode(value).decode())


def unquote(value):
    value = str(value or '')
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except ValueError:
            return value[1:-1].replace('\\"', '"').replace('\\n', '\n')
    return value


def export_graph(value, format):
    graph = Graph.model_validate(value).model_dump()
    nodes, edges = graph['nodes'], graph['edges']
    aliases = {node['id']: f'n{i}' for i, node in enumerate(nodes)}
    q = lambda value: json.dumps(value, ensure_ascii=False)
    if format == 'json':
        return json.dumps(graph, ensure_ascii=False, indent=2)
    if format == 'dot':
        lines = ['digraph ServiceMap {', '  rankdir=LR;', '  node [shape=box, style=rounded];',
                 '  kja_root=' + q(aliases[graph['root']]) + ';', '  kja_view=' + q(encode(graph['view'])) + ';']
        lines.append('  kja_summaries=' + q(encode(graph['summaries'])) + ';')
        for node in nodes:
            metadata = {k: v for k, v in node.items() if k != 'label'}
            lines.append(f'  {aliases[node["id"]]} [label={q(node["label"])}, kja_meta={q(encode(metadata))}];')
        for edge in edges:
            metadata = {k: v for k, v in edge.items() if k not in {'source', 'target', 'label'}}
            lines.append(f'  {aliases[edge["source"]]} -> {aliases[edge["target"]]} [label={q(edge["label"])}, kja_meta={q(encode(metadata))}];')
        return '\n'.join(lines + ['}'])
    if format not in {'flowchart', 'mindmap'}:
        raise ValueError('지원하지 않는 출력 형식입니다.')
    lines = [f'%% kja-root {aliases[graph["root"]]}', f'%% kja-view {encode(graph["view"])}']
    lines.append('%% kja-summaries ' + encode(graph['summaries']))
    for node in nodes:
        lines.append(f'%% kja-node {aliases[node["id"]]} {encode({k: v for k, v in node.items() if k != "label"})}')
    for i, edge in enumerate(edges):
        lines.append(f'%% kja-edge e{i} {encode({k: v for k, v in edge.items() if k not in {"source", "target", "label"}})}')
    # Mermaid entities protect brackets, quotes, newlines and directive-like labels.
    def label(value):
        return ''.join(f'#{ord(c)};' if c in '"[](){}<>|#%\\\n\r' else c for c in value)
    if format == 'flowchart':
        lines.append('flowchart LR')
        lines.extend(f'  {aliases[n["id"]]}["{label(n["label"])}"]' for n in nodes)
        for edge in edges:
            arrow = '<-->' if edge['bidirectional'] else '-.->' if edge['dashed'] and not edge['tree'] else '-->'
            text = f'|{label(edge["label"])}|' if edge['label'] else ''
            lines.append(f'  {aliases[edge["source"]]} {arrow}{text} {aliases[edge["target"]]}')
    else:
        lines.append('mindmap')
        by_id = {node['id']: node for node in nodes}
        children = defaultdict(list)
        for edge in edges:
            if edge['tree']:
                children[edge['source']].append(edge['target'])
        def visit(node_id, depth):
            lines.append('  ' * depth + f'{aliases[node_id]}["{label(by_id[node_id]["label"])}"]')
            for child in children[node_id]:
                visit(child, depth + 1)
        visit(graph['root'], 1)
        # Extra relations have no visual equivalent in mindmap syntax. Keep them
        # in comments so KJA_BOARD can restore them rather than drop them.
        for edge in edges:
            lines.append('%% kja-relation ' + encode(edge))
    return '\n'.join(lines)


def import_graph(source, format):
    if len(source.encode('utf-8')) > 2 * 1024 * 1024:
        raise ValueError('가져오기 파일은 2MB 이하로 준비하세요.')
    warnings = []
    try:
        if format == 'json':
            return Graph.model_validate_json(source).model_dump(), warnings
        if format == 'dot':
            graph = import_dot(source, warnings)
        elif format in {'flowchart', 'mindmap', 'mermaid'}:
            graph = import_mermaid(source, warnings)
        else:
            raise ValueError('지원하지 않는 가져오기 형식입니다.')
        return graph, warnings
    except (ValueError, KeyError, TypeError, RecursionError) as exc:
        raise ValueError(f'가져오기 실패: {exc}') from exc


def import_dot(source, warnings):
    import pydot
    graphs = pydot.graph_from_dot_data(source)
    if not graphs or len(graphs) != 1:
        raise ValueError('하나의 DOT graph / digraph가 필요합니다.')
    graph = graphs[0]
    records, raw_edges, groups = {}, [], []
    def collect(part, group=None):
        members = []
        for node in part.get_nodes():
            name = unquote(node.get_name())
            if name in {'node', 'edge', 'graph', '', '\n', '\\n'}:
                continue
            attrs = node.get_attributes()
            records.setdefault(name, {}).update(attrs)
            members.append(name)
        for edge in part.get_edges():
            if not isinstance(edge.get_source(), str) or not isinstance(edge.get_destination(), str):
                raise ValueError('DOT 집합 간 연결은 개별 노드 연결로 바꿔 주세요.')
            a, b = unquote(edge.get_source()), unquote(edge.get_destination())
            records.setdefault(a, {})
            records.setdefault(b, {})
            raw_edges.append((a, b, edge.get_attributes()))
            members.extend([a, b])
        for child in part.get_subgraphs():
            group_id = '__group_' + str(len(groups))
            groups.append(group_id)
            records[group_id] = {'label': child.get_label() or child.get_name(), 'kind': '그룹'}
            child_members = collect(child, group_id)
            raw_edges.extend((group_id, member, {}) for member in child_members)
            members.append(group_id)
        return members
    collect(graph)
    ids = {name: f'dot_{i}' for i, name in enumerate(records)}
    nodes = []
    for name, attrs in records.items():
        meta = decode(unquote(attrs['kja_meta'])) if attrs.get('kja_meta') else {}
        ids[name] = meta.get('id', ids[name])
        node = dict(meta, id=ids[name], label=unquote(attrs.get('label', name)))
        node.setdefault('type', attrs.get('kind', '서비스'))
        if not meta:
            overrides = {}
            for key, attr in [('color', 'fontcolor'), ('background', 'fillcolor'), ('border_color', 'color')]:
                value = unquote(attrs.get(attr, ''))
                if re.fullmatch(r'#[0-9a-fA-F]{6}', value):
                    overrides[key] = value
            node['overrides'] = overrides
        nodes.append(node)
    edges = []
    for i, (a, b, attrs) in enumerate(raw_edges):
        meta = decode(unquote(attrs['kja_meta'])) if attrs.get('kja_meta') else {}
        edges.append(dict(meta, id=meta.get('id', f'dot_e{i}'), source=ids[a], target=ids[b], label=unquote(attrs.get('label', ''))))
    root = ids.get(unquote(graph.get_attributes().get('kja_root', '')))
    result = restore_network(nodes, edges, root)
    if graph.get_attributes().get('kja_view'):
        result['view'] = decode(unquote(graph.get_attributes()['kja_view']))
    warnings.append('DOT의 배치 명령과 복잡한 스타일은 Mind Elixir에서 다시 배치합니다. 그룹은 그룹 노드로 변환합니다.')
    if graph.get_attributes().get('kja_summaries'):
        result['summaries'] = decode(unquote(graph.get_attributes()['kja_summaries']))
    return Graph.model_validate(result).model_dump()


def mermaid_text(value):
    named = {'quot': '"', 'lt': '<', 'gt': '>', 'amp': '&'}
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        value = unquote(value)
    return re.sub(r'#(\d+|quot|lt|gt|amp);', lambda m: chr(int(m[1])) if m[1].isdigit() else named[m[1]], value)


def read_node(text, start=0):
    match = re.match(r'\s*([A-Za-z_][A-Za-z0-9_-]*)', text[start:])
    if not match:
        raise ValueError(f'노드 ID를 확인하세요: {text[start:]}')
    key = match[1]
    pos = start + match.end()
    while pos < len(text) and text[pos].isspace():
        pos += 1
    label = None
    if pos < len(text) and text[pos] in '[({':
        begin = pos
        stack, quote, escaped = [], False, False
        pairs = {']': '[', ')': '(', '}': '{'}
        while pos < len(text):
            char = text[pos]
            if quote:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quote = False
            elif char == '"':
                quote = True
            elif char in '[({':
                stack.append(char)
            elif char in '])}':
                if not stack or stack.pop() != pairs[char]:
                    raise ValueError('노드 괄호가 맞지 않습니다.')
                if not stack:
                    pos += 1
                    break
            pos += 1
        if stack or quote:
            raise ValueError('닫히지 않은 노드 괄호입니다.')
        raw = text[begin:pos]
        while len(raw) >= 2 and raw[0] in '[({' and raw[-1] in '])}':
            raw = raw[1:-1]
        label = mermaid_text(raw)
    return key, label, pos


def import_mermaid(source, warnings):
    fence = re.search(r'```mermaid\s*\n(.*?)\n```', source, re.S)
    if fence:
        source = fence[1]
    node_meta, edge_meta, full_relations = {}, {}, []
    root_alias, view, summaries = None, None, []
    lines = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith('%% kja-node '):
            _, _, key, value = stripped.split(' ', 3)
            node_meta[key] = decode(value)
        elif stripped.startswith('%% kja-edge '):
            _, _, key, value = stripped.split(' ', 3)
            edge_meta[key] = decode(value)
        elif stripped.startswith('%% kja-root '):
            root_alias = stripped.split()[-1]
        elif stripped.startswith('%% kja-summaries '):
            summaries = decode(stripped.split()[-1])
        elif stripped.startswith('%% kja-view '):
            view = decode(stripped.split()[-1])
        elif stripped.startswith('%% kja-relation '):
            full_relations.append(decode(stripped.split()[-1]))
        elif stripped and not stripped.startswith('%%'):
            lines.append(line)
    if not lines:
        raise ValueError('Mermaid 코드가 없습니다.')
    header = lines.pop(0).strip()
    mindmap = header == 'mindmap'
    if not mindmap and not re.fullmatch(r'(?:flowchart|graph)\s+(?:LR|RL|TB|TD|BT)\s*;?', header):
        raise ValueError('mindmap 또는 flowchart/graph LR·TB 형식만 지원합니다.')
    records, raw_edges = {}, []
    def add(key, label):
        if key not in records:
            records[key] = label or key
        elif label is not None:
            records[key] = label
    if mindmap:
        parents = []
        for i, line in enumerate(lines):
            if '\t' in line:
                raise ValueError('mindmap 들여쓰기는 탭 대신 공백을 사용하세요.')
            depth = len(line) - len(line.lstrip())
            text = line.strip()
            try:
                key, label, end = read_node(text)
                if end < len(text) or label is None:
                    key, label = f'mm_{i}', mermaid_text(text)
            except ValueError:
                key, label = f'mm_{i}', mermaid_text(text)
            add(key, label)
            while parents and parents[-1][0] >= depth:
                parents.pop()
            if parents:
                raw_edges.append((parents[-1][1], key, ''))
            parents.append((depth, key))
    else:
        groups = []
        for line in lines:
            text = line.strip().rstrip(';')
            if text.startswith('subgraph '):
                key = f'group_{len(records)}'
                add(key, text[len('subgraph '):].strip(' []"'))
                if groups:
                    raw_edges.append((groups[-1], key, ''))
                groups.append(key)
                continue
            if text == 'end':
                if not groups:
                    raise ValueError('subgraph 없는 end입니다.')
                groups.pop()
                continue
            if re.match(r'^(?:classDef|class|style|click|linkStyle|direction)\b', text):
                warnings.append('스타일·클릭 동작·방향 선언은 가져오지 않습니다: ' + text[:80])
                continue
            a, label, pos = read_node(text)
            add(a, label)
            if groups and a != groups[-1]:
                raw_edges.append((groups[-1], a, ''))
            while pos < len(text):
                match = re.match(r'\s*(<-->|-->|---|-\.->|==>)(?:\s*\|([^|]*)\|)?\s*', text[pos:])
                if not match:
                    raise ValueError(f'지원하지 않는 연결 표현입니다. -->|이름| 형태를 사용하세요: {text[pos:]}')
                b, label, pos = read_node(text, pos + match.end())
                add(b, label)
                raw_edges.append((a, b, mermaid_text(match[2] or ''), {'dashed': match[1] == '-.->', 'bidirectional': match[1] == '<-->'}))
                a = b
        if groups:
            raise ValueError('닫히지 않은 subgraph가 있습니다.')
    ids = {key: node_meta.get(key, {}).get('id', 'm_' + str(i)) for i, key in enumerate(records)}
    nodes = [dict(node_meta.get(key, {}), id=ids[key], label=label) for key, label in records.items()]
    edges = []
    for i, record in enumerate(raw_edges):
        a, b, label = record[:3]
        meta = edge_meta.get(f'e{i}', record[3] if len(record) > 3 else {})
        edges.append(dict(meta, id=meta.get('id', f'me_{i}'), source=ids[a], target=ids[b], label=label))
    if mindmap and full_relations:
        # Preserve visible hierarchy and restore only non-tree relationships.
        edges = full_relations
    result = restore_network(nodes, edges, ids.get(root_alias))
    result['summaries'] = summaries
    if view:
        result['view'] = view
    warnings.append('Mermaid의 표현 가능한 노드·계층·관계를 가져왔습니다. 배치와 지원하지 않는 스타일은 다시 지정하세요.')
    return Graph.model_validate(result).model_dump()


def restore_network(nodes, edges, root):
    if root:
        try:
            return Graph(root=root, nodes=nodes, edges=edges).model_dump()
        except ValueError:
            pass
    return graph_from_network(nodes, edges, root)
