"""The layout of the markets a national price is taken over, built once per set of market keys and reused.

A national price reads every remembered market each time it is asked for, and it is asked for many times a year. The
parts that depend only on which markets exist (key order, the split of a key into good and area, the grouping by good)
are kept here; the prices, weights and trade ages are read fresh on every call."""
from typing import Callable, Dict, Hashable, List, Optional, Tuple

import numpy as np

from .market_memory import KEY_SEPARATOR

KEPT_LAYOUTS = 4        # market-key sets whose layout is kept: a test or a second economy rarely needs more
KEPT_MASKS = 16         # kept-market masks per layout, one per country asked about


class MarketLayout:
    """Markets in groups by good (goods in the order the sorted keys first meet them, markets of a good in key order)."""

    def __init__(self, keys: Tuple[str, ...]):
        self.keys = keys
        ordered = sorted(range(len(keys)), key=keys.__getitem__)
        code_of_good: Dict[str, int] = {}
        codes: List[int] = []
        for position in ordered:
            good = keys[position].split(KEY_SEPARATOR, 1)[0]
            codes.append(code_of_good.setdefault(good, len(code_of_good)))
        grouped = np.argsort(np.array(codes, dtype=np.int64), kind="stable")
        self.positions = np.array(ordered, dtype=np.int64)[grouped]       # grouped place -> place in the dict's order
        self.goods = list(code_of_good)
        counts = np.bincount(np.array(codes, dtype=np.int64), minlength=len(self.goods))
        self.ends = np.cumsum(counts).tolist()
        self.keys_grouped = [keys[position] for position in self.positions.tolist()]
        self.areas = [key.split(KEY_SEPARATOR, 1)[1] for key in self.keys_grouped]
        self.good_of_place = [self.goods[code] for code in np.repeat(np.arange(len(self.goods)), counts).tolist()]
        self.masks: Dict[Hashable, np.ndarray] = {}
        self.snapshot: Optional[tuple] = None       # the prices, weights and trade ages the kept answers were computed from
        self.answers: Dict[Hashable, Dict[str, float]] = {}

    def kept(self, keep: Optional[Callable[[str, str], bool]], token: Optional[Hashable]) -> np.ndarray:
        """Which markets `keep(good, area)` accepts. With a token, the answer is kept for the next ask of that token
        (the caller promises the same token means the same `keep`)."""
        if keep is None:
            return np.ones(len(self.keys), dtype=bool)
        if token is not None and token in self.masks:
            return self.masks[token]
        mask = np.array([bool(keep(good, area)) for good, area in zip(self.good_of_place, self.areas)], dtype=bool)
        if token is not None:
            if len(self.masks) >= KEPT_MASKS:
                self.masks.clear()
            self.masks[token] = mask
        return mask

    def kept_keys(self, keep: Optional[Callable[[str], bool]], token: Optional[Hashable]) -> np.ndarray:
        """Which markets `keep(market_key)` accepts, kept by token as `kept` does."""
        if keep is None:
            return np.ones(len(self.keys), dtype=bool)
        if token is not None and ("key", token) in self.masks:
            return self.masks[("key", token)]
        mask = np.array([bool(keep(key)) for key in self.keys_grouped], dtype=bool)
        if token is not None:
            if len(self.masks) >= KEPT_MASKS:
                self.masks.clear()
            self.masks[("key", token)] = mask
        return mask


_layouts: List[MarketLayout] = []


def layout_of(keys: Tuple[str, ...]) -> MarketLayout:
    """The layout of exactly these keys in this order (most recently used first)."""
    for index, layout in enumerate(_layouts):
        if layout.keys == keys:
            if index:
                _layouts.insert(0, _layouts.pop(index))
            return layout
    layout = MarketLayout(keys)
    _layouts.insert(0, layout)
    del _layouts[KEPT_LAYOUTS:]
    return layout
