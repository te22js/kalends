# Baseline operator walkthrough

This is agent-operated engineering observation, not a naive human playtest. The
operator followed displayed controls in an isolated directory before substantive
implementation. No user save on 8810/8823 was used.

- Baseline source: `377a727`; initial server `8830`, saves
  `/private/tmp/kalends-redesign-before`.
- Pompeii `pompeii_5fc571e86fbd`: Begin; short D movement (08:00→08:01);
  Talk to Sabina; ask about order; confirm disclosure; request order; confirm copy;
  review market payment; confirm; actual 08:21, purse 6→3, Sabina4/Felix2;
  open story; close; reload the same life. No claim of all optional guide chapters.
- Observatory `observatory_90ddbbff0654`: start; request Mira's report; confirm;
  eight usable units received, clock remains00:00. No baseline settlement here.
- Full interface captures/AX saved as `results/redesign/browser/before-*`.
  Initial visible IAB viewport was518×720; later hidden tabs use1280×720.
  These widths are not silently treated as matched. An unchanged source archive
  rebuilt in `/private/tmp/kalends-redesign-baseline-source` on8832 permits
  additional matched1280 captures. Its bundle exactly matches the prior release
  names `index-CbuBMLFg.js` / `index-BdUbm4iJ.css`.

| Reproduced friction | Cause / evidence | Intended correction |
|---|---|---|
| Free Sabina account: 2 clicks after conversation opens | Choice opens an administrative review requiring second click |1 intentional validated question, no hidden answer before click |
| Copy Sabina's offered order: 2 clicks | Same review for free copied evidence |1 validated observation; show newly received document |
| Mira report:2 clicks | Review exposes retained/disclosure vocabulary |1 validated question with dated received report |
| Many topics plus all choices compete with speech | Before conversation AX contains4 generic topics and7 choices |2–3 relevant replies; More preserves remaining affordances |
| Delivery result exposes private regard | Guide says Sabina's regard improves and Lucius's falls |Show quantities; grounded observed response only |
| Scene guide repeats time policy | Two paragraphs compete with current action |Compact instruction plus stable time state; fuller Help |
| History reads as list of every record | Raw category and several administrative headings |Meaningful chapters, supporting evidence/routines optional |
| Observatory juxtaposes request2 and project4 | No explanation of the distinction |Audit policy; truthful request vs threshold explanation |

Judgment: these layers felt administrative and visually busy to this operator.
That judgment is not a comprehension score, satisfaction result or user study.
