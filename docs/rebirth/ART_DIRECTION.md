# Rebirth art direction — implementation decision

The baseline is the playable Pompeii build at ad979b4. Its code-drawn roofs,
flat pale ground and large objective card make the world read as a schematic.
The redesign needs material, character expression and spatial atmosphere before
more interface chrome. Existing baseline screenshots are preserved separately.

| Proposal | Visual approach | Feasibility and risk |
|---|---|---|
| A — Mediterranean illustrated world | Warm illustrated architecture, visible plaster/stone/tiles, ochre and olive color, painted interiors and expressive character portraits | High-impact original raster assets can fit the existing authoritative map; manageable lighting/scale consistency. |
| B — 2.5D isometric town | Modular depth-sorted buildings, multiple sprite facings, tile-based movement | Strong spatial promise, but requires reprojection, many cohesive assets and new occlusion/collision testing; high migration risk for this session. |
| C — Illustrated narrative adventure | Layered panoramic scenes with large portraits, material-inspired dialogue and scene transitions | Strong conversation clarity and feasible polish, but needs visible embodied traversal to preserve the world's spatial agency. |

## Chosen direction

Choose A with C's restrained conversation composition: a textured Mediterranean
illustrated town, layered actor sprites, intimate painted interiors and large
original portraits. Preserve the existing world-coordinate contract and improve
the custom Canvas renderer. Phaser/Pixi/Godot feasibility was checked against
current official docs in ART_RESEARCH.md; no dependency migration is justified
merely to obtain features this renderer can already supply.

Use original generated raster artwork for environment and character assets.
Keep people and transactions out of background paintings: all visible characters
come from actual simulation state. Architecture is evidence-informed fiction,
without a claimed surveyed scale. No existing game's artwork is reused.

Palette: sun-warmed ochre plaster, deep indigo shadows, coral roof tile, olive
leaves, faded vermilion wall paint, cream linen and bronze accents. Light falls
consistently from upper left. Avoid beige-on-beige text, glossy cards, neon AI
visuals, modern props and UI baked into paintings. Interface text remains HTML.

The game should use most of the viewport. Keep one short current lead and a
small clock/purse; place inventory, journal and research behind intentional
controls. Choices name their real costs and consequences. Important aftermath
uses actual events, a portrait and a short line rather than a JSON receipt.

## Pipeline and review gates

All selected generated assets are copied into kalends_rebirth/static/assets.
ASSET_MANIFEST.json records origin, generation-brief summary and use; no asset is left
only in a tool's private output folder. Portrait atlases are clipped at render
time, not edited into undocumented derivatives. Web display can scale images;
original generated outputs remain available in the project.

Review actual title, street, dialogue, inventory/journal, interior, consequence,
return and World Lab screens. Capture desktop and mobile. Fix observed issues
in at least two separate passes. Baseline/new comparisons are screenshots of
running software, not concept images presented as gameplay.
