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
test('evidence graph renders an explicit sample inventory when no audit has completed',()=>{
 const result=vm.runInContext(`state.detail={dataset:{id:'demo',name:'Research set'}};state.graph={audit_completed:false,network_mode:'sample_inventory',finding_count:0,nodes:[{id:'s:s1',label:'image-1',type:'sample',split:'train'}],edges:[],note:'No completed audit.'};renderGraph()`,ctx);
 assert.ok(result.includes('id="nodeGraph"'));
 assert.ok(result.includes('No completed audit'));
 assert.ok(result.includes('data-action="run-audit"'));
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

test('baseline failure explorer shows dataset-specific requirements and job error',()=>{
 const rendered=vm.runInContext(`state.detail={dataset:{id:'ds1',name:'Test data'},experiments:[]};
  state.jobs=[{kind:'baseline',status:'failed',error:'No independent test records remain'}];
  state.baselineReadiness={ready:false,split_counts:{train:40,val:8,test:0},errors:['A separate held-out test split is required.'],warnings:[]};
  renderFailures()`,ctx);
 assert.ok(rendered.includes('Baseline dataset readiness'));
 assert.ok(rendered.includes('A separate held-out test split is required.'));
 assert.ok(rendered.includes('No independent test records remain'));
});
test('a completed baseline without its model artifact cannot unlock dependent labs',()=>{
 const ready=vm.runInContext(`state.detail={dataset:{id:'ds1',name:'Test data'},experiments:[{id:'dead',kind:'baseline',status:'completed',artifact_available:false}]};
  bestExp('baseline')`,ctx);
 assert.equal(ready,undefined);
});
