/* MedData Forensics. Dependency-free, accessible local research workbench UI. */
'use strict';
const ICONS={
 layout:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
 database:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
 search:'<circle cx="10" cy="10" r="6.5"/><path d="m15 15 5.5 5.5"/>',
 network:'<circle cx="6" cy="6" r="3"/><circle cx="18" cy="7" r="3"/><circle cx="12" cy="19" r="3"/><path d="m9 6 6 1M8 9l3 7M16 10l-3 6"/>',
 check:'<path d="M5 12l5 5L20 7"/><circle cx="12" cy="12" r="10"/>',
 scan:'<path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m13-5v3a2 2 0 0 1-2 2h-3"/><circle cx="12" cy="12" r="3"/>',
 layers:'<path d="m12 2 9 5-9 5-9-5 9-5Zm-9 10 9 5 9-5M3 17l9 5 9-5"/>',
 git:'<circle cx="6" cy="3" r="2"/><circle cx="6" cy="21" r="2"/><circle cx="18" cy="6" r="2"/><path d="M6 5v14m0-9c0-4 12 1 12-2"/>',
 chart:'<path d="M3 3v18h18M7 16l4-5 4 3 5-8"/>',activity:'<path d="M2 12h4l3-8 5 16 3-8h5"/>',
 flask:'<path d="M9 3h6M10 3v7L4 19a2 2 0 0 0 2 3h12a2 2 0 0 0 2-3l-6-9V3M8 16h8"/>',
 shield:'<path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-4"/>',
 plus:'<path d="M12 5v14M5 12h14"/>',bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 6-3 9h18c0-3-3-2-3-9M10 21h4"/>',
 x:'<path d="M18 6 6 18M6 6l12 12"/>',menu:'<path d="M4 7h16M4 12h16M4 17h16"/>',
 arrow:'<path d="M5 12h14m-7-7 7 7-7 7"/>',down:'<path d="m7 10 5 5 5-5"/>',info:'<circle cx="12" cy="12" r="10"/><path d="M12 11v6m0-10v.5"/>',
 upload:'<path d="M12 16V3m-5 5 5-5 5 5M4 16v4h16v-4"/>',download:'<path d="M12 3v13m-5-5 5 5 5-5M4 17v4h16v-4"/>',
 play:'<path d="m8 5 11 7-11 7V5Z"/>',clock:'<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
 file:'<path d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm7 0v6h6M9 14h7m-7 4h7"/>',
 alert:'<path d="M12 3 2 21h20L12 3ZM12 9v5m0 3v.5"/>',eye:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
 image:'<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 16-5-5-10 10"/>',
 rotate:'<path d="M3 12a9 9 0 0 1 15-7l3 3m0-6v6h-6M21 12a9 9 0 0 1-15 7l-3-3m0 6v-6h6"/>',
 filter:'<path d="M4 7h16M7 12h10m-7 5h4"/>',lock:'<rect x="5" y="10" width="14" height="12" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>'
};
function icon(name){return `<span class="icon" aria-hidden="true"><svg viewBox="0 0 24 24">${ICONS[name]||ICONS.info}</svg></span>`;}
document.querySelectorAll('[data-icon]').forEach(n=>n.innerHTML=icon(n.dataset.icon));
const $=s=>document.querySelector(s);
const NPZ_UPLOAD_LIMIT_MIB=256;
const ZIP_UPLOAD_LIMIT_MIB=150;
function uploadLimitMiB(filename){return String(filename||'').toLowerCase().endsWith('.npz')?NPZ_UPLOAD_LIMIT_MIB:ZIP_UPLOAD_LIMIT_MIB;}
const storage={get:(kind,key)=>{try{return window[kind].getItem(key)}catch{return null}},set:(kind,key,value)=>{try{window[kind].setItem(key,value)}catch{}}};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=x=>x==null?'—':(Number(x)*100).toFixed(1)+'%';
const number=x=>Number(x||0).toLocaleString('en-US');
const short=x=>String(x||'').length>24?String(x).slice(0,12)+'…'+String(x).slice(-8):String(x||'');
const title=s=>s.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
const state={view:'overview',datasets:[],did:'',detail:null,overview:null,findings:null,analysisJob:null,activeFilters:{kind:'',status:''},samplePage:1,counterPage:1,counterStrength:40,counterMode:'brightness',reviewPage:1,modal:null,graphUi:{search:'',severity:'all',links:'all',zoom:1},failureCell:'',dnaFilters:{split:'',label:'',search:''}};
let lastFocused=null, refreshTimer=null;
async function api(path,opt={}){
  const headers={...(opt.headers||{})}; const token=storage.get('sessionStorage','mdf-token');if(token)headers['X-MDF-Token']=token;
  if(opt.body&&!(opt.body instanceof FormData))headers['Content-Type']='application/json';
  const res=await fetch(path,{...opt,headers,cache:'no-store'});
  const type=res.headers.get('content-type')||'';
  if(!res.ok){let m='Request failed: '+res.status;try{const e=await res.json();m=e.detail||m}catch{}throw Error(Array.isArray(m)?JSON.stringify(m):m)}
  return type.includes('json')?res.json():res.text();
}
function toast(message,error=false){const el=document.createElement('div');el.className='toast'+(error?' error':'');el.innerHTML=icon(error?'alert':'check')+' <span>'+esc(message)+'</span>';$('#toastStack').append(el);setTimeout(()=>el.remove(),6000);}
let datasetImportInProgress=false;
function openModal(name,body){if(datasetImportInProgress)return;lastFocused=document.activeElement;$('#modalTitle').textContent=name;$('#modalBody').innerHTML=body;$('#modalBackdrop').hidden=false;$('#modalClose').focus();document.body.style.overflow='hidden';}
function closeModal(){if(datasetImportInProgress||$('#modalBackdrop').hidden)return;$('#modalBackdrop').hidden=true;document.body.style.overflow='';if(lastFocused&&lastFocused.focus)lastFocused.focus();}
/** Real transfer progress; server-side indexing deliberately uses an indeterminate state. */
function uploadResearchDataset(formData,onProgress,onPhase){return new Promise((resolve,reject)=>{
 const xhr=new XMLHttpRequest();
 xhr.open('POST','/api/datasets/import',true);
 xhr.timeout=0; // CPU indexing is synchronous on the server; do not guess an ETA.
 const token=storage.get('sessionStorage','mdf-token');if(token)xhr.setRequestHeader('X-MDF-Token',token);
 xhr.setRequestHeader('Cache-Control','no-store');
 xhr.upload.addEventListener('progress',e=>{if(e.lengthComputable&&e.total>0)onProgress(Math.min(100,Math.round(100*e.loaded/e.total)));});
 xhr.upload.addEventListener('load',()=>onPhase('indexing'));
 xhr.addEventListener('load',()=>{
  let body={};try{body=JSON.parse(xhr.responseText||'{}')}catch{}
  if(xhr.status>=200&&xhr.status<300&&body.dataset_id){resolve(body);return;}
  let msg=body.detail||`Import failed (HTTP ${xhr.status}).`;
  reject(Error(typeof msg==='string'?msg:JSON.stringify(msg)));
 });
 xhr.addEventListener('error',()=>reject(Error('Connection interrupted. Check that the local server is running; confirm whether the dataset was imported before retrying.')));
 xhr.addEventListener('abort',()=>reject(Error('The upload was interrupted. Verify the dataset list before retrying.')));
 xhr.send(formData);
});}

function empty(name,desc,action=''){return `<div class="empty-state"><div class="empty-icon">${icon('database')}</div><h3>${esc(name)}</h3><p>${esc(desc)}</p>${action}</div>`;}
function pill(text,type=''){return `<span class="pill ${type}">${esc(text)}</span>`;}
function head(eyebrow,name,description,actions=''){return `<header class="page-head"><div><div class="eyebrow">${esc(eyebrow)}</div><h1>${esc(name)}</h1><p class="subtitle">${esc(description)}</p></div><div class="page-actions">${actions}</div></header>`;}
function btn(label,act,kind='',extra=''){return `<button type="button" class="btn ${kind}" data-action="${esc(act)}" ${extra}>${label}</button>`;}
function notice(text,variant=''){return `<div class="info-stripe ${variant}">${icon(variant==='warn'?'alert':'info')}<div>${esc(text)}</div></div>`;}
function stat(label,value,desc){return `<div class="card stat-card"><div class="kicker">${esc(label)}</div><div class="stat-number">${esc(value)}</div><div class="stat-meta">${esc(desc)}</div></div>`;}
function bars(data,max=0,filter=''){
 const entries=Object.entries(data||{}).sort((a,b)=>Number(b[1])-Number(a[1]));
 const peak=max||Math.max(1,...entries.map(x=>Number(x[1])||0));
 return entries.length?entries.slice(0,20).map(([k,v])=>{
  const middle='<span class="bar-label" title="'+esc(k)+'">'+esc(k)+'</span>'+
   '<span class="meter" aria-hidden="true"><span class="meter-fill" style="width:'+Math.max(0,Math.min(100,100*Number(v)/peak))+'%"></span></span>'+
   '<span class="bar-val">'+number(v)+'</span>';
  return filter?'<button class="bar-row chart-bar'+(state.dnaFilters?.[filter]===k?' is-selected':'')+'" type="button" data-dna-chart="'+esc(filter)+
   '" data-dna-value="'+esc(k)+'" aria-pressed="'+(state.dnaFilters?.[filter]===k)+'" aria-label="Filter research images by '+esc(filter)+' '+esc(k)+', '+number(v)+' records">'+middle+'</button>':
   '<div class="bar-row">'+middle+'</div>';
 }).join(''):'<p class="fine">No distribution available.</p>';
}

function card(title,inner,side=''){return `<section class="card card-padded"><div class="card-title"><h3>${esc(title)}</h3>${side}</div>${inner}</section>`;}
function sampleCard(s){return `<button type="button" class="record" data-sample="${esc(s.id)}"><img loading="lazy" alt="Dataset image sample ${esc(s.sample_id)}" src="${esc(s.image_url)}"><div class="record-content"><span class="record-name">${esc(s.sample_id)}</span><span class="record-label">${esc(s.label)} · ${esc(s.split)}</span></div></button>`;}
function findingRow(f){const statusType=f.status==='confirmed'?'green':f.status==='rejected'?'red':f.status==='uncertain'?'amber':'';return `<button type="button" class="finding-row" data-finding="${esc(f.id)}"><span class="severity-line ${esc(f.severity)}"></span><span class="main-finding"><strong>${esc(f.title)}</strong><p>${esc(f.detail)}</p></span><span class="finding-end">${pill(f.status,statusType)}<span class="tiny">${(f.priority*100).toFixed(0)} priority</span></span>${icon('arrow')}</button>`;}
function metric(v){return typeof v==='number'?v.toFixed(3):'—';}
function bestExp(kind){return state.detail?.experiments?.find(e=>e.kind===kind&&e.status==='completed'&&(kind!=='baseline'||e.checkpoint_available!==false));}
const EMPTY_GUIDES={
 dna:{icon:'database',label:'DATASET PROVENANCE',title:'Explore the anatomy of a dataset',description:'Inspect origin, license, recorded labels, image dimensions, splits and immutable version history.',steps:['Import an authorized image dataset or make a synthetic sandbox','Review source metadata, dataset fingerprints and split distributions','Inspect individual image records and dataset lineage']},
 audit:{icon:'search',label:'DATASET INTEGRITY',title:'Find hidden data-quality risks',description:'Look for exact or near-duplicate images, cross-split overlap, suspicious labels and inconsistent sources.',steps:['Create or import an image classification dataset','Run the forensic detector suite','Open each finding to inspect the evidence before review']},
 graph:{icon:'network',label:'EVIDENCE RELATIONSHIPS',title:'Connect findings to their source images',description:'Visualize which records, splits, and forensic findings are linked by detector evidence.',steps:['Choose a research dataset','Run a forensic audit to generate findings','Explore the evidence network and inspect individual links']},
 review:{icon:'check',label:'RESEARCHER VERIFICATION',title:'Review findings without altering raw data',description:'Record confirmations, rejections and uncertainty with persistent reviewer notes.',steps:['Load a dataset and run a forensic audit','Inspect the underlying evidence for each finding','Save traceable decisions and review history']},
 shortcut:{icon:'scan',label:'MODEL RELIABILITY',title:'Investigate possible visual shortcuts',description:'Test how frozen-model predictions change when a controlled image region is masked.',steps:['Load a research dataset with a suitable test partition','Train the CPU baseline in Model Failure Explorer','Run the shortcut-sensitivity probe and inspect limitations']},
 counterfactual:{icon:'layers',label:'CONTROLLED IMAGE TESTS',title:'See how image changes affect predictions',description:'Compare one research image with controlled brightness, blur and corner-mask variants.',steps:['Load or create a dataset and train the CPU baseline','Choose a test image from the collection','Run perturbations and compare confidence and prediction changes']},
 cross:{icon:'git',label:'EXTERNAL GENERALIZATION',title:'Compare compatible research collections',description:'Run a frozen model against a second dataset only when labels and modality are compatible.',steps:['Load a source dataset and train its baseline','Import a distinct, compatible target dataset','Run an external evaluation and review comparability limits']},
 impact:{icon:'chart',label:'AUDIT INTERVENTIONS',title:'Measure the effect of reviewed data issues',description:'Compare model results before and after excluding reviewer-confirmed training samples.',steps:['Load a dataset and run an audit','Record evidence-backed decisions in Review Center','Run removal-only ablation using the same frozen test set']},
 failures:{icon:'activity',label:'MODEL PERFORMANCE',title:'Understand where the baseline fails',description:'Inspect misclassifications, class performance, confidence calibration and recorded source groups.',steps:['Load a research dataset with labeled splits','Train the CPU-friendly baseline model','Inspect errors, confusion matrix and subgroup measurements']},
 repro:{icon:'flask',label:'RESEARCH TRACEABILITY',title:'Make every experiment reproducible',description:'Preserve experiment manifests, fixed seeds, lineage, historical runs and transparent report exports.',steps:['Load or create a dataset with a provenance record','Run one or more forensic or model experiments','Inspect manifests and export the research evidence']}
};
/** Each empty workspace is a useful explainer, not a recycled dataset-required screen. */
function emptyWorkspaceVisual(view){
 const sample=`<div class="phantom-example" aria-label="Illustrative synthetic geometric image, not medical data"><span class="phantom-disc"></span><span class="phantom-bars"></span><span class="phantom-corner"></span></div>`;
 const block=(tag,heading,content)=>`<div class="empty-visual-block"><div class="mini-eyebrow">${tag}</div><strong>${heading}</strong><p>${content}</p></div>`;
 switch(view){
 case 'dna': return `<section class="empty-preview preview-dna" data-preview-type="dna"><div class="empty-preview-header"><span class="mini-eyebrow">DATASET DNA / STRUCTURE VIEW</span>${pill('Metadata schema · illustration')}</div><div class="dna-schema"><div class="dna-source">${icon('database')}<span><strong>Research collection</strong><small>Source, license, modality</small></span></div><div class="dna-branches"><div><b>01</b><strong>Identity</strong><small>Manifest fingerprint, record count</small></div><div><b>02</b><strong>Composition</strong><small>Classes, split policy, image dimensions</small></div><div><b>03</b><strong>Lineage</strong><small>Original version → derived experiment</small></div></div></div>${notice('Provenance metadata must come from the actual source. A lesion ID is not proof of patient identity.')}</section>`;
 case 'audit':return `<section class="empty-preview preview-audit" data-preview-type="audit"><div class="empty-preview-header"><span class="mini-eyebrow">FORENSIC AUDIT / DETECTOR PLAN</span>${pill('No scan executed')}</div><div class="audit-stage-grid">${[['01','Exact copies','SHA-256 / pixel fingerprints'],['02','Similar images','Perceptual hash and visual similarity'],['03','Split contamination','Cross-split or shared-group overlap'],['04','Label concerns','Training-only out-of-fold disagreement']].map(x=>`<div class="audit-stage"><span>${x[0]}</span><strong>${x[1]}</strong><small>${x[2]}</small></div>`).join('')}</div><div class="preview-footnote">Findings are hypotheses until a researcher checks their underlying evidence. Detectors do not automatically correct clinical labels.</div></section>`;
 case 'graph':return `<section class="empty-preview preview-graph" data-preview-type="graph"><div class="empty-preview-header"><span class="mini-eyebrow">EVIDENCE GRAPH / LINK TYPES</span>${pill('Illustrative relationships')}</div><svg class="graph-illustration" viewBox="0 0 720 270" role="img" aria-label="Conceptual network connecting two example image samples to one possible duplicate finding and one possible split overlap finding"><path d="M155 73L345 125L560 73M155 205L345 125L560 205M345 125L560 205" stroke="currentColor" stroke-width="2" stroke-opacity=".28" fill="none" stroke-dasharray="5 7"/><g class="sample-node"><rect x="32" y="47" width="165" height="55" rx="12"/><text x="114" y="80" text-anchor="middle">Sample A (train)</text></g><g class="sample-node"><rect x="32" y="178" width="165" height="55" rx="12"/><text x="114" y="211" text-anchor="middle">Sample B (test)</text></g><g class="finding-node"><rect x="268" y="99" width="155" height="55" rx="12"/><text x="345" y="131" text-anchor="middle">Duplicate link</text></g><g class="finding-node"><rect x="483" y="47" width="200" height="55" rx="12"/><text x="583" y="80" text-anchor="middle">Split overlap</text></g><g class="sample-node"><rect x="483" y="178" width="200" height="55" rx="12"/><text x="583" y="211" text-anchor="middle">Evidence relationship</text></g></svg><div class="preview-footnote">When you run an audit, real nodes represent imported samples and detector findings. Links do not prove shared patient identity.</div></section>`;
 case 'review':return `<section class="empty-preview preview-review" data-preview-type="review"><div class="empty-preview-header"><span class="mini-eyebrow">REVIEW CENTER / DECISION STATES</span>${pill('No pending cases')}</div><div class="review-states">${[['Suspected','Detector flag; no judgment yet','review-pending'],['Confirmed','Reviewer accepts the specific concern','review-confirmed'],['Rejected','Evidence does not support this flag','review-rejected'],['Uncertain','More evidence is required','review-uncertain']].map(x=>`<div class="review-state ${x[2]}"><span class="review-dot"></span><div><strong>${x[0]}</strong><p>${x[1]}</p></div></div>`).join('')}</div><div class="preview-footnote">Reviewer notes and timestamps form an append-only audit history. A confirmed concern is not a medical diagnosis.</div></section>`;
 case 'shortcut':return `<section class="empty-preview preview-shortcut" data-preview-type="shortcut"><div class="empty-preview-header"><span class="mini-eyebrow">SHORTCUT INSPECTOR / CONTROLLED PROBE</span>${pill('Synthetic example')}</div><div class="paired-phantoms"><div><span class="comparison-title">Original synthetic pattern</span>${sample}</div><div><span class="comparison-title">Corner region masked</span><div class="mask-phantom">${sample}<div class="mask-block" aria-hidden="true"></div></div></div></div><div class="protocol-row">${block('A','Freeze the model','Keep predictions from the same trained checkpoint.')}${block('B','Apply a mask','Alter one consistent region of test images.')}${block('C','Compare behavior','Measure flip rate and confidence variation.')}</div>${notice('A prediction change after masking does not, by itself, establish a causal shortcut.','warn')}</section>`;
 case 'counterfactual':return `<section class="empty-preview preview-counterfactual" data-preview-type="counterfactual"><div class="empty-preview-header"><span class="mini-eyebrow">COUNTERFACTUAL LAB / LIVE VISUAL PREVIEW</span>${pill('Synthetic illustration · no AI inference')}</div><div class="paired-phantoms"><div><span class="comparison-title">Control image</span>${sample}</div><div><span class="comparison-title">Transformed image</span><div id="counterfactualPreview" class="counterfactual-visual">${sample}<div id="counterfactualMask" class="mask-block" hidden></div></div></div></div><div class="preview-controls"><div class="field"><label for="counterfactualMode">Image transformation</label><select id="counterfactualMode" class="select"><option value="brightness">Brightness</option><option value="blur">Gaussian-like CSS blur preview</option><option value="mask">Corner masking</option></select></div><div class="field"><label for="counterfactualAmount">Strength <output id="counterfactualReadout" for="counterfactualAmount">40%</output></label><input id="counterfactualAmount" type="range" min="0" max="100" value="40" step="5"/></div></div><div class="preview-footnote">Try the controls here. Dataset-based experiments run image transformations on a trained model and report measured prediction changes.</div></section>`;
 case 'cross':return `<section class="empty-preview preview-cross" data-preview-type="cross"><div class="empty-preview-header"><span class="mini-eyebrow">CROSS-DATASET / COMPATIBILITY GATE</span>${pill('Requires two collections')}</div><div class="cross-comparison"><div class="cross-box"><span class="mini-eyebrow">SOURCE COLLECTION</span><strong>Train and freeze a model</strong><p>Declared image modality and label vocabulary</p></div><div class="cross-arrow" aria-hidden="true">${icon('arrow')}</div><div class="cross-box"><span class="mini-eyebrow">TARGET COLLECTION</span><strong>Independent evaluation</strong><p>Distinct provenance and compatible label semantics</p></div></div><div class="check-matrix"><div>${icon('check')} Same modality?</div><div>${icon('check')} Same class meaning?</div><div>${icon('check')} No dataset overlap?</div><div>${icon('check')} Frozen model?</div></div>${notice('Identical class names do not guarantee clinical or methodological comparability.','warn')}</section>`;
 case 'impact':return `<section class="empty-preview preview-impact" data-preview-type="impact"><div class="empty-preview-header"><span class="mini-eyebrow">IMPACT SIMULATOR / COMPARISON DESIGN</span>${pill('No result computed')}</div><div class="impact-lanes"><div class="impact-lane"><span class="mini-eyebrow">CONTROL TRAINING</span><strong>Original training records</strong><span class="impact-measure">F1: —</span></div><div class="impact-mid">${icon('arrow')}<small>Reviewer-confirmed exclusions</small></div><div class="impact-lane"><span class="mini-eyebrow">REVIEWED TRAINING</span><strong>Remove only confirmed issues</strong><span class="impact-measure">F1: —</span></div></div><div class="impact-test">${icon('lock')} <div><strong>Same frozen test set</strong><p>Comparison is invalid if test membership, labels, or evaluation protocol change between runs.</p></div></div></section>`;
 case 'failures':return `<section class="empty-preview preview-failures" data-preview-type="failures"><div class="empty-preview-header"><span class="mini-eyebrow">FAILURE EXPLORER / METRIC INTERPRETATION</span>${pill('Illustrative matrix · no scores')}</div><div class="failure-layout"><div class="confusion-concept" role="img" aria-label="Conceptual two-class confusion matrix: true negatives, false positives, false negatives, and true positives"><span>True negative<br/>TN</span><span>False positive<br/>FP</span><span>False negative<br/>FN</span><span>True positive<br/>TP</span></div><div class="failure-legend"><strong>What the real analysis reveals</strong><p>Which supplied labels disagree with the classifier, how errors cluster by class, and whether probabilities are well calibrated.</p><ul><li>Per-class precision and recall</li><li>Confusion matrix from a held-out test set</li><li>Confidence calibration and subgroup summaries</li></ul></div></div></section>`;
 case 'repro':return `<section class="empty-preview preview-repro" data-preview-type="repro"><div class="empty-preview-header"><span class="mini-eyebrow">REPRODUCIBILITY / EXPERIMENT CONTRACT</span>${pill('Example manifest format')}</div><div class="manifest-panel"><div class="manifest-file">${icon('file')} run_manifest.yaml <span>Illustrative only</span></div><pre>dataset_sha256: &lt;computed-after-import&gt;\nrandom_seed: 42\nmodel: cpu_baseline\ntest_policy: frozen\naudit_version: recorded\nreview_history: append_only</pre></div><div class="repro-benefits"><span>${icon('check')} Fixed seeds</span><span>${icon('check')} Traceable findings</span><span>${icon('check')} Independent test partitions</span><span>${icon('check')} Exportable evidence</span></div></section>`;
 default:return '';
 }
}
function needDataset(){
 const g=EMPTY_GUIDES[state.view]||EMPTY_GUIDES.dna;
 return `<div class="module-workspace" data-empty-view="${esc(state.view)}">
 <div class="module-heading"><div class="eyebrow">${esc(g.label)} · WORKSPACE GUIDE</div><h2>${esc(g.title)}</h2><p>${esc(g.description)}</p></div>
 ${emptyWorkspaceVisual(state.view)}
 <div class="module-next"><div class="module-next-summary"><span class="module-next-icon">${icon(g.icon)}</span><div><strong>Ready to investigate?</strong><p>No dataset is currently selected. This preview explains the method; actual findings will appear only after you load research images.</p></div></div><div class="module-next-actions">${btn(icon('plus')+' Create synthetic dataset','demo','btn-primary')}${btn(icon('upload')+' Import real research data','import')}</div></div>
 <section class="module-steps"><div class="section-heading">How to use this module</div><div class="module-step-grid">${g.steps.map((step,i)=>`<div class="module-step"><span>0${i+1}</span><p>${esc(step)}</p></div>`).join('')}</div></section>
 </div>`;
}
function updateCounterfactualPreview(){
 const target=$('#counterfactualPreview'),mode=$('#counterfactualMode'),slider=$('#counterfactualAmount');if(!target||!mode||!slider)return;
 const amount=Math.min(100,Math.max(0,Number(slider.value)||0)),m=mode.value;
 const image=target.querySelector('img')||target;image.style.filter=m==='brightness'?`brightness(${(1+amount*.00625).toFixed(2)})`:m==='blur'?`blur(${(amount*.034).toFixed(2)}px)`:'none';
 const mask=$('#counterfactualMask');if(mask){mask.hidden=m!=='mask';mask.style.width=`${Math.round(3+amount*.35)}%`;mask.style.height=`${Math.round(3+amount*.35)}%`;}
 const readout=$('#counterfactualReadout');if(readout)readout.textContent=amount+'%';
}
function renderOverview(){const o=state.overview||{};const d=state.detail?.dataset;
  let html=head('RESEARCH WORKSPACE','Find what the data hides.','Investigate dataset integrity, connect evidence, and test whether your AI can be trusted.',btn(icon('upload')+' Import dataset','import')+' '+btn(icon('play')+' New sandbox','demo','btn-primary'));
  html+=`<div class="stats-row">${stat('Datasets indexed',number(o.datasets),'Versioned research collections')}${stat('Image records',number(o.samples),'Local research image samples')}${stat('Forensic findings',number(o.findings),'Hypotheses, not diagnoses')}${stat('Review decisions',number(o.reviewed),'Traceable human judgments')}</div>`;
  html+=d?`<div class="action-banner"><div><div class="eyebrow">ACTIVE INVESTIGATION</div><h2>${esc(d.name)}</h2><p>${number(d.sample_count)} samples · ${esc(d.source)} · ${d.synthetic?'Synthetic demonstration data':'Imported research data'}</p></div><div class="banner-actions">${btn(icon('search')+' Run forensic audit','run-audit','btn-teal')}</div></div>`:`<div class="action-banner"><div><div class="eyebrow">START YOUR FIRST INVESTIGATION</div><h2>Explore a controlled research dataset</h2><p>Generate nonmedical synthetic images with known planted faults to test the workflow safely.</p></div><div class="banner-actions">${btn(icon('plus')+' Generate sandbox','demo','btn-teal')}</div></div>`;
  const recent=(o.recent_datasets||[]).map(d=>`<div class="data-row"><div><div class="row-label">${esc(d.name)} ${d.synthetic?pill('Synthetic','green'):''}</div><div class="row-desc">${number(d.sample_count)} records · ${esc(d.modality)}</div></div><button type="button" class="btn btn-small" data-dataset="${esc(d.id)}">Open ${icon('arrow')}</button></div>`).join('');
  const jobs=(o.recent_jobs||[]).slice(0,5).map(j=>`<div class="data-row"><div><div class="row-label">${esc(title(j.kind))}</div><div class="row-desc">${esc(j.message)}</div></div>${pill(j.status,j.status==='completed'?'green':j.status==='failed'?'red':j.status==='running'?'amber':'')}</div>`).join('');
  html+=`<div class="two-col">${card('Research collections',recent||empty('No datasets yet','Create the sandbox to begin.'))}${card('Analysis activity',jobs||empty('No analysis jobs','Audits and research experiments will appear here.'),btn('View jobs','jobs','btn-small'))}</div>`;
  html+=`<div class="three-col">${featureCard('01','Data provenance','Inspect imports, split policies, label distributions and lineage.','dna')}${featureCard('02','Evidence-first audits','Review inspectable duplicate, leakage and label-suspicion evidence.','audit')}${featureCard('03','Reproducible experiments','Compare baseline models and controlled data interventions.','repro')}</div>`;
  return html;
}
function featureCard(n,title,body,view){return `<button type="button" class="card card-padded clickable" style="text-align:left" data-view="${view}"><div class="eyebrow">${n} / CAPABILITY</div><h3 style="margin:11px 0">${esc(title)}</h3><p class="fine">${esc(body)}</p><div style="margin-top:22px;color:var(--teal)">${icon('arrow')}</div></button>`;}
function dnaFilterQuery(filters){
 return '&split='+encodeURIComponent(filters?.split||'')+'&label='+encodeURIComponent(filters?.label||'')+
   '&search='+encodeURIComponent(filters?.search||'');
}
function setDnaChartFilter(kind,value){
 if(!['split','label'].includes(kind))return;
 state.dnaFilters={...(state.dnaFilters||{split:'',label:'',search:''}),[kind]:String(value)};
 state.sampleFilter=dnaFilterQuery(state.dnaFilters);
 state.samplePage=1;
}
function renderDNA(){if(!state.detail)return head('DATASET LIBRARY','Dataset DNA','Explore provenance, acquisition metadata, distribution and version lineage.')+needDataset();
 const d=state.detail.dataset;const dna=state.dna||{};
 let html=head('DATASET INTELLIGENCE','Dataset DNA','Trace how a research dataset was sourced, structured, versioned and prepared for analysis.',btn(icon('upload')+' Import another dataset','import'));
 html+=notice('A matching lesion ID does not establish matching patient identity. Interpret provenance only as documented by the original dataset provider.');
 html+=`<div class="two-col equal">${card('Dataset identity',`<dl>${[['Dataset',d.name],['Source',d.source],['Modality',d.modality],['Usage terms',d.license],['Manifest SHA-256',d.manifest_hash],['Type',d.synthetic?'Synthetic training images':'External research images']].map(([k,v])=>`<div class="kv"><dt>${esc(k)}</dt><dd class="${k.includes('SHA')?'mono':''}">${esc(v)}</dd></div>`).join('')}</dl>`)}${card('Data structure',`<div class="section-heading">Split distribution</div>${bars(dna.splits,0,'split')}<div class="rule"></div><div class="section-heading">Recorded labels</div>${bars(dna.labels,0,'label')}`)}</div>`;
 html+=`<div class="two-col">${card('Source and acquisition coverage',`<div class="section-heading">Source sites</div>${bars(dna.sites)}<div class="rule"></div><div class="section-heading">Image dimensions</div>${bars(dna.image_shapes)}<p class="fine" style="margin-top:18px">Group identifiers available for ${number(dna.group_coverage?.with_group_id)} of ${number(d.sample_count)} records.</p>`)}${card('Dataset lineage',`<div class="data-list">${(dna.lineage||[]).map((n,i)=>`<div class="data-row"><div><div class="row-label">${i===0?'Current version':'Parent version'}</div><div class="row-desc">${esc(n.name)}</div><div class="mono">${esc(short(n.manifest_hash))}</div></div>${pill('Immutable','green')}</div>`).join('')}</div><p class="fine" style="margin-top:14px">Version records preserve source manifests. Derived versions do not silently overwrite originals.</p>`)}</div>`;
 html+=`<section class="card card-padded"><div class="card-title"><h3>Sample explorer</h3><div>${btn(icon('filter')+' Refresh','refresh','btn-small')}</div></div><div class="filter-row"><select class="select" id="dnaSplit" aria-label="Sample split"><option value="">All splits</option>${['train','val','test'].map(x=>`<option value="${x}" ${state.dnaFilters.split===x?'selected':''}>${x}</option>`).join('')}</select><select class="select" id="dnaLabel" aria-label="Recorded label"><option value="">All labels</option>${Object.keys(dna.labels||{}).map(x=>`<option value="${esc(x)}" ${state.dnaFilters.label===x?'selected':''}>${esc(x)}</option>`).join('')}</select><input class="input" id="dnaSearch" value="${esc(state.dnaFilters.search)}" placeholder="Search sample identifier" aria-label="Search sample identifier"><button class="btn btn-small" data-action="filter-samples">Apply filters</button><button class="btn btn-small" data-action="clear-sample-filters">Clear filters</button></div><div class="record-grid" id="sampleGrid">${(state.samples?.items||[]).map(sampleCard).join('')}</div>${pager(state.samples?.count||0,state.samplePage,24,'sample')}</section>`;
 return html;
}
function pager(count,page,size,kind){const pages=Math.ceil(count/size);return pages>1?`<div style="display:flex;justify-content:space-between;align-items:center;margin-top:18px"><span class="fine">${number(count)} records · Page ${page}/${pages}</span><div style="display:flex;gap:8px"><button class="btn btn-small" data-page="${kind}:prev" ${page<=1?'disabled':''}>Previous</button><button class="btn btn-small" data-page="${kind}:next" ${page>=pages?'disabled':''}>Next</button></div></div>`:'';}
function renderAudit(){const d=state.detail?.dataset;const findings=state.findings;
 let html=head('FORENSIC ANALYSIS','Forensic Audit','Run reproducible integrity checks and inspect the evidence behind every flagged issue.',d?btn(icon('play')+' Run new audit','run-audit','btn-primary'):'');
 if(!d)return html+needDataset();
 const audit=state.detail.audits?.find(a=>a.status==='completed');
 html+=notice('Detection does not equal medical ground truth. Label disagreements, perceptual matches and source correlations require human interpretation.','warn');
 if(!audit)return html+empty('No completed forensic audit','Run the detector suite to identify exact duplicates, split/group overlap, near-duplicates, label suspicion and source associations.',btn('Run audit now','run-audit','btn-primary'));
 const data=audit.summary||{};
 html+=`<div class="stats-row">${stat('Candidate findings',number(data.total_findings),'All detector families')}${stat('Validated records',number(data.valid_samples),'Safe decoded images')}${stat('Label review set',number(data.label_analysis?.evaluated),'Training-only cross fit')}${stat('Near pairs tested',number(data.near_duplicate_search?.candidates_tested),'Bounded approximation')}</div>`;
 const hasCandidates=Number(data.total_findings||0)>0;
 const comparisonControl=hasCandidates?btn('Compare','rankings','btn-small'):
   '<button type="button" class="btn btn-small" disabled title="No detector findings are available to compare">Compare</button>';
 html+=`${card('Finding categories',bars(data.by_kind))}<div class="section-gap">${card('Experimental review ranking',`<p class="fine" style="margin-bottom:12px">Compare review strategies at a fixed budget. Only known injected defects can be scored.</p><div class="filter-row"><label for="rankingBudget" class="fine">Review budget</label><select class="select" id="rankingBudget" ${hasCandidates?'':'disabled'}>${[3,4,6,10,15].map(n=>`<option value="${n}" ${Number(state.rankingBudget||4)===n?'selected':''}>${n} cases</option>`).join('')}</select></div><div id="rankingResult">${renderRankings()}</div>`,comparisonControl)}</div>`;
 html+=`<section class="section-gap"><div class="card-title"><h3>Forensic evidence queue</h3><span class="fine">Select an item to inspect sources and record a review</span></div><div class="filter-row"><select class="select" id="findingKind"><option value="">All detector types</option>${['split_leakage','group_overlap','exact_duplicate','pixel_duplicate','near_duplicate','label_suspicion','source_association','integrity'].map(x=>`<option value="${x}" ${state.activeFilters.kind===x?'selected':''}>${title(x)}</option>`).join('')}</select><select class="select" id="findingStatus"><option value="">All statuses</option>${['suspected','confirmed','rejected','uncertain'].map(x=>`<option ${state.activeFilters.status===x?'selected':''}>${x}</option>`).join('')}</select><button class="btn btn-small" data-action="filter-findings">Apply filters</button><a class="btn btn-small" href="/api/datasets/${esc(d.id)}/report?format=csv">${icon('download')} Export CSV</a></div><div class="findings-list">${findings?.items?.length?findings.items.map(findingRow).join(''):empty('No findings for this filter','Try selecting a different detector type or review status.')}</div>${pager(findings?.count||0,state.findingPage||1,50,'finding')}</section>`;
 return html;
}
function renderRankings(){
 const payload=state.rankings||{},rows=payload.strategies||[];
 if(!rows.length)return notice(payload.message||'Run a completed forensic audit before comparing the candidate queues.','warn');
 const scored=payload.ground_truth_available;
 const budget=Number(payload.review_budget||rows[0].review_budget);
 const cards=rows.map(r=>{
  const summary=scored?`<strong>${number(r.confirmed_known_defects)} known injected defects</strong><span class="fine"> in ${budget} reviews · experimental synthetic reference</span>`:
    `<strong>${number(r.overlap_with_igat)}/${budget} overlap with IGAT</strong><span class="fine"> · ranking agreement only, not defect detection accuracy</span>`;
  const items=(r.top_candidates||[]).map((item,i)=>`<button class="ranking-candidate" data-finding="${esc(item.id)}" title="Inspect detector evidence"><span class="ranking-index">${i+1}</span><span><strong>${esc(item.title)}</strong><small>${esc(item.kind.replaceAll('_',' '))} · sample ${esc(item.sample_id||'dataset-wide')} · priority ${(Number(item.priority)*100).toFixed(0)}%</small></span>${icon('arrow')}</button>`).join('');
  return `<section class="ranking-strategy"><div class="ranking-title"><h4>${esc(r.name)}</h4>${scored?pill('Reference-scored','green'):pill('Order only','blue')}</div><div class="ranking-summary">${summary}</div><div class="ranking-candidates">${items}</div></section>`;
 }).join('');
 const guidance=scored?'The reference truth is from deliberately injected synthetic defects, NOT independently confirmed medical image labels.':
   'This is a real comparison of which findings each ranking would review first. No validated defect yield or superiority claim is possible without independent reference labels.';
 return `<div class="ranking-comparison" data-ranking-budget="${budget}"><div class="ranking-result-head"><strong>${number(payload.candidate_count||0)} candidate findings · review budget ${budget}</strong>${pill(scored?'Known synthetic truth':'No verified reference truth',scored?'green':'amber')}</div><p class="fine ranking-guidance">${esc(guidance)}</p><div class="ranking-grid">${cards}</div><p class="tiny" style="margin-top:12px">${esc(payload.method||'')} ${esc(payload.caveat||'')}</p></div>`;
}

function renderReview(){const d=state.detail?.dataset;const items=state.findings?.items||[];
 let html=head('HUMAN-IN-THE-LOOP','Review Center','Resolve suspected issues without overwriting image labels or destroying audit history.',d?btn('Open all audit evidence','go-audit'):'');
 if(!d)return html+needDataset();
 const counts=CounterStatus(items);
 html+=`<div class="stats-row">${stat('Current queue',number(state.findings?.count),'Findings returned by active filter')}${stat('Suspected',number(counts.suspected),'Awaiting judgment')}${stat('Confirmed',number(counts.confirmed),'Reviewer decision recorded')}${stat('Uncertain',number(counts.uncertain),'Requires further evidence')}</div>`;
 html+=notice('A confirmed review decision means a reviewer accepted the specific evidence-based concern. It does not certify an image label medically correct or incorrect.');
 html+=`<div class="filter-row"><select class="select" id="findingStatus"><option value="">All statuses</option>${['suspected','confirmed','rejected','uncertain'].map(x=>`<option ${state.activeFilters.status===x?'selected':''}>${x}</option>`).join('')}</select><button class="btn btn-small" data-action="filter-findings">Apply filters</button></div><div class="findings-list">${items.length?items.map(findingRow).join(''):empty('No evidence to review','Run an audit before starting human review.')}</div>${pager(state.findings?.count||0,state.findingPage||1,50,'finding')}`;
 return html;
}
function CounterStatus(items){const a={suspected:0,confirmed:0,uncertain:0,rejected:0};items.forEach(f=>a[f.status]=(a[f.status]||0)+1);return a;}
function graphVisibleData(graph,settings=state.graphUi){
 const nodes=Array.isArray(graph?.nodes)?graph.nodes:[];
 const originals=Array.isArray(graph?.edges)?graph.edges:[];
 const byId=new Map(nodes.map(n=>[n.id,n]));
 const edges=originals.filter(e=>byId.has(e.source)&&byId.has(e.target));
 const search=String(settings?.search||'').trim().toLocaleLowerCase();
 const severity=settings?.severity||'all', mode=settings?.links||'all';
 const filteredFindings=new Set(nodes.filter(n=>n.type==='finding'&&(severity==='all'||n.severity===severity)).map(n=>n.id));
 const eligible=new Set(nodes.filter(n=>n.type==='sample'||filteredFindings.has(n.id)).map(n=>n.id));
 const eligibleEdges=edges.filter(e=>eligible.has(e.source)&&eligible.has(e.target));
 let selected=new Set(eligible);
 if(search){
  const matching=new Set(nodes.filter(n=>eligible.has(n.id)&&[n.label,n.type,n.status,n.severity,n.split,n.group]
    .some(value=>String(value||'').toLocaleLowerCase().includes(search))).map(n=>n.id));
  selected=new Set(matching);
  eligibleEdges.forEach(e=>{
   if(matching.has(e.source))selected.add(e.target);
   if(matching.has(e.target))selected.add(e.source);
  });
 }else if(severity!=='all'){
  selected=new Set(filteredFindings);
  eligibleEdges.forEach(e=>{if(filteredFindings.has(e.source))selected.add(e.target)});
 }
 const matchingEdges=eligibleEdges.filter(e=>selected.has(e.source)&&selected.has(e.target));
 if(mode!=='all'){
  const linkedIds=new Set(matchingEdges.flatMap(e=>[e.source,e.target]));
  selected=new Set([...selected].filter(id=>mode==='linked'?linkedIds.has(id):!linkedIds.has(id)));
 }
 return {nodes:nodes.filter(n=>selected.has(n.id)),
         edges:matchingEdges.filter(e=>selected.has(e.source)&&selected.has(e.target)),
         sourceNodeCount:nodes.length,sourceEdgeCount:edges.length};
}
function graphOption(value,current,label){return '<option value="'+esc(value)+'"'+(value===current?' selected':'')+'>'+esc(label)+'</option>';}
function renderGraphExplorerResults(graph){
 const view=graphVisibleData(graph),findings=view.nodes.filter(n=>n.type==='finding');
 const linked=new Set(view.edges.map(e=>e.source)).size;
 const summary='<p class="graph-results-count" role="status">'+number(view.nodes.length)+' matching records · '+
    number(view.edges.length)+' detector links · '+number(linked)+' linked findings</p>';
 const index=findings.slice(0,24).map(n=>'<button type="button" class="graph-list-item" data-finding="'+esc(n.id.slice(2))+'">'+
   '<span><strong>'+esc(n.label||'Unlabelled finding')+'</strong><small>'+esc((n.severity||'ungraded')+' · '+(n.status||'unreviewed'))+
   '</small></span>'+icon('arrow')+'</button>').join('');
 const listing=index?'<section class="graph-result-index"><h4>Inspect matching findings</h4><div class="graph-finding-index">'+index+'</div>'+
    (findings.length>24?'<p class="fine">Showing the first 24 matching findings; narrow your filters to inspect others.</p>':'')+'</section>':'';
 if(!view.nodes.length){
  return summary+'<div class="graph-empty-results"><strong>No matching records</strong><p>Change the search or filters. No evidence relationships are inferred.</p>'+
  '<button class="btn btn-small" type="button" data-action="graph-reset">Clear graph filters</button></div>';
 }
 return summary+'<div class="graph-scroll-hint">'+
    (view.edges.length?'Scroll to inspect real linked images and findings. Select a node for the underlying evidence.':
    'No detector-supported links in this selection. These are isolated real dataset nodes, not fabricated relationships.')+'</div>'+
    '<div id="nodeGraph" class="node-graph" role="region" tabindex="0" aria-label="Interactive evidence graph; scroll to explore"></div>'+
    '<p class="fine graph-canvas-footnote">Diagram previews up to 14 findings and 28 image records. '+number(view.nodes.length)+
    ' matched records are available through the filters and evidence index. Edges are detector observations, not confirmed patient identity.</p>'+listing;
}
function updateGraphExplorer(){
 const result=$('#graphExplorerResults');if(!result||!state.graph)return;
 result.innerHTML=renderGraphExplorerResults(state.graph);
 const value=$('#graphZoomValue');if(value)value.textContent=Math.round(state.graphUi.zoom*100)+'%';
 const less=document.querySelector('[data-action="graph-zoom-out"]');
 const more=document.querySelector('[data-action="graph-zoom-in"]');
 if(less)less.disabled=state.graphUi.zoom<=0.75;
 if(more)more.disabled=state.graphUi.zoom>=1.5;
 drawGraph(state.graph);
}
function renderGraph(){
 let html=head('EVIDENCE EXPLORATION','Forensic Evidence Graph',
    'Search and inspect actual image records and detector findings without inventing relationships.',
    btn('Run audit','run-audit','btn-primary')+' '+btn('Reload graph','refresh'));
 if(!state.detail)return html+needDataset();
 const graph=state.graph||{nodes:[],edges:[]};
 const allEdges=Array.isArray(graph.edges)?graph.edges:[];
 const allNodes=Array.isArray(graph.nodes)?graph.nodes:[];
 const status=allEdges.length?number(allEdges.length)+' observed image–finding links':
   graph.audit_completed?'Audit complete · no image-linked evidence':'No completed audit yet';
 html+=notice(graph.note||'Connections are detector observations, not verified medical identities.',allEdges.length?'':'warn');
 html+='<section class="card card-padded graph-workbench"><div class="card-title"><h3>'+esc(status)+
  '</h3><div class="graph-legend"><span class="legend-item"><span class="legend-dot"></span>Image record</span>'+
  '<span class="legend-item"><span class="legend-dot blue"></span>Detector finding</span></div></div>';
 if(allNodes.length){
  const ui=state.graphUi;
  html+='<div class="graph-toolbar" role="group" aria-label="Evidence graph tools">'+
   '<label class="graph-field graph-search"><span>Search evidence</span><input class="input" id="graphSearch" type="search" autocomplete="off" '+
   'placeholder="Sample ID, finding, split…" value="'+esc(ui.search||'')+'"></label>'+
   '<label class="graph-field"><span>Severity</span><select class="select" id="graphSeverity">'+
   [['all','All severities'],['critical','Critical'],['high','High'],['medium','Medium'],['low','Low']].map(([v,l])=>graphOption(v,ui.severity,l)).join('')+
   '</select></label><label class="graph-field"><span>Connections</span><select class="select" id="graphLinks">'+
   [['all','All real records'],['linked','Linked only'],['unlinked','Unlinked only']].map(([v,l])=>graphOption(v,ui.links,l)).join('')+
   '</select></label><div class="graph-zoom-controls"><span class="graph-zoom-label">Zoom</span><div class="graph-zoom-buttons">'+
   '<button class="btn btn-small" type="button" data-action="graph-zoom-out" aria-label="Zoom evidence graph out" '+(ui.zoom<=0.75?'disabled':'')+'>−</button>'+
   '<output id="graphZoomValue" aria-label="Graph zoom level">'+Math.round(ui.zoom*100)+'%</output>'+
   '<button class="btn btn-small" type="button" data-action="graph-zoom-in" aria-label="Zoom evidence graph in" '+(ui.zoom>=1.5?'disabled':'')+'>+</button></div></div>'+
   '<button class="btn btn-small graph-reset-btn" type="button" data-action="graph-reset">Reset view</button></div>'+
   '<div id="graphExplorerResults" aria-live="off">'+renderGraphExplorerResults(graph)+'</div>';
 }else html+=empty('No source records available','Import data or create a synthetic sandbox, then run an audit to investigate evidence.',btn('Import dataset','import'));
 html+='</section>';
 if(!graph.audit_completed)html+='<div class="module-next" style="margin-top:20px"><div><strong>Generate the first evidence network</strong>'+
   '<p>Run the audit; relationships appear only when detectors return actual sample-linked findings.</p></div>'+
   btn(icon('play')+' Run forensic audit','run-audit','btn-primary')+'</div>';
 return html;
}

function labBase(eyebrow,titleText,desc,kind,buttonText='Run research experiment'){
 const d=state.detail?.dataset;
 let html=head(eyebrow,titleText,desc);
 if(!d)return {html:html+needDataset(),e:null,ready:false};
 const baselineRequired=['shortcut','counterfactual','cross_dataset'].includes(kind);
 const ready=!baselineRequired||Boolean(bestExp('baseline'));
 const e=bestExp(kind);
 html+=notice('These are research-only sensitivity experiments, not clinical validation or proof of causal shortcut learning.');
 if(!ready)html+=`<div class="lab-prerequisite" role="status">${icon('alert')}<div><strong>First complete the CPU baseline</strong><p>The ${esc(titleText)} uses a saved model checkpoint. Without it, there is nothing to compare. A failed or queued model run does not satisfy this requirement.</p></div>${btn('Train baseline','baseline-launch','btn-primary')}</div>`;
 const action=kind==='counterfactual'?'counterfactual-launch':kind==='cross_dataset'?'cross-launch':kind;
 const launch=ready?`<button type="button" class="btn btn-primary" data-action="${esc(action)}">${icon('play')} ${esc(buttonText)}</button>`:
 `<span class="fine">Awaiting trained baseline</span>`;
 html+=`<div class="lab-hero"><div class="lab-feature"><span class="lab-icon">${icon(kind==='impact'?'chart':kind==='shortcut'?'scan':kind==='cross_dataset'?'git':'layers')}</span><div><h3>${esc(d.name)}</h3><p>${esc(desc)}</p></div></div>${launch}</div>`;
 if(!e)html+=`<div class="lab-no-result"><strong>No completed experiment yet.</strong><p>After you start a valid run, open Analysis Jobs to see progress or the exact failure reason. Completed results will appear here automatically.</p>${btn('Open Analysis Jobs','jobs','btn-small')}</div>`;
 else html+=`<div class="result-title">Latest completed run · ${esc(e.id)}</div>`;
 return {html,e,ready};
}

function renderShortcut(){const {html,e}=labBase('MODEL INVESTIGATION','AI Shortcut Inspector','Stress-test model predictions by removing a small corner region; quantify output changes, without assuming causality.','shortcut','Probe shortcut sensitivity');
 if(!e)return html;
 const r=e.result;return html+`<div class="stats-row">${stat('Test images',number(r.test_n),'Frozen test partition')}${stat('Prediction flip rate',pct(r.prediction_flip_rate),'Change after corner mask')}${stat('Confidence variation',pct(r.mean_max_confidence_change),'Mean absolute change')}${stat('Probe region',r.region?.split(' ')[0]||'Corner','Controlled perturbation')}</div>${notice(r.caveat,'warn')}${card('Experimental protocol',`<div class="diagram"><div class="item"><span>CONTROL</span><strong>Original images</strong><p>Feature extraction and frozen model inference</p></div><div class="item"><span>INTERVENTION</span><strong>Corner mask</strong><p>Occlude a consistent region in each test image</p></div><div class="item"><span>COMPARISON</span><strong>Prediction stability</strong><p>Flip rate and confidence change</p></div></div>`)}`;
}
function renderCounterfactual(){
 const {html,e,ready}=labBase('CONTROLLED PERTURBATIONS','Counterfactual Lab','Test how a saved CPU model reacts to four controlled changes of a research image.','counterfactual','Run image perturbations');
 if(!state.detail)return html;
 const sampleRows=state.samples?.items||[];
 const selected=sampleRows.find(x=>x.id===(state.counterSampleId||e?.result?.sample_id))||sampleRows[0]||null;
 const opts=sampleRows.map(s=>`<option value="${esc(s.id)}" ${s.id===selected?.id?'selected':''}>${esc(s.sample_id)} — ${esc(s.label)} (${esc(s.split)})</option>`).join('');
 let h=html;
 h+=`<section class="card card-padded counter-lab-card"><div class="card-title"><h3>Choose an image and transformation</h3>${pill('Image preview · no AI result','blue')}</div><div class="field"><label for="counterSample">Research sample</label><select class="select" id="counterSample" ${!selected?'disabled':''}>${opts||'<option>No image samples available</option>'}</select><small>These are imported image records. Changes in the preview are not model predictions.</small>${pager(state.samples?.count||0,state.counterPage,24,'counter')}</div><div class="counter-stage"><div class="counter-panel"><span>Original image</span>${selected?`<img id="counterOriginalImage" src="${esc(selected.image_url)}" alt="Original image in dataset">`:'<div class="counter-missing">No samples imported</div>'}</div><div class="counter-panel"><span>Visual transformation preview</span><div id="counterfactualPreview" class="counter-real-preview">${selected?`<img id="counterModifiedImage" src="${esc(selected.image_url)}" alt="Visual preview of selected transformation">`:'<div class="counter-missing">Choose a sample</div>'}<div class="mask-block" id="counterfactualMask" hidden></div></div></div><div class="preview-controls"><div class="field"><label for="counterfactualMode">Preview transformation</label><select class="select" id="counterfactualMode"><option value="brightness" ${state.counterMode==='brightness'?'selected':''}>Brightness</option><option value="blur" ${state.counterMode==='blur'?'selected':''}>Blur</option><option value="mask" ${state.counterMode==='mask'?'selected':''}>Corner mask</option></select></div><div class="field"><label for="counterfactualAmount">Experiment strength <output id="counterfactualReadout" for="counterfactualAmount">${number(state.counterStrength)}%</output></label><input id="counterfactualAmount" type="range" min="0" max="100" value="${state.counterStrength}" step="5"></div></div><div class="counter-explanation">The model experiment applies the chosen strength to four predefined transformations and records the resulting predictions. The browser preview illustrates a single selected transformation; it is not used for scoring.</div>${!ready?notice('Train the baseline first to enable a real model experiment.','warn'):''}</section>`;
 if(e&&selected?.id!==e.result?.sample_id)h+=notice('The latest result belongs to a different image. Run the experiment again to evaluate the currently selected record.','warn');
 if(e&&selected?.id===e.result?.sample_id){const r=e.result;h+=`<div class="stats-row">${stat('Original prediction',r.original_prediction,'CPU baseline result')}${stat('Original confidence',pct(r.original_confidence),'Not diagnostic certainty')}${stat('Strength used',pct(r.strength??.4),'Recorded configuration')}${stat('Variants',number(r.variants?.length),'Controlled transformations')}</div><div class="variant-grid">${(r.variants||[]).map(v=>`<div class="variant"><img loading="lazy" src="/artifacts/${esc(v.image_path)}" alt="${esc(v.name)} transformed sample"><div class="content"><strong>${esc(title(v.name))}</strong><p>${esc(v.predicted)} · ${pct(v.confidence)} confidence ${v.changed_prediction?pill('Prediction changed','amber'):pill('Stable','green')}</p></div></div>`).join('')}</div>${notice(r.caveat,'warn')}`;}
 return h;
}

function renderCross(){let {html,e}=labBase('GENERALIZATION TEST','Cross-Dataset Reliability Lab','Evaluate a frozen baseline model against a second, explicitly compatible research dataset.','cross_dataset','Run external evaluation');
 if(!state.detail)return html;
 html=html.replace('data-experiment="cross_dataset"','data-action="cross-launch"');
 const others=state.datasets.filter(d=>d.id!==state.did);
 html+=`<div class="card card-padded" style="margin-bottom:20px"><div class="card-title"><h3>External research collection</h3></div><div class="field"><label for="crossTarget">Target dataset</label><select class="select" id="crossTarget"><option value="">Choose a distinct collection</option>${others.map(d=>`<option value="${esc(d.id)}">${esc(d.name)} (${number(d.sample_count)} samples)</option>`).join('')}</select><small>The declared modality and complete label vocabulary must match. Text matches alone do not establish clinical compatibility.</small></div></div>`;
 if(e){const r=e.result,m=r.external_test?.metrics||{};html+=`<div class="stats-row">${stat('External macro-F1',metric(m.macro_f1),'Frozen model')}${stat('Balanced accuracy',metric(m.balanced_accuracy),'Target dataset')}${stat('Target samples',number(m.n),'Held-out target test')}${stat('Data source',short(r.target_dataset_id),'Target dataset ID')}</div>${notice((r.comparison_limits||[]).join(' '),'warn')}`;}
 return html;
}
function renderImpact(){const {html,e}=labBase('INTERVENTION ANALYSIS','Audit Impact Simulator','Compare frozen-test performance before and after removing reviewer-confirmed training samples.','impact','Run removal-only ablation');
 if(!e)return html;
 const r=e.result;return html+`<div class="stats-row">${stat('Samples excluded',number(r.removed_count),'Training partition only')}${stat('Baseline macro-F1',metric(r.before?.macro_f1),'Original training set')}${stat('Curated macro-F1',metric(r.after?.macro_f1),'Removal-only ablation')}${stat('F1 change',(r.macro_f1_delta>=0?'+':'')+metric(r.macro_f1_delta),'Not necessarily improvement')}</div>${notice((r.limitations||[]).join(' '),'warn')}${card('Independent evaluation contract',`<dl><div class="kv"><dt>Original train count</dt><dd>${number(r.original_train_n)}</dd></div><div class="kv"><dt>Curated train count</dt><dd>${number(r.curated_train_n)}</dd></div><div class="kv"><dt>Frozen test fingerprint</dt><dd class="mono">${esc(r.evaluation_test_ids_sha256)}</dd></div></dl>`)}`;
}
function baselineReadinessPanel(){
 const r=state.baselineReadiness;if(!r)return '';
 const counts=Object.entries(r.training_class_counts||{}).sort((a,b)=>a[0].localeCompare(b[0]))
    .map(([k,v])=>'<span class="baseline-class">'+esc(k)+': <strong>'+number(v)+'</strong></span>').join('');
 const issues=(r.reasons||[]).map(v=>'<li>'+esc(v)+'</li>').join('');
 const warnings=(r.warnings||[]).map(v=>'<li>'+esc(v)+'</li>').join('');
 const last=r.last_attempt||null;
 const failure=last&&last.status==='failed'
   ?'<div class="baseline-last-error" role="alert"><strong>Previous baseline failed</strong><p>'+esc(last.error||'No detailed error was saved; open Analysis Jobs.')+'</p></div>':'';
 const missing=last&&last.status==='completed'&&!last.checkpoint_available
   ?'<div class="baseline-last-error" role="alert">The previous model file is missing. Rerun baseline; other labs cannot use that checkpoint.</div>':'';
 return card('Baseline readiness', '<div class="baseline-readiness">'+
    '<div class="baseline-readiness-top">'+pill(r.ready?'Ready to attempt training':'Dataset not ready',r.ready?'green':'amber')+
    '<span class="fine">'+number(r.train_count)+' training images · '+number(r.test_count)+' test images · '+number(counts.length)+' training classes</span></div>'+
    (counts?'<div class="baseline-class-list" aria-label="Training class support">'+counts+'</div>':'')+
    (issues?'<div class="baseline-messages"><strong>Required changes</strong><ul>'+issues+'</ul></div>':'')+
    (warnings?'<div class="baseline-messages"><strong>Research cautions</strong><ul>'+warnings+'</ul></div>':'')+
    failure+missing+
    '<p class="fine">This check does not guarantee training success or independent test records. The full leakage and file checks run in the background job.</p></div>');
}
function renderFailureGallery(experiment){
 const result=experiment?.result?.test||{},predictions=result.predictions||[];
 const labels=result.metrics?.labels||[];
 const cell=String(state.failureCell||'');
 const ids=cell.match(/^([0-9]+):([0-9]+)$/);
 const selected=ids&&labels[Number(ids[1])]!==undefined&&labels[Number(ids[2])]!==undefined;
 const actual=selected?labels[Number(ids[1])]:null,predicted=selected?labels[Number(ids[2])]:null;
 const rows=predictions.filter(p=>selected?String(p.actual)===String(actual)&&String(p.predicted)===String(predicted):!p.correct);
 const display=rows.slice(0,36);
 const heading=selected?'Actual '+String(actual)+' → Predicted '+String(predicted):'Misclassified research samples';
 const cards=display.map(p=>'<button type="button" class="record" data-sample="'+esc(p.sample_db_id)+'">'+
  '<img src="/files/'+esc(p.sample_db_id)+'" alt="Research image '+esc(p.sample_id)+'" loading="lazy">'+
  '<div class="record-content"><span class="record-name">'+esc(p.sample_id)+'</span>'+
  '<span class="record-label">'+esc(p.actual)+' → '+esc(p.predicted)+'</span></div></button>').join('');
 return '<section class="card card-padded" id="failureGallery" aria-live="polite">'+
  '<div class="card-title"><h3>'+esc(heading)+'</h3>'+pill(number(rows.length)+' samples',selected?'blue':'amber')+'</div>'+
  (selected?'<div class="failure-filter-context"><p>Showing the selected confusion-matrix cell. Counts reflect supplied research labels, not clinical ground truth.</p>'+
   '<button type="button" class="btn btn-small" data-action="failure-reset">Show all errors</button></div>':'')+
  '<div class="record-grid">'+cards+'</div>'+
  (!rows.length?empty(selected?'No records in this cell':'No disagreements on this test split',
     'This does not establish clinical reliability. Select another cell or review the full evaluation.'):'')+
  (rows.length>36?'<p class="fine">Showing the first 36 matching image records.</p>':'')+'</section>';
}
function updateFailureExplorer(){
 const e=bestExp('baseline');if(!e)return;
 const gallery=$('#failureGallery');
 if(gallery)gallery.outerHTML=renderFailureGallery(e);
 document.querySelectorAll('[data-confusion]').forEach(button=>{
  const pressed=button.dataset.confusion===state.failureCell;
  button.setAttribute('aria-pressed',String(pressed));
  button.classList.toggle('is-selected',pressed);
 });
}
function renderFailures(){let html=head('PERFORMANCE INVESTIGATION','Model Failure Explorer','Inspect prediction mistakes, confusion matrices, uncertainty and performance across recorded source groups.',btn(icon('play')+' Run baseline','baseline-launch','btn-primary'));
 if(!state.detail)return html+needDataset();
 html+=baselineReadinessPanel();
 const e=bestExp('baseline');if(!e){const failed=state.detail?.experiments?.some(x=>x.kind==='baseline'&&x.status==='failed');return html+(failed?notice('The last baseline model failed. Open Analysis Jobs to read the error, then select Run baseline to retry after updating the software.','warn'):'')+empty('No completed model evaluation yet','Train the CPU baseline to examine test-split misclassifications. For failed attempts, use Analysis Jobs to review the exact error.',btn('Train baseline model','baseline-launch','btn-primary')+' '+btn('View failed jobs','jobs'));}
 const r=e.result.test||{},m=r.metrics||{},errors=(r.predictions||[]).filter(x=>!x.correct);
 html+=notice('These are research-label disagreements from a lightweight model. Misclassification is not a verified clinical diagnosis error.');
 if(e.result.training_warnings?.length)html+=notice('Training cautions: '+e.result.training_warnings.join(' '),'warn');
 html+=`<div class="stats-row">${stat('Test macro-F1',metric(m.macro_f1),'Bootstrap interval: '+((m.macro_f1_ci95||[]).map(metric).join(' to ')||'n/a'))}${stat('Balanced accuracy',metric(m.balanced_accuracy),'Class-balanced test metric')}${stat('Test errors',number(errors.length),'Disagreements with supplied labels')}${stat('Calibration error',metric(m.expected_calibration_error),'Exploratory ECE; lower is better')}</div>`;
 const cm=m.confusion_matrix||[];let mat='';if(cm.length){const mx=Math.max(1,...cm.flat());mat=`<div class="cm-grid" style="grid-template-columns:repeat(${cm.length},minmax(0,1fr))">${cm.flatMap((row,i)=>row.map((v,j)=>{
 const id=i+':'+j,active=state.failureCell===id,actual=m.labels?.[i]||'',predicted=m.labels?.[j]||'';
 return `<button type="button" class="cm-cell ${active?'is-selected':''}" data-confusion="${id}" aria-pressed="${active}" aria-label="Inspect ${number(v)} test images, actual ${esc(actual)}, predicted ${esc(predicted)}" title="Inspect actual ${esc(actual)}; predicted ${esc(predicted)}" style="background:rgba(33,117,104,${(.08+.65*v/mx).toFixed(2)})">${number(v)}<small>${i===j?'correct':'error'}</small></button>`;})).join('')}</div><p class="fine" style="margin-top:13px">Rows: actual labels · columns: predicted labels. ${esc((m.labels||[]).join(' · '))}. Select any cell to inspect its actual image records.</p>`;}
 html+=`<div class="two-col equal">${card('Confusion matrix',mat||'<p>No confusion matrix reported.</p>')}${card('Performance by recorded site',`<div class="data-list">${(r.subgroups||[]).map(s=>`<div class="data-row"><div><div class="row-label">${esc(s.name)}</div><div class="row-desc">${s.n} samples</div></div><strong>${s.metric==null?'Insufficient data':pct(s.metric)}</strong></div>`).join('')}</div><p class="fine" style="margin-top:12px">Exploratory subgroup metrics only; no fairness conclusion.</p>`)}</div>`;
 html+=`<div class="two-col equal section-gap">${card('Per-class performance',`<div class="table-wrap"><table><thead><tr><th>Recorded class</th><th>Precision</th><th>Recall</th><th>F1</th><th>N</th></tr></thead><tbody>${(m.labels||[]).map(l=>{const x=m.per_class?.[l]||{};return `<tr><td>${esc(l)}</td><td>${metric(x.precision)}</td><td>${metric(x.recall)}</td><td>${metric(x['f1-score'])}</td><td>${number(x.support)}</td></tr>`}).join('')}</tbody></table></div>`)}${card('Calibration by confidence',`<p class="fine" style="margin-bottom:12px">Empirical accuracy in bins of predicted confidence. Small bins have high uncertainty.</p>${(m.calibration_bins||[]).map(b=>`<div class="bar-row"><span class="bar-label">${Math.round(b.lower*100)}–${Math.round(b.upper*100)}%</span><div class="meter"><div class="meter-fill" style="width:${Math.round(b.empirical_accuracy*100)}%"></div></div><span class="bar-val">${number(b.n)} img</span></div>`).join('')}`)}</div>`;
 html+=renderFailureGallery(e);
 return html;
}
function renderRepro(){const d=state.detail?.dataset;let html=head('SCIENTIFIC TRACEABILITY','Reproducibility Engine','Reopen experiments, inspect immutable manifests and export transparent research audit records.',d?btn(icon('download')+' Export JSON report','download-json','btn-primary'):'');
 if(!d)return html+needDataset();
 const exps=state.detail.experiments||[];
 html+=`<div class="two-col equal">${card('Dataset fingerprint',`<div class="eyebrow">SHA-256 MANIFEST</div><div class="mono-box">${esc(d.manifest_hash)}</div><p class="fine" style="margin-top:14px">Manifest fingerprints change when dataset membership or labels change. Source images remain unchanged in derived label scenarios.</p>`)}${card('Controlled scenario generator',`<p class="fine" style="margin-bottom:15px">Create a derived dataset version with seeded, known training-label corruption. Original images and labels remain unchanged.</p><div class="field-group"><div class="field"><label for="scenarioSeed">Fixed random seed</label><input class="input" id="scenarioSeed" type="number" value="42" min="1" max="999999"></div><div class="field"><label for="scenarioRate">Flip percentage</label><select class="select" id="scenarioRate"><option value="0.05">5%</option><option value="0.08" selected>8%</option><option value="0.12">12%</option></select></div></div>${btn(icon('play')+' Generate version','scenario-launch','btn-teal')}`)}</div>`;
 html+=`<section class="card card-padded section-gap"><div class="card-title"><h3>Source-file integrity check</h3>${pill('Read-only verification')}</div><p class="fine" style="margin-bottom:12px">Verify each local image against the SHA-256 stored at import and check the dataset version manifest. This does not verify medical labels, patient identity or licensing.</p>${btn(icon('shield')+' Verify dataset hashes','verify-integrity','btn-teal')}<div id="integrityResults" role="status" aria-live="polite"></div></section>`;
 html+=`<section class="card card-padded"><div class="card-title"><h3>Experiment registry</h3>${pill(number(exps.length)+' recorded')}</div>${exps.length?`<div class="table-wrap"><table class="tablesimple"><thead><tr><th>Experiment</th><th>Kind</th><th>Status</th><th>Created</th><th>Manifest</th></tr></thead><tbody>${exps.map(e=>`<tr><td class="mono">${esc(short(e.id))}</td><td>${esc(title(e.kind))}</td><td>${pill(e.status,e.status==='completed'?'green':e.status==='failed'?'red':'amber')}</td><td>${esc(String(e.created_at||'').split('T')[0])}</td><td><button type="button" class="btn btn-small" data-experiment-detail="${esc(e.id)}">Inspect</button></td></tr>`).join('')}</tbody></table></div>`:empty('No experiment records','Run the baseline or an audit laboratory to begin collecting reproducible evidence.')}</section>`;
 html+=`<div class="section-gap two-col equal">${card('Audit export formats',`<div class="data-list">${[['JSON evidence bundle','json'],['CSV findings','csv'],['Printable HTML report','html'],['Reproducibility + file integrity bundle','repro']].map(([x,f])=>`<div class="data-row"><span class="row-label">${esc(x)}</span><a class="btn btn-small" href="/api/datasets/${esc(d.id)}/report?format=${f}" download>${icon('download')} Export</a></div>`).join('')}</div>`)}${card('Research safeguards',`<ul class="feature-list"><li>Fixed seeds and model configurations</li><li>Training-only label-suspicion cross-validation</li><li>Provenance-screened held-out evaluation partitions</li><li>Reviewer decisions append to audit history</li><li>No automated medical relabeling</li><li>Disclosure of incomplete evidence and benchmark limits</li></ul>`)}</div>`;
 return html;
}
function renderPrivacy(){let html=head('DATA GOVERNANCE','Privacy & Integrity Guard','Local-first processing, bounded uploads, transparent access and documented research limitations.');
 const p=state.privacy||{};
 html+=`<div class="three-col">${featureCard('01','Local inference','Models run on your computer without paid or remote inference APIs.','overview')}${featureCard('02','Protected image storage','Raw data sits outside the web frontend and is served by validated API paths.','dna')}${featureCard('03','Controlled exports','Evidence files disclose detector assumptions and clinical limitations.','repro')}</div>`;
 html+=`<div class="two-col equal">${card('Active technical protections',`<ul class="feature-list"><li>ZIP traversal and symlink checks</li><li>Upload size and per-image decoding limits</li><li>Only supported NPZ arrays; no pickle loading</li><li>Relative-path validation before image access</li><li>Data and artifacts kept outside public web root</li><li>No default outbound telemetry</li><li>Optional localhost access token</li><li>Strict no-cache for research records</li></ul>`)}${card('Research-data responsibility',`<p class="fine" style="margin-bottom:15px">This workstation software does not automatically de-identify images. Upload only data you are authorized to use. Respect each dataset's licensing and permitted redistribution conditions.</p>${notice('Do not expose the local server to a public network or upload real identifiable clinical data without proper institutional governance.','warn')}<div class="scope-label">LOCAL SESSION ACCESS · ${p.token_required?'TOKEN ENABLED':'TOKEN DISABLED (DEFAULT)'}</div><p class="fine" style="margin:12px 0">${p.token_required?'Enter the secret configured in PowerShell with MDF_ACCESS_TOKEN before launching the server.':'No access token is necessary when running locally at 127.0.0.1 and MDF_ACCESS_TOKEN has not been set. Never expose this default setup on a public network.'}</p><div class="field"><label for="authToken">Optional access token</label><input class="input" type="password" id="authToken" value="" autocomplete="off" placeholder="Set if MDF_ACCESS_TOKEN is configured"><small>Stored only for this browser tab/session, never bundled with the project.</small></div>${p.token_required?btn('Apply token','save-token','btn-small'):'<span class="fine">Not configured. You can leave this field empty.</span>'}`)}</div>`;
 return html;
}
function renderError(error){$('#main').innerHTML=head('REQUEST ERROR','We could not load this workspace','Check the backend or the research data and retry.')+`<div class="card card-padded">${notice(error?.message||String(error),'warn')}${btn(icon('rotate')+' Retry','refresh','btn-primary')} ${btn('Set access token','auth-prompt')}</div>`;}
async function loadCore(){const [overview,datasets]=await Promise.all([api('/api/overview'),api('/api/datasets')]);state.overview=overview;state.datasets=datasets;
 const preferred=state.did||storage.get('localStorage','mdf-dataset')||'';
 state.did=datasets.some(d=>d.id===preferred)?preferred:(datasets[0]?.id||'');
 if(state.did){state.detail=await api('/api/datasets/'+state.did)}else state.detail=null;
 const sel=$('#datasetSelect');sel.innerHTML=`<option value="">No dataset loaded</option>`+datasets.map(d=>`<option value="${esc(d.id)}" ${d.id===state.did?'selected':''}>${esc(d.name)}</option>`).join('');
}
async function loadView(){const did=state.did;
 if(!did)return;
 if(['dna','counterfactual'].includes(state.view)){
  const page=state.view==='counterfactual'?state.counterPage:state.samplePage;
  const filters=state.view==='dna'?(state.sampleFilter||''):'';
  const tasks=[api(`/api/datasets/${did}/samples?page=${page}&size=24${filters}`)];
  if(state.view==='dna')tasks.push(api(`/api/datasets/${did}/dna`));
  const out=await Promise.all(tasks);state.samples=out[0];if(out[1])state.dna=out[1];
 }
 if(['audit','review'].includes(state.view)){
  const f=state.activeFilters;const q=`?size=50&page=${state.findingPage||1}&kind=${encodeURIComponent(f.kind)}&status=${encodeURIComponent(f.status)}`;
  state.findings=await api(`/api/datasets/${did}/findings${q}`);
  if(state.view==='audit')state.rankings=await api(`/api/datasets/${did}/rankings?budget=${state.rankingBudget||4}`);
 }
 if(state.view==='graph')state.graph=await api(`/api/datasets/${did}/graph?limit=100`);
 if(state.view==='privacy')state.privacy=await api('/api/privacy');
 if(state.view==='failures')state.baselineReadiness=await api('/api/datasets/'+did+'/baseline-readiness');
}
const RENDER={overview:renderOverview,dna:renderDNA,audit:renderAudit,graph:renderGraph,review:renderReview,shortcut:renderShortcut,counterfactual:renderCounterfactual,cross:renderCross,impact:renderImpact,failures:renderFailures,repro:renderRepro,privacy:renderPrivacy};
async function render(){try{$('#main').innerHTML='<div class="loading-screen"><div class="spinner"></div><p>Loading research evidence…</p></div>';await loadView();$('#crumbCurrent').textContent=({dna:'Dataset DNA',audit:'Forensic Audit',graph:'Evidence Graph',review:'Review Center',shortcut:'Shortcut Inspector',counterfactual:'Counterfactual Lab',cross:'Cross-Dataset Lab',impact:'Impact Simulator',failures:'Failure Explorer',repro:'Reproducibility',privacy:'Privacy & Integrity'})[state.view]||'Overview';const rendered=(RENDER[state.view]||renderOverview)();if(typeof rendered!=='string'||!rendered.trim())throw Error('The '+state.view+' workspace did not render correctly.');$('#main').innerHTML=rendered;document.querySelectorAll('.nav-link').forEach(b=>b.classList.toggle('active',b.dataset.view===state.view));if(state.view==='graph'&&state.graph?.nodes?.length)drawGraph(state.graph);}catch(e){renderError(e)}}
async function refresh(full=true){try{if(full)await loadCore();await render()}catch(e){renderError(e)}}
async function navigate(view){state.view=RENDER[view]?view:'overview';window.location.hash='#/'+state.view;$('#sidebar').classList.remove('open');$('#mobileOverlay').hidden=true;$('#menuToggle').setAttribute('aria-expanded','false');state.findingPage=1;await render();$('#main')?.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'})}
async function changeDataset(did){state.did=did;storage.set('localStorage','mdf-dataset',did);state.activeFilters={kind:'',status:''};state.samplePage=1;state.counterPage=1;state.findingPage=1;state.sampleFilter='';state.counterSampleId=null;state.counterStrength=40;state.counterMode='brightness';state.samples=null;state.findings=null;state.graph=null;state.rankings=null;state.baselineReadiness=null;state.graphUi={search:'',severity:'all',links:'all',zoom:1};state.failureCell='';state.dnaFilters={split:'',label:'',search:''};await refresh(true);toast('Research dataset selected.');}
function drawGraph(graph){
 const box=$('#nodeGraph');if(!box)return;
 const visible=graphVisibleData(graph);
 const connectedIds=new Set(visible.edges.flatMap(e=>[e.source,e.target]));
 const findings=visible.nodes.filter(n=>n.type==='finding'&&connectedIds.has(n.id)).slice(0,14);
 const findingIds=new Set(findings.map(n=>n.id));
 const linkedSampleIds=new Set(visible.edges.filter(e=>findingIds.has(e.source)).map(e=>e.target));
 const selectedSamples=visible.nodes.filter(n=>n.type==='sample'&&linkedSampleIds.has(n.id)).slice(0,28);
 const otherFindings=visible.nodes.filter(n=>n.type==='finding'&&!connectedIds.has(n.id));
 const otherSamples=visible.nodes.filter(n=>n.type==='sample'&&!connectedIds.has(n.id));
 const roomFindings=14-findings.length,roomSamples=28-selectedSamples.length;
 const shownFindings=findings.concat(otherFindings.slice(0,Math.max(0,roomFindings)));
 const shownSamples=selectedSamples.concat(otherSamples.slice(0,Math.max(0,roomSamples)));
 const chosen=new Set([...shownFindings,...shownSamples].map(n=>n.id));
 const displayedEdges=visible.edges.filter(e=>chosen.has(e.source)&&chosen.has(e.target));
 const nodes=[...shownSamples,...shownFindings];
 if(!nodes.length){
  box.innerHTML='<p class="fine graph-empty-note" role="status">No records match these filters.</p>';return;
 }
 const baseWidth=950,baseHeight=Math.max(340,Math.max(shownFindings.length,shownSamples.length)*68+96);
 const zoom=Math.min(1.5,Math.max(0.75,Number(state.graphUi?.zoom)||1));
 const position={};
 const place=(items,x)=>items.forEach((node,index)=>{position[node.id]={x,y:52+(index+.5)*(baseHeight-110)/Math.max(1,items.length)}});
 place(shownSamples,210);place(shownFindings,720);
 const edges=displayedEdges.map(edge=>{
   const left=position[edge.target],right=position[edge.source];
   if(!left||!right)return '';
   return '<path d="M'+(left.x+112)+','+left.y+' C'+(left.x+270)+','+left.y+' '+(right.x-270)+','+right.y+
    ' '+(right.x-112)+','+right.y+'" fill="none" stroke="var(--teal)" stroke-opacity=".8" stroke-width="2.5"/>';
 }).join('');
 const cards=nodes.map(node=>{
   const p=position[node.id],finding=node.type==='finding',label=String(node.label||'Unnamed record');
   const shown=label.length>30?label.slice(0,29)+'…':label;
   const sub=finding?String(node.severity||node.status||'suspected').toUpperCase():String(node.split||'image').toUpperCase();
   return '<g tabindex="0" role="button" data-node="'+esc(node.id)+'" aria-label="Inspect '+esc(label)+
   '" class="graph-card" transform="translate('+(p.x-112)+','+(p.y-24)+')"><rect width="224" height="48" rx="9" class="graph-card-bg '+
   (finding?'graph-card-finding':'')+'"/><rect width="5" height="30" x="11" y="9" rx="2.5" fill="'+
   (finding?'#4779b6':'#237568')+'"/><text class="graph-label" x="23" y="21">'+esc(shown)+
   '</text><text class="graph-caption" x="23" y="36">'+esc(sub)+'</text><title>'+esc(label)+'</title></g>';
 }).join('');
 box.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" width="'+Math.round(baseWidth*zoom)+'" height="'+
   Math.round(baseHeight*zoom)+'" viewBox="0 0 '+baseWidth+' '+baseHeight+
   '" role="group" aria-label="Actual forensic evidence connections and isolated records"><title>Evidence map</title>'+
   '<text x="100" y="24" class="graph-col-title">SOURCE IMAGE RECORDS</text>'+
   '<text x="610" y="24" class="graph-col-title">FORENSIC FINDINGS</text><g>'+edges+'</g><g>'+cards+'</g></svg>';
 box.querySelectorAll('[data-node]').forEach(el=>{
  const open=()=>{const id=el.dataset.node;if(id.startsWith('f:'))openFinding(id.slice(2));else if(id.startsWith('s:'))openSample(id.slice(2))};
  el.addEventListener('click',open);
  el.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();open()}});
 });
}

async function openFinding(id){try{const out=await api('/api/findings/'+id);const f=out.finding;let h=`${notice('All findings remain hypotheses unless supported by independently reviewed evidence.')}`;
 h+=`<div class="comparison"><div class="image-panel">${out.sample?`<img src="${esc(out.sample.image_url)}" alt="Primary sample ${esc(out.sample.sample_id)}"><p>${esc(out.sample.sample_id)} · ${esc(out.sample.split)}</p>`:'<div class="empty-state">Dataset-wide finding</div>'}</div><div class="image-panel">${out.linked?`<img src="${esc(out.linked.image_url)}" alt="Linked sample ${esc(out.linked.sample_id)}"><p>${esc(out.linked.sample_id)} · ${esc(out.linked.split)}</p>`:'<div class="empty-state">No second image</div>'}</div></div>`;
 h+=`<div style="display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:19px 0">${pill(f.kind,'blue')}${pill(f.severity,f.severity==='critical'?'red':f.severity==='high'?'amber':'')}${pill(f.status,f.status==='confirmed'?'green':'')}</div><p style="margin-bottom:18px;font-size:13px">${esc(f.detail)}</p><details><summary class="clickable" style="font-weight:650">Inspect measurement evidence</summary><div class="mono-box" style="margin:12px 0">${esc(JSON.stringify(f.evidence,null,2))}</div></details>`;
 h+=`<div class="rule"></div><div class="scope-label">HUMAN REVIEW DECISION</div><div class="field-group"><div class="field"><label for="reviewer">Reviewer</label><input class="input" id="reviewer" value="Local researcher" maxlength="100"></div><div class="field"><label for="reviewDuration">Review duration (seconds)</label><input class="input" id="reviewDuration" type="number" min="0" placeholder="Optional"></div></div><div class="field"><label for="reviewNotes">Evidence and limitations</label><textarea class="textarea" id="reviewNotes" rows="3" maxlength="4000" placeholder="Explain the evidence supporting your decision…"></textarea></div><div class="actions"><button class="btn btn-teal" data-review="${esc(id)}:confirmed">${icon('check')} Confirm concern</button><button class="btn btn-danger" data-review="${esc(id)}:rejected">Reject</button><button class="btn" data-review="${esc(id)}:uncertain">Uncertain</button></div>`;
 if(out.reviews?.length)h+=`<div class="rule"></div><div class="scope-label">PRESERVED REVIEW HISTORY</div>${out.reviews.map(r=>`<div class="history-entry"><strong>${esc(r.reviewer)}</strong> · ${pill(r.decision)}<p>${esc(r.notes||'No rationale supplied')} · ${esc(r.created_at||'')}</p></div>`).join('')}`;
 openModal(f.title,h);
 }catch(e){toast(e.message,true)}}
async function openSample(id){try{const d=await api('/api/samples/'+id),s=d.sample;openModal('Image record · '+s.sample_id,`<div class="comparison"><div class="image-panel"><img src="${esc(s.image_url)}" alt="Selected research image" style="height:300px"><p>${esc(s.sample_id)}</p></div><div><dl>${[['Label',s.label],['Split',s.split],['Group ID',s.group_id||'Not recorded'],['Group meaning',s.group_type||'Not documented'],['Source site',s.site||'Unknown'],['Dimensions',s.width+'×'+s.height],['SHA256',short(s.sha256)]].map(([k,v])=>`<div class="kv" style="grid-template-columns:100px 1fr"><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl></div></div><div class="rule"></div><h3>Linked forensic findings</h3>${(d.findings||[]).length?`<div class="findings-list" style="margin-top:13px">${d.findings.slice(0,8).map(findingRow).join('')}</div>`:'<p class="fine" style="margin-top:12px">No related audit evidence recorded.</p>'}`)}catch(e){toast(e.message,true)}}
async function startAudit(){if(!state.did)return toast('Select a dataset first',true);try{const v=await api('/api/datasets/'+state.did+'/audit',{method:'POST'});toast('Forensic analysis queued. Watch Analysis Jobs.');openJobs();}catch(e){toast(e.message,true)}}
async function launchExperiment(kind,config={}){
 if(!state.did)return toast('Select a dataset first',true);
 try{
  if(kind==='baseline'){
   const readiness=await api('/api/datasets/'+state.did+'/baseline-readiness');
   state.baselineReadiness=readiness;
   if(!readiness.ready){
    toast('Cannot train yet: '+(readiness.reasons?.[0]||'Dataset prerequisites missing'),true);
    await navigate('failures');return;
   }
  }
  if(['shortcut','counterfactual','cross_dataset'].includes(kind)&&!bestExp('baseline')){
   toast('Train baseline and keep its saved model file first; open Model Failure Explorer.',true);
   await navigate('failures');return;
  }
  const v=await api('/api/datasets/'+state.did+'/experiments',{method:'POST',body:JSON.stringify({kind,config})});
  toast(title(kind)+' experiment queued.');await openJobs();
 }catch(e){toast(e.message,true)}
}
const JOB_NOTIFICATION_STORAGE_KEY='mdf-cleared-job-notifications-v1';
const TERMINAL_JOB_STATES=new Set(['completed','failed','cancelled']);
function isFinishedJob(job){return TERMINAL_JOB_STATES.has(job?.status)}
function clearedJobIds(){
 try{
  const saved=JSON.parse(storage.get('localStorage',JOB_NOTIFICATION_STORAGE_KEY)||'[]');
  return new Set(Array.isArray(saved)?saved.filter(id=>typeof id==='string'&&id.length<=100).slice(-500):[]);
 }catch{return new Set()}
}
function saveClearedJobIds(ids){storage.set('localStorage',JOB_NOTIFICATION_STORAGE_KEY,JSON.stringify([...ids].slice(-500)))}
function visibleJobNotifications(rows,includeCleared=false){
 const cleared=clearedJobIds();
 return rows.filter(job=>includeCleared||!isFinishedJob(job)||!cleared.has(job.id));
}
function updateJobIndicator(rows){
 const badge=$('#jobIndicator');if(!badge)return;
 const cleared=clearedJobIds();
 badge.hidden=!rows.some(job=>['queued','running'].includes(job.status)||(isFinishedJob(job)&&!cleared.has(job.id)));
}
function renderJobInbox(rows,showHistory=false){
 const cleared=clearedJobIds();
 const items=visibleJobNotifications(rows,showHistory);
 const actionable=rows.filter(job=>isFinishedJob(job)&&!cleared.has(job.id));
 const archived=rows.filter(job=>isFinishedJob(job)&&cleared.has(job.id)).length;
 const heading=showHistory?'Recent job history':'Notifications & analysis jobs';
 const intro=showHistory?'The latest 35 job records are shown, including cleared notifications.':
   'Active jobs stay visible; finished notifications can be cleared without deleting results.';
 const header='<div class="job-inbox-header"><div><h3>'+heading+'</h3><p class="fine">'+intro+'</p></div>'+
   '<button class="btn btn-small" type="button" data-action="clear-job-notifications" '+(actionable.length?'':'disabled')+'>Clear notifications ('+actionable.length+')</button></div>';
 const info='<p class="job-inbox-note">'+(archived?archived+' cleared notification(s) in recent history. ':'')+
   'Clearing hides messages in this browser only. Audit records, errors and experiment history remain saved.</p>';
 const contents=items.length?items.map(job=>{
  const terminal=isFinishedJob(job),done=terminal&&cleared.has(job.id);
  const action=terminal?(done?'<span class="job-cleared-label">Cleared</span>':
   '<button class="btn btn-small job-dismiss" type="button" data-dismiss-job="'+esc(job.id)+'" aria-label="Clear '+esc(title(job.kind))+' notification">Clear</button>'):
   '<button class="btn btn-small" type="button" data-cancel-job="'+esc(job.id)+'">Cancel</button>';
  return '<div class="data-row job-inbox-row'+(done?' is-cleared':'')+'"><div class="job-inbox-details"><div class="row-label">'+
   esc(title(job.kind))+' '+pill(job.status,job.status==='completed'?'green':job.status==='failed'?'red':job.status==='running'?'amber':'')+
   '</div><div class="row-desc">'+esc(job.message||'')+'</div>'+
   (job.status==='running'?'<div class="meter" style="margin-top:9px"><div class="meter-fill" style="width:'+Math.max(0,Math.min(100,Number(job.progress)||0))+'%"></div></div>':'')+
   (job.error?'<p class="fine job-error">'+esc(job.error)+'</p>':'')+'</div><div class="job-inbox-actions">'+action+'</div></div>';
 }).join(''):empty('No notifications to show','New or active analysis jobs will appear here. Cleared job records remain available in recent history.');
 const footer='<div class="actions job-inbox-footer">'+
    btn(icon('rotate')+' Refresh','jobs','btn-small')+
    (showHistory?btn('Show notifications','jobs','btn-small'):btn('Show recent history','jobs-history','btn-small'))+
    btn('Refresh workspace','refresh','btn-small')+'</div>';
 return header+info+'<div class="data-list job-inbox-list" aria-live="polite">'+contents+'</div>'+footer;
}
async function clearJobNotifications(){
 const rows=await api('/api/jobs');
 const cleared=clearedJobIds();
 const toClear=rows.filter(job=>isFinishedJob(job)&&!cleared.has(job.id));
 for(const job of toClear)cleared.add(job.id);
 saveClearedJobIds(cleared);
 updateJobIndicator(rows);
 await openJobs();
 toast(toClear.length?toClear.length+' notification(s) cleared. Job history preserved.':'No finished notifications to clear.');
}
async function clearJobNotification(id){
 const job=await api('/api/jobs/'+encodeURIComponent(id));
 if(!isFinishedJob(job)){toast('Active jobs cannot be cleared; they remain visible until finished.',true);return;}
 const cleared=clearedJobIds();
 cleared.add(job.id);
 saveClearedJobIds(cleared);
 await openJobs();
 toast('Notification cleared. Job history preserved.');
}
async function openJobs(showHistory=false){
 try{
  const rows=await api('/api/jobs');
  updateJobIndicator(rows);
  openModal('Analysis jobs',renderJobInbox(rows,showHistory));
 }catch(error){toast(error.message,true);}
}
async function openImport(){
 const html=`<p class="fine" style="margin-bottom:20px">Upload an authorized dataset to this computer. NPZ files up to 256 MiB support MedMNIST train/val/test arrays; ZIP files up to 150 MiB require a root-level samples.csv with sample_id, image_path, label and split columns. No cloud transfer.</p>
 <form id="importForm"><div id="importFields"><div class="field"><label for="fileUpload">Dataset file (.npz or .zip)</label><input class="input" id="fileUpload" type="file" accept=".npz,.zip" required></div>
 <div class="field"><label for="datasetName">Dataset name</label><input class="input" id="datasetName" required minlength="2" maxlength="200" placeholder="e.g. DermaMNIST"></div>
 <div class="field-group"><div class="field"><label for="datasetSource">Source / provenance</label><input class="input" id="datasetSource" value="MedMNIST / Zenodo"></div><div class="field"><label for="datasetLicense">License / authorization</label><input class="input" id="datasetLicense" value="Verify dataset provider terms"></div></div>
 <div class="field"><label for="maxImages">Maximum NPZ images per split</label><input class="input" id="maxImages" type="number" min="10" max="10000" value="500"><small>The import manifest records whether sampling occurred. On an Intel Iris Xe laptop, begin with 500 images per split.</small></div></div>
 <section class="import-tracker" id="importTracker" hidden aria-label="Import progress">
  <div class="import-tracker-head"><span id="importPhase" class="import-phase-label">Preparing dataset…</span><strong class="import-percent" id="importPercent">0%</strong></div>
  <progress id="importProgress" max="100" value="0" aria-label="Dataset upload progress"></progress>
  <div class="import-working" id="importWorking" hidden aria-hidden="true"><span class="spinner"></span><span>Indexing research images on this computer…</span></div>
  <p class="import-message" id="importMessage" role="status" aria-live="polite">Preparing local upload.</p>
  <ol class="import-milestones"><li id="importMilestoneUpload" class="active">1. Upload</li><li id="importMilestoneIndex">2. Verify &amp; index images</li><li id="importMilestoneDone">3. Dataset ready</li></ol>
  <p class="fine">During indexing, progress cannot be measured precisely. Keep this tab open until the result appears.</p>
 </section>
 <div class="actions"><button type="submit" id="importSubmit" class="btn btn-primary">${icon('upload')} <span id="importSubmitLabel">Import local research data</span></button></div></form>`;
 openModal('Import dataset',html);
 const form=$('#importForm');
 form.addEventListener('submit',async e=>{
  e.preventDefault();if(datasetImportInProgress)return;
  const f=$('#fileUpload').files?.[0];if(!f)return;
  const button=$('#importSubmit'),buttonText=$('#importSubmitLabel'),status=$('#importTracker'),bar=$('#importProgress'),phase=$('#importPhase'),pct=$('#importPercent'),message=$('#importMessage');
  const stamp=(text)=>{message.textContent=text;};
  const mark=(stage)=>{
   const indexed=stage==='indexing',done=stage==='done';
   $('#importMilestoneUpload').className=indexed||done?'done':'active';
   $('#importMilestoneIndex').className=done?'done':indexed?'active':'';
   $('#importMilestoneDone').className=done?'done':'';
  };
  const limitMiB=uploadLimitMiB(f.name);
  if(f.size>limitMiB*1024*1024){status.hidden=false;phase.textContent='File too large';pct.textContent='';stamp(`${f.name} is ${(f.size/(1024*1024)).toFixed(1)} MiB and exceeds the ${limitMiB} MiB ${f.name.toLowerCase().endsWith('.npz')?'NPZ':'ZIP'} limit. Selecting fewer images per split does not reduce the original upload size.`);status.classList.add('import-error');return;}
  const b=new FormData(); // Inputs use IDs, so populate the upload payload explicitly.
  b.append('file',f);b.append('name',$('#datasetName').value);b.append('source',$('#datasetSource').value);b.append('license',$('#datasetLicense').value);b.append('max_per_split',$('#maxImages').value);
  datasetImportInProgress=true;status.hidden=false;status.classList.remove('import-error','import-complete');
  $('#importFields').querySelectorAll('input').forEach(el=>el.disabled=true);button.disabled=true;$('#modalClose').disabled=true;
  buttonText.textContent='Import in progress';phase.textContent='Uploading dataset';pct.textContent='0%';bar.hidden=false;$('#importWorking').hidden=true;bar.value=0;stamp(`Uploading ${f.name} (${(f.size/(1024*1024)).toFixed(1)} MB) to the local server…`);mark('upload');
  const onProgress=(n)=>{bar.value=n;pct.textContent=n+'%';};
  const onPhase=(stage)=>{if(stage==='indexing'){
   bar.hidden=true;$('#importWorking').hidden=false;pct.textContent='Processing';phase.textContent='Validating and indexing';
   stamp('Upload received. Validating file structure, extracting image samples and writing the local research index. This may take a while on CPU.');mark('indexing');
  }};
  try{
   const out=await uploadResearchDataset(b,onProgress,onPhase);
   datasetImportInProgress=false;$('#modalClose').disabled=false;
   state.did=out.dataset_id;storage.set('localStorage','mdf-dataset',out.dataset_id);
   await refresh(true);navigate('dna');
   status.classList.add('import-complete');bar.hidden=false;$('#importWorking').hidden=true;bar.value=100;
   pct.textContent='Complete';phase.textContent='Dataset imported successfully';mark('done');
   stamp('Your dataset is indexed locally and is now selected. Open Dataset DNA to inspect its images, splits and provenance.');
   button.disabled=false;button.type='button';buttonText.textContent='View Dataset DNA';
   button.onclick=()=>{closeModal();navigate('dna')};
   toast(`${f.name} imported successfully. Dataset DNA is ready.`);
  }catch(err){
   datasetImportInProgress=false;$('#modalClose').disabled=false;status.classList.add('import-error');bar.hidden=true;$('#importWorking').hidden=true;
   pct.textContent='Failed';phase.textContent='Import did not finish';stamp(err.message||String(err));
   button.disabled=false;buttonText.textContent='Retry import';
   $('#importFields').querySelectorAll('input').forEach(el=>el.disabled=false);
   toast('Dataset import failed. See the explanation in the import dialog.',true);
  }
 });
}
async function openDemo(){openModal('Generate synthetic research sandbox',`<p class="fine" style="margin-bottom:18px">Creates geometric phantoms, not medical images. Known label flips, exact copies, near copies and group overlaps are injected so detectors can be sanity-tested.</p><div class="field-group"><div class="field"><label for="demoCount">Number of base patterns</label><input class="input" id="demoCount" type="number" min="40" max="1200" value="128"></div><div class="field"><label for="demoSeed">Generation seed</label><input class="input" id="demoSeed" type="number" min="1" max="999999" value="42"></div></div><div class="actions">${btn(icon('plus')+' Create training sandbox','create-demo','btn-primary')}</div>`)}
async function createDemo(){const button=document.querySelector('[data-action="create-demo"]');if(button)button.disabled=true;const returnTo=state.view;try{const out=await api('/api/datasets/demo',{method:'POST',body:JSON.stringify({count:Number($('#demoCount').value),seed:Number($('#demoSeed').value)})});closeModal();state.did=out.dataset_id;storage.set('localStorage','mdf-dataset',out.dataset_id);await refresh(true);navigate(returnTo==='overview'?'dna':returnTo);toast('Created an entirely synthetic, local research sandbox.')}catch(e){toast(e.message,true);if(button)button.disabled=false}}
async function showExperiment(id){try{const e=await api('/api/experiments/'+id);openModal('Experiment manifest · '+title(e.kind),`<p class="fine">${esc(e.status)} · Research record ${esc(e.id)}</p><div class="scope-label" style="margin-top:18px">EXPERIMENT CONFIGURATION</div><div class="mono-box">${esc(JSON.stringify(e.config,null,2))}</div><div class="scope-label" style="margin-top:18px">RECORDED RESULT</div><div class="mono-box">${esc(JSON.stringify(e.result,null,2))}</div>`)}catch(e){toast(e.message,true)}}
async function handleAction(action){switch(action){case 'import':return openImport();case 'demo':return openDemo();case 'create-demo':return createDemo();case 'run-audit':return startAudit();case 'jobs':return openJobs();case 'jobs-history':return openJobs(true);case 'clear-job-notifications':return clearJobNotifications();case 'refresh':return refresh(true);case 'graph-zoom-in':state.graphUi.zoom=Math.min(1.5,Math.round((state.graphUi.zoom+0.25)*100)/100);return updateGraphExplorer();
 case 'graph-zoom-out':state.graphUi.zoom=Math.max(0.75,Math.round((state.graphUi.zoom-0.25)*100)/100);return updateGraphExplorer();
 case 'graph-reset':state.graphUi={search:'',severity:'all',links:'all',zoom:1};$('#main').innerHTML=renderGraph();drawGraph(state.graph);return;
 case 'failure-reset':state.failureCell='';return updateFailureExplorer();
 case 'rankings':{state.rankingBudget=Number($('#rankingBudget')?.value||4);const target=$('#rankingResult');if(target)target.innerHTML='<div class="rank-pending" role="status">Comparing real candidate order…</div>';state.rankings=await api('/api/datasets/'+state.did+'/rankings?budget='+state.rankingBudget);if(target)target.innerHTML=renderRankings();return;}case 'filter-findings':state.activeFilters={kind:$('#findingKind')?.value||'',status:$('#findingStatus')?.value||''};state.findingPage=1;return render();case 'filter-samples':state.dnaFilters={split:$('#dnaSplit')?.value||'',label:$('#dnaLabel')?.value||'',search:$('#dnaSearch')?.value||''};state.sampleFilter=dnaFilterQuery(state.dnaFilters);state.samplePage=1;return render();
 case 'clear-sample-filters':state.dnaFilters={split:'',label:'',search:''};state.sampleFilter=dnaFilterQuery(state.dnaFilters);state.samplePage=1;return render();case 'go-audit':return navigate('audit');case 'go-privacy':return navigate('privacy');case 'baseline-launch':return launchExperiment('baseline',{seed:42});case 'shortcut':return launchExperiment('shortcut',{seed:42});case 'impact':return launchExperiment('impact',{seed:42});case 'counterfactual-launch':{const sid=$('#counterSample')?.value;if(!sid)return toast('Select a research image first',true);return launchExperiment('counterfactual',{sample_id:sid,strength:Number($('#counterfactualAmount')?.value||40)/100})}case 'cross-launch':{const did=$('#crossTarget')?.value;if(!did)return toast('Select a target dataset first',true);return launchExperiment('cross_dataset',{target_dataset_id:did})}case 'scenario-launch':return launchExperiment('scenario',{seed:Number($('#scenarioSeed').value),label_flip_rate:Number($('#scenarioRate').value)});case 'verify-integrity':{if(!state.did)return toast('Select a dataset first',true);try{const info=await api('/api/datasets/'+state.did+'/verify');const target=$('#integrityResults');if(target)target.innerHTML=`<div class="notice ${info.passed?'':'warning'}" style="margin-top:12px"><strong>${info.passed?'Integrity check passed':'Integrity check found issues'}</strong><p>Files checked: ${number(info.checked_files)} · Problems: ${number(info.problem_count)}</p><p class="fine">${esc((info.problems||[]).slice(0,5).map(p=>p.kind+': '+(p.sample_id||'manifest')).join('; ') || 'No recorded mismatches.')}</p></div>`;}catch(e){toast(e.message,true)}return;}case 'download-json':window.location.href='/api/datasets/'+state.did+'/report?format=json';return;case 'auth-prompt':openModal('Local access token',`<div class="field"><label for="authToken">MDF_ACCESS_TOKEN</label><input class="input" type="password" id="authToken" placeholder="Enter configured token"></div>${btn('Authenticate','save-token','btn-primary')}`);return;case 'save-token':storage.set('sessionStorage','mdf-token',$('#authToken').value);await api('/api/session',{method:'POST'});toast('Authenticated for this local session');return;default:toast('Unknown control: '+action,true)}}
document.addEventListener('click',async e=>{
 const nav=e.target.closest('[data-view]');if(nav){navigate(nav.dataset.view);return}
 const act=e.target.closest('[data-action]');if(act){act.disabled=true;try{await handleAction(act.dataset.action)}catch(err){toast(err.message,true)}finally{if(act.isConnected)act.disabled=false}return}
 const matrix=e.target.closest('[data-confusion]');if(matrix){state.failureCell=matrix.dataset.confusion;updateFailureExplorer();return}
 const chart=e.target.closest('[data-dna-chart]');if(chart){setDnaChartFilter(chart.dataset.dnaChart,chart.dataset.dnaValue);render();return}
 const dataset=e.target.closest('[data-dataset]');if(dataset){changeDataset(dataset.dataset.dataset);return}
 const f=e.target.closest('[data-finding]');if(f){openFinding(f.dataset.finding);return}
 const s=e.target.closest('[data-sample]');if(s){openSample(s.dataset.sample);return}
 const rev=e.target.closest('[data-review]');if(rev){const [id,decision]=rev.dataset.review.split(':');const notes=$('#reviewNotes')?.value||'';if(decision==='confirmed'&&notes.trim().length<8){toast('Please explain the evidence for confirming a concern (at least 8 characters).',true);return}try{await api('/api/findings/'+id+'/review',{method:'POST',body:JSON.stringify({decision,notes,reviewer:$('#reviewer')?.value||'Local researcher',duration_seconds:Number($('#reviewDuration')?.value)||null})});closeModal();toast('Decision preserved in review history.');await refresh(true)}catch(err){toast(err.message,true)}return}
 const exp=e.target.closest('[data-experiment]');if(exp){launchExperiment(exp.dataset.experiment,{seed:42});return}
 const ed=e.target.closest('[data-experiment-detail]');if(ed){showExperiment(ed.dataset.experimentDetail);return}
 const dismiss=e.target.closest('[data-dismiss-job]');if(dismiss){dismiss.disabled=true;try{await clearJobNotification(dismiss.dataset.dismissJob)}catch(error){toast(error.message,true)}finally{if(dismiss.isConnected)dismiss.disabled=false}return}
 const cancel=e.target.closest('[data-cancel-job]');if(cancel){try{await api('/api/jobs/'+cancel.dataset.cancelJob+'/cancel',{method:'POST'});toast('Cancellation requested');openJobs()}catch(err){toast(err.message,true)}return}
 const page=e.target.closest('[data-page]');if(page){const [kind,dir]=page.dataset.page.split(':');if(kind==='sample'){state.samplePage=Math.max(1,state.samplePage+(dir==='next'?1:-1))}else if(kind==='counter'){state.counterPage=Math.max(1,state.counterPage+(dir==='next'?1:-1));state.counterSampleId=null}else{state.findingPage=Math.max(1,(state.findingPage||1)+(dir==='next'?1:-1))}render();return}
});
$('#themeToggle').addEventListener('click',()=>{const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=theme;storage.set('localStorage','mdf-theme',theme);$('#themeToggle').setAttribute('aria-label',theme==='dark'?'Switch to light mode':'Switch to dark mode')});
const storedTheme=storage.get('localStorage','mdf-theme');if(storedTheme==='dark'){document.documentElement.dataset.theme='dark';$('#themeToggle').setAttribute('aria-label','Switch to light mode')}
$('#importTrigger').addEventListener('click',openImport);$('#jobsTrigger').addEventListener('click',()=>openJobs());$('#modalClose').addEventListener('click',closeModal);
$('#modalBackdrop').addEventListener('click',e=>{if(e.target===$('#modalBackdrop'))closeModal()});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();if(e.key==='Tab'&&!$('#modalBackdrop').hidden){const focusable=[...$('#modal').querySelectorAll('button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex="0"]')];if(focusable.length){const first=focusable[0],last=focusable[focusable.length-1];if(e.shiftKey&&document.activeElement===first){last.focus();e.preventDefault()}else if(!e.shiftKey&&document.activeElement===last){first.focus();e.preventDefault()}}}});
document.addEventListener('input',e=>{if(e.target.id==='counterfactualAmount'){state.counterStrength=Number(e.target.value);updateCounterfactualPreview()}
 if(e.target.id==='graphSearch'){state.graphUi.search=e.target.value;updateGraphExplorer()}
});
document.addEventListener('change',e=>{
 if(e.target.id==='graphSeverity'){state.graphUi.severity=e.target.value;updateGraphExplorer()}
 if(e.target.id==='graphLinks'){state.graphUi.links=e.target.value;updateGraphExplorer()}
 if(e.target.id==='counterfactualMode'){state.counterMode=e.target.value;updateCounterfactualPreview()}if(e.target.id==='counterSample'){const sample=state.samples?.items?.find(s=>s.id===e.target.value);if(sample){state.counterSampleId=sample.id;for(const id of ['counterOriginalImage','counterModifiedImage']){const el=$('#'+id);if(el)el.src=sample.image_url}updateCounterfactualPreview()}}});
$('#datasetSelect').addEventListener('change',e=>changeDataset(e.target.value));
$('#menuToggle').addEventListener('click',()=>{$('#sidebar').classList.toggle('open');const opened=$('#sidebar').classList.contains('open');$('#mobileOverlay').hidden=!opened;$('#menuToggle').setAttribute('aria-expanded',String(opened))});
$('#mobileOverlay').addEventListener('click',()=>{$('#sidebar').classList.remove('open');$('#mobileOverlay').hidden=true;$('#menuToggle').setAttribute('aria-expanded','false')});
window.addEventListener('hashchange',()=>{const view=location.hash.replace('#/','');if(view&&view!==state.view){state.view=RENDER[view]?view:'overview';render()}});
async function pollJobs(){try{const rows=await api('/api/jobs');updateJobIndicator(rows);
 const terminal=rows.filter(j=>['completed','failed','cancelled'].includes(j.status)).map(j=>j.id+':'+j.status).join('|');
 if(pollJobs.last!==undefined&&pollJobs.last!==terminal){await loadCore();await render()}
 pollJobs.last=terminal;
 }catch{} }
(async()=>{try{const start=location.hash.replace('#/','');state.view=RENDER[start]?start:'overview';await loadCore();await render();pollJobs.last=undefined;refreshTimer=setInterval(pollJobs,4500)}catch(e){renderError(e)}})();
