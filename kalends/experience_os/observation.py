"""Explicit free-disclosure boundary over unchanged canonical actions.

The request's accepted-prefix identity survives server restarts. Reconciliation
replays that prefix rather than inventing a second persistence format.
"""
from __future__ import annotations
import copy
from .runtime import ExperienceRuntime, digest

POMPEII = {'hear_dispute': 'Sabina', 'examine_receipt': 'Sabina', 'examine_tablet': 'Dama'}

class ParticipantOperationError(ValueError):
    def __init__(self, message, code, *, outcome='rejected'):
        super().__init__(message)
        self.code, self.outcome = code, outcome


def is_observation(adapter, action):
    if not isinstance(action, dict) or set(action) != {'action', 'recipient'}:
        return False
    kind, recipient = action.get('action'), action.get('recipient')
    if not isinstance(kind, str) or not isinstance(recipient, str):
        return False
    if adapter == 'pompeii':
        return POMPEII.get(kind) == recipient
    return adapter == 'commons' and kind == 'share' and recipient in {'team_a', 'team_b', 'team_c'}


def _resources(runtime):
    economy = runtime.world.economy
    return copy.deepcopy((runtime.minute, economy.cash, economy.inventory, economy.commitments))


def observation_trial(runtime, action):
    if not is_observation(runtime.spec.setting['adapter'], action):
        raise ParticipantOperationError('This choice needs a review before it can go ahead.', 'observation_not_permitted')
    if runtime.spec.setting['adapter'] == 'pompeii':
        runtime.world.require_near(action['recipient'])
        if not any(c.get('enabled', True) and c.get('action') == action for c in runtime.world.choices(action['recipient'])):
            raise ParticipantOperationError('That question is no longer offered. Reopen the conversation.', 'observation_unavailable')
    trial = object.__new__(type(runtime))
    trial.__dict__ = {**runtime.__dict__, 'world': copy.deepcopy(runtime.world), 'commands': list(runtime.commands), 'journal_path': None}
    receipt = trial._perform('action', copy.deepcopy(action))
    if _resources(trial) != _resources(runtime):
        raise ParticipantOperationError('This choice now has a cost or obligation. Review its terms first.', 'observation_not_free')
    return receipt


def observe(runtime, action, expected_revision, expected_state_hash):
    if not is_observation(runtime.spec.setting['adapter'], action):
        raise ParticipantOperationError('This choice needs a review before it can go ahead.', 'observation_not_permitted')
    if type(expected_revision) is not int or expected_revision < 0 or not isinstance(expected_state_hash, str) or len(expected_state_hash) != 64:
        raise ParticipantOperationError('The question lost its saved starting point. Reload the conversation.', 'observation_invalid_identity')
    identity = digest({'life': runtime.spec.id, 'revision': expected_revision, 'state_hash': expected_state_hash, 'action': action})
    if expected_revision < len(runtime.commands):
        previous = runtime.commands[expected_revision]
        if previous['operation'] == 'action' and previous['data'] == action:
            prefix = ExperienceRuntime(runtime.spec, retention=runtime.retention)
            for command in runtime.commands[:expected_revision]:
                prefix._perform(command['operation'], copy.deepcopy(command['data']))
                prefix.commands.append(copy.deepcopy(command))
            if prefix.state_hash() == expected_state_hash:
                receipt = next((e for e in runtime.events() if e['event_id'] == previous['receipt_id']), None)
                return {'outcome': 'already_accepted', 'observation_id': identity, 'command_index': expected_revision,
                        'accepted_revision': expected_revision + 1, 'receipt': receipt}
    if expected_revision != len(runtime.commands) or expected_state_hash != runtime.state_hash():
        raise ParticipantOperationError('The situation changed. Reopen the conversation before asking again.', 'observation_stale')
    observation_trial(runtime, action)
    result = runtime.commit('action', action)
    return {**result, 'outcome': 'accepted', 'observation_id': identity, 'accepted_revision': len(runtime.commands)}
