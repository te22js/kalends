"""Outcome-level synthetic economy study of the actual AgentMind contracts.

No provider credentials are loaded. This is not an evaluation of the full game,
natural-language understanding, modern dense retrieval or human enjoyment.
Use ``design`` first; only ``register`` freezes a prospective heldout protocol.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics
import sys
import time

from .minds import AgentMind, MindConfig, Episode, Goal, ActionOption, BeliefCondition, SocialCondition, Belief, SocialSignal
from kalends.memory.base import Experience, Query
from kalends.memory.structured import StructuredMemory
from kalends.memory.hybrid import HybridGuardedMemory
from kalends.memory.retrieval import BM25Index

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ("temporal_correction", "correlated_testimony", "personal_history", "strategic_communication", "long_absence", "goal_revision")
PRIMARY_ARMS = ("fifo", "bm25", "structured", "guarded", "mind", "no_consolidation", "no_lineage", "no_revision")
RETENTION_ARMS = ("retention_recency", "retention_salience", "retention_prediction_error", "retention_goal")
REFERENCE_ARMS = ("observed_history_reference", "omniscient_upper_bound")
ARMS = PRIMARY_ARMS + RETENTION_ARMS + REFERENCE_ARMS
DEVELOPMENT_SEEDS = tuple(range(97000, 97008))
HELDOUT_SEEDS = tuple(range(97100, 97132))
CAPACITY = 12
CONTEXT = 6


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def fingerprint():
    paths = ("kalends_rebirth/minds.py", "kalends_rebirth/mindsbench_v2.py", "kalends/memory/base.py",
             "kalends/memory/structured.py", "kalends/memory/hybrid.py", "kalends/memory/vector.py", "kalends/memory/retrieval.py")
    files = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    return {"sha256": digest(files), "files": files}


def design():
    return {"version": 1, "question": "Do bounded provenance-aware revised beliefs improve executed utility under a fixed selector?",
        "development_seeds": list(DEVELOPMENT_SEEDS), "heldout_seeds": list(HELDOUT_SEEDS),
        "families": list(FAMILIES), "primary_arms": list(PRIMARY_ARMS), "secondary_retention_arms": list(RETENTION_ARMS),
        "separate_references": list(REFERENCE_ARMS), "capacity_records": CAPACITY, "decision_context_records": CONTEXT,
        "primary_contrast": "mind minus structured, paired terminal coin-equivalent utility; each seed averaged across six families",
        "primary_endpoint": "Actor cash change plus declared value of actually delivered goods; credit/report payments are actual funded transfers. All verification/booking costs included.",
        "secondary": ["deadline goal completion", "per-family utility and ablations", "stale/unknown belief relative to admitted evidence", "communicated independent-source groups", "unsupported evidence citations", "memory bytes", "local selection latency"],
        "information": "Identical scoped structured+text observation tapes and public goal/action terms for all deployable arms. No world-state or future-outcome input. Purchased verification is a real costly endogenous observation, separately recorded.",
        "planner": "Same AgentMind.choose and common options_from_view for every arm; only memory retention/retrieval/belief maintenance varies. Utilities and resource/deadline checks fixed.",
        "budgets": "One complete memory record cap across episodic/semantic/social/revision/reflection. Own-goal/last-decision state separately bounded; serialized bytes measured. Semantic records can be smaller; equal slots are not equal bytes. No archive retrieval.",
        "baselines": "FIFO and BM25 retain at most12 episodes. Bounded structured/guarded adapters rebuild original algorithms only from the shared capped context. Guarded equals structured on this keyed track; its text-only hashed fallback is not a dense baseline.",
        "controls": "Four balanced seed variants per family: true/false or unchanged/changed reports, shared/independent roots, fulfilled/broken history, interference/no-interference, resource changes and no feasible profitable action. Verification can waste funds; stale high-salience records can mislead.",
        "source_lineage": "Only communicated origin claims count; no omniscient authentication. False reports can be epistemically supported and unlucky. Roots are not independent merely because relay speakers differ.",
        "inference": "2000 percentile paired bootstrap resamples over32 seed means; families reported separately. Other contrasts descriptive, no significance-star selection.",
        "failure_policy": "Abort on invalid accounting, storage/context/access violations or changed registered source. Preserve raw rows. No heldout tuning; new changes need a new version and unused seeds.",
        "limits": ["Small authored synthetic economy, not full-game outcome evidence", "Structured propositions/terms are shared oracle-format assistance, not language parsing", "No verified embedding model", "No live model or human study", "Policy utilities and evidence thresholds are authored heuristics, not calibrated expected values", "Functional local timings are uncontrolled"],
        "source": fingerprint()}


def experience(record):
    return Experience(tick=record["observed_at"], kind=record["kind"], subject=record.get("subject"), predicate=record.get("predicate"),
        value=record.get("value"), source_agent=record.get("source_agent"), as_of=record["as_of"], accepted=record["accepted"],
        event_id=record["event_id"], text=record.get("text", ""), claimed_origin_kind="observed" if record.get("origin_observer") else None,
        claimed_origin_event=record.get("origin_event"), claimed_origin_observer=record.get("origin_observer"))


class RetrievalMind(AgentMind):
    """Bounded adaptations, not unchanged unbounded historical benchmark arms."""
    def __init__(self, arm):
        self.arm = arm
        super().__init__("Merchant", MindConfig(capacity=CAPACITY, context_records=CONTEXT, retention_policy="recency", consolidation=False))

    def _retrieve(self, now, *, keys=(), social=()):
        if self.arm != "bm25":
            return super()._retrieve(now, keys=keys, social=social)
        index = BM25Index()
        for record in self._episodes:
            index.add(experience(record))
        query = " ".join(f"{s} {p}" for s, p in keys) + " " + " ".join(f"{s} {p}" for s, p in social)
        ids = {e.event_id for _, e in index.search(query, self.config.context_records)}
        return [r for r in self._episodes if r["event_id"] in ids]

    def _belief(self, subject, predicate, records):
        if self.arm not in ("structured", "guarded"):
            return super()._belief(subject, predicate, records)
        legacy = StructuredMemory() if self.arm == "structured" else HybridGuardedMemory()
        for record in self._claim_records(records):
            legacy.ingest(experience(record))
        answer = legacy.answer(Query("belief", f"{subject} {predicate}", subject, predicate))
        if answer.value == "unknown":
            return Belief(subject, predicate, None, "unknown")
        claims = [r for r in self._claim_records(records) if r["subject"] == subject and r["predicate"] == predicate and r["accepted"]]
        chosen = max(claims, key=lambda r: (r["as_of"], r["observed_at"], r["event_id"]))
        # The old independent-source diagnostic counts retained equal-valued
        # accepted claims, including older vintages. Preserve that behavior.
        support = [r for r in claims if r["value"] == answer.value]
        return Belief(subject, predicate, answer.value, "known", chosen["as_of"], chosen["observed_at"],
            tuple(sorted(r["event_id"] for r in support)), tuple(sorted({self._root(r) for r in support})),
            tuple(sorted(r["event_id"] for r in claims if r["value"] != answer.value)),
            tuple(sorted(r["event_id"] for r in claims if r["as_of"] < chosen["as_of"])), chosen["kind"] == "observed", .5)


def make_mind(arm):
    if arm in ("fifo", "bm25", "structured", "guarded"):
        return RetrievalMind(arm)
    options = {"capacity": CAPACITY, "context_records": CONTEXT}
    if arm == "no_consolidation": options["consolidation"] = False
    elif arm == "no_lineage": options["source_lineage"] = False
    elif arm == "no_revision": options["belief_revision"] = False
    elif arm.startswith("retention_"): options["retention_policy"] = arm.removeprefix("retention_")
    elif arm in REFERENCE_ARMS: options.update(capacity=256, context_records=256, consolidation=False, retention_policy="recency")
    elif arm != "mind": raise ValueError("Unknown study arm")
    return AgentMind("Merchant", MindConfig(**options))


@dataclass
class Case:
    seed: int
    family: str
    variant: int
    actual_ready: bool
    now: int
    deadline: int
    goods_value: int
    preferred_cost: int
    safe_cost: int
    verification_cost: int
    initial_cash: int
    source_requirement: int
    observations: list[Episode]
    missing_change_observation: bool = False

    @property
    def subject(self):
        return {"personal_history": "partner", "strategic_communication": "report", "goal_revision": "route"}.get(self.family, "supplier")

    @property
    def predicate(self):
        return {"personal_history": "kept_promise", "strategic_communication": "authorized", "goal_revision": "open"}.get(self.family, "available")

    def public(self):
        return {"family": self.family, "subject": self.subject, "predicate": self.predicate, "deadline": self.deadline,
            "preferred_cost": self.preferred_cost, "safe_cost": self.safe_cost, "verification_cost": self.verification_cost,
            "source_requirement": self.source_requirement, "preferred_utility": 6, "safe_utility": 3}


def generate_case(seed, family):
    if family not in FAMILIES or type(seed) is not int: raise ValueError("Unknown family or invalid seed")
    rng = random.Random(f"minds-v2:{family}:{seed}")
    variant = seed % 4
    now = 7*1440 if family == "long_absence" else 240 + rng.randrange(40)
    value = rng.randrange(10, 14)
    ready = variant in (0, 2)
    case = Case(seed, family, variant, ready, now, now+8, value, value-6, value-3, 1, 30, 1, [])
    words = ("The account says", "The dated dispatch records", "The received terms report", "The message gives")

    def claim(when, vintage, value, *, source="Witness", origin="Witness", salience=.8, direct=False, social=()):
        identifier = len(case.observations)
        text = f"{rng.choice(words)} {case.subject} {case.predicate} {value}, as of {vintage}; received {when}. "
        text += "I observed this directly." if direct else f"{source} relays the originating account of {origin}."
        case.observations.append(Episode(identifier, "Merchant", when, "observed" if direct else "told", text,
            case.subject, case.predicate, value, vintage, None if direct else source, identifier if direct else 0,
            "Merchant" if direct else origin, participants=("Partner",), salience=salience,
            goal_tags=("settle",), social_signals=tuple(social)))

    def routine(count, start, end):
        for n in range(count):
            tick = start + (end-start)*n//max(1,count)
            case.observations.append(Episode(len(case.observations), "Merchant", tick, "episodic",
                f"Routine inventory sweep {n}; {rng.choice(('lamp','rope','jar','cloth'))} checked at {tick}.", salience=.05))

    if family == "temporal_correction":
        claim(0, 0, "yes")
        claim(now-20, now-20, "yes" if ready else "no", source="Checker", origin="Checker", direct=True)
        routine(2, now-18, now-10)
        claim(now-3, 0, "yes", source="RelayA", origin="Witness")
        claim(now-1, 0, "yes", source="RelayB", origin="Witness")
    elif family == "correlated_testimony":
        case.source_requirement = 2
        for n, source in enumerate(("RelayA", "RelayB", "RelayC")):
            claim(now-10+n, now-20, "yes", source=source, origin="Original" if variant < 2 else f"Observer{n}")
        case.missing_change_observation = not ready
    elif family == "personal_history":
        signal = SocialSignal("Partner", "reliability", .3 if ready else -.3)
        claim(10, 10, "yes" if ready else "no", direct=True, social=(signal,), salience=.95)
        routine(30 if variant < 2 else 3, 20, now-2)
    elif family == "strategic_communication":
        claim(0, 0, "yes", source="Seller", origin="OldLicense")
        claim(now-15, now-15, "yes" if ready else "no", source="RightsHolder", origin="RightsHolder", salience=.7)
        claim(now-1, 0, "yes", source="InterestedRelay", origin="OldLicense")
    elif family == "long_absence":
        claim(10, 10, "yes" if ready else "no", salience=.95)
        routine(48, 20, now-4)
        if variant >= 2:
            claim(now-1, now-1, "yes" if ready else "no", direct=True, salience=.4)
    elif family == "goal_revision":
        claim(0, 0, "yes", direct=True)
        if variant in (0, 1):
            ready = False
            case.actual_ready = False
            claim(now-1, now-1, "no", direct=True)
        elif variant == 2:
            case.actual_ready = True
            case.initial_cash = case.preferred_cost - 1
            case.safe_cost = max(1, case.preferred_cost-2)
        else:
            case.actual_ready = True
            case.deadline = now  # No offered action can meet the known deadline.
    assert case.observations == sorted(case.observations, key=lambda e:(e.observed_at,e.event_id))
    return case


class Economy:
    """Three funded contract types; no memory policy can mutate these balances."""
    def __init__(self, case):
        self.case = case
        self.cash = {"Merchant": float(case.initial_cash), "Partner": 100., "Inspector": 20., "Courier": 20., "Buyer": 100., "Escrow": 0.}
        self.goods = {"Merchant": 0, "Preferred": 2, "Safe": 2}
        self.reports = {"Buyer": []}
        self.now = case.now
        self.ledger = []
        self.verification_used = False
        self.completed = False
        self.initial_total = sum(self.cash.values())
        if case.family == "personal_history":
            self.now=0
            self.transfer("Merchant","Partner",2,"earlier observed loan")
            self.now=10
            if case.actual_ready:self.transfer("Partner","Merchant",3,"earlier kept promise")
            self.ledger.append({"at":10,"event_id":0,"earlier_obligation":"fulfilled" if case.actual_ready else "broken"})
            self.now=case.now
        self.starting_cash=self.cash["Merchant"]

    def transfer(self, source, target, amount, reason):
        if type(amount) not in (int,float) or not math.isfinite(amount) or amount < 0 or self.cash[source] < amount: raise ValueError("Unfunded transfer")
        self.cash[source] -= amount; self.cash[target] += amount
        self.ledger.append({"at":self.now,"source":source,"target":target,"coins":amount,"reason":reason})

    def execute(self, action_id):
        if action_id == "abstain": return []
        if action_id == "verify":
            if self.verification_used or self.now+1>self.case.deadline: raise ValueError("Verification unavailable")
            self.transfer("Merchant","Inspector",self.case.verification_cost,"paid direct check")
            self.verification_used=True;self.now+=1
            return [Episode(1000, "Merchant", self.now, "observed", "A paid direct check establishes the present terms.",
                self.case.subject, self.case.predicate, "yes" if self.case.actual_ready else "no", self.now,
                participants=("Partner",), salience=.9, goal_tags=("settle",)),
                Episode(1001,"Merchant",self.now,"observed","The paid check is available as a current proof.",
                self.case.subject,"verified", "yes" if self.case.actual_ready else "no",self.now,salience=.9,goal_tags=("settle",))]
        preferred = action_id in ("preferred_testimony", "preferred_proof")
        if action_id not in ("preferred_testimony", "preferred_proof", "safe"): raise ValueError("Unknown contract")
        cost = self.case.preferred_cost if preferred else self.case.safe_cost
        duration = 2 if preferred else 1
        if self.now+duration>self.case.deadline or self.cash["Merchant"]<cost: raise ValueError("Contract is infeasible")
        fulfilled = self.case.actual_ready if preferred else True
        # Validate all funding and goods before the first transfer. A rejected
        # registry action cannot leave a partial payment in this small world.
        if self.case.family == "personal_history":
            if self.cash["Partner"] < (6 if preferred and fulfilled else cost+3 if not preferred else 0):raise ValueError("Unfunded counterparty")
        elif self.case.family == "strategic_communication":
            if fulfilled and self.cash["Buyer"]<cost+(6 if preferred else 3):raise ValueError("Unfunded buyer")
        elif fulfilled and self.goods["Preferred" if preferred else "Safe"]<1:
            raise ValueError("No physical stock")
        if self.case.family == "personal_history":
            if not preferred:
                self.transfer("Partner","Escrow",cost+3,"reserve agreed collateral")
            self.transfer("Merchant","Partner",cost,"advance a funded contract")
            self.now += duration
            if not preferred:
                self.transfer("Escrow","Merchant",cost+3,"settle collateralized obligation")
                fulfilled=True
            elif fulfilled:
                self.transfer("Partner","Merchant",cost+6,"settle kept obligation")
        elif self.case.family == "strategic_communication":
            fee=cost
            self.transfer("Merchant","Courier",fee,"commission report delivery")
            self.now += duration
            if fulfilled:
                self.transfer("Buyer","Merchant",fee+(6 if preferred else 3),"pay for authorized report")
                self.reports["Buyer"].append("exclusive dispatch" if preferred else "public notice")
                self.ledger.append({"at":self.now,"communication":"exclusive dispatch" if preferred else "public notice","to":"Buyer","authorized":True})
        else:
            self.transfer("Merchant","Partner",cost,"reserve a dated delivery; payment at risk")
            self.now += duration
            if fulfilled:
                stock="Preferred" if preferred else "Safe"
                if self.goods[stock]<1:raise ValueError("No physical stock")
                self.goods[stock]-=1;self.goods["Merchant"]+=1
                self.ledger.append({"at":self.now,"goods_from":stock,"goods_to":"Merchant","quantity":1,"reason":"actual delivered unit"})
        self.completed = fulfilled
        self.ledger.append({"at":self.now,"contract":action_id,"fulfilled":fulfilled})
        return []

    def check(self):
        assert abs(sum(self.cash.values())-self.initial_total)<1e-9
        assert min(self.cash.values())>=0 and sum(self.goods.values())==4 and min(self.goods.values())>=0

    def utility(self):
        return self.cash["Merchant"]-self.starting_cash+self.goods["Merchant"]*self.case.goods_value


def options_from_view(mind, public, *, own_coins, now, verified):
    """Shared authored selector input; this function cannot inspect world truth."""
    subject,predicate=public["subject"],public["predicate"]
    belief=mind.believe(subject,predicate,now=now)
    proof=mind.believe(subject,"verified",now=now)
    options=[ActionOption("safe","Use collateral or the reliable alternative",3,"settle",{"coins":public["safe_cost"]},duration=1),
             ActionOption("abstain","Take no contract",0)]
    if proof.value != "no":
        options.append(ActionOption("preferred_testimony","Use the better supported offer",6,"settle",{"coins":public["preferred_cost"]},
            (BeliefCondition(subject,predicate,"yes",public["source_requirement"]),),duration=2))
        options.append(ActionOption("preferred_proof","Use a directly checked offer",6,"settle",{"coins":public["preferred_cost"]},
            (BeliefCondition(subject,"verified","yes"),),duration=2))
    uncertain = belief.status != "known" or (belief.value == "yes" and len(belief.source_groups)<public["source_requirement"])
    if uncertain and not verified:
        options.append(ActionOption("verify","Pay for a current direct check",4,"settle",{"coins":public["verification_cost"]},duration=1))
    return mind.choose(options,own_resources={"coins":own_coins},now=now)


def run_arm(case, arm):
    world=Economy(case);mind=make_mind(arm)
    mind.set_goals([Goal("settle","Complete a funded arrangement",deadline=case.deadline,
        relevant_keys=((case.subject,case.predicate),(case.subject,"verified")),tags=("settle",))])
    observed=set();admitted=list(case.observations)
    for episode in case.observations:
        mind.observe(episode);observed.add(episode.event_id)
    if arm == "omniscient_upper_bound":
        # Deliberately privileged and clearly separated from deployable policies.
        extra=Episode(2000,"Merchant",case.now,"observed","Privileged evaluator truth; unavailable to deployable policies.",
            case.subject,"verified","yes" if case.actual_ready else "no",case.now,salience=1)
        mind.observe(extra);observed.add(extra.event_id);admitted.append(extra)
    decisions=[];latencies=[];unsupported=[];max_records=mind.footprint()["memory_records"]
    for _ in range(3):
        started=time.perf_counter_ns()
        decision=options_from_view(mind,case.public(),own_coins=world.cash["Merchant"],now=world.now,verified=world.verification_used)
        latencies.append((time.perf_counter_ns()-started)/1e6)
        decisions.append(asdict(decision))
        unsupported.extend(sorted(set(decision.evidence_ids+decision.context_event_ids)-observed))
        if len(decision.context_event_ids)>mind.config.context_records:raise AssertionError("Context overflow")
        action=decision.action_id or "abstain"
        for observation in world.execute(action):mind.observe(observation);observed.add(observation.event_id);admitted.append(observation)
        world.check();max_records=max(max_records,mind.footprint()["memory_records"])
        if action != "verify":break
    belief=mind.believe(case.subject,case.predicate,now=world.now)
    claims=[e for e in admitted if e.key==(case.subject,case.predicate) and e.accepted]
    freshest=max(e.as_of for e in claims)
    available_values={e.value for e in claims if e.as_of==freshest}
    stale=belief.value is not None and len(available_values)==1 and belief.value not in available_values
    expected_value=next(iter(available_values)) if len(available_values)==1 else None
    latest=[e for e in claims if e.as_of==freshest and e.value==expected_value]
    expected_groups={"origin-observer:Merchant" if e.kind=="observed" else "origin-observer:"+e.origin_observer if e.origin_observer else "claimed-root-event:"+str(e.origin_event) if e.origin_event is not None else "speaker:"+e.source_agent for e in latest}
    attribution_evaluable=expected_value is not None and belief.value==expected_value
    retained_claims=[r for r in mind._claim_records(mind._episodes+mind._semantic) if (r["subject"],r["predicate"])==(case.subject,case.predicate)]
    failure="none"
    if belief.status=="unknown":failure="retrieval" if retained_claims else "retention"
    elif stale:failure="belief_revision"
    elif not world.completed:failure="missing_observation" if case.missing_change_observation else "planning_or_execution"
    footprint=mind.footprint()
    if footprint["memory_records"]>mind.config.capacity:raise AssertionError("Memory capacity exceeded")
    if unsupported:raise AssertionError("Unobserved evidence entered a decision")
    return {"arm":arm,"utility":world.utility(),"goal_completed":world.completed,"cash":world.cash,"goods":world.goods,
        "minute":world.now,"reports":world.reports,"verification_used":world.verification_used,"verification_cost":case.verification_cost if world.verification_used else 0,
        "decisions":decisions,"final_belief":asdict(belief),"stale_against_admitted_evidence":stale,"unknown_belief":belief.status=="unknown",
        "unobserved_change":case.missing_change_observation,"unsupported_evidence_ids":unsupported,"ledger":world.ledger,
        "footprint":footprint,"max_memory_records":max_records,"selection_ms":latencies,
        "attribution_evaluable":attribution_evaluable,"communicated_source_group_error":abs(len(expected_groups)-len(belief.source_groups)) if attribution_evaluable else None,
        "expected_communicated_groups":sorted(expected_groups),"failure_stage_diagnostic":failure,
        "diagnostic_limits":"Stage tags are deterministic traces, not independently adjudicated causal diagnoses. Missing observation is separate from memory error."}


def interval(values):
    if not values:return None
    rng=random.Random(94617)
    boot=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(2000))
    return {"mean":statistics.mean(values),"low":boot[49],"high":boot[1949],"unit":"paired seed mean","n":len(values)}


def summarize(rows):
    summary={"worlds":len(rows),"families":{},"arms":{},"primary_contrast":None,
        "scope":"Bounded structured synthetic economy with fixed authored selector, not full-game/live-model/human evidence"}
    for family in (None,)+FAMILIES:
        selected=[r for r in rows if family is None or r["family"]==family]
        target=summary["arms"] if family is None else summary["families"].setdefault(family,{})
        for arm in ARMS:
            cells=[r["arms"][arm] for r in selected]
            target[arm]={"mean_utility":statistics.mean(c["utility"] for c in cells),"goal_completion_rate":statistics.mean(c["goal_completed"] for c in cells),
                "verification_rate":statistics.mean(c["verification_used"] for c in cells),"stale_rate":statistics.mean(c["stale_against_admitted_evidence"] for c in cells),
                "unknown_rate":statistics.mean(c["unknown_belief"] for c in cells),"mean_serialized_bytes":statistics.mean(c["footprint"]["serialized_bytes"] for c in cells),
                "max_memory_records":max(c["max_memory_records"] for c in cells),"unsupported_citations":sum(len(c["unsupported_evidence_ids"]) for c in cells),
                "median_selection_ms":statistics.median(t for c in cells for t in c["selection_ms"]),
                "source_attribution_denominator":sum(c["attribution_evaluable"] for c in cells),
                "source_group_error_sum":sum(c["communicated_source_group_error"] or 0 for c in cells),
                "failure_stages":{stage:sum(c["failure_stage_diagnostic"]==stage for c in cells) for stage in ("none","retrieval","retention","belief_revision","missing_observation","planning_or_execution")}}
    seeds=sorted({r["seed"] for r in rows})
    differences=[statistics.mean(r["arms"]["mind"]["utility"]-r["arms"]["structured"]["utility"] for r in rows if r["seed"]==seed) for seed in seeds]
    summary["primary_contrast"]=interval(differences)
    summary["per_family_primary_contrast"]={family:interval([r["arms"]["mind"]["utility"]-r["arms"]["structured"]["utility"] for r in rows if r["family"]==family]) for family in FAMILIES}
    return summary


def run(output, *, phase, registration=None):
    if phase not in ("pilot","heldout"):raise ValueError("Unknown study phase")
    before=fingerprint()
    if phase=="heldout":
        if registration is None or json.loads(Path(registration).read_text())!=design():raise ValueError("Heldout registration/source differs")
    seeds=DEVELOPMENT_SEEDS if phase=="pilot" else HELDOUT_SEEDS
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    metadata={"phase":phase,"started_utc":datetime.now(timezone.utc).isoformat(),"python":sys.version,"platform":platform.platform(),"design":design()}
    (output/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    rows=[];seed=None;family=None;arm=None
    try:
        with (output/"raw.jsonl").open("x") as stream:
            for seed in seeds:
                for family in FAMILIES:
                    case=generate_case(seed,family)
                    row={"seed":seed,"family":family,"variant":case.variant,"observation_digest":digest([asdict(e) for e in case.observations]),
                        "case":asdict(case),"arms":{}}
                    for arm in ARMS:row["arms"][arm]=run_arm(case,arm)
                    stream.write(canonical(row)+"\n");stream.flush();rows.append(row)
                print(f"{phase}: seed {seed} complete",flush=True)
        if fingerprint()!=before:raise ValueError("Source changed during run")
        result=summarize(rows)
        (output/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
        metadata.update(finished_utc=datetime.now(timezone.utc).isoformat(),rows=len(rows),source_unchanged=True)
        (output/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    except BaseException as error:
        failure={"phase":phase,"seed":seed,"family":family,"arm":arm,"completed_rows":len(rows),"error_type":type(error).__name__,"message":str(error),"source_at_failure":fingerprint()}
        (output/"failure.json").write_text(json.dumps(failure,indent=2)+"\n")
        raise
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("design")
    registration=sub.add_parser("register");registration.add_argument("--out",required=True)
    pilot=sub.add_parser("pilot");pilot.add_argument("--out",required=True)
    heldout=sub.add_parser("run");heldout.add_argument("--registration",required=True);heldout.add_argument("--out",required=True)
    args=parser.parse_args(argv)
    if args.command=="design":print(json.dumps(design(),indent=2))
    elif args.command=="register":
        path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("x") as stream:stream.write(json.dumps(design(),indent=2)+"\n")
        print(path)
    else:
        result=run(args.out,phase="pilot" if args.command=="pilot" else "heldout",registration=getattr(args,"registration",None))
        print(json.dumps({"worlds":result["worlds"],"primary_contrast":result["primary_contrast"]},indent=2))


if __name__=="__main__":main()
