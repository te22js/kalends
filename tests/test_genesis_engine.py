"""Genesis invariants: bounded information, physical outcomes and participation."""
import copy
import json
from dataclasses import asdict

import pytest

from kalends.actionbench.policy import AlwaysDeferPolicy
from kalends.genesis import GenesisConfig, GenesisSimulation
from kalends.genesis.policy import GenesisPolicy, effective_records
from kalends.genesis.simulation import GenesisEconomy, INSPECTION_FEE
from kalends.memory.base import Experience


def make(**kwargs):
    return GenesisSimulation(GenesisConfig(**kwargs))


def digest(sim):
    return json.dumps(sim.snapshot(operator=True), sort_keys=True)


def test_multi_day_run_determinism_and_partition_steps():
    first = make(n_ticks=32).step(3).step(10).run()
    second = make(n_ticks=32).run()
    assert first.ledger.to_json() == second.ledger.to_json()
    assert first.decisions == second.decisions
    assert first.metrics() == second.metrics()
    assert first.tick == 31 and first.done
    assert [c['deadline'] for c in first.economy.commitments['Livia']] == [7, 15, 23, 31]


def test_identity_fork_copies_queues_memory_preferences_and_accounts():
    sim = make(n_ticks=24).step(4)
    branch = sim.fork({'kind': 'none'})
    branch.preferences['Livia']['caution'] = .1
    assert sim.preferences['Livia']['caution'] == .75
    branch.preferences['Livia']['caution'] = .75
    assert branch._retained['Livia'] is not sim._retained['Livia']
    branch.run(); sim.run()
    assert branch.ledger.to_json() == sim.ledger.to_json()
    assert branch.compare(sim)['identical']


def test_all_agent_reads_and_views_obey_one_fifo_capacity():
    sim = make(n_ticks=24, capacity=3).run()
    for agent in sim.agent_ids + ['Player']:
        assert len(sim.remembered(agent)) <= 3
        assert len(sim.private_view(agent)['experiences']) <= 3
        ids = {e.event_id for e in sim.remembered(agent)}
        assert set(sim.knowledge(agent)['grain.supply']['evidence_ids']) <= ids
    assert any(len(sim.experiences[a]) > 3 for a in sim.agent_ids)


def test_evicted_claim_cannot_be_recovered_from_archive_or_epistemic_oracle():
    sim = make(capacity=2).step(1)
    sim.inject_claim('Livia', 'disrupted')
    for n in range(3):
        sim.inject_claim('Marcus', 'available')  # Player's own receipts also have a real cap.
        event = sim._emit(sim.tick, 'state_change', 'forum', ('Livia',), 'local_episode', f'Local task {n}', scope='private')
        sim._receipt('Livia', event, action='episode', cash_delta=0, evidence_ids=[], description='A local task')
    assert any(e.kind == 'told' for e in sim.experiences['Livia'])
    assert sim.knowledge('Livia')['grain.supply']['value'] == 'unknown'
    before = sim.knowledge('Livia')
    # Mutating audit-only information cannot plant operational knowledge.
    sim.experiences['Livia'].append(Experience(0, 'observed', 'grain', 'supply', 'disrupted', None, 0, True, 0, 'audit only'))
    assert sim.knowledge('Livia') == before
    sim._gossip(sim.tick)
    assert not any(m['speaker'] == 'Livia' for m in sim.messages)


def test_gossip_uses_selected_bounded_backend_without_operational_ledger_lookup():
    sim = make(capacity=3).step(1)
    sim.inject_claim('Dama', 'disrupted')
    for agent in ('Dama', 'Livia', 'Marcus'):
        sim.state.agent_locations[agent] = 'forum'
    # A ledger getter trap demonstrates that gossip does not retrieve messages
    # or source depth from the full event archive.
    class ArchiveTrap:
        @property
        def events(self):
            raise AssertionError('gossip accessed the archive')
        def append(self, *args, **kwargs):
            return original.append(*args, **kwargs)
        def __len__(self):
            return len(original)
    original = sim.ledger
    sim.ledger = ArchiveTrap()
    sim._gossip(2)
    sim.ledger = original
    assert any(m['speaker'] == 'Dama' for m in sim.messages)


def test_retraction_removes_same_root_relays_and_tombstone_consumes_cap():
    sim = make(capacity=4).step(1)
    claim = sim.inject_claim('Livia', 'disrupted')
    root = claim['event_id']
    assert sim.knowledge('Livia')['grain.supply']['value'] == 'disrupted'
    sim.retract('Livia', root)
    assert sim.knowledge('Livia')['grain.supply']['value'] == 'unknown'
    assert any(e.kind == 'retracted' for e in sim.remembered('Livia'))
    assert len(sim.remembered('Livia')) <= 4
    for n in range(5):
        event = sim._emit(sim.tick, 'state_change', 'forum', ('Livia',), 'episode', f'task{n}', scope='private')
        sim._receipt('Livia', event, action='episode', cash_delta=0, evidence_ids=[])
    assert not any(e.kind == 'retracted' for e in sim.remembered('Livia'))
    assert not any(e.subject == 'grain' and e.predicate == 'supply' for e in effective_records(sim.remembered('Livia')))


def test_genuine_pre_history_observation_becomes_outdated_after_reversal():
    sim = make(n_ticks=16).step(7)
    delivered = next(e for e in sim.ledger.events if e.payload.get('category') == 'message_delivered'
                     and e.payload['speaker'] == 'Dama' and e.payload['listener'] == 'Livia'
                     and e.payload['as_of'] == 0)
    root = sim.ledger.events[delivered.payload['root_event']]
    assert root.payload['category'] == 'supply' and root.tick == 0
    assert root.payload['value'] == delivered.payload['value'] == 'available'
    assert 'Dama' in root.actors
    assert delivered.tick == 6 and sim.state.facts['grain.supply'] == 'disrupted'
    assert not any(e.payload.get('assessment') == 'contradicted' and
                   e.payload.get('root_event') == root.event_id for e in sim.ledger.events)


def test_paid_dated_inspection_distinguishes_truthful_outdated_and_false_reports():
    truthful = make(n_ticks=16).step(7)
    original = next(e for e in truthful.remembered('Dama') if e.kind == 'observed' and e.as_of == 0)
    truthful.inject_claim('Modestus', 'available', source='Dama', as_of=0, root_event=original.claimed_origin_event)
    truthful.inspect('Modestus'); truthful.step()
    assessments = [e.payload for e in truthful.ledger.events if e.payload.get('category') == 'relationship'
                   and e.payload.get('claim_as_of') == 0 and e.actors == ('Modestus',)]
    assert any(p['assessment'] == 'truthful_outdated' for p in assessments)
    assert truthful.state.trust[('Modestus', 'Dama')] >= .6
    false = make(n_ticks=8).step(1)
    report = false.inject_claim('Livia', 'disrupted')
    false.step(2)
    assessments = [e.payload for e in false.ledger.events if e.payload.get('claim_event') == report['event_id']]
    assert any(p.get('assessment') == 'contradicted' for p in assessments)
    assert false.state.trust[('Livia', 'Player')] < .35
    records = [e for e in false.ledger.events if e.payload.get('category') == 'inspection_record']
    assert records and records[0].payload['record_as_of'] == 0
    assert 'lookback eight' in records[0].payload['mechanism']


def test_repeated_inspections_do_not_repeatedly_punish_same_remembered_claim():
    sim = make(n_ticks=12, capacity=32).step(1)
    sim.inject_claim('Livia', 'disrupted'); sim.step(2)
    first = sim.state.trust[('Livia', 'Player')]
    sim.inspect('Livia'); sim.step()
    assert sim.state.trust[('Livia', 'Player')] == first


def test_unknown_statement_is_incomplete_not_a_false_claim():
    sim = make(n_ticks=8).step(1)
    report = sim.inject_claim('Livia', 'unknown')
    sim.step(2)
    assessments = [e.payload for e in sim.ledger.events if e.payload.get('claim_event') == report['event_id']]
    assert all(p.get('assessment') != 'contradicted' for p in assessments)
    assert sim.state.trust.get(('Livia', 'Player'), .6) >= .6


def test_caution_preference_materially_changes_policy_choice():
    sim = make().step(1)
    sim.inject_claim('Livia', 'disrupted')
    view = sim.private_view('Livia')
    policy = GenesisPolicy(sim.config)
    cautious = policy.decide_local(view, 0)
    view['preferences']['caution'] = .1
    bold = policy.decide_local(view, 0)
    assert cautious['action'] == 'verify' and bold['action'] == 'reserve'
    assert view['beliefs'] == sim.private_view('Livia')['beliefs']


def test_distinct_role_strategies_have_distinct_material_actions():
    sim = make().step(1)
    view = sim.private_view('Livia')
    view['beliefs']['grain.supply'].update(value='available', confidence=.6)
    view['inventory'] = 0
    policy = GenesisPolicy(sim.config)
    merchant = policy.decide_local(view, 0)
    baker_view = copy.deepcopy(view)
    baker_view['role'] = 'baker'; baker_view['preferences']['procure_early'] = True
    baker = policy.decide_local(baker_view, 0)
    trader_view = copy.deepcopy(view)
    trader_view['role'] = 'trader'; trader_view['preferences']['speculative_buffer'] = 2
    trader_view['quoted_price'] = 4
    trader = policy.decide_local(trader_view, 0)
    assert merchant['action'] == 'defer'
    assert baker['action'] == trader['action'] == 'reserve'
    assert sim.preferences['Dama']['share_unverified']
    assert sim.preferences['Flavia']['inspect_interval'] == 6


def test_player_inspection_has_same_cost_delay_and_no_free_current_truth():
    sim = make().step(1)
    cash = sim.player['cash']
    before = sim.knowledge('Player')
    event = sim.inspect()
    assert sim.player['cash'] == cash - INSPECTION_FEE
    assert sim.knowledge('Player') == before
    assert event['payload']['fee'] == 2
    sim.step()
    observed = [e for e in sim.remembered('Player') if e.subject == 'grain' and e.predicate == 'supply']
    assert observed and observed[-1].tick == 1
    assert sim.metrics()['player']['inspection_cost'] == 2


def test_false_player_claim_has_real_trust_access_and_bounded_explanation():
    sim = make(n_ticks=16).step(1)
    report = sim.inject_claim('Livia', 'disrupted')
    sim.step(2)
    view = sim.private_view('Livia')
    assert view['trust_player'] < .35 and not view['commercial_access']
    assert any('contradicted' in e['text'] for e in view['experiences'])
    assert any(e.payload.get('claim_event') == report['event_id'] for e in sim.ledger.events)
    before = digest(sim)
    with pytest.raises(ValueError, match='access refused'):
        sim.player_contract('Livia', 1, 7)
    assert digest(sim) == before


def test_player_trade_conserves_cash_and_inventory_and_contract_settles():
    sim = make(n_ticks=12).step(1)
    sim.player_trade('market', 2)
    cash = sim.economy.cash['Player'] + sim.economy.cash['Livia']
    inventory = sim.economy.inventory['Player'] + sim.economy.inventory['Livia']
    sim.player_trade('Livia', 1)
    assert sim.economy.cash['Player'] + sim.economy.cash['Livia'] == cash
    assert sim.economy.inventory['Player'] + sim.economy.inventory['Livia'] == inventory
    sim.player_contract('Livia', 1, 3)
    sim.step(3)
    contract = sim.economy.commitments['Player'][0]
    assert contract['status'] == 'fulfilled' and contract['fulfilled'] == 1
    economy = GenesisEconomy()
    for event in sim.ledger.events:
        economy.apply(event)
    assert asdict(economy) == asdict(sim.economy)


def test_zero_fill_order_has_no_inventory_or_cash_utility_reward():
    sim = make(n_ticks=8).step(1)
    # A genuine ledger transaction exhausts stock; no hidden direct mutation.
    sim._emit(sim.tick, 'state_change', 'forum', (), 'stock_export', 'Export remaining grain',
              market_stock_delta=-sim.economy.market_stock)
    before_cash, before_inventory = sim.economy.cash['Livia'], sim.economy.inventory['Livia']
    before_utility = next(r['net_asset_change'] for r in sim.metrics()['agents'] if r['agent'] == 'Livia')
    order = sim._purchase_quantity('Livia', 3, sim.tick)
    after_utility = next(r['net_asset_change'] for r in sim.metrics()['agents'] if r['agent'] == 'Livia')
    assert order.payload['quantity'] == 0
    assert sim.economy.cash['Livia'] == before_cash and sim.economy.inventory['Livia'] == before_inventory
    assert before_utility == after_utility
    assert sim.metrics()['regret'] is None


def test_asset_utility_uses_cash_and_inventory_once_and_all_orders_have_actual_fills():
    sim = make(n_ticks=24).run()
    metrics = sim.metrics()
    for row in metrics['agents'] + [metrics['player']]:
        assert row['net_asset_change'] == pytest.approx(row['cash_delta'] + 3 * row['inventory_delta'])
        assert 0 <= row['purchase_filled'] <= row['purchase_attempted']
    assert 0 <= metrics['delivery_fill_rate'] <= 1
    assert all('regret' not in d and 'loss' not in d for d in sim.decisions)
    assert all('local_recall_correct' in d and 'belief_current_correct' in d for d in sim.decisions)


def test_population_supply_control_and_seeded_order_have_declared_semantics():
    small = make(n_agents=8, n_ticks=1).run()
    large = make(n_agents=32, n_ticks=1).run()
    fixed = make(n_agents=32, n_ticks=1, supply_mode='fixed').run()
    arrivals = lambda s: sum(e.payload.get('market_stock_delta', 0) for e in s.ledger.events if e.payload.get('category') == 'supply')
    assert arrivals(large) >= 3.8 * arrivals(small)
    assert arrivals(fixed) == 22
    assert make(allocation='fixed')._order(0) == small.agent_ids
    rotating = make(allocation='rotating')
    assert rotating._order(0)[0] != rotating._order(2)[0]
    seeded = make()
    assert seeded._order(0) == make()._order(0)
    assert seeded._order(0) != seeded._order(2)


def test_player_snapshot_has_no_citizen_private_memory_or_truth():
    sim = make().step(8)
    view = sim.snapshot()
    assert view['world']['facts'] == {} and view['world']['supply'] == 'unknown'
    assert 'operator' not in view and view['decisions'] == []
    assert set(view['metrics']) == {'player'}
    for agent in view['agents']:
        assert not set(agent) & {'beliefs', 'experiences', 'cash', 'inventory', 'preferences', 'commitments'}
    operator = sim.snapshot(operator=True)
    assert operator['operator']['facts']['grain.supply'] == sim.state.facts['grain.supply']
    assert 'experiences' in operator['agents'][0]


def test_settlement_trace_links_executed_procurement_and_previous_account_checkpoint():
    sim = make(n_ticks=16).run()
    settlements = [e for e in sim.ledger.events if e.payload.get('category') == 'commitment_settled'
                   and e.payload.get('owner') == 'Livia']
    first, second = settlements
    assert first.payload['accounting_checkpoint'] == 0
    assert {0, first.event_id} <= set(second.payload['parents'])
    assert second.payload['accounting_checkpoint'] == first.event_id
    purchases = [e for e in sim.ledger.events if e.payload.get('category') == 'purchase'
                 and e.payload.get('owner') == 'Livia' and e.event_id < first.event_id]
    assert purchases and all(e.event_id in first.payload['inventory_dependency_events'] for e in purchases)
    ancestors = sim.trace(first.event_id)['ancestors']
    assert {'purchase', 'price', 'decision'} <= {e['category'] for e in ancestors}
    assert first.payload['inventory_before_settlement'] >= first.payload['quantity']
    assert 'fungible' in first.payload['inventory_allocation']
    assert 'not necessary or minimal causes' in first.payload['dependency_scope']
    for event in sim.ledger.events:
        assert event.event_id == sim.ledger.events.index(event)
        assert all(type(parent) is int and 0 <= parent < event.event_id for parent in event.payload['parents'])


def test_player_contract_settlement_trace_contains_agreement_and_inventory_acquisition():
    sim = make(n_ticks=12).step(1)
    purchase = sim.player_trade('market', 2)
    agreement = sim.player_contract('Livia', 1, 3)
    sim.step(3)
    settlement = next(e for e in sim.ledger.events if e.payload.get('category') == 'commitment_settled'
                      and e.payload.get('owner') == 'Player')
    assert {0, purchase['event_id'], agreement['event_id']} <= set(settlement.payload['parents'])
    assert settlement.payload['quantity'] == 1
    assert sum(settlement.payload['cash_delta'].values()) == 0
    assert sum(settlement.payload['inventory_delta'].values()) == 0
    assert 'no per-unit FIFO attribution' in settlement.payload['inventory_allocation']


@pytest.mark.parametrize('action', [
    {'kind': 'claim', 'recipient': 'Nobody', 'value': 'disrupted'},
    {'kind': 'claim', 'recipient': 'Livia', 'value': 'disrupted', 'as_of': 999},
    {'kind': 'trade', 'recipient': 'market', 'quantity': 999},
    {'kind': 'trade', 'recipient': 'Livia', 'quantity': True},
    {'kind': 'contract', 'recipient': 'Livia', 'quantity': 1, 'deadline': -1},
    {'kind': 'retract', 'recipient': 'Livia', 'root_event': 0},
    {'kind': 'move', 'location': 'moon'}, {'kind': 'world_fact', 'value': 'disrupted'},
])
def test_invalid_player_actions_do_not_mutate_ledger_state_or_memory(action):
    sim = make(n_ticks=16).step(1)
    before = digest(sim)
    with pytest.raises(ValueError):
        sim.apply_player_action(action)
    assert digest(sim) == before


@pytest.mark.parametrize('kwargs', [{'capacity': 0}, {'n_agents': 129}, {'n_ticks': True},
                                    {'family': 'rumour'}, {'allocation': 'random'}, {'supply_mode': 'oracle'}])
def test_invalid_genesis_configs_rejected(kwargs):
    with pytest.raises(ValueError):
        GenesisConfig(**kwargs)
