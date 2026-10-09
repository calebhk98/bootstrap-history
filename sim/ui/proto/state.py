"""The agent state reply: founder, standing, progress, risk, goal and the assembler _agent_state."""

from .state_waiting import (
    _agent_end_reason, _founder_death_info, _goal_progress_count,
    _risk_without_the_essays, _staff_fraction_note,
)
from .state_projects import (
    _agent_state_active_projects, _agent_state_headline_money,
    _agent_state_operations, _agent_state_spend_and_net,
    _agent_state_training_and_hours,
)
import sim.engine.ui_port as ui_port
from sim.engine.ui_port import shortage_conditions
from sim.engine.ui_port import knowledge_loss_warning
from .step_alerts import demographic_emergency
from .state_succession import succession_block


def _agent_state_founder(sim):
    """Alive or not, and if not, when and how old - plus the two staff
    headline counts that sit next to it on the same screen.
    """
    return {
        "seat": sim.state.acting_seat,
        "founder_alive": sim.founder_alive,
        "founder_age": (sim.founder_age()
                        if sim.founder_alive and not sim.cfg.get("immortal", True) else None),
        "founder_usual_age_at_death": (
            [round(sim.cfg["founder_arrival_age"] + sim.cfg["founder_life_mean"] - sim.cfg["founder_life_sd"]),
             round(sim.cfg["founder_arrival_age"] + sim.cfg["founder_life_mean"] + sim.cfg["founder_life_sd"])]
            if not sim.cfg.get("immortal", True) else None),
        # THE AGE ITSELF, AS A FIELD, not only inside a log sentence a script
        # would have to parse. See _founder_death_info.
        "founder_died_aged": (_founder_death_info(sim) or {}).get("aged_about"),
        "founder_died_in": (_founder_death_info(sim) or {}).get("year"),
        "scholars": round(sim.scholars, 2), "artisans": round(sim.artisans, 2),
        "directors_extra": round(sim.directors_extra, 2),
        "succession": succession_block(sim),
    }


def _agent_state_standing(sim):
    """Reputation, scandal, eminence and the other soft-power gauges,
    literacy and its ceilings, and how far what you built has diffused.
    """
    # WHAT YOU BUILT HAS CHANGED THE COUNTRY - see SocietyMixin.
    # world_diffusion_report (society.py). Computed once here, gated to
    # None while dormant, so a fresh game's `state full` reply (already the
    # reply most often bumping the "state full stays readable" byte budget)
    # pays nothing for a mechanism that has not fired yet - same pattern as
    # _worth_knowing_early just below.
    _wd = sim.world_diffusion_report()
    return {
        # NO "suspicion" FIELD: `scandal` is the live mechanic (see core.py:
        # "doing something a society cannot explain is alarming; doing a
        # lot of ordinary things over decades is not"). `suspicion` is set
        # to 0.0 at startup and never written again - reporting a dead
        # number every turn is worse than not having it: it teaches the
        # player that a live mechanic is broken.
        "reputation": round(sim.reputation, 1),
        "scandal": round(sim.scandal, 2), "eminence": round(sim.eminence, 2),
        "protection": round(sim.protection, 3), "familiarity": round(sim.familiarity, 3),
        # HOW EDUCATED THIS SOCIETY IS, AND HOW FAR THAT COULD GO: the
        # ceiling has to be shown alongside the current figure, not just
        # the figure alone, or a founder watching literacy_general climb
        # with no sense of where it stops cannot tell a slow success from
        # a mechanism that has already maxed out. See
        # SocietyMixin.literacy_ceiling_general/_elite (society.py).
        "literacy": {
            "general": round(float(sim.civ.get("literacy_general", 0.0)), 3),
            "general_ceiling_now": round(sim.literacy_ceiling_general(), 3),
            "elite": round(float(sim.civ.get("literacy_elite", 0.0)), 3),
            "elite_ceiling": round(sim.literacy_ceiling_elite(), 3),
            "schools_actually_teaching": ui_port.schooling_flow(sim) > 0.0,
            "farm_share_of_working_hours": round(sim.labour.farm_share_of_hours(), 3),
        },
        # HOW MUCH OF WHAT YOU RUN HAS LEAKED TO COMPETITORS. See
        # SocietyMixin.diffusion_share/diffusion_index (society.py) for what
        # moves this; it is not yet spent anywhere in this engine's own
        # pricing, only reported, because that spending is another agent's
        # seam to wire in (see that function's own docstring).
        "diffusion_index": round(sim.diffusion_index(), 3),
        # THE COUNTRY, NOT ONLY YOUR OWN MARKET SHARE. Present only once
        # something the founder built has actually begun to spread - see
        # world_diffusion_report's own docstring for the None gate.
        **({"world_diffusion": _wd} if _wd else {}),
    }


def _agent_state_progress(sim, active):
    """What is done versus granted, the active projects themselves, staff
    and trades, and the household and policy figures that go with them.
    """
    return {
        # SEPARATE THE TWO: technologies the society already had (granted)
        # and technologies actually earned must not be conflated - "you
        # have 140 technologies" and "you have built 3 technologies" are
        # very different situations.
        "done_count": len(sim.done),
        "done_granted": len(sim.granted & sim.done),
        "done_earned": len(sim.done - sim.granted),
        "active": active,
        # STAFF IS NOT A TECHNICAL PREREQUISITE, so it appears in no
        # dependency list, and the remedy for a stalled ceiling only ever
        # showing up in a refusal message means a player who never happens
        # to try a staff-gated project never sees it at all. Tell them
        # unprompted.
        "how_to_grow_staff": {
            "scholars": sim.labour.staff_advice("scholars"),
            "artisans": sim.labour.staff_advice("artisans"),
        },
        "where_the_money_comes_from": sim.revenue_sources(),
        "employees": {trade: round(value, 2) for trade, value in sorted(sim.employees.items()) if value > 0.005},
        "employees_total": round(sum(sim.employees.values()), 2),
        "household_places_used_of_all": "%.1f of %.1f"
            % (sim.labour.headcount(), sim.labour.headcount() + max(0.0, sim.labour.household_room())),
        "annual_wage_bill": round(sim.labour.wage_bill(), 1),
        # WHAT THE PROMPT'S sch/art MEAN: those two figures count yourself
        # and any hours you have bought, so the prompt can read "sch 1
        # art 1" on a turn where you employ nobody, which looks like a
        # contradiction next to "EMPLOY: 0 people" unless this says so.
        # Both are right; they are answering different questions.
        "what_you_can_field": (
            "counting yourself and hours you have bought: %.1f scholars and "
            "%.1f craft hands. That pair is what the prompt shows and what "
            "'why' and 'start' test a project against; the count above is "
            "people on your payroll."
            % (sim.labour.effective_scholars(), sim.labour.craft_hands_available())),
        # FRACTIONS ARE REAL, NOT A DISPLAY GLITCH: staff grow and decay
        # gradually (hiring phases in, training takes years, attrition is
        # a yearly 3.5%), so at any given moment a trade you have IS a
        # partial year's worth of one more or one fewer person, the same
        # way a company's headcount can be "40.5 FTE". Said only when it
        # would actually be confusing - a whole-number staff needs no
        # footnote.
        # _staff_fraction_note, NOT A SECOND COPY OF THIS EXPLANATION - see
        # its own docstring. `labour` shows the identical fractional counts
        # and must say the identical thing about them.
        "staff_are_fractional_because": _staff_fraction_note(sim),
        "trades_you_created": sorted(sim.trades_created),
        # WHICH OF THOSE THE SOCIETY NOW SUPPLIES ON ITS OWN. See
        # SocietyMixin.advance_society (society.py): once a taught trade has
        # been established long enough, with schools actually running, it
        # stops being only the founder's secret.
        "trades_society_now_has_on_its_own": sorted(sim.trades_endemic),
        "mothballed": sorted(getattr(sim, "mothballed", set())),
        "policy": dict(sim.policy),
        "in_bondage_for_debt": round(sim.bondage_years_left, 1),
        "debt_still_to_work_off": round(sim.bondage_debt, 1),
    }


def _agent_state_risk_and_pressure(sim):
    """The court's jealousy and the treasury's attention, credit and
    debt, the knowledge-loss risk, the scandal clock, and the physical
    resource figures (throttle, forest, mines, unfree labour).
    """
    return {
        # HOW CLOSE YOU ARE TO BEING DESTROYED FOR BEING TOO LARGE, and what
        # changes it: a bare number with no threshold, no trend and no
        # lever leaves nothing telling a player they are one bad year from
        # the end. At a successful late game the equilibrium lands within
        # five per cent of the threshold, which makes the outcome look like
        # a coin toss decided by noise unless the real levers are visible -
        # a dispersed academy network cuts it by a third, and getting close
        # to the throne raises it by half. An unseen lever is not a
        # choice.
        "prominence": sim.eminence_report(),
        # THE OTHER HALF OF BEING LARGE: eminence_report() above is the
        # court's jealousy of a great man; this is the treasury's own
        # interest in a large enterprise - requisition, a pressed office, a
        # demand for military supply, and confiscation as a tail risk at
        # the top of the same scale. See SocietyMixin.state_pressure_report
        # (society.py).
        "state_attention": sim.state_pressure_report(),
        "credit_limit": round(sim.credit_limit(), 1),
        "debt_interest_rate": round(sim.debt_interest_rate(), 4),
        "interest_paid_total": round(getattr(sim, "interest_paid", 0.0), 1),
        # WITHOUT THE HISTORY ESSAYS: each dated hazard carries a real
        # historical note, several of them a couple of hundred words, and
        # embedding the lot here would balloon a `state full` reply to tens
        # of thousands of bytes. The numbers stay; the prose lives in
        # `risk`, which is the command you type when you want it.
        "knowledge_risk": _risk_without_the_essays(sim.knowledge_risk()),
        # THE OTHER HAZARD THAT ENDS THE RUN, on the same screen as the one that
        # already explains itself. See step() 6.
        "scandal_danger": sim.cfg["suspicion_danger"],
        "chance_of_being_denounced_this_year": round(
            max(0.0, (sim.scandal - sim.cfg["suspicion_danger"]) / 60.0), 4),
        # AND WHICH WAY IT IS GOING: the chance above is computed from where
        # scandal stands now, and the roll happens after a year in which it
        # moves, so the figure alone is honest about today and blind to the
        # step about to happen - a reading of "0%" can still be followed by
        # denunciation inside one step if scandal is rising fast. The trend
        # has to be shown too.
        "scandal_now": round(sim.scandal, 1),
        "scandal_rose_by_last_year": (
            round(sim.scandal - sim.scandal_last_year, 1)
            if getattr(sim, "scandal_last_year", None) is not None else None),
        "years_until_scandal_crosses_the_line": (
            int(max(0.0, (sim.cfg["suspicion_danger"] - sim.scandal))
                / (sim.scandal - sim.scandal_last_year)) + 1
            if (getattr(sim, "scandal_last_year", None) is not None
                and sim.scandal - sim.scandal_last_year > 0.05
                and sim.scandal < sim.cfg["suspicion_danger"]) else None),
        "resource_throttle": round(sim.throttle, 3), "throttle_binding": sim.binding,
        "forest_ha": round(sim.forest_ha, 1),
        "mine_capacity": {material: round(value, 1) for material, value in sim.mine_capacity.items()},
        "slaves": sim.slaves, "freedmen": sim.freedmen,
        "scholars_including_you": round(sim.labour.effective_scholars(), 2),
    }


def _agent_state_goal(sim, nodes, end_reason):
    """The goal itself (fog-safe), whether and when it was reached, and
    whether the run itself has ended.
    """
    return {
        "founder_ages": not sim.cfg.get("immortal", True),
        "goal": None if sim.fog else sim.goal,
        # The NAME, not the id, so it survives fog without handing back the
        # prerequisite crawl the visibility guard exists to stop.
        "goal_in_words": (sim.nodes[sim.goal]["name"]
                          if sim.goal in sim.nodes else None),
        "goal_reached": sim.goal_year is not None, "goal_year": sim.goal_year,
        # THE FOG-SAFE VERSION OF final_report's "146 nodes in all; you had
        # 122": the TOTAL is withheld until the run ends on purpose,
        # because it is the size of the tree's own spoiler surface (same
        # reasoning as
        # downstream_count being hidden for a single node, just applied to
        # the whole road at once). So during play this says only how many of
        # the road's nodes you already have, never how many there are in
        # all and never which ones remain - you get a sense of progress
        # without being handed a map.
        "on_the_road_to_the_goal_so_far": (
            _goal_progress_count(sim, nodes) if sim.fog else None),
        "fog_of_war": sim.fog,
        "manual": sim.manual, "ended": end_reason is not None, "end_reason": end_reason,
    }


def _agent_state_shorten(out, full):
    """`full:false` (the default): fold the heaviest blocks down to a
    pointer at the command that shows them in full, so an ordinary
    `state` stays short. See the comment above for why - unchanged from
    when this lived inline in _agent_state.
    """
    # A SHORT REPLY BY DEFAULT: embedding a hazard briefing (or other heavy
    # blocks) verbatim on every single call would return dozens of fields
    # and several kilobytes even when nothing about them changed since the
    # last call. The three heaviest blocks have commands of their own, so
    # a player reads them when they want them, instead of every turn.
    if not full:
        moved = {"knowledge_risk": "risk", "how_to_grow_staff": "labour",
                 "policy": "policy", "where_the_money_comes_from": "money",
                 "training_pending": "labour"}
        elided = []
        for field, where in moved.items():
            if field in out:
                if field == "knowledge_risk":
                    knowledge_risk = out[field]
                    haz = [hazard["name"] for hazard in knowledge_risk.get("known_hazards_ahead", [])
                           if hazard.get("in_progress")]
                    out["at_risk"] = {
                        "technologies_you_could_lose": knowledge_risk.get("technologies_at_risk"),
                        "hedged_by": knowledge_risk.get("hedged_by"),
                        "happening_now": haz or None,
                        "hazards_still_ahead": len(knowledge_risk.get("known_hazards_ahead", [])),
                        "in_full": '{"cmd":"risk"}'}
                elif field == "training_pending" and out[field]:
                    out["in_training"] = len(out[field])
                del out[field]
                elided.append('%s -> {"cmd":"%s"}' % (field, where))
        # THE ONE COMMAND FOR "WHY AM I NOT GETTING ON", advertised where a
        # player will see it every turn: without it, a long stall's cause
        # is discoverable only by guessing at `why`.
        elided.append('why_you_are_not_getting_on -> {"cmd":"stuck"}')
        out["also_available"] = elided
        out["everything_at_once"] = '{"cmd":"state","full":true}'
    return out


def _agent_state(sim, nodes, cmd=None):
    """The JSON state reply: the single most-used command in the
    protocol, and the one an agent player reads every turn.

    Split into one function per concern, the same pattern _node_explain
    uses in techtree.py: each _agent_state_* helper returns its own
    dict and decides nothing about any other section, and this function
    only assembles their pieces, via out.update(), in a fixed order.
    """
    active = _agent_state_active_projects(sim, nodes)
    end_reason = _agent_end_reason(sim)
    full = bool((cmd or {}).get("full"))
    end_year = getattr(sim, "end_year", sim.cfg["start_year"] + sim.cfg["horizon_years"])
    out = {}
    out.update(_agent_state_headline_money(sim, end_year))
    out.update(_agent_state_operations(sim, nodes))
    out.update(_agent_state_spend_and_net(sim))
    # free_hours_going_unused (among the rest of this section's fields) is
    # produced by this call, inside _agent_state's own call graph, not by a
    # screen-specific layer wrapped around 'state' alone - see
    # test_parallelism_note.py's own check that `step`'s reply, which is
    # built from this exact same _agent_state() call, gets it too.
    out.update(_agent_state_training_and_hours(sim, active, full))
    out.update(_agent_state_founder(sim))
    out.update(_agent_state_standing(sim))
    out.update(_agent_state_progress(sim, active))
    out.update(_agent_state_risk_and_pressure(sim))
    out.update(_agent_state_goal(sim, nodes, end_reason))
    warning = knowledge_loss_warning(sim)
    if warning:
        out["knowledge_loss_warning"] = warning
    emergency = demographic_emergency(sim.state.population.population_change_last_year)
    if emergency:
        out["demographic_emergency"] = emergency
    conditions = shortage_conditions.condition_rows(sim)
    if conditions:
        out["conditions"] = conditions
    living_stock = sim.held_living_stock()
    if living_stock:
        out["living_stock"] = living_stock
    return _agent_state_shorten(out, full)
