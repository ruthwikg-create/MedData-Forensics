/** Regression checks for all dataset-empty workspaces; no browser/npm dependencies. */
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const test=require('node:test');
const assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../frontend/static/app.js'),'utf8');
// Exercise actual renderer functions without starting DOM event handlers or the API polling loop.
const renderSource=source.split("document.addEventListener('click',async e=>{")[0];
const ctx=vm.createContext({
  document:{querySelectorAll:()=>[]},
  window:{},
  console,
});
vm.runInContext(renderSource,ctx,{filename:'frontend/static/app.js'});
const routes={
  dna:['Dataset DNA','Explore the anatomy of a dataset'],
  audit:['Forensic Audit','Find hidden data-quality risks'],
  graph:['Forensic Evidence Graph','Connect findings to their source images'],
  review:['Review Center','Review findings without altering raw data'],
  shortcut:['AI Shortcut Inspector','Investigate possible visual shortcuts'],
  counterfactual:['Counterfactual Lab','See how image changes affect predictions'],
  cross:['Cross-Dataset Reliability Lab','Compare compatible research collections'],
  impact:['Audit Impact Simulator','Measure the effect of reviewed data issues'],
  failures:['Model Failure Explorer','Understand where the baseline fails'],
  repro:['Reproducibility Engine','Make every experiment reproducible'],
};
for(const [view,[pageTitle,onboardingTitle]] of Object.entries(routes)){
  test(`${view} renders a unique no-dataset onboarding, not Overview`,()=>{
    const html=vm.runInContext(`state.view=${JSON.stringify(view)};RENDER[state.view]()`,ctx);
    assert.equal(typeof html,'string');
    assert.ok(html.includes(`<h1>${pageTitle}</h1>`),`${view} should show its own heading`);
    assert.ok(html.includes(`<h2>${onboardingTitle}</h2>`),`${view} should provide specific next steps`);
    assert.ok(html.includes(`data-empty-view="${view}"`),`${view} should preserve correct route`);
    assert.ok(html.includes(`data-preview-type="${view}"`), `${view} should have a distinct module-specific preview`);
    assert.ok(!html.includes('Find what the data hides.'),`${view} must not silently render Overview`);
    assert.ok(html.includes('data-action="demo"'));
    assert.ok(html.includes('data-action="import"'));
  });
}
test('every lab renderer returns consistent {html,e} when no dataset is present',()=>{
  for(const name of ['shortcut','counterfactual','cross_dataset','impact']){
    const result=vm.runInContext(`state.view=${JSON.stringify(name)};labBase('test','Lab','Desc',${JSON.stringify(name)})`,ctx);
    assert.equal(typeof result.html,'string');
    assert.equal(result.e,null);
    assert.ok(result.html.includes('data-empty-view='));
  }
});
test('overview and privacy guard remain useful without imported data',()=>{
 for(const v of ['overview','privacy']){
  const html=vm.runInContext(`state.view=${JSON.stringify(v)};RENDER[state.view]()`,ctx);
  assert.equal(typeof html,'string');
  assert.ok(html.length>500);
 }
});

const uniquePatterns={
 dna:['DATASET DNA / STRUCTURE VIEW','dna-branches'],
 audit:['FORENSIC AUDIT / DETECTOR PLAN','audit-stage-grid'],
 graph:['EVIDENCE GRAPH / LINK TYPES','graph-illustration'],
 review:['REVIEW CENTER / DECISION STATES','review-states'],
 shortcut:['SHORTCUT INSPECTOR / CONTROLLED PROBE','paired-phantoms'],
 counterfactual:['COUNTERFACTUAL LAB / LIVE VISUAL PREVIEW','counterfactualMode'],
 cross:['CROSS-DATASET / COMPATIBILITY GATE','cross-comparison'],
 impact:['IMPACT SIMULATOR / COMPARISON DESIGN','impact-lanes'],
 failures:['FAILURE EXPLORER / METRIC INTERPRETATION','confusion-concept'],
 repro:['REPRODUCIBILITY / EXPERIMENT CONTRACT','manifest-panel'],
};
for(const [view,required] of Object.entries(uniquePatterns)) {
 test(`${view} has a distinguishable meaningful preview`,()=>{
  const html=vm.runInContext(`state.view=${JSON.stringify(view)};RENDER[state.view]()`,ctx);
  for(const part of required)assert.ok(html.includes(part),`${view} missing ${part}`);
 });
}
test('the counterfactual example is explicitly synthetic with interactive controls',()=>{
 const html=vm.runInContext(`state.view='counterfactual';RENDER.counterfactual()`,ctx);
 assert.ok(html.includes('no AI inference'));
 assert.ok(html.includes('id="counterfactualAmount"'));
 assert.ok(html.includes('id="counterfactualMask"'));
});
test('all no-data research pages disclose that results need a real dataset',()=>{
 for(const view of Object.keys(uniquePatterns)){
  const html=vm.runInContext(`state.view=${JSON.stringify(view)};RENDER[state.view]()`,ctx);
  assert.ok(html.includes('actual findings will appear only after you load research images.'),view);
 }
});

test('real-data ranking compare displays candidate order without inventing verified defect counts',()=>{
 const result=vm.runInContext(`state.rankings={review_budget:6,candidate_count:14,ground_truth_available:false,method:'Fixed candidates',caveat:'Independent truth unavailable',strategies:[{name:'IGAT (experimental)',review_budget:6,overlap_with_igat:6,top_candidates:[{id:'fx1',title:'Potential split overlap',kind:'split_leakage',sample_id:'im-1',priority:.81,confidence:.71}]}]};renderRankings()`,ctx);
 assert.ok(result.includes('data-ranking-budget="6"'));
 assert.ok(result.includes('6/6 overlap with IGAT'));
 assert.ok(result.includes('data-finding="fx1"'));
 assert.ok(result.includes('No validated defect yield'));
 assert.ok(!result.includes('known injected defects'));
});
test('evidence graph draws isolated real sample nodes without invented links',()=>{
 const result=vm.runInContext(`state.detail={dataset:{id:'demo',name:'Research set'}};state.graph={audit_completed:false,network_mode:'sample_inventory',finding_count:0,nodes:[{id:'s:s1',label:'image-1',type:'sample',split:'train'}],edges:[],note:'No completed audit.'};renderGraph()`,ctx);
 assert.ok(result.includes('id="nodeGraph"'));
 assert.ok(result.includes('isolated real dataset nodes'));
 assert.ok(result.includes('No completed audit'));
 assert.ok(result.includes('data-action="run-audit"'));
 const box={innerHTML:'',querySelectorAll:()=>[]};
 ctx.document.querySelector=sel=>sel==='#nodeGraph'?box:null;
 vm.runInContext('drawGraph(state.graph)',ctx);
 assert.ok(box.innerHTML.includes('data-node="s:s1"'));
 assert.ok(!box.innerHTML.includes('<path'), 'no detector links means no connecting lines');
 delete ctx.document.querySelector;
});
test('shortcut and counterfactual make a trained baseline a visible prerequisite',()=>{
 const result=vm.runInContext(`state.detail={dataset:{id:'demo',name:'Research set'},experiments:[]};state.samples={items:[{id:'a',sample_id:'image-1',label:'0',split:'test',image_url:'/files/a'}]};[renderShortcut(),renderCounterfactual()]`,ctx);
 assert.ok(result[0].includes('Train baseline'));
 assert.ok(!result[0].includes('data-action="shortcut"'));
 assert.ok(result[1].includes('id="counterfactualAmount"'));
 assert.ok(result[1].includes('id="counterModifiedImage"'));
 assert.ok(!result[1].includes('data-action="counterfactual-launch"'));
});
test('completed baseline enables real lab actions and parameter preview',()=>{
 const result=vm.runInContext(`state.detail={dataset:{id:'demo',name:'Research set'},experiments:[{kind:'baseline',status:'completed',result:{}}]};state.samples={items:[{id:'a',sample_id:'image-1',label:'0',split:'test',image_url:'/files/a'}]};[renderShortcut(),renderCounterfactual()]`,ctx);
 assert.ok(result[0].includes('data-action="shortcut"'));
 assert.ok(result[1].includes('data-action="counterfactual-launch"'));
});
test('access token panel explains that localhost does not require a token by default',()=>{
 const result=vm.runInContext(`state.privacy={token_required:false};renderPrivacy()`,ctx);
 assert.ok(result.includes('TOKEN DISABLED (DEFAULT)'));
 assert.ok(result.includes('No access token is necessary'));
});

test('evidence graph displays linked findings as accessible, scrollable node cards',()=>{
 const html=vm.runInContext("state.detail={dataset:{id:'demo',name:'Research set'}};state.graph={audit_completed:true,network_mode:'evidence',finding_count:1,nodes:[{id:'s:s1',label:'image-1',type:'sample',split:'train'},{id:'f:f1',label:'split leakage',type:'finding',status:'suspected'}],edges:[{source:'f:f1',target:'s:s1'}],note:'Detector evidence only'};renderGraph()",ctx);
 assert.ok(html.includes('id="nodeGraph"'));
 assert.ok(html.includes('Interactive evidence graph; scroll to explore'));
 assert.ok(html.includes('1 observed image–finding links'));
 const box={innerHTML:'',querySelectorAll:()=>[]};
 ctx.document.querySelector=s=>s==='#nodeGraph'?box:null;
 vm.runInContext("drawGraph(state.graph)",ctx);
 assert.ok(box.innerHTML.includes('<svg'));
 assert.ok(box.innerHTML.includes('width="950"'));
 assert.ok(box.innerHTML.includes('Actual forensic evidence connections'));
 assert.ok(box.innerHTML.includes('data-node="s:s1"'));
 assert.ok(box.innerHTML.includes('data-node="f:f1"'));
 assert.ok(box.innerHTML.includes('stroke-opacity=".8"'));
 delete ctx.document.querySelector;
});
test('global-only findings produce inspectable unlinked graph nodes without invented edges',()=>{
 const html=vm.runInContext("state.detail={dataset:{id:'demo',name:'Research set'}};state.graph={audit_completed:true,network_mode:'sample_inventory',finding_count:1,nodes:[{id:'s:s1',label:'image-1',split:'train',type:'sample'},{id:'f:f1',type:'finding',label:'source association',status:'suspected'}],edges:[],note:'Dataset-wide association only'};renderGraph()",ctx);
 assert.ok(html.includes('id="nodeGraph"'));
 assert.ok(html.includes('data-finding="f1"'));
 const box={innerHTML:'',querySelectorAll:()=>[]};
 ctx.document.querySelector=sel=>sel==='#nodeGraph'?box:null;
 vm.runInContext("drawGraph(state.graph)",ctx);
 assert.ok(box.innerHTML.includes('data-node="s:s1"'));
 assert.ok(box.innerHTML.includes('data-node="f:f1"'));
 assert.ok(!box.innerHTML.includes('<path'),'no unsupported links may be drawn');
 delete ctx.document.querySelector;
});

test('approved transparent MedData Forensics wordmark replaces the old sidebar logo',()=>{
 const html=fs.readFileSync(path.join(__dirname,'../frontend/static/index.html'),'utf8');
 assert.ok(html.includes('class="brand-wordmark"'));
 assert.ok(html.includes('src="/assets/meddata-wordmark-dark.svg"'));
 assert.ok(html.includes('alt="MedData Forensics"'));
 assert.ok(!html.includes('class="brand-mark"'), 'old graphic symbol must be removed');
 const dark=fs.readFileSync(path.join(__dirname,'../frontend/static/meddata-wordmark-dark.svg'),'utf8');
 const light=fs.readFileSync(path.join(__dirname,'../frontend/static/meddata-wordmark.svg'),'utf8');
 assert.ok(dark.includes('<title>MedData Forensics</title>'));
 assert.ok(dark.includes('viewBox="0 0 874 288"'));
 for(const source of [dark,light]){
  assert.ok(!source.includes('<rect'), 'wordmark must have no background rectangle');
  assert.ok(!source.includes('<image'), 'wordmark must not have embedded raster background');
  assert.ok(source.includes('<path'), 'logo lettering must be scalable vector artwork');
 }
 const css=fs.readFileSync(path.join(__dirname,'../frontend/static/styles.css'),'utf8');
 assert.ok(css.includes('.brand-wordmark{display:block'));
 assert.ok(css.includes('aspect-ratio:874/288'));
});

test('baseline failure provides a clear Analysis Jobs link',()=>{
 const html=vm.runInContext("state.detail={dataset:{id:'demo',name:'Research set'},experiments:[{kind:'baseline',status:'failed',result:{}}]};renderFailures()",ctx);
 assert.ok(html.includes('The last baseline model failed'));
 assert.ok(html.includes('data-action="jobs"'));
 assert.ok(html.includes('data-action="baseline-launch"'));
});

test('baseline failure displays actionable data checks and the exact previous job error',()=>{
 const html=vm.runInContext("state.detail={dataset:{id:'demo',name:'Sorted data'},experiments:[]};\n  state.baselineReadiness={ready:false,train_count:13,test_count:4,training_class_counts:{class_a:13},\n    reasons:['At least 20 decodable training images are needed.','At least 2 training classes are needed.'],\n    warnings:[],last_attempt:{status:'failed',error:'ValueError: 2 training classes required'}};\n  renderFailures()",ctx);
 assert.ok(html.includes('Baseline readiness'));
 assert.ok(html.includes('Dataset not ready'));
 assert.ok(html.includes('At least 2 training classes are needed.'));
 assert.ok(html.includes('ValueError: 2 training classes required'));
 assert.ok(!html.includes('Test macro-F1'));
});
test('a completed baseline row without a checkpoint cannot unlock model labs',()=>{
 const results=vm.runInContext("state.detail={dataset:{id:'demo',name:'Research set'},\n   experiments:[{kind:'baseline',status:'completed',checkpoint_available:false,result:{}}]};\n  state.baselineReadiness={ready:true,train_count:30,test_count:9,\n   training_class_counts:{a:15,b:15},warnings:[],reasons:[],\n   last_attempt:{status:'completed',checkpoint_available:false}};\n  [renderShortcut(),renderCounterfactual(),renderFailures()]",ctx);
 assert.ok(!results[0].includes('data-action="shortcut"'));
 assert.ok(!results[1].includes('data-action="counterfactual-launch"'));
 assert.ok(results[2].includes('previous model file is missing'));
 assert.ok(results[2].includes('Train baseline'));
});

test('ranking comparison explains completed audits with no candidate findings',()=>{
 const out=vm.runInContext("state.rankings={strategies:[],message:'Audit completed with no candidate findings. There is nothing to compare.'};renderRankings()",ctx);
 assert.ok(out.includes('There is nothing to compare.'));
});
test('Compare button is disabled when audit has zero findings',()=>{
 const out=vm.runInContext("state.detail={dataset:{id:'demo',name:'No-finding set'},audits:[{status:'completed',summary:{total_findings:0,valid_samples:42,by_kind:{}}}]};state.findings={items:[],count:0};state.rankings={strategies:[],message:'Audit completed with no candidate findings.'};renderAudit()",ctx);
 assert.ok(out.includes('disabled title="No detector findings are available to compare"'));
 assert.ok(out.includes('Audit completed with no candidate findings'));
});


test('Evidence Graph controls have real search, severity, connection and zoom behaviors',()=>{
 const graph={audit_completed:true,note:'Synthetic detector observations',
   nodes:[
    {id:'s:s1',type:'sample',label:'scan-a',split:'train'},
    {id:'s:s2',type:'sample',label:'scan-b',split:'test'},
    {id:'s:s3',type:'sample',label:'scan-c',split:'validation'},
    {id:'f:f1',type:'finding',label:'split leakage',severity:'high',status:'suspected'},
    {id:'f:f2',type:'finding',label:'source association',severity:'medium',status:'uncertain'}],
   edges:[{source:'f:f1',target:'s:s1'},{source:'f:f1',target:'s:s2'}]};
 ctx.testGraph=graph;
 let html=vm.runInContext("state.detail={dataset:{id:'synthetic',name:'Synthetic QA'}};state.graph=testGraph;state.graphUi={search:'',severity:'all',links:'all',zoom:1};renderGraph()",ctx);
 for(const part of ['id="graphSearch"','id="graphSeverity"','id="graphLinks"','data-action="graph-zoom-out"','data-action="graph-zoom-in"','data-action="graph-reset"','graphExplorerResults']){
  assert.ok(html.includes(part),'missing functional graph control '+part);
 }
 let view=vm.runInContext("graphVisibleData(testGraph,{search:'',severity:'high',links:'all'})",ctx);
 assert.equal(view.edges.length,2);
 assert.ok(view.nodes.some(n=>n.id==='f:f1'));
 assert.ok(!view.nodes.some(n=>n.id==='f:f2'));
 view=vm.runInContext("graphVisibleData(testGraph,{search:'scan-b',severity:'all',links:'all'})",ctx);
 assert.equal(view.edges.length,1);
 assert.equal(view.nodes.length,2);
 assert.deepEqual([...view.nodes.map(x=>x.id)].sort(),['f:f1','s:s2']);
 view=vm.runInContext("graphVisibleData(testGraph,{search:'',severity:'all',links:'unlinked'})",ctx);
 assert.equal(view.edges.length,0);
 assert.ok(view.nodes.some(n=>n.id==='s:s3'));
 assert.ok(view.nodes.some(n=>n.id==='f:f2'));
 view=vm.runInContext("graphVisibleData(testGraph,{search:'absent',severity:'all',links:'all'})",ctx);
 assert.equal(view.nodes.length,0);
 assert.equal(view.edges.length,0);
 const box={innerHTML:'',querySelectorAll:()=>[]};
 ctx.document.querySelector=sel=>sel==='#nodeGraph'?box:null;
 vm.runInContext("state.graphUi.zoom=1.5;drawGraph(testGraph)",ctx);
 assert.ok(box.innerHTML.includes('width="1425"'),'SVG zoom should reflect the selected scale');
 assert.ok(box.innerHTML.includes('data-node="f:f1"'));
 assert.ok(box.innerHTML.includes('data-node="s:s1"'));
 delete ctx.document.querySelector;
 vm.runInContext("state.graphUi={search:'',severity:'all',links:'all',zoom:1}",ctx);
});

test('real baseline confusion cells drill into actual predicted test records',()=>{
 const payload={kind:'baseline',status:'completed',checkpoint_available:true,
   result:{test:{metrics:{labels:['A','B'],macro_f1:0.5,balanced_accuracy:0.5,
      confusion_matrix:[[1,1],[0,1]],calibration_bins:[],per_class:{}},
     predictions:[
      {sample_db_id:'db1',sample_id:'s1',actual:'A',predicted:'A',correct:true},
      {sample_db_id:'db2',sample_id:'s2',actual:'A',predicted:'B',correct:false},
      {sample_db_id:'db3',sample_id:'s3',actual:'B',predicted:'B',correct:true}
     ]}}};
 ctx.baselinePayload=payload;
 const html=vm.runInContext("state.detail={dataset:{id:'demo'},experiments:[baselinePayload]};state.failureCell='';renderFailures()",ctx);
 assert.ok(html.includes('data-confusion="0:1"'));
 assert.ok(html.includes('aria-pressed="false"'));
 assert.ok(html.includes('id="failureGallery"'));
 assert.ok(html.includes('data-sample="db2"'));
 let selected=vm.runInContext("state.failureCell='1:1';renderFailureGallery(baselinePayload)",ctx);
 assert.ok(selected.includes('data-sample="db3"'));
 assert.ok(!selected.includes('data-sample="db2"'));
 assert.ok(selected.includes('data-action="failure-reset"'));
 let defaultGallery=vm.runInContext("state.failureCell='';renderFailureGallery(baselinePayload)",ctx);
 assert.ok(defaultGallery.includes('data-sample="db2"'));
 assert.ok(!defaultGallery.includes('data-sample="db1"'));
});

test('Dataset DNA histograms are actual sample filters and persist across rerenders',()=>{
 const html=vm.runInContext("state.detail={dataset:{id:'demo',name:'Synthetic record set',source:'Generated',modality:'Synthetic',license:'CC0',manifest_hash:'abc',synthetic:true,sample_count:48}};state.dna={splits:{train:30,val:9,test:9},labels:{a:24,b:24},sites:{none:48},image_shapes:{'28x28':48},lineage:[],group_coverage:{with_group_id:20}};state.samples={items:[],count:0};state.samplePage=1;state.dnaFilters={split:'',label:'',search:''};renderDNA()",ctx);
 assert.ok(html.includes('data-dna-chart="split"'));
 assert.ok(html.includes('data-dna-value="train"'));
 assert.ok(html.includes('data-dna-chart="label"'));
 assert.ok(html.includes('aria-pressed="false"'));
 vm.runInContext("setDnaChartFilter('split','train');setDnaChartFilter('label','b')",ctx);
 const query=vm.runInContext("state.sampleFilter",ctx);
 assert.ok(query.includes('split=train'));
 assert.ok(query.includes('label=b'));
 const active=vm.runInContext("renderDNA()",ctx);
 assert.ok(active.includes('data-dna-value="train" aria-pressed="true"'));
 assert.ok(active.includes('data-dna-value="b" aria-pressed="true"'));
 assert.ok(active.includes('id="dnaSearch"'));
 assert.ok(active.includes('data-action="clear-sample-filters"'));
 vm.runInContext("state.dnaFilters={split:'',label:'',search:''};state.sampleFilter=''",ctx);
});
test('navigation transfers focus to main content after route changes',()=>{
 assert.ok(source.includes("await render();$('#main')?.focus({preventScroll:true})"));
});

test('Counterfactual Lab has independent pagination and persistent visual controls',()=>{
 const html=vm.runInContext("state.detail={dataset:{id:'demo',name:'Synthetic research'},experiments:[]};state.samples={count:53,items:[{id:'s1',sample_id:'0001',label:'0',split:'test',image_url:'/files/s1'}]};state.counterPage=2;state.counterStrength=75;state.counterMode='mask';renderCounterfactual()",ctx);
 assert.ok(html.includes('data-page="counter:prev"'));
 assert.ok(html.includes('data-page="counter:next"'));
 assert.ok(html.includes('Page 2/3'));
 assert.ok(html.includes('id="counterfactualAmount" type="range" min="0" max="100" value="75"'));
 assert.ok(html.includes('id="counterfactualReadout" for="counterfactualAmount">75%'));
 assert.ok(html.includes('value="mask" selected'));
 assert.ok(source.includes("state.view==='counterfactual'?state.counterPage:state.samplePage"));
 assert.ok(source.includes("state.view==='dna'?(state.sampleFilter||''):''"));
 vm.runInContext("state.counterPage=1;state.counterMode='brightness';state.counterStrength=40",ctx);
});

test('evidence graph offers interactive network and trace layouts with only observed links',()=>{
 const html=vm.runInContext("state.detail={dataset:{id:'demo',name:'Test'}};state.graph={nodes:[{id:'s:1',type:'sample',label:'Sample one'},{id:'f:1',type:'finding',label:'Finding one',severity:'high'}],edges:[{source:'f:1',target:'s:1'}],audit_completed:true};renderGraph()",ctx);
 assert.ok(html.includes('id="graphLayout"'));
 assert.ok(html.includes('Evidence network'));
 assert.ok(html.includes('Two-column trace'));
 assert.ok(html.includes('id="nodeGraph"'));
 const filtered=vm.runInContext("graphVisibleData(state.graph,{search:'',severity:'all',links:'all',layout:'network',zoom:1})",ctx);
 assert.equal(filtered.nodes.length,2);
 assert.equal(filtered.edges.length,1);
});


test('Cross-Dataset Lab explains the one-dataset empty state and offers import actions',()=>{
 const html=vm.runInContext(`
  state.did='ham';state.detail={dataset:{id:'ham',name:'HAM10000'},experiments:[]};
  state.datasets=[{id:'ham',name:'HAM10000'}];
  state.crossReadiness={targets:[],compatible_target_count:0};
  renderCross()
 `,ctx);
 assert.ok(html.includes('Only one dataset is currently loaded'));
 assert.ok(html.includes('needs a second, independently collected dataset'));
 assert.ok(html.includes('data-action="import"'));
 assert.ok(html.includes('data-action="large-import"'));
 assert.ok(!html.includes('id="crossTarget"'));
});

test('Cross-Dataset Lab explains incompatible candidates and disables external evaluation',()=>{
 const html=vm.runInContext(`
  state.did='ham';state.detail={dataset:{id:'ham',name:'HAM10000'},experiments:[
   {kind:'baseline',status:'completed',checkpoint_available:true}
  ]};
  state.datasets=[{id:'ham',name:'HAM10000'},{id:'path',name:'PathMNIST'}];
  state.crossReadiness={targets:[{id:'path',name:'PathMNIST',sample_count:100,modality:'Histopathology',
   compatible:false,reasons:['Declared modality does not match the source collection.']}]};
  renderCross()
 `,ctx);
 assert.ok(html.includes('No compatible target found'));
 assert.ok(html.includes('PathMNIST'));
 assert.ok(html.includes('Declared modality does not match'));
 assert.ok(html.includes('disabled aria-disabled="true"'));
 assert.ok(!html.includes('data-action="cross-launch"'));
});

test('Cross-Dataset Lab exposes only compatible target options',()=>{
 const html=vm.runInContext(`
  state.did='ham';state.detail={dataset:{id:'ham',name:'HAM10000'},experiments:[
   {kind:'baseline',status:'completed',checkpoint_available:true}
  ]};
  state.datasets=[{id:'ham',name:'HAM10000'},{id:'derma',name:'Derma collection'}];
  state.crossReadiness={targets:[{id:'derma',name:'Derma collection',sample_count:120,modality:'Dermatoscopic images',
   compatible:true,reasons:[]}]};
  renderCross()
 `,ctx);
 assert.ok(html.includes('id="crossTarget"'));
 assert.ok(html.includes('value="derma"'));
 assert.ok(html.includes('data-action="cross-launch"'));
});

test('Impact Simulator shows evidence prerequisites and prior failure instead of implying results exist',()=>{
 const html=vm.runInContext(`
  state.did='ham';state.detail={dataset:{id:'ham',name:'HAM10000'},experiments:[]};
  state.impactReadiness={ready:false,audit_completed:true,train_count:8000,test_count:1000,
   confirmed_supported_findings:0,confirmed_training_samples:0,suspected_training_samples:4,
   reasons:['No reviewer-confirmed supported finding is linked to a training image.'],
   last_attempt:{status:'failed',error:'No confirmed training-sample findings.'}};
  renderImpact()
 `,ctx);
 assert.ok(html.includes('Impact experiment readiness'));
 assert.ok(html.includes('Complete prerequisites first'));
 assert.ok(html.includes('disabled aria-disabled="true"'));
 assert.ok(!html.includes('data-action="impact"'));
 assert.ok(html.includes('Previous attempt did not complete'));
 assert.ok(html.includes('No confirmed training-sample findings.'));
 assert.ok(html.includes('data-action="go-review"'));
 assert.ok(html.includes('Open Forensic Audit'));
 assert.ok(html.includes('Eligible evidence types'));
 assert.ok(!html.includes('Baseline macro-F1'));
});
