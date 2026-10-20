"""Reproducible offline language and gameplay evidence, without a human-study claim."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time
from .server import PompeiiSession

CASES=[
 ('Buy four flour units','buy'),('I promise four flour units','accept_delivery'),
 ('I brought the flour','deliver'),('I need a paid shift','work'),
 ('I would like an advance','patronage'),('Inspect the flour dispatch','inspect'),
 ('Sell my report','sell_information'),('Complete service','service'),
 ('Flour supply is disrupted','claim'),('Flour supply is available','claim'),
 ('What have you heard about flour supply?','talk'),('What do you remember about me?','talk'),
 ('Who are you?','talk'),('What is your work?','talk'),
 ('I will not buy four flour','talk'),('I do not promise four flour','talk'),
 ('Can I deliver later?','talk'),('Never accept an advance','talk'),
 ('Cancel the purchase','talk'),('Tell me about a dragon','talk')]


def run(out):
    out=Path(out)
    if out.exists(): raise ValueError('Choose a fresh evidence directory')
    out.mkdir(parents=True)
    s=PompeiiSession();s.apply('move',{'location':'bakery'})
    rows=[]
    for text,expected in CASES:
        start=time.perf_counter();proposal=s.propose({'text':text,'recipient':'Felix'});elapsed=time.perf_counter()-start
        action=proposal['interpretations'][0]['action']
        # Replies are exact literal retained statements or explicitly authored role text.
        ids=set(proposal['reply']['evidence_ids'])
        allowed={e.event_id for e in s.original.remembered('Felix')}
        rows.append({'text':text,'expected_intent':expected,'proposed_intent':action['action'],
            'matched':action['action']==expected,'latency_seconds':elapsed,'evidence_ids':sorted(ids),
            'evidence_in_character_memory':ids<=allowed,'language_source':proposal['language_source']})
    (out/'offline_language.json').write_text(json.dumps(rows,indent=2)+'\n')
    routes={}
    for route in ('wage','household','information'):
        game=PompeiiSession();game.apply('move',{'location':'bakery'})
        game.apply('interact',{'action':'accept_delivery','recipient':'Felix'})
        if route=='wage':
            game.apply('move',{'location':'thermopolium'});game.apply('interact',{'action':'work','recipient':'Sabina'})
        elif route=='household':
            game.apply('move',{'location':'household'});game.apply('interact',{'action':'patronage','recipient':'Lucius'})
        else:
            game.apply('move',{'x':930,'y':415})
            p=game.propose({'text':'What have you heard about flour supply?','recipient':'Marcus'})
            game.act({'proposal_id':p['proposal_id'],'interpretation_id':'0'})
            game.apply('move',{'location':'bakery'});game.apply('interact',{'action':'sell_information','recipient':'Felix'})
        game.apply('move',{'location':'bakery'});game.apply('interact',{'action':'buy','recipient':'Felix','quantity':4})
        result=game.apply('interact',{'action':'deliver','recipient':'Felix'})
        settled=game.original.metrics()
        result_id=result['receipt']['event_id']
        game.apply('advance',{'minutes':7*1440,'mode':'skip'})
        game.apply('move',{'location':'bakery'})
        reply=game.propose({'text':'What do you remember about me?','recipient':'Felix'})['reply']
        game.apply('mode',{'mode':'lab'})
        original_hash=game.original.ledger.content_hash()
        game.apply('fork',{'kind':'remove_action','event_id':result_id})
        assert original_hash==game.original.ledger.content_hash()
        routes[route]={'at_settlement':settled,'after_absence':game.original.metrics(),
            'return_reply':reply,'counterfactual':game.state()['comparison'],'intervention':game.intervention,
            'commands':game.commands,'events':game.original.ledger.to_json()}
        (out/f'{route}_history.json').write_text(json.dumps(routes[route],indent=2)+'\n')
    summary={'kind':'automated developer fixtures, not human evaluation','language_cases':len(rows),
        'intent_matches':sum(r['matched'] for r in rows),'evidence_scope_passes':sum(r['evidence_in_character_memory'] for r in rows),
        'median_proposal_seconds':statistics.median(r['latency_seconds'] for r in rows),
        'max_proposal_seconds':max(r['latency_seconds'] for r in rows),'provider_calls':0,'inference_cost_usd':0,
        'language_limit':'Rule parser and literal grounded replies; evidence membership does not establish rich dialogue quality or general factual accuracy.',
        'routes':{k:{'settlement':v['at_settlement'],'after_absence':v['after_absence'],'return_reply':v['return_reply'],
                     'alternate_changed_fields':v['counterfactual']['changed_fields']} for k,v in routes.items()}}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    files={str(p.name):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.json')}
    (out/'manifest.json').write_text(json.dumps({'files_sha256':files,'config':{'seed':79,'population':6},'method':'fresh independent route worlds; scripted interactions; all fictional'},indent=2)+'\n')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True)
    args=parser.parse_args();print(json.dumps(run(args.out),indent=2))
if __name__=='__main__':main()
