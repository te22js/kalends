'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {shellHarness}=require('./helpers/product_harness.cjs');

test('actual Pompeii saved-life cards show one day label with the recorded local world time',async()=>{
 for(const [minute,day] of [[67,1],[1507,2]]){
  const h=await shellHarness({path:'/your-worlds',initialLife:{life:{id:'life_a',template_id:'pompeii_life',participant:'Aelia',minute,day,revision:39,location:'street',save_status:'saved'}}}),markup=h.node('#main').innerHTML;
  assert.ok(markup.includes(`Aelia · Day ${day} · 09:07 · street`));assert.doesNotMatch(markup,/Day \d+ · Day \d+/);assert.equal(h.requests.some(r=>r.method==='POST'),false);
 }
});
