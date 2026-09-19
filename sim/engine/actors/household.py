"""`Household`: the founder and family as an economic actor.

Money, staff, knowledge, standing and every cache keyed off any of them
live here, not on the `Sim` god object, so something other than the
founder's own household - a government, a rival household, a firm - can
someday own a purse and a stock of knowledge of its own without needing a
second `Sim`. See `docs/architecture/HOUSEHOLD_EXTRACTION.md` for the
design and `docs/architecture/SIM_STATE_INVENTORY.md` for the measured
field-by-field classification this class is built from.

WHAT DID NOT MOVE HERE, ON PURPOSE:

  - WORLD state (the calendar year, population, wage/price indices) stays on
    `Sim`, because it belongs to the world whoever is playing, not to any one
    actor in it.
  - SCENARIO state (the loaded tree, the civilisation record, `goal`, `fog`,
    `policy`, ...) stays on `Sim` too - it is how this session is configured,
    not what this household owns. `policy` in particular reads as household
    state (it is this household's own automation switches) but one of its
    keys, `auto_court_heir`, is written for succession after a mortal owner's
    death, so the whole dict stays with the other founder-biographical fields
    below rather than being split for one key. `goal` reads the same way
    (SIM_STATE_INVENTORY.md flags it as a real fork - a win condition is
    naturally a property of whoever is playing, not of the world - but that
    is a design question for when a second actor exists to make it concrete,
    not something this extraction should guess at) and stays put along with
    its cache, `_goal_closure`/`_goal_critical_floor`, which is keyed on
    `self.goal` and `self.nodes`, not on anything a household owns.
  - Eight fields the inventory calls out by name as biographical to one
    mortal person, with no meaning for a firm or a government as written:
    `founder_alive`, `life_left`, `dead_reason`, `director_hours_spent_founder`,
    `hours_this_year`, `living_cost_paid`, `policy` (see above), and
    `last_patron_death`. Moving these would mean designing what death,
    personal hours or "a patron" mean for a non-person owner, which is
    guessing at a design this codebase has not made yet. They, and the three
    INTERNAL caches that exist only to remember when/how old the founder was
    when they died (`_founder_death_aged`, `_founder_death_year`,
    `_founder_death_cache`), stay on `Sim`.

WHAT DID, INCLUDING THREE FIELDS THE INVENTORY FLAGGED AS ONLY ARGUABLY
BELONGING HERE (`granted`, the `trades_*` trio, `shortages`,
`_material_stock_ledger`): the inventory classifies all four as HOUSEHOLD (or,
for `_material_stock_ledger`, as an INTERNAL cache keyed off household state)
today, and flags a *future* fork - `granted` mirrors a civilisation-wide fact
per `Sim` rather than truly varying per actor; a trade taught into existence
might reasonably become available to every actor once the society has it;
`shortages` is a diagnostic nobody's decisions read. None of those forks
exist yet, so the obvious move - not a redesign - is to move them with
everything else classified the same way and let whoever builds the second
actor resolve the fork then, with a second example to design against instead
of a guess.
"""
import collections
from collections import defaultdict
from typing import (Any, Callable, DefaultDict, Dict, Iterable, List,
                     Optional, Set, Tuple, TypedDict)

from ..economy import _InvalidatingSet, _InvalidatingDict


class MineWorking(TypedDict):
    """One entry of `self.mines`, below - a single owned mining operation.
    Fixed at exactly these five fields: the only place any of these dicts is
    built is `commission_mines()` (economy_mining.py), which always writes
    all five, and every read site across economy_mining.py reads only
    `material`, `capacity` and `intensity_yrs` (`opened_year` and
    `capex_paid` exist for save/display, not for the mining arithmetic
    itself) - none of them, in that file or anywhere else, adds a sixth
    key. Contrast `ActiveProjectState` below, which stays a plain mapping
    because ITS dicts genuinely do grow new keys at runtime."""
    material: str
    capacity: float
    opened_year: int
    capex_paid: float
    intensity_yrs: float


# `self.active[node_id]`'s value type. NOT a TypedDict, on purpose, unlike
# `MineWorking` just above: `core_step_phases.py` alone (not owned by this
# task) writes more than a dozen additional keys into one of these over a
# project's life - `pool_total_this_year`, `blocked_on_trades`,
# `stalled_years`, `waiting_on_money`, `cost_left`, and others - none of
# them present at creation (`dict(ph_left=..., yrs=0.0, spent=0.0)` in
# `projects_starting.py`). A TypedDict would either have to declare all of
# them NotRequired (in which case it says nothing a plain mapping does not
# already say) or would be lying about which keys are actually there at any
# given moment. This is exactly the "open and data-driven" case the task's
# own instructions distinguish from `MineWorking`'s fixed one.
ActiveProjectState = Dict[str, Any]


class Household:
    """The founder's household: money, staff, knowledge, plant and standing.

    Every field below was, until this class existed, a plain attribute of
    `Sim` itself - see core.py's own history (git blame) for the original
    site of each one, and SIM_STATE_INVENTORY.md for why each one is here and
    not on `Sim`. The grouping and the comments are carried over unchanged;
    only `self.` now means "this household" rather than "this whole game".

    THE PARAGRAPH BELOW DEFENDS THE CURRENT ENCODING; Complaints/57 ARGUES
    AGAINST IT. Read both. The complaint accepts that "this has never
    happened yet" is real information worth keeping and objects to the
    channel it travels through, which is whether an attribute exists at all:
    invisible at the definition site, indistinguishable from a field somebody
    forgot, reconstructed through `getattr(obj, name, default)` at every read
    site, and enforced by the comment you are reading plus one tool nobody
    runs by accident. It also notes that the usual reason to keep an
    absence-means-something encoding, that old saves are already written that
    way, is explicitly not a reason in this project (CLAUDE.md SS3.5). Left
    as is for now by decision, not by oversight.

    A NOTE ON WHAT IS *ABSENT* HERE, NOT JUST WHAT IS SET: several fields
    below are deliberately never assigned in `__init__` at all, and are
    created lazily, the first time some method does
    `getattr(self.household, "name", default)`. That is not an oversight -
    see the long comment inside `Sim.__init__` (core.py) that this class's
    own `__init__` continues, and `sim/ARCHITECTURE.md`'s account of the one
    time promoting one of these to a real `__init__` attribute passed the
    whole test suite while silently breaking save-file semantics. A save
    file missing one of these fields means "this has never happened yet", not
    "zero", and `SAVE_FIELDS` (sim/engine/proto/saveload.py) is the
    authoritative list of which ones. The `Sim` properties that expose these
    fields to the world outside the engine (protocol, save/load, the CLI,
    the tests) are written to preserve that: `self.household.name` raises
    `AttributeError` exactly when the field has never been touched, and never
    supplies a default of its own, so `getattr(sim, name, default)` still
    sees the field's true, possibly-absent, state.
    """

    def __init__(self, starting_capital: float,
                 operating_changed: Callable[[], None],
                 active_changed: Optional[Callable[[], None]] = None,
                 workforce_changed: Optional[Callable[[], None]] = None) -> None:
        """`starting_capital`: this household's opening purse, in the
        civilisation's own currency and price level - computed by the
        caller (today, `Sim.__init__`, from `cfg["start_capital"]` and
        `price_index`) rather than here, so this class does not need to know
        the shape of a run's configuration dict to be constructed. A firm or
        a government will fund itself differently; nothing about `Household`
        should have to change for that.

        `operating_changed`: a callable invoked after every mutation of
        `self.operating` (see the `_InvalidatingSet` class, economy.py, for
        the full reasoning). It is passed in rather than looked up on `self`
        because the cache it invalidates (`_cap_factor`, `_operating_ver`)
        lives on THIS object, but the method that owns the invalidation
        logic (`Sim._operating_changed`, in `EconomyMixin`) stayed on `Sim`
        along with every other piece of the engine's actual behaviour - this
        extraction moved the DATA a household owns, not the RULES the engine
        applies to it. See HOUSEHOLD_EXTRACTION.md section 2 for why call sites are
        rewritten explicitly (`self.household.x`) rather than forwarded
        through `__getattr__`, and why that same reasoning keeps the engine's
        methods where they are.
        """
        # -- MONEY, AND THE TWO COUNTERS EVERYTHING ELSE'S CACHE INVALIDATION
        #    KEYS ON -------------------------------------------------------
        # AT THIS SOCIETY'S PRICES, like everything else you will spend it on.
        # See core.py's Sim.__init__, where `starting_capital` is computed,
        # for why a kit is priced where you are rather than at a single
        # global rate.
        self.capital: float = float(starting_capital)
        self._done_ver: int = 0
        self._operating_ver: int = 0
        self._active_ver: int = 0
        self._workforce_ver: int = 0
        self._inst_units_ver: int = 0
        self.done: Set[str] = set()
        self._done_seq: Optional[List[str]] = None
        self._cap_factor: Optional[float] = None   # capability_factor()'s cache; see economy.py
        # [[artisan_capacity, year_it_matures], ...] usually, but
        # `labour_training.py` (not owned by this task) also appends a
        # 4-element [progress, year, trade, count] row for taught-trade
        # training, so a row's own length and field meanings vary by who
        # wrote it - genuinely heterogeneous, not a fixed record this pass
        # can name honestly.
        self.training: List[List[Any]] = []
        # Held because the SOCIETY has it, not because this household built
        # it. See the module docstring above for the `granted` fork this
        # inventory flags for whenever a second actor exists to force the
        # question of whether it should be shared rather than duplicated.
        self.granted: Set[str] = set()
        self.active: _InvalidatingDict = _InvalidatingDict(on_change=active_changed)
        self.failed_attempts: DefaultDict[str, int] = defaultdict(int)
        # YOU ARRIVE ALONE: no employees, no slaves, no household. You stepped
        # out of the future into a street in a city where nobody knows you,
        # and nobody starts already hired on your behalf. You are your own
        # only scholar (see effective_scholars) and everyone else has to be
        # found, paid, taught or bought, by you, on purpose.
        self.scholars: float = 0.0
        self.artisans: float = 0.0
        self.directors_extra: float = 0.0
        # Standing staff BY TRADE, which is what makes a smith not a scribe.
        self.employees: _InvalidatingDict = _InvalidatingDict(on_change=workforce_changed)
        # Trades this society does not have and you have taught into existence.
        self.trades_created: Set[str] = set()
        # WHEN a taught trade was first taught, and which taught trades this
        # society has since gone on to naturalise on its own - see
        # SocietyMixin.advance_society (society.py) for what moves these and
        # why. Separate from trades_created because that set answers "can
        # this be hired at all", which stays true for ever once taught, while
        # these two answer "since when" and "does the society now supply its
        # own", which trades_created alone cannot say.
        self.trade_introduced_year: Dict[str, int] = {}
        self.trades_endemic: Set[str] = set()
        self.contract_projects: Set[str] = set()   # projects staffed by the job, not by employees
        self.wages_paid: float = 0.0
        self.contract_hours: Dict[str, float] = {}         # trade -> hours bought this year, by the job
        self.commissioned: Dict[str, float] = {}           # trade -> hours bought this year, cumulative log
        self.teaching_hours_this_year: float = 0.0
        # A STANDING INSTRUCTION, NOT A ONE-TURN COMMAND. {project id: hours
        # a year} for every project the player has told step() to give a
        # fixed share of their own hours to, every year, without having to
        # retype it - this game is played over hundreds of turns. The
        # reserved key "work" is the same standing instruction for selling
        # hours as wages (see `work_trade` just below): "work" is never a
        # node id, so it can never collide with one. Read ONLY by step()'s
        # own allocator (core.py, "5. progress") and reported back verbatim
        # by `portfolio` (protocol.py) - see that loop's own comment on why
        # an explicit allocation has to flow through the exact code that
        # already decides and reports the ordinary, undirected split, not a
        # second path that could disagree with it. Hours nobody has
        # directed are untouched by this and keep being shared out by
        # priority exactly as before - a player who never calls `allocate`
        # sees no change at all.
        self.hour_allocations: Dict[str, float] = {}
        # WHICH TRADE "work" IN hour_allocations SELLS HOURS AS. A STANDING
        # hour-allocation for wages has to name one, the same way the `work`
        # command itself takes a trade argument every time it is typed; this
        # is that argument, remembered.
        self.work_trade: Optional[str] = None
        self.trade_hours_used: Dict[str, float] = {}       # trade -> hours consumed by projects this year
        self.mothballed: Set[str] = set()          # completed works you shut down on purpose
        self.forgotten: Dict[str, int] = {}              # {node: year} destroyed by a sacking
        self.opened_year: Dict[str, int] = {}            # {node: year} the doors first opened
        self.paid_towards: Dict[str, float] = {}         # {node: denarii} sunk before it stopped
        self.last_taught: Dict[str, int] = {}            # {trade: year} auto_train last taught it
        self.wages_prepaid: float = 0.0         # first-year wages `hire` already took
        # WHAT YOU ACTUALLY RUN, as opposed to what you know how to do. Revenue
        # and upkeep follow this set and nothing else does: completing the
        # research must not start paying you until you actually open the
        # doors - see is_venture and open_venture in projects.py.
        #
        # An _InvalidatingSet (economy.py), not a plain set: every .add/
        # .discard/.update/... invalidates capability_factor()'s cache
        # through the object itself. See _operating_changed()'s comment in
        # economy.py for why this is a set subclass and not a property, and
        # this class's own __init__ docstring, above, for why the callback
        # is a constructor argument rather than a lookup on `self`.
        self.operating: _InvalidatingSet = _InvalidatingSet(on_change=operating_changed)
        self.bondage_years_left: float = 0.0    # years of service still owed for a debt
        self.bondage_debt: float = 0.0
        self.credit_frozen_until: int = 0     # year until which nobody will fund new work
        # -- A HANDFUL OF "LAST TIME I SAID/DID X" TRACKERS, GIVEN A REAL
        #    STARTING VALUE HERE INSTEAD OF SPRINGING INTO EXISTENCE ON FIRST
        #    USE -----------------------------------------------------------
        # Given a real value here so every call site can read
        # `self.household.name` directly, rather than paying a
        # `getattr(self.household, name, default)` dict-and-default lookup on
        # a path that runs every single step. TRAP FOR A FIELD ALSO IN
        # SAVE_FIELDS: perf_fingerprint.py hashes that list at year 0, and a
        # save MISSING one of those fields reads back as "has never happened
        # yet" (None), a state distinct from an explicit zero or sentinel -
        # giving such a field a real value here makes year 0's hash disagree
        # with any baseline recorded before this field existed. See
        # core.py's own copy of this comment for the fuller account. Every
        # name below has been checked
        # against SAVE_FIELDS (proto/saveload.py) and is NOT a member of it;
        # the ones that ARE members (this household's `insolvent_years`,
        # `wage_hours_this_year`, `_said_deputies`, `_said_scandal`,
        # `last_withdrawal`, `_said_near_limit`, `_said_autoopen`,
        # `_said_parallelism`) are deliberately left OUT of this constructor
        # and still read through `getattr(self.household, name, default)` at
        # every call site, unchanged.
        self._staff_scale: float = 1.0            # labour.py's staff_capacity() sets the real value every step before core.py reads it; this is only the pre-first-step default
        self._spend_this_year: float = 0.0        # denarii spent this year; reset to 0.0 at the end of every step() (spend_last_year, the field that IS saved, always gets a real value from this every step)
        self._said_eminence: int = -999         # last eminence "band" warned about; -999 guarantees the first qualifying band always warns
        self._said_requisition: int = -999      # last year a state-requisition note was printed
        self._said_notice_approach: int = 0     # last state-notice "band" warned about
        self.last_military_demand: int = -999   # last year this household was subject to a military levy
        self._said_confiscation_band: int = -1  # last confiscation-risk "band" warned about
        self.gov: float = 0.0
        self.log: List[Tuple[Any, str]] = []
        self.goal_year: Optional[int] = None
        self.stalled: int = 0
        self.last_settlement: int = -999
        self.bounties_paid: int = 0
        self.bountied: Set[str] = set()
        self.total_spend: float = 0.0
        # REPUTATION: your ability to be believed and followed. Distinct from money
        # and from political protection. A man with a great reputation gets his
        # ideas adopted; a man without one gets them ignored however right he is.
        self.reputation: float = 5.0
        # SCANDAL replaces the old scalar "suspicion". Doing something a society
        # cannot explain is alarming; doing a lot of ordinary things over decades
        # is not. The old model conflated speed with sorcery, which is wrong: the
        # iPhone was astonishing in 2007 and boring by 2012.
        self.scandal: float = 0.0
        self.eminence: float = 0.0
        self.familiarity: float = 0.0      # how used to you the world has become
        self.protection: float = 0.0       # patrons, office, citizenship, priesthood
        self.bribes_ytd: float = 0.0
        self.slaves: int = 0
        self.freedmen: int = 0
        self.manumitted_total: int = 0
        self.atrocity: int = 0           # counted, never scored as a benefit
        # -- RAW MATERIAL QUANTITIES AND PLANT THIS HOUSEHOLD OWNS ---------
        self.forest_ha: float = 0.0        # coppice you own, in hectares
        self.nitre_bed_m2: float = 0.0
        self.market_pressure: float = 0.0  # how hard you have recently leaned on the slave market
        # A WORKING IS A THING: material, rated capacity, the year it was
        # commissioned, what it cost to sink, and its own depletion clock -
        # see economy.py's class comment above _workings_of(). mine_capacity
        # is a property computed from this list (economy.py), not a
        # second number kept in sync by hand.
        self.mines: List[MineWorking] = []             # your OWN workings - see EconomyMixin
        self.mine_pending: Dict[str, float] = {}      # sunk but not yet producing
        self.mine_ready: Dict[str, int] = {}        # material -> year it comes on stream
        self.mine_cost_paid: float = 0.0
        self.shortages: "collections.Counter[str]" = collections.Counter()
        self.throttle: float = 1.0
        self.binding: Optional[str] = None
        # NOTE: `done`/`granted` are populated from `civ["starting_techs"]`
        # by the CALLER (Sim.__init__), not here - the loop that does it also
        # has to raise ValueError on an unknown starting technology, which
        # needs the loaded tree and civ record this class deliberately does
        # not hold a reference to. See Sim.__init__, core.py.

    # -- FOG OF WAR: WHICH NODES ARE VISIBLE TO THIS HOUSEHOLD -------------
    # FOG IS A RATCHET, NOT A REWIND: a property, not a plain attribute, so
    # this holds regardless of WHICH code assigns to `.revealed` -
    # `load_state` (proto/saveload.py) is one such path, but this does not
    # require editing it or knowing about every future caller. Assigning a
    # smaller set here only ever grows what is already known, never
    # shrinks it: visibility is this household's own accumulated knowledge
    # of the tree, not the world's, and nothing may un-reveal a node it has
    # already discovered.
    @property
    def revealed(self) -> Set[str]:
        return self.__dict__.get("_revealed", set())

    @revealed.setter
    def revealed(self, value: Iterable[str]) -> None:
        cur = self.__dict__.get("_revealed")
        self.__dict__["_revealed"] = (set(value) if cur is None
                                      else set(cur) | set(value))
