"""Validated participant presentation helpers; no ledger or simulation mutation."""
import math
import re
import copy


def quantity(value, unit='unit'):
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValueError('A displayed quantity must be a finite number')
    number = format(value, 'g')
    return f"{number} {unit if value == 1 else unit+'s'}"


def sentence(text):
    if not isinstance(text,str):
        raise ValueError('Participant copy must be text')
    text=text.strip()
    for unit in ('unit', 'coin', 'minute', 'project'):
        text = re.sub(r'(?<![\d.])1 '+unit+r's\b', '1 '+unit, text)
    text = re.sub(r'(?<![\d.])1 allocated units\b', '1 allocated unit', text)
    return text if not text or text.endswith(('.', '!', '?', '…', '.”', '!”', '?”')) else text+'.'


def event_text(event):
    payload=event['payload']
    if payload.get('category') == 'rb_resolution' and isinstance(payload.get('allocation'), dict):
        deliveries = [f"{who} received {quantity(amount, 'flour unit')}" for who,amount in payload['allocation'].items()]
        return sentence('; '.join(deliveries) or 'The buyers settled the cart arrangement')
    document=payload.get('document')
    if payload.get('category')=='rb_evidence' and isinstance(document,dict) and document.get('title'):
        return sentence('You read the document “'+document['title']+'”')
    return sentence(payload.get('title', 'A moment was recorded'))


def event_copy(event):
    result=copy.deepcopy(event)
    result['voice'] = 'transaction'
    result['kind'] = 'receipt'
    result['payload'].pop('relationship_axes', None)
    result['title']=event_text(result)
    result['payload']['title']=result['title']
    return result


# The existing cart actions and costs are unchanged. These are presentation
# descriptions of their reviewed terms, not a claim that delivery has occurred.
_CART_CHOICES = {
    'support_market': {
        'label': 'Pay for the market delivery',
        'description': 'Pay the carrying charge to direct four sacks of flour to Sabina and two to Felix.',
        'cost': '3 coins · 20 world minutes',
        'consequence': 'The action advances twenty minutes and attempts the delivery during that time. Review the actual receipt afterwards. The household advance is refunded; market work opens and Lucius loses priority.',
    },
    'mediate': {
        'label': 'Negotiate a delivery using the three accounts',
        'description': 'Use the copied market, household and loading accounts to arrange four sacks for the household and two for Sabina.',
        'cost': 'Three copied accounts · 20 world minutes',
        'consequence': 'Marcus covers the carrying charge. The action advances twenty minutes and attempts delivery. Review the actual receipt afterwards. Broker work opens.',
    },
    'guarantee_household': {
        'label': 'Accept the household advance and service obligation',
        'description': 'Receive six coins and give the household priority over the flour cart. You commit to two hours of service within three days.',
        'cost': '20 world minutes now · 120 minutes of service due within three days',
        'consequence': 'Delivery is attempted during this action. Review the actual receipt afterwards. The service remains a separate obligation. Household work opens; Sabina loses delivery priority.',
    },
    'decline_dispute': {
        'label': 'Leave the decision to the buyers',
        'description': 'Decline to arrange this delivery. The buyers can act at their own deadline.',
        'consequence': 'No payment or service promise is made by this choice. The dispute remains active until the buyers act; inspect the eventual recorded outcome.',
    },
}


def choice_copy(choice):
    result = copy.deepcopy(choice)
    if result.get('description') == 'Recall selected retained shared experiences.':
        result['description'] = 'Ask about dealings this person remembers.'
    action = result.get('action', {}).get('action')
    prose = _CART_CHOICES.get(action)
    if prose:
        result.update(prose)
        if 'transmission' in choice:
            result['transmission'] = prose['description']
    return result


def game_world_copy(world):
    result=copy.deepcopy(world)
    for agent in result.get('agents', []):
        agent.pop('relationship', None)
    for field in ('journal',):
        if isinstance(result.get(field),list):
            result[field]=[event_copy(e) if isinstance(e,dict) and isinstance(e.get('payload'),dict) else e for e in result[field]]
    montage=result.get('montage')
    if isinstance(montage,dict) and isinstance(montage.get('events'),list):
        montage['events']=[event_copy(e) if isinstance(e,dict) and isinstance(e.get('payload'),dict) else e for e in montage['events']]
    return result


def participant_context(runtime, recipient, view):
    """Speak from retained permitted evidence, never the global route flag.

    Authored role lines are labelled separately from recalled episodes. A known
    institutional duty is a system reminder and cannot establish human recall.
    """
    from kalends_rebirth.world import PERSONALITY
    result = copy.deepcopy(view)
    allowed = runtime.visible_ids()
    events = {e['event_id']: e for e in runtime.events()}
    retained = {e.event_id for e in runtime.world.remembered(recipient) if e.accepted}
    support = retained & allowed
    agreements = [e for i,e in events.items() if i in support and e['payload'].get('category') == 'rb_agreement'
                  and recipient in e.get('actors', ())]
    deliveries = [e for i,e in events.items() if i in support and e['payload'].get('category') == 'rb_resolution'
                  and recipient in e.get('actors', ())]
    greeting = {'text': PERSONALITY[recipient]['opening'], 'evidence_ids': [], 'voice': 'person', 'kind': 'authored_role'}
    # Causal thanks needs both retained observations and their accepted parent.
    for delivery in reversed(deliveries):
        match = next((a for a in agreements if a['event_id'] in delivery['payload'].get('parents', ())), None)
        amount = delivery['payload'].get('allocation', {}).get(recipient, 0)
        if match and amount > 0:
            greeting = {'text': f"You helped arrange that cart. I received {quantity(amount, 'flour unit')}. Thank you.",
                        'evidence_ids': [match['event_id'], delivery['event_id']], 'voice': 'person', 'kind': 'recalled_response'}
            break
    if deliveries and greeting['kind'] != 'recalled_response':
        amount = deliveries[-1]['payload'].get('allocation', {}).get(recipient, 0)
        greeting = {'text': f"I received {quantity(amount, 'flour unit')} from that cart.",
                    'evidence_ids': [deliveries[-1]['event_id']], 'voice': 'person', 'kind': 'recalled_observation'}
    result['greeting'] = greeting
    result.pop('relationship', None)
    for topic in result.get('topics', []):
        topic['voice'] = 'person'
        topic['kind'] = 'speech'
        if topic.get('withheld'):
            topic.update(text=('Checking my loading account costs one coin and takes fifteen minutes.' if topic['id']=='loading_record'
                               else 'Ask me for this account if you would like to read it.'), kind='offer')
        elif topic['id'] in {'market_receipt','household_tablet','loading_record'}:
            topic.update(voice='notebook', kind='received_document')
        elif topic['id'] == 'memory':
            if greeting['kind'].startswith('recalled'):
                topic.update(text=greeting['text'], evidence_ids=greeting['evidence_ids'])
            else:
                # No stronger denial of earlier meetings or continuing duties.
                topic.update(text="I don’t remember us doing business before.", evidence_ids=[])
        elif topic['id'] == 'goals':
            # Role goals are authored offers; avoid laundering private planner
            # traces into the speaker's voice or inferring current inventory.
            topic.update(text=PERSONALITY[recipient]['role'], evidence_ids=[], kind='authored_role')
        elif topic['id'] == 'news':
            topic['text'] = topic['text'].replace('My retained dispatch says', 'The dispatch I remember says').replace('at world minute', 'at minute')
    result['revision'] = len(runtime.commands)
    result['state_hash'] = runtime.state_hash()
    result['obligations'] = []
    for obligation in runtime.world.economy.commitments.get('Player', ()):
        if obligation.get('status') == 'open' and obligation.get('beneficiary') == recipient:
            service = obligation.get('id') in {'rebirth-service', 'household-service'}
            unit = 'minutes' if service else 'units'
            result['obligations'].append({'voice':'transaction', 'kind':'obligation_reminder',
                'text':f"Your agreement with {recipient} remains open: {obligation.get('fulfilled',0)} of {obligation.get('quantity',0)} {unit} completed.",
                'deadline':obligation.get('deadline'), 'source':'Your agreement register; this does not establish the speaker’s recollection.'})
    result['voices_version'] = 1
    return result
