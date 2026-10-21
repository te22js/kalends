"""Rebirth local game: reviewed actions, versioned saves, scoped conversation and lab."""
from __future__ import annotations
import argparse
import copy
from dataclasses import asdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, unquote, urlparse
import uuid

from kalends.pompeii.district import PompeiiConfig
from kalends.pompeii.server import PompeiiSession
from kalends.pompeii.world import PompeiiWorld
from .language import ACTIONS, Language, execute, grounded_reply, validate_action
from .world import RebirthWorld

ROOT=Path(__file__).resolve().parents[1]
STATIC=Path(__file__).with_name('static')
PRODUCT_EVENTS={'start','conversation_open','first_interaction','decision','consequence_seen','opening_skipped',
    'time_control','return','journal_open','voluntary_continue','session_end','location','evidence_open'}


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def restore_legacy(payload):
    if not isinstance(payload,dict) or payload.get('version')!=3:raise ValueError('A verified Pompeii version3 journal is required')
    world=PompeiiWorld(PompeiiConfig(**payload['config']))
    for command in payload['commands']:PompeiiSession._perform(world,command['operation'],command['data'])
    if world.ledger.content_hash()!=payload['ledger_hash']:raise ValueError('Legacy replay hash differs; the source save has been preserved')
    return world


class RebirthSession:
    version=4
    def __init__(self,journal_path=None,*,config=None,optimized=True,language=None,migrate_from=None):
        self.lock=threading.RLock();self.journal_path=Path(journal_path) if journal_path else None
        self.optimized=bool(optimized);self.language=language or Language();self.mode='game'
        self.origin=None;self.commands=[];self.proposals={};self.branch=None;self.intervention=None
        self.telemetry_enabled=False;self.product_events=[];self.session_id=uuid.uuid4().hex[:12]
        self.opened=time.monotonic();self._proposal_counter=0
        if isinstance(config,dict):config=PompeiiConfig(**config)
        self.original=RebirthWorld(config=config,optimized=self.optimized)
        self.config=asdict(self.original.config)
        if self.journal_path and self.journal_path.exists():
            if migrate_from:raise ValueError('Destination already exists; choose a new Rebirth journal')
            payload=json.loads(self.journal_path.read_text())
            if payload.get('version')!=self.version:raise ValueError('Preserve this older save; use --migrate-from with a different new journal path')
            self.config=payload['config'];self.origin=payload.get('origin')
            self.original=self._fresh()
            for command in payload['commands']:
                self._perform(self.original,command['operation'],command['data'],memory_presentation_revision=command.get('memory_presentation_revision',1),
                    movement_revision=command.get('movement_revision',1),minds_revision=command.get('minds_revision',0))
            if self.original.ledger.content_hash()!=payload['ledger_hash']:raise ValueError('Rebirth replay differs from this runtime; save preserved without modification')
            self.commands=payload['commands'];self.mode=payload.get('mode','game')
            self.telemetry_enabled=payload.get('telemetry_enabled',False)
            self.product_events=payload.get('product_events',[])[-1000:]
            if payload.get('intervention'):self._fork(payload['intervention']['event_id'])
        elif migrate_from:
            source=Path(migrate_from)
            if self.journal_path and source.resolve()==self.journal_path.resolve():raise ValueError('Migration requires a different destination; legacy saves are never overwritten')
            self.origin=json.loads(source.read_text());legacy=restore_legacy(self.origin)
            self.original=RebirthWorld.from_legacy(legacy,optimized=self.optimized)
            self.config=asdict(self.original.config)
            self.save()

    def _fresh(self):
        if self.origin:return RebirthWorld.from_legacy(restore_legacy(self.origin),optimized=self.optimized)
        return RebirthWorld(PompeiiConfig(**self.config),optimized=self.optimized)

    def save(self):
        if not self.journal_path:return
        self.journal_path.parent.mkdir(parents=True,exist_ok=True)
        payload={'version':self.version,'config':self.config,'origin':self.origin,'commands':self.commands,
            'mode':self.mode,'ledger_hash':self.original.ledger.content_hash(),'intervention':self.intervention,
            'telemetry_enabled':self.telemetry_enabled,'product_events':self.product_events[-1000:]}
        temporary=self.journal_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n');temporary.replace(self.journal_path)

    @staticmethod
    def _validate_movement_revision(revision):
        if type(revision) is not int or revision not in (1,2):
            raise ValueError('Unsupported movement revision; save preserved without modification')

    @staticmethod
    def _validate_minds_revision(revision):
        if type(revision) is not int or revision not in (0,2):
            raise ValueError('Unsupported minds revision; save preserved without modification')

    @staticmethod
    def _perform(world,operation,data,*,memory_presentation_revision=2,movement_revision=2,minds_revision=0):
        RebirthSession._validate_movement_revision(movement_revision)
        RebirthSession._validate_minds_revision(minds_revision)
        if type(memory_presentation_revision) is not int or memory_presentation_revision not in (1,2):
            raise ValueError('Unsupported memory presentation revision; save preserved without modification')
        if operation not in ('move','advance','action'):raise ValueError('Unknown accepted operation')
        if minds_revision==2:world.v2_activate_minds()
        if operation=='move':
            previous=getattr(world,'_movement_revision',None)
            world._movement_revision=movement_revision
            try:return world.move(**data)
            finally:
                if previous is None:del world._movement_revision
                else:world._movement_revision=previous
        if operation=='advance':return world.advance(**data)
        if operation=='action':
            # Presentation became chronological in revision2. Old accepted memory
            # conversations/reflections must reproduce their original ledger bytes.
            previous=getattr(world,'_memory_presentation_revision',None)
            world._memory_presentation_revision=memory_presentation_revision
            try:return execute(world,data)
            finally:
                if previous is None:del world._memory_presentation_revision
                else:world._memory_presentation_revision=previous
        raise ValueError('Unknown accepted operation')

    def state(self):
        lab=self.mode=='lab';comparison=None
        if lab and self.branch:
            a,b=self.original.fidelity_state(),self.branch.fidelity_state()
            comparison={'original_minute':a['minute'],'branch_minute':b['minute'],'identical':a==b,
                'changed_fields':[key for key in a if a[key]!=b.get(key)],
                'original_player':self.original.snapshot()['player'],'altered_player':self.branch.snapshot()['player'],
                'original_metrics':self.original.metrics(),'altered_metrics':self.branch.metrics(),
                'original_story':self.original.snapshot().get('story'),'altered_story':self.branch.snapshot().get('story'),
                'interpretation':'One accepted action removed. Later commands replay at original start times where feasible; infeasible commands are disclosed. Changed IDs alone are not an outcome.'}
        result={'world':self.original.snapshot(operator=lab),'branch':self.branch.snapshot(operator=True) if lab and self.branch else None,
            'comparison':comparison,'mode':self.mode,'telemetry_enabled':self.telemetry_enabled,'save_version':self.version,
            'capabilities':{'navigation_revision':2,'route_preview':True,'minds_revision':2},
            'language':{'mode':self.language.cognition.adapter.name,'external_calls':self.language.cognition.metrics['external_calls']},'intervention':copy.deepcopy(self.intervention) if lab else None}
        if lab:
            result['language']=self.language.cognition.debug()
            result['removable_actions']=[{'event_id':c['receipt_id'],'minute':c['at'],'data':copy.deepcopy(c['data'])} for c in self.commands if c['operation']=='action']
            result['product_metrics']={'enabled':self.telemetry_enabled,'events':copy.deepcopy(self.product_events),'local_only':True,'typed_dialogue_logged':False}
        return result

    def context(self,recipient):
        self.original.require_near(recipient);view=self.original.context(recipient)
        # Rich private context stays server-side. Only deliberately authored
        # disclosures, action offers and the present relationship enter the UI.
        return {key:copy.deepcopy(view[key]) for key in ('speaker','greeting','topics','choices','relationship','dialogue_version','counter_order') if key in view}

    def route(self,data):
        """Read-only route preview. Walking still commits validated short steps."""
        from .navigation_v2 import ROOMS, PUBLIC_LOCATIONS, door_points, path_between, path_distance, point_walkable, project_point
        if set(data)-{'x','y','location'}:raise ValueError('Unexpected route fields')
        world=self.original;current=world.state.agent_locations['Player'];start=world.positions['Player']
        destination=data.get('location');has_coordinates='x' in data or 'y' in data
        if has_coordinates and not {'x','y'}<=set(data):raise ValueError('A route needs both coordinates')
        if destination is not None:
            if destination in ROOMS:
                room=ROOMS[destination];target=(data['x'],data['y']) if has_coordinates else (room['x']+room['w']*.5,room['y']+room['h']*.85)
                target_location=destination
            elif destination=='street':
                target=(data['x'],data['y']) if has_coordinates else door_points(current)[0] if current in ROOMS else start
                target_location='street'
            elif destination in PUBLIC_LOCATIONS:
                landmark=next(p for p in world.snapshot()['map']['locations'] if p['id']==destination)
                target=(data['x'],data['y']) if has_coordinates else (landmark['door']['x'],landmark['door']['y'])
                target_location='street'
            else:raise ValueError('Unknown route destination')
        elif has_coordinates:
            target=(data['x'],data['y'])
            target_location=current if current in ROOMS else 'street'
            target=project_point(target,target_location,max_distance=48)
        else:raise ValueError('Choose a route destination')
        points=path_between(start,target,current,target_location)
        nodes=[]
        for index,point in enumerate(points):
            location='street'
            if current in ROOMS and point_walkable(point,current):location=current
            if target_location in ROOMS and point_walkable(point,target_location):location=target_location
            if index==0:location=current
            nodes.append({'x':point[0],'y':point[1],'location':location})
        return {'revision':world.ledger.content_hash(),'navigation_revision':2,'points':nodes,'distance':path_distance(points),
            'destination':{'x':points[-1][0],'y':points[-1][1],'location':target_location}}

    def propose(self,data):
        recipient=data.get('recipient');self.original.require_near(recipient)
        view=self.original.context(recipient)
        if data.get('choice_id') is not None:
            choice=next((c for c in view.get('choices',[]) if c['id']==data['choice_id']),None)
            if not choice or not choice.get('enabled',True):raise ValueError(choice.get('reason','This opportunity is unavailable') if choice else 'Unknown conversation choice')
            action=validate_action(choice['action'],recipient,view)
            proposal={'reply':None,'interpretations':[{'id':'0','label':choice['label'],'transmission':choice.get('description',choice.get('consequence','')),
                'action':action,'cost':choice.get('cost'),'consequence':choice.get('consequence'),**({'terms':copy.deepcopy(choice['terms'])} if 'terms' in choice else {})}],
                'language_source':'authored contextual choice','clarification':None}
        else:proposal=self.language.propose(data.get('text'),recipient,view)
        for interpretation in proposal.get('interpretations',[]):
            action=interpretation['action']
            if action['action']=='buy':
                quote=self.original.buy_quote(action['recipient'],action.get('quantity',1))
                interpretation.update(quote=quote,cost_amount=quote['total_cost'],cost=f"{quote['quantity']} × {quote['unit_price']:g} = {quote['total_cost']:g} coins",
                    available=quote['available'],unavailable_reason=quote['reason'])
            elif action['action']=='accept_commission':
                # Typed and authored choices disclose the same authoritative terms.
                offer=next((c for c in view['choices'] if c['id']=='accept_commission'),None)
                if offer:
                    interpretation.update(transmission=offer['description'],cost=offer['cost'],consequence=offer['consequence'],terms=copy.deepcopy(offer['terms']))
        if self.mode!='lab':proposal.pop('ai_receipt',None)
        self._proposal_counter+=1;identifier=f'p{len(self.commands)}-{self._proposal_counter}'
        self.proposals[identifier]={**copy.deepcopy(proposal),'revision':self.original.ledger.content_hash()}
        if len(self.proposals)>16:self.proposals.pop(next(iter(self.proposals)))
        return {**proposal,'proposal_id':identifier}

    def commit(self,operation,data):
        trial=copy.deepcopy(self.original);at=trial.minute
        receipt=self._perform(trial,operation,copy.deepcopy(data),minds_revision=2)
        command={'operation':operation,'data':copy.deepcopy(data),'at':at,'after':trial.minute,
            'receipt_id':receipt.get('event_id') if operation!='advance' and isinstance(receipt,dict) else None,
            'memory_presentation_revision':2,'movement_revision':2,'minds_revision':2}
        previous=self.original;previous_branch=self.branch;previous_intervention=self.intervention;previous_events=copy.deepcopy(self.product_events)
        self.original=trial;self.commands.append(command);self.branch=None;self.intervention=None
        try:
            if operation=='action':self.record_product('decision',{'choice':data['action']})
            self.save()
        except Exception:
            self.original=previous;self.commands.pop();self.branch=previous_branch;self.intervention=previous_intervention;self.product_events=previous_events
            raise
        self.proposals.clear()
        return {**self.state(),'receipt':receipt if operation!='advance' else None}

    def act(self,data):
        proposal=self.proposals.get(data.get('proposal_id'))
        if not proposal or proposal['revision']!=self.original.ledger.content_hash():raise ValueError('The situation changed. Review this choice again.')
        choice=next((c for c in proposal['interpretations'] if c['id']==data.get('interpretation_id')),None)
        if not choice:raise ValueError('Choose the action you want to confirm')
        action=choice['action'];result=self.commit('action',action)
        recipient=action['recipient']
        if self.original._near(recipient):
            result['reply']=grounded_reply(self.original.context(recipient),action.get('topic','dispute'))
            result['conversation']=self.context(recipient)
        return result

    def trace(self,identifier):
        if type(identifier) is not int or not 0<=identifier<len(self.original.ledger):raise ValueError('Unknown record')
        events=self.original.ledger.events
        if self.mode!='lab' and not self.original._visible(events[identifier]):raise ValueError('Aelia has not learned this record')
        todo=[identifier];seen=set();hidden=set()
        while todo:
            i=todo.pop()
            if i in seen:continue
            if self.mode!='lab' and not self.original._visible(events[i]):hidden.add(i);continue
            seen.add(i);todo.extend(events[i].payload.get('parents',[]))
        return {'events':[self.original.event_dict(events[i],operator=self.mode=='lab') for i in sorted(seen)],
            'unavailable_parent_count':len(hidden),'interpretation':'Recorded dependencies show support and accounts. An executed alternative tests an intervention.'}

    def _fork(self,event_id):
        omitted=next((i for i,c in enumerate(self.commands) if c['operation']=='action' and c['receipt_id']==event_id),None)
        if omitted is None:raise ValueError('Select an accepted action from this chapter')
        candidate=self._fresh();skipped=[]
        for i,command in enumerate(self.commands):
            self._validate_movement_revision(command.get('movement_revision',1))
            self._validate_minds_revision(command.get('minds_revision',0))
            if i==omitted:continue
            trial=copy.deepcopy(candidate)
            try:
                if trial.minute<command['at']:trial.advance(command['at']-trial.minute,'compress')
                self._perform(trial,command['operation'],command['data'],memory_presentation_revision=command.get('memory_presentation_revision',1),
                    movement_revision=command.get('movement_revision',1),minds_revision=command.get('minds_revision',0));candidate=trial
            except ValueError as error:skipped.append({'command':i,'reason':str(error)})
        if candidate.minute<self.original.minute:candidate.advance(self.original.minute-candidate.minute,'compress')
        self.branch=candidate;self.intervention={'kind':'remove_action','event_id':event_id,'removed_command':omitted,'skipped':skipped,
            'scheduling':'Later accepted commands remain at their original start minutes where feasible.'}

    def record_product(self,event,detail=None):
        if not self.telemetry_enabled:return
        if event not in PRODUCT_EVENTS:raise ValueError('Unknown local product event')
        detail=detail or {}
        if not isinstance(detail,dict) or set(detail)-{'screen','choice','mode','location'}:raise ValueError('Only bounded nonpersonal event metadata is allowed')
        categories={'screen':{'opening','street','journal','story','people','bag','places','records','aftermath'},
            'mode':{'game','lab','live','compress','montage','skip'},
            'location':{'street','water','forum_access','bakery','fullery','thermopolium','household'},
            'choice':ACTIONS|{'confirmed'}}
        if any(not isinstance(v,str) or v not in categories[key] for key,v in detail.items()):raise ValueError('Only categorical product metadata is allowed')
        self.product_events.append({'event':event,'elapsed_seconds':round(time.monotonic()-self.opened,3),'minute':self.original.minute,'detail':detail})
        self.product_events=self.product_events[-1000:]

    def apply(self,operation,data):
        with self.lock:
            if not isinstance(data,dict):raise ValueError('Expected an object')
            if operation=='propose':return self.propose(data)
            if operation=='route':return self.route(data)
            if operation=='act':return self.act(data)
            if operation in ('move','advance'):
                allowed={'x','y','location'} if operation=='move' else {'minutes','mode'}
                if set(data)-allowed:raise ValueError('Unexpected action fields')
                if operation=='advance' and data.get('mode')=='naive' and self.mode!='lab':raise ValueError('The coarse baseline belongs in World Lab')
                return self.commit(operation,data)
            if operation=='mode':
                if data.get('mode') not in ('game','lab'):raise ValueError('Unknown view')
                previous=self.mode;self.mode=data['mode']
                try:self.save()
                except Exception:self.mode=previous;raise
                return self.state()
            if operation=='fork':
                if self.mode!='lab' or data.get('kind')!='remove_action':raise ValueError('Open World Lab and choose a supported intervention')
                previous=(self.branch,self.intervention)
                try:self._fork(data.get('event_id'));self.save()
                except Exception:self.branch,self.intervention=previous;raise
                return self.state()
            if operation=='settings':
                if set(data)!={'telemetry_enabled'} or type(data['telemetry_enabled']) is not bool:raise ValueError('Use an explicit local-notes setting')
                previous=self.telemetry_enabled;self.telemetry_enabled=data['telemetry_enabled']
                try:self.save()
                except Exception:self.telemetry_enabled=previous;raise
                return self.state()
            if operation=='product-event':
                previous=copy.deepcopy(self.product_events)
                try:self.record_product(data.get('event'),data.get('detail'));self.save()
                except Exception:self.product_events=previous;raise
                return {'recorded':self.telemetry_enabled}
            raise ValueError('Unknown endpoint')


def make_server(session,host='127.0.0.1',port=8782):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,status,body,content_type='application/json'):
            raw=body if isinstance(body,bytes) else canonical(body).encode() if content_type=='application/json' else body.encode()
            textual=content_type.startswith('text/') or content_type in ('application/json','application/javascript')
            self.send_response(status);self.send_header('Content-Type',content_type+('; charset=utf-8' if textual else ''))
            self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'self'")
            self.end_headers();self.wfile.write(raw)
        def host_allowed(self):return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
        def do_GET(self):
            if not self.host_allowed():return self.send(403,{'error':'Use the local game address'})
            route=urlparse(self.path);path=unquote(route.path)
            try:
                with session.lock:
                    if path=='/api/state':return self.send(200,session.state())
                    if path=='/api/context':return self.send(200,session.context(parse_qs(route.query).get('recipient',[''])[0]))
                    if path=='/api/trace':return self.send(200,session.trace(int(parse_qs(route.query).get('event_id',[''])[0])))
                    if path=='/api/export':
                        if session.mode!='lab':raise ValueError('Open World Lab to export the complete archive')
                        return self.send(200,{'version':session.version,'config':session.config,'origin':session.origin,'commands':session.commands,
                            'events':session.original.ledger.to_json(),'state':session.state()})
                if path in ('/history','/history-rebirth','/research'):
                    file=ROOT/'docs'/('pompeii/HISTORICAL_SOURCE_LEDGER.md' if path=='/history' else 'rebirth/HISTORY_NOTES.md' if path=='/history-rebirth' else 'rebirth/RESEARCH_RESULTS.md')
                    return self.send(200,file.read_text() if file.exists() else 'The research record is being finalized.','text/plain')
                # The 3D client is a separate, locally built presentation. The
                # existing client and all simulation endpoints remain intact.
                if path=='/immersion':
                    self.send_response(302);self.send_header('Location','/immersion/');self.end_headers();return
                mounts=(('/immersion/',ROOT/'kalends_3d'/'dist'),('/immersion-assets/',ROOT/'kalends_3d'/'assets'))
                for prefix,directory in mounts:
                    if not path.startswith(prefix):continue
                    relative=path[len(prefix):] or 'index.html'
                    file=(directory/relative).resolve()
                    allowed=('.html','.css','.js','.json','.glb','.gltf','.bin','.png','.jpg','.jpeg','.webp','.svg','.woff2','.ogg','.mp3','.wav','.txt')
                    if file.is_relative_to(directory.resolve()) and file.is_file() and file.suffix in allowed:
                        mime={'.glb':'model/gltf-binary','.gltf':'model/gltf+json','.js':'application/javascript','.bin':'application/octet-stream'}.get(file.suffix,mimetypes.guess_type(file)[0] or 'application/octet-stream')
                        return self.send(200,file.read_bytes(),mime)
                    return self.send(404,{'error':'3D client file missing. Run npm ci && npm run build in kalends_3d.'})
                file=(STATIC/('index.html' if path=='/' else path.lstrip('/'))).resolve()
                if file.is_relative_to(STATIC.resolve()) and file.is_file() and file.suffix in ('.html','.css','.js','.png','.jpg','.webp','.svg','.woff2','.json'):
                    return self.send(200,file.read_bytes(),mimetypes.guess_type(file)[0] or 'application/octet-stream')
                self.send(404,{'error':'Not found'})
            except OSError:self.send(500,{'error':'The local save could not be written. The last accepted world is preserved; check available storage and retry.'})
            except (ValueError,TypeError,KeyError) as error:self.send(400,{'error':str(error)})
        def do_POST(self):
            if not self.host_allowed():return self.send(403,{'error':'Use the local game address'})
            try:
                if self.headers.get('Origin') not in (None,f'http://{self.headers.get("Host")}'):return self.send(403,{'error':'Use the local game origin'})
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=16384:raise ValueError('Request body must be bounded')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('Expected JSON')
                data=json.loads(self.rfile.read(length),parse_constant=lambda v:(_ for _ in ()).throw(ValueError('Nonfinite input')))
                self.send(200,session.apply(urlparse(self.path).path.removeprefix('/api/'),data))
            except OSError:self.send(500,{'error':'The local save could not be written. The last accepted world is preserved; check available storage and retry.'})
            except (ValueError,TypeError,KeyError,OverflowError) as error:self.send(400,{'error':str(error)})
    return ThreadingHTTPServer((host,port),Handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8782);parser.add_argument('--journal',default='.kalends/rebirth_session.json')
    parser.add_argument('--temporary',action='store_true');parser.add_argument('--migrate-from')
    args=parser.parse_args();session=RebirthSession(None if args.temporary else args.journal,migrate_from=args.migrate_from)
    server=make_server(session,port=args.port)
    print(f'Rebirth is open at http://127.0.0.1:{server.server_port}/',flush=True)
    print('Local illustrated game. External inference is disabled unless explicitly configured and budgeted.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
