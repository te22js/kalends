/* The renderer translates public state; only the Python session changes a life. */
export const WORLD_SCALE = 0.02;
export const WORLD_ORIGIN = Object.freeze({x:800, y:415});
export const PUBLIC_LOCATIONS = Object.freeze(['street','water','forum_access']);

const finite = (v, name) => {
  if (typeof v !== 'number' || !Number.isFinite(v)) throw new TypeError(`${name} must be finite.`);
  return v;
};
const copy = value => value === undefined ? undefined : JSON.parse(JSON.stringify(value));
const pick = (value, keys) => Object.fromEntries(keys.filter(key => value?.[key] !== undefined).map(key => [key, copy(value[key])]));

export function toScene(point, height=0) {
  return {x:(finite(point.x,'x')-WORLD_ORIGIN.x)*WORLD_SCALE, y:finite(height,'height'), z:(finite(point.y,'y')-WORLD_ORIGIN.y)*WORLD_SCALE};
}
export function toWorld(point) {
  return {x:finite(point.x,'x')/WORLD_SCALE+WORLD_ORIGIN.x, y:finite(point.z,'z')/WORLD_SCALE+WORLD_ORIGIN.y};
}
export function sameFloor(a,b) {return a===b || PUBLIC_LOCATIONS.includes(a)&&PUBLIC_LOCATIONS.includes(b);}
export function worldDistance(a,b) {return Math.hypot(a.x-b.x,a.y-b.y);}

const ENTITY_KEYS = ['id','name','role','x','y','location','path','nearby','activity','portrait','movement_event','movement_minute'];
const PLAYER_KEYS = [...ENTITY_KEYS,'cash','inventory','reputation','commitments','commissions','documents','progression','affiliation','social_position'];
const LOCATION_KEYS = ['id','name','x','y','w','h','door','kind','interior','source_id','history_label'];
const JOURNAL_KEYS = ['event_id','minute','tick','category','title','text','location','participants','parents','evidence','as_of'];
const STORY_KEYS = ['chapter','title','hook','stage','route','objective','leads','deadline','followup_ready','followup_done','service_due','service_done','service_missed'];

/** Reject operator snapshots, then explicitly select the normal game surface.
 * Do not pass the raw payload through to NPC entity components or DOM state.
 */
export function projectSnapshot(payload) {
  if (!payload || payload.mode !== 'game' || !payload.world?.player) throw new Error('A public game snapshot is required.');
  const w=payload.world;
  const entity = value => {
    const result=pick(value,ENTITY_KEYS);
    finite(result.x,'entity x');finite(result.y,'entity y');
    return result;
  };
  const player={...entity(w.player),...pick(w.player,PLAYER_KEYS)};
  const world={
    ...pick(w,['minute','day','clock','historical_note','elapsed_policy','objective','opportunities','montage','time_stats']),
    player,
    agents:(w.agents||[]).map(entity),
    nearby:copy(w.nearby||[]),
    map:{...pick(w.map,['width','height','bounds','streets','disclaimer']), locations:(w.map?.locations||[]).map(location=>pick(location,LOCATION_KEYS))},
    story:pick(w.story,STORY_KEYS),
    journal:(w.journal||[]).map(event=>pick(event,JOURNAL_KEYS)),
    // This is the server's player-facing market summary, not its operator mind.
    counter_market:pick(w.counter_market,['active','version','title','contracts','nearby_offers','completed_batches']),
  };
  return {world,mode:'game',...pick(payload,['capabilities','save_version','telemetry_enabled']),language:pick(payload.language,['mode','external_calls'])};
}

export function projectContext(context) {
  if (!context || typeof context.speaker !== 'string') throw new Error('A valid conversation is required.');
  return pick(context,['speaker','greeting','topics','choices','relationship','dialogue_version','counter_order']);
}

export class BusyError extends Error {constructor(){super('The previous action is still being saved.');this.name='BusyError';}}
export class StaleResponseError extends Error {constructor(){super('The situation changed. Open the conversation and review again.');this.name='StaleResponseError';}}

export class KalendsBridge {
  constructor({fetchImpl=globalThis.fetch?.bind(globalThis),base='',onState=()=>{},onStatus=()=>{},onTiming=()=>{}}={}) {
    if (typeof fetchImpl !== 'function') throw new TypeError('A fetch implementation is required.');
    this.fetchImpl=fetchImpl;this.base=base.replace(/\/$/,'');this.onState=onState;this.onStatus=onStatus;this.onTiming=onTiming;
    this.snapshot=null;this._pending=null;this._stateEpoch=0;this._conversationEpoch=0;this._proposal=null;this._confirmation=null;
  }
  get pending(){return Boolean(this._pending);}
  get proposal(){return copy(this._proposal);}
  get world(){return this.snapshot?.world||null;}
  cancelConversation(){this._conversationEpoch++;this._proposal=null;}
  async request(path,body) {
    const begin=globalThis.performance?.now?.()??Date.now();let ok=false;
    try {
      const response=await this.fetchImpl(this.base+path,body===undefined?{cache:'no-store',credentials:'same-origin'}:{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      let value;
      try {value=await response.json();} catch {throw new Error('The local game returned an unreadable response.');}
      if (!response.ok || value?.error) throw new Error(value?.error||`Local game request failed (${response.status}).`);
      ok=true;return value;
    } finally {
      this.onTiming({path,duration_ms:(globalThis.performance?.now?.()??Date.now())-begin,ok});
    }
  }
  async _accept(payload) {
    // World Lab uses the same server session in the separately runnable legacy
    // client. Never project its operator response, even after a valid action.
    if(payload?.mode==='lab')payload=await this.request('/api/mode',{mode:'game'});
    const projected=projectSnapshot(payload);this.snapshot=projected;this.onState(projected);return projected;
  }
  _exclusive(label,operation,{invalidateConversation=true}={}) {
    if(this.pending)return Promise.reject(new BusyError());
    if(invalidateConversation)this.cancelConversation();
    this._stateEpoch++;
    const marker={label};this._pending=marker;this.onStatus({pending:true,label});
    const promise=Promise.resolve().then(operation).finally(()=>{if(this._pending===marker){this._pending=null;this.onStatus({pending:false,label});}});
    return promise;
  }
  async state() {
    if(this.pending)throw new BusyError();
    const epoch=++this._stateEpoch;
    let value=await this.request('/api/state');
    if(epoch!==this._stateEpoch)throw new StaleResponseError();
    if(value.mode==='lab') {
      return this._exclusive('Return to game',async()=>this._accept(await this.request('/api/mode',{mode:'game'})));
    }
    return this._accept(value);
  }
  async context(recipient) {
    if(this.pending)throw new BusyError();
    const epoch=++this._conversationEpoch;this._proposal=null;
    const value=await this.request('/api/context?recipient='+encodeURIComponent(recipient));
    if(epoch!==this._conversationEpoch)throw new StaleResponseError();
    return projectContext(value);
  }
  async propose(recipient,{choice_id,text}={}) {
    if(this.pending)throw new BusyError();
    if((choice_id===undefined)===(text===undefined))throw new Error('Choose one response or enter one message.');
    const epoch=this._conversationEpoch;
    return this._exclusive('Review choice',async()=>{
      const value=await this.request('/api/propose',{recipient,...(choice_id!==undefined?{choice_id}:{text})});
      if(epoch!==this._conversationEpoch)throw new StaleResponseError();
      const proposal=pick(value,['proposal_id','reply','interpretations','language_source','clarification']);
      if(typeof proposal.proposal_id!=='string'||!Array.isArray(proposal.interpretations))throw new Error('The local game returned an invalid proposal.');
      this._proposal=proposal;return copy(proposal);
    },{invalidateConversation:false});
  }
  confirm(proposalId,interpretationId='0') {
    const key=proposalId+':'+interpretationId;
    if(this._confirmation?.key===key)return this._confirmation.promise;
    if(this.pending)return Promise.reject(new BusyError());
    if(this._proposal?.proposal_id!==proposalId)return Promise.reject(new StaleResponseError());
    if(!this._proposal.interpretations.some(option=>option.id===interpretationId))return Promise.reject(new Error('Review the response you want to confirm.'));
    this._proposal=null;
    const promise=this._exclusive('Saving choice',async()=>{
      const payload=await this.request('/api/act',{proposal_id:proposalId,interpretation_id:interpretationId});
      const result=await this._accept(payload);
      return {...result,receipt:pick(payload.receipt,['event_id','minute','category','text','title','accepted']),reply:copy(payload.reply),conversation:payload.conversation?projectContext(payload.conversation):null};
    });
    const record={key,promise};this._confirmation=record;
    promise.finally(()=>{if(this._confirmation===record)this._confirmation=null;}).catch(()=>{});
    return promise;
  }
  async route(body) {
    const value=await this.request('/api/route',pick(body,['x','y','location']));
    if(!Array.isArray(value.points)||!value.points.length)throw new Error('No walking route was returned.');
    for(const point of value.points){finite(point.x,'route x');finite(point.y,'route y');if(typeof point.location!=='string')throw new Error('A route scene is missing.');}
    return pick(value,['revision','navigation_revision','points','distance','destination']);
  }
  move(body) {return this._exclusive('Walking',async()=>this._accept(await this.request('/api/move',pick(body,['x','y','location']))));}
  advance(minutes,mode='compress') {
    if(!Number.isInteger(minutes)||minutes<1)return Promise.reject(new Error('Choose a positive whole number of world minutes.'));
    return this._exclusive('Time passes',async()=>this._accept(await this.request('/api/advance',{minutes,mode})));
  }
}
