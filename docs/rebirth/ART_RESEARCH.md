# Renderer and presentation investigation

Checked 21 October 2026 against primary documentation. This is a feasibility
review, not a measured renderer comparison. The game owner makes the final
choice in `ART_DIRECTION.md`; browser captures and visual QA assess the result.

| Option | Verified capability | Fit and cost for this build |
|---|---|---|
| Phaser 4 | Browser-focused JavaScript/TypeScript 2D game framework; WebGL/Canvas; current renderer adds GPU sprite/tile layers and filters. | Strong candidate for many animated sprites, tilemaps, cameras and input. A new scene/input lifecycle and dependency still require integration and regression work. |
| PixiJS 8 | Async Application initialization, WebGL/WebGPU rendering, containers, sprites, assets and scene graph. | Good rendering foundation; gameplay orchestration remains application work. Switching alone does not supply compelling art, story or navigation. |
| Godot web | WebAssembly plus WebGL2 Compatibility; single-threaded web export is default; browser and audio constraints remain. | Viable for a larger authored game pipeline. A new project/export/runtime layer is a substantial cost while retaining Python authority. |
| Asset-driven Canvas | Browser image drawing and controlled smoothing; existing route animation and input can be retained. | Lowest migration cost for this small cast. Layered original backgrounds, portraits, depth, camera and responsive dialogue can improve quality immediately. Needs explicit layering and culling discipline. |

**Recommendation:** prioritize a coherent asset-driven scene over an engine
rewrite. Keep the authoritative simulation independent. Retain layered Canvas
if it can ship the selected art direction with reliable interaction now; move to
Phaser when measured animation/tilemap/camera complexity justifies that cost.
This recommendation does not claim Canvas is faster, prettier or more scalable.

Three feasible directions have different production risks:

- Mediterranean illustration: textured environment layers and warm material
  detail; strong fit for the setting, requiring perspective/lighting consistency.
- 2.5D/isometric town: readable depth and attractive architecture; harder to
  match generated assets, route geometry and occlusion across multiple interiors.
- Illustrated narrative adventure: portraits and layered scenes make intimate
  choices legible; can reduce free spatial exploration if overused.

A hybrid of the first and third is achievable: a richly illustrated navigable
street, distinct interiors, expressive character portraits and restrained HUD.
Do not paint decorative people or completed trades into background art. Character
activity should remain an independent layer driven by actual state. Door positions
must match the interaction geometry even when an illustration looks convincing.

Pentiment's official presentation connects its historical materials, typography
and limited-frame animation into one visual language. The transferable principle
is coherence between period, interface and motion. Its sixteenth-century
manuscript/woodcut identity is inappropriate to copy into first-century Pompeii;
no protected game screenshots or assets should become Kalends backgrounds.

Practical gates: inspect ordinary desktop and narrow/mobile sizes; compare
baseline and new start, street, dialogue, journal, interior, consequence, return
and lab captures. Check that the world has enough room, entrances are readable,
portraits do not obscure choices, contrast survives a sunny background, and
reduced motion/optional sound preserve the same information. A framework choice
is not evidence these gates passed.

Primary sources:

- [Phaser introduction](https://docs.phaser.io/phaser/getting-started/what-is-phaser)
  and [Phaser 3/4 changes, 13 May 2026](https://phaser.io/news/2026/05/phaser-3-vs-phaser-4).
- [PixiJS 8 Application](https://pixijs.com/8.x/guides/components/application).
- [Godot stable web export](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html).
- [Canvas image smoothing](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/imageSmoothingEnabled).
- [Pentiment official site](https://pentiment.obsidian.net/) and
  [Obsidian's announcement](https://www.obsidian.net/news/obsidian/obsidian-entertainment-announces-pentiment).

No third-party image was downloaded or relicensed in this investigation. Asset
origin, license/usage conditions and selected generation outputs belong in the
implementation's actual asset manifest.
