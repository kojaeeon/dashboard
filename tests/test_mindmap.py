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

@pytest.mark.parametrize('kind',['dot','flowchart','mindmap','json'])
def test_summary_roundtrip_and_sqlite(kind, tmp_path):
    graph=example_graph()
    graph['summaries']=[{'id':'summary1','parent':'root','start':0,'end':1,
                         'label':'고객 처리 요약','style':{'stroke':'#123456','labelColor':'#abcdef'}}]
    original=Graph.model_validate(graph).model_dump()
    converted,_=import_graph(export_graph(original,kind),kind)
    assert converted['summaries']==original['summaries']
    store=MindMapStore(Database(str(tmp_path/'summary.db')))
    key,_=store.save('summary',converted)
    assert store.get(key)['graph']['summaries']==original['summaries']


def test_summary_rejects_missing_parent_and_invalid_range():
    graph=example_graph()
    for parent,start,end in [('missing',0,0),('root',0,99),('root',2,1)]:
        graph['summaries']=[{'id':'s','parent':parent,'start':start,'end':end}]
        with pytest.raises(ValueError):Graph.model_validate(graph)

@pytest.mark.parametrize('shape',['diamond','cylinder','hexagon','document'])
def test_custom_shapes_preserve_type_and_override(shape,tmp_path):
    store=MindMapStore(Database(str(tmp_path/'shapes.db')))
    store.save_type({'name':'Custom','style':{'shape':shape,'background':'#223344'}})
    graph=example_graph();graph['nodes'][1]['type']='Custom';graph['nodes'][2]['overrides']['shape']=shape
    key,_=store.save('shapes',graph)
    restored=store.get(key)['graph']
    assert next(t for t in store.types() if t['name']=='Custom')['style']['shape']==shape
    for kind in ['dot','mindmap','flowchart','json']:
        imported,_=import_graph(export_graph(restored,kind),kind)
        assert next(n for n in imported['nodes'] if n['id']=='service')['overrides']['shape']==shape
        assert next(n for n in imported['nodes'] if n['id']=='controller')['type']=='Custom'
