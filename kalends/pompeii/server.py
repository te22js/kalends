"""Local Pompeii game, durable command replay, and an isolated World Lab."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlparse

from .district import PompeiiConfig
from .language import ProposalLanguage, execute, grounded_reply
from .world import PompeiiWorld

ROOT=Path(__file__).resolve().parents[2]
STATIC=Path(__file__).with_name("static")


class PompeiiSession:
    version=3

    def __init__(self,journal_path=None,provider=None):
        self.lock=threading.RLock()
        self.journal_path=Path(journal_path) if journal_path else None
        self.language=ProposalLanguage(provider)
        self.mode="game"
        self.original=PompeiiWorld()
        self.config=asdict(self.original.config)
        self.commands=[]
        self.proposals={}
        self.branch=None
        self.intervention=None
        if self.journal_path and self.journal_path.exists():
            payload=json.loads(self.journal_path.read_text())
            if payload.get("version")!=self.version: raise ValueError("Unsupported Pompeii save version; preserve this file and start a new journal.")
            self.config=payload["config"]
            self.original=PompeiiWorld(PompeiiConfig(**self.config))
            for command in payload["commands"]:
                self._perform(self.original,command["operation"],command["data"])
            if self.original.ledger.content_hash()!=payload["ledger_hash"]:
                raise ValueError("Saved replay hash differs from this runtime; the original save has been preserved.")
            self.commands=payload["commands"]
            self.mode=payload.get("mode","game")
            if payload.get("intervention"):
                self._fork(payload["intervention"]["event_id"])

    def save(self):
        if self.journal_path:
            self.journal_path.parent.mkdir(parents=True,exist_ok=True)
            payload={"version":self.version,"config":self.config,"commands":self.commands,"mode":self.mode,
                "ledger_hash":self.original.ledger.content_hash(),"intervention":self.intervention}
            temp=self.journal_path.with_suffix(".tmp")
            temp.write_text(json.dumps(payload,indent=2,allow_nan=False)+"\n")
            temp.replace(self.journal_path)

    @staticmethod
    def _perform(world,operation,data):
        if operation=="move": return world.move(**data)
        if operation=="advance": return world.advance(**data)
        if operation=="action": return execute(world,data)
        raise ValueError("Unknown accepted operation")

    def commit(self,operation,data):
        # Run the entire action on a candidate. Failed validation, expired promises,
        # and persistence failure leave the accepted world byte-for-byte unchanged.
        candidate=copy.deepcopy(self.original)
        at=candidate.minute
        receipt=self._perform(candidate,operation,data)
        command={"operation":operation,"data":copy.deepcopy(data),"at":at,
            "receipt_id":receipt.get("event_id") if isinstance(receipt,dict) else None,
            "after":candidate.minute}
        before=self.original
        self.original=candidate
        self.commands.append(command)
        try: self.save()
        except Exception:
            self.original=before;self.commands.pop();raise
        self.proposals.clear()
        return {**self.state(),"receipt":receipt if operation!="advance" else None}

    def state(self):
        operator=self.mode=="lab"
        comparison=None
        if self.branch:
            a,b=self.original.fidelity_state(),self.branch.fidelity_state()
            comparison={"original_minute":a["minute"],"branch_minute":b["minute"],
                "identical":a==b,"changed_fields":[k for k in a if a[k]!=b.get(k)],
                "original_metrics":self.original.metrics(),"altered_metrics":self.branch.metrics(),
                "interpretation":"Executed removal of one accepted action. Later commands stay at their original times where feasible; infeasible commands are explicitly skipped. Ledger IDs alone are not an outcome difference."}
        return {"world":self.original.snapshot(operator=operator),"branch":self.branch.snapshot(operator=operator) if operator and self.branch else None,
            "comparison":comparison if operator else None,"mode":self.mode,"language":copy.deepcopy(self.language.metrics),
            "intervention":copy.deepcopy(self.intervention) if operator else None,
            "removable_actions":[{"event_id":c["receipt_id"],"operation":c["operation"],"data":c["data"],"minute":c["at"]} for c in self.commands if c["operation"]=="action"] if operator else []}

    def propose(self,data):
        recipient=data.get("recipient")
        self.original.require_near(recipient)
        proposal=self.language.propose(data.get("text"),recipient,self.original.private_view(recipient))
        revision=self.original.ledger.content_hash()
        identifier=f"p{len(self.commands)}-{len(self.proposals)}"
        self.proposals[identifier]={**copy.deepcopy(proposal),"revision":revision}
        if len(self.proposals)>16: self.proposals.pop(next(iter(self.proposals)))
        return {**proposal,"proposal_id":identifier}

    def act(self,data):
        proposal=self.proposals.get(data.get("proposal_id"))
        if not proposal: raise ValueError("That proposal has expired. Speak again.")
        if proposal["revision"]!=self.original.ledger.content_hash(): raise ValueError("The world changed. Review a fresh proposal.")
        choice=next((c for c in proposal["interpretations"] if c["id"]==data.get("interpretation_id")),None)
        if not choice: raise ValueError("Choose an interpretation")
        action=choice["action"]
        result=self.commit("action",action)
        if action["action"]=="talk":
            result["reply"]=grounded_reply(self.original.private_view(action["recipient"]),action.get("topic","memory"))
        return result

    def trace(self,identifier):
        if type(identifier) is not int or not 0<=identifier<len(self.original.ledger): raise ValueError("Unknown event")
        events=self.original.ledger.events
        if self.mode!="lab" and not self.original._visible(events[identifier]): raise ValueError("This record is not available to your character")
        todo=[identifier];seen=set();hidden=set()
        while todo:
            i=todo.pop()
            if i in seen: continue
            if self.mode!="lab" and not self.original._visible(events[i]): hidden.add(i);continue
            seen.add(i);todo.extend(events[i].payload.get("parents",[]))
        return {"events":[self.original.event_dict(events[i],operator=self.mode=="lab") for i in sorted(seen)],"unavailable_parent_count":len(hidden),
            "interpretation":"Recorded informational or accounting dependencies; counterfactual effects require an executed World Lab intervention."}

    def _fork(self,event_id):
        target=next((i for i,c in enumerate(self.commands) if c["operation"]=="action" and c["receipt_id"]==event_id),None)
        if target is None: raise ValueError("Select an accepted player action, rather than a scheduled event")
        candidate=PompeiiWorld(PompeiiConfig(**self.config));skipped=[]
        for i,command in enumerate(self.commands):
            if i==target: continue
            trial=copy.deepcopy(candidate)
            if trial.minute<command["at"]: trial.advance(command["at"]-trial.minute,"compress")
            try:
                self._perform(trial,command["operation"],command["data"])
                candidate=trial
            except ValueError as error:
                skipped.append({"command":i,"reason":str(error)})
        if candidate.minute<self.original.minute: candidate.advance(self.original.minute-candidate.minute,"compress")
        self.branch=candidate
        self.intervention={"kind":"remove_action","event_id":event_id,"removed_command":target,"skipped":skipped,
            "scheduling":"Replay later accepted commands at their original start minutes, or as soon as feasible if an earlier action runs longer."}

    def apply(self,operation,data):
        with self.lock:
            if not isinstance(data,dict): raise ValueError("Expected a JSON object")
            if operation=="propose": return self.propose(data)
            if operation=="act": return self.act(data)
            if operation=="interact":
                if set(data)-{"action","recipient","quantity"}: raise ValueError("Unexpected interaction fields")
                return self.commit("action",data)
            if operation=="move":
                if set(data)-{"x","y","location"}: raise ValueError("Unexpected movement fields")
                return self.commit("move",data)
            if operation=="advance":
                if set(data)-{"minutes","mode"}: raise ValueError("Unexpected time fields")
                if data.get("mode")=="naive" and self.mode!="lab": raise ValueError("The distorted coarse baseline belongs in World Lab")
                return self.commit("advance",data)
            if operation=="mode":
                if data.get("mode") not in ("game","lab"): raise ValueError("Unknown view mode")
                self.mode=data["mode"];self.save();return self.state()
            if operation=="fork":
                if self.mode!="lab": raise ValueError("Open World Lab before changing recorded history")
                if data.get("kind")!="remove_action": raise ValueError("Unsupported intervention")
                self._fork(data.get("event_id"));self.save();return self.state()
            raise ValueError("Unknown endpoint")


def make_server(session,host="127.0.0.1",port=8780):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def send(self,status,body,content_type="application/json"):
            raw=json.dumps(body,allow_nan=False).encode() if content_type=="application/json" else body if isinstance(body,bytes) else body.encode()
            self.send_response(status)
            self.send_header("Content-Type",content_type+ ("; charset=utf-8" if not content_type.startswith("image/") else ""))
            self.send_header("Content-Length",str(len(raw)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            route=urlparse(self.path);path=route.path
            try:
                with session.lock:
                    if path=="/api/state": return self.send(200,session.state())
                    if path=="/api/trace":
                        identifier=int(parse_qs(route.query).get("event_id",[""])[0])
                        return self.send(200,session.trace(identifier))
                    if path=="/api/export":
                        if session.mode!="lab": raise ValueError("Open World Lab to export the operator ledger")
                        return self.send(200,{"version":session.version,"config":session.config,"commands":session.commands,
                            "events":session.original.ledger.to_json(),"state":session.state()})
                if path in ("/history","/research"):
                    filename="HISTORICAL_SOURCE_LEDGER.md" if path=="/history" else "RESEARCH_PAPER.md"
                    file=ROOT/"docs"/"pompeii"/filename
                    return self.send(200,file.read_text() if file.exists() else "Research report is being finalized.","text/plain")
                filename={"/":"index.html","/index.html":"index.html","/style.css":"style.css","/app.js":"app.js"}.get(path)
                if filename:
                    file=STATIC/filename
                    return self.send(200,file.read_bytes(),mimetypes.guess_type(filename)[0] or "text/plain")
                return self.send(404,{"error":"Not found"})
            except (ValueError,TypeError,KeyError) as error: self.send(400,{"error":str(error)})
        def do_POST(self):
            try:
                origin=self.headers.get("Origin")
                expected=f"http://{self.headers.get('Host')}"
                if origin and origin!=expected: return self.send(403,{"error":"Use the local game origin"})
                length=int(self.headers.get("Content-Length","0"))
                if not 0<length<=16384: raise ValueError("Request body must be 1..16384 bytes")
                if self.headers.get("Content-Type","").split(";")[0]!="application/json": raise ValueError("Expected application/json")
                operation=urlparse(self.path).path.removeprefix("/api/")
                data=json.loads(self.rfile.read(length),parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
                self.send(200,session.apply(operation,data))
            except (ValueError,TypeError,KeyError,OverflowError) as error: self.send(400,{"error":str(error)})
    return ThreadingHTTPServer((host,port),Handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,default=8780)
    parser.add_argument("--journal",default=".kalends/pompeii_session.json")
    parser.add_argument("--temporary",action="store_true",help="Do not load or save a session")
    args=parser.parse_args()
    session=PompeiiSession(None if args.temporary else args.journal)
    server=make_server(session,port=args.port)
    print(f"Pompeii is open at http://127.0.0.1:{server.server_port}/",flush=True)
    print("Time advances during foreground LIVE play or explicit movement/skip. No offline catch-up.",flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=="__main__": main()
