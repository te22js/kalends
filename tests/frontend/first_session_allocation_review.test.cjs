'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {allocationTotal}=require('../../kalends/experience_os/static/product/app.js');
const {shellHarness}=require('./helpers/product_harness.cjs');

const initialLife=report=>({
 life:{id:'life_a',template_id:'shared_observatory',revision:0,minute:60},
 snapshot:{setting:'commons',minute:60,command_count:0,allocation:null,promises:{},requests:{},credits:12,own_reports:[{tick:0,payload:{value:'fragile',as_of:0}}]},
 guide:{enabled:false,known:{report}},time:{known_stops:[{kind:'public_round_deadline',at:1439}]}
});
async function review(report,allocation={team_a:4,team_b:4,team_c:4}) {
 const h=await shellHarness({initialLife:initialLife(report),responder:({url,body})=>url==='/product/api/propose'?{body:{proposal_id:'allocation_review',action:body.action}}:undefined});
 await h.inputAllocation(allocation);
 h.node('#allocation-form').elements=Object.fromEntries(Object.entries(allocation).map(([id,value])=>[id,{value:String(value)}]));
 await h.submitId('allocation-form');return h;
}

test('allocation review repeats the total and admitted dated capacity before explicit confirmation',async()=>{
 const h=await review({usable:8,as_of:0,kind:'testimony',source:'Mira'}),markup=h.node('#review-content').innerHTML;
 assert.equal(h.node('#review-dialog').open,true);
 for(const phrase of ['Total allocation: 12 of 12 rated units.','8 usable units','Day 1 · 00:00 (world minute 0)','may be out of date','exceeds the reported usable capacity by 4 units','If that condition still holds','Amir → Mira → Lin','Settlement: Day 1 · 23:59','Delivery has not happened yet.'])assert.ok(markup.includes(phrase),phrase);
 assert.equal(h.node('#confirm-choice').disabled,false);
 assert.equal(h.requests.some(r=>r.url.endsWith('/confirm')),false);
 assert.equal(h.life.life.revision,0);
});

test('allocation review uses public guide evidence only and handles no report or missing date honestly',async()=>{
 const unknown=await review(null);assert.match(unknown.node('#review-content').innerHTML,/Usable capacity is unconfirmed in your admitted evidence/);assert.doesNotMatch(unknown.node('#review-content').innerHTML,/8 units|world minute 0|exceeds the reported/);
 const undated=await review({usable:8,kind:'direct observation'},{team_a:4,team_b:4,team_c:0});assert.match(undated.node('#review-content').innerHTML,/Your direct inspection described/);assert.match(undated.node('#review-content').innerHTML,/observation date unavailable/);assert.doesNotMatch(undated.node('#review-content').innerHTML,/world minute 0|exceeds the reported/);
});

test('invalid allocation entries suppress totals and reassuring report comparisons',async()=>{
 const h=await shellHarness({initialLife:initialLife({usable:8,as_of:0,kind:'testimony'})});
 for(const value of [-1,1.5,'',13,'not a number']){
  const allocation={team_a:value,team_b:4,team_c:4};await h.inputAllocation(allocation);
  assert.equal(allocationTotal(allocation),null);assert.match(h.node('#allocation-total').innerHTML,/Total unavailable/);assert.match(h.node('#allocation-total').innerHTML,/whole number from 0 to 12/);assert.doesNotMatch(h.node('#allocation-total').innerHTML,/fits your last dated report|Total:|exceeds the 8/);
 }
 await h.inputAllocation({team_a:0,team_b:4,team_c:4});assert.match(h.node('#allocation-total').innerHTML,/Total: 8 of 12/);assert.match(h.node('#allocation-total').innerHTML,/fits your last dated report/);
 assert.equal(h.requests.some(r=>/\/(propose|confirm)$/.test(r.url)),false);
});

test('next-round review preserves the prior settlement without claiming another execution',async()=>{
 const initial=initialLife(null);initial.snapshot.minute=1439;initial.snapshot.round_closed=true;
 const h=await shellHarness({initialLife:initial});await h.clickData({guideAction:'next_round'});
 const markup=h.node('#known-deadlines').innerHTML;
 assert.equal(h.node('#time-dialog').open,true);assert.match(markup,/Advance from Day 1 · 23:59 to Day 2 · 00:00: 1 world minute\./);assert.match(markup,/No open promise is recorded for the upcoming step\. The previous settlement remains in your history\./);assert.doesNotMatch(markup,/Finishing still executes/);assert.equal(h.requests.some(r=>r.url.endsWith('/advance')),false);
});

test('settled allocation summary uses recorded delivery and drops prospective review advice',async()=>{
 const initial=initialLife({usable:8,as_of:0,kind:'testimony'});initial.snapshot.round_closed=true;initial.snapshot.allocation={team_a:4,team_b:4,team_c:4};initial.guide.result={at:1439,allocation:initial.snapshot.allocation,executed:{team_a:4,team_b:4,team_c:0},explanation:[]};
 const h=await shellHarness({initialLife:initial});await h.inputAllocation({team_a:-1,team_b:4,team_c:4});
 const markup=h.node('#allocation-total').innerHTML;
 assert.match(markup,/Total allocated: 12 units/);assert.match(markup,/Actual delivery: 8 units/);assert.match(markup,/This round has settled/);assert.doesNotMatch(markup,/may review|If that condition|fits your|Total unavailable/);
 const unavailable=initialLife(null);unavailable.snapshot.round_closed=true;const absent=await shellHarness({initialLife:unavailable});assert.match(absent.node('#allocation-total').innerHTML,/This round has settled/);assert.doesNotMatch(absent.node('#allocation-total').innerHTML,/Actual delivery|0 units/);
});
