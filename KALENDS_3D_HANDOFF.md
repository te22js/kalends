# KALENDS — Project Immersion handoff

21 October 2026 · local PlayCanvas vertical slice · branch `codex/project-immersion`

The new client is playable against the existing authoritative Kalends server. It contains a textured 3D district, seven skinned animated people, a usable bakery interior, keyboard and destination movement, compact conversations, reviewed actions, real economic consequences and saved history. It is a functioning prototype with a small coherent scene; it is not a finished game or a surveyed reconstruction of Pompeii.

## Run it

From the repository root:

```sh
cd kalends_3d
npm ci
npm run build
cd ..
./scripts/start_immersion.sh --port 8790
```

- [Play the 3D client](http://127.0.0.1:8790/immersion/).
- [Open the retained illustrated client and World Lab](http://127.0.0.1:8790/).
- Check or stop only the managed local process with `./scripts/start_immersion.sh --status` or `./scripts/start_immersion.sh --stop`.
- The launcher uses Python 3.10 or newer, preferring the bundled Python runtime. Set `KALENDS_PYTHON` if another compatible interpreter is needed. Validation used Python 3.12.14 and Node 24.11.1.
- `kalends_3d/dist/` and `node_modules/` are generated and ignored. Build before launching; plain Vite development mode alone does not supply the Python API.

The default journal is `.kalends/immersion_session.json`, separate from the user's original Rebirth life. The delivered service was restarted with a fresh life: six coins, 08:00, and the unresolved fountain situation. It subsequently received 254 movement commands from an open client; the latest verified view resumes at 09:03 with six coins and the dispute unresolved. That progress is retained. The exercised QA life is preserved at `.kalends/immersion_qa_verified.json` and `results/immersion/qa_final_session.json`; the independently replayed earlier checkpoint remains in `results/immersion/qa_verified_session.json`. See the [archive record](results/immersion/qa_archive.json). Both clients on port 8790 share whichever journal that service runs. Use one gameplay controller per journal: the presentation does not continuously synchronize another tab's actions, so reload after playing through another client. Server proximity/resource checks still reject stale requests. To begin another life, supply an unused `--journal` path and a free `--port`; the launcher guards against starting two managed writers for one journal.

The launcher forces the offline provider and disables external inference. No paid editor account, asset purchase, hosted deployment or live model budget is required. Asset and inference spending for this sprint was $0.

## Play and controls

Enter or continue as Aelia. On a new life, the fountain dispute is the first meaningful situation: find Sabina, hear the account, review a choice and confirm it. The tested market route pays a real three-coin carrying charge and resolves the cart through the simulator.

| Control | Behavior |
| --- | --- |
| WASD / arrows | Camera-relative walking; a tap also produces a short step |
| Click ground | Choose a server-validated destination |
| Click a name/person | Approach their current location, then talk when actually nearby |
| E | Contextual talk, entrance, exit or stop |
| Escape | Stop remaining uncommitted navigation or leave a conversation, including from its speech field |
| X / visible street button | Leave an interior |
| Shift | Faster visual locomotion; no extra economic or simulation authority |
| J | Journal with witnessed events, people, places and dealings |
| Right drag / [ / ] | Adjust the limited three-quarter camera arc |
| Wheel / F / follow button | Zoom / return to following Aelia |
| Live / Wait 30m / A day later | Explicit world-time progression |

An accepted movement step can finish after cancellation; cancelling does not erase its saved position or time cost. Walking, menus, conversations, visibility loss and explicit time controls pause Live progression. Use Settings for three graphics tiers, reduced motion and optional synthesized ambient sound.

## Engine decision and implementation

PlayCanvas 2.23.3 is pinned through npm, with Vite 8.3.5 and a committed lockfile. The local spike demonstrated a textured GLB, rigged animated characters, keyboard and destination navigation, following camera and actual backend actions. That met the preferred engine choice without a substantial blocker. Babylon's code-first animation documentation was considered; no head-to-head engine performance claim is made.

Primary references: [standalone PlayCanvas](https://developer.playcanvas.com/user-manual/engine/standalone/), [AnimComponent](https://api.playcanvas.com/engine/classes/AnimComponent.html), [CameraFrame](https://api.playcanvas.com/engine/classes/CameraFrame.html), [Babylon animation](https://doc.babylonjs.com/features/featuresDeepDive/animation/animation_introduction/).

```mermaid
flowchart LR
  A[Authoritative Python Session] -->|Public snapshot and receipt| B[KalendsBridge]
  B --> C[3D actors, animation and UI]
  C -->|Player intent| D[Existing route and portal navigation]
  D -->|Short move or reviewed action| B
  B -->|Validated API request| A
```

- `kalends_3d/bridge.js` projects an explicit public field allowlist, validates coordinates, rejects operator snapshots and normalizes a shared World Lab session back to game mode without replaying a transaction.
- The bridge uses existing state, context, proposal, action, route, move and time APIs. Only Python changes cash, goods, promises, memories or history. Rendering frames never advance consequential state.
- Mutations are single-flight. Duplicate in-flight confirmations share the same promise; stale conversations/proposals are rejected. The renderer submits server-issued proposal/interpretation IDs rather than invented action effects.
- `src/main.js` handles controls, contextual prompts, dialogue review, journal, settings, explicit time and local diagnostics. Advanced memory/causal inspection remains in the legacy World Lab.
- `src/renderer.js` interpolates accepted paths and selects animation from displayed movement, reported activities or an actual conversation. Public location, displayed floor and server proximity must all agree before talking across a doorway.
- Coordinates are meters, Y up: `sceneX=(simX-800)*0.02`, `sceneZ=(simY-415)*0.02`; normalized adults are about 1.7 m tall. See the [technical art guide](kalends_3d/ART_GUIDE.md).

Navigation deliberately retains the tested authoritative floor/visibility-graph and entrance/portal system. It is not Recast, a physics engine, dynamic NPC collision or arbitrary furniture collision. The 3D scenery respects the existing clear walkable floors; decorative props do not silently create server obstacles or economic stock.

The only existing backend source changed is `kalends_rebirth/server.py`: contained static mounts for `/immersion/` and `/immersion-assets/`, correct binary/text response handling and MIME types. Legacy routes and the simulator/cognition/research modules remain in place. CSP and loopback protections remain; runtime models and materials are local.

## Scene, characters and art

The original authored district contains Roman-inspired street frontages, paved lanes, modeled terracotta tiles, masonry, columns, pottery, shutters, canopy cloth, a real oven recess and four mapped rooms. The bakery is the fully walked and conversed interior. Entering a room swaps its roof/walls for authored cutaway geometry; the camera arc is limited to keep that view readable.

The market cart has six distinct sack meshes while the authoritative story is unresolved/committed. Its cargo disappears on actual resolution. The cart's recessed presentation position is disclosed in the art guide; it is not a new authoritative cart entity. Nearby shutters provide inexpensive visual ambience without inventing consequential activity.

- Runtime bodies, skeletons, weights, hair and motion come from the free Quaternius Universal Base Characters and Universal Animation Library, individually documented as CC0.
- Two runtime GLBs provide nine real source clips mapped to idle, walk, jog, speech and contextual interaction. Cross-fades and smooth turning replace static positional markers. NPC work poses depend on reported activity; a generic animation is not a Roman baking simulation.
- Project-authored pleated tunics, belts, body masking beneath clothing and individual cloth/skin palettes adapt those professional bases. Original vendor sources remain preserved.
- Twelve actual Poly Haven diffuse/normal/ARM maps provide stone, plaster, terracotta and wood. PBR, warm sun/fill, shadows, ACES grading, restrained bloom and optional SSAO form the presentation pipeline.
- The earlier KayKit prototypes and three optional Quaternius foliage GLBs remain as source/fallback assets. They are not the active character set or claimed runtime foliage.
- Audio is optional local synthesized wind, steps and receipt feedback; no downloaded voice or music pack was used. Listening quality has not been independently evaluated.

See [asset licenses](kalends_3d/ASSET_LICENSES.md), [full provenance/hashes](kalends_3d/ASSET_PROVENANCE.json) and [environment manifest](kalends_3d/assets/environment/scene_manifest.json). The inventory contains 52 local files, 49,265,201 bytes, including preserved sources and unused alternatives—not the runtime download size.

The final environment is 17,246,388 bytes, 126,608 triangles and 66 nodes. Its 218 stored primitive batches include mutually exclusive wall alternatives; these are not GPU draw calls. Two humans and three optional foliage models have zero Khronos errors. The environment also has zero errors, with 178 documented generated-tangent warnings; PlayCanvas generates those tangents during import. Ninety sampled CPU-skinned character poses pass finite transform/weight checks. These validators do not certify facial quality, garment contact in every pose, foot sliding or enjoyment.

## Verified gameplay and persistence

The actual browser walkthrough entered the district, approached Sabina, heard her account, confirmed the market choice, saw the cart resolve, entered the bakery, spoke with Felix, bought one real flour unit, used free speech, exited, advanced 30 minutes and reloaded.

The preserved [QA checkpoint](results/immersion/qa_verified_session.json) has 31 commands: 26 moves, four actions and one time advance. It contains exactly one market-support action, one resolution and one purchase of one flour from Felix. At 09:00 the player has one coin and one flour. Two independent restores produce identical full fidelity state and the saved ledger hash. Later capture movement may advance the live QA journal; the immutable checkpoint remains identified by its hash in the [replay report](results/immersion/qa_replay.json).

The original `.kalends/rebirth_session.json` remains at SHA256 `118e303c163e8b79cb9d24a310387bd97acaab1fe4080ff7f24e031ce30e25e2`: 470 commands, world minute 689. Its older exact backup is also retained at SHA256 `5f6ff85810e63884868a3586a7ccd72131ec9465e0a84342001886dfad0501e2`; all 181 older commands remain its prefix. The newer original life predates this Immersion brief, so it is not described as byte-identical to that older backup. No original save was reset or restored over the current life.

## Tests, review and defects fixed

| Evidence | Result and scope |
| --- | --- |
| [Full Python log](results/immersion/validation_python.txt) | 692 passed, including prior save/replay/research coverage and new actual Node bridge → HTTP → Session checks |
| [Final frontend log](results/immersion/validation_frontend_final.txt) | 98 passed; includes existing checks plus bridge, Live, renderer and measurements regressions |
| [Native browser regression](results/immersion/browser_regression.json) | 10 visible UI checkpoints: resources, room arrival, conversation, focused-input Escape, exit, keyboard movement, unchanged resources and reload |
| [Browser test source](tests/browser/immersion.cua.mjs) | Reproducible documented CUA locators, starting from the preserved market-resolved one-coin/one-flour QA street checkpoint |
| [Independent bridge review](results/immersion/bridge_review.json) / [renderer review](results/immersion/adversarial_review.json) | Separate technical review with source checkpoint hashes and explicit limits |

Automated coverage includes loading/static MIME and route containment, state projection, unauthorized operator payload exclusion, rejected moves/actions, camera smoothing, displayed portal proximity, single-flight and duplicate confirmation, cancellation, stale conversations and exact resume. Numeric asset validation complements actual native loading; it does not replace it.

Native and independent review exposed defects that were corrected: invalid native fetch binding, a position setter mismatch, early conversations across room boundaries, camera distance snapping, roof/sign/front-wall occlusion, tunic body intersections, stale Live timers and frozen diagnostics cancelling a route after an already accepted move. The frozen-trace guard has two regression tests and a passing native doorway/exit walkthrough. The reviews describe their earlier checkpoints rather than pretending every later UI edit was independently re-audited.

Core checkpoint: `7880f9d` (`Build local PlayCanvas district with authoritative Kalends bridge`). The following release commit contains the diagnostics correction, recoverable recording, choice readability, browser evidence and this handoff; consult `git log -2` for its exact identity.

## Performance and demonstration

The [performance report](results/immersion/PERFORMANCE.md) links all raw traces and measurement definitions. On the actual Apple M2 / 8 GiB / Chromium 155 / WebGL2 reference, with a normal 1280×720 CSS viewport and balanced 1920×1080 backing canvas:

| Setting | Intervals | Mean frame interval | p95 |
| --- | ---: | ---: | ---: |
| Balanced | 3,062 | 16.667 ms | 18.1 ms |
| Low | 1,048 | 16.699 ms | 17.9 ms |
| High | 1,921 | 16.666 ms | 17.6 ms |

The balanced window lasted about 51 seconds and included five completed idle taps: mean input-to-matching-accepted-player-draw submission was 38.18 ms, p95 48.22 ms. A cached localhost reload reached ready at 443.5 ms and first ready draw submission at 571.8 ms; this is not cold network loading. Unequal mostly stationary windows do not establish a quality ranking or universal 60 FPS. The endpoint is JavaScript draw submission, not GPU completion, browser composition or physical display latency. Cold cache, sustained thermal behavior, mobile and broader hardware remain unmeasured.

The later comparison measured legacy mean/p95 33.129/34.3 ms and 3D balanced 33.256/34.4 ms. Both ran at roughly 30 Hz after the interruption, unlike the earlier 60 Hz windows. The report preserves the changed cadence, unequal windows, slightly different positions and small input samples. No cause for the cadence change or renderer speedup is inferred.

| Artifact | What it demonstrates |
| --- | --- |
| [Bakery cutaway](demo/immersion/04_bakery_final.png) | Both people visible in the accessible room, readable oven and distinct clothing |
| [Trade confirmation](demo/immersion/05_trade_confirmation.png) | Actual quoted two-coin transaction before commitment |
| [Grounded speech](demo/immersion/06_grounded_conversation.png) | Dated retained supply report in conversation |
| [Final conversation view](demo/immersion/07_final_bakery_conversation.png) | Native conversation framing and compact UI |
| [Fresh district](demo/immersion/09_delivered_fresh_district.png) | The initial six-coin state before subsequent movement |
| [Delivered resumed view](demo/immersion/11_delivered_resumed_district.png) | Current life reloaded after the additional movement; zero browser errors |
| [Legacy comparison](demo/immersion/08_legacy_comparison.png) | Retained illustrated client against the same QA service |
| [Actual scene recording](demo/immersion/kalends_immersion_scene.webm) | Recorded entry, conversation framing and return; VP9, 1920×1080, approximately 19.98 seconds |

The 20-second recorder uses the actual WebGL canvas stream, not a screenshot montage. Its recoverable download link appears under Game menu → Local developer measurements after recording. HTML HUD/nameplates/dialogue and audio are outside the video; screenshots supply that context. The [container audit](results/immersion/capture_validation.json) found 576 nonempty encoded frames, about 28.82 FPS, with a maximum timestamp gap of 600 ms. Native AVFoundation could not decode WebM and browser playback navigation was blocked by its URL policy; independently decoded playback quality is therefore unverified. The live running scene and full viewport screenshots were visually inspected. Recording is separate from performance runs because encoding changes their cost. Files 01–03 are preserved development spikes; file 10 records the stale shared-client check. They are not final conversation evidence.

## Next release priorities

1. Furnish the sparse bakery with a convincing counter, bread and storage, adding matching authoritative obstacle geometry wherever a prop blocks walking.
2. Reduce busy paving repetition and repeated backdrop windows; add bespoke faces, garments, occupation-specific gestures and stronger character recognition.
3. Measure foot contact and locomotion transitions during longer mixed movement, repeated retargeting and all camera limits. Add proper dynamic avoidance only with a shared server/client contract.
4. Complete cold-cache/network, long-session and additional-device testing; profile passes/materials and reduce startup bundle/asset cost before enlarging the district.
5. Expand sustained human playtesting of story clarity, dialogue pacing and consequences. Automated success does not establish that the game is fun.

The existing cognition/provider interfaces are preserved for the next intelligence stage. This release supplies an appearance and interaction layer for validated identity, location, activity, conversation and commitments; it does not add a new cognition engine or bind the game to a paid foundation model.
