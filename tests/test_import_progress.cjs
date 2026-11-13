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

test('large import uploader transfers only bounded chunks and reports server-confirmed bytes',async()=>{
 const total=17*1024*1024;
 const offsets=[];const steps=[];let accepted=0,processed=false;
 const fakeFile={name:'large.zip',size:total,
   slice:(a,b)=>({size:b-a,start:a,end:b})};
 const response=(obj)=>({ok:true,status:200,headers:{get:()=>'application/json'},json:async()=>obj});
 const fakeFetch=async(url,options={})=>{
  if(url==='/api/datasets/import-large'&&options.method==='POST')
   return response({id:'a'.repeat(32),phase:'uploading',chunk_bytes:8*1024*1024,files:[{name:'large.zip',size:total,received:0}]});
  if(url.includes('/files/0?offset=')&&options.method==='PUT'){
   const offset=Number(url.split('offset=')[1]);offsets.push(offset);
   assert.equal(offset,accepted);
   assert.ok(options.body.size<=8*1024*1024);
   accepted+=options.body.size;
   return response({files:[{received:accepted}],received_bytes:accepted,total_bytes:total});
  }
  if(url.endsWith('/process')&&options.method==='POST'){
   assert.equal(accepted,total);processed=true;return response({phase:'queued'});
  }
  if(url.includes('/api/datasets/import-large/')&&(!options.method||options.method==='GET'))
   return response({phase:processed?'completed':'uploading',dataset_id:processed?'demo':null,
      files:[{name:'large.zip',size:total,received:accepted}],received_bytes:accepted,total_bytes:total});
  throw Error('Unexpected request: '+url);
 };
 const values={};
 const ctx=vm.createContext({XMLHttpRequest:class{},storage:{get:()=>null,set:(where,key,value)=>{values[key]=value}},
  fetch:fakeFetch,document:{querySelectorAll:()=>[]},window:{},console,setTimeout:(fn)=>fn()});
 vm.runInContext(renderSource,ctx,{filename:'app.js'});
 const result=await vm.runInContext('uploadLargeResearchDataset([file],{name:"Sample",source:"Local"},onProgress,onIndex)',
  Object.assign(ctx,{file:fakeFile,onProgress:x=>steps.push(x),onIndex:()=>{}}));
 assert.equal(result.dataset_id,'demo');
 assert.deepEqual(offsets,[0,8*1024*1024,16*1024*1024]);
 assert.equal(accepted,total);
 assert.equal(steps.at(-1),100);
 assert.equal(values['mdf-large-upload-session'],'');
});

test('HAM10000 large uploader includes metadata and part integrity instructions',()=>{
 assert.ok(source.includes('HAM10000_metadata.csv'));
 assert.ok(source.includes('HAM10000_images_part_1.zip'));
 assert.ok(source.includes('HAM10000_images_part_2.zip'));
 assert.ok(source.includes('Import large ZIP or HAM10000'));
 assert.ok(source.includes('Resume previous import'));
 assert.ok(source.includes('Discard staged files'));
});
