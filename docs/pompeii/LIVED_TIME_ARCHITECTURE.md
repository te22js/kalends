# Lived time and exact scheduled simulation

Pompeii separates presentation from computation. A montage can show highlights
while the world scheduler executes all supported scheduled transitions. Skipping
animation does not authorize skipping decisions, messages, deadlines, or costs.

`kalends.pompeii.temporal.EventClock` implements established discrete-event
simulation with a heap. This is an engineering implementation, not a claim of a
new scheduling or time-compression algorithm. Exactness applies to a world whose
autonomous changes are represented by scheduled tasks; continuous dynamics or
unscheduled per-minute side effects are outside that claim.

## World integration API

```python
from kalends.pompeii.temporal import EventClock

clock = EventClock(now=0)
clock.schedule(17, "arrival", {"agent": "Livia"})
next_minute = clock.peek()  # int, or None
stats = clock.advance(1440, world.on_task, mode="compress")
saved = clock.snapshot()
restored = EventClock.from_snapshot(saved)
```

Tasks have `due`, `sequence`, `key`, `kind`, and JSON-object `data`. Due times and
clock times are nonnegative integer minutes. Scheduling before the current clock
time is rejected. A handler can schedule another task at the same minute; stable
sequence order ensures that the new task runs after previously queued tasks at
that minute. Internal task records and serialized data are immutable; returned
task dictionaries and queue inspection views are detached copies. Snapshots save
both the pending heap and the next sequence identity for stable replay.

Handlers receive `executed_at` and `lateness` in addition to the task record and
must use `clock.now` as actual execution time. Exact modes execute at `due`;
switching from a delayed naive run can leave overdue tasks, so such mixed-mode
runs are not part of the exact-equivalence comparison. Advances include events
due at the target minute. Calling advance again does not replay consumed events.

## Three execution modes

* `live` scans each integer minute from the current minute through the target,
  checking the heap on every iteration. It calls the handler only for due tasks.
* `compress` jumps between queued event times, draining all tasks at each time,
  and finishes at the requested target. It preserves intended task timing and
  sequence exactly, including dynamically scheduled work.
* `naive`, with a default 60-minute coarse interval, rounds execution upward to
  the next absolute coarse boundary. It preserves task count and order within a
  bin rather than deleting difficult tasks. Reactions schedule relative to their
  delayed execution time, so deadlines, beliefs, costs, and subsequent behavior
  can diverge. Tasks whose rounded time exceeds the target remain pending.

Returned statistics are `wall_seconds`, `ticks_visited`, `dispatched`,
`idle_skipped`, `total_lateness`, and pending count, together with mode/start/target.
The live reference visits `target-start+1` minutes; compression counts distinct
execution minutes plus the target if it has not already visited it. Empty minutes
never trigger a world callback in any mode. Scheduler work and montage rendering
are measured separately.

Exact equivalence follows from the shared queue and handler, not from a learned
prediction of what can be omitted. At each earliest queued minute the two exact
modes dispatch the same stable sequence, receive the same state, and therefore
enqueue the same later work. Minute scanning does nothing between those times.
This argument requires deterministic handlers and no external input during an
advance. Messages, inspections, decisions, opening hours, and deadlines must be
explicit tasks if they can affect the world. A continuously changing quantity
needs a valid analytical elapsed-time update or additional scheduled transitions;
it cannot be silently assumed constant. Presentation interpolation does not add
authoritative world changes.

## Evaluation protocol (to be frozen before heldout execution)

The temporal benchmark will instantiate the actual `PompeiiWorld`, including its
real decision, message, relationship, and commitment transitions. Development
seeds are 30000–30009. Reserved heldout seeds are 70000–70029. Each mode starts
from a fresh matched seed at horizons of 1, 7, and 30 days. Runtime runs and Python
traced-allocation peak runs are separate; traced allocations are not process RSS.
The report will compare full state and semantic projections for decisions,
beliefs, relationships, commitments, and events, alongside executed event counts.
Live/compress equivalence is an exact equality requirement, not a mean score.
Naive divergence is reported honestly along with timing and fidelity. The model,
benchmark source, and projection definitions must be frozen before heldout runs.

The actual world exposes `PompeiiWorld(seed=...)`, `.clock`, `.on_task`, and
`.fidelity_state()`. The benchmark adapts its accounts, facts, positions, flags,
memories, authoritative locations, and queue into `state`, with separate
`decisions`, `beliefs`, `relationships`, `commitments`, and full ledger `events`.
An explicit `temporal_projection()` is also supported. The measured world has six
citizens and a 32-record ordinary memory capacity. No dummy town is substituted
if this interface is absent. Each horizon/mode gets its own fresh world. Mode execution
order is shuffled by a separate deterministic seed; it does not consume world
random draws. Each cell has five fresh untraced runtime runs (the median is
reported) and one separate traced repeat, whose projection hashes must agree.
One-time Python module import is excluded from all modes; construction is timed.

The state projection also checks ordinary and consolidated memory buffers
separately, disclosed event IDs, and the account-parent index. Additional
projections distinguish each agent's ordered action-only and action/prediction histories (without
timestamps, event IDs, or inter-agent interleaving), terminal belief values, and
executed outcome metrics (without minute/event/decision counts). A difference in
dated records alone is never described as a changed action or economic result.

Every benchmark world executes the same legitimate player prefix: walk to the
bakery and accept Felix's delivery through the game's validated interaction.
Delivery remains open until its scheduled deadline, with no subsequent player
procurement. This exercises an actual missed-promise/commitment/trust transition, rather than
reporting equality of empty commitment and relationship structures. The prefix
uses no evaluator truth or adaptive player policy and is included in runtime.
The first passive development pilot is preserved separately; the registered
study uses this declared prefix and five timing repeats.

The benchmark calls `clock.advance` with the game's actual `on_task` handler.
The UI wrapper's `time_advanced` record includes the selected presentation mode,
so that wrapper is excluded from this computation-only equivalence comparison.
Autonomous model events are compared in full, including their exact timestamps;
neither game decisions nor private memories are removed from the comparison.

```sh
python -m kalends.pompeii.temporal_bench --phase development
# After development and source freeze:
python -m kalends.pompeii.temporal_bench --register
python -m kalends.pompeii.temporal_bench --phase heldout
```

Registration captures the complete Python source fingerprint. Heldout execution
refuses a changed source/protocol or an existing output path. The final report
checks the fingerprint again. Raw JSONL records include seed, horizon, mode,
projection hashes, exact comparison details, actual event/decision counts,
scheduler work, untraced timing, and separately measured traced allocation peak.
Uncertainty resamples matched seeds, separately by horizon; individual decisions
are not independent samples. Binary exact fidelity is a strict check and can be
lost from timing differences alone, so per-projection differences are reported
alongside the plot rather than interpreted as a graded outcome-quality score.

## Development evidence and limits

`results/pompeii/temporal_development_v1` preserves the initial passive pilot
(one timing run per cell). `temporal_development_v2` uses the declared promise
prefix and five fresh timing runs. It contains 450 runtime runs and 90 separate
traced runs over ten development seeds. All 30 live/compress pairs match every
projection exactly, and every repeat is deterministic. Naive execution differs
in dated belief/decision records, events, and state in all 30 cells; its final commitment
and trust results match in this fixed missed-promise scenario. This does not
establish that every possible coarse schedule must change a final commitment.

| Development horizon | Compressed mean paired speedup | Live mean time | Compressed mean time |
| --- | ---: | ---: | ---: |
| 1 day | 1.103× | 0.478 ms | 0.435 ms |
| 7 days | 1.209× | 2.513 ms | 2.078 ms |
| 30 days | 1.185× | 10.415 ms | 8.791 ms |

These are development measurements on this host, not heldout estimates or
browser frame rates. Absolute runtimes are small and susceptible to scheduling
noise. At 30 days, the mean minute checks fall from 43,191 to 528.3, but event
execution still dominates much of the work. Mean traced allocation peaks are
approximately 620 KB in either exact mode, so no substantial memory reduction is
claimed. Peaks cover fresh world construction and execution; serialization of
benchmark comparison projections and plotting are outside the traced interval.
The ledger remains a growing operator archive. Ordinary local memory is
32 records plus a separate eight-record bounded literal consolidation store;
this scheduler evaluation does not claim a 32-record bound on total world state.

The benchmark exercises a single scripted promise outcome. It does not evaluate
adaptive human play, all possible branches, long-term economic realism, dialogue
quality, true historical reconstruction, or an optimum policy. Exactness here
means equivalence to the explicit scheduled reference model, rather than fidelity
to an independently observed historical city.

## Frozen heldout result

The final runtime was frozen at Git commit
`a024da5768f2eb1deaae3b89c586a56a574e3adb`. Local prospective registration is
`results/pompeii/temporal_preregistration.json`; the complete runtime fingerprint
is `3e99eb91af66bf6fcb61ea57d7ce714ba008807c12ad464910677f1c20d22dbd`.
The final development rerun (`temporal_development_final`) passes all checks on
that source: 450 runtime runs and 90 traced runs. Earlier v1–v4 pilots remain
intact; v3 added semantic projections, and v4's source guard correctly refused
success after concurrent source edits (`source_unchanged=false`). None is
substituted for the frozen heldout evidence.

`results/pompeii/temporal_heldout` contains 270 cells: 30 fresh seeds × three
horizons × three modes. Five fresh runtime repeats per cell give 1,350 runs;
270 separate traced runs bring the total to 1,620 world runs. The pipeline took
29.10 seconds. Both the final development and heldout source guards pass, and
all runtime and traced repeat hashes agree. Measurement Python is 3.12.14 on
Darwin/arm; no language-model calls are involved.

Compression exactly matches the minute-scanning reference in all 90 paired
seed/horizon comparisons across all ten declared projections. The table reports
the mean paired ratio of per-cell median runtimes. Intervals are descriptive
95% paired-seed percentile bootstrap intervals (30 independent seeds at each
horizon), rather than treating repeated timings or decisions as independent.

| Heldout horizon | Compression speedup, mean [95% CI] | Live mean time | Compressed mean time | Naive mean speedup |
| --- | ---: | ---: | ---: | ---: |
| 1 day | 1.117× [1.091, 1.141] | 0.454 ms | 0.407 ms | 1.113× |
| 7 days | 1.210× [1.195, 1.227] | 2.449 ms | 2.025 ms | 1.216× |
| 30 days | 1.195× [1.185, 1.206] | 10.429 ms | 8.728 ms | 1.235× |

Naive execution loses exact dated-record fidelity in all 90 comparisons.
However, its per-agent **action-only histories, terminal belief values,
executed terminal outcomes, commitments, and relationships match in all 90**.
Per-agent action/prediction histories differ in 16/30 seeds at seven days and
16/30 at thirty days; those differences are prediction values, not action
strings. There is no observed terminal economic harm from this coarse baseline
in the registered scenario. Thus the experiment demonstrates preserved detailed
chronology and evidence under exact scheduling, not an outcome advantage over
naive execution. The lower panels of the fidelity plot make this negative result
explicit rather than presenting every timestamp/ID difference as a changed act.

At thirty days, exact minute visits fall from 43,197 to a mean 527 while both
exact modes dispatch a mean 643.27 tasks and emit a mean 637.4 events. All three
modes have equal matched task-dispatch counts; naive runs emit fewer resulting
events (mean 619.67) as handler-level information states differ. No queued task
is dropped as a baseline shortcut. Mean Python traced allocation peaks are
621,559 bytes live and 621,427 bytes compressed: this supports no substantial
memory-saving claim.

The heldout raw JSONL SHA-256 is
`a95ea38434f077d7ba8eedf72eb85c24856105cf9fd5ec201ce6d04ebaaac4ee`.
`manifest.json` records every runtime file hash; `worlds.jsonl` contains the
actual matched-seed records; `summary.json` contains exact comparisons and seed
intervals. `fidelity_speedup.png` and `.svg` were generated from saved data using
host Matplotlib without rerunning a world. The separate `plot_manifest.json`
documents that render, since measurement Python has no Matplotlib installed.
The original immutable measurement summary therefore correctly records that
plotting was unavailable in its own Python environment.
