/** Upload-phase tests: no npm dependencies or network access. */
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const test=require('node:test'), assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../frontend/static/app.js'),'utf8');
const renderSource=source.split("document.addEventListener('click',async e=>{")[0];
function context(status=200,responseText=JSON.stringify({dataset_id:'test-dataset',message:'ok'})){
 const instances=[];
 class FakeXHR{
  constructor(){this.handlers={};this.upload={handlers:{},addEventListener:(name,fn)=>this.upload.handlers[name]=fn};this.status=status;this.responseText=responseText;this.headers={};instances.push(this)}
  open(method,url){this.method=method;this.url=url}
  setRequestHeader(k,v){this.headers[k]=v}
  addEventListener(name,fn){this.handlers[name]=fn}
  send(body){this.body=body}
  emit(name,event={}){this.handlers[name](event)}
 }
 const ctx=vm.createContext({XMLHttpRequest:FakeXHR,storage:{get:()=>null},document:{querySelectorAll:()=>[]},window:{},console});
 vm.runInContext(renderSource,ctx,{filename:'app.js'});
 return {ctx,instances};
}
test('real uploaded bytes drive only the transfer percentage',async()=>{
 const {ctx,instances}=context();const progresses=[],phases=[];
 const p=vm.runInContext('uploadResearchDataset({dataset:"data"},globalProgress,globalPhase)',Object.assign(ctx,{globalProgress:n=>progresses.push(n),globalPhase:v=>phases.push(v)}));
 const x=instances[0];
 assert.equal(x.method,'POST');assert.equal(x.url,'/api/datasets/import');
 x.upload.handlers.progress({lengthComputable:true,loaded:333,total:1000});
 assert.deepEqual(progresses,[33]);
 x.upload.handlers.load();assert.deepEqual(phases,['indexing']);
 x.emit('load');const result=await p;assert.equal(result.dataset_id,'test-dataset');
});
test('validation errors are shown instead of being reported as success',async()=>{
 const {ctx,instances}=context(422,JSON.stringify({detail:'NPZ size cap exceeded'}));
 const p=vm.runInContext('uploadResearchDataset({},()=>{},()=>{})',ctx);
 instances[0].emit('load');await assert.rejects(p,/size cap exceeded/);
});
test('import UI provides upload, indexing, success, and failure states',()=>{
 for(const marker of ['Uploading dataset','Validating and indexing','Dataset imported successfully','Import did not finish','role="status" aria-live="polite"','id="importProgress"','View Dataset DNA','NPZ files up to 256 MiB','ZIP files up to 150 MiB']) {
  assert.ok(source.includes(marker),`missing state: ${marker}`);
 }
 const css=fs.readFileSync(path.join(__dirname,'../frontend/static/styles.css'),'utf8');
 assert.ok(css.includes('prefers-reduced-motion'));
 assert.ok(css.includes('importSweep'));
});

test('different archive types use their separate hard limits',()=>{
 const {ctx}=context();
 const npz=vm.runInContext("uploadLimitMiB('pathmnist.npz')",ctx);
 const zip=vm.runInContext("uploadLimitMiB('images.zip')",ctx);
 assert.equal(npz,256);
 assert.equal(zip,150);
 assert.equal(vm.runInContext("uploadLimitMiB('PATHMNIST.NPZ')",ctx),256);
 assert.ok(npz>zip);
});
