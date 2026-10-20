# Pompeii: a life that leaves traces

This build is a small historical-fiction game, not a complete ancient city.
Its player is Aelia, a fictional freedwoman with six coins, no flour, and a need
for dependable work. The first playable question is concrete: will she obtain
four flour units and keep a promise before dusk, and what will that choice cost
her later? The environment is a schematic Via dell'Abbondanza district with
three attested building anchors and one explicitly fictional bread counter.
The [source ledger](HISTORICAL_SOURCE_LEDGER.md) separates archaeology,
interpretation, speculation, and fiction.

## What changed from Genesis

Genesis remains available through its original server and artifacts. Pompeii
adds a spatial player, streets and doors, cutaway interiors, movement duration,
proximity permissions, owned resources, paid shifts, personal promises, household
service, repeat orders, information sales, and a separate research view. The new
Canvas frontend uses original code-drawn masonry, plaster, pottery, work surfaces,
roof tiles, and tunic sprites. It has no external asset download or runtime
JavaScript dependency. This choice makes the slice launchable offline and keeps
rendered people tied to actual simulation positions. It is not a surveyed 3D
reconstruction or a production art pipeline.

The old ledger, WorldState projection, Experience records, keyed randomness and
GenesisEconomy remain the underlying primitives. A new event scheduler replaces
the old tick loop for this district's explicitly scheduled dynamics. Existing
Genesis results are not rerun, relabeled, pooled, or overwritten.

## The screen is a place

The town occupies the screen. The clock, purse, flour, objective and controls
sit above it. Clicking a street makes Aelia follow an authoritative route;
clicking a building walks through its doorway. WASD/arrows move within legal
street/interior areas. E opens the nearby character conversation. The map can
be panned with Shift-drag, zoomed, recentered, or viewed through the minimap.
Entering an interior removes its roof and shows its actual occupants. NPCs
inside other buildings are not decorative pedestrians on the street.

A contextual button names what can be done here. Character conversations carry
role, legal/social position, and locally visible trust. Natural-language input
produces a review card. Confirmation, proximity checks, resource checks and the
canonical ledger determine the result. The offline grammar is deliberately
limited: it is useful for promises, purchasing, work, service, inspection,
claims, information sales, and questions. It is not unrestricted roleplay.

The journal contains witnessed events and the player's own institutional
transactions. Arriving at a place does not reveal its unwitnessed past. A
character may describe a literal retained shared experience when approached;
that differs from an operator recovering the complete archive. Private starting
accounts are redacted in game mode. World Lab deliberately exposes operator
state and actual historical reruns; it is behind the journal's separate entry.

## Three connected systems

| System | Actual resource or restriction | Cross-system consequence |
|---|---|---|
| Work and commerce | Cash, flour, finite merchant inventory/shared supply, changing price, paid shifts, elapsed minutes | A wage finances delivery; a purchase consumes stock another agent might need. |
| Commitments and patronage | Four-unit flour promise, deadline, household eight-coin advance, two-hour service, affiliation | Keeping delivery raises Felix's trust; missing delivery or service changes later relationships and reputation. |
| Information and verification | Retained dated reports, claimed origin, finite memory, one-coin inspection, recipient-specific willingness to pay | A useful report can finance a promise; stale or contradicted reports can change inspection spending, decisions and trust. |

There is no universal objective function. A household advance gives more cash
but creates a durable affiliation and a real future time obligation. A wage
costs present time and is limited per day. Brokerage can be quick, but requires
someone with a usable report and another person willing and able to pay; it can
fail when the recipient already knows it, the report is not useful, or trust is
too low. Morning route examples are demonstrations, not a claim of balanced
optimal play across all seeds or horizon lengths.

## Characters and plans

Six fictional NPCs have different cash, inventory, occupations, caution, daily
locations, duties and information valuations. Marcus maintains a speculative
buffer. Felix needs flour for bread, Sabina has a smaller food-counter demand,
and Lucius secures household supplies. Dama carries reports along a household
routine. Chreste is an enslaved workshop worker; a paid help shift is funded by
the household, not an invented independent wage account for Chreste. Enslavement
is represented as coercion and restricted social position, not as a bonus.

Procurement uses each character's retained knowledge and owned accounts.
Uncertainty can trigger costly inspection. A sufficiently trusted disruption
report can cause a cautious character to defer and retry once. Low balances
revise the displayed immediate goal toward protecting liquidity; low trust
revises it toward verification. These are authored policies with state-dependent
plans, not learned personalities or conscious people. Routine schedules remain
simple, and there is no claim of open-ended social intelligence.

## Time, absence, and narrative

LIVE sends one simulated-minute request every 1.7 foreground seconds while it
is enabled. Movement and shifts also advance time. COMPRESS executes thirty
world minutes using exact event dispatch. MONTAGE advances to the next scheduled
change and displays selected actual events. SKIP can reach the next change or
simulate a week. Browser visibility changes stop LIVE; closing the app does not
pretend a server continued running. An explicit skip is how to return after a
long absence in this local build.

The narrative selector surfaces actual promise settlements, paid work, reports,
relationship checks and opportunities. It neither creates a hidden outcome nor
adds an omniscient narrator to character memory. Daily flour orders can reopen;
physical stock, balances, trust, affiliations, outstanding and settled obligations
continue. Significant experiences use an eight-record literal consolidation
store alongside the ordinary memory buffer. Institutions and the growing audit
ledger are separate from recall.

## Validation and next product gates

Automated scripts exercise three solutions, a seven-day absence, memory-based
return dialogue, durable save/reload and an executed removed-action alternative.
Fresh studies measure computation and physical/social outcomes. The
[playtest protocol](PLAYTEST_PROTOCOL.md) is a future independent test, not a
completed human study. No claim of fun, retention, historical teaching efficacy,
or commercial demand is supported yet.

This slice lacks voice, autonomous LLM dialogue, complex interior permissions,
continuous off-screen movement, a large economy, save migration across changed
runtime versions, and a complete life arc. A production successor needs specialist
historical review, uncoached playtests, better navigation/accessibility, more
expressive art and daily plans, content tools, and evidence that another day is
worth playing. The full city, multiplayer, public UGC, cognitive effects and
neural interfaces remain future work rather than features hidden in this build.
