import pytest
from app.common.database import Database
from app.mindmap.model import Graph, example_graph
from app.mindmap.formats import export_graph, import_graph
from app.mindmap.store import MindMapStore

@pytest.mark.parametrize('kind',['dot','flowchart','mindmap','json'])
def test_round_trip_preserves_content(kind):
    graph=example_graph()
    graph['nodes'][1]['label']='Customer "A" [x] / 고객\n조회'
    graph['nodes'][1]['overrides']['color']='#123456'
    result,_=import_graph(export_graph(graph,kind),kind)
    assert sorted(result['nodes'],key=lambda n:n['id'])==sorted(graph['nodes'],key=lambda n:n['id'])
    assert sorted(result['edges'],key=lambda n:n['id'])==sorted(graph['edges'],key=lambda n:n['id'])
    assert result['view']==graph['view']

def test_cycles_and_multiple_parents_are_preserved():
    graph,_=import_graph('digraph {a -> b; b -> c; c -> a; a -> c;}','dot')
    assert len(graph['edges'])-sum(e['tree'] for e in graph['edges'])==2
    assert Graph.model_validate(graph)

def test_plain_mindmap_repeated_labels_are_distinct():
    graph,_=import_graph('mindmap\n  root\n    child\n    child','mermaid')
    assert len(graph['nodes'])==3

def test_mermaid_relations_and_unsafe_directives():
    graph,warnings=import_graph('flowchart LR\nA["화면"] -.->|호출| B["API"]\nB <--> A\nclick A "javascript:alert(1)"','mermaid')
    assert graph['edges'][0]['dashed']
    assert graph['edges'][1]['bidirectional']
    assert any('click' in item for item in warnings)

def test_store_conflicts_and_custom_types(tmp_path):
    db=Database(str(tmp_path/'test.db'));store=MindMapStore(db)
    key,revision=store.save('map',example_graph())
    store.save('updated',example_graph(),key,revision)
    with pytest.raises(ValueError,match='다른 화면'):
        store.save('stale',example_graph(),key,revision)
    store.save_type({'name':'Queue','style':{'color':'#ffffff','shape':'pill'}})
    reopened=MindMapStore(Database(str(tmp_path/'test.db')))
    assert reopened.get(key)['title']=='updated'
    assert any(t['name']=='Queue' for t in reopened.types())
    with pytest.raises(ValueError):reopened.delete(key,1)
    reopened.delete(key,2)
    assert not reopened.list()

def test_invalid_graph_is_not_stored(tmp_path):
    store=MindMapStore(Database(str(tmp_path/'test.db')))
    graph=example_graph();graph['edges'][0]['target']='missing'
    with pytest.raises(ValueError):store.save('bad',graph)
    assert not store.list()
