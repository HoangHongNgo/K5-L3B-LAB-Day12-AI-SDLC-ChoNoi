"""Readable per-item fixtures for the gather, cooking and scenario regressions."""

from collections import Counter


def fresh_items(kinds):
    return [{"id": f"I{n}", "kind": kind, "fresh": 100} for n, kind in enumerate(kinds, 1)]


def stocked(**counts):
    return fresh_items(kind for kind, count in counts.items() for _ in range(count))


def kinds(items):
    return [item["kind"] for item in items]


def counts(items):
    return dict(Counter(kinds(items)))


def after_tick(items, tuning, phase="gather"):
    rate = tuning["freshness"][phase + "_decay_per_s"]
    return [dict(item, fresh=item["fresh"] - rate / tuning["tick_hz"]) for item in items]


def opening_price(dish, tuning):
    # At the first cooking interaction the kitchen has already aged full-fresh stock by one tick.
    freshness = tuning["freshness"]["initial"] - tuning["freshness"]["quan_decay_per_s"] / tuning["tick_hz"]
    return int(tuning["menu"][dish]["price"] * freshness / 100)
