# Fresh agent usability probe

Date: 2026-10-24. Method: an agent using the displayed browser UI, not a human playtest. No implementation files, solution scripts, prior QA results, gameplay APIs, browser mutations through JavaScript, or shell gameplay were inspected or used. This report does not establish human comprehension, learning, accessibility conformance, or enjoyment.

## Scope and identities

- Starting URL: http://127.0.0.1:8831/ only. All subsequent navigation followed visible controls.
- Disposable QA installation was designated by the parent as /private/tmp/kalends-redesign-qa. The browser UI confirms saves on this installation; this probe did not independently inspect the server storage location.
- New Pompeii life: pompeii_ed1ec6ef7a97, displayed name “Aelia — a place in the city”. Started Day 1 08:00; left at Day 1 08:36 with 3 coins.
- New Shared Observatory life: observatory_f9b238328cb8, displayed name “Your shared observatory”. Started Day 1 00:00; left at Day 1 23:59 with the round settled.
- An existing Pompeii life, pompeii_19e89db35b27, appeared on home/saved-worlds screens. It was not entered. Recorded examples were not entered. Ports 8810 and 8823 were never used.
- CUA native accessibility actions drove the walkthrough. Full AX snapshots include offscreen content, and clicking an AX control can scroll it into view. This makes the agent's discovery burden different from a human's visual search. The ordinary browser viewport was retained; screenshots are uncropped full-viewport JPEGs, not full-page captures.
- No external assistance was needed to complete the two paths. CUA visibility initially failed because subagent threads do not support visible IAB creation; reopening without a visibility option worked. This was a test-tool limitation, not a product defect.

## Observed outcome

Both bounded journeys reached an informed consequential choice, an observable result, and a successful leave/return. Pompeii also exposed an explicit historical evidence/invention distinction. A premature paid review was canceled without a charge or time change. Guidance off/return/resume worked in both experiences. No hard blocker prevented completion.

The clearest remaining product issues were the Pompeii result-review destination, Observatory requests arriving after the allocation decision, and the allocation becoming locked without that consequence being prominent before confirmation. These findings are specific to the observed paths.

## Pompeii click path and reasoning

| Step | Displayed control/action | Visible fact or outcome |
|---|---|---|
| 1 | Home → Begin another morning | Created the new life. Home says Aelia is fictional, the dispute is fictional, and places draw on archaeological evidence. |
| 2 | Who am I? How do I move? | Aelia is a fictional freedwoman, formerly enslaved. Her work/choices were invented. Click ground or use keys to walk; E speaks nearby. |
| 3 | Begin → Talk to Sabina | Sabina says she paid Marcus for flour and the household now claims the cart. |
| 4 | Pay for the market delivery | A review says 3 coins, 20 world minutes, four sacks to Sabina and two to Felix, household advance refunded, Lucius loses priority. |
| 5 | Keep looking | Canceled the premature choice. Still 6 coins and Day 1 08:00. This was a deliberate ordinary mistake: opening the prominently offered paid action before hearing both accounts. |
| 6 | What happened to your order? | Sabina asks who the six sacks were promised to. Guide changes to Understand the two claims. |
| 7 | May I see your order? | Wax account: two flour units, four coins advanced to Marcus. Explicitly labeled fictional gameplay document and this person's account. |
| 8 | Leave conversation → Walk to Thermopolium of Vetutius Placidus | Guide moved to a historical stop after one account. Walking advanced time to 08:09. The destination eventually offered What is this place? |
| 9 | What is this place? → How do we know? → What we invented | Historical card distinguishes surviving counter/jars, a schematic reconstruction, and invented people/stock/prices/dispute. |
| 10 | Close notebook → Walk to the public street meeting point | Arrived at 08:16. Guide offered Talk to Dama. This resolved the concern that it had skipped the second account entirely. |
| 11 | Talk to Dama → May I see the household’s instructions? | Household reserved four flour units with eight coins advanced; Dama was told to repeat the quantity, not claim the whole cart. Explicitly fictional gameplay document. |
| 12 | Leave conversation → Help & directions → Turn guidance off | Context card remained, with Open your journal and Resume guidance. Live became available but remained unchecked. |
| 13 | Back to your worlds → Continue on the most recent life | Time remained 08:16; guidance remained off; return notice named both copied documents. |
| 14 | Continue from here → Resume guidance | Returned to Choose whether and how to help. The off/resume control was in the same expanded directions area. |
| 15 | Talk to Sabina → Pay for market delivery → scroll review → Pay 3 coins | Accepted the arrangement after both accounts and the review. Time became 08:36, coins 3. Sabina said she received four flour units. |
| 16 | Leave conversation → Review what happened | Opened Your story / Reflect. The selected action was the payment, but the prominent content was pre-choice walking records and alternative-execution controls. |
| 17 | Chapters | The leading chapter clearly said Sabina received four units and Felix two. This was the durable result I sought. |
| 18 | Close story → Back to your worlds → home | Saved-world card showed 08:36. Proceeded to the separate Observatory entry. |

My decision rationale: I chose to spend half of Aelia's six coins to support the market counters, accepting that this redirected the cart away from the household and refunded its advance. The review made the tradeoff explicit. I did not infer that this honored the original two/four order split, that it was morally preferable, or that it was an optimal outcome. I did not inspect Marcus's third account, the household advance, negotiation, or other outcome branches.

Historical distinction actually encountered: the card attributes the surviving serving counter and embedded vessels to the Archaeological Park of Pompeii. It states that those remains do not establish the exact daily menu or workers' identities. The game counter is a schematic reconstruction, and Sabina, her stock, prices, and the flour dispute are fictional. I read this distinction in the UI; I did not open or independently verify the external source. The visible question about which feature suggests serving customers was not answered through a quiz or assessment.

## Shared Observatory click path and reasoning

| Step | Displayed control/action | Visible fact or outcome |
|---|---|---|
| 1 | Home → Enter Shared Observatory | Created a new life. Role is coordinator of a shared instrument used by three teams. Units are simplified shares, not measured telescope hours. |
| 2 | Begin the guided round → I understand this request | Mira currently requested two units. Request, promise, and allocation are described as separate. |
| 3 | Ask Mira for the report | Received an observation at Day 1 00:00 of eight usable units, against a twelve-unit rating. |
| 4 | What the teams need to finish their projects | Each team needs four units in one delivery, due Day 2 00:00. Smaller delivery records use but does not finish a project. |
| 5 | Amir tab → Another question or an inspection | Amir had no current request. His introduction mentioned a deadline and distinguishing promises from delivery. |
| 6 | Type “How many units does your team need for this round?” → Ask | Returned a limitation notice: supported speech concerns dated reports, inspections, and quantified promises. No request was obtained. I did not try guessed phrases repeatedly. |
| 7 | Lin tab | Lin also had no current request. No direct Ask for request control was visible. |
| 8 | Set Mira 4, Lin 4, leave Amir 0 → Review allocation | Review showed 0/4/4, total eight, dated eight-unit report, public order Amir → Mira → Lin, and settlement 23:59. |
| 9 | Confirm this choice | Allocation saved; fields disabled. Only now did the main page explicitly say saved amounts cannot be changed during this round. |
| 10 | Continue without making a promise | Guided flow clearly allowed no promise. |
| 11 | Review and finish this round → Run with these saved choices | Review named start/end time, saved quantities, dated capacity report, order, and no open promise. Round advanced to 23:59. |
| 12 | Continue from here → Compare requests, promises and delivery | Actual result: Amir 0, Mira 4, Lin 4. Mira and Lin completed; Amir remained open. Table now showed all three requested two units. |
| 13 | Explore without guidance → Back to your worlds → Continue | Result and 23:59 persisted; guidance remained off. |
| 14 | Continue from here → Help → Resume guidance | Help displayed guidance off, offered resume, then confirmed on. |
| 15 | Review the actual result | Closed Help and focused/scrolled to the actual round-result card. This destination matched its label. |

My decision rationale: with eight observed usable units and four-unit project thresholds, I chose two complete projects instead of three incomplete shares. Mira and Lin were the chosen beneficiaries; nothing in the evidence I received established that they deserved precedence over Amir. I made no promise because the UI allowed allocation without a separate commitment, and because the report could become stale before settlement. The observed delivery matched my saved allocation. I did not test inspection, a promise, over-allocation, a second day, or failed delivery.

## Ambiguities, friction, and unnecessary steps encountered

| Priority | Observation and practical effect | Evidence |
|---|---|---|
| Medium | Pompeii's Review what happened opens Reflect with pre-choice evidence, dominated by walking/time records. It did not directly show the payment's delivery receipt. Chapters required one extra tab selection to reveal a clear result. | 14-pompeii-outcome; 15-pompeii-chapters |
| Medium | Reflect uses “accepted action”, “admitted records”, “admitted prefix”, “executes one omission”, “declared choices”, and “retained memory”. These terms required agent inference and are much more technical than the street task. Most recent 8 of 54 records hid Sabina's earlier account behind an expansion while seven prominent records were movement/time. | 14-pompeii-outcome |
| Medium | Observatory tells the coordinator to read teams' requests, but before deciding only Mira's request existed in the displayed state. Amir/Lin tabs say no current request; natural speech asking Amir's need was unsupported. Both requests appear after settlement. This left the first allocation informed by project thresholds, not all three team requests. It is unknown whether a separate visible time action would have produced them earlier; the guide did not direct me there. | 17-observatory-report; 18-observatory-request-question; 21/22-observatory-result |
| Medium | Allocation confirmation locks the amounts for the round. The pre-confirm review says commit and save separately from promises, but does not explicitly state that saved numbers cannot be changed before running. The lock becomes explicit only after confirmation. This matters if a player wants to correct a number after collecting a new report. | 19-observatory-allocation-review; 20-observatory-round-review; later AX states |
| Low | Pompeii inserts the historical trip between the first and second account. The change from Understand the two claims to Learn one historical idea in place made me briefly infer the second claim might be optional or skipped. It was later resolved by the return destination and Talk to Dama. | 05-pompeii-order; 08/09-history and household |
| Low | The first Pompeii paid review's confirm/cancel controls lie below the initial visible conversation viewport. The panel's scroll state persisted across some conversation changes, occasionally clipping its heading. AX access made this easier than it may be visually. A later manual scroll exposed the complete review and controls. | 04-pompeii-premature-review; 05-pompeii-order; 13-pompeii-final-review |
| Low | The home page offers another morning below the initially visible continue card. Existing lives share the same Aelia title; most-recent status, time, location, and link identity distinguished them in this probe. I did not see a naming affordance in the traversed path. | 01-home; 11-saved-lives |
| Low | Pompeii's guide hides during conversation, so I closed each conversation to use the next guide step. This is understandable but adds a close/reopen transition between hearing accounts and continuing the guided path. | 03/05/09 conversation captures |
| Low | The source card exposes an internal-looking reference token “first-session-history-v1:S2” beside the real source link. It adds no apparent help to the current task. | 08-pompeii-history-expanded |
| Low | Pompeii's off/resume control remains within the directions panel; Observatory's off control removes the guide entirely, so resuming required Help. Help was a reasonable place to look, but the two worlds differ and there was no immediate Resume control on the Observatory page. | 10/12-pompeii; 23/24-observatory |
| Low | Observatory project-threshold disclosure collapsed when switching people. Reading another person caused the long page content to rebuild; retaining the expanded needs panel would reduce repeated disclosure work. | 18-observatory-request-question and surrounding steps |
| Low | Observatory has an acknowledgement click (“I understand this request”), separate save confirmation, an explicit no-promise choice, and another run confirmation. The distinctions are explained, but the acknowledgement alone adds a step without eliciting evidence of understanding. | 16/17-observatory; 19/20-review |
| Low | Result page contains repeated execution-order explanation, and both “table above” and “recorded result below” direction text. The compare table is collapsed by default. The compact result itself is clear; the directional copy and repeated prose can add scanning work. | 22-observatory-result-comparison |
| Low | Some receipt/return text still uses implementation-like wording (“declared project register”, “Elsewhere in this world”, “Movement, accepted work…”). The Observatory return notice mentions movement although this journey is a dashboard. | 21-observatory-result; 23-observatory-return |

No claim here establishes that a human will misunderstand these points. These are observed labels, transitions, and agent interpretation costs. The priority labels are recommendations for product review, not a completed severity study.

## Assistance and unknowns

Displayed guidance was sufficient for the core paths. The only in-product Help use was to discover Observatory Resume guidance after returning. No parent supplied the answer to a puzzle or choice. There was no need to inspect source, mutate state, invoke a hidden API, brute force speech, or access existing user lives.

Actual unknowns include human comprehension and retention; keyboard-only traversal; screen-reader use; mobile layouts; very long save lists; novice recognition of panel scrollbars; alternative branches; promised versus failed delivery; later-day consequences; independent historical accuracy; and whether other explicit time choices resolve the missing first-round requests before allocation. The browser UI alone did not verify underlying save-directory placement or causal correctness beyond the visible receipts.

## Evidence index

All files are in results/redesign/browser/fresh-probe/. Each numbered basename has a .jpg full-viewport screenshot and a .ax.txt full accessibility state. Captures are unedited.

1. 01-home
2. 02-pompeii-arrival
3. 03-pompeii-sabina
4. 04-pompeii-premature-review
5. 05-pompeii-order
6. 06-pompeii-historical-place (captured while still walking, not final arrival)
7. 07-pompeii-source-distinction
8. 08-pompeii-history-expanded
9. 09-pompeii-household
10. 10-pompeii-guidance-off
11. 11-saved-lives
12. 12-pompeii-return
13. 13-pompeii-final-review
14. 14-pompeii-outcome (Reflect destination; filename does not imply the receipt is present)
15. 15-pompeii-chapters
16. 16-observatory-arrival
17. 17-observatory-report
18. 18-observatory-request-question
19. 19-observatory-allocation-review
20. 20-observatory-round-review
21. 21-observatory-result
22. 22-observatory-result-comparison
23. 23-observatory-return
24. 24-observatory-guidance-resumed
25. 25-observatory-review-destination

Browser walkthrough complete; no source files changed. This report and its evidence were written using CUA filesystem operations.
