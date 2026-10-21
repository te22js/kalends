# Immersion technical art conventions

The district is an original, stylized Roman-inspired environment built around
the existing simulator's schematic geometry. It is not a surveyed Pompeii
reconstruction. Rendered furnishings do not add economic inventory.

- **Coordinates:** right-handed Y up; meters. `sceneX=(simX-800)*0.02`,
  `sceneZ=(simY-415)*0.02`. The main street is32×2.6m. Adult characters should
  be1.7m tall after normalization. Do not reinterpret simulator coordinates
  as meters or change server navigation to fit a prettier model.
- **Palette/materials:** lime plaster, warm ochre and faded red dado; grey-beige
  paving; weathered brown timber; muted terracotta (explicit rust tint on light source tiles); restrained cream/russet
  fabric. Poly Haven CC0 diffuse/OpenGL normal/ARM maps are embedded without
  modifying the original JPGs. Warm material factors adapt those materials to
  this composition. Gloss is reserved for water/bronze. Plaster roughness.9,
  stone.9, wood.8, terracotta.85–.9; normal intensity.32–.55.
- **Light:** root client uses warm directional sunlight from the southwest and
  cool desaturated ambient fill. Preserve visible eave/arch/pottery contact
  shadows; avoid black ambient interiors and washed-out white walls. Optional
  SSAO is a quality setting, not a substitute for readable framing.
- **Camera:** elevated three-quarter camera from positiveZ toward north; FOV45,
  default distance13.5m, height factor.72/horizontal factor.65, default yaw24°.
  Semi-orbit is limited to[-35°,55°] so authored cutaways remain meaningful.
  Follow uses exponential dt smoothing rate5; conversation distance multiplies
  by.82 with smoothing rate4. Do not move scene geometry to fit the camera.
- **Movement presentation:** walk115simunits/s=2.3m/s, run185=3.7m/s;
  NPC interpolation100=2m/s. Actual displayed velocity selects the clip and
  server updates remain authoritative. These are animation/presentation speeds,
  not a permission to change committed simulation outcomes.
- **Actual quality settings:** balanced1024 shadow map/MSAA2; high2048 shadow
  map/SSAO8; low.75 render resolution without shadows. Reduced motion remains
  available. These settings describe implementation, not measured60FPS results.
- **Visible consequences:** `market_cart` contains child `market_cart_cargo`,
  six individual sack meshes. Keep cargo enabled only during authoritative
  unresolved/committed story stages; hide after resolution, leaving the empty
  cart. It sits in a recessed nonwalkable apron at presentation position1020,325,
  near Marcus; that offset is not an authoritative world-cart position.
- **Animation:** use genuine skinned character clips and cross-fades; actual
  displayed velocity selects locomotion. Model normalization belongs on a
  parent transform, not the skeleton. Ground pivot must stay at feet. NPC
  work/dialogue poses must be tied to reported activity/actual conversation.
- **Geometry:** modeled stone pavers and beveled masonry, continuous plaster
  facades, arch voussoirs, profiled columns, curved two-shell roof tiles, lathed
  hollow-rim amphorae, planked shutters, striped sagged cloth, recessed oven
  and work shelves. Original buildings are composite authored meshes, not
  standalone primitive placeholders. Vertex data is indexed and material-batched.
- **Navigation contract:** public floors and15-unit-inset room floors stay
  clear. Decorative counters, oven and storage are recessed beyond the clear
  floors. The fountain basin sits at the north margin beside the named water
  point, not across the server's unobstructed street. Curbs/thresholds are
  nonblocking visual margins. Client physics must not pretend undisclosed
  furniture collision is authoritative simulation geometry.
- **District context:** an undulating warm earth mesh and raised lot foundations
  close every exposed floor edge; background Roman-inspired roof silhouettes
  provide depth. These are noninteractive scenery outside the approved floors.
  Client framing should use `playable_scene_bounds`, not the full terrain AABB.
- **Interior wall visibility:** `ID_cutaway_walls` is a separately authored
  alternate mesh for each room, with capped.82m sides and.75–.82m south walls;
  the northern backdrop stays2.6–2.72m. Hide all cutaway groups initially, then
  replace `ID_walls` only for the room the player actually occupies. Do not
  render both variants together. Hide `bakery_frontage_sign` while inside the
  bakery; it parents both wood board and lettering. Bakery cutaway doorposts
  stop at.98m and omit the overhead lintel/sign to keep player heads visible.
  The northern wall includes a real recess revealing the oven. Door openings
  and navigation stay identical.
- **Visibility:** `bakery_roof`, `fullery_roof`, `thermopolium_roof`,
  `household_roof` are independent GLB nodes. Hide the current room's roof for
  a cutaway; keep the front doorway/threshold legible. South rooms use low
  camera-facing walls; the bakery has an open taberna front.
- **Initial budgets:** under150k original environment triangles, about200 active
  material batches before client batching (stored cutaway alternatives are
  mutually exclusive with their original walls); no per-frame geometry rebuilding.
  Mobile/reduced presets may omit decorative shadows and use lower resolution.
  These are asset budgets, not measured60FPS claims. Actual GLB bytes, bounds,
  nodes, material batches and triangles are in `assets/environment/scene_manifest.json`.

Rebuild with `python3 scripts/build_immersion_scene.py` (numpy and Pillow). The
script is deterministic for seed79 and does not access the network or mutate
any simulator, journal, research artifact or legacy presentation asset.
