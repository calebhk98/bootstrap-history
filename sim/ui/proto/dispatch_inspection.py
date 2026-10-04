"""Read-only overview commands: state, available, log, score, finish, why."""

from .command_registry import command
from sim.ui.figures import FIGURES
from .dispatch_figures import figure_reply
from sim.ui.market_report import goods_market_line, opening_effect
from sim.engine.ui_port import active_years_left, remaining_critical_path_years
from .explain_once import already_explained
from .nodes import _did_you_mean
from .score import final_report, score_report
from .score_change import attach_change_since_last_score
from .state import _agent_state
from .state_log import _agent_log
from .techtree import _agent_available, _node_explain


@command("state", group="overview", aliases=("s", "st", "status"),
         summary="where you stand",
         usage=["state", "state full", "state compact"],
         options={"full": "include every field, not only the headline ones",
                  "json / compact": "json is the raw reply; compact is a short summary (year, money, net_per_year, founder_hours_free, projects with blockers, concerns, standing, danger, nearest_goal_blocker)"},
         description="Year, money, income, founder hours, active projects with "
                     "what each is waiting on, and what to look at next.")
def _cmd_state(sim, nodes, cmd, ended):
    out = dict(ok=True, **_agent_state(sim, nodes, cmd))
    if out.get("you_know_how_to_run_but_have_not_opened") and already_explained(sim, "shut_concerns_pointer", cmd):
        out["shut_concerns_pointer_seen"] = True
    return out



@command("available", group="overview", aliases=("a", "av"),
         summary="what you could begin today",
         usage=["available", "available <subject>", "available find <text>",
                "available state:blocked tag:<topic>", "available sort:price reverse",
                "available metallurgy sort risk limit 10 offset 10"],
         options={"subject / find": "narrow by subject word or search text",
                  "afford": "only what you can pay for now",
                  "all:true": "every row, not the summary by subject",
                  "limit / offset": "page through the rows",
                  "sort": "price, hours, years, earns, upkeep, risk, alpha or fewest_missing",
                  "reverse": "flip the order",
                  "state": "startable, blocked, active or done (blocked rows say what is missing)",
                  "tag / category": "narrow by topic or node category"},
         description="Summarised by subject, with cost, founder hours and risk. "
                     "An empty search suggests tags to try. fewest_missing orders the "
                     "heard-of list by how few of a thing's own prerequisites are "
                     "missing, not by distance to a goal; see path for that.")
def _cmd_available(sim, nodes, cmd, ended):
    return _agent_available(sim, nodes, cmd)



@command("log", group="overview", aliases=("history", "diary", "logs", "journal"),
         summary="your own exact history, most recent first",
         usage=["log", "log failures:true", "log find:<text> since:<year> before:<year>",
                "log oldest", "log limit:20 offset:20"],
         options={"failures": "only failures", "find": "text to search for",
                  "since / before": "year bounds", "oldest": "oldest first",
                  "limit / offset": "page size and position"},
         description="Starts, completions, failures, hazards, openings, closures and "
                     "staffing, paginated; never the whole record at once.")
def _cmd_log(sim, nodes, cmd, ended):
    return _agent_log(sim, cmd)



@command("score", shape="bare", group="overview",
         summary="what you are optimising, any time",
         usage=["score"], options={},
         description="Each ending-score component, raw and weighted. Under fog the "
                     "technology-coverage share stays withheld until the run is over.")
def _cmd_score(sim, nodes, cmd, ended):
    return {"ok": True, **attach_change_since_last_score(sim, score_report(sim, nodes))}



@command("finish", group="game",
         summary="end the run and see the score",
         usage=["finish"], options={},
         description="Ends the run here and shows the full score, including the "
                     "technology share fog otherwise withholds. The save still loads, "
                     "but the run stays ended.")
def _cmd_finish(sim, nodes, cmd, ended):
    if not ended:
        sim.dead_reason = "you finished the run in %d AD and asked for the score" % sim.year
    return {"ok": True, **final_report(sim, nodes)}


@command("why", shape="tech", group="overview", aliases=("explain", "look", "inspect"),
         summary="everything known about one thing",
         usage=["why <id or name>", "why <id> compact", "why <id> full"],
         options={"<id>": "a technology or concern, by id or name",
                  "compact": "short reply: status, blocked_by, explanation",
                  "full": "repeat the explanations otherwise shown once per game"},
         description="Cost, staff, risk, chain, what it unlocks, and exactly why it "
                     "is or is not startable right now.")
def _cmd_why(sim, nodes, cmd, ended):
    node_id = cmd.get("id")
    if node_id in FIGURES and node_id not in nodes:
        return figure_reply(sim, node_id)
    # The goal is the one thing you were told the name of on arrival; see
    # the _goal_why note on the fog guard above for why it is `why` alone.
    if (isinstance(node_id, str) and node_id in nodes and not sim.is_visible(node_id)
            and node_id != sim.goal):
        return {"ok": False,
                "error": "you have never heard of that. You know what you have "
                         "built and what you could begin now; use 'available'."}
    if not isinstance(node_id, str):
        return {"ok": False,
                "error": 'which one? give an id, for example '
                         '{"cmd":"why","id":"units_standards"}. '
                         'Use {"cmd":"available"} to see what you could begin.'
                if node_id is None else
                "id must be a name in quotes, not %s" % type(node_id).__name__}
    if node_id not in nodes:
        # Only blame the fog when there IS any: with fog off, the error must
        # not claim fog is limiting the suggestions, in a game started with
        # the whole tree visible.
        return {"ok": False, "error": "unknown node %r. did you mean: %s"
                % (node_id, ", ".join(_did_you_mean(node_id, nodes, sim=sim))
                   or ("no idea, and under fog of war I can only suggest "
                       "things you have heard of"
                       if sim.fog
                       else "no idea - nothing in the tree is spelled much "
                            "like that"))}
    explained = _node_explain(sim, nodes, node_id)
    if explained.get("staff_to_keep_it_open_means"):
        if already_explained(sim, "staffing_means", cmd):
            explained["staff_to_keep_it_open_means"] = (
                "a share of their year, not a headcount, and separate from "
                "the crew that builds it ('why %s full' explains it again)"
                % node_id)
        if already_explained(sim, "staffing_share", cmd):
            explained["these_are_a_share_of_their_year_not_a_headcount"] = None
    # The floor still ahead: finished nodes count nothing, active ones what
    # is left of them. critical_path_years stays the from-scratch floor.
    explained["critical_path_years_remaining"] = (
        None if sim.fog else round(remaining_critical_path_years(
            nodes, node_id, sim.done, active_years_left(nodes, sim.active)), 1))
    if goods_market_line(sim, node_id):
        explained["goods_market_line"] = goods_market_line(sim, node_id)
    if opening_effect(sim, node_id):
        explained["opening_effect"] = opening_effect(sim, node_id)
    return dict(ok=True, **explained)
