import {loadResource} from '../../static/utils/resources.js';
const clone = x => JSON.parse(JSON.stringify(x));
// getRandomValues also works on an intranet HTTP origin; randomUUID requires HTTPS.
const uid = () => 'n_' + Array.from(crypto.getRandomValues(new Uint8Array(8)), b => b.toString(16).padStart(2,'0')).join('');
// Shared by editor instances and retained when a different map is loaded.
let nodeClipboardText = '';
export default {
 props: {graph:Object, types:Array, resourcePath:String},
 emits:['save_request','type_save','load_error'],
 template:`<div class="kja-map" ref="root" tabindex="0" @keydown.capture="key" @copy.capture="copyNodes" @paste.capture="pasteNodes">
 <div class="mm-toolbar">
 <button @click="add(false)" title="하위 노드 (Tab)">＋ 하위</button><button @click="add(true)" title="같은 수준 (Enter)">＋ 형제</button><button @click="removeNode">삭제</button><button @click="createSummary" title="선택한 노드 묶음 요약">요약 추가</button>
 <button @click="undo(-1)" :disabled="cursor<=0" title="실행 취소">↶</button><button @click="undo(1)" :disabled="cursor>=history.length-1" title="다시 실행">↷</button>
 <select aria-label="맵 방향" v-model.number="direction" @change="layout"><option :value="1">오른쪽</option><option :value="0">왼쪽</option><option :value="2">양쪽</option><option :value="3">아래쪽</option></select>
 <button @click="expand(true)">모두 펼치기</button><button @click="expand(false)">접기</button>
 <span class="mm-spacer"></span><span>{{dirty?'● 저장 안 됨':'변경 없음'}}</span>
 <button @click="zoom(-.15)" title="축소">−</button><button @click="zoom(0)">{{percent}}%</button><button @click="zoom(.15)" title="확대">＋</button><button @click="fit" title="화면에 맞추기">맞춤</button><button @click="fullscreen" title="전체 화면">⛶</button>
 </div><div class="mm-searchbar">
 <div class="mm-search-input"><input ref="nodeSearch" type="search" aria-label="노드 검색" placeholder="이름 · 유형 · 설명 · 파일 경로 검색" v-model="searchQuery" @input="searchIndex=-1;searchOpen=true" @keydown.enter.prevent="stepSearch($event.shiftKey?-1:1)" @keydown.escape.prevent="searchOpen=false" autocomplete="off"><button v-if="searchQuery" type="button" class="mm-search-clear" aria-label="검색어 지우기" title="검색어 지우기" @click="clearSearch">×</button></div>
 <span role="status" class="mm-search-count">{{searchQuery.trim()?searchMatches.length+'개'+(searchIndex>=0?' · '+(searchIndex+1)+'/'+searchMatches.length:''):''}}</span>
 <button @click="stepSearch(-1)" :disabled="!searchMatches.length" title="이전 검색 결과" aria-label="이전 검색 결과">↑</button><button @click="stepSearch(1)" :disabled="!searchMatches.length" title="다음 검색 결과" aria-label="다음 검색 결과">↓</button><button @click="searchOpen=!searchOpen" :disabled="!searchQuery.trim()" :aria-expanded="searchOpen">검색 결과</button>
 <button @click="highlightRelations=!highlightRelations;paintRelations()" :aria-pressed="highlightRelations" class="mm-highlight-toggle" title="선택한 노드에 직접 연결된 계층과 추가 관계를 강조합니다">연결 관계 강조</button><span v-if="highlightRelations" class="mm-search-count">{{selected?relationContext(current,selected).edges.length+'개 직접 연결 · 계층 포함':'노드를 선택하세요'}}</span>
 <div v-if="searchOpen && searchQuery.trim()" class="mm-search-results" aria-label="노드 검색 결과"><p v-if="!searchMatches.length">검색 결과가 없습니다.</p><button v-for="(n,i) in searchMatches" :key="n.id" @click="jumpToNode(n.id,i)"><strong>{{n.label}}</strong><span>{{n.type}} · {{n.file||n.description||'추가 정보 없음'}}</span></button></div>
 </div><div class="mm-body"><div ref="canvas" class="mm-canvas" aria-label="마인드맵 캔버스" @pointerdown.capture="focusCanvas" @pointerup="focusCanvas"></div>
 <div class="mm-inspector-rail"><button type="button" @click="toggleInspector" :aria-label="inspectorCollapsed?'오른쪽 패널 펼치기':'오른쪽 패널 접기'" :title="inspectorCollapsed?'오른쪽 패널 펼치기':'오른쪽 패널 접기'" :aria-expanded="!inspectorCollapsed" :aria-controls="panelId">{{inspectorCollapsed?'‹':'›'}}</button></div>
 <aside v-show="!inspectorCollapsed" class="mm-inspector" :id="panelId" aria-label="마인드맵 속성 패널"><div class="mm-tabs" role="tablist" aria-label="속성 패널 탭" ref="inspectorTabs" @keydown="tabKey">
 <button type="button" role="tab" class="mm-tab-node" :id="panelId+'-node'" :aria-controls="panelId+'-content'" :aria-selected="panel==='node'" :tabindex="panel==='node'?0:-1" @click="panel='node'">노드</button>
 <button type="button" role="tab" class="mm-tab-relation" :id="panelId+'-relation'" :aria-controls="panelId+'-content'" :aria-selected="panel==='relation'" :tabindex="panel==='relation'?0:-1" @click="panel='relation'">관계</button>
 <button type="button" role="tab" class="mm-tab-summary" :id="panelId+'-summary'" :aria-controls="panelId+'-content'" :aria-selected="panel==='summary'" :tabindex="panel==='summary'?0:-1" @click="panel='summary'">요약</button>
 <button type="button" role="tab" class="mm-tab-style" :id="panelId+'-type'" :aria-controls="panelId+'-content'" :aria-selected="panel==='type'" :tabindex="panel==='type'?0:-1" @click="panel='type'">스타일</button>
 </div><div role="tabpanel" :id="panelId+'-content'" :aria-labelledby="panelId+'-'+panel">
 <template v-if="panel==='node' && selected"><h3>노드 속성</h3><label>이름<input aria-label="노드 이름" v-model="form.label" maxlength="1000"></label><label>유형<select v-model="form.type"><option v-for="t in localTypes" :key="t.name">{{t.name}}</option><option v-if="!localTypes.some(t=>t.name===form.type)">{{form.type}}</option></select></label><label>설명<textarea v-model="form.description" rows="3"></textarea></label><label>파일 경로<input v-model="form.file"></label>
 <label><input type="checkbox" v-model="custom"> 노드 스타일 직접 지정</label><template v-if="custom"><div class="mm-colors"><label>배경<input type="color" v-model="style.background"></label><label>글자<input type="color" v-model="style.color"></label><label>테두리<input type="color" v-model="style.border_color"></label></div><label>글자 크기<input type="number" min="10" max="40" v-model.number="style.font_size"></label><label>모양<select aria-label="노드 모양" v-model="style.shape"><option value="rounded">둥근 사각형</option><option value="rectangle">사각형</option><option value="pill">캡슐</option><option value="ellipse">타원</option><option value="diamond">마름모</option><option value="cylinder">원통</option><option value="hexagon">육각형</option><option value="document">문서형</option></select></label><label>아이콘<input v-model="style.icon" maxlength="12"></label></template>
 <button class="mm-primary" @click="applyNode">노드 적용</button><button @click="resetStyle">유형 기본값으로</button></template>
 <template v-if="panel==='relation'"><h3>추가 관계</h3><p>선택한 노드에서 대상으로 연결합니다.</p><label>대상<select aria-label="관계 대상" v-model="relation.target"><option v-for="n in nodes.filter(n=>n.id!==selected)" :value="n.id">{{n.label}}</option></select></label><label>관계 유형<input v-model="relation.kind"></label><label>표시 이름<input v-model="relation.label"></label><label>선 색상<input type="color" v-model="relation.color"></label><label><input type="checkbox" v-model="relation.dashed"> 점선</label><label><input type="checkbox" v-model="relation.bidirectional"> 양방향</label><button @click="addRelation">{{relation.id?'관계 수정':'관계 추가'}}</button><button v-if="relation.id" @click="relation.id=null">새 관계</button><div v-for="e in relations" :key="e.id" class="mm-relation"><span @click="editRelation(e)" tabindex="0" @keydown.enter="editRelation(e)" style="cursor:pointer" title="관계 편집">{{nodeLabel(e.source)}} → {{nodeLabel(e.target)}} · {{e.label||e.kind}}</span><button @click="deleteRelation(e.id)" title="관계 삭제">×</button></div></template>
 <template v-if="panel==='summary'"><h3>요약 (Summary)</h3><p>요약 글자나 괄호를 클릭해 선택하고 더블클릭으로 이름을 바꿀 수 있습니다.</p><div v-for="s in summaries" :key="s.id"><button @click="chooseSummary(s.id)" :aria-pressed="summaryId===s.id">{{s.label}}</button></div><template v-if="summaryId"><label>요약 이름<input ref="summaryName" aria-label="요약 이름" v-model="summaryForm.label" maxlength="1000" @keydown.enter.prevent="applySummary"></label><div class="mm-colors"><label>선 색상<input type="color" v-model="summaryForm.style.stroke"></label><label>글자 색상<input type="color" v-model="summaryForm.style.labelColor"></label></div><button class="mm-primary" @click="applySummary">요약 적용</button><button @click="removeSummary">요약 삭제</button></template><p v-if="!summaries.length">노드를 선택한 뒤 상단 ‘요약 추가’를 누르세요.</p></template>
 <template v-if="panel==='type'"><h3>유형 기본 스타일</h3><select aria-label="편집할 유형" @change="editType($event.target.value)"><option value="">새 유형</option><option v-for="t in localTypes">{{t.name}}</option></select><label>유형 이름<input aria-label="유형 이름" v-model="typeForm.name" maxlength="60"></label><div class="mm-colors"><label>배경<input type="color" v-model="typeForm.style.background"></label><label>글자<input type="color" v-model="typeForm.style.color"></label><label>테두리<input type="color" v-model="typeForm.style.border_color"></label></div><label>글자 크기<input type="number" min="10" max="40" v-model.number="typeForm.style.font_size"></label><label>모양<select aria-label="유형 모양" v-model="typeForm.style.shape"><option value="rounded">둥근 사각형</option><option value="rectangle">사각형</option><option value="pill">캡슐</option><option value="ellipse">타원</option><option value="diamond">마름모</option><option value="cylinder">원통</option><option value="hexagon">육각형</option><option value="document">문서형</option></select></label><label>아이콘<input v-model="typeForm.style.icon" maxlength="12"></label><button class="mm-primary" @click="$emit('type_save',cloneValue(typeForm))">유형 저장</button><p>같은 이름으로 저장하면 기본 스타일을 변경합니다. 개별 노드의 직접 지정 값이 우선합니다.</p></template>
 <p class="mm-hint">빈 공간 드래그: 이동 · 노드 드래그: 계층 변경 · 더블클릭: 이름 수정 · Ctrl+클릭: 다중 선택 · Ctrl+A: 전체 선택 · Ctrl+Shift+C/V 또는 Ctrl+C/V: 노드 복사/붙여넣기 · 노드 우클릭: 복사/붙여넣기 · Ctrl+S: 저장</p><p role="status">{{message}}</p></div></aside></div></div>`,
 data(){return {ready:false,dirty:false,selected:null,searchQuery:'',searchIndex:-1,searchOpen:false,highlightRelations:false,summaryId:null,summaryForm:{},summaries:[],form:{},custom:false,style:{},localTypes:clone(this.types),panel:'node',inspectorCollapsed:false,panelId:uid(),direction:1,percent:100,history:[],cursor:-1,nodes:[],relations:[],message:'',typeForm:{name:'',style:{background:'#222b24',color:'#eee9de',border_color:'#b89a60',font_size:15,shape:'rounded',icon:'◇'}},relation:{target:'',kind:'참조',label:'',color:'#b89a60',dashed:true,bidirectional:false}}},
 computed:{searchMatches(){return this.matchNodes(this.nodes,this.searchQuery)}},
 methods:{
 async toggleInspector(){
  const before=this.mind?.container.getBoundingClientRect();this.inspectorCollapsed=!this.inspectorCollapsed;
  await this.$nextTick();if(!this.ready||!before)return;
  const after=this.mind.container.getBoundingClientRect();this.mind.move((after.width-before.width)/2,0);this.paintRelations();
 },
 tabKey(e){
  const order=['node','relation','summary','type'];let index=order.indexOf(this.panel);
  if(e.key==='ArrowRight')index=(index+1)%order.length;
  else if(e.key==='ArrowLeft')index=(index+order.length-1)%order.length;
  else if(e.key==='Home')index=0;else if(e.key==='End')index=order.length-1;else return;
  e.preventDefault();this.panel=order[index];this.$nextTick(()=>this.$refs.inspectorTabs.querySelector('[aria-selected="true"]').focus());
 },
 matchNodes(nodes,query){
  const words=String(query||'').normalize('NFKC').toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  if(!words.length)return [];
  return nodes.filter(n=>{const text=[n.label,n.type,n.description,n.file].filter(Boolean).join(' ').normalize('NFKC').toLocaleLowerCase();return words.every(word=>text.includes(word))});
 },
 relationContext(graph,id){
  const edges=(graph?.edges||[]).filter(e=>e.source===id||e.target===id);
  return {ids:new Set([id,...edges.flatMap(e=>[e.source,e.target])]),edges};
 },
 clearSearch(){this.searchQuery='';this.searchIndex=-1;this.searchOpen=false;this.$nextTick(()=>this.$refs.nodeSearch.focus())},
 async stepSearch(delta){
  const hits=this.searchMatches;if(!hits.length)return;
  const index=this.searchIndex<0?(delta<0?hits.length-1:0):(this.searchIndex+delta+hits.length)%hits.length;
  await this.jumpToNode(hits[index].id,index);
 },
 async jumpToNode(id,index=-1){
  if(!this.ready)return;
  const graph=this.getSnapshot().graph;if(!graph.nodes.some(n=>n.id===id))return;
  const parents=new Map(graph.edges.filter(e=>e.tree).map(e=>[e.target,e.source]));
  const byId=new Map(graph.nodes.map(n=>[n.id,n]));let changed=false;
  for(let parent=parents.get(id);parent;parent=parents.get(parent)){const n=byId.get(parent);if(n.expanded===false){n.expanded=true;changed=true}}
  if(changed){await this.show(graph);this.capture()}
  await this.$nextTick();
  const el=this.mind.findEle(id);if(!el)return;
  this.mind.clearSelection();this.mind.selectNodes([el]);this.select(id);this.panel='node';
  const box=el.getBoundingClientRect(),canvas=this.mind.container.getBoundingClientRect();
  this.mind.move(canvas.left+canvas.width/2-box.left-box.width/2,canvas.top+canvas.height/2-box.top-box.height/2);
  this.searchIndex=index;this.searchOpen=false;this.paintRelations();
 },
 visibleNode(id){return this.mind.nodes.querySelector('[data-nodeid="me'+id+'"]')},
 paintRelations(){
  if(!this.ready||!this.mind?.nodes)return;
  const active=!!(this.highlightRelations&&this.selected),ctx=this.relationContext(this.current,this.selected);
  this.$refs.canvas.classList.toggle('mm-relation-focus',active);
  for(const el of this.mind.nodes.querySelectorAll('.me-tpc')){
   const id=el.nodeObj.id;el.classList.toggle('mm-muted',active&&!ctx.ids.has(id));el.classList.toggle('mm-related',active&&ctx.ids.has(id));el.classList.toggle('mm-focus-node',active&&id===this.selected);
  }
  const arrowIds=new Map();
  for(const el of this.mind.arrowSvg.querySelectorAll('[data-linkid]')){
   const related=ctx.edges.some(e=>e.id===el.dataset.linkid);arrowIds.set(el.id,related);
   el.classList.toggle('mm-muted',active&&!related);el.classList.toggle('mm-related-edge',active&&related);
  }
  for(const el of this.mind.labelContainer.querySelectorAll('.svg-label[data-type="arrow"]'))el.classList.toggle('mm-muted',active&&!arrowIds.get(el.dataset.svgId));
  this.mind.nodes.querySelector('.mm-relation-overlay')?.remove();if(!active)return;
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.classList.add('mm-relation-overlay');
  const origin=this.mind.nodes.getBoundingClientRect(),scale=this.mind.scaleVal;
  for(const edge of ctx.edges.filter(e=>e.tree)){
   const from=this.visibleNode(edge.source),to=this.visibleNode(edge.target);if(!from||!to)continue;
   const a=from.getBoundingClientRect(),b=to.getBoundingClientRect();
   let x1=a.left+a.width/2,y1=a.top+a.height/2,x2=b.left+b.width/2,y2=b.top+b.height/2;
   if(Math.abs(x2-x1)>Math.abs(y2-y1)){const sign=Math.sign(x2-x1);x1+=sign*a.width/2;x2-=sign*b.width/2}else{const sign=Math.sign(y2-y1);y1+=sign*a.height/2;y2-=sign*b.height/2}
   const line=document.createElementNS(ns,'path');line.setAttribute('d',`M ${(x1-origin.left)/scale} ${(y1-origin.top)/scale} L ${(x2-origin.left)/scale} ${(y2-origin.top)/scale}`);svg.appendChild(line);
  }
  this.mind.nodes.appendChild(svg);
 },
 cloneValue:clone,
 focusCanvas(e){if(!this.editing(e))this.$refs.root.focus({preventScroll:true})},
 editing(e){return !!e.target.closest('input,textarea,select,[contenteditable]:not([contenteditable="false"])')},
 contextMenuOptions(){return {extend:[
  {name:'복사',key:'Ctrl+Shift+C',onclick:()=>this.copySelection()},
  {name:'붙여넣기',key:'Ctrl+Shift+V',onclick:()=>this.pasteSelection()}
 ]}},
 closeClipboardMenu(){
  const menu=this.$refs.canvas.querySelector('.context-menu');
  if(menu)menu.hidden=true;
  this.$refs.root.focus({preventScroll:true});
 },
 selectionText(){
  if(!this.ready)return '';
  const g=this.getSnapshot().graph;
  const chosen=new Set((this.mind.currentNodes||[]).map(el=>el.nodeObj.id));
  if(!chosen.size){this.message='복사할 노드를 먼저 선택하세요.';return ''}
  // Include descendants once, even when both parent and child are selected.
  const included=new Set(chosen);
  let count;
  do{count=included.size;for(const edge of g.edges)if(edge.tree&&included.has(edge.source))included.add(edge.target)}while(count!==included.size);
  const nodes=g.nodes.filter(n=>included.has(n.id));
  const edges=g.edges.filter(edge=>included.has(edge.source)&&included.has(edge.target));
  const children=new Set(edges.filter(edge=>edge.tree).map(edge=>edge.target));
  const payload={format:'kja-mindmap-clipboard-v1',roots:nodes.filter(n=>!children.has(n.id)).map(n=>n.id),nodes,edges};
  return JSON.stringify(payload);
 },
 rememberCopy(text){
  nodeClipboardText=text;
  this.message=`${JSON.parse(text).nodes.length}개 노드를 복사했습니다. 대상 노드에서 Ctrl+Shift+V 또는 우클릭 → 붙여넣기를 사용하세요.`;
 },
 copySelection(){
  const text=this.selectionText();
  if(!text)return;
  this.rememberCopy(text);
  this.closeClipboardMenu();
  // Internal copy is synchronous, even when Clipboard API permission is denied.
  try{globalThis.navigator?.clipboard?.writeText(text)?.catch(()=>{})}catch{}
 },
 async pasteSelection(){
  if(!this.ready)return;
  const parent=this.mind.currentNodes?.at(-1)?.nodeObj.id;
  this.closeClipboardMenu();
  if(!parent){this.message='붙여넣을 대상 노드를 먼저 선택하세요.';return}
  if(nodeClipboardText){this.pasteText(nodeClipboardText,parent);return}
  try{
   const text=await globalThis.navigator?.clipboard?.readText();
   if(!this.disposed&&text&&this.pasteText(text,parent))return;
  }catch{}
  if(!this.disposed)this.message='먼저 노드를 복사하세요. 다른 탭에서 복사한 경우 Ctrl+V를 사용하세요.';
 },
 copyNodes(e){
  if(!this.ready||this.editing(e)||!e.clipboardData)return;
  const text=this.selectionText();
  if(!text)return;
  e.clipboardData.setData('text/plain',text);
  this.rememberCopy(text);
  e.preventDefault();e.stopPropagation();
 },
 pasteNodes(e){
  if(!this.ready||this.editing(e)||!e.clipboardData)return;
  const text=e.clipboardData.getData('text/plain');
  if(this.pasteText(text)){e.preventDefault();e.stopPropagation()}
 },
 pasteText(text,parent=this.mind.currentNodes?.at(-1)?.nodeObj.id){
  if(text.length>2*1024*1024){this.message='붙여넣기 데이터는 2MB 이하여야 합니다.';return}
  let data;try{data=JSON.parse(text)}catch{return}
  if(data?.format!=='kja-mindmap-clipboard-v1')return;
  const g=this.getSnapshot().graph;
  if(!g.nodes.some(n=>n.id===parent)){this.message='붙여넣을 대상 노드를 먼저 선택하세요.';return true}
  try{
   if(!Array.isArray(data.nodes)||!data.nodes.length||!Array.isArray(data.edges)||!Array.isArray(data.roots)||!data.roots.length)throw Error();
   if(g.nodes.length+data.nodes.length>2000||g.edges.length+data.edges.length+data.roots.length>5000){this.message='최대 2,000노드·5,000관계까지 붙여넣을 수 있습니다.';return true}
   const ids=new Map(data.nodes.map(n=>[n.id,uid()]));
   if(ids.size!==data.nodes.length||data.nodes.some(n=>typeof n.id!=='string'||typeof n.label!=='string'||n.label.length>1000))throw Error();
   const parents=new Map();
   for(const edge of data.edges){if(!ids.has(edge.source)||!ids.has(edge.target))throw Error();if(edge.tree){if(parents.has(edge.target))throw Error();parents.set(edge.target,edge.source)}}
   const roots=data.nodes.filter(n=>!parents.has(n.id)).map(n=>n.id);
   if(roots.length!==data.roots.length||new Set(data.roots).size!==roots.length||roots.some(id=>!data.roots.includes(id)))throw Error();
   const targetParents=new Map(g.edges.filter(edge=>edge.tree).map(edge=>[edge.target,edge.source]));
   let targetDepth=0;for(let id=parent;targetParents.has(id);id=targetParents.get(id))targetDepth++;
   for(const n of data.nodes){const visited=new Set();let id=n.id,depth=targetDepth+1;while(parents.has(id)){if(visited.has(id))throw Error();visited.add(id);id=parents.get(id);depth++}if(depth>100){this.message='계층 깊이는 100 이하여야 합니다.';return true}}
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
  return true;
 },
 effective(n){const base=this.localTypes.find(t=>t.name===n.type)?.style||this.localTypes.find(t=>t.name==='서비스')?.style||{background:'#222b24',color:'#eee9de',border_color:'#b89a60',font_size:15,shape:'rounded',icon:''};return {...base,...Object.fromEntries(Object.entries(n.overrides||{}).filter(([k,v])=>v!==null))}},
 native(g){const by={};for(const n of g.nodes){const s=this.effective(n);by[n.id]={id:n.id,topic:n.label,expanded:n.expanded,metadata:clone(n),style:{background:s.background,color:s.color,fontSize:s.font_size?s.font_size+'px':undefined,border:'1px solid '+s.border_color},icons:s.icon?[s.icon]:[],children:[]}}for(const e of g.edges.filter(e=>e.tree))by[e.source].children.push(by[e.target]);return {nodeData:by[g.root],direction:g.view.direction,summaries:clone(g.summaries||[]),arrows:g.edges.filter(e=>!e.tree).map(e=>({id:e.id,from:e.source,to:e.target,label:e.label,delta1:{x:50,y:0},delta2:{x:-50,y:0},bidirectional:e.bidirectional,style:{stroke:e.color,strokeWidth:2,strokeDasharray:e.dashed?'6 4':'',labelColor:e.color},metadata:clone(e)}))}},
 getSnapshot(){if(!this.mind||!this.ready)return {graph:null,dirty:false};const d=this.mind.getData(),nodes=[],edges=[];const walk=(n,parent)=>{const original=n.metadata||{};nodes.push({...original,id:n.id,label:n.topic,type:original.type||'서비스',description:original.description||'',file:original.file||'',overrides:original.overrides||{},expanded:n.expanded!==false});if(parent){const old=this.current.edges.find(e=>e.tree&&e.source===parent&&e.target===n.id);edges.push(old?clone(old):{id:uid(),source:parent,target:n.id,label:'',kind:'계층',tree:true,color:'#b89a60',dashed:false,bidirectional:false})}for(const c of n.children||[])walk(c,n.id)};walk(d.nodeData,null);for(const a of d.arrows||[])edges.push({...a.metadata,id:a.id,source:a.from,target:a.to,label:a.label||'',kind:a.metadata?.kind||'참조',tree:false,color:a.style?.stroke||'#b89a60',dashed:!!a.style?.strokeDasharray,bidirectional:!!a.bidirectional});return {graph:{version:1,root:d.nodeData.id,nodes,edges,summaries:clone(d.summaries||[]),view:{direction:this.mind.direction,scale:this.mind.scaleVal,scroll_left:Math.max(0,this.mind.container.scrollLeft),scroll_top:Math.max(0,this.mind.container.scrollTop),pan_x:parseFloat(this.mind.map.style.transform.match(/translate3d\(([-.0-9]+)/)?.[1]||0),pan_y:parseFloat(this.mind.map.style.transform.match(/translate3d\([-.0-9]+px,\s*([-.0-9]+)/)?.[1]||0)}},dirty:this.dirty}},
 capture(){if(this.suppress||!this.ready)return;this.current=this.getSnapshot().graph;this.nodes=clone(this.current.nodes);this.summaries=clone(this.current.summaries||[]);this.relations=clone(this.current.edges.filter(e=>!e.tree));this.history=this.history.slice(0,this.cursor+1);this.history.push(clone(this.current));if(this.history.length>60)this.history.shift();this.cursor=this.history.length-1;this.dirty=true;this.decorate()},
 shapePaths(shape,w,h){
  const right=w-1,bottom=h-1;
  if(shape==='diamond')return [`M ${w/2} 1 L ${right} ${h/2} L ${w/2} ${bottom} L 1 ${h/2} Z`];
  if(shape==='hexagon'){const cut=Math.min(24,w*.15);return [`M ${cut} 1 H ${w-cut} L ${right} ${h/2} L ${w-cut} ${bottom} H ${cut} L 1 ${h/2} Z`]}
  if(shape==='cylinder'){const cap=Math.min(10,h/5);return [`M 1 ${cap} C 1 1 ${right} 1 ${right} ${cap} V ${h-cap} C ${right} ${bottom} 1 ${bottom} 1 ${h-cap} Z`,`M 1 ${cap} C 1 ${cap*2} ${right} ${cap*2} ${right} ${cap}`]}
  if(shape==='document'){const fold=Math.min(18,w/5,h/3);return [`M 1 1 H ${w-fold} L ${right} ${fold} V ${bottom} H 1 Z`,`M ${w-fold} 1 V ${fold} H ${right}`]}
  return [];
 },
 decorate(){requestAnimationFrame(()=>{
  if(this.disposed||!this.ready)return;
  const shaped=new Set(['diamond','cylinder','hexagon','document']);let relink=false;
  for(const n of this.current.nodes){
   const el=this.visibleNode(n.id);if(!el)continue;
   const style=this.effective(n),shape=style.shape,before=[el.offsetWidth,el.offsetHeight];
   el.dataset.shape=shape||'rounded';el.classList.toggle('mm-node-shape',shaped.has(shape));
   el.style.borderRadius=shape==='ellipse'?'50%':shape==='pill'?'999px':shape==='rectangle'?'0':'10px';
   el.querySelector('.mm-node-outline')?.remove();
   if(!shaped.has(shape)){el.style.removeProperty('padding');continue}
   if(shape==='diamond'){
    const text=el.querySelector('.text'),icons=el.querySelector('.icons');
    const width=(text?.offsetWidth||0)+(icons?.offsetWidth||0)+12,height=Math.max(text?.offsetHeight||20,icons?.offsetHeight||0);
    el.style.padding=`${Math.ceil(height/2+14)}px ${Math.ceil(width/2+18)}px`;
   }else el.style.padding=shape==='cylinder'?'21px 18px':shape==='hexagon'?'13px 30px':'18px 26px 14px 16px';
   const w=el.offsetWidth,h=el.offsetHeight,ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
   svg.classList.add('mm-node-outline');svg.setAttribute('aria-hidden','true');svg.setAttribute('viewBox',`0 0 ${w} ${h}`);svg.setAttribute('preserveAspectRatio','none');
   this.shapePaths(shape,w,h).forEach((d,i)=>{const path=document.createElementNS(ns,'path');path.setAttribute('d',d);path.setAttribute('fill',i===0?style.background||'#222b24':'none');path.setAttribute('stroke',style.border_color||'#b89a60');path.setAttribute('stroke-width','1.5');path.setAttribute('stroke-linejoin','round');svg.appendChild(path)});
   el.prepend(svg);if(w!==before[0]||h!==before[1])relink=true;
  }
  if(relink)this.mind.linkDiv();this.paintRelations();
 })},
 select(id){this.summaryId=null;if(this.panel==='summary')this.panel='node';this.selected=id;const n=this.getSnapshot().graph.nodes.find(n=>n.id===id);if(!n)return;this.form=clone(n);this.custom=Object.values(n.overrides||{}).some(v=>v!==null);this.style=this.effective(n);if(this.searchQuery?.trim())this.searchIndex=this.searchMatches.findIndex(n=>n.id===id);this.paintRelations()},
 async show(g,reset=false){this.suppress=true;if(reset){this.searchQuery='';this.searchIndex=-1;this.searchOpen=false}this.current=clone(g);this.direction=g.view.direction;this.mind.refresh(this.native(g));[()=>this.mind.initLeft(),()=>this.mind.initRight(),()=>this.mind.initSide(),()=>this.mind.initDown()][g.view.direction]();this.mind.scale(g.view.scale);this.mind.container.scrollLeft=g.view.scroll_left;this.mind.container.scrollTop=g.view.scroll_top;this.nodes=clone(g.nodes);this.summaries=clone(g.summaries||[]);this.relations=clone(g.edges.filter(e=>!e.tree));this.select(g.root);this.mind.selectNode(this.mind.findEle(g.root));if(g.view.pan_x||g.view.pan_y)this.mind.map.style.transform=`translate3d(${g.view.pan_x}px, ${g.view.pan_y}px, 0) scale(${g.view.scale})`;if(reset&&!g.view.pan_x&&!g.view.pan_y&&this.$refs.canvas.clientWidth)requestAnimationFrame(()=>this.fit());this.percent=Math.round(this.mind.scaleVal*100);this.decorate();this.suppress=false;if(reset){this.history=[clone(g)];this.cursor=0;this.dirty=false}},
 loadGraphFromProps(){if(this.ready)this.show(this.graph,true)},
 markSaved(){this.dirty=false},
 updateTypes(types){this.localTypes=clone(types);const g=this.getSnapshot().graph;this.show(g);},
 commit(g){
  const previous=this.current;
  g.summaries=(g.summaries||[]).flatMap(s=>{
   const old=(previous?.edges||g.edges).filter(e=>e.tree&&e.source===s.parent).map(e=>e.target);
   const next=g.edges.filter(e=>e.tree&&e.source===s.parent).map(e=>e.target);
   const members=old.slice(s.start,s.end+1).map(id=>next.indexOf(id)).filter(i=>i>=0);
   if(!g.nodes.some(n=>n.id===s.parent)||!members.length)return [];
   return [{...s,start:Math.min(...members),end:Math.max(...members)}];
  });
  this.show(g);this.capture()
 },
 summarySelected(s){if(this.suppress)return;this.selected=null;this.paintRelations();this.summaryId=s.id;this.summaryForm={...clone(s),style:{stroke:'#b89a60',labelColor:'#eee9de',...s.style}};this.panel='summary'},
 chooseSummary(id){const el=this.mind.nodes.querySelector('[id="s-'+id+'"]');if(!el){this.message='대상 계층을 펼쳐 요약을 확인하세요.';return}this.mind.clearSelection();this.mind.selectSummary(el)},
 createSummary(){if(!this.mind.currentNodes?.length){this.message='요약할 노드를 먼저 선택하세요.';return}this.mind.createSummary({style:{stroke:'#b89a60',labelColor:'#eee9de'}})},
 applySummary(){if(!this.summaryForm.label?.trim())return;const g=this.getSnapshot().graph;const s=g.summaries.find(s=>s.id===this.summaryId);if(!s)return;Object.assign(s,clone(this.summaryForm));const id=s.id;this.commit(g);this.chooseSummary(id)},
 removeSummary(){if(!this.summaryId)return;const g=this.getSnapshot().graph;g.summaries=g.summaries.filter(s=>s.id!==this.summaryId);this.summaryId=null;this.commit(g);this.panel='summary'},
 add(sibling){const g=this.getSnapshot().graph;const parent=sibling?g.edges.find(e=>e.tree&&e.target===this.selected)?.source:this.selected;if(!parent){this.message='루트에는 형제 노드를 추가할 수 없습니다.';return}const id=uid();g.nodes.push({id,label:'새 노드',type:'서비스',description:'',file:'',overrides:{},expanded:true});g.nodes.find(n=>n.id===parent).expanded=true;g.edges.push({id:uid(),source:parent,target:id,label:'',kind:'계층',tree:true,color:'#b89a60',dashed:false,bidirectional:false});this.commit(g);this.mind.selectNode(this.mind.findEle(id));this.select(id)},
 removeNode(){if(this.summaryId){this.removeSummary();return}const g=this.getSnapshot().graph;if(this.selected===g.root){this.message='루트는 삭제할 수 없습니다.';return}const gone=new Set([this.selected]);let size;do{size=gone.size;g.edges.filter(e=>e.tree&&gone.has(e.source)).forEach(e=>gone.add(e.target))}while(size!==gone.size);g.nodes=g.nodes.filter(n=>!gone.has(n.id));g.edges=g.edges.filter(e=>!gone.has(e.source)&&!gone.has(e.target));this.commit(g)},
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
 key(e){
  const mod=e.ctrlKey||e.metaKey, k=e.key.toLowerCase();
  if(mod&&k==='f'&&!this.editing(e)){e.preventDefault();this.$refs.nodeSearch.focus();this.$refs.nodeSearch.select();return}
  if(mod&&k==='s'){e.preventDefault();this.$emit('save_request');return}
  if(this.editing(e)||!this.ready||e.isComposing)return;
  if(mod&&!e.altKey){
   if(k==='c'){
    e.preventDefault();e.stopPropagation();
    if(!e.repeat)this.copySelection();
    return;
   }
   // Leave native Ctrl+V available for a first paste from another browser tab.
   if(k==='v'&&(e.shiftKey||nodeClipboardText)){
    e.preventDefault();e.stopPropagation();
    if(!e.repeat)this.pasteSelection();
    return;
   }
  }
  if(mod&&k==='a'){e.preventDefault();this.mind.selectNodes(this.nodes.map(n=>this.mind.findEle(n.id)));return}
  if(e.key==='Tab'){e.preventDefault();this.add(false)}
  else if(e.key==='Enter'){e.preventDefault();if(this.summaryId){this.panel='summary';this.$nextTick(()=>this.$refs.summaryName?.focus())}else this.add(true)}
  else if(e.key==='Delete'){e.preventDefault();this.removeNode()}
  else if(mod&&k==='z'){e.preventDefault();this.undo(e.shiftKey?1:-1)}
  else if(mod&&k==='y'){e.preventDefault();this.undo(1)}
 }
 },
 async mounted(){try{const path=(window.path_prefix||'')+this.resourcePath;await loadResource(path+'/MindElixir.css');const {default:MindElixir}=await import(path+'/MindElixir.js');if(this.disposed)return;this.mind=new MindElixir({el:this.$refs.canvas,direction:this.graph.view.direction,editable:true,contextMenu:this.contextMenuOptions(),toolBar:false,keypress:false,allowUndo:false,mouseSelectionButton:2,overflowHidden:false,alignment:'nodes',scaleMin:.1,scaleMax:8,newTopicName:'새 노드'});await this.mind.init(this.native(this.graph));this.ready=true;await this.show(this.graph,true);this.mind.bus.addListener('operation',()=>{this.capture();const summary=this.mind.currentSummary?.summaryObj;if(summary)this.summarySelected(summary);else if(this.selected)this.select(this.selected)});this.mind.bus.addListener('linkDiv',()=>this.paintRelations());this.mind.bus.addListener('selectSummary',s=>this.summarySelected(s));this.mind.bus.addListener('unselectSummary',()=>{if(!this.suppress)this.summaryId=null});this.mind.bus.addListener('selectNodes',nodes=>{if(nodes?.[0])this.select(nodes[0].id)});this.observer=new ResizeObserver(()=>{if(this.$refs.canvas.clientWidth>0&&!this.visibleOnce){this.visibleOnce=true;if(!this.graph.view.pan_x&&!this.graph.view.pan_y)this.fit()}});this.observer.observe(this.$refs.canvas);this.onWheel=()=>{this.percent=Math.round(this.mind.scaleVal*100)};this.$refs.canvas.addEventListener('wheel',this.onWheel);}catch(e){console.error(e);this.message=String(e);this.$emit('load_error',String(e))}},
 beforeUnmount(){this.disposed=true;this.observer?.disconnect();this.mind?.destroy?.()}
};
