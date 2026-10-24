# Actual next-phase walkthrough

The screenshots in `final/` are captures of the real local interface. They are
not concept art or inserted world events. Baseline captures in `baseline/` show
the older interface before this phase; they are not delivery proof.

1. Open `http://127.0.0.1:8810/`. Choose Worlds and inspect either supported
   setting. Begin a new life creates a unique journal; Continue opens a saved one.
   `home_desktop.jpg`, `home_narrow.jpg` and `saves_narrow.jpg` show this entrance.
2. Observatory: select Mira, ask for a dated report, review and confirm. A
   cancelled request does not disclose a report or spend credits. Invalid 5/5/5
   allocations are rejected. A second tab advancing time makes an earlier review
   stale (`stale_review.jpg`).
3. Promise Lin four units and separately allocate 4/4/4. Continue the day stops
   before the known deadline. Explicitly let that deadline pass: delivery is
   4/4/0, and Lin's promise is missed (`observatory_consequence.jpg`). The saved
   demo life is `observatory_2898dc1a5d60`; later cross-life testing advanced it
   to day 2. Its history retains the first-day settlement.
4. Your story → Reflect restores the admitted pre-choice evidence. Select the
   allocation and execute the omission. Later commands remain fixed where
   feasible, and the original is preserved (`executed_alternative.jpg`).
   Narrow conversation/reflection captures are also included.
5. Pompeii: enter as Aelia, speak with Sabina and read an ordinary-life topic.
   Leave an unsent draft, rotate the camera, open Your story, then return. The
   same scene and draft survive. Full reload restores the same life and local
   view (`pompeii_before_history.jpg`, `pompeii_after_history.jpg`).
6. Review the three-coin market arrangement. Cancel first, then newly review and
   accept: cash becomes three only after the receipt. Advance an hour. Dama acts
   independently and the affected households/counters change. Find Sabina in
   the journal and walk to her current counter. Her changed greeting reports
   the real delivery; the draft remains (`pompeii_return_consequence.jpg`,
   `pompeii_changed_encounter.jpg`). Demo life: `pompeii_b2436bc08914`.
7. Read Research for the actual comparison table and report links. Lab is reached
   through the world menu and requires an exposure acknowledgement. This was
   tested on a disposable life (`lab_boundary.jpg`), with private DOM removed on
   return. The product demonstration lives were not exposed to Lab.
8. Experimental Studio validates finite fields and creates a separate authored
   life (`studio_validated.jpg`). Save-failure images are from a separate,
   disposable 8812 fixture: the failed journal write retained 12 credits; a new
   successful review charged once. An independent metadata failure displayed
   **World saved · Display metadata needs attention** (`metadata_warning.jpg`).

`scene_performance_raw.json` was read from the retained developer measurement UI,
with 1088 frame intervals over about 36 seconds. It measures browser callbacks
and render submission, not GPU completion or a physical display. Only full UI
stills are presented here; the existing canvas recorder cannot record HTML
controls and was not represented as a full-interface video.
