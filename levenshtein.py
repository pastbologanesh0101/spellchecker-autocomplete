"""
Levenshtein (edit) distance, implemented from scratch with classic dynamic
programming (no library calls).

distance(a, b) is the minimum number of single-character insertions,
deletions, and substitutions needed to turn `a` into `b`.

An optional `counter` dict can be passed in; if given, `counter["calls"]`
is incremented once per invocation. This is used elsewhere in the project
purely for *instrumentation* -- counting how many full edit-distance
computations a search strategy performs, so we can demonstrate that the
BK-tree pruning genuinely does less work than brute force, not just that
it returns the same answer.
"""

from __future__ import annotations

from typing import Dict, Optional


def distance(a: str, b: str, counter: Optional[Dict[str, int]] = None) -> int:
    if counter is not None:
        counter["calls"] = counter.get("calls", 0) + 1

    a = a or ""
    b = b or ""
    n, m = len(a), len(b)

    if n == 0:
        return m
    if m == 0:
        return n

    # Single-row DP: prev_row[j] = edit distance between a[:i] and b[:j]
    # for the previous i. This is the textbook Wagner-Fischer algorithm,
    # O(n*m) time, O(m) space.
    prev_row = list(range(m + 1))
    for i in range(1, n + 1):
        curr_row = [i] + [0] * m
        a_char = a[i - 1]
        for j in range(1, m + 1):
            cost = 0 if a_char == b[j - 1] else 1
            deletion = prev_row[j] + 1
            insertion = curr_row[j - 1] + 1
            substitution = prev_row[j - 1] + cost
            curr_row[j] = min(deletion, insertion, substitution)
        prev_row = curr_row

    return prev_row[m]


# Backwards/alternate name some callers may expect.
levenshtein = distance
