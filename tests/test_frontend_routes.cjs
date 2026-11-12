/** Regression checks for dataset-empty workspaces; no browser/npm dependencies. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),test=require('node:test'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../frontend/static/app.js'),'utf8');
const ctx=vm.createContext({document:{querySelectorAll:()=>[]},window:{},console});
vm.runInContext(source.split("document.addEventListener('click',async e=>{")[0],ctx,{filename:'frontend/static/app.js'});
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
 repro:['Reproducibility Engine','Make every experiment reproducible']
};
for(const entry of Object.entries(routes)){
 const view=entry[0],heading=entry[1][0],subtitle=entry[1][1];
 test(view+' renders distinct no-dataset content',()=>{
  const markup=vm.runInContext('state.view='+JSON.stringify(view)+';RENDER[state.view]()',ctx);
  assert.equal(typeof markup,'string');
  assert.ok(markup.includes('<h1>'+heading+'</h1>'));
  assert.ok(markup.includes('<h2>'+subtitle+'</h2>'));
  assert.ok(markup.includes('data-empty-view="'+view+'"'));
  assert.ok(!markup.includes('Find what the data hides.'));
  assert.ok(markup.includes('data-action="demo"'));
  assert.ok(markup.includes('data-action="import"'));
 });
}
test('labBase returns a consistent object when the dataset is absent',()=>{
 for(const view of ['shortcut','counterfactual','cross_dataset','impact']){
  const markup=vm.runInContext('state.view='+JSON.stringify(view)+';labBase("lab","lab","desc",'+JSON.stringify(view)+')',ctx);
  assert.equal(typeof markup.html,'string');assert.equal(markup.e,null);
 }
});