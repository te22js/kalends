"""Small first-session projection over real participant state, never a quest engine.

Only UI acknowledgements/history reading live in product metadata. Movement,
knowledge, payments, allocation and outcomes are derived afresh from accepted
commands and admitted events. No guide text is put into character memory.
"""
from __future__ import annotations
import copy
import json
from .history_cards import cards_for
from .participant_copy import quantity

VERSION = 'first-session-v1'
ACKS = frozenset({'role_arrival','request_read','promise_explained','skip_history','controls_known','reflection_done','dispute_explained'})
TEAMS = {'team_a':'Amir','team_b':'Mira','team_c':'Lin'}


def preferences(raw=None):
    raw = raw or {}
    if raw.get('version', VERSION) != VERSION:
        # Do not mistake old tutorial acknowledgements for this version's steps.
        return {'version':VERSION,'enabled':False,'learn':False,'practice':bool(raw.get('practice')), 'ack':[], 'read_cards':[]}
    return {'version':VERSION,'enabled':raw.get('enabled') is True,'learn':raw.get('learn') is True,
            'practice':raw.get('practice') is True, 'ack':[x for x in raw.get('ack',[]) if x in ACKS],
            'read_cards':[x for x in raw.get('read_cards',[]) if isinstance(x,str)][:5]}


def _payload_value(e):
    value = e['payload'].get('value')
    if isinstance(value,str):
        try: return json.loads(value)
        except (ValueError,TypeError): pass
    return value


def _step(ident,title,body,kind,label,**action):
    return {'id':ident,'title':title,'body':body,'hint':'You can ask for help, leave this guide or take another supported route.',
            'action':{'kind':kind,'label':label,**action},
            'time_policy':'Reading this guide does not advance world time. Moving and accepted work keep their displayed time costs. Automatic Live time is off during guidance.'}


def _evidence(events):
    rows=[]
    for e in events:
        p=e['payload']
        if p.get('category') == 'rb_evidence' and isinstance(p.get('document'),dict):
            d=p['document']
            rows.append({'event_id':e['event_id'],'title':d.get('title','A copied account'), 'text':d.get('text',''),
                         'source':next((a for a in e['actors'] if a!='Player'),'A recorded account'),
                         'at':d.get('as_of',e['tick']),'kind':'Copied fictional document; its contents are a claim'})
        elif p.get('category') == 'report' and p.get('listener') == 'Player':
            rows.append({'event_id':e['event_id'],'title':'Dated instrument report','text':f"The reported condition was {p.get('value')}.",
                         'source':TEAMS.get(p.get('speaker'),p.get('speaker','A speaker')), 'at':p.get('as_of',e['tick']), 'kind':'Testimony'})
        elif p.get('category') == 'conversation' and p.get('topic') == 'dispute' and p.get('spoken_text') and 'Lucius' in e.get('actors',[]):
            rows.append({'event_id':e['event_id'],'title':'The household steward’s account','text':p['spoken_text'],
                         'source':'Lucius','at':e['tick'],'kind':'Testimony; not a verified delivery record'})
    return rows[-8:]


def known_target(world, events, actor, fallback):
    """No use of unseen actor's current coordinates for a guide route."""
    near = next((a for a in world.get('agents',[]) if a['id']==actor and a.get('nearby')),None)
    if near:
        return {'type':'person','id':actor}, f'{actor} is nearby. Wait until you have reached them before speaking.'
    sightings = [e for e in events if e.get('etype')=='move' and actor in e.get('actors',[]) and 'position' in e['payload']]
    if sightings:
        seen=sightings[-1]; x,y=seen['payload']['position']
        return {'type':'location','id':seen['payload']['to'],'x':x,'y':y,'at':seen['tick'],'person':actor}, f"Go to where you last saw {actor}, at world minute {seen['tick']}. They may have moved; this is not live tracking."
    return {'type':'location','id':fallback,'person':actor}, f"Try the known {fallback.replace('_',' ')} meeting place. {actor}'s current whereabouts have not been established. Another supported route remains available."


def commons_result(events):
    settled=[e for e in events if e['payload'].get('category')=='allocation_settled']
    if not settled: return None
    last=settled[-1]; outcome=_payload_value(last)
    if not isinstance(outcome,dict): return None
    prop=last['payload'].get('prop',[])
    round_id=prop[1].split(':')[-1] if len(prop)>1 else '0'
    def register(prefix):
        candidates=[e for e in events if e['event_id']<=last['event_id'] and e['payload'].get('prop')==['experience',prefix+':'+round_id]]
        return _payload_value(candidates[-1]) if candidates else {}
    promises=register('promises') or {}; requests=register('requests') or {}
    allocation=outcome.get('allocation',{}); executed=outcome.get('executed',{})
    missed=[a for a,q in promises.items() if executed.get(a,0)<q]
    explanation=[f"The round ran with {outcome['actual_capacity']} usable capacity units. The exercise gives capacity to Amir first, then Mira, then Lin."]
    explanation += [f"{name} was allocated {quantity(allocation.get(a,0))} and received {quantity(executed.get(a,0))}." for a,name in TEAMS.items()]
    explanation += [f"You promised {quantity(promises[a])} to {TEAMS[a]}, so that promise was not met." for a in missed]
    return {'at':last['tick'],'event_id':last['event_id'],'requests':requests,'promises':promises,'allocation':allocation,
            'executed':executed,'actual_capacity':outcome['actual_capacity'],'missed_promises':missed,'explanation':explanation}


def _commons(snapshot, commands, events, prefs, settings):
    ack=set(prefs['ack']); evidence=_evidence(events); result=commons_result(events)
    requests=snapshot.get('requests',{}); allocation=snapshot.get('allocation'); promises=snapshot.get('promises',{})
    reports=snapshot.get('own_reports',[]); report=None
    if reports:
        e=reports[-1]; p=e['payload']; condition=p.get('value')
        capacity=settings.get('capacity',12)
        report={'condition':condition,'as_of':p.get('as_of',e['tick']),'observed_at':e['tick'],
                'source':TEAMS.get(p.get('speaker'),p.get('speaker','Your direct inspection')),
                'kind':'testimony' if e.get('etype')=='tell' else 'direct observation',
                'usable':capacity if condition=='stable' else max(1,capacity*2//3) if condition=='fragile' else None,
                'event_id':e['event_id']}
    projects=[]
    for e in events:
        if e['payload'].get('category')=='goal_register':
            raw=_payload_value(e)
            if isinstance(raw,dict):
                for ident,g in raw.items():
                    projects.append({'id':ident, 'label':g.get('label',ident), 'text':f"{TEAMS.get(g.get('actor'),g.get('actor','Team'))}: {g.get('quantity',g.get('target',{}).get('quantity','the stated'))} units in a settled batch; deadline minute {g.get('deadline','not stated')}."})
    done={'o0': 'role_arrival' in ack, 'o1':'request_read' in ack or bool(allocation) or bool(result),
          'o2':bool(report) or bool(result),'o3':allocation is not None or bool(result),
          'o4':bool(promises) or 'promise_explained' in ack or bool(result),'o5':bool(result),
          'o6':bool(result) and 'reflection_done' in ack,'o7':bool(result) and 'reflection_done' in ack}
    first_request=next(iter(requests.items()),None)
    request_text=f"{TEAMS.get(first_request[0],first_request[0])} currently requests {quantity(first_request[1], 'capacity unit')}." if first_request else 'No team has an active request in the current register yet.'
    steps=[
        _step('o0','You coordinate one shared instrument.',"Amir, Mira and Lin represent three teams. Read what they request, obtain a dated report, divide the available capacity, then check what each team actually receives. A capacity unit is a simplified share of use, not a measured hour of telescope time.",'ack','Begin the guided round',ack='role_arrival'),
        _step('o1','Read a real request.',request_text+' A request says what a team wants. It creates neither a promise nor an allocation. Blank quantities mean no record; an explicit zero is a recorded zero.','ack','I understand this request',ack='request_read'),
        _step('o2','Ask Mira for her dated report.','The rated capacity is twelve units. The current condition is not yet known from your received reports. Ask Mira to share what she observed; confirmation records the actual disclosure. A direct inspection is another supported route and costs one credit.','report','Ask Mira for the report'),
        _step('o3','Choose an allocation you can explain.',('The latest admitted report describes '+str(report['usable'])+' usable units, dated minute '+str(report['as_of'])+'. It may be out of date. ' if report else '')+'Set a quantity for each team and review the total. Delivery follows the public exercise order: Amir, then Mira, then Lin. A project needs its stated minimum in a settled batch; equal shares are not always useful.','allocation','Review your allocation'),
        _step('o4','A promise is optional and separate.','A promise tells a team what you commit to provide. An allocation instructs the division of capacity; settlement determines delivery. You may review a promise to one team, or continue without making one. Changing an allocation field never creates a promise.','promise','Review an optional promise',ack='promise_explained'),
        _step('o5','Finish this round deliberately.','Your allocation is recorded, but delivery has not happened. Review the target time and every known commitment, then explicitly finish the round. Reading this panel does not move the clock.','finish_round','Review and finish this round'),
        _step('o6','Read what actually happened.',' '.join(result['explanation']) if result else 'No settlement has been recorded yet.','results','Review the actual result',ack='reflection_done'),
        _step('o7','Continue with less guidance.','Can you explain the difference between a request, a promise, an allocation and actual delivery? If that is still unclear, reopen this help or review your saved choice. This is an optional reflection, not a measured test result.','complete','Continue exploring'),
    ]
    # A closed or early-completed round is reviewed instead of impossible work.
    if result and not done['o6']:
        current=steps[6]
    else:
        current=next((s for s in steps if not done[s['id']]),steps[-1])
    known={'summary':[request_text, 'Requests, promises, allocated amounts and delivered amounts are different records.'],
           'evidence':evidence,'request':{'text':request_text,'quantities':requests},'report':report,'project_requirements':projects}
    return steps,done,current,known,result,{'text':'The three representatives are listed beside the instrument. Select Mira to ask for her report.','target':None},[]


def _pompeii(snapshot, commands, events, prefs):
    world=snapshot.get('world',{}); ack=set(prefs['ack']); evidence=_evidence(events)
    actions=[c['data'].get('action') for c in commands if c.get('operation')=='action']
    categories={e['payload'].get('category') for e in events}
    moved=any(c.get('operation')=='move' or c.get('operation')=='action' and c.get('data',{}).get('action')=='move' for c in commands)
    heard='hear_dispute' in actions or 'rb_dispute_heard' in categories
    documents={e['payload'].get('document_key') for e in events if e['payload'].get('category')=='rb_evidence'}
    second_account = any(e['payload'].get('category')=='conversation' and e['payload'].get('topic')=='dispute'
                         and e['payload'].get('spoken_text') and 'Lucius' in e.get('actors',[]) for e in events)
    chosen=any(a in actions for a in ('mediate','support_market','guarantee_household','decline_dispute'))
    resolutions=[e for e in events if e['payload'].get('category')=='rb_resolution']
    notices=[e for e in events if e['payload'].get('category')=='rb_public_notice']
    resolved=bool(resolutions or notices)
    cards=cards_for(snapshot,commands,prefs['read_cards'])
    historical='food_counter' in prefs['read_cards'] or 'skip_history' in ack or not prefs['learn']
    actual_result=None
    if resolutions:
        e=resolutions[-1]; p=e['payload']; delivery=p.get('allocation',{})
        payment=sum(-e['payload'].get('cash_delta',{}).get('Player',0) for e in events if e['payload'].get('category')=='rb_agreement')
        explanation=[f"The recorded delivery sent {quantity(q, 'flour unit')} to {who}." for who,q in delivery.items()]
        if payment>0: explanation.insert(0,f'You paid {payment:g} coins for the arrangement.')
        elif payment<0: explanation.insert(0,f'You received {-payment:g} coins for arranging the delivery.')
        for change in p.get('relationship_axes',[]):
            delta=change.get('delta',{}).get('affinity',0)
            if delta:
                explanation.append(f"{change['agent']}’s recorded regard for you {'improved' if delta>0 else 'fell'} after this arrangement.")
        if not explanation: explanation=[p.get('title','The buyers completed their own arrangement.')]
        actual_result={'at':e['tick'],'event_id':e['event_id'],'delivered':delivery,'explanation':explanation,'relationship_note':'Read the affected person’s response or your story for the recorded relationship changes. Other people can react differently to the same agreement.'}
    elif notices:
        e=notices[-1]; actual_result={'at':e['tick'],'event_id':e['event_id'],'delivered':{},'explanation':[e['payload']['title']], 'relationship_note':'Only the admitted notice is shown; unseen quantities are not inferred.'}
    done={'p0':'role_arrival' in ack,'p1':moved or heard or chosen or 'controls_known' in ack,
          'p2':heard or bool(documents) or chosen or resolved,'p3':'dispute_explained' in ack or bool(documents) or chosen or resolved,
          'p4':historical,'p5':{'market_receipt','household_tablet'} <= documents or 'loading_record' in documents or second_account or chosen or resolved,
          'p6':chosen or resolved,'p7':resolved,'p8':resolved and 'reflection_done' in ack}
    sabina,hint=known_target(world,events,'Sabina','thermopolium')
    dama,dhint=known_target(world,events,'Dama','household')
    if dama.get('id')=='household' and not any(e.get('etype')=='move' and 'Dama' in e.get('actors',[]) for e in events):
        # The opening's cart meeting point is a fixed public scenario landmark,
        # not a query for the messenger's later private endpoint.
        dama={'type':'location','id':'street','x':850,'y':430,'person':'Dama','basis':'public opening cart meeting point'}
        dhint='Try the cart meeting point on the public street. This does not track Dama. If she has left, try the known household doorway, or review another supported arrangement.'
    summary=[]
    if heard: summary.append('Sabina has asked you to investigate the disputed flour cart. Hearing her account does not verify every claim.')
    if documents: summary.append('You obtained '+', '.join({'market_receipt':"Sabina’s account",'household_tablet':"the household instructions",'loading_record':"the checked loading account"}.get(d,d) for d in sorted(documents))+'.')
    if not documents: summary.append('You have not copied a written order yet. No hidden account is supplied by the guide.')
    steps=[
        _step('p0','You are Aelia.','You play a fictional freedwoman in Pompeii: a woman who was enslaved and is now free. A flour delivery is disputed. Hear the accounts before deciding whether to help. Aelia’s biography and opportunities are invented; they do not represent every freedwoman.','ack','Begin',ack='role_arrival'),
        _step('p1','Find Sabina.','Click the ground to walk, or use the movement controls shown in the scene. Moving advances world time by its actual travel cost. You may take another route or explicitly skip the controls lesson.','scene','Show me the way',target=sabina),
        _step('p2','Talk to Sabina, the food seller.','When Aelia has reached her, select Sabina or use the displayed interaction key. Ask what happened to her order. Read and confirm the offered disclosure; simply opening a conversation does not complete it.','scene','Find Sabina and speak',target=sabina),
        _step('p3','Understand the two claims.','Sabina has given her side. The household also has a claim. You can copy the accounts, ask the household messenger or investigate the cart before deciding how much uncertainty to accept.','ack','Look at the evidence',ack='dispute_explained'),
        _step('p4','Learn one historical idea in place.','Visit the food counter and open “What is this place?” The counter and inset jars represent archaeological features; Sabina and her prices are invented. Reading is optional and does not move the clock.','history','What is this place?',card='food_counter',target={'type':'location','id':'thermopolium'}),
        _step('p5','Compare the accounts you actually obtained.','A copied claim is evidence of what its holder recorded, not automatic proof of the whole dispute. Dama can share the household instructions. If she has moved, ask Lucius about the dispute at the household and confirm that conversation. Marcus can check his loading account for one coin and fifteen minutes. You may instead choose any eligible arrangement; the guide never requires a payment you cannot afford.','scene','Seek another account',target=dama),
        _step('p6','Choose whether and how to help.','Return to a claimant and review an eligible arrangement. The market route costs three coins. A household advance creates a later service obligation. The evidence route requires the actual copied accounts. You may also tell Sabina you will leave the decision to the buyers. Confirm only terms you intend to accept.','scene','Review your available choices',target=sabina),
        _step('p7','See the actual delivery.','Your accepted choice is recorded. Some arrangements execute their delivery during their displayed twenty-minute action; declining leaves the buyers’ own deadline in place. Use the deliberate time controls if nothing has settled. The guide never silently pays, promises or advances time.','time','Review time and known obligations'),
        _step('p8','Your decision, and the history behind it.',' '.join(actual_result['explanation'])+' The dispute, prices and rewards were invented for this simulation. Compare them with a sourced card, then continue exploring, visit the fullery or review your saved story.' if actual_result else 'Keep exploring; the first outcome has not yet reached you.','reflect','Review what happened',ack='reflection_done'),
    ]
    # If the opportunity has passed, never keep asking for an impossible order.
    if resolved:
        current=steps[8] if not done['p8'] else _step('p9','Choose what comes next.','You can work, speak with residents, learn at the fullery or follow an unresolved obligation. Help and your notebook remain available.','complete','Continue exploring')
    elif chosen:
        current=steps[7]
    elif not done['p0']:
        current=steps[0]
    else:
        current=next((s for s in steps if not done[s['id']]),steps[-1])
    target=current['action'].get('target')
    hinttext=dhint if target==dama else hint if target==sabina else 'Use a known public route. A place on the map is not proof that a person is still there.'
    return steps,done,current,{'summary':summary,'evidence':evidence,'project_requirements':[]},actual_result,{'text':hinttext,'target':target},cards


def guide_view(snapshot, commands, events, settings, meta=None):
    prefs=preferences(meta)
    if snapshot['setting']=='pompeii':
        steps,done,current,known,result,hint,cards=_pompeii(snapshot,commands,events,prefs)
    else:
        steps,done,current,known,result,hint,cards=_commons(snapshot,commands,events,prefs,settings)
    return {**prefs,'step':current,'completed':[s['id'] for s in steps if done.get(s['id'])],
            'chapters':[{'id':s['id'],'title':s['title'],'status':'complete' if done.get(s['id']) else 'current' if s['id']==current['id'] else 'upcoming'} for s in steps],
            'known':known,'result':result,'hint':hint,'history_cards':cards,
            'excluded_from_unassisted_research':prefs['enabled'] or prefs['practice'] or bool((meta or {}).get('guided_origin')),
            'not_a_comprehension_score':True}
