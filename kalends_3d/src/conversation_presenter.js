/* Ordering and labels only. The server supplies permitted choices and evidence;
 * this module never interprets typed text or grants an action permission. */
export function conversationChoices(context, world, recipient) {
  const choices = context?.choices || [];
  const documents = new Set((world?.player?.documents || []).map(value => value.id));
  const rank = choice => {
    const action = choice.action?.action;
    if (choice.enabled === false) return 100;
    if (action === 'hear_dispute') return 0;
    if (action === 'examine_receipt' && !documents.has('market_receipt')) return 1;
    if (action === 'examine_tablet' && !documents.has('household_tablet')) return 1;
    if (action === 'verify_cart' && !documents.has('loading_record')) return 2;
    if (['support_market', 'guarantee_household', 'mediate'].includes(action)) return 3;
    if (action === 'work') return 4;
    if (action === 'decline_dispute') return 5;
    return 20;
  };
  const ordered = choices.map((choice, index) => ({choice, index})).sort((a, b) => rank(a.choice) - rank(b.choice) || a.index - b.index).map(value => value.choice);
  return {primary: ordered.slice(0, 3), more: ordered.slice(3)};
}
export function conversationChoiceLabel(choice, recipient) {
  const action = choice.action?.action;
  if (action === 'hear_dispute') return recipient === 'Sabina' ? 'What happened to your order?' : 'Tell me your account.';
  if (action === 'examine_receipt') return 'May I see your order?';
  if (action === 'examine_tablet') return 'May I see the household’s instructions?';
  if (action === 'verify_cart') return 'Check the loading account';
  return choice.label || 'Ask about this';
}
export function receivedDocuments(world, recipient) {
  const owner = {market_receipt: 'Sabina', household_tablet: 'Dama', loading_record: 'Marcus'};
  return (world?.player?.documents || []).filter(document => owner[document.id] === recipient);
}
export function pompeiiTime(minute) {
  if (!Number.isFinite(minute)) return 'an unknown time';
  const total = 480 + Math.floor(minute);
  return 'Day ' + (Math.floor(total / 1440) + 1) + ' · ' + String(Math.floor(total % 1440 / 60)).padStart(2, '0') + ':' + String(total % 60).padStart(2, '0');
}

export function continuingOptions(world) {
  if(world?.story?.stage!=='resolved')return [];
  const options=[];
  const open=(world.player?.commitments||[]).find(c=>c.status==='open');
  if(open)options.push({kind:'journal',label:'Review your open commitment',detail:open.title||'Check what you promised and when it is due.'});
  const offer=(world.opportunities||[]).find(q=>q.enabled===true&&q.action?.recipient);
  if(offer&&options.length<2)options.push({kind:'person',recipient:offer.action.recipient,label:'Speak to '+offer.action.recipient,detail:offer.title});
  for(const id of ['fullery','thermopolium']){
    if(options.length>=2)break;
    const place=world.map?.locations?.find(q=>q.id===id);
    if(place&&world.player?.location!==id)options.push({kind:'location',location:id,label:id==='fullery'?'Visit the fullery':'Visit the food counter',detail:'Walk to '+place.name+'. Walking takes time.'});
  }
  return options;
}
