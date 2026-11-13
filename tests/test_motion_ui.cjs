/* UI motion checks: no dependencies, no fake research progress. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {test}=require('node:test'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..','frontend','static');
const source=fs.readFileSync(path.join(root,'app.js'),'utf8');
const css=fs.readFileSync(path.join(root,'motion.css'),'utf8');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
function context(){
 const main={innerHTML:'',attrs:{},setAttribute(k,v){this.attrs[k]=v}};
 const topbar={classList:{toggle(k,v){topbar.loading=v}}};
 const crumb={textContent:''};
 const dom={'#main':main,'.topbar':topbar,'#crumbCurrent':crumb};
 const ctx=vm.createContext({document:{querySelectorAll:()=>[],querySelector:(s)=>dom[s]||null},window:{},console});
 vm.runInContext(source.split("document.addEventListener('click',async e=>{")[0],ctx,{filename:'app.js'});
 return {ctx,main,topbar,crumb};
}
test('loader is indeterminate and accessible',()=>{
 const {ctx}=context(),h=vm.runInContext('workspaceLoader("Retrieving evidence")',ctx);
 assert.match(h,/role="status" aria-live="polite"/);
 assert.match(h,/No simulated progress or results/);
 assert.doesNotMatch(h,/aria-valuenow=|100%/);
 assert.match(html,/aria-busy="true"/);
 assert.match(html,/href="\/assets\/motion\.css"/);
});
test('reduced-motion overrides and feedback styles are present',()=>{
 for(const name of ['workspace-page','workspaceShimmer','workspaceRail','toastSlide','dialogEnter','loader-orbit','prefers-reduced-motion:reduce','.btn.is-pending'])
 assert.ok(css.includes(name),name);
});
test('render clears busy state',async()=>{
 const {ctx,main,topbar}=context();
 await vm.runInContext('render()',ctx);
 assert.equal(main.attrs['aria-busy'],'false');assert.equal(topbar.loading,false);assert.match(main.innerHTML,/workspace-page/);
});
test('out-of-order requests preserve latest view',async()=>{
 const {ctx,main}=context();ctx.pending=[];
 vm.runInContext('loadView=()=>new Promise(resolve=>pending.push(resolve))',ctx);
 const first=vm.runInContext('state.view="audit";render()',ctx);
 const second=vm.runInContext('state.view="dna";render()',ctx);
 ctx.pending[1]();await second;
 assert.match(main.innerHTML,/<h1>Dataset DNA<\/h1>/);
 ctx.pending[0]();await first;
 assert.match(main.innerHTML,/<h1>Dataset DNA<\/h1>/);
 assert.equal(main.attrs['aria-busy'],'false');
});
