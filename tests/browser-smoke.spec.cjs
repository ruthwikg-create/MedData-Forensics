/* Browser-level smoke checks against the real FastAPI server.
   Everything here is generated synthetic research data, never patient images. */
const {test,expect}=require('@playwright/test');

test.use({baseURL:'http://127.0.0.1:8765',viewport:{width:1280,height:900}});
test.setTimeout(150000);

async function sandbox(request,seed,count=64){
 const response=await request.post('/api/datasets/demo',{data:{seed,count}});
 expect(response.ok(),await response.text()).toBeTruthy();
 return (await response.json()).dataset_id;
}

test('Dataset DNA and Evidence Graph have working filters and zoom',async({page,request},testInfo)=>{
 const did=await sandbox(request,963,64);
 await page.goto('/#/dna');
 await page.locator('#datasetSelect').selectOption(did);
 await expect(page.getByRole('heading',{name:'Dataset DNA'})).toBeVisible();
 await page.locator('[data-dna-chart="split"][data-dna-value="train"]').click();
 await expect(page.locator('#dnaSplit')).toHaveValue('train');
 await page.locator('[data-action="clear-sample-filters"]').click();
 await expect(page.locator('#dnaSplit')).toHaveValue('');
 await page.locator('[data-view="graph"]').click();
 await expect(page.getByRole('heading',{name:'Forensic Evidence Graph'})).toBeVisible();
 await expect(page.locator('#nodeGraph svg')).toBeVisible();
 await page.locator('#graphSearch').fill('phantom-0001');
 await expect(page.locator('.graph-results-count')).toContainText('matching records');
 await expect(page.locator('#nodeGraph')).toContainText('phantom-0001');
 await page.locator('[data-action="graph-zoom-in"]').click();
 await expect(page.locator('#graphZoomValue')).toHaveText('125%');
 await page.locator('#graphSeverity').selectOption('high');
 await page.locator('[data-action="graph-reset"]').click();
 await expect(page.locator('#graphSearch')).toHaveValue('');
 await expect(page.locator('#graphZoomValue')).toHaveText('100%');
 await page.screenshot({path:testInfo.outputPath('evidence-graph-desktop.png'),fullPage:true});
});

test('CPU baseline completes and confusion matrix opens recorded predictions',async({page,request},testInfo)=>{
 const did=await sandbox(request,964,64);
 const response=await request.post('/api/datasets/'+did+'/experiments',{
   data:{kind:'baseline',config:{seed:42}}});
 expect(response.ok(),await response.text()).toBeTruthy();
 const {job_id}=await response.json();
 let job=null;
 for(let i=0;i<85;i++){
  const status=await request.get('/api/jobs/'+job_id);
  expect(status.ok()).toBeTruthy();
  job=await status.json();
  if(['completed','failed','cancelled'].includes(job.status))break;
  await new Promise(resolve=>setTimeout(resolve,900));
 }
 expect(job?.status,'Baseline job result: '+JSON.stringify(job)).toBe('completed');
 await page.goto('/#/failures');
 await page.locator('#datasetSelect').selectOption(did);
 await expect(page.getByRole('heading',{name:'Model Failure Explorer'})).toBeVisible();
 await expect(page.locator('.cm-grid button[data-confusion]').first()).toBeVisible();
 await page.locator('.cm-grid button[data-confusion]').first().click();
 await expect(page.locator('#failureGallery')).toContainText('Actual');
 await expect(page.locator('[data-action="failure-reset"]')).toBeVisible();
 await page.screenshot({path:testInfo.outputPath('baseline-interactive-desktop.png'),fullPage:true});
});

test('mobile navigation, theme and graph controls do not overflow viewport',async({page,request},testInfo)=>{
 const did=await sandbox(request,965,40);
 await page.setViewportSize({width:390,height:844});
 await page.goto('/#/');
 await page.locator('#datasetSelect').selectOption(did);
 await page.locator('#menuToggle').click();
 await expect(page.locator('#sidebar')).toHaveClass(/open/);
 await page.locator('[data-view="graph"]').click();
 await expect(page.getByRole('heading',{name:'Forensic Evidence Graph'})).toBeVisible();
 await expect(page.locator('#menuToggle')).toHaveAttribute('aria-expanded','false');
 await page.locator('#themeToggle').click();
 await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 await expect(page.locator('#graphSearch')).toBeVisible();
 const pageOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2);
 expect(pageOverflow).toBe(false);
 await page.screenshot({path:testInfo.outputPath('graph-mobile-dark.png'),fullPage:true});
});

async function waitForCompletedJob(request,jobId){
 let job=null;
 for(let i=0;i<100;i++){
  const response=await request.get('/api/jobs/'+jobId);
  expect(response.ok()).toBeTruthy();
  job=await response.json();
  if(['completed','failed','cancelled'].includes(job.status))break;
  await new Promise(resolve=>setTimeout(resolve,900));
 }
 expect(job?.status,'Job result: '+JSON.stringify(job)).toBe('completed');
 return job;
}

test('Cross-Dataset, Impact and Reproducibility work through their real UI controls',async({page,request})=>{
 const source=await sandbox(request,971,64),target=await sandbox(request,972,64);
 const baseline=await request.post('/api/datasets/'+source+'/experiments',{data:{kind:'baseline',config:{seed:42}}});
 expect(baseline.ok(),await baseline.text()).toBeTruthy();
 await waitForCompletedJob(request,(await baseline.json()).job_id);

 await page.goto('/#/cross');
 await page.locator('#datasetSelect').selectOption(source);
 await expect(page.getByRole('heading',{name:'Cross-Dataset Reliability Lab'})).toBeVisible();
 await expect(page.locator('#crossTarget')).toBeVisible();
 await page.locator('#crossTarget').selectOption(target);
 await page.locator('#crossIndependenceConfirm').check();
 await expect(page.locator('[data-action="cross-launch"]')).toBeEnabled();
 const crossResponsePromise=page.waitForResponse(response=>
  response.request().method()==='POST'&&/\/api\/datasets\/[^/]+\/experiments$/.test(new URL(response.url()).pathname));
 await page.locator('[data-action="cross-launch"]').click();
 const crossResponse=await crossResponsePromise;
 expect(crossResponse.ok(),await crossResponse.text()).toBeTruthy();
 const crossJob=await crossResponse.json();
 await waitForCompletedJob(request,crossJob.job_id);
 await page.reload();await page.goto('/#/cross');
 await page.locator('#datasetSelect').selectOption(source);
 await expect(page.getByText('External macro-F1')).toBeVisible();

 const impact=await sandbox(request,973,64);
 const audit=await request.post('/api/datasets/'+impact+'/audit');
 expect(audit.ok(),await audit.text()).toBeTruthy();
 await waitForCompletedJob(request,(await audit.json()).job_id);
 const findingResponse=await request.get('/api/datasets/'+impact+'/findings?size=200');
 const findings=(await findingResponse.json()).items;
 const sampleResponse=await request.get('/api/datasets/'+impact+'/samples?split=train&size=100');
 const trainIds=new Set((await sampleResponse.json()).items.map(item=>item.id));
 const supported=new Set(['split_leakage','group_overlap','exact_duplicate','pixel_duplicate','near_duplicate','label_suspicion']);
 const finding=findings.find(item=>supported.has(item.kind)&&[item.sample_id,item.linked_id].some(id=>id&&trainIds.has(id)));
 expect(finding,'Synthetic audit should produce a reviewable training-linked finding').toBeTruthy();
 const review=await request.post('/api/findings/'+finding.id+'/review',{data:{
  reviewer:'Browser QA','decision':'confirmed',
  notes:'Confirmed for the synthetic workflow test after inspecting linked evidence.'}});
 expect(review.ok(),await review.text()).toBeTruthy();
 const impactReadyResponse=await request.get('/api/datasets/'+impact+'/impact-readiness');
 expect(impactReadyResponse.ok()).toBeTruthy();
 const impactReady=await impactReadyResponse.json();
 expect(impactReady.audit_completed).toBe(true);
 expect(impactReady.confirmed_training_samples).toBeGreaterThan(0);
 expect(impactReady.ready,JSON.stringify(impactReady.reasons)).toBe(true);

 // The dataset was created through the API after the SPA had already loaded.
 // Reload so the active-dataset selector includes the new test collection.
 await page.reload();
 await page.goto('/#/impact');
 await page.locator('#datasetSelect').selectOption(impact);
 await expect(page.getByText('Ready to run')).toBeVisible();
 const impactResponsePromise=page.waitForResponse(response=>
  response.request().method()==='POST'&&new URL(response.url()).pathname.endsWith('/experiments'));
 await page.locator('[data-action="impact"]').click();
 const impactResponse=await impactResponsePromise;
 expect(impactResponse.ok(),await impactResponse.text()).toBeTruthy();
 const impactJob=await impactResponse.json();
 await waitForCompletedJob(request,impactJob.job_id);
 await page.reload();await page.goto('/#/impact');
 await page.locator('#datasetSelect').selectOption(impact);
 await expect(page.getByText('Samples excluded')).toBeVisible();

 await page.goto('/#/failures');
 await page.locator('#datasetSelect').selectOption(source);
 await expect(page.locator('.cm-grid button[data-confusion]').first()).toBeVisible();

 await page.goto('/#/repro');
 await page.locator('#datasetSelect').selectOption(source);
 await expect(page.getByRole('heading',{name:'Reproducibility Engine'})).toBeVisible();
 await expect(page.getByText('Dataset fingerprint')).toBeVisible();
 const downloadPromise=page.waitForEvent('download');
 await page.locator('[data-action="download-repro"]').click();
 const download=await downloadPromise;
 expect(download.suggestedFilename()).toContain('_repro.json');
});
