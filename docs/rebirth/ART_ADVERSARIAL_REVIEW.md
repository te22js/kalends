# Rebirth visual review — art-director perspective

Agent review of actual browser captures, 21 October 2026. This is a separate
reviewer’s assessment, not an external professional endorsement or human
playtest. No source files or assets were changed by this reviewer.

## Evidence inspected

- Preserved baseline: `demo/rebirth/baseline/09_fresh_audit_street.jpg`.
- Rebirth: `demo/rebirth/pass2/01_title.jpg` through `07_aftermath.jpg`,
  including the street, conversation, review card, journal and withheld account.
- Contained mobile title: `demo/rebirth/pass1/04_mobile_title.jpg`, showing a
  real 390 × 844 CSS-pixel game viewport inside the browser page.
- Read-only inspection of `kalends_rebirth/static/app.js` and `style.css`.

These are captured running screens. They are not concept art presented as
implemented gameplay. Interior and mobile-gameplay captures were not yet in
this reviewed set; their final QA must be checked separately.

## Priority findings

| Priority | Observed problem | Practical repair and verification |
|---|---|---|
| P2 | The six-sack cart in `pass2/02_street.jpg` has flat beige fills and geometric wheel/sack outlines. It reads as a diagram pasted onto the materially painted street, immediately beside characters rendered with shading and cloth detail. | Give this focal story prop painted material/shadow detail or replace it with an original transparent painted prop. Keep six visible sacks and state-dependent appearance. Reduce its visual weight modestly so it belongs at the actors’ scale. Check the actual opening screenshot, rather than the prop in isolation. |
| P2 | Secondary interactive text is unusually small: desktop topic chips and choice helpers are 9px; mobile topics are 8px and helpers 9px. The larger-text setting increases the dialogue and choice heading but leaves these supporting controls tiny. | Raise actionable topic/helper text to roughly 11px and choice headings to 12–13px; extend the larger-text treatment to them. Increase touch targets for close/settings/movement controls, using padding rather than oversized icon glyphs. Verify expanded choices and the review card at 390px width, including wrapped costs. |

No P1 visual obstruction or broken composition was visible in this capture set.
This does not establish that every dynamic state or smaller viewport is sound.

## Assessment against the brief

The change from the baseline is substantial. Buildings now have distinct
materials, believable wear and architectural detail; the previous schematic
roof blocks and pale empty ground no longer dominate. The street occupies the
whole viewport, with a smaller lead card rather than a large instruction panel.
Actors have readable identities at the opening camera scale. Their ochre,
vermilion, olive and linen colors sit comfortably within the environment.

The title screen has a clear focal sequence: identity, premise, entry action.
The dark green overlay protects the large serif title without flattening the
entire painting. Its 390px version retains that sequence and avoids clipped
headline or entry button in the captured full-height viewport.

Portrait dialogue, review, journal and aftermath use the same paper, vermilion
and serif vocabulary. Sabina’s portrait and field sprite have compatible hair,
clothing and palette. The review card visibly distinguishes consideration from
commitment. The aftermath’s larger event titles are readable and show the
actual changed agreement, rather than technical ledger JSON.

The restrained interface is appropriate, but it depends too much on very small
metadata. Essential costs and topics must remain comfortably readable. Preserve
the hierarchy while correcting that issue; adding more panels would weaken the
composition.

## Remaining visual limits

The renderer layers sprites over one painted street and four room images.
There are no complete foreground occlusion masks or furniture collision meshes.
Sprite animation is limited, including a two-pose Aelia presentation, rather than
a full directional walk set. Building scale and perspective are schematic;
illustration does not establish archaeological accuracy. A phone-sized iframe
checks responsive layout, not device GPU performance, touch ergonomics or
physical-phone rendering.

Final release evidence should include an interior, the mobile conversation and
review card, a later return, and World Lab. Any repaired findings above need a
fresh running screenshot before being described as resolved.
