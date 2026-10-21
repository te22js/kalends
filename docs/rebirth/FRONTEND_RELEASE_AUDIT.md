# Frontend release audit

21 October 2026. Independent read-only review of `kalends_rebirth/static/app.js`, `index.html` and `style.css`, plus actual release captures `04_review.jpg` and `07_bakery_interior.jpg`. The reviewer did not control the browser or alter game Python. Root owns browser verification and fixes; source review alone is not a completed interaction test.

## Findings and repair status

| Priority | Finding | Evidence and disposition |
|---|---|---|
| P2 | Direct travel between interiors retained the old room throughout the intervening street walk. | `draw()` cleared the room only when the destination was null. Root changed the condition to `S.desired !== S.interior`, exiting at the old doorway before entering the destination. Repair inspected in current source; browser transition verification belongs in VISUAL_QA.md. |
| P2 | Closing a conversation while a proposal request was pending could create an invisible proposal that blocked walking. A late context response could also reopen a closed conversation. | `propose()` assigned its response after `closeConversation()` cleared selection. Root added conversation epochs to context/proposal requests and invalidates them on close; late responses/errors are discarded. Repair inspected in current source. |
| P2, repaired | The local-notes consent checkbox permitted overlapping saves. | Root now disables it during a pending save, captures the requested boolean and restores actual saved state on failure. Offline integration checks exercise serialization, failure and retry. No forced browser race is claimed. |
| P2, repaired | Commission review did not reveal the actual time limit before accepting the promise. | Root and the offers agent added authoritative duration/due-time terms from the actual commission specification. `23_final_commission_deadline.jpg` verifies a240-minute limit and Day8 14:59 before acceptance. This is a post-study release change. |

## Checks that did not reveal another blocker

The interior projection and pointer inverse both use the same `.43/.36` vertical mapping. The explicit room-exit button avoids relying on the footer-obscured canvas marker. District overview is retained indoors until recentering or travel. Modal key guards prevent journal/map shortcuts from operating behind an open dialog.

Question replies, copied document text and transaction receipts have separate display paths. Typed purchase quantities retain the server's reviewed quantity; the UI does not invent a numeric current price. All inserted prose is escaped. The counterfactual view names the removed record, preserves the selected action, shows unresolved/no-access alternatives, and exposes skipped-command explanations.

Normal startup returns a persisted operator session to Game before accepting its view. World Lab is explicitly labeled as revealing private state. The game is a single local session; this review does not establish a multi-user authorization model.

Painting is skipped on the title screen, when the document is hidden, and under modal dialogs. This avoids unnecessary full-scene redraws but is not an FPS measurement. The bakery capture shows a readable explicit exit, restrained HUD and actors on the painted floor; it does not prove furniture collision or foreground occlusion.

The latest CSS enlarges topics/helper text and gives the movement pad44-pixel controls. The supplied390px preview is a contained browser viewport, not a physical phone test. Root should verify scrolling, confirmation controls and exit access there; compact landscape layouts and physical-device performance are not established by these captures.

Final verification subsequently used a real390×844 browser viewport: dialogue, review controls and the household exit were reachable. See VISUAL_QA.md for current captures. Eight source integration checks cover the asynchronous fixes and disabled purchase confirmation; these checks do not measure browser frame rate or physical-phone usability.
