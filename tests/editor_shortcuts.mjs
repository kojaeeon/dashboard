// Run with: node --test tests/editor_shortcuts.mjs
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {test} from 'node:test';
const source = readFileSync(new URL('../app/common/mindmap.js', import.meta.url), 'utf8')
    .replace(/^import .*?;\n/, '');
const {default: component} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const clone = x => structuredClone(x);
function setup() {
    const graph = {
        root:'root', view:{direction:1},
        nodes:['root','parent','child','target'].map(id => ({id,label:id,type:'Service',
            description:'설명',file:'src/Test.java',expanded:true,overrides:{color:'#abcdef'}})),
        edges:[{id:'a',source:'root',target:'parent',tree:true},
            {id:'b',source:'parent',target:'child',tree:true},
            {id:'c',source:'root',target:'target',tree:true},
            {id:'inside',source:'child',target:'parent',tree:false,label:'호출'},
            {id:'outside',source:'parent',target:'target',tree:false}],
    };
    const vm = {...component.methods, ready:true, graph:clone(graph), commits:0};
    const element = id => ({nodeObj:{id}});
    vm.mind = {currentNodes:[element('parent'),element('child')], findEle:element,
        unselectNodes(){this.currentNodes=[]}, selectNodes(nodes){this.currentNodes=nodes}};
    vm.getSnapshot = () => ({graph:clone(vm.graph)});
    vm.commit = g => {vm.graph=clone(g); vm.commits++};
    vm.select = id => {vm.selected=id};
    const clipboard = new Map();
    const event = (editing=false) => ({target:{closest:()=>editing},
        clipboardData:{getData:type=>clipboard.get(type)||'',setData:(type,data)=>clipboard.set(type,data)},
        preventDefault(){this.prevented=true}, stopPropagation(){this.stopped=true}});
    return {vm,graph,event,clipboard,element};
}
test('copy overlapping selections once; paste with independent IDs, metadata and internal relations', () => {
    const {vm,graph,event,clipboard,element}=setup();
    vm.copyNodes(event());
    const copied=JSON.parse(clipboard.get('text/plain'));
    assert.deepEqual(copied.roots,['parent']);
    assert.equal(copied.nodes.length,2);
    assert.deepEqual(copied.edges.map(e=>e.id),['b','inside']);
    vm.mind.currentNodes=[element('target')];
    vm.pasteNodes(event());
    assert.equal(vm.commits,1);
    assert.equal(vm.graph.nodes.length,6);
    const added=vm.graph.nodes.slice(4);
    assert.equal(new Set(vm.graph.nodes.map(n=>n.id)).size,6);
    assert.equal(new Set(vm.graph.edges.map(e=>e.id)).size,vm.graph.edges.length);
    for(const n of added)assert.deepEqual({...n,id:n.label},graph.nodes.find(x=>x.id===n.label));
    const parent=added.find(n=>n.label==='parent').id;
    const child=added.find(n=>n.label==='child').id;
    assert(vm.graph.edges.some(e=>e.tree&&e.source==='target'&&e.target===parent));
    assert(vm.graph.edges.some(e=>e.tree&&e.source===parent&&e.target===child));
    assert(vm.graph.edges.some(e=>!e.tree&&e.source===child&&e.target===parent&&e.label==='호출'));
    vm.pasteNodes(event());
    assert.equal(vm.graph.nodes.length,8);
    assert.equal(new Set(vm.graph.nodes.map(n=>n.id)).size,8);
});
test('copy root and paste in another map; original clipboard is a snapshot', () => {
    const {vm,event,clipboard,element}=setup();
    vm.mind.currentNodes=[element('root')];vm.copyNodes(event());
    vm.graph.nodes[0].label='changed';
    const target=setup();target.clipboard.set('text/plain',clipboard.get('text/plain'));
    target.vm.mind.currentNodes=[target.element('target')];target.vm.pasteNodes(target.event());
    assert.equal(target.vm.graph.nodes.length,8);
    assert.equal(target.vm.graph.nodes[4].label,'root');
});
test('input fields and foreign clipboard text retain native copy/paste', () => {
    const {vm,event,clipboard}=setup();
    const input=event(true);vm.copyNodes(input);vm.pasteNodes(input);
    assert(!input.prevented);assert.equal(vm.commits,0);
    clipboard.set('text/plain','ordinary text');
    const native=event();vm.pasteNodes(native);assert(!native.prevented);
});
test('missing paste target and cyclic clipboard leave graph unchanged', () => {
    const {vm,event,clipboard}=setup();vm.copyNodes(event());
    vm.mind.currentNodes=[];vm.pasteNodes(event());assert.equal(vm.commits,0);
    const data=JSON.parse(clipboard.get('text/plain'));
    data.edges.push({id:'cycle',source:'child',target:'parent',tree:true});
    data.roots=[];clipboard.set('text/plain',JSON.stringify(data));
    vm.mind.currentNodes=[{nodeObj:{id:'target'}}];vm.pasteNodes(event());
    assert.equal(vm.commits,0);assert.equal(vm.graph.nodes.length,4);
});
test('Ctrl+A selects all nodes, while text editing retains native select-all', () => {
    const {vm,event}=setup();vm.nodes=vm.graph.nodes;
    const key={...event(),ctrlKey:true,key:'a'};vm.key(key);
    assert(key.prevented);assert.equal(vm.mind.currentNodes.length,4);
    const input={...event(true),ctrlKey:true,key:'a'};vm.key(input);assert(!input.prevented);
});
