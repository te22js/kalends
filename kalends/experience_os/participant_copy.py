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
    document=payload.get('document')
    if payload.get('category')=='rb_evidence' and isinstance(document,dict) and document.get('title'):
        return sentence('You read the document “'+document['title']+'”')
    return sentence(payload.get('title', 'A moment was recorded'))


def event_copy(event):
    result=copy.deepcopy(event)
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
        'consequence': 'Marcus covers the carrying charge. The action advances twenty minutes and attempts delivery. Review the actual receipt afterwards. Broker work opens; Marcus resents the scrutiny.',
    },
    'guarantee_household': {
        'label': 'Accept the household advance and service obligation',
        'description': 'Receive six coins and give the household priority over the flour cart. You commit to two hours of service within three days.',
        'cost': '20 world minutes now · 120 minutes of service due within three days',
        'consequence': 'Delivery is attempted during this action. Review the actual receipt afterwards. The service remains a separate obligation. Household work opens; Sabina loses priority and welcomes you less.',
    },
    'decline_dispute': {
        'label': 'Leave the decision to the buyers',
        'description': 'Decline to arrange this delivery. The buyers can act at their own deadline.',
        'consequence': 'No payment or service promise is made by this choice. The dispute remains active until the buyers act; inspect the eventual recorded outcome.',
    },
}


def choice_copy(choice):
    result = copy.deepcopy(choice)
    action = result.get('action', {}).get('action')
    prose = _CART_CHOICES.get(action)
    if prose:
        result.update(prose)
        if 'transmission' in choice:
            result['transmission'] = prose['description']
    return result


def game_world_copy(world):
    result=copy.deepcopy(world)
    for field in ('journal',):
        if isinstance(result.get(field),list):
            result[field]=[event_copy(e) if isinstance(e,dict) and isinstance(e.get('payload'),dict) else e for e in result[field]]
    montage=result.get('montage')
    if isinstance(montage,dict) and isinstance(montage.get('events'),list):
        montage['events']=[event_copy(e) if isinstance(e,dict) and isinstance(e.get('payload'),dict) else e for e in montage['events']]
    return result
