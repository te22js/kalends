"""Context-keyed deterministic randomness.

Instead of one sequential RNG stream, every random decision is a pure function
of (seed, context labels): det_rand(seed, "gossip", tick, speaker, listener).

Why this matters (not just style): with a sequential stream, deleting one event
shifts every later draw, so a counterfactual run ("same world minus event E")
diverges everywhere for spurious reasons. With context-keyed draws, two runs
differ ONLY through genuine causal channels (beliefs, positions, tells that
actually depended on E). This is what makes the counterfactual analysis in
kalends/counterfactual.py meaningful.
"""
from __future__ import annotations

import hashlib
from typing import Sequence, TypeVar

T = TypeVar("T")


def det_rand(seed: int, *context) -> float:
    """Uniform [0,1) determined by seed + context labels."""
    key = f"{seed}|" + "|".join(str(c) for c in context)
    h = hashlib.sha256(key.encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64


def det_choice(seq: Sequence[T], seed: int, *context) -> T:
    return seq[int(det_rand(seed, "choice", *context) * len(seq))]


def det_randint(lo: int, hi: int, seed: int, *context) -> int:
    """Inclusive range [lo, hi]."""
    return lo + int(det_rand(seed, "randint", *context) * (hi - lo + 1))


def det_shuffle(seq: Sequence[T], seed: int, *context) -> list[T]:
    return sorted(seq, key=lambda x: det_rand(seed, "shuffle", x, *context))
