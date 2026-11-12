import {loadResource} from '../../static/utils/resources.js';
const clone = x => JSON.parse(JSON.stringify(x));
const uid = () => 'n_' + crypto.randomUUID().replaceAll('-', '').slice(0,16);
export default {
 props: {graph:Object, types:Array, resourcePath:String},
 emits:['save_request','type_save','load_error'],
 template:`<div class="kja-map" ref="root" tabindex="0" @keydown="key" @copy.capture="copyNodes" @paste.capture="pasteNodes">
 <div class="mm-toolbar">
 <button @click="add(false)" title="하위 노드 (Tab)">＋ 하위</button><button @click="add(true)" title="같은 수준 (Enter)">＋ 형제</button><button @click="removeNode">삭제</button>
 <button @click="undo(-1)" :disabled="cursor<=0" title="실행 취소">↶</button><button @click="undo(1)" :disabled="cursor>=history.length-1" title="다시 실행">↷</button>
 <select aria-label="맵 방향" v-model.number="direction" @change="layout"><option :value="1">오른쪽</option><option :value="0">왼쪽</option><option :value="2">양쪽</option><option :value="3">아래쪽</option></select>
 <button @click="expand(true)">모두 펼치기</button><button @click="expand(false)">접기</button>
 <span class="mm-spacer"></span><span>{{dirty?'● 저장 안 됨':'변경 없음'}}</span>
 <button @click="zoom(-.15)" title="축소">−</button><button @click="zoom(0)">{{percent}}%</button><button @click="zoom(.15)" title="확대">＋</button><button @click="fit" title="화면에 맞추기">맞춤</button><button @click="fullscreen" title="전체 화면">⛶</button>
 </div><div class="mm-body"><div ref="canvas" class="mm-canvas" aria-label="마인드맵 캔버스" @pointerdown.capture="focusCanvas"></div>
 <aside class="mm-inspector"><div class="mm-tabs"><button @click="panel='node'">노드</button><button @click="panel='relation'">관계</button><button @click="panel='type'">유형·스타일</button></div>
 <template v-if="panel==='node' && selected"><h3>노드 속성</h3><label>이름<input aria-label="노드 이름" v-model="form.label" maxlength="1000"></label><label>유형<select v-model="form.type"><option v-for="t in localTypes" :key="t.name">{{t.name}}</option><option v-if="!localTypes.some(t=>t.name===form.type)">{{form.type}}</option></select></label><label>설명<textarea v-model="form.description" rows="3"></textarea></label><label>파일 경로<input v-model="form.file"></label>
 <label><input type="checkbox" v-model="custom"> 노드 스타일 직접 지정</label><template v-if="custom"><div class="mm-colors"><label>배경<input type="color" v-model="style.background"></label><label>글자<input type="color" v-model="style.color"></label><label>테두리<input type="color" v-model="style.border_color"></label></div><label>글자 크기<input type="number" min="10" max="40" v-model.number="style.font_size"></label><label>모양<select v-model="style.shape"><option value="rounded">둥근 사각형</option><option value="rectangle">사각형</option><option value="pill">캡슐</option><option value="ellipse">타원</option></select></label><label>아이콘<input v-model="style.icon" maxlength="12"></label></template>
 <button class="mm-primary" @click="applyNode">노드 적용</button><button @click="resetStyle">유형 기본값으로</button></template>
 <template v-if="panel==='relation'"><h3>추가 관계</h3><p>선택한 노드에서 대상으로 연결합니다.</p><label>대상<select aria-label="관계 대상" v-model="relation.target"><option v-for="n in nodes.filter(n=>n.id!==selected)" :value="n.id">{{n.label}}</option></select></label><label>관계 유형<input v-model="relation.kind"></label><label>표시 이름<input v-model="relation.label"></label><label>선 색상<input type="color" v-model="relation.color"></label><label><input type="checkbox" v-model="relation.dashed"> 점선</label><label><input type="checkbox" v-model="relation.bidirectional"> 양방향</label><button @click="addRelation">{{relation.id?'관계 수정':'관계 추가'}}</button><button v-if="relation.id" @click="relation.id=null">새 관계</button><div v-for="e in relations" :key="e.id" class="mm-relation"><span @click="editRelation(e)" tabindex="0" @keydown.enter="editRelation(e)" style="cursor:pointer" title="관계 편집">{{nodeLabel(e.source)}} → {{nodeLabel(e.target)}} · {{e.label||e.kind}}</span><button @click="deleteRelation(e.id)" title="관계 삭제">×</button></div></template>
 <template v-if="panel==='type'"><h3>유형 기본 스타일</h3><select aria-label="편집할 유형" @change="editType($event.target.value)"><option value="">새 유형</option><option v-for="t in localTypes">{{t.name}}</option></select><label>유형 이름<input aria-label="유형 이름" v-model="typeForm.name" maxlength="60"></label><div class="mm-colors"><label>배경<input type="color" v-model="typeForm.style.background"></label><label>글자<input type="color" v-model="typeForm.style.color"></label><label>테두리<input type="color" v-model="typeForm.style.border_color"></label></div><label>글자 크기<input type="number" min="10" max="40" v-model.number="typeForm.style.font_size"></label><label>모양<select v-model="typeForm.style.shape"><option value="rounded">둥근 사각형</option><option value="rectangle">사각형</option><option value="pill">캡슐</option><option value="ellipse">타원</option></select></label><label>아이콘<input v-model="typeForm.style.icon" maxlength="12"></label><button class="mm-primary" @click="$emit('type_save',cloneValue(typeForm))">유형 저장</button><p>같은 이름으로 저장하면 기본 스타일을 변경합니다. 개별 노드의 직접 지정 값이 우선합니다.</p></template>
 <p class="mm-hint">빈 공간 드래그: 이동 · 노드 드래그: 계층 변경 · 더블클릭: 이름 수정 · Ctrl+클릭: 다중 선택 · Ctrl+A: 전체 선택 · Ctrl+C/V: 노드 복사/붙여넣기 · Ctrl+S: 저장</p><p role="status">{{message}}</p></aside></div></div>`,
 data(){return {ready:false,dirty:false,selected:null,form:{},custom:false,style:{},localTypes:clone(this.types),panel:'node',direction:1,percent:100,history:[],cursor:-1,nodes:[],relations:[],message:'',typeForm:{name:'',style:{background:'#222b24',color:'#eee9de',border_color:'#b89a60',font_size:15,shape:'rounded',icon:'◇'}},relation:{target:'',kind:'참조',label:'',color:'#b89a60',dashed:true,bidirectional:false}}},
 methods:{
 cloneValue:clone,
 focusCanvas(e){if(!this.editing(e))this.$refs.root.focus({preventScroll:true})},
 editing(e){return !!e.target.closest('input,textarea,select,[contenteditable]:not([contenteditable="false"])')},
 copyNodes(e){
  if(!this.ready||this.editing(e)||!e.clipboardData)return;
  const g=this.getSnapshot().graph;
  const chosen=new Set((this.mind.currentNodes||[]).map(el=>el.nodeObj.id));
  if(!chosen.size)return;
  // Include descendants once, even when both parent and child are selected.
  const included=new Set(chosen);
  let count;
  do{count=included.size;for(const edge of g.edges)if(edge.tree&&included.has(edge.source))included.add(edge.target)}while(count!==included.size);
  const nodes=g.nodes.filter(n=>included.has(n.id));
  const edges=g.edges.filter(edge=>included.has(edge.source)&&included.has(edge.target));
  const children=new Set(edges.filter(edge=>edge.tree).map(edge=>edge.target));
  const payload={format:'kja-mindmap-clipboard-v1',roots:nodes.filter(n=>!children.has(n.id)).map(n=>n.id),nodes,edges};
  e.clipboardData.setData('text/plain',JSON.stringify(payload));
  e.preventDefault();e.stopPropagation();
  this.message=`${nodes.length}개 노드를 복사했습니다. 대상 노드를 선택하고 Ctrl+V로 붙여넣으세요.`;
 },
 pasteNodes(e){
  if(!this.ready||this.editing(e)||!e.clipboardData)return;
  const text=e.clipboardData.getData('text/plain');
  if(text.length>2*1024*1024){this.message='붙여넣기 데이터는 2MB 이하여야 합니다.';return}
  let data;try{data=JSON.parse(text)}catch{return}
  if(data?.format!=='kja-mindmap-clipboard-v1')return;
  e.preventDefault();e.stopPropagation();
  const g=this.getSnapshot().graph;
  const parent=this.mind.currentNodes?.at(-1)?.nodeObj.id;
  if(!g.nodes.some(n=>n.id===parent)){this.message='붙여넣을 대상 노드를 먼저 선택하세요.';return}
  try{
   if(!Array.isArray(data.nodes)||!data.nodes.length||!Array.isArray(data.edges)||!Array.isArray(data.roots)||!data.roots.length)throw Error();
   if(g.nodes.length+data.nodes.length>2000||g.edges.length+data.edges.length+data.roots.length>5000){this.message='최대 2,000노드·5,000관계까지 붙여넣을 수 있습니다.';return}
   const ids=new Map(data.nodes.map(n=>[n.id,uid()]));
   if(ids.size!==data.nodes.length||data.nodes.some(n=>typeof n.id!=='string'||typeof n.label!=='string'||n.label.length>1000))throw Error();
   const parents=new Map();
   for(const edge of data.edges){if(!ids.has(edge.source)||!ids.has(edge.target))throw Error();if(edge.tree){if(parents.has(edge.target))throw Error();parents.set(edge.target,edge.source)}}
   const roots=data.nodes.filter(n=>!parents.has(n.id)).map(n=>n.id);
   if(roots.length!==data.roots.length||new Set(data.roots).size!==roots.length||roots.some(id=>!data.roots.includes(id)))throw Error();
   const targetParents=new Map(g.edges.filter(edge=>edge.tree).map(edge=>[edge.target,edge.source]));
   let targetDepth=0;for(let id=parent;targetParents.has(id);id=targetParents.get(id))targetDepth++;
   for(const n of data.nodes){const visited=new Set();let id=n.id,depth=targetDepth+1;while(parents.has(id)){if(visited.has(id))throw Error();visited.add(id);id=parents.get(id);depth++}if(depth>100){this.message='계층 깊이는 100 이하여야 합니다.';return}}
   g.nodes.push(...data.nodes.map(n=>({...clone(n),id:ids.get(n.id)})));
   g.edges.push(...data.edges.map(edge=>({...clone(edge),id:uid(),source:ids.get(edge.source),target:ids.get(edge.target)})));
   for(const root of roots)g.edges.push({id:uid(),source:parent,target:ids.get(root),label:'',kind:'계층',tree:true,color:'#b89a60',dashed:false,bidirectional:false});
   g.nodes.find(n=>n.id===parent).expanded=true;
   this.commit(g);
   this.mind.unselectNodes(this.mind.currentNodes);
   this.mind.selectNodes(roots.map(id=>this.mind.findEle(ids.get(id))));
   this.select(ids.get(roots[0]));
   this.message=`${data.nodes.length}개 노드를 붙여넣었습니다. Ctrl+Z로 취소할 수 있습니다.`;
  }catch{this.message='올바른 마인드맵 노드 데이터가 아닙니다.'}
 },
 effective(n){const base=this.localTypes.find(t=>t.name===n.type)?.style||this.localTypes.find(t=>t.name==='서비스')?.style||{background:'#222b24',color:'#eee9de',border_color:'#b89a60',font_size:15,shape:'rounded',icon:''};return {...base,...Object.fromEntries(Object.entries(n.overrides||{}).filter(([k,v])=>v!==null))}},
 native(g){const by={};for(const n of g.nodes){const s=this.effective(n);by[n.id]={id:n.id,topic:n.label,expanded:n.expanded,metadata:clone(n),style:{background:s.background,color:s.color,fontSize:s.font_size,border:'1px solid '+s.border_color},icons:s.icon?[s.icon]:[],children:[]}}for(const e of g.edges.filter(e=>e.tree))by[e.source].children.push(by[e.target]);return {nodeData:by[g.root],direction:g.view.direction,arrows:g.edges.filter(e=>!e.tree).map(e=>({id:e.id,from:e.source,to:e.target,label:e.label,delta1:{x:50,y:0},delta2:{x:-50,y:0},bidirectional:e.bidirectional,style:{stroke:e.color,strokeWidth:2,strokeDasharray:e.dashed?'6 4':'',labelColor:e.color},metadata:clone(e)}))}},
 getSnapshot(){if(!this.mind||!this.ready)return {graph:null,dirty:false};const d=this.mind.getData(),nodes=[],edges=[];const walk=(n,parent)=>{const original=n.metadata||{};nodes.push({...original,id:n.id,label:n.topic,type:original.type||'서비스',description:original.description||'',file:original.file||'',overrides:original.overrides||{},expanded:n.expanded!==false});if(parent){const old=this.current.edges.find(e=>e.tree&&e.source===parent&&e.target===n.id);edges.push(old?clone(old):{id:uid(),source:parent,target:n.id,label:'',kind:'계층',tree:true,color:'#b89a60',dashed:false,bidirectional:false})}for(const c of n.children||[])walk(c,n.id)};walk(d.nodeData,null);for(const a of d.arrows||[])edges.push({...a.metadata,id:a.id,source:a.from,target:a.to,label:a.label||'',kind:a.metadata?.kind||'참조',tree:false,color:a.style?.stroke||'#b89a60',dashed:!!a.style?.strokeDasharray,bidirectional:!!a.bidirectional});return {graph:{version:1,root:d.nodeData.id,nodes,edges,view:{direction:this.mind.direction,scale:this.mind.scaleVal,scroll_left:Math.max(0,this.mind.container.scrollLeft),scroll_top:Math.max(0,this.mind.container.scrollTop),pan_x:parseFloat(this.mind.map.style.transform.match(/translate3d\(([-.0-9]+)/)?.[1]||0),pan_y:parseFloat(this.mind.map.style.transform.match(/translate3d\([-.0-9]+px,\s*([-.0-9]+)/)?.[1]||0)}},dirty:this.dirty}},
 capture(){if(this.suppress||!this.ready)return;this.current=this.getSnapshot().graph;this.nodes=clone(this.current.nodes);this.relations=clone(this.current.edges.filter(e=>!e.tree));this.history=this.history.slice(0,this.cursor+1);this.history.push(clone(this.current));if(this.history.length>60)this.history.shift();this.cursor=this.history.length-1;this.dirty=true;this.decorate()},
 decorate(){requestAnimationFrame(()=>{for(const n of this.current.nodes){const el=this.mind.findEle(n.id);if(el){const shape=this.effective(n).shape;el.style.borderRadius=shape==='ellipse'?'50%':shape==='pill'?'999px':shape==='rectangle'?'0':'10px'}}})},
 select(id){this.selected=id;const n=this.getSnapshot().graph.nodes.find(n=>n.id===id);if(!n)return;this.form=clone(n);this.custom=Object.values(n.overrides||{}).some(v=>v!==null);this.style=this.effective(n)},
 async show(g,reset=false){this.suppress=true;this.current=clone(g);this.direction=g.view.direction;this.mind.refresh(this.native(g));[()=>this.mind.initLeft(),()=>this.mind.initRight(),()=>this.mind.initSide(),()=>this.mind.initDown()][g.view.direction]();this.mind.scale(g.view.scale);this.mind.container.scrollLeft=g.view.scroll_left;this.mind.container.scrollTop=g.view.scroll_top;this.nodes=clone(g.nodes);this.relations=clone(g.edges.filter(e=>!e.tree));this.select(g.root);this.mind.selectNode(this.mind.findEle(g.root));if(g.view.pan_x||g.view.pan_y)this.mind.map.style.transform=`translate3d(${g.view.pan_x}px, ${g.view.pan_y}px, 0) scale(${g.view.scale})`;if(reset&&!g.view.pan_x&&!g.view.pan_y&&this.$refs.canvas.clientWidth)requestAnimationFrame(()=>this.fit());this.percent=Math.round(this.mind.scaleVal*100);this.decorate();this.suppress=false;if(reset){this.history=[clone(g)];this.cursor=0;this.dirty=false}},
 loadGraphFromProps(){if(this.ready)this.show(this.graph,true)},
 markSaved(){this.dirty=false},
 updateTypes(types){this.localTypes=clone(types);const g=this.getSnapshot().graph;this.show(g);},
 commit(g){this.show(g);this.capture()},
 add(sibling){const g=this.getSnapshot().graph;const parent=sibling?g.edges.find(e=>e.tree&&e.target===this.selected)?.source:this.selected;if(!parent){this.message='루트에는 형제 노드를 추가할 수 없습니다.';return}const id=uid();g.nodes.push({id,label:'새 노드',type:'서비스',description:'',file:'',overrides:{},expanded:true});g.nodes.find(n=>n.id===parent).expanded=true;g.edges.push({id:uid(),source:parent,target:id,label:'',kind:'계층',tree:true,color:'#b89a60',dashed:false,bidirectional:false});this.commit(g);this.mind.selectNode(this.mind.findEle(id));this.select(id)},
 removeNode(){const g=this.getSnapshot().graph;if(this.selected===g.root){this.message='루트는 삭제할 수 없습니다.';return}const gone=new Set([this.selected]);let size;do{size=gone.size;g.edges.filter(e=>e.tree&&gone.has(e.source)).forEach(e=>gone.add(e.target))}while(size!==gone.size);g.nodes=g.nodes.filter(n=>!gone.has(n.id));g.edges=g.edges.filter(e=>!gone.has(e.source)&&!gone.has(e.target));this.commit(g)},
 applyNode(){if(!this.form.label?.trim())return;const g=this.getSnapshot().graph;const n=g.nodes.find(n=>n.id===this.selected);Object.assign(n,this.form,{overrides:this.custom?clone(this.style):{}});this.commit(g);this.select(n.id);this.mind.selectNode(this.mind.findEle(n.id))},
 resetStyle(){this.custom=false;this.applyNode()},
 addRelation(){if(!this.relation.target||!this.selected)return;const g=this.getSnapshot().graph;const old=this.relation.id;g.edges=g.edges.filter(e=>e.id!==old);g.edges.push({...clone(this.relation),id:old||uid(),source:this.selected,tree:false});this.commit(g);this.relation.id=null},
 editRelation(edge){this.select(edge.source);this.relation=clone(edge)},
 deleteRelation(id){const g=this.getSnapshot().graph;g.edges=g.edges.filter(e=>e.id!==id);this.commit(g)},
 nodeLabel(id){return this.nodes.find(n=>n.id===id)?.label||id},
 editType(name){const t=this.localTypes.find(t=>t.name===name);this.typeForm=t?clone(t):{name:'',style:{background:'#222b24',color:'#eee9de',border_color:'#b89a60',font_size:15,shape:'rounded',icon:'◇'}}},
 undo(delta){const next=this.cursor+delta;if(next<0||next>=this.history.length)return;this.cursor=next;this.show(clone(this.history[next]));this.dirty=true},
 layout(){const g=this.getSnapshot().graph;g.view.direction=this.direction;this.commit(g);this.fit()},
 expand(open){const g=this.getSnapshot().graph;g.nodes.forEach(n=>n.expanded=n.id===g.root?true:open);this.commit(g)},
 zoom(delta){this.mind.scale(delta===0?1:Math.max(.1,Math.min(8,this.mind.scaleVal+delta)));this.percent=Math.round(this.mind.scaleVal*100)},
 fit(){this.mind.scaleFit();this.percent=Math.round(this.mind.scaleVal*100)},
 async fullscreen(){try{if(document.fullscreenElement===this.$refs.root)await document.exitFullscreen();else await this.$refs.root.requestFullscreen()}catch(e){this.message='브라우저에서 전체 화면을 허용해 주세요.'}},
 key(e){if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();this.$emit('save_request');return}if(this.editing(e)||!this.ready||e.isComposing)return;if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='a'){e.preventDefault();this.mind.selectNodes(this.nodes.map(n=>this.mind.findEle(n.id)));return}if(e.key==='Tab'){e.preventDefault();this.add(false)}else if(e.key==='Enter'){e.preventDefault();this.add(true)}else if(e.key==='Delete'){e.preventDefault();this.removeNode()}else if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();this.undo(e.shiftKey?1:-1)}else if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='y'){e.preventDefault();this.undo(1)}}
 },
 async mounted(){try{const path=(window.path_prefix||'')+this.resourcePath;await loadResource(path+'/MindElixir.css');const {default:MindElixir}=await import(path+'/MindElixir.js');if(this.disposed)return;this.mind=new MindElixir({el:this.$refs.canvas,direction:this.graph.view.direction,editable:true,contextMenu:true,toolBar:false,keypress:false,allowUndo:false,mouseSelectionButton:2,overflowHidden:false,alignment:'nodes',scaleMin:.1,scaleMax:8,newTopicName:'새 노드'});await this.mind.init(this.native(this.graph));this.ready=true;await this.show(this.graph,true);this.mind.bus.addListener('operation',()=>{this.capture();if(this.selected)this.select(this.selected)});this.mind.bus.addListener('selectNodes',nodes=>{if(nodes?.[0])this.select(nodes[0].id)});this.observer=new ResizeObserver(()=>{if(this.$refs.canvas.clientWidth>0&&!this.visibleOnce){this.visibleOnce=true;if(!this.graph.view.pan_x&&!this.graph.view.pan_y)this.fit()}});this.observer.observe(this.$refs.canvas);this.onWheel=()=>{this.percent=Math.round(this.mind.scaleVal*100)};this.$refs.canvas.addEventListener('wheel',this.onWheel);}catch(e){console.error(e);this.message=String(e);this.$emit('load_error',String(e))}},
 beforeUnmount(){this.disposed=true;this.observer?.disconnect();this.mind?.destroy?.()}
};
