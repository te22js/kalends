'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {describeAction}=require('../../kalends/experience_os/static/product/app.js');
const {shellHarness}=require('./helpers/product_harness.cjs');

async function reflection(choices) {
 return shellHarness({path:'/lives/life_a/reflect',responder:({url})=>url.startsWith('/product/api/reflect?')?{body:{choices}}:undefined});
}

test('reflection defaults to the latest accepted decision even after later walking and never executes it',async()=>{
 const choices=[{index:0,at:0,action:{action:'move'},then_evidence:[{title:'Arrival'}]},{index:1,at:2,action:{action:'hear_dispute'},then_evidence:[]},{index:37,at:16,action:{action:'support_market'},then_evidence:[{at:8,title:'Sabina’s copied account'}]},{index:38,at:36,action:{action:'move'},then_evidence:[]}];
 const h=await reflection(choices);
 assert.equal(h.node('#reflect-choice').value,'37');assert.match(h.node('#story-content').innerHTML,/<option value="37" selected>.*Pay for the market delivery/);assert.doesNotMatch(h.node('#story-content').innerHTML,/support market|hear dispute/);assert.match(h.node('#then-evidence').innerHTML,/Sabina’s copied account/);assert.equal(h.requests.some(r=>r.url.endsWith('/fork')||r.url.endsWith('/confirm')),false);
 await h.change('reflect-choice',{value:'1'});assert.match(h.node('#then-evidence').innerHTML,/No earlier admitted evidence/);
 assert.equal(describeAction({action:'hear_dispute'}),'Hear an account of the delivery dispute');
});

test('a movement-only history selects its latest accepted walk and an empty history has no invented choice',async()=>{
 const h=await reflection([{index:3,at:1,action:{action:'move'}},{index:8,at:4,data:{action:'move'}}]);assert.equal(h.node('#reflect-choice').value,'8');assert.match(h.node('#story-content').innerHTML,/<option value="8" selected>/);
 const empty=await reflection([]);assert.match(empty.node('#story-content').innerHTML,/No accepted participant action/);assert.doesNotMatch(empty.node('#story-content').innerHTML,/<option /);
});

test('reflection labels the recent-eight excerpt and keeps the entire admitted prefix available read-only',async()=>{
 const evidence=[{at:0,title:'Sabina <private to admitted> account'},...Array.from({length:9},(_,i)=>({at:i+1,title:`Admitted record ${i+1}`}))];
 const h=await reflection([{index:20,at:16,action:{action:'support_market'},then_evidence:evidence}]),markup=h.node('#then-evidence').innerHTML;
 assert.match(markup,/Most recent 8 of 10 admitted records/);assert.match(markup,/<details><summary>Earlier admitted records \(2\)<\/summary>/);assert.doesNotMatch(markup,/<details open/);assert.match(markup,/Sabina &lt;private to admitted&gt; account/);assert.equal((markup.match(/class="evidence-item"/g)||[]).length,10);assert.equal(h.requests.some(r=>r.url.endsWith('/fork')),false);
});
