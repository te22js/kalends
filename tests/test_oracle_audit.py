"""Adversarial audit of the epistemic oracle itself (see brief §9).

The benchmark's validity rests on this object, so every semantically tricky
case gets an explicit test that DOCUMENTS the intended semantics. Where a rule
is a modeling choice rather than a necessity, the test says so.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalends.epistemic import TRUST_THRESHOLD, EpistemicState
from kalends.propositions import Proposition, Provenance

P = Proposition("gate", "status")


def _eps():
    return EpistemicState("A")


def test_hearsay_after_direct_observation_older_info_rejected():
    eps = _eps()
    eps.record_observation(10, P, "open", 1)
    eps.record_told(12, P, "closed", 2, "B", claimed_as_of=8,
                    claimed_chain=None, trust_in_speaker=0.9)
    assert eps.belief(P).value == "open"        # my observation is fresher
    assert eps.belief(P).kind == "observed"


def test_hearsay_after_observation_with_fresher_info_wins():
    """MODELING CHOICE: trusted hearsay carrying strictly fresher information
    (later as_of) supersedes an older direct observation. The world may have
    changed since I looked; a trusted witness of the change updates me."""
    eps = _eps()
    eps.record_observation(10, P, "open", 1)
    root = Provenance(kind="observed", event_id=5)
    eps.record_told(20, P, "closed", 6, "B", claimed_as_of=15,
                    claimed_chain=Provenance(kind="observed", event_id=5),
                    trust_in_speaker=0.9)
    assert eps.belief(P).value == "closed"
    assert eps.belief(P).kind == "told"


def test_direct_observation_after_hearsay_wins():
    eps = _eps()
    eps.record_told(5, P, "closed", 1, "B", claimed_as_of=4,
                    claimed_chain=None, trust_in_speaker=0.9)
    eps.record_observation(10, P, "open", 2)
    assert eps.belief(P).value == "open"


def test_same_tick_observations_later_event_wins():
    """Simultaneous observations (same tick): ledger order breaks the tie —
    the later event id is defined as the later micro-instant."""
    eps = _eps()
    eps.record_observation(10, P, "open", 1)
    eps.record_observation(10, P, "closed", 2)
    assert eps.belief(P).value == "closed"


def test_gossip_echo_cannot_ping_pong():
    """A tells B; B echoes the same-vintage info back. Strict as_of freshness
    means the echo is rejected — belief flip-flop through loops is impossible."""
    eps = _eps()
    eps.record_observation(10, P, "open", 1)
    eps.record_told(12, P, "open", 2, "B", claimed_as_of=10,
                    claimed_chain=None, trust_in_speaker=0.9)
    hist = eps.belief_history(P)
    assert hist[1].accepted is False
    assert eps.belief(P).kind == "observed"


def test_retraction_back_to_original_value_still_counts_as_superseded():
    eps = _eps()
    eps.record_observation(5, P, "open", 1)
    eps.record_observation(10, P, "closed", 2)
    eps.record_observation(15, P, "open", 3)
    assert eps.belief(P).value == "open"
    assert eps.was_superseded(P)     # history open->closed->open changed twice


def test_trust_exactly_at_threshold_is_accepted():
    eps = _eps()
    eps.record_told(5, P, "open", 1, "B", claimed_as_of=4,
                    claimed_chain=None, trust_in_speaker=TRUST_THRESHOLD)
    assert eps.belief(P) is not None


def test_distrusted_claim_becomes_believable_only_via_trusted_source():
    """Heard-vs-believed distinction (brief §9): a distrusted claim is in
    memory ('heard') but not believed; the same content later from a trusted
    source creates the belief."""
    eps = _eps()
    eps.record_told(5, P, "open", 1, "Rufus", claimed_as_of=4,
                    claimed_chain=None, trust_in_speaker=0.1)
    assert eps.has_heard_of(P) and eps.belief(P) is None
    eps.record_told(8, P, "open", 2, "Livia", claimed_as_of=4,
                    claimed_chain=None, trust_in_speaker=0.9)
    assert eps.belief(P).value == "open"
    assert eps.belief(P).source_agent == "Livia"


def test_rejected_exposures_do_not_count_as_evidence_lines():
    eps = _eps()
    eps.record_told(5, P, "open", 1, "Rufus", claimed_as_of=4,
                    claimed_chain=Provenance(kind="observed", event_id=0),
                    trust_in_speaker=0.1)
    assert eps.independent_origins(P) == 0
    eps.record_observation(10, P, "open", 2)
    # The distrusted report shares no signature with my observation; only my
    # own accepted line counts.
    assert eps.independent_origins(P) == 1


def test_unterminated_hearsay_chain_root_is_told():
    prov = Provenance(kind="told", event_id=9, source_agent="B", upstream=None)
    assert prov.root_kind() == "told"
    kind, _, _ = prov.root_signature("A")
    assert kind == "told"


def test_repeated_identical_tells_from_same_source_do_not_inflate_origins():
    eps = _eps()
    root = Provenance(kind="observed", event_id=3)
    for i in range(5):
        eps.record_told(5 + i, P, "open", 10 + i, "B", claimed_as_of=4,
                        claimed_chain=root, trust_in_speaker=0.9)
    assert eps.independent_origins(P) == 1
