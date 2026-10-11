"""Compact transport/cache encoding for run results.

Large piece lists (a 84-inch break lists ~250k low-pressure pieces, ~5 MB of JSON) become a
base64 bitset over all pieces: {"bits": "<b64>"} (~48 KB, smaller gzipped). Small lists stay
plain arrays. web/src/Timeline.tsx decodes both forms.
"""
import base64

import numpy as np

LIST_MAX = 2000


def pack(pieces, n):
    if len(pieces) <= LIST_MAX:
        return list(pieces)
    m = np.zeros(n, bool)
    m[np.asarray(pieces, dtype=np.int64)] = True
    return {"bits": base64.b64encode(np.packbits(m, bitorder="little").tobytes()).decode()}


def encode(run, n):
    out = dict(run)
    for s in ("paper", "real", "fixed"):
        if s in run:
            out[s] = dict(run[s], phases=[dict(p, pieces=pack(p["pieces"], n)) for p in run[s]["phases"]])
    return out
