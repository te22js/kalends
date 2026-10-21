# Rebirth visual QA

21 October 2026. This record inventories running-game screenshots, the
frontend/art reviews and the final browser pass. The document author inspected
the screenshots from disk; the final browser interactions below were performed
and reported by the root agent after the user reopened a legitimate tab.

## Capture inventory

Pass1, pass2 and release 03–12 desktop JPEGs are 1280 × 720 pixels. The mobile-title JPEG is
1265 × 846 pixels and contains a **390 × 844 CSS-pixel game viewport** inside a
desktop page. It is not a physical-phone capture.

Paths are relative to `demo/rebirth/`.

| Capture | Visible evidence |
|---|---|
| `pass1/03_review_before_fix.jpg` | Sabina's receipt review with the full choice list still above it; confirmation sits near the bottom of the panel. |
| `pass1/04_mobile_title.jpg` | Contained 390 × 844 title layout; headline, Continue button and chapter caption fit in the captured viewport. |
| `pass2/01_title.jpg` | Desktop title, entry action and illustrated district. |
| `pass2/02_street.jpg` | Opening at Day 1, 08:00, six coins; Aelia, Sabina, Dama, Marcus, lead and six-sack cart. |
| `pass2/03_conversation.jpg` | Sabina portrait dialogue, four primary choices and collapsed other work. |
| `pass2/04_review.jpg` | Receipt review replaces the choices; Confirm and Step back are visible. |
| `pass2/05_journal.jpg` | Counter receipt marked read, with Dama and Marcus leads still present. |
| `pass2/06_withheld_account.jpg` | Marcus at 08:03 with six coins; the loading account is explicitly withheld pending a one-coin, fifteen-minute check. |
| `pass2/07_aftermath.jpg` | The paid check, broker arrangement and actual delivery: four sacks to the household, two to Sabina, with 20 world minutes passed. |
| `release/03_conversation_after_choice.jpg` | Marcus at 09:38, seven coins; changed response, relationship-repair choice and report commission. |
| `release/04_review.jpg` | Report commission review: new direct inspection, three-coin reward and confirmation controls. Its deadline wording is generic. |
| `release/05_bag_and_progress.jpg` | Bag at 10:08: nine coins, no flour, broker access and a fulfilled checked-report commission. |
| `release/06_time_and_opportunity.jpg` | Sixty-minute passage aftermath and Marcus's new-account/grievance event. File numbering does not establish action order. |
| `release/07_bakery_interior.jpg` | Bakery at 10:11 with Aelia, Felix and Dama; explicit To the street control. |
| `release/08_fullery_interior.jpg` | Fullery at 10:21 with Chreste and the same exit control. |
| `release/09_food_counter_interior.jpg` | Food counter at 10:37 with Sabina and exit control. |
| `release/10_household_interior.jpg` | Household at 10:52 with Lucius and exit control. |
| `release/11_world_lab.jpg` | Labeled private operator view; removal of verify-cart record 24 shows nine versus five coins and broker versus unresolved route. |
| `release/12_local_notes.jpg` | Scrolled World Lab, four skipped later commands and enabled local play-note records. |

The preserved [baseline manifest](../../demo/rebirth/baseline/manifest.json)
identifies the old Pompeii build and hashes. The [capture manifest](../../demo/rebirth/capture_manifest.json)
adds dimensions and SHA-256 values for all sets. Exact earlier runtime identities
remain unrecorded rather than retroactively assigning the final commit. Final
release20–25 follow the restart to `2c5d9a1`. Release 03–12 came from the then-running `8782` QA browser
with a separate `/tmp` journal. Its preserved save and audit are
`results/rebirth/browser_walkthrough/before_week.json` and
`before_week_audit.json`: 172 world minutes, nine coins, broker route, commission
fulfilled and working relationship repaired. They establish these visible
states and a replayable accepted-command journal, not an independent playtest or every route in
the walkthrough.

## Observed sequence and repairs

The pass2 evidence follows entry, street, Sabina conversation, receipt review,
retained-document journal, Marcus's withheld account and the broker delivery
aftermath. The release evidence adds a later conversation and commission,
fulfilled progress, four distinct interiors and a causal alternative in World
Lab. This supports a connected playable sequence beyond the opening screen.
It does not establish elapsed real-world onboarding time, save/restart behavior
or complete market/household-route browser runs. The one-week continuation was
initially validated in Python only; the final browser pass below now adds an
actual week/return interaction and captures.

Pass1 exposed a crowded review with the other choices still taking space.
Pass2 visibly separates primary choices from other work and replaces choices
with the active review. The later review retains readable confirmation and
cancellation controls. The interior captures show actors over painted floors
and a clear exit button, but cannot prove correct room-to-room animation,
furniture collision or foreground occlusion.

The [art review](ART_ADVERSARIAL_REVIEW.md) found a substantial improvement over
the schematic baseline, while flagging the geometric cart and tiny topic/helper
text. The [frontend audit](FRONTEND_RELEASE_AUDIT.md) identified stale room
rendering between interiors, late conversation/proposal responses, overlapping
consent saves and undisclosed commission deadlines. These reviews are internal
agent assessments, not external endorsements.

## Final browser pass

The earlier browser-authority block was resolved when the user reopened the
game. The root agent resumed the legitimate browser session and used actual
viewport controls for desktop and narrow captures. Continued gameplay used
`8785` with the separate `/private/tmp/kalends-rebirth-qa-resumed.json` journal;
`8787` supplied a separate fresh life for the opening scene. The user's `8782`
life was captured without gameplay actions. No workaround browser was used.

All final screenshots are in `demo/rebirth/release/`; dimensions were checked
from the JPEGs, and each image was inspected.

| Capture | Pixels | Visible evidence |
|---|---|---|
| `13_final_street.jpg`, `15_final_street_narrow440.jpg` | 440 × 724 | User's current narrow street at 08:41, six coins; painted cart, context, movement and time controls. These are not 390px captures. |
| `14_final_title_desktop.jpg` | 1280 × 720 | Current title with Continue as Aelia. |
| `16_final_bag_desktop.jpg` | 1280 × 720 | Resumed QA life: nine coins, no flour, broker access and fulfilled report commission. |
| `17_final_mobile_conversation.jpg` | 390 × 844 | Lucius conversation with readable supporting text, wrapping topic buttons and close control. |
| `18_final_mobile_review.jpg` | 390 × 844 | Inspection review with one-coin/fifteen-minute cost and both Confirm and Step back visible. Preview was cancelled without a charge. |
| `19_final_mobile_room.jpg` | 390 × 844 | Household, movement pad and reachable To the street button; the subsequent browser exit succeeded at world minute 179. |
| `20_final_street_desktop.jpg` | 1280 × 720 | Fresh 08:00 opening with six visible painted sacks. Wood, wheels, sack shading and scale now sit coherently beside the painted actors and street. |
| `21_final_week_return.jpg` | 1280 × 720 | Actual A week UI passage: 10,080 minutes passed and a Day 8 household-trust event. |
| `22_final_retained_memory.jpg` | 1280 × 720 | Day 8, 10:59; Marcus's Our history recalls the fulfilled three-coin report commission and working-relationship repair. |
| `23_final_commission_deadline.jpg` | 1280 × 720 | Commission review discloses 240 world minutes and Day 8, 14:59 before confirmation. |
| `24_final_unavailable_quote.jpg` | 1280 × 720 | Typed 12-unit purchase: 12 × 2 = 24 coins, explicit need for 24 coins, Confirm disabled while Aelia has nine. |
| `25_final_completed_purchase.jpg` | 1280 × 720 | After reviewing one unit at two coins and confirming, the Bag shows seven coins and one flour unit, with the purchase receipt. |

The actual browser sequence resumed the fulfilled/repaired life, inspected and
cancelled the mobile review, left the household, and selected A week. Time moved
from 179 to 10,259 world minutes, exactly 10,080 minutes later. It then revisited
Marcus's retained history, reviewed a new commission without accepting it,
cancelled an unaffordable purchase preview, and completed the affordable
one-unit purchase. The week capture supersedes the earlier Python-only limit.
The resulting `final_browser_journal.json` and `final_browser_audit.json` preserve
19 accepted commands at minute10259; exact read-only replay recovered the hash,
seven coins and one flour unit without modifying the QA source journal.

## Repair verification and remaining checks

The working tree adds a painted cart, enlarges supporting text and touch
controls, guards conversation/proposal responses with conversation generations,
serializes consent saves and exits the previous room before street traversal.
Public-offer work adds authoritative cost/deadline information before commitment
and disables confirmation when the server reports an unavailable purchase.
The earlier `04_review.jpg` remains evidence of the generic deadline wording;
the final `23_final_commission_deadline.jpg` now records the numeric repair.

| Area | Final status |
|---|---|
| Painted cart and desktop composition | Rechecked in fresh opening capture 20. |
| Larger supporting copy, 390px conversation/review and room exit | Rechecked in captures 17–19; both review actions fit, cancellation incurred no charge, and the exit was used successfully. This is browser-viewport evidence. |
| Public commission deadline and purchase quote/availability | Rechecked in captures 23–25, including successful purchase state change. |
| Week passage and remembered return | Actual browser actions and captures 21–22 now complete. |
| Delayed context/proposal close races and serialized consent saves | Covered by the source checks below; artificial response interleavings were not forced in the browser. |
| Direct interior → street → different interior animation | Source regression check passes; final browser evidence establishes room exit, not the full transition sequence. |

Narrow captures use browser viewports, not physical phones. Compact landscape,
physical-device touch ergonomics, rendering/GPU performance and exhaustive
scrolling states remain unverified. There was no human playtest, video or FPS
measurement. The renderer still lacks full furniture collision and foreground
occlusion, as the art review explains.

## Separate source regression checks

`node --test tests/frontend/rebirth_client.test.cjs` passed **8 tests, 0 failed**.
The tests execute the actual `app.js` in a Node VM with a minimal fake
DOM/canvas/fetch: delayed context close, same-person reopen, delayed proposal
close, proposal failure, consent serialization, consent failure/retry,
street rendering between interiors, and an unavailable trade review showing
the server's numeric cost/reason with Confirm disabled. They make no network or
browser calls.
They support request/DOM/drawing behavior under controlled inputs and are
**source checks, not visual evidence** or proof of browser race interleavings.
