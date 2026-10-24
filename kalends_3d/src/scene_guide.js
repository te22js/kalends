/* Presentation of the host's saved-life guide. This module never advances a
 * tutorial or writes to the world. Only accepted server state can do that. */
const string=(value,max=1400)=>typeof value==='string'?value.slice(0,max):'';
const object=value=>value&&typeof value==='object'&&!Array.isArray(value)?value:{};
const ACTIONS=new Set(['help','history','toggle','resume','begin','hint','review','complete','controls','skip-history']);

export function guideView(value){
  const raw=object(value),step=object(raw.step),action=object(step.action),hint=object(raw.hint),target=object(hint.target);
  return {version:string(raw.version,80),enabled:raw.enabled===true,learn:raw.learn===true,
    step:{id:string(step.id,80),title:string(step.title,180),body:string(step.body),hint:string(step.hint),
      time_policy:string(step.time_policy,600),action:{kind:string(action.kind,50),label:string(action.label,120),
        id:string(action.id,80),target:string(action.target,80),recipient:string(action.recipient,80),
        location:string(action.location,80),card_id:string(action.card_id||action.card,80)}},
    hint:{text:string(hint.text,600),target:['person','location'].includes(target.type)&&string(target.id,80)?
      {type:target.type,id:string(target.id,80),person:string(target.person,80),basis:string(target.basis,240),
        ...(Number.isFinite(target.x)&&Number.isFinite(target.y)?{x:target.x,y:target.y}:{}),
        ...(Number.isFinite(target.at)?{at:target.at}:{})}:null}};
}

export function installSceneGuideHost({windowObject=globalThis.window,onGuide=()=>{},onAction=()=>{}}={}){
  const host=windowObject;
  if(!host||host.parent===host)return {hosted:false,request(){return false;},destroy(){}};
  const origin=host.location.origin,lifeId=new URL(host.location.href).searchParams.get('experience')||'pompeii_life';
  const receive=event=>{const data=event.data;if(event.origin!==origin||event.source!==host.parent||!data||data.life_id!==lifeId)return;
    if(data.kind==='kalends:guide')onGuide(guideView(data.guide));
    else if(data.kind==='kalends:guide-action'&&data.action==='primary')onAction('primary');};
  host.addEventListener('message',receive);
  return {hosted:true,request(action,extra={}){if(!ACTIONS.has(action))return false;
    host.parent.postMessage({kind:'kalends:guide-request',life_id:lifeId,action,
      ...(string(extra.card_id,80)?{card_id:string(extra.card_id,80)}:{}),
      ...(string(extra.location,80)?{location:string(extra.location,80)}:{})},origin);return true;},
    destroy(){host.removeEventListener('message',receive);}};
}

/** A guide may name a public meeting place, never an unseen person's latest
 * coordinates. The caller must use both rendered and authoritative proximity. */
export function knownGuideTarget(guide,world,isNear=()=>false){
  const target=guide?.hint?.target;if(!target||!world)return null;
  if(target.type==='person')return isNear(target.id)&&world.nearby?.includes(target.id)?{type:'person',id:target.id}:null;
  // `street` is an existing canonical navigation floor, represented by public
  // rectangles in map.streets rather than an entry in map.locations.
  const publicStreet=target.id==='street'&&Number.isFinite(target.x)&&Number.isFinite(target.y)&&world.map?.streets?.some(r=>
    [r.x,r.y,r.w,r.h].every(Number.isFinite)&&target.x>=r.x&&target.x<=r.x+r.w&&target.y>=r.y&&target.y<=r.y+r.h);
  if(!world.map?.locations?.some(p=>p.id===target.id)&&!publicStreet)return null;
  return {type:'location',id:target.id,...(Number.isFinite(target.x)&&Number.isFinite(target.y)?
    {x:target.x,y:target.y,person:target.person,...(Number.isFinite(target.at)?{at:target.at}:{}),...(target.basis?{basis:target.basis}:{})}:{})};
}

export function sceneActivity(actor,{moving=false,talking=false}={}){
  if(talking)return 'In conversation';
  if(moving)return 'Walking';
  const activity=string(actor?.activity,150);
  return activity?activity.charAt(0).toUpperCase()+activity.slice(1):'At this place';
}

// A context may describe an owner-held order. The participant must receive a
// copy through the supported action before its text becomes a reading topic.
export function admittedTopics(context,world){
  const documentTopics=new Set(['market_receipt','household_tablet','loading_record']);
  const admitted=new Set((world?.player?.documents||[]).map(d=>d.id));
  return (context?.topics||[]).filter(topic=>!documentTopics.has(topic.id)||admitted.has(topic.id));
}

const OPENINGS=new Map([
  ['Six sacks, two buyers, and somehow my bowls are the ones left empty. I paid Marcus. Ask him what changed.',
    'I paid Marcus for flour for my counter. Now the household is claiming the cart. Can you find out what happened?'],
  ['The order was ready at first light. That is what my message said. Ready is not the same as carried to your door.',
    'My message said the flour was ready at first light. That did not mean it had been delivered. Ask to check the loading account before drawing a conclusion.'],
  ['I was told to repeat the quantity, not argue about it. If you want the instructions, ask plainly.',
    'I carry the household’s delivery instructions. Ask me to repeat the quantity I was sent to carry. I cannot promise you the household’s money.'],
  ["Four sacks were reserved for this house. I will hear terms, not an accusation delivered on someone else's word.",
    'This household reserved four sacks of flour. I can discuss an arrangement. Hear the accounts and review the terms before you agree.'],
  ['A cart can stand still all morning while people make speeches. Someone must still bake.',
    'I bake and sell bread. I need flour and reliable help. You can ask about my work or review an available offer.'],
  ['If you want work, there is work here. The household pays for extra help. Do not mistake that for my freedom to leave.',
    'I am enslaved in this fullery. I cannot leave. The household pays free workers for extra help; you can ask about a shift.'],
]);
export function greetingCopy(value){const text=typeof value==='string'?value:value?.text||'';return OPENINGS.get(text)||text;}
export function topicCopy(topic){
  if(topic?.id==='memory'&&topic.text==='We have no consequential shared dealing in my retained memory yet.')return 'I don’t remember us doing business before.';
  if(topic?.id==='goals'&&typeof topic.text==='string'){
    const [aim,...rest]=topic.text.split('. For now, I must ');
    if(rest.length)return 'I need to '+aim.charAt(0).toLowerCase()+aim.slice(1)+'. For now, I must '+rest.join('. For now, I must ');
  }
  return string(topic?.text);
}
export const topicLabel=topic=>({role:'What is your work here?',goals:'What do you need now?',memory:'Do you remember our dealings?',news:'Do you have a dated report?'}[topic?.id]||string(topic?.label,160));
export function quantityCopy(value,singular,plural=singular+'s'){
  return Number.isFinite(value)?value+' '+(value===1?singular:plural):'Quantity unknown';
}
export function contractCopy(contract){return (contract.delivered??0)+' of '+quantityCopy(contract.quantity??2,'flour unit')+' delivered.';}
export function choiceDetails(choice){
  const description=string(choice?.description).trim(),cost=string(choice?.cost,600).trim().replace(/world minutes?/g,match=>match.endsWith('s')?'minutes':'minute'),reason=string(choice?.reason).trim();
  const sentence=value=>value&&!/[.!?…]$/.test(value)?value+'.':value,details=[];
  if(description&&description!==cost)details.push({kind:'description',text:sentence(description)});
  if(cost)details.push({kind:'cost',text:sentence('Cost: '+cost)});
  if(choice?.enabled===false&&reason&&reason!==description&&reason!==cost)details.push({kind:'reason',text:sentence(reason.startsWith('Needs ')?'This action needs '+reason.slice(6):reason)});
  return details;
}
export function confirmationLabel(action,speaker,cost){
  const payment=typeof cost==='string'?cost.match(/^(\d+) coins?\b/):null;
  if(action==='support_market'&&payment)return 'Pay '+payment[1]+(Number(payment[1])===1?' coin':' coins');
  return ({hear_dispute:'Hear '+speaker+'’s account',examine_receipt:'Copy this account',examine_tablet:'Copy these instructions',
    verify_cart:'Pay for this check',inspect:'Pay for this inspection',work:'Start this shift',decline_dispute:'Leave the decision to the buyers',
    reflect:'Ask about our dealings',support_market:'Confirm arrangement',guarantee_household:'Confirm arrangement',mediate:'Confirm arrangement',
    talk:'Ask '+speaker}[action]||'Confirm this action');
}

/** Position HTML markers without changing their world anchors or hit actions.
 * Priority markers keep the closest available position; secondary labels use
 * compact measured boxes. All labels remain keyboard and pointer reachable. */
export function layoutSceneLabels(labels,width,height){
  const placed=[],result=new Map(),margin=8,gap=7;
  const offsets=[];for(const dy of [0,-22,22,-44,44,-66,66,-88,88])for(const dx of [0,-28,28,-56,56,-84,84])offsets.push({dx,dy});
  offsets.sort((a,b)=>Math.abs(a.dy)+Math.abs(a.dx)*1.3-Math.abs(b.dy)-Math.abs(b.dx)*1.3);
  for(const label of [...labels].sort((a,b)=>(b.priority||0)-(a.priority||0))){
    const w=Math.min(label.width,Math.max(1,width-margin*2)),h=Math.min(label.height,Math.max(1,height-margin*2));
    let chosen;
    for(const {dx,dy} of offsets){const x=Math.max(margin+w/2,Math.min(width-margin-w/2,label.x+dx)),y=Math.max(margin+h,Math.min(height-margin,label.y+dy));
      const box={left:x-w/2,right:x+w/2,top:y-h,bottom:y};
      if(!chosen)chosen={x,y,box};
      if(!placed.some(p=>box.left<p.right+gap&&box.right>p.left-gap&&box.top<p.bottom+gap&&box.bottom>p.top-gap)){chosen={x,y,box};break;}
    }
    placed.push(chosen.box);result.set(label.id,{x:chosen.x,y:chosen.y});
  }
  return result;
}

export function timeReview(world,minutes){
  const from=Number(world?.minute)||0,to=from+minutes,known=[];
  for(const c of world?.player?.commitments||[]){const due=Number(c.deadline??c.due);
    if(c.status==='open'&&Number.isFinite(due)&&due>=from&&due<=to)known.push({at:due,title:string(c.title||c.id||'Your commitment',200)});}
  const deadline=world?.story?.deadline;
  if(Number.isFinite(deadline)&&deadline>=from&&deadline<=to&&['unresolved','awaiting_stock','committed'].includes(world?.story?.stage))
    known.push({at:deadline,title:'The disputed delivery reaches its decision deadline.'});
  return {from,to,minutes,known};
}
