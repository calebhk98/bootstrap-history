"""What is shared about ongoing concerns/ventures across every screen that shows venture_hands() numbers: the one supervision-hours explanation, so it cannot disagree with itself from one screen to the next."""

import collections, hashlib, json, math, os, random, re
from collections import defaultdict

from ..data import *          # the shared tables and loaders
from ..data import (ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, closure,
                   critical_path, downstream_count, is_downstream, load, money_word,
                   topo_order, trade_family)
from ..fog import strip_self_play_advice

from ..core import Sim




# WHY keeping a concern open can want "2.13 craftsmen" - and it is not a
# body count either, for a different reason than _staff_fraction_note's.
# venture_hands() (projects.py) is a continuous SHARE of a scholar's or
# craftsman's YEAR that running the concern claims, scaled by how much it
# takes in - it is not even trying to count people, the way scholars/
# artisans above at least approximately are. A player who had never seen
# either explanation measured the exact case this answers: "'open' refused
# lens_grinding, which a moment earlier 'why' had said needs 2 artisans,
# over a SEPARATE figure - 2.13 craftsmen - that 'why' never showed at
# all." Read by `why`, `start`, `stuck` and `ventures` - every screen that
# shows venture_hands()'s own numbers - so the one explanation for what
# they mean cannot disagree with itself from one screen to the next.
_VENTURE_SUPERVISION_NOTE = (
    "the craftsmen/scholars a concern wants to stay open are not a "
    "headcount: venture_hands (what 'open' actually checks) is a "
    "continuous SHARE of a person's YEAR that watching it claims, scaled "
    "by how much it takes in - 2.13 craftsmen means the year-round "
    "attention of two of them plus a little over a third of a third "
    "one's, not that a person is divided. staff_needed, the crew that "
    "BUILDS it, is the one figure on these screens that really is whole "
    "people.")
