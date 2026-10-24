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

test('actual story routine disclosures use zero, singular and plural record labels',async()=>{
 for(const count of [0,1,2]){
  const initialLife={history:{chapters:[{at:1,title:'A short walk',routines:[{title:'Everyday activity',count,beats:[]}]}]}};
  const h=await shellHarness({path:'/lives/life_a/history',initialLife}),markup=h.node('#story-content').innerHTML;
  assert.ok(markup.includes(`Everyday activity · ${count} record${count===1?'':'s'}`));assert.doesNotMatch(markup,/\b1 records\b/);assert.match(markup,/<details><summary/);
 }
});
