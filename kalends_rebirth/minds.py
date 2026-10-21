"""Bounded agent memory, revisable beliefs and a provider-independent planner.

This module never accepts a world or ledger. The caller admits only an agent's
legitimate observation/communication stream. ``Episode.from_experience`` bridges
the existing Kalends Experience contract; it does not grant archival access.

Episodic, compact semantic/social, revision and reflection records share one
hard record budget. A decision retrieves one capped context across *all* options.
Goals are bounded current planner input, identical across memory comparisons.
The complete serialized footprint is reported as well as record counts: one
record is not claimed to equal one byte or one token. Source groups count
communicated lineage, not a proof that a speaker's lineage claim is truthful.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
from typing import Mapping


RETENTION_POLICIES = frozenset({"recency", "salience", "prediction_error", "goal", "hybrid"})
SOCIAL_AXES = frozenset({"reliability", "credibility", "affinity", "competence", "favors", "obligation"})


def _integer(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _number(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return float(value)


def _text(value, name, maximum=512, *, optional=False):
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{name} must be nonempty text of at most {maximum} characters")
    return value


@dataclass(frozen=True)
class MindConfig:
    capacity: int = 32
    context_records: int = 8
    retention_policy: str = "hybrid"
    consolidation: bool = True
    source_lineage: bool = True
    belief_revision: bool = True
    max_goals: int = 8
    max_options: int = 16

    def __post_init__(self):
        if type(self.capacity) is not int or not 1 <= self.capacity <= 256:
            raise ValueError("capacity must be between1 and256 records")
        if type(self.context_records) is not int or not 1 <= self.context_records <= self.capacity:
            raise ValueError("context_records must fit the total record capacity")
        if self.retention_policy not in RETENTION_POLICIES:
            raise ValueError("unknown retention policy")
        if any(type(getattr(self, key)) is not bool for key in ("consolidation", "source_lineage", "belief_revision")):
            raise ValueError("ablation settings must be booleans")
        if type(self.max_goals) is not int or not 1 <= self.max_goals <= 16:
            raise ValueError("max_goals must be between1 and16")
        if type(self.max_options) is not int or not 1 <= self.max_options <= 32:
            raise ValueError("max_options must be between1 and32")


@dataclass(frozen=True)
class SocialSignal:
    """A witnessed consequence, not an unaudited summary personality score."""
    other: str
    axis: str
    delta: float

    def __post_init__(self):
        _text(self.other, "social participant", 64)
        if self.axis not in SOCIAL_AXES:
            raise ValueError("unknown social axis")
        bound = 10000 if self.axis == "obligation" else 9 if self.axis == "favors" else 1
        if abs(_number(self.delta, "social delta")) > bound:
            raise ValueError("social delta is outside its bounded scale")


@dataclass(frozen=True)
class Episode:
    event_id: int
    agent_id: str
    observed_at: int
    kind: str
    text: str
    subject: str | None = None
    predicate: str | None = None
    value: str | None = None
    as_of: int | None = None
    source_agent: str | None = None
    origin_event: int | None = None
    origin_observer: str | None = None
    accepted: bool = True
    participants: tuple[str, ...] = ()
    salience: float = .2
    goal_tags: tuple[str, ...] = ()
    social_signals: tuple[SocialSignal, ...] = ()

    def __post_init__(self):
        _integer(self.event_id, "event_id"); _integer(self.observed_at, "observed_at")
        _text(self.agent_id, "agent_id", 64); _text(self.text, "episode text", 1024)
        if self.kind not in ("observed", "told", "episodic"):
            raise ValueError("unknown episode kind")
        if (self.subject is None) != (self.predicate is None) or (self.subject is None) != (self.value is None):
            raise ValueError("a fact needs subject, predicate and value together")
        for name in ("subject", "predicate", "value"):
            _text(getattr(self, name), name, 128, optional=True)
        if self.as_of is not None and _integer(self.as_of, "as_of") > self.observed_at:
            raise ValueError("a received claim cannot describe an unobserved future fact")
        if self.origin_event is not None:
            _integer(self.origin_event, "origin_event")
        for name in ("source_agent", "origin_observer"):
            _text(getattr(self, name), name, 64, optional=True)
        if self.kind == "told" and self.source_agent is None:
            raise ValueError("received testimony requires its immediate speaker")
        if type(self.accepted) is not bool:
            raise ValueError("accepted must be a boolean")
        if not 0 <= _number(self.salience, "salience") <= 1:
            raise ValueError("salience must lie in[0,1]")
        if len(self.participants) > 12 or len(self.goal_tags) > 8 or len(self.social_signals) > 6:
            raise ValueError("episode metadata exceeds its bounded context")
        for name in self.participants:
            _text(name, "participant", 64)
        for tag in self.goal_tags:
            _text(tag, "goal tag", 128)
        if any(not isinstance(signal, SocialSignal) for signal in self.social_signals):
            raise ValueError("social signals must use the typed contract")
        if self.social_signals and self.kind == "told":
            raise ValueError("social consequences require a direct personal episode; testimony belongs in a belief")
        if self.social_signals and not set(s.other for s in self.social_signals) <= set(self.participants):
            raise ValueError("a social consequence must name an episode participant")

    @classmethod
    def from_experience(cls, agent_id, experience, *, participants=(), salience=.2, goal_tags=(), social_signals=()):
        """Adapt an already admitted per-agent Experience; never query a ledger."""
        return cls(event_id=experience.event_id, agent_id=agent_id, observed_at=experience.tick,
            kind=experience.kind, text=experience.text,
            subject=experience.subject, predicate=experience.predicate, value=experience.value,
            as_of=experience.as_of, source_agent=experience.source_agent,
            origin_event=experience.claimed_origin_event,
            origin_observer=experience.claimed_origin_observer, accepted=experience.accepted,
            participants=tuple(participants), salience=salience, goal_tags=tuple(goal_tags), social_signals=tuple(social_signals))

    @property
    def key(self):
        return (self.subject, self.predicate) if self.subject is not None else None


@dataclass(frozen=True)
class Belief:
    subject: str
    predicate: str
    value: str | None
    status: str
    as_of: int | None = None
    learned_at: int | None = None
    evidence_ids: tuple[int, ...] = ()
    source_groups: tuple[str, ...] = ()
    contradictory_ids: tuple[int, ...] = ()
    superseded_ids: tuple[int, ...] = ()
    direct: bool = False
    confidence: float = 0.0
    confidence_kind: str = "uncalibrated evidence heuristic"
    lineage_kind: str = "communicated origin claims; not independently authenticated"


@dataclass(frozen=True)
class BeliefCondition:
    subject: str
    predicate: str
    equals: str
    min_sources: int = 1
    max_age: int | None = None

    def __post_init__(self):
        for key in ("subject", "predicate", "equals"):
            _text(getattr(self, key), key, 128)
        if type(self.min_sources) is not int or not 1 <= self.min_sources <= 16:
            raise ValueError("min_sources must be between1 and16")
        if self.max_age is not None:
            _integer(self.max_age, "max_age")


@dataclass(frozen=True)
class SocialCondition:
    other: str
    axis: str
    minimum: float | None = None
    maximum: float | None = None

    def __post_init__(self):
        _text(self.other, "social participant", 64)
        if self.axis not in SOCIAL_AXES:
            raise ValueError("unknown social axis")
        for name in ("minimum", "maximum"):
            if getattr(self, name) is not None:
                _number(getattr(self, name), name)
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("social condition bounds are reversed")


@dataclass(frozen=True)
class Goal:
    goal_id: str
    label: str
    priority: float = 1.0
    deadline: int | None = None
    relevant_keys: tuple[tuple[str, str], ...] = ()
    tags: tuple[str, ...] = ()
    status: str = "active"

    def __post_init__(self):
        _text(self.goal_id, "goal_id", 64); _text(self.label, "goal label", 256)
        if not 0 < _number(self.priority, "goal priority") <= 100:
            raise ValueError("goal priority must lie in(0,100]")
        if self.deadline is not None:
            _integer(self.deadline, "goal deadline")
        if self.status not in ("active", "completed", "abandoned"):
            raise ValueError("unknown goal status")
        if len(self.relevant_keys) > 8 or len(self.tags) > 8:
            raise ValueError("goal context exceeds its bounded size")
        for key in self.relevant_keys:
            if len(key) != 2:
                raise ValueError("goal proposition needs subject and predicate")
            for part in key:
                _text(part, "goal proposition", 128)
        for tag in self.tags:
            _text(tag, "goal tag", 128)


@dataclass(frozen=True)
class ActionOption:
    """Candidate registry entry; the world must still validate execution."""
    action_id: str
    label: str
    utility: float
    goal_id: str | None = None
    costs: Mapping[str, float] = field(default_factory=dict)
    conditions: tuple[BeliefCondition, ...] = ()
    social_conditions: tuple[SocialCondition, ...] = ()
    duration: int = 0
    deadline: int | None = None

    def __post_init__(self):
        _text(self.action_id, "action_id", 64); _text(self.label, "action label", 256)
        _number(self.utility, "utility"); _integer(self.duration, "duration")
        _text(self.goal_id, "goal_id", 64, optional=True)
        if self.deadline is not None:
            _integer(self.deadline, "action deadline")
        if len(self.costs) > 8 or len(self.conditions) > 8 or len(self.social_conditions) > 8:
            raise ValueError("option context exceeds its bounded size")
        for key, amount in self.costs.items():
            _text(key, "resource", 64)
            if _number(amount, "resource cost") < 0:
                raise ValueError("resource costs cannot invent an advance reward")
        if any(not isinstance(c, BeliefCondition) for c in self.conditions):
            raise ValueError("belief conditions must use the typed contract")
        if any(not isinstance(c, SocialCondition) for c in self.social_conditions):
            raise ValueError("social conditions must use the typed contract")


@dataclass(frozen=True)
class Decision:
    action_id: str | None
    goal_id: str | None
    utility: float | None
    reasons: tuple[str, ...]
    evidence_ids: tuple[int, ...]
    context_event_ids: tuple[int, ...]
    rejected: tuple[tuple[str, tuple[str, ...]], ...]
    previous_action: str | None = None


class AgentMind:
    version = 1

    def __init__(self, agent_id, config=None):
        self.agent_id = _text(agent_id, "agent_id", 64)
        self.config = config if isinstance(config, MindConfig) else MindConfig(**(config or {}))
        self._episodes = []
        self._semantic = []
        self._revisions = []
        self._reflections = []
        self.goals = []
        self.last_decision = None
        self._serial = 0
        self._observed_count = 0

    def set_goals(self, goals):
        goals = list(goals)
        if len(goals) > self.config.max_goals or any(not isinstance(g, Goal) for g in goals):
            raise ValueError("goals exceed the typed bounded goal contract")
        if len({g.goal_id for g in goals}) != len(goals):
            raise ValueError("goal identifiers must be unique")
        self.goals = goals

    def _active(self, now):
        return [g for g in self.goals if g.status == "active" and (g.deadline is None or now <= g.deadline)]

    def _goal_relevance(self, record, now):
        key = (record.get("subject"), record.get("predicate"))
        tags = set(record.get("goal_tags", ()))
        active = self._active(now)
        return float(any(key in g.relevant_keys or tags.intersection(g.tags) for g in active))

    def _score(self, record, now):
        recency = 1 / (1 + max(0, now - record["observed_at"]) / 180)
        importance = record.get("salience", .2)
        surprise = record.get("prediction_error", 0)
        relevance = self._goal_relevance(record, now)
        policy = self.config.retention_policy
        main = recency if policy == "recency" else importance if policy == "salience" else surprise if policy == "prediction_error" else relevance if policy == "goal" else .25*recency + .3*importance + .2*surprise + .25*relevance
        # Compact facts win a same-event tie without introducing another source.
        return (main, record["observed_at"], record["event_id"], record.get("compact", False), record["serial"])

    def _all(self):
        return self._episodes + self._semantic + self._revisions + self._reflections

    def _prune(self, now):
        keep = {r["serial"] for r in sorted(self._all(), key=lambda r:self._score(r,now), reverse=True)[:self.config.capacity]}
        for key in ("_episodes", "_semantic", "_revisions", "_reflections"):
            setattr(self, key, [r for r in getattr(self,key) if r["serial"] in keep])

    def _new(self, **record):
        self._serial += 1
        return {**record, "serial":self._serial}

    def _root(self, record):
        if record.get("kind") == "observed":
            return f"origin-observer:{self.agent_id}"
        if self.config.source_lineage and record.get("origin_observer"):
            return "origin-observer:" + record["origin_observer"]
        if self.config.source_lineage and record.get("origin_event") is not None:
            return "claimed-root-event:" + str(record["origin_event"])
        return "speaker:" + (record.get("source_agent") or self.agent_id)

    def observe(self, episode):
        if not isinstance(episode, Episode) or episode.agent_id != self.agent_id:
            raise ValueError("a mind can encode only its own admitted experience stream")
        if any(r["event_id"] == episode.event_id for r in self._episodes + self._semantic):
            return False
        prior = self.believe(*episode.key, now=episode.observed_at) if episode.key else None
        surprise = float(prior is not None and prior.value is not None and prior.value != episode.value and episode.accepted)
        record = asdict(episode)
        record["as_of"] = episode.observed_at if episode.as_of is None else episode.as_of
        record["prediction_error"] = surprise
        record["record_type"] = "episode"
        self._episodes.append(self._new(**record))
        if self.config.consolidation and (episode.key or episode.social_signals):
            compact = {k:v for k,v in record.items() if k not in ("text", "participants")}
            compact.update(record_type="semantic",compact=True)
            if episode.key:
                same = [r for r in self._semantic if (r.get("subject"),r.get("predicate")) == episode.key]
                if not self.config.belief_revision and same:
                    compact = None
                elif episode.accepted:
                    root = self._root(record)
                    # One newest head per proposition/source group; a late old
                    # relay never overwrites a fresher head from that source.
                    newer = [r for r in same if self._root(r)==root and r["as_of"] > record["as_of"]]
                    if newer:
                        compact = None
                    else:
                        self._semantic = [r for r in self._semantic if not ((r.get("subject"),r.get("predicate"))==episode.key and self._root(r)==root and r["as_of"]<=record["as_of"])]
            if compact is not None:
                self._semantic.append(self._new(**compact))
        self._observed_count += 1
        self._prune(episode.observed_at)
        if episode.key and self.config.consolidation and self.config.belief_revision:
            current = self.believe(*episode.key,now=episode.observed_at)
            if prior.value is not None and current.value is not None and prior.value != current.value:
                self._revisions.append(self._new(record_type="revision",event_id=episode.event_id,observed_at=episode.observed_at,
                    subject=episode.subject,predicate=episode.predicate,old_value=prior.value,new_value=current.value,
                    evidence_ids=list(current.evidence_ids),replaces=list(prior.evidence_ids),salience=max(.6,episode.salience),
                    prediction_error=surprise,goal_tags=list(episode.goal_tags),reason="newer admitted evidence supersedes a prior interpretation"))
                self._prune(episode.observed_at)
        return True

    def _claim_records(self, records):
        result = {}
        for record in records:
            if record.get("record_type") in ("episode", "semantic") and record.get("subject") is not None:
                result[record["event_id"]] = record
        return list(result.values())

    def _retrieve(self, now, *, keys=(), social=()):
        keys, social = set(keys), set(social)
        relevant=[]
        for record in self._episodes+self._semantic:
            key=(record.get("subject"),record.get("predicate"))
            social_hit=any((s["other"],s["axis"]) in social for s in record.get("social_signals",()))
            if key in keys or social_hit:
                relevant.append(record)
        # Query relevance filters the *retained* pool. It never restores a lost
        # event from the archive. Context contains unique experiences, not both
        # their episodic and compact representations.
        unique={}
        def retrieval_order(record):
            # Persisted belief heads are read before surrounding episodes. Their
            # declared validity time outranks a late relay's receipt time.
            semantic = record.get("record_type") == "semantic"
            vintage = record.get("as_of",record["observed_at"]) if self.config.belief_revision else -record["observed_at"]
            return (semantic,vintage,self._score(record,now))
        for record in sorted(relevant,key=retrieval_order,reverse=True):
            unique.setdefault(record["event_id"],record)
        return list(unique.values())[:self.config.context_records]

    def _belief(self, subject, predicate, records):
        records=[r for r in self._claim_records(records) if (r["subject"],r["predicate"])==(subject,predicate) and r["accepted"]]
        if not records:
            return Belief(subject,predicate,None,"unknown")
        if self.config.belief_revision:
            as_of=max(r["as_of"] for r in records)
            current=[r for r in records if r["as_of"]==as_of]
        else:
            first=min(records,key=lambda r:(r["observed_at"],r["event_id"]))
            as_of=first["as_of"]
            current=[r for r in records if r["as_of"]==as_of and r["value"]==first["value"]]
        values={r["value"] for r in current}
        direct_values={r["value"] for r in current if r["kind"]=="observed"}
        chosen=next(iter(values)) if len(values)==1 else next(iter(direct_values)) if len(direct_values)==1 else None
        if chosen is None:
            return Belief(subject,predicate,None,"conflicted",as_of,min(r["observed_at"] for r in current),
                contradictory_ids=tuple(sorted(r["event_id"] for r in current)),
                superseded_ids=tuple(sorted(r["event_id"] for r in records if r["as_of"]<as_of)))
        support=[r for r in current if r["value"]==chosen]
        groups=tuple(sorted({self._root(r) for r in support}))
        direct=any(r["kind"]=="observed" for r in support)
        confidence=1.0 if direct else min(.9,.35+.15*len(groups))
        return Belief(subject,predicate,chosen,"known",as_of,min(r["observed_at"] for r in support),
            tuple(sorted(r["event_id"] for r in support)),groups,
            tuple(sorted(r["event_id"] for r in current if r["value"]!=chosen)),
            tuple(sorted(r["event_id"] for r in records if r["as_of"]<as_of)),direct,confidence)

    def believe(self, subject, predicate, *, now):
        _integer(now,"now"); _text(subject,"subject",128); _text(predicate,"predicate",128)
        return self._belief(subject,predicate,self._retrieve(now,keys=[(subject,predicate)]))

    @staticmethod
    def _social(other, axis, records):
        signals={}
        for record in records:
            if not record.get("accepted",True):
                continue
            for signal in record.get("social_signals",()):
                if signal["other"]==other and signal["axis"]==axis:
                    signals[(record["event_id"],other,axis)]=signal["delta"]
        baseline=0 if axis in ("favors","obligation") else .5
        result=baseline+sum(signals.values())
        result=max(-9,min(9,result)) if axis=="favors" else max(0,result) if axis=="obligation" else max(0,min(1,result))
        return {"value":round(result,6),"evidence_ids":sorted({key[0] for key in signals}),"baseline":baseline,"basis":"retained witnessed social consequences"}

    def social(self, other, axis, *, now):
        _text(other,"social participant",64)
        if axis not in SOCIAL_AXES:
            raise ValueError("unknown social axis")
        return self._social(other,axis,self._retrieve(now,social=[(other,axis)]))

    def choose(self, options, *, own_resources, now):
        _integer(now,"now");options=list(options)
        if not options or len(options)>self.config.max_options or any(not isinstance(o,ActionOption) for o in options):
            raise ValueError("options exceed the typed bounded action contract")
        if len({o.action_id for o in options})!=len(options):
            raise ValueError("action identifiers must be unique")
        if not isinstance(own_resources,Mapping) or len(own_resources)>16:
            raise ValueError("provide only a bounded map of the actor's own resources")
        for resource,amount in own_resources.items():
            _text(resource,"resource",64);_number(amount,"owned resource")
        keys=[(c.subject,c.predicate) for o in options for c in o.conditions]
        social=[(c.other,c.axis) for o in options for c in o.social_conditions]
        records=self._retrieve(now,keys=keys,social=social)
        active={g.goal_id:g for g in self._active(now)}
        feasible=[];rejected=[]
        for option in options:
            failures=[];evidence=set();reasons=[]
            goal=active.get(option.goal_id) if option.goal_id else None
            if option.goal_id and goal is None:
                failures.append("the associated goal is inactive or overdue")
            deadline=option.deadline if option.deadline is not None else goal.deadline if goal else None
            if deadline is not None and now+option.duration>deadline:
                failures.append("the action cannot finish before its known deadline")
            for resource,cost in option.costs.items():
                if own_resources.get(resource,0)<cost:
                    failures.append(f"insufficient owned {resource}")
            for condition in option.conditions:
                belief=self._belief(condition.subject,condition.predicate,records)
                if belief.value!=condition.equals or belief.status!="known":
                    failures.append(f"no settled retained support for {condition.subject}.{condition.predicate}={condition.equals}")
                elif len(belief.source_groups)<condition.min_sources:
                    failures.append(f"too few distinct communicated source groups for {condition.subject}.{condition.predicate}")
                elif condition.max_age is not None and now-belief.as_of>condition.max_age:
                    failures.append(f"the retained {condition.subject}.{condition.predicate} report is too old")
                else:
                    evidence.update(belief.evidence_ids)
                    reasons.append(f"retained {condition.subject}.{condition.predicate}={belief.value}, dated{belief.as_of}")
            for condition in option.social_conditions:
                assessment=self._social(condition.other,condition.axis,records)
                if condition.minimum is not None and assessment["value"]<condition.minimum or condition.maximum is not None and assessment["value"]>condition.maximum:
                    failures.append(f"retained {condition.other} {condition.axis} does not meet these terms")
                else:
                    evidence.update(assessment["evidence_ids"])
                    reasons.append(f"retained {condition.other} {condition.axis}={assessment['value']:g}")
            if failures:
                rejected.append((option.action_id,tuple(failures)))
            else:
                score=option.utility*(goal.priority if goal else 1)
                feasible.append((score,option.action_id,option,tuple(reasons or ["feasible from owned resources and known prerequisites"]),tuple(sorted(evidence))))
        previous=self.last_decision.action_id if self.last_decision else None
        if feasible:
            score,_,chosen,reasons,evidence=sorted(feasible,key=lambda item:(-item[0],item[1]))[0]
            decision=Decision(chosen.action_id,chosen.goal_id,score,reasons,evidence,tuple(sorted(r["event_id"] for r in records)),tuple(rejected),previous)
        else:
            decision=Decision(None,None,None,("no offered action has currently supported prerequisites",),(),tuple(sorted(r["event_id"] for r in records)),tuple(rejected),previous)
        self.last_decision=decision
        return decision

    def reflect(self, *, now):
        """Derive limited, reversible assessments from retained evidence only.

        Reflection does not manufacture a new experience or directly change a
        relationship score. Social preconditions consume the underlying signals;
        the reflection explains that learned assessment and its supporting IDs.
        """
        _integer(now,"now")
        pairs=sorted({(s["other"],s["axis"]) for r in self._episodes+self._semantic for s in r.get("social_signals",())})
        summaries=[]
        for other,axis in pairs[:8]:
            assessment=self.social(other,axis,now=now)
            if not assessment["evidence_ids"]:
                continue
            policy="require verification before extending credit" if axis in ("reliability","credibility") and assessment["value"]<.4 else "retain the observed social assessment"
            summaries.append({"other":other,"axis":axis,"value":assessment["value"],"policy":policy,"evidence_ids":assessment["evidence_ids"]})
        if summaries and self.config.consolidation:
            # One bounded reflection record; it competes with all other memories.
            ids=sorted({i for s in summaries for i in s["evidence_ids"]})[:self.config.context_records]
            allowed=set(ids)
            summaries=[{**s,"evidence_ids":[i for i in s["evidence_ids"] if i in allowed]} for s in summaries if allowed.intersection(s["evidence_ids"])]
            record=self._new(record_type="reflection",event_id=max(ids),observed_at=now,created_at=now,
                summaries=summaries,evidence_ids=ids,salience=.65,prediction_error=0,goal_tags=[])
            self._reflections.append(record);self._prune(now)
        return {"version":1,"at":now,"assessments":summaries,"goal_states":[{"goal_id":g.goal_id,"status":"overdue" if g.status=="active" and g.deadline is not None and now>g.deadline else g.status} for g in self.goals]}

    def to_dict(self):
        return json.loads(json.dumps({"version":self.version,"agent_id":self.agent_id,"config":asdict(self.config),"episodes":self._episodes,
            "semantic":self._semantic,"revisions":self._revisions,"reflections":self._reflections,
            "goals":[asdict(g) for g in self.goals],"last_decision":asdict(self.last_decision) if self.last_decision else None,
            "serial":self._serial,"observed_count":self._observed_count},allow_nan=False))

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value,dict) or value.get("version")!=cls.version:
            raise ValueError("unsupported mind snapshot version")
        # Round-trip into detached ordinary JSON, rejecting nonfinite values and
        # foreign executable objects. Snapshot parsing does not consult a ledger.
        value=json.loads(json.dumps(value,allow_nan=False))
        mind=cls(value["agent_id"],value["config"])
        for source,target in (("episodes","_episodes"),("semantic","_semantic"),("revisions","_revisions"),("reflections","_reflections")):
            records=value.get(source,[])
            if not isinstance(records,list):
                raise ValueError("mind memory must be bounded record lists")
            setattr(mind,target,records)
        if len(mind._all())>mind.config.capacity:
            raise ValueError("snapshot exceeds the complete memory record budget")
        serials=[]
        for record in mind._all():
            if not isinstance(record,dict) or record.get("record_type") not in ("episode","semantic","revision","reflection"):
                raise ValueError("unknown memory record")
            serials.append(_integer(record["serial"],"serial"));_integer(record["event_id"],"event_id");_integer(record["observed_at"],"observed_at")
            if len(json.dumps(record))>16384:
                raise ValueError("oversized memory record")
            if record["record_type"] in ("episode","semantic") and record.get("agent_id")!=mind.agent_id:
                raise ValueError("snapshot contains another agent's memory")
            if record["record_type"] in ("episode","semantic"):
                fields={k:record[k] for k in Episode.__dataclass_fields__ if k in record}
                signals=tuple(SocialSignal(**s) for s in record.get("social_signals",()))
                fields.update(text=record.get("text","A compact admitted experience."),social_signals=signals,
                    participants=tuple(record.get("participants",[s.other for s in signals])),goal_tags=tuple(record.get("goal_tags",())))
                Episode(**fields)
                expected=set(Episode.__dataclass_fields__)|{"serial","record_type","prediction_error"}
                if record["record_type"]=="semantic":expected.add("compact")
                if set(record)-expected:
                    raise ValueError("unexpected memory fields")
            if not 0<=_number(record.get("salience",.2),"salience")<=1 or not 0<=_number(record.get("prediction_error",0),"prediction error")<=1:
                raise ValueError("invalid memory score")
            for key in ("evidence_ids","replaces"):
                refs=record.get(key,[])
                if not isinstance(refs,list) or len(refs)>mind.config.context_records:
                    raise ValueError("memory evidence exceeds the context budget")
                for ref in refs:_integer(ref,"supporting event")
        if len(set(serials))!=len(serials):
            raise ValueError("memory record identities must be unique")
        mind._serial=_integer(value.get("serial",0),"serial")
        if serials and mind._serial<max(serials):
            raise ValueError("snapshot serial precedes its retained records")
        mind._observed_count=_integer(value.get("observed_count",0),"observed_count")
        goals=[Goal(**{**g,"relevant_keys":tuple(tuple(k) for k in g.get("relevant_keys",())) ,"tags":tuple(g.get("tags",()))}) for g in value.get("goals",[])]
        mind.set_goals(goals)
        if value.get("last_decision") is not None:
            d=value["last_decision"]
            if len(d.get("context_event_ids",()))>mind.config.context_records or len(d.get("rejected",()))>mind.config.max_options:
                raise ValueError("saved decision exceeds its bounded context")
            mind.last_decision=Decision(**{**d,"reasons":tuple(d["reasons"]),"evidence_ids":tuple(d["evidence_ids"]),
                "context_event_ids":tuple(d["context_event_ids"]),"rejected":tuple((a,tuple(r)) for a,r in d["rejected"])})
        return mind

    def footprint(self):
        snapshot=self.to_dict()
        references=sum(len(r.get("evidence_ids",()))+len(r.get("replaces",())) for r in self._all())
        return {"memory_records":len(self._all()),"capacity":self.config.capacity,"episodic_records":len(self._episodes),
            "semantic_social_records":len(self._semantic),"revision_records":len(self._revisions),"reflection_records":len(self._reflections),
            "reference_ids":references,"active_goal_records":len(self.goals),"serialized_bytes":len(json.dumps(snapshot,sort_keys=True,separators=(',',':'),allow_nan=False).encode()),
            "budget_scope":"episodic+semantic/social+revision+reflection records; separately bounded own-goal and last-decision working state; bytes include all state"}

    def inspect(self, *, now):
        _integer(now,"now")
        keys=sorted({(r["subject"],r["predicate"]) for r in self._episodes+self._semantic if r.get("subject") is not None})
        # Private operator view. The integrating server must never project this
        # wholesale into player mode; disclosures require actual communication.
        return {**self.to_dict(),"beliefs":[asdict(self.believe(*key,now=now)) for key in keys],"footprint":self.footprint(),
            "epistemic_boundary":"Only admitted observations; source lineage is communicated, not independently authenticated; no archive lookup."}
