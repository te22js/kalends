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


def game_world_copy(world):
    result=copy.deepcopy(world)
    for field in ('journal',):
        if isinstance(result.get(field),list):
            result[field]=[event_copy(e) if isinstance(e,dict) and isinstance(e.get('payload'),dict) else e for e in result[field]]
    montage=result.get('montage')
    if isinstance(montage,dict) and isinstance(montage.get('events'),list):
        montage['events']=[event_copy(e) if isinstance(e,dict) and isinstance(e.get('payload'),dict) else e for e in montage['events']]
    return result
