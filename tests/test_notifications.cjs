/** Regression coverage for the analysis notifications inbox. No npm dependencies. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const test=require('node:test'),assert=require('node:assert/strict');
const src=fs.readFileSync(path.join(__dirname,'../frontend/static/app.js'),'utf8')
 .split("document.addEventListener('click',async e=>{")[0];
function harness(){
 const data=new Map(),ind={hidden:true};
 const localStorage={getItem:key=>data.get(key)||null,setItem:(key,value)=>data.set(key,String(value))};
 const ctx=vm.createContext({document:{querySelectorAll:()=>[],querySelector:sel=>sel==='#jobIndicator'?ind:null},
  window:{localStorage},console});
 vm.runInContext(src,ctx,{filename:'app.js'});
 const rows=[
  {id:'failed1',kind:'baseline',status:'failed',error:'Training failed: insufficient test records',message:'Analysis failed'},
  {id:'done1',kind:'audit',status:'completed',message:'Completed successfully'},
  {id:'active1',kind:'counterfactual',status:'running',message:'Testing',progress:42},
 ];
 ctx.testRows=rows;
 return {ctx,rows,ind,data};
}
test('inbox exposes per-item and clear-all controls only for finished jobs',()=>{
 const {ctx}=harness();
 const html=vm.runInContext('renderJobInbox(testRows)',ctx);
 assert.match(html,/Clear notifications \(2\)/);
 assert.match(html,/data-dismiss-job="failed1"/);
 assert.match(html,/data-dismiss-job="done1"/);
 assert.doesNotMatch(html,/data-dismiss-job="active1"/);
 assert.match(html,/data-cancel-job="active1"/);
 assert.match(html,/Show recent history/);
});
test('clearing notifications hides failed/completed while keeping active jobs and evidence',()=>{
 const {ctx,data}=harness();
 vm.runInContext("saveClearedJobIds(new Set(['failed1','done1']))",ctx);
 let html=vm.runInContext('renderJobInbox(testRows)',ctx);
 assert.doesNotMatch(html,/Training failed: insufficient test records/);
 assert.match(html,/Testing/);
 assert.match(html,/Clear notifications \(0\)/);
 const history=vm.runInContext('renderJobInbox(testRows,true)',ctx);
 assert.match(history,/Training failed: insufficient test records/);
 assert.match(history,/Cleared/);
 assert.ok(data.has('mdf-cleared-job-notifications-v1'));
});
test('cleared notices persist on reload, invalid storage is safe, new jobs remain visible',()=>{
 const {ctx,data}=harness();
 vm.runInContext("saveClearedJobIds(new Set(['done1']))",ctx);
 assert.match(vm.runInContext('renderJobInbox(testRows)',ctx),/Training failed/);
 assert.doesNotMatch(vm.runInContext('renderJobInbox(testRows)',ctx),/Completed successfully/);
 data.set('mdf-cleared-job-notifications-v1','bad JSON');
 assert.match(vm.runInContext('renderJobInbox(testRows)',ctx),/Completed successfully/);
});
test('bell indicator includes active and uncleared failed jobs, not cleared notices',()=>{
 const {ctx,ind}=harness();
 vm.runInContext("updateJobIndicator(testRows)",ctx);
 assert.equal(ind.hidden,false);
 vm.runInContext("saveClearedJobIds(new Set(['failed1','done1']))",ctx);
 vm.runInContext("updateJobIndicator(testRows)",ctx);
 assert.equal(ind.hidden,false); // active job is still visible
 vm.runInContext("updateJobIndicator(testRows.filter(j=>j.status!=='running'))",ctx);
 assert.equal(ind.hidden,true);
});
test('clear-all actions cannot mutate or delete backend job history',async()=>{
 const {ctx}=harness();
 vm.runInContext("api=async function(path){if(path==='/api/jobs')return testRows;if(path==='/api/jobs/active1')return testRows[2];return null};openJobs=async function(){};toast=function(){}",ctx);
 await vm.runInContext("clearJobNotifications()",ctx);
 const inbox=vm.runInContext("renderJobInbox(testRows)",ctx);
 assert.doesNotMatch(inbox,/Training failed/);
 assert.match(inbox,/Testing/);
 await vm.runInContext("clearJobNotification('active1')",ctx);
 const after=vm.runInContext("renderJobInbox(testRows)",ctx);
 assert.match(after,/Testing/);
});
