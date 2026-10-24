# Product frontend implementation and verification

24 October 2026. Frontend changes are confined to
`kalends/experience_os/static/product/` and the product frontend test file.
The original Experience OS interface remains available through compatibility
routes. The homepage loads no scene iframe or PlayCanvas bundle.

The product now has public home, two-world catalog, detail/start, saved-life,
research, about, data, accessibility and asset/source pages. A life uses a
compact header, a retained scene or Observatory stage, and participant history,
people and reflection drawers. Observatory distinguishes requested, promised,
allocated and delivered units. Accepted changes come from server receipts.
Known-deadline protection and explicit deadline crossing are different actions.
Research Lab requires acknowledgement and removes its private DOM on exit.
Studio edits only the four backend-supported fields; it never exposes a general
code-generation surface.

Each entered Pompeii life owns one retained iframe. Opening history, changing
public routes and receiving ordinary accepted-state updates do not replace it.
Hidden scenes pause. Returning unhides the active frame and performs a read-only
refresh. Busy scene responses receive bounded read-only retries, never repeated
world mutations. Camera, conversation, drafts and local interface state emitted
by the existing scene adapter are stored in per-life sessionStorage and restored
after scene readiness. They are not telemetry or NPC memory.

Life changes invalidate old reads. Revisions and request ordering reject stale
same-life responses. Commons drafts are keyed by life and recipient; ordinary
reconciliation restores the focused field and its caret. An ambiguous write
requires an authoritative read before another write. Personal notes/bookmarks
remain separate from the canonical history.

Verification commands:

```sh
node --check kalends/experience_os/static/product/app.js
node --test tests/frontend/next_phase_product.test.cjs
```

The lead agent owns actual desktop and narrow browser walkthroughs and records
their results in `PRODUCT_QA.md`. The frontend implementer additionally inspected
the captured homepage and Observatory consequence images in
`demo/next_phase/final/`; their hierarchy and readability were coherent. Those
captures preceded several continuity fixes, so they are not evidence of the
later fixes. Handler and scene-protocol tests complement the browser evidence;
they do not establish human enjoyment, accessibility certification or demand.

The product test file passes 13 checks. Six execute the actual application boot
and registered handlers against a small DOM/fetch boundary, checking retained
iframe identity, visibility restoration, sessionStorage restoration, read-only
busy-scene retries, private Lab DOM removal and revision ordering. This harness
does not emulate browser layout, WebGL, focus behavior or physical presentation.
The remaining checks cover request invalidation, scene-message identity,
consequential labels and text escaping. Real browser QA remains necessary.
