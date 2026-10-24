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
      {type:target.type,id:string(target.id,80),person:string(target.person,80),
        ...(Number.isFinite(target.x)&&Number.isFinite(target.y)?{x:target.x,y:target.y}:{}),
        ...(Number.isFinite(target.at)?{at:target.at}:{})}:null}};
}

export function installSceneGuideHost({windowObject=globalThis.window,onGuide=()=>{}}={}){
  const host=windowObject;
  if(!host||host.parent===host)return {hosted:false,request(){return false;},destroy(){}};
  const origin=host.location.origin,lifeId=new URL(host.location.href).searchParams.get('experience')||'pompeii_life';
  const receive=event=>{const data=event.data;if(event.origin!==origin||event.source!==host.parent||!data||
    data.kind!=='kalends:guide'||data.life_id!==lifeId)return;onGuide(guideView(data.guide));};
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
  if(!world.map?.locations?.some(p=>p.id===target.id))return null;
  return {type:'location',id:target.id,...(Number.isFinite(target.x)&&Number.isFinite(target.y)?
    {x:target.x,y:target.y,person:target.person,at:target.at}:{})};
}

export function sceneActivity(actor,{moving=false,talking=false}={}){
  if(talking)return 'In conversation';
  if(moving)return 'Walking · recorded movement';
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
    'I paid Marcus for flour for my food counter. The household also has a claim on the cart. Hear our accounts before deciding whether to help.'],
  ['The order was ready at first light. That is what my message said. Ready is not the same as carried to your door.',
    'My message said the flour was ready at first light. That did not mean it had been delivered. Ask to check the loading account before drawing a conclusion.'],
  ['I was told to repeat the quantity, not argue about it. If you want the instructions, ask plainly.',
    'I carry the household’s delivery instructions. Ask me to repeat the quantity I was sent to carry. I cannot promise you the household’s money.'],
  ["Four sacks were reserved for this house. I will hear terms, not an accusation delivered on someone else's word.",
    'This household reserved four sacks of flour. I can discuss an arrangement. Hear the accounts and review the terms before you agree.'],
  ['A cart can stand still all morning while people make speeches. Someone must still bake.',
    'I bake and sell bread. I need flour and reliable help. You can ask about my work or review an available offer.'],
  ['If you want work, there is work here. The household pays for extra help. Do not mistake that for my freedom to leave.',
    'I work in this fullery under constraint. The household pays for extra help, but I am not free to leave. Ask about the work before accepting a paid shift.'],
]);
export function greetingCopy(value){const text=typeof value==='string'?value:value?.text||'';return OPENINGS.get(text)||text;}
export function topicCopy(topic){
  if(topic?.id==='memory'&&topic.text==='We have no consequential shared dealing in my retained memory yet.')return 'I do not remember discussing a past dealing with you.';
  if(topic?.id==='goals'&&typeof topic.text==='string'){
    const [aim,...rest]=topic.text.split('. For now, I must ');
    if(rest.length)return 'I need to '+aim.charAt(0).toLowerCase()+aim.slice(1)+'. For now, I must '+rest.join('. For now, I must ');
  }
  return string(topic?.text);
}
export const topicLabel=topic=>({role:'What is your work here?',goals:'What do you need now?',memory:'Do you remember our dealings?',news:'Do you have a dated report?'}[topic?.id]||string(topic?.label,160));
export function quantityCopy(value,singular,plural=singular+'s'){
  return Number.isFinite(value)?value+' '+(value===1?singular:plural):'Quantity not recorded';
}
export function contractCopy(contract){return (contract.delivered??0)+' of '+quantityCopy(contract.quantity??2,'flour unit')+' delivered.';}
export function confirmationLabel(action,speaker){
  return ({hear_dispute:'Hear '+speaker+'’s account',examine_receipt:'Copy this account',examine_tablet:'Copy these instructions',
    verify_cart:'Pay for this check',inspect:'Pay for this inspection',work:'Start this shift',decline_dispute:'Leave the decision to the buyers',
    reflect:'Ask about our dealings',support_market:'Confirm arrangement',guarantee_household:'Confirm arrangement',mediate:'Confirm arrangement',
    talk:'Ask '+speaker}[action]||'Confirm this action');
}

export function timeReview(world,minutes){
  const from=Number(world?.minute)||0,to=from+minutes,known=[];
  for(const c of world?.player?.commitments||[]){const due=Number(c.deadline??c.due);
    if(c.status==='open'&&Number.isFinite(due)&&due>=from&&due<=to)known.push({at:due,title:string(c.title||c.id||'Your recorded commitment',200)});}
  const deadline=world?.story?.deadline;
  if(Number.isFinite(deadline)&&deadline>=from&&deadline<=to&&['unresolved','awaiting_stock','committed'].includes(world?.story?.stage))
    known.push({at:deadline,title:'The disputed delivery reaches its decision deadline.'});
  return {from,to,minutes,known};
}
