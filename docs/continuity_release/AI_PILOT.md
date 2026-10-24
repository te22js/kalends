# Optional bounded character pilot

The character pilot is disabled by default. This release preparation authorizes
no real endpoint, paid model call, credential read, or live configuration. Its
verification uses deterministic mocks and the existing injected transport
fixtures only. No model quality or live character experience has been measured.

The pilot reuses `kalends_rebirth.ai.Cognition`, its existing
`OpenAIResponsesAdapter`, and the bounded evidence validation helpers in
`kalends.experience_os.providers`. It adds no transport, credential loader,
archive lookup, memory writer, world executor, or automatic action confirmation.

## Inspect or demonstrate without network

```sh
python3 -m kalends.continuity_release.pilot --status
python3 -m kalends.continuity_release.pilot --offline-fixture
python3 -m pytest -q tests/test_continuity_pilot.py
```

`--status` shows redacted limits and the reason calls are disabled.
`--offline-fixture` uses a fixed mock configuration and explicitly reports
`kind: mock`. It is not a model result. `--config path.json` accepts explicit
`PilotConfig` fields for status inspection only; the CLI never constructs a live
adapter or reads environment variables or credentials. A safe example is:

```json
{"enabled": false, "max_turns": 3, "max_context_bytes": 8000,
 "max_output_tokens": 256, "max_output_bytes": 2400,
 "timeout_seconds": 2.0}
```

## Host API and evidence boundary

```python
pilot = CharacterPilot(PilotConfig())  # remains disabled
result = pilot.interact(host_scope, local_text=None)
status = pilot.status()
```

`host_scope` has exactly these keys:

```json
{
  "actor": "Sabina",
  "viewer": "Player",
  "minute": 10,
  "evidence": [{"event_id": 4, "text": "The receipt records three coins.",
                "at": 5, "kind": "direct"}],
  "allowed_event_ids": [4],
  "retained_event_ids": [4],
  "admitted_event_ids": [4],
  "options": [{"id": "inspect", "label": "Review the receipt",
               "evidence_ids": [4], "enabled": true}]
}
```

The host must derive these permission sets from its actual current visibility,
retention, admission and disclosure rules. Every supplied record must be in all
three sets. Extra permission identities do not retrieve records: the model sees
only the supplied rows and the permission sets are reduced to those rows. Future
evidence, duplicate identities, unknown fields, private archive/world dumps and
unsupported record kinds fail before inference. Record kinds are `event`,
`direct`, `testimony`, or `inference`; `at` and `kind` are optional. Disabled
options are removed before inference. Each option's support must already be
present in the supplied evidence.

This boundary cannot authenticate a host that lies about permissions or supplies
an unsupported factual clause as reviewed evidence. That responsibility remains
with the host. A supplied testimony or inference remains literal testimony or
inference; the pilot does not independently establish its truth.

`local_text` accepts at most 2,000 UTF-8 bytes for local UI compatibility. It is
not interpreted, sent to a provider, included in hashes, cached, saved, or
included in receipts/status. The pilot does not use it to infer an intention. A
host may offer a separate explicit option selector; it must preserve this local
free-text exclusion and the existing action review boundary.

### Concrete existing-runtime caller, offline only

This runnable host-side example compiles the existing Shared Observatory in
memory. It uses the systems team's retained episode text and further restricts
it to observations already admitted to both that NPC and the participant. It
does not initiate disclosure of private NPC reports. No world archive, operator
projection, `runtime.events()`, semantic source lookup, or retained-ID lookup is
used to recover text. A compact semantic record without its literal episode is
omitted. The snapshot is bounded by the existing mind's capacity, and the final
provider scope contains at most eight literal clauses.

```python
from kalends.experience_os.compiler import ExperienceCompilerV1, SPEC_DIR
from kalends.continuity_release.pilot import CharacterPilot, PilotConfig, FIXTURE_ENDPOINT
from kalends_rebirth.ai import Cognition, MockAdapter

runtime = ExperienceCompilerV1().compile(SPEC_DIR / "shared_observatory.json")
actor, viewer = "team_b", "Player"
with runtime.lock:
    mind = runtime.minds[actor]
    allowed = (set(mind.retained_event_ids()) & runtime.visible_ids(actor)
               & runtime.visible_ids(viewer))
    rows = [row for row in mind.to_dict()["base"]["episodes"]
            if row["event_id"] in allowed and row.get("accepted") is True
            and row["observed_at"] <= runtime.minute and len(row["text"]) <= 500][-8:]
    kinds = {"observed": "direct", "told": "testimony", "episodic": "event"}
    evidence = [{"event_id": row["event_id"], "text": row["text"],
                 "at": row["observed_at"], "kind": kinds[row["kind"]]} for row in rows]
    ids = [row["event_id"] for row in evidence]
    host_scope = {"actor": actor, "viewer": viewer, "minute": runtime.minute,
        "evidence": evidence, "allowed_event_ids": ids,
        "retained_event_ids": ids, "admitted_event_ids": ids, "options": []}

config = PilotConfig(enabled=True, authorized_endpoint=FIXTURE_ENDPOINT,
                     session_cap_usd=0.01, fixture_mode=True)
adapter = MockAdapter({"phrase_id": "careful", "event_ids": ids[:1],
                       "choice_id": "wait", "evidence_ids": []})
result = CharacterPilot(config, cognition=Cognition(adapter)).interact(host_scope)
assert result["output"]["action_suggestion"]["status"] == "OFFERED"
assert adapter.external is False
```

The corresponding integration test verifies that private retained NPC identities
do exist, are excluded from the provider scope, and that the world hash and
accepted commands remain unchanged. This example offers only `wait`; adding a
real option requires the existing host precondition/review protocol. It applies
to the existing Commons adapter, whose `visible_ids(viewer)` handles that viewer.
The Pompeii implementation's similarly named method is participant-oriented and
must not be assumed to establish an arbitrary NPC's admission permission. No
public product API or enable switch was added for this pilot.

## Character phrasing and factual audit

The model can return only `phrase_id`, up to three `event_ids`, one offered
`choice_id` (or `wait`), and that option's exact `evidence_ids`. It cannot return
prose, variables, action payloads, memory edits, completed history, or world
patches. The three reviewed phrase IDs are `plain`, `careful`, and `direct`;
their fixed prefixes contain no new world fact.

The host constructs the display text from that fixed prefix and literal supplied
evidence text. Every factual clause has `support_ids` and an
`audit: literal_host_evidence` marker, plus the supplied `kind` and optional
observation `at`. Testimony and inference get explicit fixed attribution prefixes
in the displayed text, so their source type is not flattened into a direct
observation. The timestamp records observation/receipt time, not an independently
verified fact date. It rejects any unknown evidence identity,
extra output field, unsupported option, incorrect support set, or oversized
rendering. There is no permissive semantic claim classifier that can accept a
new factual paraphrase. Provider rejection produces the fixed empty/wait fallback
and keeps any known charge in the receipt.

`output.action_suggestion.status` is always `OFFERED`.
`review_required`, `confirm_required`, and
`current_state_revalidation_required` are true. The result contains an option
identity and a literal host label, with zero world effects. Before any separate
command is committed, the host must show the current action for review, obtain
explicit confirmation, and revalidate it against current world state. Calling
`interact` has no execution path.

## Gates and hard limits

These are a **bounded paid-live limit gate, not production authorization**.
There is no user authentication, deployment approval, distributed quota, durable
cross-process budget, or provider billing guarantee in this experiment.

Future live use would require a separately authorized host to supply all of:

1. `PilotConfig.enabled = true`.
2. The exact authorized endpoint `https://api.openai.com/v1/responses`, matching
   the existing transport.
3. A finite positive numeric `session_cap_usd`.
4. A dedicated existing explicitly enabled `OpenAIResponsesAdapter`, with its
   own key/model/current price assumptions already configured by that host and
   its existing total budget no larger than the session cap.

The pilot does not read that key or discover configuration from the environment.
The existing adapter performs its credential/model check and conservative
preflight cost reservation. Unpriced `LocalJSONAdapter` endpoints are rejected:
their unknown dollar costs cannot honestly enforce this pilot's numeric cap.
Fixture mode requires an injected transport for the Responses adapter, or a
mock/offline adapter with the fixture endpoint `fixture://continuity-character`.
It cannot fall through to the real transport.

| Limit | Default | Maximum |
| --- | ---: | ---: |
| Turns per pilot instance, including failed ingress | 3 | 5 |
| Concurrent requests | 1 | 1 |
| Serialized context bytes | 8,000 | 12,000 |
| Evidence clauses / offered options | 8 / 8 | 8 / 8 |
| Literal clause length | 500 characters | 500 characters |
| Selected factual clauses | 3 | 3 |
| Requested provider output tokens | 256 | 512 |
| Serialized rendered output bytes | 2,400 | 4,000 |
| Request timeout seconds | 2 | 5 |
| Automatic retries / cached proposals | 0 / 0 | 0 / 0 |
| Pilot receipt history | 16 | 16 |

An in-flight concurrency rejection does not consume another turn. Once the turn
limit is exhausted, further requests are rejected without provider work. Each
pilot must own one dedicated adapter; hosts must not create fresh instances to
bypass the session boundary or share an adapter with unrelated work.

Timeouts and uncertain charges halt the pilot. A later turn cannot retry them,
even if the original worker eventually finishes. The existing adapter retains
the reserved estimated cost on an ambiguous failure. Known usage is accounted
even when a schema/claim check rejects the result. A known refusal/incomplete
response is attempted once. A provider reporting output beyond the token limit
is rejected and halts the session; any reported budget overrun also halts it.
The existing request reservation prevents knowingly overspending the configured
estimate, but a provider's eventual invoice is outside this local gate.

## Receipts and verification

Invalid host scope or a hard limit returns `output: null` and a `REJECTED`
receipt with a fixed code; it does not echo rejected input. Disabled inference
returns the reviewed empty/wait display and a `DISABLED` receipt with zero
attempts. Accepted/rejected model selections report `ACCEPTED`/`FALLBACK`, usage,
known estimated cost, unknown-cost count, errors, and a scoped context hash.
Receipts contain neither raw local prose nor provider-generated prose.

Offline tests cover the enable/endpoint/cap gates, UTF-8 output/context limits,
turn and concurrency limits, retained/admitted evidence checks, private/future
evidence rejection, unsupported claim/action attacks, local text exclusion,
fixture-only transport, exact action support, known failure accounting,
uncertain-charge reserve retention and terminal halt, and the status/fixture CLI.
They establish these local contracts only; they do not establish production
security, historical truth, learning benefit, or live-model quality.
