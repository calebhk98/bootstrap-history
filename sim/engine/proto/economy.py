"""Money and industry: the portfolio, capacity, mines, and the economy/changes reports read off the running Sim."""

from ..data import ANNUAL_WAGE, WAGES, trade_family

from .state import _agent_state

# WHAT EACH TRAIT IN self.w ACTUALLY DOES, in the player's own words. Event
# text has always named these fields directly - "corpus_dispersed changes
# the society: w_novelty" (see society.apply_tech_effects) - with no command
# anywhere that would tell a player what w_novelty IS, let alone what it is
# now. Two testers asked for exactly this, in separate rounds, in close to
# the same words. Not civ-specific and not a fog spoiler: these field names
# and what they do are the same across every civilisation, only the starting
# numbers differ, so naming what the mechanic does is not a leak of
# anything the founder in the story would not already understand about their
# own society.
_VALUE_MEANINGS = {
    "adaptation_rate": "how fast this society stops being alarmed by "
                       "something it has now seen for a while",
    "bribability": "how far money moves scandal down, and how much of an "
                   "opposed project's delay a bribe buys off",
    "patronage_weight": "how much protection a patron actually gives you",
    "w_commerce": "how much the state cares about work it can tax or trade on",
    "w_eminence_danger": "how dangerous standing out is here - autocracies "
                         "run this high",
    "w_information": "how much the state cares about work that spreads ideas",
    "w_labour_saving": "negative here means a machine that displaces hands "
                       "is itself alarming, on top of anything else about it",
    "w_magic_fear": "how alarmed this society is by anything inexplicable "
                    "or showy",
    "w_military": "how much the state cares about work it could use militarily",
    "w_novelty": "negative here means novelty itself is alarming, whatever "
                "the work actually is",
    "w_religious_rigidity": "how threatening anything religion-adjacent looks",
}


def _agent_values(s):
    """What this society actually believes, as numbers you can look up.

    These move over the course of a run - printing raises literacy, the
    scientific method lowers the fear of the inexplicable - and the only
    record of a move has ever been a completion's "changes the society:
    w_novelty, w_commerce" line, naming fields with no way to see what they
    are or what they are now. This is that way.
    """
    weights = dict(getattr(s, "w", {}) or {})
    rows = [{"field": field, "value": round(weights[field], 3), "means": _VALUE_MEANINGS.get(field)}
            for field in sorted(weights) if not field.startswith("_")]
    return {"ok": True, "values": rows,
            "note": "a completion's own 'changes the society' line says which "
                    "of these moved and when."}


# ---------------------------------------------------------------------------
# THE INDUSTRIAL DASHBOARD. A player who had already won the game asked for
# one command that answers "what physical capability does my society
# currently have, not just what I know how to build" - tonnages and
# kilowatts, not tech names. Every figure below reads a function economy.py
# (or this file) already computes for some OTHER purpose: resource_throttle's
# own supply-vs-demand arithmetic, mine_yield_t, hours_you_can_call_on,
# _agent_state's own per-project accounting. Nothing here is a second copy of
# a number computed somewhere else - see _power_status's own note for the one
# place that would have needed one and does not get it: the tree narrates
# power capability in kilowatts and megawatts (node names, notes) but nothing
# in the engine ever turns that into a tracked wattage, so this reports the
# capability gate honestly instead of inventing a figure to match the prose.
# ---------------------------------------------------------------------------

def _material_capacity_rows(s):
    """Capacity, demand and surplus/shortfall for every material currently in
    demand, or in which you have sunk your own capacity even if nothing
    currently needs it - the same own-supply-plus-market arithmetic
    resource_throttle() already runs to find the ONE worst-binding material
    (see economy.py's _own_material_supply/_material_market_tonnes), laid
    out for every material instead of only the worst.
    """
    demand = s.annual_material_demand()
    by_tag = s._demand_by_supply_tag(demand)
    rows = {}
    for (emp_key, tag), need in by_tag.items():
        own = s._own_material_supply(tag)
        market = s._material_market_tonnes(emp_key)
        rows[emp_key] = {
            "material": emp_key,
            "capacity_t_per_yr": round(own + market, 1),
            "your_own_capacity_t_per_yr": round(own, 1),
            "market_capacity_t_per_yr": round(market, 1),
            "demand_t_per_yr": round(need, 1),
            "surplus_t_per_yr": round(own + market - need, 1)}
    # OWNED CAPACITY WITH NO CURRENT DEMAND. A mine you sank and no longer
    # need does not simply vanish from what you could still supply.
    for mat in s.mine_capacity:
        if mat in rows:
            continue
        own = s._own_material_supply("mine:" + mat)
        market = s._material_market_tonnes(mat)
        rows[mat] = {
            "material": mat,
            "capacity_t_per_yr": round(own + market, 1),
            "your_own_capacity_t_per_yr": round(own, 1),
            "market_capacity_t_per_yr": round(market, 1),
            "demand_t_per_yr": 0.0,
            "surplus_t_per_yr": round(own + market, 1)}
    for mat, row in rows.items():
        if mat in s.mine_capacity:
            note = s.mine_depletion_note(mat)
            if note:
                row["yield_note"] = note
    # WORST SHORTFALL FIRST - the bottleneck a player actually has to reason
    # about belongs at the top, not buried alphabetically.
    return sorted(rows.values(), key=lambda r: (r["surplus_t_per_yr"], -r["demand_t_per_yr"]))


# THE POWER LADDER, in the order the tree actually builds it. Each entry is a
# real capability node; the label is the tree's OWN description of its scale
# (node name/note), not a number this file made up - see _power_status.
_POWER_LADDER = (
    ("cap_power_muscle", "muscle and animal power"),
    ("cap_power_water", "water power, tens of kW on one shaft"),
    ("cap_power_steam", "portable steam power, hundreds of kW"),
    ("cap_power_electric", "local electric power, kW scale (workshop-scale)"),
    ("cap_power_grid", "grid electric power, MW scale (central generation)"))


def _power_tiers(s, nodes):
    """Which rungs of _POWER_LADDER are visible to this player yet, and the
    highest one actually built - the fog rule from _power_status's own
    docstring (a rung is named only once built, active, or revealed)
    applied, and nothing else.
    """
    tiers = []
    highest = None
    for nid, label in _POWER_LADDER:
        if nid not in nodes or not s.is_visible(nid):
            continue
        built = s.has(nid)
        tiers.append({"capability": label, "id": nid, "built": built})
        if built:
            highest = label
    return tiers, highest


def _power_generation_block(s):
    """Real generation and demand figures in kilowatts, once at least one
    power tier is visible - generation_kw, demand_kw, reserve_margin,
    transmission_capacity_kw, the optional mechanical-shaft breakdown, the
    optional binding-constraint flag, and the closing note. See
    _power_status's own docstring for where these numbers come from and why
    they are safe to show under fog; this only reads them.
    """
    gen = s.generation_breakdown_kw()
    demand_kw = s._electricity_demand_kw()
    total_kw = gen["total_kw"]
    block = {
        "generation_kw": {"local_workshop_scale": round(gen["local_kw"], 1),
                          "grid_scale": round(gen["grid_kw"], 1),
                          "total": round(total_kw, 1)},
        "demand_kw": round(demand_kw, 1),
        "reserve_margin": (None if demand_kw <= 1e-9 else
                           round((total_kw - demand_kw) / demand_kw, 3)),
        "transmission_capacity_kw": round(gen["transmission_kw"], 1),
    }
    mech = gen["mechanical_kw"]
    if mech.get("water") or mech.get("steam"):
        block["mechanical_shaft_power_kw"] = {mechanism: round(value, 1)
                                              for mechanism, value in sorted(mech.items()) if value}
    if s.binding == "electricity":
        block["electricity_is_the_binding_constraint"] = True
        block["throttle"] = round(s.throttle, 3)
    block["note"] = ("generation and demand are both averaged continuous "
                     "kilowatts, the same annual-flow convention every other "
                     "tracked resource in this engine uses - not an "
                     "instantaneous or peak reading.")
    return block


def _power_waiting_on(s, nodes, grid_known):
    """Which not-yet-built, visible projects are waiting on workshop-scale
    power versus the grid specifically - called only once the player has
    themselves discovered workshop-scale electricity; see _power_status's
    own docstring for why the grid split waits on grid_known too.
    """
    workshop_scale, grid_scale = [], []
    for node_id, node in nodes.items():
        if node_id in s.done or not s.is_visible(node_id):
            continue
        pre = node.get("pre") or []
        if grid_known and not s.has("cap_power_grid") and "cap_power_grid" in pre:
            grid_scale.append(node_id)
        elif not s.has("cap_power_electric") and "cap_power_electric" in pre:
            workshop_scale.append(node_id)
    out = {}
    if workshop_scale:
        out["waiting_on_workshop_scale_power"] = sorted(workshop_scale)
    if grid_scale:
        out["waiting_on_grid_scale_power"] = sorted(grid_scale)
    return out


def _power_status(s, nodes):
    """What this society can generate, transmit and draw, in real kilowatts,
    and - once electrification has actually begun for THIS player - which
    visible projects are waiting on workshop-scale power versus the grid.

    REAL FIGURES NOW, not only a capability gate: economy.py's
    generation_breakdown_kw()/_electricity_demand_kw() (see that file's own
    long comment on where every number in them came from, and where the
    tree's own notes were too vague to give one) turn the ladder's names -
    "kW scale", "tens of kW", "hundreds of kW", "MW scale" - into tracked
    watts, the same way resource_throttle() already tracks iron and copper.
    This screen reads those functions; it computes nothing of its own.

    FOG: a rung is named only once it is visible (built, active, or
    revealed) - the ladder itself is not spoiled by naming an unbuilt lower
    rung, since is_visible already governs which rungs qualify. The
    generation/demand FIGURES are safe to show even so: both functions sum
    only over self.done/self.active, and is_visible(k) is unconditionally
    true for anything in either set (fog.py's own definition) - a number is
    never built from a node the player has not already built or started
    themselves. The workshop-versus-grid split on projects goes further: it
    distinguishes the two scales for a project only once the player has
    themselves discovered BOTH cap_power_electric and, separately,
    cap_power_grid - naming "this needs the grid" before the player has ever
    heard of a grid would hand over the existence of the next tier exactly
    the way `bounty` once handed over power_grid's id by naming a raw
    prerequisite; here nothing is named until it is not a prerequisite the
    player would be seeing for the first time.
    """
    tiers, highest = _power_tiers(s, nodes)
    out = {
        "power_tiers_you_have_discovered": tiers or "none yet",
        "highest_you_have_built": highest,
    }
    if not tiers:
        out["note"] = ("nothing discovered yet: no generation, no demand.")
        return out
    out.update(_power_generation_block(s))
    elec_known = s.is_visible("cap_power_electric")
    grid_known = s.is_visible("cap_power_grid")
    if elec_known:
        out.update(_power_waiting_on(s, nodes, grid_known))
    return out


# copper_wire_kg/wire_drawn_kg and gold_kg: economy.py's MATERIAL_CHECKS now
# tracks these against the same copper/gold supply the `mines` row is about
# (see that table's own comment); this key map has to agree or "you actually
# need" would silently exclude what 36 electrical nodes and a central bank
# draw.
_MINE_DEMAND_KEYS = {"coal": ("coal_kg",), "iron": ("iron_bar_kg", "iron_ore_kg"),
                     "copper": ("copper_kg", "copper_wire_kg", "wire_drawn_kg"),
                     "lead": ("lead_kg",),
                     "tin": ("tin_kg",), "silver": ("silver_kg",),
                     "gold": ("gold_kg",)}


def _mine_pending_workings(s):
    """Shafts already paid for but not yet in production, summed by
    material. PENDING WORKINGS COUNT: a shaft takes years to come into
    production and is paid for the moment you sink it, so a player who has
    just bought one and types `mines` must not be told they own none. Not
    yet a working - it has no commissioning year until commission_mines()
    actually makes it one - so these stay grouped by material, as before.
    """
    pending = {}
    for tranche in sorted(getattr(s, "mine_tranches", [])):
        material, amt, ready = tranche[0], tranche[1], tranche[2]
        pending.setdefault(material, [0.0, ready])
        pending[material][0] += amt
        pending[material][1] = min(pending[material][1], ready)
    return pending


def _mine_rows_for_material(s, material, workings, want):
    """One row per actual working of this material, ordered by commissioning
    year so several workings of the same seam read as a chronology, not a
    jumble - see _agent_mines' own docstring for the full rationale behind
    every column.
    """
    total_rated = sum(working["capacity"] for working in workings)
    rows = []
    for working in sorted(workings, key=lambda w: (
            w.get("opened_year") if w.get("opened_year") is not None
            else -1)):
        # ACTUAL yield, not the nominal tonnage sunk: THIS working's own
        # depletion (the easy ore going, aged from its own commissioning
        # year - see economy.py's class comment above _workings_of) and
        # current mining technology both move this away from rated
        # capacity, and a player whose coal yield has halved over eighty
        # years has to be able to see that here, not just infer it from a
        # lower revenue somewhere else.
        actual = s.mine_yield_t_for(working)
        # UTILISATION: rated capacity against what is really being drawn -
        # the question the player actually asked. Demand for this material
        # is shared across its workings in proportion to their own rated
        # capacity (the model has no finer-grained way to say which working
        # feeds which furnace); what a working can actually be drawn on for
        # is capped by its OWN yield, so a fully depleted working shows low
        # utilisation even when every tonne it can still raise is being
        # used, and an unused one shows 0% however healthy its seam is -
        # exactly the distinction between a real supply and an economic
        # asset the player asked to see.
        share = want * (working["capacity"] / total_rated) if total_rated > 0 else 0.0
        drawn = min(share, actual)
        util = (drawn / working["capacity"]) if working["capacity"] > 0 else 0.0
        rows.append({
            "material": material,
            "commissioned_year": working.get("opened_year") if working.get("opened_year")
                                 is not None else "unknown (from a save "
                                 "written before per-working tracking "
                                 "existed)",
            "rated_capacity_t_per_yr": round(working["capacity"], 2),
            "actual_output_t_per_yr": round(actual, 2),
            "material_demand_t_per_yr": round(want, 2),
            "costs_you_a_year": round(s.mine_operating_cost_for(working), 1),
            "utilization": ("%d%%" % round(100.0 * util))
                           if working["capacity"] > 0 else "-",
            # WHETHER IT IS ACTUALLY SUPPLYING ANYTHING, as a plain flag,
            # not only as a percentage a reader has to interpret. A
            # tester's own question was exactly this: does the game count
            # a mine as real supply, or only as an economic asset sitting
            # on the books?
            "actually_supplying_demand": bool(drawn > 1e-9),
            "yield_note": s.mine_depletion_note_for(working),
            "shut_it_with": "close %s" % material})
    return rows


def _mine_pending_rows(dem, pending):
    """One row per material still being sunk, standing in for a working
    that does not exist yet - see _mine_pending_workings for how these are
    gathered."""
    rows = []
    for material, (amt, ready) in sorted(pending.items()):
        rows.append({
            "material": material,
            "commissioned_year": "pending",
            "rated_capacity_t_per_yr": 0.0,
            "actual_output_t_per_yr": 0.0,
            "material_demand_t_per_yr":
                round(sum(dem.get(demand_key, 0.0)
                          for demand_key in _MINE_DEMAND_KEYS.get(material, (material,))), 2),
            "costs_you_a_year": 0.0,
            "utilization": "sinking",
            "actually_supplying_demand": False,
            "ready_in": ready,
            "tonnes_a_year_when_it_is_ready": round(amt, 2),
            "shut_it_with": "close %s" % material})
    return rows


def _agent_mines(s):
    """A list of your own mines, ONE ROW PER WORKING: the material it
    raises, its rated capacity, its actual output after ITS OWN depletion
    and current technology, what it costs to run, its utilisation, the
    year it was commissioned, and whether it is actually supplying any of
    this year's demand or merely standing there being paid for. See the
    `mines`/`workings` dispatch below and _agent_capacity, which both call
    this rather than keeping two copies of the same arithmetic.

    A player who had already won the game asked for exactly this: "a mines
    command showing each mine, resource key, rated capacity, actual
    output, operating cost, utilization, commissioning year, and whether
    it is currently supplying anything would have prevented several
    confusing decisions." Before economy.py's self.mines existed there was
    no "it" to ask any of this about - mine_capacity was one float per
    material, so a mine had no individual identity, no commissioning year,
    and no per-working depletion; a shaft opened last year read as
    depleted as one opened three centuries earlier because they were the
    same number. This does not fabricate what that model never recorded:
    a working carried over from a save written before this existed has
    "commissioned_year": None, shown as "unknown" (see load_state's own
    save/load contract), never a guessed year.

    Separately, auto_mine quietly took 353,039 a year against 467,227 of
    revenue for a play tester, and there was no command anywhere that named
    what they owned or what it cost; two `close` calls took their net from
    -61,884 to +291,156. The verbs to sink one and to shut one both
    existed; nothing showed you the books.
    """
    dem = s.annual_material_demand()
    # GENERALISED (COMMODITY_DYNAMISM.md, economy.py's open_mine() is no
    # longer limited to the seven names in _MINE_DEMAND_KEYS): for a mine in
    # a material outside the curated list, the material key IS its own
    # demand key (see economy.py's _material_tag(), same convention), so a
    # default of "look up the key by its own name" covers it rather than
    # silently reporting 0 tonnes needed for anything not in the table.
    pending = _mine_pending_workings(s)
    # GROUPED BY MATERIAL, ordered by commissioning year within it (done in
    # _mine_rows_for_material), so several workings of the same seam read as
    # a chronology, not a jumble. self.mines is a list (append/commission
    # order), not a set, so the groupby itself needs no sorted() to be
    # deterministic across hash seeds - only the final row order does,
    # hence the explicit sort key below.
    by_mat = {}
    for working in getattr(s, "mines", ()):
        by_mat.setdefault(working["material"], []).append(working)
    rows = []
    for material in sorted(by_mat):
        want = sum(dem.get(demand_key, 0.0)
                   for demand_key in _MINE_DEMAND_KEYS.get(material, (material,)))
        rows.extend(_mine_rows_for_material(s, material, by_mat[material], want))
    rows.extend(_mine_pending_rows(dem, pending))
    return {"ok": True,
            "mines_you_own": rows or "none",
            "they_cost_you_a_year_in_all": round(s.mine_operating_cost(), 1),
            "your_revenue_is": round(s.revenue(), 1),
            "still_being_sunk": {material: value[1] for material, value in sorted(pending.items())},
            "note": "Workings are charged every year they stand, whether or "
                    "not you use what they raise. One you no longer need is "
                    "money going out for nothing: 'close <material>'. "
                    "Reopening means sinking it again. 'close' shuts every "
                    "working of that material at once - there is no way to "
                    "shut just one of several workings in the same seam."}


def _portfolio_constraint(waiting):
    """Which of the SIX things a project could be waiting on, from the
    exact sentence _waiting_on already builds for `state` - a second
    classifier reading the same words back, not a second guess at what is
    actually binding.

    Used to be five, with "nobody to do the work" covering both an absolute
    staffing shortage and a trade your OWN other active work has booked -
    two different facts with two different remedies, now two different
    buckets (see _waiting_on's own comment on the split). "materials" is new
    outright: a project can be short of nothing - staff, money, trade,
    calendar - and still be making less progress than its hours alone would
    buy, because the whole economy is throttled by one scarce input.
    """
    if not isinstance(waiting, str):
        return "unclear"
    if waiting.startswith("nobody to do the work"):
        return "staffing"
    if waiting.startswith("trade hours already booked"):
        return "trade_hours"
    if waiting.startswith("materials:"):
        return "materials"
    if waiting.startswith("money") or "pace it can absorb money" in waiting:
        return "money"
    if waiting == "the calendar":
        return "calendar"
    if waiting == "your hours" or waiting.startswith("your hours:"):
        return "founder_hours"
    return "unclear"


# ORDER A PLAYER SHOULD TRIAGE IN: the things only they can fix (staffing,
# trade hours, money) before the things that are just the calendar or their
# own queue running its course. "materials" sits with the other three
# actionable causes - buy the woodland, sink the mine - ahead of the two
# that are not really problems, only pace.
_PORTFOLIO_ORDER = {"staffing": 0, "trade_hours": 1, "materials": 2,
                    "money": 3, "founder_hours": 4, "calendar": 5,
                    "unclear": 6}


def _portfolio_rows(nodes, active_out):
    """Every project you have in hand, grouped by what is actually
    constraining it, reusing _agent_state's own per-project accounting
    (waiting_on, founder-hours, risk) rather than a second copy of it - the
    same active dict `state` already returns, resorted so several long
    clocks running at once read as one screen instead of requiring a player
    to hold each one in their head.
    """
    rows = []
    for node_id, entry in active_out.items():
        node = nodes[node_id]
        constraint = _portfolio_constraint(entry.get("waiting_on"))
        row = {
            "id": node_id, "name": entry["name"], "constraint": constraint,
            "waiting_on": entry.get("waiting_on"),
            # READ, NOT RECOMPUTED, same as everything below it: arrears
            # gives unspendable founder hours back, so waiting_on above can
            # say "your hours" for a project that is really underfunded.
            # why_underfunded is the real reason, already sitting on the
            # same active-dict entry - see _waiting_on's own comment.
            "why_underfunded": entry.get("why_underfunded"),
            "founder_hours_left": entry.get("founder_hours_left"),
            "founder_hours_total": entry.get("founder_hours_total"),
            # READ, NOT RECOMPUTED. These four come straight off the same
            # st dict step()'s own allocator loop wrote them to (core.py,
            # "pool_total_this_year" and neighbours) - the actual share this
            # project got this year, and why, never a second guess at it
            # that could end up disagreeing with what was actually applied.
            "hours_offered_this_year": entry.get("hours_offered_this_year"),
            "hours_effective_this_year": entry.get("hours_effective_this_year"),
            # THE STANDING ORDER ITSELF, same read-not-recomputed rule as
            # its four neighbours - None for every project nobody has
            # directed, which is most of them on any save that predates
            # `allocate` or never uses it.
            "hours_directed_this_year": entry.get("hours_directed_this_year"),
            "pool_rank_this_year": entry.get("pool_rank_this_year"),
            "pool_active_count_this_year": entry.get("pool_active_count_this_year"),
            "pool_total_this_year": entry.get("pool_total_this_year"),
            "years_in_progress": entry.get("years_in_progress"),
            "calendar_years_left": round(
                max(0.0, float(node["yrs"]) - float(entry.get("years_in_progress") or 0.0)), 1),
            "still_to_pay": entry.get("still_to_pay"),
            "chance_of_failure": node.get("risk") or None,
        }
        if "will_be_abandoned_in_years" in entry:
            row["will_be_abandoned_in_years"] = entry["will_be_abandoned_in_years"]
            row["because_nobody_here_can"] = entry.get("because_nobody_here_can")
        rows.append(row)
    rows.sort(key=lambda r: (_PORTFOLIO_ORDER.get(r["constraint"], 9),
                             -(r["founder_hours_left"] or 0.0)))
    return rows


def _spare_capacity(s, state_out):
    """Founder-hours, staff and cash flow not currently spoken for: enough
    to teach parallelism without saying what to build with it. Every figure
    here is hours_you_can_call_on(t)/trade_hours_used - the same pair
    _waiting_on already reads per project - summed by trade family instead
    of read one project at a time, plus the spending figures `money`/`state`
    already compute for their own screens.
    """
    families = {}
    for trade in WAGES:
        if not s.trade_available(trade):
            continue
        fam = trade_family(trade)
        pair = families.setdefault(fam, [0.0, 0.0])
        supply = s.hours_you_can_call_on(trade)
        used = min(supply, s.trade_hours_used.get(trade, 0.0))
        pair[0] += supply
        pair[1] += used
    rows = []
    for fam, (supply, used) in sorted(families.items()):
        spare = max(0.0, supply - used)
        if supply <= 0:
            continue
        rows.append({"trade_family": fam,
                     "spare_hours_this_year": round(spare, 0),
                     "spare_people_equivalent": round(
                         spare / s.HOURS_PER_PERSON_YEAR, 1)})
    return {
        "founder_hours_available": state_out.get("founder_hours_available"),
        "free_hours_going_unused": state_out.get("free_hours_going_unused"),
        "spare_by_trade_family": rows or "none",
        "you_could_raise_right_now": round(s.spending_power("buy"), 1),
        "credit_limit": round(s.credit_limit(), 1),
        "standing_net_per_year": state_out.get("net_per_year"),
        # WHERE THE HEADROOM COMES FROM, because a starting grant was
        # invisible. Rome alone begins with fin_societas and so oversees ten
        # people in its first year where the other four civilisations oversee
        # six, and nothing told a Roman player why or told a Norse player what
        # they were missing. supervision_room_from (labour.py) walks the same
        # sources supervision_room sums, so this cannot drift from the figure
        # it explains.
        "people_you_can_oversee": round(s.supervision_room(), 1),
        "and_where_that_comes_from": s.supervision_room_from(),
        "note": "standing net per year is this household's own ordinary-year "
                "surplus or deficit before this year's project spend - "
                "roughly how much more annual project spend you could "
                "sustain going forward if it is positive, not cash sitting "
                "idle today. 'money' shows how it is made up.",
    }


def _trade_demand_rows(s):
    """trade_demand_vs_supply (projects.py), with the family a player
    actually hires by attached and sorted worst-first - the aggregate
    picture a player needs BEFORE committing to one more project that
    shares a trade already oversubscribed: "the game reported 10,000-25,000
    founder-hours free, while a project requiring only hundreds of hours
    advanced very slowly because of the active portfolio" was never a
    founder-hours problem at all in the run that said it; it was this.
    """
    rows = []
    for trade, detail in s.trade_demand_vs_supply().items():
        rows.append({
            "trade": trade, "trade_family": trade_family(trade),
            "demand_hours_this_year": detail["demand_hours_this_year"],
            "supply_hours_this_year": detail["supply_hours_this_year"],
            "oversubscribed": detail["oversubscribed"],
            "projects_drawing_on_it": detail["projects_drawing_on_it"],
        })
    rows.sort(key=lambda r: (not r["oversubscribed"],
                             r["supply_hours_this_year"] - r["demand_hours_this_year"]))
    return rows


def _agent_portfolio(s, nodes, cmd=None):
    """The screen a player who had already won the game asked for four
    separate times in one run: what every active project is actually
    getting this year, why, and whether the portfolio as a whole is asking
    its trades for more than they can give - all of it read back from the
    allocator's own bookkeeping (core.py step(), projects.py trade_draw_
    plan/trade_demand_vs_supply), never recomputed here.
    """
    state_out = _agent_state(s, nodes)
    active_out = state_out.get("active") or {}
    rows = _portfolio_rows(nodes, active_out)
    pool_total = state_out.get("founder_hours_available")
    count = len(active_out)
    return {
        "ok": True,
        "active_project_count": count,
        "founder_hours_available_this_year": pool_total,
        "free_hours_going_unused": state_out.get("free_hours_going_unused"),
        "projects": rows,
        "trade_hours_demand_vs_supply": _trade_demand_rows(s),
        "note": ("%d active project%s %s sharing this year's %s directed "
                "hours; each row above shows what IT got and why. "
                "'trade_hours_demand_vs_supply' is the same question for "
                "every hired trade your portfolio draws on, summed across "
                "all of them, before you commit to one more."
                % (count, "" if count == 1 else "s",
                   "is" if count == 1 else "are",
                   "{:,.0f}".format(pool_total or 0.0))) if count else
                "nothing active yet - 'available' or 'stuck' says what you "
                "could begin today.",
    }


def _agent_capacity(s, nodes, cmd=None):
    """The industrial dashboard: physical capability, not just known
    technologies. One underlying summary for resources, power, mines, the
    project portfolio and spare capacity, because a player reasoning about
    a bottleneck needs all five in the same place, not six commands to
    cross-reference by hand.
    """
    state_out = _agent_state(s, nodes)
    active_out = state_out.get("active") or {}
    return {
        "ok": True,
        "resources": _material_capacity_rows(s),
        "power": _power_status(s, nodes),
        "mines": _agent_mines(s),
        "portfolio": _portfolio_rows(nodes, active_out),
        "spare_capacity": _spare_capacity(s, state_out),
        "resource_throttle": state_out.get("resource_throttle"),
        "throttle_binding": state_out.get("throttle_binding"),
        "note": "'mines' gives the same mine rows with more room; 'labour' "
                "gives any one trade in full; 'money' gives the ledger this "
                "reads its cash figures from.",
    }


def _dashboard_snapshot(s):
    """One year's worth of the numbers `changes` diffs against later - a
    timestamped copy of figures already computed elsewhere (price_index,
    literacy, mine_capacity, ...), not a new figure of its own. Called once
    per simulated year from the `step` dispatch below."""
    return {
        "year": s.year,
        "price_index": round(s.price_index, 4),
        "wage_index": round(s.wage_index, 4),
        "literacy_general": round(float(s.civ.get("literacy_general", 0.0)), 4),
        "literacy_elite": round(float(s.civ.get("literacy_elite", 0.0)), 4),
        "capital": round(s.capital, 1),
        "revenue": round(s.revenue(), 1),
        "credit_limit": round(s.credit_limit(), 1),
        "throttle": round(s.throttle, 3),
        "binding": s.binding,
        "operating_count": len(s.operating),
        "done_earned": len(s.done - s.granted),
        "employees_total": round(sum(s.employees.values()), 2),
        "scholars": round(s.scholars, 2),
        "artisans": round(s.artisans, 2),
        "mine_capacity": {material: round(value, 1) for material, value in s.mine_capacity.items()},
        "scandal": round(s.scandal, 2),
        "reputation": round(s.reputation, 1),
        "eminence": round(s.eminence, 2),
    }


def _agent_economy(s, cmd=None):
    """A short, readable economic summary, with detail behind an explicit
    ask rather than printed by default - major prices, wages, cost of
    living, literacy, market saturation and household capacity, all read
    from figures `money`/`labour`/`state` already compute for their own
    screens, plus what has moved most recently using the same yearly
    snapshots `changes` reads.
    """
    full = bool((cmd or {}).get("full"))
    hist = getattr(s, "_dashboard_history", None) or []
    moved = {}
    if hist:
        now = hist[-1]
        for n_yrs in (5, 10):
            cutoff = s.year - n_yrs
            base = None
            for rec in hist:
                if rec["year"] <= cutoff:
                    base = rec
                else:
                    break
            if base is not None:
                moved["last_%d_years" % n_yrs] = {
                    "price_index": round(now["price_index"] - base["price_index"], 4),
                    "wage_index": round(now["wage_index"] - base["wage_index"], 4),
                    "literacy_general": round(
                        now["literacy_general"] - base["literacy_general"], 4)}
    out = {
        "ok": True,
        "price_index": round(s.price_index, 4),
        "wage_index": round(s.wage_index, 4),
        "cost_of_living_a_year": round(s.living_cost() - s.wage_bill(), 1),
        "literacy": {"general": round(float(s.civ.get("literacy_general", 0.0)), 3),
                     "elite": round(float(s.civ.get("literacy_elite", 0.0)), 3)},
        "household_places_used_of_all": "%.1f of %.1f" % (
            s.headcount(), s.headcount() + max(0.0, s.household_room())),
        "where_the_money_comes_from": s.revenue_sources(),
        "market_saturation": s.goods_market_summary(),
        "materials_at_a_premium": s.material_market_summary(),
        "what_moved_most": moved or "not enough history yet - step forward "
                                    "and ask again",
        "more_detail": '{"cmd":"economy","full":true}',
    }
    if full:
        # THE SAME PER-MATERIAL FACTOR money's own material_market_summary
        # already aggregates into one worst-case note, here as the rows that
        # note is built from, for every tracked commodity rather than just
        # the worst one.
        rows, seen = [], set()
        for pair in s.MATERIAL_CHECKS.values():
            material_key = pair[0]
            if material_key in seen:
                continue
            seen.add(material_key)
            rows.append({"material": material_key,
                        "price_factor_over_book": round(s.material_price_factor(material_key), 3)})
        out["tracked_material_prices"] = sorted(rows, key=lambda r: -r["price_factor_over_book"])
        # THE SAME FORMULA `labour`'s own row() uses for "a_year_of_one", not
        # a second version of a wage this file already prints elsewhere.
        out["wages_by_trade"] = [
            {"trade": trade, "a_year_of_one": round(s.annual_wage(trade), 0),
             "wage_foundation": {
                 "base_for_skill_and_difficulty": ANNUAL_WAGE.get(trade, 375.0),
                 **{factor_key: round(value, 3) for factor_key, value in s.wage_cost_factors(trade).items()},
                 "demographic_scarcity": round(s.wage_index, 3),
                 "local_trade_scarcity": round(s.labour_price_factor(trade), 3)}}
            for trade in sorted(WAGES) if s.trade_available(trade)]
    return out


def _uniq(seq):
    """Preserve order, drop repeats - list(dict.fromkeys(seq)) under a name
    that says what it is for."""
    return list(dict.fromkeys(seq))


def _parse_changes_years(raw):
    """Validate the `years` argument for `changes`, the four checks the
    original inline code ran in order. Returns (years, None) once valid, or
    (None, error_dict) on the first check that fails.
    """
    if isinstance(raw, bool):
        return None, {"ok": False, "error": "years must be a number, not true or false"}
    try:
        years = int(raw)
    except (TypeError, ValueError):
        return None, {"ok": False, "error": "years must be an integer"}
    if float(raw) != years:
        return None, {"ok": False, "error": "years must be a whole number of years. "
                                            "Nothing was changed."}
    if years < 1:
        return None, {"ok": False, "error": "years must be >= 1"}
    return years, None


def _changes_baseline(hist, cutoff, current_year):
    """Find the snapshot at least `cutoff`'s worth of years back from now, or
    an error dict explaining why there is not one yet - the two
    history-availability checks the original inline code ran before it had
    anything to diff. Returns (now, baseline, None) when found, or
    (None, None, error_dict) when not.
    """
    if not hist:
        return None, None, {"ok": False, "error": "nothing has been recorded yet; step "
                                                    "forward a year first, then ask again"}
    now = hist[-1]
    baseline = None
    for rec in hist:
        if rec["year"] <= cutoff:
            baseline = rec
        else:
            break
    if baseline is None:
        earliest = hist[0]["year"]
        return None, None, {"ok": False,
                "error": ("this run's own record only goes back to %d AD, %d "
                          "years ago; ask for %d or fewer"
                          % (earliest, current_year - earliest, current_year - earliest))}
    return now, baseline, None


def _changes_moved(baseline, now):
    """The per-metric deltas between the baseline snapshot and now - one
    subtraction per tracked figure, nothing conditional about any of them."""
    return {
        "price_index": round(now["price_index"] - baseline["price_index"], 4),
        "wage_index": round(now["wage_index"] - baseline["wage_index"], 4),
        "literacy_general": round(
            now["literacy_general"] - baseline["literacy_general"], 4),
        "literacy_elite": round(
            now["literacy_elite"] - baseline["literacy_elite"], 4),
        "capital": round(now["capital"] - baseline["capital"], 1),
        "revenue": round(now["revenue"] - baseline["revenue"], 1),
        "credit_limit": round(now["credit_limit"] - baseline["credit_limit"], 1),
        "employees_total": round(
            now["employees_total"] - baseline["employees_total"], 2),
        "scholars": round(now["scholars"] - baseline["scholars"], 2),
        "artisans": round(now["artisans"] - baseline["artisans"], 2),
        "operating_count": now["operating_count"] - baseline["operating_count"],
        "technologies_completed": now["done_earned"] - baseline["done_earned"],
        "scandal": round(now["scandal"] - baseline["scandal"], 2),
        "reputation": round(now["reputation"] - baseline["reputation"], 1),
        "eminence": round(now["eminence"] - baseline["eminence"], 2),
    }


def _changes_capacity(baseline, now):
    """Which mined materials' capacity moved by more than a rounding error
    over the window, as {"material", "change_t_per_yr"} rows."""
    then_cap = baseline.get("mine_capacity") or {}
    now_cap = now.get("mine_capacity") or {}
    rows = []
    for material in sorted(set(then_cap) | set(now_cap)):
        change = round(now_cap.get(material, 0.0) - then_cap.get(material, 0.0), 1)
        if abs(change) > 0.05:
            rows.append({"material": material, "change_t_per_yr": change})
    return rows


def _changes_tech_gather(hist, cutoff):
    """Concatenate each year's own record of completions, reveals, and
    concern opens/closes over the window - deduplication happens in the
    caller, _changes_tech_events."""
    completed, revealed, opened, closed = [], [], [], []
    for rec in hist:
        if rec["year"] <= cutoff:
            continue
        completed.extend(rec.get("completed") or [])
        revealed.extend(rec.get("revealed_added") or [])
        opened.extend(rec.get("concerns_opened") or [])
        closed.extend(rec.get("concerns_closed") or [])
    return completed, revealed, opened, closed


def _changes_tech_events(hist, cutoff):
    """Which technologies completed or were newly heard of, and which
    concerns opened or closed, over the window - each year's own snapshot
    already lists these; this only concatenates and de-duplicates them."""
    completed, revealed, opened, closed = _changes_tech_gather(hist, cutoff)
    completed = _uniq(completed)
    revealed = _uniq([node_id for node_id in revealed if node_id not in completed])
    opened = _uniq(opened)
    closed = _uniq([node_id for node_id in closed if node_id not in opened])
    return {
        "technologies_completed": completed or "none",
        "technologies_newly_heard_of": revealed or "none",
        "concerns_opened": opened or "none",
        "concerns_closed": closed or "none",
    }


def _changes_notable_events(s, cutoff):
    """A HANDFUL OF WORDS, NOT THE WHOLE LOG. Anything the engine already
    logged as happening TO this player over the window, filtered to the
    kind of thing a player would call a political event rather than
    ordinary bookkeeping ("hired a smith"). The log itself is already
    player-facing prose (see `log`); this only picks out a slice of it.
    """
    _MARKERS = ("sack", "denounced", "founder dies", "plague", "crisis",
               "scandal", "credit exhausted", "insolvency", "war", "revolt",
               "famine", "fire", "died", "denunciation")
    return [{"year": year, "message": message} for year, message in s.log
            if cutoff < year <= s.year and any(marker in message.lower() for marker in _MARKERS)]


def _agent_changes(s, nodes, cmd=None):
    """What materially changed over the last N years - the diff a player
    otherwise has to work out by holding two screens in their head, which is
    exactly what one of our own testers had to do to diagnose a bug. Reads
    the yearly snapshots `step` records (_dashboard_snapshot) rather than
    recomputing anything; see that function for what is actually stored.
    """
    raw = (cmd or {}).get("years", 5)
    years, error = _parse_changes_years(raw)
    if error:
        return error
    hist = getattr(s, "_dashboard_history", None) or []
    cutoff = s.year - years
    now, baseline, error = _changes_baseline(hist, cutoff, s.year)
    if error:
        return error
    result = {
        "ok": True,
        "from_year": baseline["year"], "to_year": now["year"],
        "moved": _changes_moved(baseline, now),
        "bottleneck": {"then": baseline.get("binding"), "now": now.get("binding")},
        "capacity_gained_or_lost": _changes_capacity(baseline, now) or "none",
    }
    result.update(_changes_tech_events(hist, cutoff))
    result["notable_events"] = _changes_notable_events(s, cutoff) or "none"
    return result
