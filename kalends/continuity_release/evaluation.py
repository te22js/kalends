"""Frozen-memory comparisons on independent workflow fixtures; offline only.

The evaluator alone owns truth/assertions. Controller input is limited to newly
admitted own observations, public contracts/register and owned credits. No model,
archive lookup, hidden-state option filter or target update is used.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict, replace
import gzip
import hashlib
import json
from pathlib import Path
import random
import statistics
import time

from kalends.events import Ledger
from kalends.world import WorldState, apply_event
from kalends.genesis.simulation import GenesisEconomy
from kalends.pompeii.temporal import EventClock
from kalends.experience_os.minds import PersistentMind
from kalends.next_phase.diagnostic import DependencyRetentionMind
from kalends.memory.base import Experience
from kalends.memory.retrieval import BM25Index, tokens
from kalends_rebirth.minds import ActionOption, BeliefCondition, Episode, Goal, MindConfig

ROOT = Path(__file__).resolve().parents[2]
ARMS = ('dependency_retention', 'v3_hybrid', 'bm25_fifo', 'bm25_task', 'latest_per_key')
STATE_BYTES, CONTEXT_BYTES, CAPACITY, CONTEXT = 16384, 4096, 16, 4


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def key(f):
    return f['subject'] + '.' + f['predicate']


def matches(register, facts):
    return all(register.get(key(f)) == f['value'] for f in facts)


def public_actions(actions):
    """Static effect-key schema is public; scripted outcomes are evaluator-only.

    Expose possible written keys, never attempt counts/statuses/private values
    from an outcome override. This schema is identical across memory arms.
    """
    return [{**{k: v for k, v in a.items() if k != 'outcomes'},
        'effect_keys': sorted({key(f) for f in a.get('effects', []) +
            [f for o in a.get('outcomes', []) for f in o.get('effects', [])]})} for a in actions]


class LexicalMind(PersistentMind):
    """Rebuilt BM25 over bounded episodes. No hidden archive or dense claim.

    Task-aware variant retains lexical matches to public goal/condition cues.
    Both use unchanged V3 belief revision/planner and no duplicate semantic store.
    Index/query material is charged by Controller before and during retrieval.
    """
    task_aware = False

    def _query(self, keys=(), social=()):
        return ' '.join(' '.join(pair) for pair in list(keys) + list(social)).replace('_', ' ')

    def _score(self, record, now):
        if not self.task_aware:
            return super()._score(record, now)
        query = set(tokens(' '.join(g.label + ' ' + self._query(g.relevant_keys) for g in self._active(now))))
        document = set(tokens(self._text(record)))
        # Conventional task-aware lexical retention, without exact-key bonus.
        return (len(query & document) / max(1, len(document)), record['as_of'], record['event_id'], record['serial'])

    @staticmethod
    def _text(r):
        return r.get('text', '') + ' ' + ' '.join(str(r.get(k) or '') for k in ('subject', 'predicate', 'value'))

    def _retrieve(self, now, *, keys=(), social=()):
        index, records = BM25Index(), {}
        for r in self._episodes:
            if not r.get('accepted', True):
                continue
            records[r['event_id']] = r
            index.add(Experience(r['observed_at'], r['kind'], r.get('subject'), r.get('predicate'),
                r.get('value'), r.get('source_agent'), r['as_of'], r['accepted'], r['event_id'], self._text(r)))
        return [records[e.event_id] for _, e in index.search(self._query(keys, social), self.config.context_records)]


class TaskLexicalMind(LexicalMind):
    task_aware = True


class LatestMind(PersistentMind):
    """Accepted latest-per-key/source revision heads; unrelated receipts FIFO.

    Same total record/byte/context budget. Contradictory equal-time sources are
    retained, rather than selecting the answer from canonical world truth.
    """
    def observe(self, episode):
        if episode.key and episode.accepted:
            same = [r for r in self._episodes if (r.get('subject'), r.get('predicate')) == episode.key and r.get('accepted')]
            vintage = episode.as_of if episode.as_of is not None else episode.observed_at
            newest = max((r['as_of'] for r in same), default=-1)
            if vintage < newest:
                return False
            self._episodes = [r for r in self._episodes if not ((r.get('subject'), r.get('predicate')) == episode.key and r.get('accepted') and r['as_of'] < vintage)]
        return super().observe(episode)


CLASSES = dict(zip(ARMS, (DependencyRetentionMind, PersistentMind, LexicalMind, TaskLexicalMind, LatestMind)))


def new_mind(arm):
    config = MindConfig(capacity=CAPACITY, context_records=CONTEXT, retention_policy='hybrid')
    if arm in ('bm25_fifo', 'bm25_task', 'latest_per_key'):
        config = replace(config, retention_policy='recency', consolidation=False)
    return CLASSES[arm]('Player', config)


class WorkflowWorld:
    """Research fixture adapter over existing ledger, clock and projections."""
    def __init__(self, spec, seed):
        self.spec = spec
        self.ledger, self.state, self.economy, self.clock = Ledger(), WorldState(), GenesisEconomy(), EventClock()
        self.public_register, self.stream, self.receipts, self.attempts = {}, [], [], {}
        self.emit({'cash_delta': {'Player': spec['credits']}}, scope='private')
        for fact in spec['initial_facts']:
            self.fact(fact, public=fact.get('public', False))
        rng = random.Random(seed)
        for row in spec['timeline']:
            if row.get('kind') == 'noise':
                for i in range(row['count']):
                    at = row['at'] + rng.randrange(row.get('spread_minutes', 0) + 1)
                    self.clock.schedule(at, 'noise', {'text': f"{row.get('label', 'Intake receipt')} {rng.randrange(1000000)} item {i}"})
            else:
                self.clock.schedule(row['at'], 'fact', row)

    @property
    def now(self):
        return self.clock.now

    def emit(self, payload, *, scope='public', etype='state_change'):
        ev = self.ledger.append(self.now, etype, 'workflow', ('Player',), payload, scope)
        apply_event(self.state, ev)
        self.economy.apply(ev)
        return ev

    def fact(self, f, *, public, observe=False, unknown=False):
        value = str(int(self.state.facts.get(key(f), '0')) + int(f['value'])) if f.get('op') == 'increment' else f['value']
        ev = self.emit({'prop': [f['subject'], f['predicate']], 'value': value}, scope='public' if public else 'private')
        if public:
            self.public_register[key(f)] = value
        if observe and not unknown:
            self.observation(ev, {**f, 'value': value})
        return ev

    def observation(self, ev, row):
        told = row.get('visibility') == 'told'
        self.stream.append(Episode(ev.event_id, 'Player', self.now, 'told' if told else 'observed',
            row.get('text', f"Observed {row['subject']}.{row['predicate']}={row['value']}"),
            row['subject'], row['predicate'], row['value'], row.get('as_of', self.now),
            source_agent=row.get('source') if told else None, accepted=row.get('accepted', True), salience=row.get('salience', .5)))

    def advance(self, at):
        def dispatch(task):
            row = task['data']
            if task['kind'] == 'noise':
                ev = self.emit({'category': 'unrelated', 'title': row['text']})
                self.stream.append(Episode(ev.event_id, 'Player', self.now, 'episodic', row['text'], salience=.25))
                return
            visibility = row.get('visibility', 'direct')
            update = row.get('update_truth', visibility != 'told')
            if update:
                ev = self.fact(row, public=visibility == 'public')
            else:
                payload = {'speaker': row.get('source', 'registrar'), 'listener': 'Player', 'title': row.get('text', '')}
                ev = self.emit(payload, scope='private', etype='tell')
            if visibility != 'hidden':
                if visibility == 'direct' and self.state.facts.get(key(row)) != row['value']:
                    raise ValueError('direct observation differs from actual world')
                self.observation(ev, row)
        self.clock.advance(at, dispatch)

    def register(self):
        return dict(self.public_register)

    def execute(self, action):
        rejected = not matches(self.state.facts, action.get('requires', []) + action.get('public_requires', []))
        cost = action.get('cost', 0)
        if self.economy.cash['Player'] < cost:
            rejected = True
        effects = []
        if rejected:
            status = 'rejected'
        elif 'inspect' in action:
            status = 'succeeded'
            for f in action['inspect']:
                row = {**f, 'value': self.state.facts.get(key(f), 'unknown')}
                ev = self.emit({'category': 'inspection', 'prop': [f['subject'], f['predicate']], 'value': row['value']}, scope='private')
                self.observation(ev, row)
        else:
            self.attempts[action['id']] = self.attempts.get(action['id'], 0) + 1
            override = next((o for o in action.get('outcomes', []) if o['attempt'] == self.attempts[action['id']]), None)
            status = override['status'] if override else 'succeeded'
            effects = override.get('effects', []) if override else action.get('effects', [])
            for f in effects:
                self.fact(f, public=f.get('public', True), observe=status != 'unknown', unknown=status == 'unknown')
        receipt = {'action': action['id'], 'status': status, 'at': self.now, 'cost': 0 if rejected else cost}
        ev = self.emit({'category': 'execution_receipt', **receipt, 'cash_delta': {'Player': -receipt['cost']}})
        receipt['event_id'] = ev.event_id
        self.receipts.append(receipt)
        self.stream.append(Episode(ev.event_id, 'Player', self.now, 'episodic', f"Execution {action['id']} returned {status}; cost {receipt['cost']}", salience=.5))
        return receipt

    def snapshot(self):
        return {'ledger': self.ledger.to_json(), 'clock': self.clock.snapshot(), 'public_register': self.public_register,
            'stream': [asdict(e) for e in self.stream], 'receipts': self.receipts, 'attempts': self.attempts}

    @classmethod
    def restore(cls, spec, snapshot):
        world = cls.__new__(cls)
        world.spec, world.ledger, world.state, world.economy = spec, Ledger(), WorldState(), GenesisEconomy()
        for row in snapshot['ledger']:
            ev = world.ledger.append(row['tick'], row['etype'], row['location'], tuple(row['actors']), row['payload'], row['scope'])
            if ev.event_id != row['event_id']:
                raise ValueError('checkpoint identity mismatch')
            apply_event(world.state, ev)
            world.economy.apply(ev)
        world.clock = EventClock.from_snapshot(snapshot['clock'])
        world.public_register = dict(snapshot['public_register'])
        world.stream = [Episode(**{**r, 'participants': tuple(r['participants']), 'goal_tags': tuple(r['goal_tags']), 'social_signals': ()}) for r in snapshot['stream']]
        world.receipts, world.attempts = snapshot['receipts'], snapshot['attempts']
        return world


class Controller:
    def __init__(self, arm):
        self.arm, self.mind = arm, new_mind(arm)
        self.plan = {'cursor': 0, 'recovery': [], 'receipt_ids': []}
        self.max_state_bytes = self.max_context_bytes = self.max_index_bytes = self.byte_evictions = 0
        self.max_query_bytes = self.retrieval_calls = self.context_dropped_records = self.withheld_decisions = 0
        # Evaluator-only diagnostics, never read by a policy or checkpointed as
        # agent memory. No retrieved values are cached outside the charged mind.
        self._retrieval_events = []
        self._install_retrieval_guard()

    def snapshot(self):
        return {'arm': self.arm, 'mind': self.mind.to_dict(), 'plan': self.plan}

    @classmethod
    def restore(cls, snapshot):
        c = cls(snapshot['arm'])
        c.mind = CLASSES[c.arm].from_dict(snapshot['mind'])
        c.plan = json.loads(canonical(snapshot['plan']))
        c._install_retrieval_guard()
        return c

    def accounting(self):
        return {name: getattr(self, name) for name in (
            'max_state_bytes', 'max_context_bytes', 'max_index_bytes', 'max_query_bytes',
            'byte_evictions', 'retrieval_calls', 'context_dropped_records', 'withheld_decisions')}

    def index_material(self, query=''):
        if not isinstance(self.mind, LexicalMind):
            return {}
        # Mirror the actual existing BM25Index data, including its copied
        # Experience payload, postings, per-document lengths, df and total length.
        # Rebuilding a full index is reserved even between calls; the actual
        # query replaces the empty query during each guarded retrieval.
        index = BM25Index()
        for r in self.mind._episodes:
            if r.get('accepted', True):
                index.add(Experience(r['observed_at'], r['kind'], r.get('subject'), r.get('predicate'),
                    r.get('value'), r.get('source_agent'), r['as_of'], r['accepted'], r['event_id'], self.mind._text(r)))
        return {'documents': [{'tokens': dict(postings), 'length': length, 'experience': asdict(experience)}
                for postings, length, experience in index._docs],
            'document_frequency': dict(index._df), 'total_length': index._total_len,
            'query': query, 'query_tokens': tokens(query)}

    def charge(self, now, *, query=None):
        while True:
            lexical = isinstance(self.mind, LexicalMind)
            index_size = len(canonical(self.index_material(query if query is not None else '')).encode()) if lexical else 0
            query_size = len(canonical(query).encode()) if query is not None else 0
            size = len(canonical(self.snapshot()).encode()) + index_size + (query_size if not lexical else 0)
            if size <= STATE_BYTES:
                break
            records = self.mind._all()
            if not records:
                raise ValueError('controller/goals/plans exceed charged state budget')
            victim = min(records, key=lambda r: self.mind._score(r, now))['serial']
            for name in ('_episodes', '_semantic', '_revisions', '_reflections'):
                setattr(self.mind, name, [r for r in getattr(self.mind, name) if r['serial'] != victim])
            self.byte_evictions += 1
        self.max_state_bytes = max(self.max_state_bytes, size)
        self.max_index_bytes = max(self.max_index_bytes, index_size)
        self.max_query_bytes = max(self.max_query_bytes, query_size)
        return size

    def _install_retrieval_guard(self):
        """Apply one external byte/context gate to every native retrieval call.

        This wraps, rather than changes, all frozen mechanisms. In particular
        observe/believe and a discarded first planning cycle cannot evade the
        same accounting used by the final action-selection cycle.
        """
        retrieve = self.mind._retrieve

        def guarded(now, *, keys=(), social=()):
            keys, social = tuple(keys), tuple(social)
            query = self.mind._query(keys, social) if isinstance(self.mind, LexicalMind) else {
                'keys': list(keys), 'social': list(social)}
            before_evictions = self.byte_evictions
            state_size = self.charge(now, query=query)
            candidates = retrieve(now, keys=keys, social=social)
            context = []
            # Preserve the mechanism's ranking; admit only the prefix that fits
            # the common count AND byte limits, before any belief/planner uses it.
            for record in candidates:
                if len(context) >= CONTEXT or len(canonical(context + [record]).encode()) > CONTEXT_BYTES:
                    break
                context.append(record)
            context_size = len(canonical(context).encode())
            dropped = len(candidates) - len(context)
            self.retrieval_calls += 1
            self.context_dropped_records += dropped
            self.max_context_bytes = max(self.max_context_bytes, context_size)
            self._retrieval_events.append({'context_event_ids': [r['event_id'] for r in context],
                'context_bytes': context_size, 'query_bytes': len(canonical(query).encode()),
                'index_bytes': len(canonical(self.index_material(query)).encode()) if isinstance(self.mind, LexicalMind) else 0,
                'state_bytes': state_size, 'state_evictions': self.byte_evictions - before_evictions,
                'context_dropped_records': dropped})
            self._retrieval_events = self._retrieval_events[-64:]
            return context

        self.mind._retrieve = guarded

    @staticmethod
    def goals(spec_goals, actions, public):
        return [Goal(g['id'], g['label'], g['priority'], g['deadline'],
            relevant_keys=tuple(sorted({(f['subject'], f['predicate']) for a in actions if a.get('goal') == g['id'] for f in a.get('requires', [])})),
            status='completed' if matches(public, g['complete_when']) else 'active') for g in spec_goals]

    def admit(self, episodes, goals, now):
        self.mind.set_goals(goals)
        for e in episodes:
            if e.agent_id != 'Player' or e.observed_at > now:
                raise ValueError('inadmissible participant stream')
            self.mind.observe(e)
            self.charge(now)
        self.plan['cursor'] += len(episodes)
        self.charge(now)

    def select(self, goals, actions, public, credits, now):
        complete = {g.goal_id for g in goals if g.status == 'completed'}
        available = [a for a in actions if a.get('goal') not in complete and matches(public, a.get('public_requires', [])) and credits >= a.get('cost', 0)]
        recovery = self.plan['recovery']
        mutations = [a for a in available if 'inspect' not in a and a['id'] not in recovery]
        def options(rows):
            return [ActionOption(a['id'], a['label'], a.get('priority', 1), a.get('goal'), costs={'credits': a.get('cost', 0)},
                conditions=tuple(BeliefCondition(f['subject'], f['predicate'], f['value'], max_age=f.get('max_age', 129600), allow_direct=True) for f in a.get('requires', [])),
                deadline=next((g.deadline for g in goals if g.goal_id == a.get('goal')), None)) for a in rows] + [ActionOption('wait', 'Wait without supported execution', 0)]
        self.mind.set_goals(goals)
        self.charge(now)
        # The same native V3 evidence-based planner is used for every arm.
        withheld = []

        def cycle(offered):
            selected = self.mind.cycle([], goals, offered, {'credits': credits}, now)['decision']
            self.charge(now)
            retained = set(self.mind.retained_event_ids())
            missing_evidence = set(selected['evidence_ids']) - retained
            missing_context = set(selected['context_event_ids']) - retained
            if selected['action_id'] not in (None, 'wait') and (missing_evidence or missing_context):
                reason = 'Common budget gate withheld a selection whose supporting context was evicted.'
                withheld.append({'action_id': selected['action_id'],
                    'missing_evidence_ids': sorted(missing_evidence), 'missing_context_ids': sorted(missing_context)})
                self.withheld_decisions += 1
                self.mind.evaluate(selected['action_id'], 'cancelled', now=now, detail=reason)
                self.mind.last_decision = replace(self.mind.last_decision, action_id='wait', goal_id=None,
                    utility=0, reasons=(reason,), evidence_ids=(), context_event_ids=(), rejected=())
                selected = asdict(self.mind.last_decision)
                self.charge(now)
            return selected

        opts = options(mutations)
        decision = cycle(opts)
        if decision['action_id'] in (None, 'wait'):
            inspections = [a for a in available if 'inspect' in a]
            if recovery:
                failed = [a for a in actions if a['id'] in recovery]
                touched = {key(f) for a in failed for f in a.get('requires', [])} | {k for a in failed for k in a.get('effect_keys', [])}
                inspections = [a for a in inspections if touched & {key(f) for f in a['inspect']}]
            else:
                # Inspect only keys needed by an available unfinished mutation.
                needed = {key(f) for a in mutations for f in a.get('requires', [])}
                inspections = [a for a in inspections if needed & {key(f) for f in a['inspect']}]
            opts = options(inspections)
            decision = cycle(opts)
        context = {r['event_id']: r for r in self.mind._episodes + self.mind._semantic if r['event_id'] in decision['context_event_ids']}
        detail = {'decision': decision, 'context': list(context.values()), 'state_bytes': self.charge(now),
            'index_bytes': len(canonical(self.index_material()).encode()) if isinstance(self.mind, LexicalMind) else 0,
            'public_register': public, 'options': [asdict(o) for o in opts], 'controller': json.loads(canonical(self.plan)),
            'retrievals': self._retrieval_events, 'budget_withheld': withheld, 'accounting': self.accounting()}
        self._retrieval_events = []
        return decision, detail

    def feedback(self, action, receipt, now, actions=()):
        self.mind.evaluate(action['id'], 'succeeded' if receipt['status'] == 'succeeded' else 'failed', now=now)
        if receipt['status'] in ('failed', 'partial', 'unknown', 'rejected'):
            self.plan['recovery'] = sorted(set(self.plan['recovery']) | {action['id']})
        elif 'inspect' in action:
            inspected = {key(f) for f in action['inspect']}
            reconciled = {a['id'] for a in actions if inspected & ({key(f) for f in a.get('requires', [])} | set(a.get('effect_keys', [])))}
            self.plan['recovery'] = [a for a in self.plan['recovery'] if a not in reconciled]
        self.plan['receipt_ids'] = (self.plan['receipt_ids'] + [receipt['event_id']])[-4:]
        self.charge(now)


def score(spec, world):
    results = []
    receipts = world.receipts
    for a in spec['assertions']:
        kind = a['type']
        if kind == 'fact':
            passed = matches(world.state.facts, [a])
        elif kind == 'receipt_count':
            n = sum(r['action'] == a['action'] and ('status' not in a or r['status'] == a['status']) for r in receipts)
            passed = a.get('min', 0) <= n <= a.get('max', float('inf'))
        elif kind == 'order':
            before = [i for i, r in enumerate(receipts) if r['action'] == a['before'] and r['status'] == 'succeeded']
            after = [i for i, r in enumerate(receipts) if r['action'] == a['after'] and r['status'] == 'succeeded']
            passed = bool(before and after and before[0] < after[0])
        elif kind == 'never':
            passed = not any(r['action'] == a['action'] for r in receipts)
        elif kind == 'credits_min':
            passed = world.economy.cash['Player'] >= a['value']
        elif kind == 'rejections_max':
            passed = sum(r['status'] == 'rejected' for r in receipts) <= a['value']
        else:
            raise ValueError('unknown scoring assertion')
        results.append({'assertion': a, 'passed': bool(passed)})
    return results


def validate(doc):
    if doc.get('version') != 1 or not isinstance(doc.get('cases'), list) or not doc['cases']:
        raise ValueError('invalid workflow document')
    ids = set()
    for s in doc['cases']:
        if s['id'] in ids:
            raise ValueError('duplicate case')
        ids.add(s['id'])
        if not 1 <= s['horizon_minutes'] <= 129600 or not 0 <= s['credits'] <= 20 or not 6 <= len(s['decisions']) <= 32 or not 1 <= len(s['goals']) <= 8 or not 1 <= len(s['actions']) <= 14 or len(s['timeline']) > 128:
            raise ValueError('workflow bounds exceeded')
        if sorted(d['at'] for d in s['decisions']) != [d['at'] for d in s['decisions']] or any(not 0 <= d['at'] <= s['horizon_minutes'] or not 1 <= d.get('max_actions', 1) <= 4 for d in s['decisions']):
            raise ValueError('invalid decision windows')
        action_ids = {a['id'] for a in s['actions']}
        if len(action_ids) != len(s['actions']) or 'wait' in action_ids:
            raise ValueError('duplicate/reserved action')
        for row in s['timeline']:
            if row.get('kind') == 'noise':
                if not 0 <= row['count'] <= 64 or row['at'] + row.get('spread_minutes', 0) > s['horizon_minutes']:
                    raise ValueError('invalid noise')
            elif row.get('as_of', row['at']) > row['at'] or not 0 <= row['at'] <= s['horizon_minutes']:
                raise ValueError('invalid observation time')
        Controller.goals(s['goals'], s['actions'], {})
    return doc


def run_case(spec, seed, arm, *, checkpoint=True):
    world, controller, trace = WorkflowWorld(spec, seed), Controller(arm), []
    contracts = public_actions(spec['actions'])
    peak = {'state': 0, 'context': 0, 'index': 0, 'evictions': 0}
    checkpoints = 0
    for window in spec['decisions']:
        world.advance(window['at'])
        for _ in range(window.get('max_actions', 1)):
            public = world.register()
            goals = Controller.goals(spec['goals'], contracts, public)
            controller.admit(world.stream[controller.plan['cursor']:], goals, world.now)
            if checkpoint and window.get('checkpoint'):
                metrics, retrievals = controller.accounting(), controller._retrieval_events
                before = {'world': world.snapshot(), 'controller': controller.snapshot()}
                world = WorkflowWorld.restore(spec, json.loads(canonical(before['world'])))
                controller = Controller.restore(json.loads(canonical(before['controller'])))
                for name, value in metrics.items():
                    setattr(controller, name, value)
                controller._retrieval_events = retrievals
                if sha(before) != sha({'world': world.snapshot(), 'controller': controller.snapshot()}):
                    raise ValueError('checkpoint does not round-trip')
                checkpoints += 1
            decision, detail = controller.select(goals, contracts, public, world.economy.cash['Player'], world.now)
            detail['at'] = world.now
            if decision['action_id'] in (None, 'wait'):
                trace.append(detail)
                break
            action = next(a for a in spec['actions'] if a['id'] == decision['action_id'])
            receipt = world.execute(action)
            controller.feedback(next(a for a in contracts if a['id'] == action['id']), receipt, world.now, contracts)
            detail['receipt'] = receipt
            trace.append(detail)
            peak = {k: max(peak[k], v) for k, v in {'state': controller.max_state_bytes, 'context': controller.max_context_bytes, 'index': controller.max_index_bytes, 'evictions': controller.byte_evictions}.items()}
    world.advance(spec['horizon_minutes'])
    results = score(spec, world)
    peak = {k: max(peak[k], v) for k, v in {'state': controller.max_state_bytes, 'context': controller.max_context_bytes, 'index': controller.max_index_bytes, 'evictions': controller.byte_evictions}.items()}
    return {'case': spec['id'], 'family': spec['family'], 'seed': seed, 'arm': arm,
        'passed': all(r['passed'] for r in results), 'assertions': results,
        'goals': {g['id']: matches(world.register(), g['complete_when']) for g in spec['goals']},
        'credits_remaining': world.economy.cash['Player'], 'spend': spec['credits'] - world.economy.cash['Player'],
        'outcomes': dict(Counter(r['status'] for r in world.receipts)),
        'inspections': sum('inspect' in next(a for a in spec['actions'] if a['id'] == r['action']) for r in world.receipts),
        'peak_bytes': peak, 'accounting': controller.accounting(),
        'checkpoints': checkpoints, 'trace': trace, 'world': world.snapshot()}


def verify_candidate():
    manifest = json.loads((ROOT / 'results/continuity_release/candidate_freeze.json').read_text())
    for path, expected in manifest['source_sha256'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('frozen candidate dependency changed: ' + path)


def study(path, out, seeds):
    verify_candidate()
    if path.name == 'heldout.json':
        freeze = json.loads((ROOT / 'results/continuity_release/research_freeze.json').read_text())
        for file, expected in freeze['source_sha256'].items():
            if hashlib.sha256((ROOT / file).read_bytes()).hexdigest() != expected:
                raise ValueError('Final comparison source changed after freeze: ' + file)
        if hashlib.sha256(path.read_bytes()).hexdigest() != freeze['heldout_sha256'] or list(seeds) != freeze['heldout_seeds']:
            raise ValueError('Final comparison task bytes or seeds differ from the frozen protocol')
    doc = validate(json.loads(path.read_text()))
    out.mkdir(parents=True, exist_ok=False)
    (out / 'raw').mkdir()
    start, rows = time.monotonic(), []
    manifest = {'task_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'task_file': str(path), 'seeds': list(seeds),
        'arms': list(ARMS), 'budgets': {'state_bytes': STATE_BYTES, 'context_bytes': CONTEXT_BYTES, 'records': CAPACITY, 'context_records': CONTEXT},
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('kalends/continuity_release',) for p in sorted((ROOT / folder).glob('*.py'))},
        'model_calls': 0, 'spend_usd': 0}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for spec in doc['cases']:
        for seed in seeds:
            for arm in ARMS:
                result = run_case(spec, seed, arm)
                # Every executed world is compared with uninterrupted execution.
                replay = run_case(spec, seed, arm, checkpoint=False)
                result['replay_equal'] = result['world']['ledger'] == replay['world']['ledger'] and result['goals'] == replay['goals'] and result['credits_remaining'] == replay['credits_remaining']
                if not result['replay_equal']:
                    raise ValueError('checkpoint altered executed outcomes')
                with gzip.open(out / 'raw' / f"{spec['id']}_{seed}_{arm}.json.gz", 'wt') as f:
                    json.dump(result, f)
                rows.append({k: v for k, v in result.items() if k not in ('trace', 'world')})
    summary = {'runs': len(rows), 'seconds': round(time.monotonic() - start, 3), 'model_calls': 0, 'spend_usd': 0,
        'by_case': {s['id']: {a: {'passed': sum(r['passed'] for r in rows if r['case'] == s['id'] and r['arm'] == a),
            'n': len(seeds), 'mean_spend': statistics.mean(r['spend'] for r in rows if r['case'] == s['id'] and r['arm'] == a)} for a in ARMS} for s in doc['cases']},
        'all_replays_equal': all(r['replay_equal'] for r in rows), 'rows': rows}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, indent=2))
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tasks', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seeds', type=int, default=6)
    p.add_argument('--seed-start', type=int, default=0)
    args = p.parse_args()
    if not 1 <= args.seeds <= 64:
        p.error('seeds must be 1..64')
    study(args.tasks.resolve(), args.out.resolve(), range(args.seed_start, args.seed_start + args.seeds))

if __name__ == '__main__':
    main()
