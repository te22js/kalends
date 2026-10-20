import copy
import hashlib
import json
import random

import pytest

from kalends.events import Ledger
from kalends.genesis.simulation import GenesisEconomy
from kalends_rebirth.immutable import PersistentLedger, SealedWorldEvent


def test_nested_history_is_detached_from_input_and_rejects_mutation():
    raw={"nested":{"list":[{"value":3}]},"position":(4,5)}
    ledger=PersistentLedger();event=ledger.append(0,"state_change","street",("Player",),raw)
    digest=ledger.content_hash()
    raw["nested"]["list"][0]["value"]=99
    assert event.payload["nested"]["list"][0]["value"]==3
    with pytest.raises(TypeError): event.payload["nested"]["list"][0]["value"]=4
    with pytest.raises(TypeError): event.payload["nested"]["list"][0]=4
    with pytest.raises(AttributeError): event.payload["nested"]["list"].append(4)
    with pytest.raises(TypeError): event.payload._data={"replacement":3}
    assert ledger.content_hash()==digest


def test_exports_are_detached_and_preserve_list_tuple_shapes():
    ledger=PersistentLedger();event=ledger.append(1,"move","street",("Player",),{"path":[(1,2),(3,4)],"flags":{"x":[1,2]}})
    result=event.to_dict();assert result["payload"]["path"]==[(1,2),(3,4)]
    result["payload"]["flags"]["x"][0]=9
    assert event.payload["flags"]["x"][0]==1
    exported=ledger.to_json();exported[0]["payload"]["path"].append((7,8))
    assert len(event.payload["path"])==2


def test_deepcopy_shares_only_sealed_events_and_isolates_appends_and_hashes():
    first=PersistentLedger();first.append(0,"incident","street",("Player",),{"nested":[{"a":1}]})
    clone=copy.deepcopy(first)
    assert clone.events[0] is first.events[0]
    original_hash=first.content_hash();clone.append(2,"state_change","street",("Player",),{"new":True})
    assert len(first)==1 and len(clone)==2
    assert first.content_hash()==original_hash and clone.content_hash()!=original_hash
    first.append(3,"state_change","street",("Felix",),{"other":True})
    assert first.events[-1].actors==("Felix",) and clone.events[-1].actors==("Player",)


def test_incremental_hash_matches_original_full_json_after_each_random_append():
    rng=random.Random(72341);legacy=Ledger();sealed=PersistentLedger()
    assert sealed.content_hash()==legacy.content_hash()==hashlib.sha256(b"[]").hexdigest()
    for i in range(100):
        payload={"unicode":"Aelia · café", "n":rng.random(), "position":(rng.randrange(10),rng.randrange(10)),
                 "rows":[{"q":rng.randrange(9),"ok":bool(i%2)},None],"negative":-i}
        actors=("Player","Felix") if i%2 else ("Marcus",)
        legacy.append(i,"state_change","street",actors,payload,"private")
        sealed.append(i,"state_change","street",actors,payload,"private")
        assert sealed.to_json()==legacy.to_json()
        assert sealed.content_hash()==legacy.content_hash()


def test_conversion_preserves_existing_history_and_candidate_isolation():
    legacy=Ledger();legacy.append(0,"state_change","street",(),{"initial":{"coins":7}})
    sealed=PersistentLedger.from_ledger(legacy)
    assert sealed.content_hash()==legacy.content_hash()
    legacy.events[0].payload["initial"]["coins"]=999
    assert sealed.events[0].payload["initial"]["coins"]==7
    second=PersistentLedger.from_ledger(sealed);second.append(2,"incident","street",(),{})
    assert len(sealed)==1 and len(second)==2


def test_legacy_economy_receives_mutable_owned_copy_of_new_commitment():
    economy=GenesisEconomy();ledger=PersistentLedger()
    initial=ledger.append(0,"state_change","street",(),{"category":"city_initialized","cash":{"Player":6},"inventory":{"Player":0},"commitments":{"Player":[]}})
    economy.apply(initial)
    event=ledger.append(1,"state_change","street",("Player",),{"owner":"Player","new_commitment":{"id":"x","status":"open","quantity":4}})
    economy.apply(event)
    economy.commitments["Player"][0]["status"]="fulfilled"
    assert event.payload["new_commitment"]["status"]=="open"
    assert economy.commitments["Player"][0]["status"]=="fulfilled"


def test_invalid_payload_does_not_partly_change_hash_or_history():
    ledger=PersistentLedger();before=ledger.content_hash()
    for payload in ({"x":float('nan')},{"x":set()},{1:"bad key"}):
        with pytest.raises(TypeError): ledger.append(0,"incident","street",(),payload)
        assert len(ledger)==0 and ledger.content_hash()==before
    with pytest.raises(ValueError): ledger.append(0,"wrong-type","street",(),{})
    with pytest.raises(TypeError): ledger.append(0,"incident","street",(["Player"],),{})
    with pytest.raises(TypeError): ledger.append(0,"incident",["street"],(),{})
    assert len(ledger)==0
