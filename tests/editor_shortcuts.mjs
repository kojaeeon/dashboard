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

function menuRefs(vm) {
    const menu={hidden:false};let focused=0;
    vm.$refs={canvas:{querySelector:()=>menu},root:{focus(){focused++}}};
    return {menu,focused:()=>focused};
}
function shortcut(event,key,shiftKey=true) {
    return {...event(),ctrlKey:true,shiftKey,key,clipboardData:undefined};
}
test('Ctrl+Shift+C/V copies and pastes without browser clipboard events or API', async () => {
    const {vm,event,element}=setup();menuRefs(vm);
    const descriptor=Object.getOwnPropertyDescriptor(globalThis,'navigator');
    Object.defineProperty(globalThis,'navigator',{value:{},configurable:true});
    try {
        const copy=shortcut(event,'C');vm.key(copy);
        assert(copy.prevented&&copy.stopped);
        assert.match(vm.message,/2개 노드를 복사/);
        vm.mind.currentNodes=[element('target')];
        const paste=shortcut(event,'V');vm.key(paste);
        assert(paste.prevented&&paste.stopped);
        assert.equal(vm.graph.nodes.length,6);
        assert.equal(vm.commits,1);
        // Holding the shortcut does not duplicate the subtree repeatedly.
        vm.key({...shortcut(event,'V'),repeat:true});
        assert.equal(vm.commits,1);
    } finally {
        if(descriptor)Object.defineProperty(globalThis,'navigator',descriptor);
        else delete globalThis.navigator;
    }
});
test('context menu copies right-click selection and pastes under the current target', async () => {
    const {vm,element}=setup();const refs=menuRefs(vm);
    const options=vm.contextMenuOptions();
    assert.deepEqual(options.extend.map(x=>x.name),['복사','붙여넣기']);
    assert.deepEqual(options.extend.map(x=>x.key),['Ctrl+Shift+C','Ctrl+Shift+V']);
    options.extend[0].onclick();
    assert(refs.menu.hidden);assert.equal(refs.focused(),1);
    vm.mind.currentNodes=[element('target')];
    await options.extend[1].onclick();
    assert.equal(vm.graph.nodes.length,6);
    assert.equal(refs.focused(),2);
});
test('Ctrl+C/V also works when Clipboard API rejects permission', async () => {
    const {vm,event,element}=setup();menuRefs(vm);
    const descriptor=Object.getOwnPropertyDescriptor(globalThis,'navigator');
    Object.defineProperty(globalThis,'navigator',{value:{clipboard:{
        writeText:async()=>{throw Error('NotAllowedError')},
        readText:async()=>{throw Error('NotAllowedError')},
    }},configurable:true});
    try {
        vm.key(shortcut(event,'c',false));
        vm.mind.currentNodes=[element('target')];
        vm.key(shortcut(event,'v',false));
        await Promise.resolve();
        assert.equal(vm.graph.nodes.length,6);
    } finally {
        if(descriptor)Object.defineProperty(globalThis,'navigator',descriptor);
        else delete globalThis.navigator;
    }
});
test('node shortcuts leave text fields alone and support Cmd modifiers', () => {
    const {vm,event,element}=setup();menuRefs(vm);
    for(const key of ['c','v']) {
        const input={...event(true),ctrlKey:true,shiftKey:true,key};
        vm.key(input);assert(!input.prevented);
    }
    vm.key({...event(),metaKey:true,shiftKey:true,key:'C'});
    vm.mind.currentNodes=[element('target')];
    vm.key({...event(),metaKey:true,shiftKey:true,key:'V'});
    assert.equal(vm.commits,1);
});
test('paste generates IDs on HTTP origins without crypto.randomUUID', () => {
    const {vm,event,element}=setup();vm.copyNodes(event());
    vm.mind.currentNodes=[element('target')];
    const descriptor=Object.getOwnPropertyDescriptor(globalThis,'crypto');
    const getRandomValues=globalThis.crypto.getRandomValues.bind(globalThis.crypto);
    Object.defineProperty(globalThis,'crypto',{value:{getRandomValues},configurable:true});
    try {
        vm.pasteNodes(event());
        assert.equal(vm.graph.nodes.length,6);
        assert.equal(new Set(vm.graph.nodes.map(n=>n.id)).size,6);
    } finally {Object.defineProperty(globalThis,'crypto',descriptor)}
});
