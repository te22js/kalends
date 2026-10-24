# Superseded decision-input trace

The first comparison preserved all 760 raw worlds and frozen sources. A reviewer found that the controller plan in a before-choice trace aliased the mutable controller plan, so it could show a later phase when saved. World choices, receipts and outcomes remain preserved. The corrected run in ../frozen_comparison_v2 detaches the snapshot and re-executes the same cases, seeds, candidate and endpoints. This is an audit repair, not heldout retuning. Use V2 for decision-input provenance.
