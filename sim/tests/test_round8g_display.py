"""round8g_display: split verbatim from the old test_regressions.py (original lines 10077-10531).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# ======================================================================
# ROUND 8g: a five-report playtest sweep of protocol.py / cli.py (display).
# ======================================================================

from engine.protocol import (render_state as _RSTATE, render_risk as _RRISK,
                             render_why as _RWHY, render_ventures as _RVENT,
                             render_path as _RPATH)

# --- FINDING: "finished, stays finished" meant three different things -
# a plain prerequisite, a structural bonus, and a non-DAG gate - and the
# engine said it the same way for all three. `why` now names a
# CAPABILITY_INSTITUTIONS node for what it is, and leaves an ordinary
# prerequisite alone.
_s_cap = sim(civ="rome_100ad", capital=5000000.0)
_wr_cap = S._agent_dispatch(_s_cap, NODES, {"cmd": "why", "id": "workshop_first"})
check("why flags a capability institution as needing to stay OPEN, not "
      "only built",
      bool(_wr_cap.get("this_is_a_capability_you_must_keep_open")),
      _wr_cap.get("this_is_a_capability_you_must_keep_open"))
check("...and the sentence appears on the rendered page too",
      "KEEP THIS OPEN" in _RWHY(_wr_cap), _RWHY(_wr_cap))
_wr_plain = S._agent_dispatch(_s_cap, NODES, {"cmd": "why", "id": "scientific_method"})
check("...while an ordinary prerequisite (not a capability institution) is "
      "not flagged the same way",
      _wr_plain.get("this_is_a_capability_you_must_keep_open") is None,
      _wr_plain.get("this_is_a_capability_you_must_keep_open"))

# --- FINDING: `ventures` scored identity_cover/workshop_first (structural
# bonuses) and patron_local (a non-DAG gate) exactly like an ordinary
# earn/cost business, so a Rome player could not tell them apart from a
# shuttered shop. They now get their own list.
_s_vcap = sim(civ="rome_100ad", capital=5000000.0)
_s_vcap.done.update(["identity_cover", "tex_horizontal_loom"])
_s_vcap._done_changed()
_vt_cap = S._agent_dispatch(_s_vcap, NODES, {"cmd": "ventures"})
_cap_ids = [r.get("id") for r in (_vt_cap.get(
    "capabilities_you_know_how_to_run_but_have_not_opened") or [])
    if isinstance(r, dict)]
_ord_ids = [r.get("id") for r in (_vt_cap.get(
    "you_know_how_but_have_not_opened") or []) if isinstance(r, dict)]
check("ventures puts an idle capability institution in its own list, not "
      "the ordinary earn/cost one",
      "identity_cover" in _cap_ids and "identity_cover" not in _ord_ids,
      (_cap_ids, _ord_ids))
check("...and leaves an ordinary idle business in the ordinary list",
      "tex_horizontal_loom" in _ord_ids and "tex_horizontal_loom" not in _cap_ids,
      (_cap_ids, _ord_ids))

# --- FINDING: the headline "net X/yr" conflated one-off project spend with
# recurring burn, so `state` looked like it was about to go broke on any
# turn a player started something expensive. `state` now prints the
# recurring figure plainly, not only the after-spend one.
_s_net = sim(civ="rome_100ad", capital=50000.0)
_st_net = S._agent_dispatch(_s_net, NODES, {"cmd": "start", "id": "scientific_method"})
_stt_net = S._agent_dispatch(_s_net, NODES, {"cmd": "state"})
_rendered_net = _RSTATE(_stt_net)
check("state's money line names the recurring net as the one to watch",
      "recurring" in _rendered_net and "one to watch" in _rendered_net,
      _rendered_net.splitlines()[4:7])
check("...and, once a project has actually taken spend, also shows the "
      "one-off after-spend figure alongside it",
      (_stt_net.get("project_spend_this_year") or 0) <= 0.5
      or "one-off" in _rendered_net,
      (_stt_net.get("project_spend_this_year"), _rendered_net.splitlines()[4:7]))

# --- FINDING: an undocumented per-project throttle (cost divided by the
# calendar floor, however much cash is in hand) already explained itself on
# `state`; it said nothing on `why` for that same active project, which is
# the screen a player checking on one stalled project by name would reach
# for.
_s_thr = sim(civ="han_china_100ad", capital=5000000.0)
_ok_thr, _ = _s_thr.start_project("sc2_method_negative_result")
_s_thr.step()
_wr_thr = S._agent_dispatch(_s_thr, NODES, {"cmd": "why", "id": "sc2_method_negative_result"})
check("why on an ACTIVE project says what it is waiting on, not just ACTIVE",
      bool(_wr_thr.get("waiting_on")), _wr_thr.get("waiting_on"))
check("...and, with abundant cash against a 20-year calendar floor, names "
      "the pace throttle by the same words `state` uses for it",
      "pace it can absorb money" in (_wr_thr.get("waiting_on") or ""),
      _wr_thr.get("waiting_on"))

# --- FINDING: `risk`'s per-year percentages read as one low-stakes roll,
# when the engine actually checks them independently EVERY year a hazard's
# window is open. A Rome player was sacked twice in the same window having
# read exactly this kind of figure as safe. The screen now says the window
# is repeated and what it adds up to.
_s_haz = sim(civ="rome_100ad")
_s_haz.events = True
_s_haz.year = 240          # inside Rome's Third Century Crisis, 235-284
_rk = S._agent_dispatch(_s_haz, NODES, {"cmd": "risk"})
_crisis = next((h for h in (_rk.get("knowledge_risk") or {}).get(
    "known_hazards_ahead") or [] if "Third century" in h.get("name", "")), None)
check("a real dated, multi-year sacking hazard exists to check against",
      _crisis is not None, [h.get("name") for h in
      (_rk.get("knowledge_risk") or {}).get("known_hazards_ahead") or []])
if _crisis:
    _rendered_risk = _RRISK(_rk)
    check("risk says a per-year hazard is rolled EVERY year of its window, "
          "not once",
          "checked EVERY year" in _rendered_risk and "chance" in _rendered_risk,
          [ln for ln in _rendered_risk.splitlines() if "checked EVERY year" in ln])
    check("...and the cumulative chance across the window is higher than "
          "the bare per-year figure, which is the whole point",
          any("100%" in ln or "chance at least one sacking" in ln
              for ln in _rendered_risk.splitlines()),
          [ln for ln in _rendered_risk.splitlines() if "sacking lands" in ln])

# --- FINDING: `path <goal>` is the actual walkthrough and was buried in one
# line of `help commands`, absent from the five starter verbs, and answered
# a different question from `available` - "what the goal still needs" never
# joined to "what I could start today". A Han player scripted the
# intersection themselves outside the game. `path` now does the join.
_s_pth2 = sim(civ="rome_100ad")
_rp2 = S._agent_dispatch(_s_pth2, NODES, {"cmd": "path", "id": GOAL})
check("path names how many of the remaining nodes are startable today",
      isinstance(_rp2.get("startable_today_count"), int)
      and _rp2["startable_today_count"] >= 1,
      _rp2.get("startable_today_count"))
_av2 = S._agent_dispatch(_s_pth2, NODES, {"cmd": "available", "all": True})
_av_ids = {e["id"] for e in (_av2.get("available") or []) if isinstance(e, dict)}
_path_startable_ids = {e["id"] for e in (_rp2.get("startable_today_toward_this") or [])
                       if isinstance(e, dict)}
check("...and every one of those is genuinely on `available` too - the "
      "join is a real intersection, not an invented list",
      _path_startable_ids <= _av_ids, _path_startable_ids - _av_ids)
_welcome = S._agent_dispatch(_s_pth2, NODES, {"cmd": "help"})
check("...and path is now reachable from the welcome screen, not only "
      "buried in `help commands`",
      '"cmd":"path"' in str(_welcome), _welcome.get("help"))
check("path has its own rendering, not a raw key/value dump",
      "ROUTE TO" in _RPATH(_rp2) and "STARTABLE TODAY" in _RPATH(_rp2),
      _RPATH(_rp2)[:80])

# --- FINDING, RAISED TWICE: `path` was promoted into the welcome screen's
# starter verbs on the strength of one player calling it decisive, and three
# MORE players then hit the problem that promotion exposed: early in any
# tree the critical path is almost pure knowledge, zero revenue, and `path`
# pointed firmly at it with no word that none of it earns a denarius. One
# player started four DIFFERENT path items over five years - each
# individually affordable on the day it was started - and spent the next 24
# years in a debt spiral with two insolvencies and a reputation crash,
# because can_start asks "could I begin this, today, alone", never "could I
# afford several of these together". The fix is NOT gated on the household
# already being broke, because by the time recurring income actually goes
# negative the damage from several affordable-alone starts is often already
# done; it is said plainly, every time the route cannot pay for itself on
# its own, with the COMBINED bill of everything listed, which individual
# affordability checks never show.
_s_pay = sim(civ="rome_100ad")
_rp_pay_ok = S._agent_dispatch(_s_pay, NODES, {"cmd": "path", "id": GOAL})
check("set-up: on a fresh turn-one Rome game every startable node on the "
      "route to the goal earns nothing by itself - this is the real "
      "opening, not an invented fixture",
      bool(_rp_pay_ok.get("startable_today_toward_this"))
      and all(e.get("earns_per_year", 0) <= 0
              for e in _rp_pay_ok["startable_today_toward_this"]
              if isinstance(e, dict)),
      [(e.get("id"), e.get("earns_per_year"))
       for e in _rp_pay_ok.get("startable_today_toward_this") or []])
check("`path` says outright, from turn one, that an all-knowledge route "
      "will not cover costs and names a command that finds what actually "
      "pays - not only after the household is already in the red, which "
      "is too late to prevent the debt these players were carried into",
      "earns" in (_rp_pay_ok.get("this_route_pays_for_nothing") or "")
      and '"sort":"earns"' in (_rp_pay_ok.get("this_route_pays_for_nothing") or ""),
      _rp_pay_ok.get("this_route_pays_for_nothing"))
check("...and the warning reaches the rendered page too, not only the JSON",
      "!!" in _RPATH(_rp_pay_ok) and "sort" in _RPATH(_rp_pay_ok),
      _RPATH(_rp_pay_ok))
# A route with at least one real earner among today's startable nodes must
# NOT get the all-knowledge warning: the condition is "nothing on this list
# pays", not "you are poor" - found by scanning the tree for a goal whose
# critical path has a revenue-positive node startable right now, rather
# than assuming one exists.
_s_scan = sim(civ="rome_100ad")
_earning_goal = next((g for g in NODES
                     if any(NODES[p]["rev"] > 0 and _s_scan.can_start(p)
                            for p in S.closure(NODES, g))), None)
check("a goal with a real earner on its startable-today route exists to "
      "test the negative case against",
      _earning_goal is not None, _earning_goal)
if _earning_goal:
    _rp_eg = S._agent_dispatch(sim(civ="rome_100ad"), NODES,
                               {"cmd": "path", "id": _earning_goal})
    check("...and that route gets no 'pays for nothing' warning",
          "this_route_pays_for_nothing" not in _rp_eg,
          _rp_eg.get("this_route_pays_for_nothing"))

# --- THE COMBINED BILL, not each item's own affordability. Several
# individually-affordable starts are not one affordable start; this is the
# exact number the England playtester needed and never had before losing
# 24 years to debt over it.
_s_comb = sim(civ="rome_100ad", capital=1.0)
_rp_comb = S._agent_dispatch(_s_comb, NODES, {"cmd": "path", "id": GOAL})
check("set-up: a household with almost nothing to spend, tested against "
      "the same all-knowledge opening route",
      bool(_rp_comb.get("startable_today_toward_this")), _rp_comb)
_comb_total = sum(_s_comb.project_cost(e["id"])
                  for e in _rp_comb["startable_today_toward_this"])
check("`path` names the combined cost of everything listed against what "
      "can actually be raised, when that combined cost exceeds it - the "
      "one number individual affordability checks never show",
      "these_together_cost_more_than_you_can_raise" in _rp_comb
      and "{:,.0f}".format(_comb_total) in
          _rp_comb["these_together_cost_more_than_you_can_raise"],
      (_comb_total, _rp_comb.get("these_together_cost_more_than_you_can_raise")))

# --- FINDING: `train` and `hire` are two required steps for a taught
# (TRADES_ABSENT) trade, and neither train's own success message nor a
# project's `why` said so beforehand - the refusal only ever appeared at
# `start`.
_s_th = sim(civ="han_china_100ad", capital=5000000.0)
_tr = S._agent_dispatch(_s_th, NODES, {"cmd": "train", "trade": "machinist", "n": 1})
check("train's own success message says a second step (hire) still stands "
      "between training a taught trade and a project being able to use it",
      bool(_tr.get("means")) and "hire" in _tr["means"], _tr.get("means"))
_wr_th = S._agent_dispatch(_s_th, NODES, {"cmd": "why", "id": "ag2_baler"})
check("why on a project needing that just-taught trade says nobody can do "
      "the work yet, before `start` ever refuses it",
      "machinist" in (_wr_th.get("trades_taught_but_nobody_here_to_do_them_yet") or []),
      _wr_th.get("trades_taught_but_nobody_here_to_do_them_yet"))
check("...and the same sentence appears on the rendered page",
      "TAUGHT, BUT NOBODY HERE" in _RWHY(_wr_th), _RWHY(_wr_th))

# --- FINDING (same root cause as above): closing a capability institution
# for the upkeep back used to read exactly like closing an ordinary
# business - a Mexica player did this and lost the capability silently,
# twice. `mothball` now says so.
_s_mb = sim(civ="rome_100ad", capital=5000000.0)
_s_mb.done.add("identity_cover"); _s_mb._done_changed()
_s_mb.open_venture("identity_cover")
_mb_out = S._agent_dispatch(_s_mb, NODES, {"cmd": "mothball", "id": "identity_cover"})
check("mothballing a capability institution says more than its upkeep "
      "stopped",
      _mb_out.get("ok") and bool(_mb_out.get("but"))
      and "capability" in _mb_out["but"], _mb_out.get("but"))
_s_mb2 = sim(civ="rome_100ad", capital=5000000.0)
_s_mb2.done.add("tex_horizontal_loom"); _s_mb2._done_changed()
_s_mb2.open_venture("tex_horizontal_loom")
_mb_out2 = S._agent_dispatch(_s_mb2, NODES, {"cmd": "mothball", "id": "tex_horizontal_loom"})
check("...and an ordinary business closing carries no such warning",
      _mb_out2.get("ok") and "but" not in _mb_out2, _mb_out2)

# --- naive14: AN OUTSIDE PLAYER WON BLIND AS LATER HAN WITH FOG ON AND AN
# IMMORTAL FOUNDER (grown and alloy junction transistors, 575 AD, 168/168
# required nodes) and reported what nearly cost them the run anyway. See
# rome/playtest/naive14/EXTERNAL_TOP_PROBLEMS.md and
# EXTERNAL_BLIND_PLAYTHROUGH.md.
#
# TOP_PROBLEMS #1, rated most damaging: point_contact_transistor's own note
# says Bardeen and Brattain worked POLYCRYSTALLINE germanium in December
# 1947 "with no pulled crystal and no zone refining, neither of which
# existed yet" - and the node still would not start without a semiconductor
# from single_crystal or silicon_path, which forced an entire post-1947
# manufacturing programme (arc furnace, zone refining, single-crystal
# growth, each with a multi-year floor and a near-coinflip failure rate)
# onto the path to a device whose own text says it did not need any of
# that. Checked against the tree: the node already lists ge_reduction in
# `pre` and already consumes 200g of germanium_g in `mat` - the purified
# polycrystalline metal its note describes - so the req_any group was a
# second, contradictory gate stacked on a prerequisite the node already
# had. single_crystal stays required for junction_transistor itself
# (unconditionally, in `pre`), which is the node whose own note says a
# single crystal is what makes the device MANUFACTURABLE - so the
# recommendation (let the 1947 device build on polycrystalline
# germanium, keep single-crystal growth mandatory for the transistor
# that replaces it) holds and is now how the tree reads.
check("point_contact_transistor no longer gates on single_crystal/"
      "silicon_path - the contradiction between its own note and its "
      "prerequisite graph is gone",
      NODES["point_contact_transistor"]["req_any"] == [],
      NODES["point_contact_transistor"]["req_any"])
check("...the mechanism that used to refuse to start it (substitution_"
      "quality, the req_any gate) now clears trivially, with neither "
      "single_crystal nor silicon_path done",
      sim(civ="han_china_100ad").substitution_quality("point_contact_transistor")
      == (1.0, True),
      sim(civ="han_china_100ad").substitution_quality("point_contact_transistor"))
check("...while single_crystal is still mandatory for the goal itself - "
      "the manufacturable junction transistor, not its 1947 proof of "
      "concept, is where single-crystal growth belongs",
      "single_crystal" in NODES["junction_transistor"]["pre"],
      NODES["junction_transistor"]["pre"])
check("...and the goal's required closure is unchanged at 168 nodes - "
      "loosening the contradictory gate did not also loosen what the "
      "goal actually needs",
      len(S.closure(NODES, GOAL)) == 168, len(S.closure(NODES, GOAL)))

# THE BUG CLASS, not just the one instance: a node's own note disclaiming a
# prerequisite ("no X and no Y, neither of which existed yet", "X had not
# yet been invented", ...) while `pre` or a req_any option - single-choice
# OR a genuine multi-way substitution, since that is exactly how this one
# shipped invisibly past closure() - still names that same thing. The
# window searched is the disclaiming sentence itself, narrowed to the
# actual "no X"/"without X" spans in it, not the whole sentence: a note is
# allowed to mention germanium (from ge_reduction, a real and correct
# prerequisite) in the same breath as disclaiming pulled crystals and zone
# refining, and a keyword match against the whole sentence flagged exactly
# that as a false positive before the window was narrowed.
def _disclaimed_prereq_contradictions(nodes):
    disclaim_pats = (r"neither of which existed yet", r"none of which existed yet",
                      r"did not yet exist", r"had not yet been invented",
                      r"not yet invented", r"yet to be invented")
    negation_span = re.compile(
        r"\b(?:no|without)\s+([a-z][a-z\- ]{2,40}?)"
        r"(?=\s*,|\s+and\s+no\b|\s+and\s+without\b|\s+neither\b|\s+none\b|\s*\.|$)")
    stop = set("and the for with from that this into over under being than "
               "then which what when were was has have had does did already "
               "both only also even more most make made gives give were "
               "being could would should before after still about".split())

    def keywords(text):
        return {w for w in re.findall(r"[a-z]{5,}", text.lower()) if w not in stop}

    out = []
    for k, n in sorted(nodes.items()):
        low = (n.get("note") or "").lower()
        hit = None
        for pat in disclaim_pats:
            m = re.search(pat, low)
            if m:
                hit = m
                break
        if not hit:
            continue
        sent_start = low.rfind(".", 0, hit.start())
        sent_start = 0 if sent_start == -1 else sent_start + 1
        window = low[sent_start:hit.start()]
        wkw = set()
        for span in negation_span.findall(window):
            wkw |= keywords(span)
        if not wkw:
            continue
        prereq_ids = list(n.get("pre") or [])
        for g in (n.get("req_any") or []):
            prereq_ids.extend((g.get("options") or {}).keys())
        for pid in prereq_ids:
            pn = nodes.get(pid)
            if not pn:
                continue
            pkw = keywords(pn.get("name") or "") | {pid.lower()}
            if wkw & pkw:
                out.append((k, pid, hit.group(0), sorted(wkw & pkw)))
    return out


check("the bug class, not just the instance: no node's note disclaims a "
      "prerequisite as not having existed yet while the node's own pre "
      "or req_any (including a genuine multi-option substitution) still "
      "requires it - re-run against a restored copy of the original "
      "req_any to confirm this scanner actually catches the fix it is "
      "here to pin",
      _disclaimed_prereq_contradictions(NODES) == [],
      _disclaimed_prereq_contradictions(NODES))
_nodes_predisclaim = copy.deepcopy(NODES)
_nodes_predisclaim["point_contact_transistor"]["req_any"] = [
    {"group": "semiconductor", "options": {"silicon_path": 0.9, "single_crystal": 1.0}}]
check("...and the scanner is not vacuous: it does flag the original, "
      "now-fixed req_any when restored on a copy of the tree",
      _disclaimed_prereq_contradictions(_nodes_predisclaim) != [],
      _disclaimed_prereq_contradictions(_nodes_predisclaim))

# --- TOP_PROBLEMS #4, generalised: EVERY `located_material` node rolls
# `self.rng.random() < n["risk"]` every year it is active, with no modifier
# of any kind. Ten of the category's eleven nodes shared risk 0.95 - the
# single highest value anywhere in the 2,833-node tree outside this one
# category (`expedition`, the category modelling the actual voyage these
# sit behind in `pre`, averages 0.35 and tops out at 0.55), and the
# eleventh (med_coca_alkaloid) was already tuned to 0.25, which is why this
# reads as an unrevisited placeholder rather than a researched figure: none
# of these notes describe a 19-in-20 failure, they describe buying an
# already-characterised commodity from people who already produce it, or
# carrying home seed stock of a crop grown locally forever after. This is
# what cost the naive14 player "years" on platinum specifically (gating the
# vacuum tube, hence the goal) with "no visible way to improve the odds" -
# pinned at the category level so a future located_material node cannot
# reintroduce the same placeholder unnoticed.
_located_risks = {k: n["risk"] for k, n in NODES.items() if n.get("cat") == "located_material"}
check("no located_material node rolls a near-certain failure every year - "
      "0.95 was an unrevisited placeholder copied across ten of the "
      "category's eleven nodes, not a researched figure",
      _located_risks and max(_located_risks.values()) <= 0.3,
      sorted(_located_risks.items(), key=lambda kv: -kv[1])[:3])

# --- TOP_PROBLEMS #12, generalised beyond the one platinum instance
# already named there: a data file (as opposed to the `kb` field's
# deliberate rome/knowledge/*.md citations, shown to the player on every
# `why` screen as an in-fiction "recipe" reference) is not something a
# player's own note should ever send them to read.
_geo_leaks = [k for k, n in NODES.items() if "data/world/" in (n.get("note") or "")]
check("no node's player-facing note sends the player to read a data file "
      "out of the game - ten notes did ('See data/world/geography.json "
      "...'), platinum among them, found and fixed as a family rather "
      "than one at a time",
      _geo_leaks == [], _geo_leaks)

# --- naive14, ROUND 2 (a Mexica fog-off run): the civilization's own intro
# says "no wheel in practical use... no amount of teaching will fix it", but
# tr_hopper_wagon was startable turn one with empty `pre`, and the needs_first
# mechanism that already exists for exactly this purpose (and is already used
# for harness/saddle/pack-animal nodes) never named it. Verified against the
# actual tree, not assumed: a wheeled CART needs something to pull it, which
# is the real Mesoamerican absence (there are wheeled toys; there is no
# draught animal), so the fix gates the vehicles on exp_import_draught_animals
# alongside the harnesses, and deliberately leaves the wheel concept itself
# (lnd_wheel_spoked), human-powered wheeled things (lnd_wheelbarrow,
# lnd_litter) and anything turned by water or by people (en_overshot_wheel
# and kin) alone - they owe nothing to a draught animal.
_mex_needs_first = S.load_civ("mexica_1500")["needs_first"]["draught animals"]["ids"]
_GATED_VEHICLES = ("tr_hopper_wagon", "lnd_two_wheel_cart", "lnd_four_wheel_cart",
                   "mil_artillery_carriage", "pwr_animal_treadmill")
check("the wheeled/animal-powered vehicles a Mexica player actually reached "
      "turn one are now in the same needs_first group as the harnesses, not "
      "a separate, unenforced list",
      all(k in _mex_needs_first for k in _GATED_VEHICLES),
      [k for k in _GATED_VEHICLES if k not in _mex_needs_first])
_s_mex2 = sim(civ="mexica_1500")
check("...and a fresh Mexica founder cannot start any of them turn one",
      not any(_s_mex2.can_start(k) for k in _GATED_VEHICLES),
      [k for k in _GATED_VEHICLES if _s_mex2.can_start(k)])
check("...including the ambient-grant path, not only explicit `start` - "
      "pwr_animal_treadmill is tier 0 with no cost, which is exactly what "
      "grant_ambient() hands out for free the moment prerequisites clear, "
      "and it already checks needs_first before doing so",
      "pwr_animal_treadmill" not in _s_mex2.done, "pwr_animal_treadmill")
_s_mex3 = sim(civ="mexica_1500")
_s_mex3.done.add("exp_import_draught_animals")
_s_mex3._done_changed()
# needs_first(), not can_start(): mil_artillery_carriage also needs
# mat_wrought_iron and mil_trunnion, real and unrelated prerequisites this
# fix does not touch (Mexica's own handicap is "no iron", a separate,
# legitimate constraint) - so the thing this check must confirm is that the
# draught-animal GATE specifically is gone, not that every other real
# requirement has also been met by one node on its own.
check("...and importing draught animals lifts the gate on all of them, the "
      "same way it already does for horse_collar and the rest - checked as "
      "needs_first() clearing, not as can_start(), since a vehicle can "
      "have its own further, unrelated prerequisites (mil_artillery_carriage "
      "still wants iron and a trunnion)",
      all(_s_mex3.needs_first(k)[0] is None for k in _GATED_VEHICLES),
      [(k, _s_mex3.needs_first(k)) for k in _GATED_VEHICLES
       if _s_mex3.needs_first(k)[0] is not None])
_s_mex4 = sim(civ="mexica_1500")
check("the wheel concept itself, human-powered wheeled transport, and "
      "water/human-turned machinery are NOT swept into the same gate - "
      "only the animal-drawn vehicles were the bug",
      _s_mex4.can_start("lnd_wheel_spoked") is False
      and "lnd_wheel_spoked" in _s_mex4.done  # already granted, not gated
      and "lnd_litter" in _s_mex4.done
      and "cap_power_muscle" in _s_mex4.done,
      (_s_mex4.can_start("lnd_wheel_spoked"),
       "lnd_wheel_spoked" in _s_mex4.done,
       "lnd_litter" in _s_mex4.done,
       "cap_power_muscle" in _s_mex4.done))

