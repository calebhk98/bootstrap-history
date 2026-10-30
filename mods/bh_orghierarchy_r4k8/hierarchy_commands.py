"""Organisational hierarchy for directed work (Complaints/closed/104): the layers of managers a workforce needs.

Span of control is a labelled heuristic (span_data.json) that known technologies raise; managers needed follow from
workers / span, layer by layer. The functions above `register` are a pure rule any actor (firm, state, household)
can call with its own headcount, manager hours and known technologies.
"""
import json
import math
import os

from sim.mod_api import FireStaff, HireStaff

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "span_data.json")


def load_parameters(path=DATA_FILE):
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def channel_factors(parameters, known_nodes):
    """{channel: (factor, node_id or None)}: the best known technology per channel (1.0 when none is known)."""
    found = {}
    for channel, entry in parameters["channels"].items():
        known = {node_id: factor for node_id, factor in entry["factor_when_known"].items() if node_id in known_nodes}
        best = min(known, key=known.get) if known else None
        found[channel] = (known[best] if best else 1.0, best)
    return found


def span_of_control(manager_hours_per_year, parameters, factors):
    """Direct reports one manager can carry: supervising hours / coordination hours one report costs."""
    supervising = manager_hours_per_year * parameters["supervision_share_of_manager_hours"]["value"]
    scale = 1.0
    for factor, _node in factors.values():
        scale *= factor
    return max(2.0, supervising / (parameters["coordination_hours_per_report_per_year"]["value"] * scale))


def managers_by_layer(workers, span):
    """[managers over the workers, managers over those managers, ...]; the apex actor directs the last layer."""
    layers = []
    reports = math.ceil(workers)
    while reports > span:
        reports = math.ceil(reports / span)
        layers.append(reports)
    return layers


def order_fidelity(layer_count, parameters, factors):
    """Share of an order's intent that reaches the workers through this many layers."""
    return (1.0 - parameters["order_loss_per_layer"]["value"] * factors["messaging"][0]) ** layer_count


def plan(workers, manager_hours_per_year, parameters, known_nodes):
    factors = channel_factors(parameters, known_nodes)
    span = span_of_control(manager_hours_per_year, parameters, factors)
    layers = managers_by_layer(workers, span)
    return {"workers": workers, "span_of_control": span, "layers": len(layers), "managers_by_layer": layers,
            "managers_total": sum(layers), "factors": factors,
            "apex_direct_reports": layers[-1] if layers else math.ceil(workers),
            "order_fidelity": order_fidelity(len(layers), parameters, factors)}


def founder_direct_reports(workers, span, hired):
    """People the apex actor still directs itself when `hired` managers stand between it and `workers`: each manager
    hired from the lowest layer up takes `span` reports off the apex and adds one."""
    reports = math.ceil(workers)
    for layer in managers_by_layer(workers, span):
        covered = min(layer, hired)
        hired -= covered
        if covered < layer:
            return max(1, reports - covered * (span - 1))
        reports = layer
    return reports


def apex_overhead_hours(workers, manager_hours, parameters, known_nodes, hired):
    """Hours a year the apex spends on its direct reports: reports times the coordination hours one costs."""
    factors = channel_factors(parameters, known_nodes)
    span = span_of_control(manager_hours, parameters, factors)
    scale = 1.0
    for factor, _node in factors.values():
        scale *= factor
    return founder_direct_reports(workers, span, hired) * parameters["coordination_hours_per_report_per_year"]["value"] * scale


def technology_contributions(workers, manager_hours, parameters, known_nodes, in_tree):
    """For each listed technology that exists in the tree: span and managers needed with it known and without it."""
    rows = []
    for channel, entry in parameters["channels"].items():
        for node_id in entry["factor_when_known"]:
            if node_id not in in_tree:
                continue
            known = node_id in known_nodes
            with_it = plan(workers, manager_hours, parameters, known_nodes | {node_id})
            without_it = plan(workers, manager_hours, parameters, known_nodes - {node_id})
            rows.append({"node": node_id, "channel": channel, "known": known,
                         "factor": entry["factor_when_known"][node_id],
                         "span_with_it": round(with_it["span_of_control"], 1),
                         "managers_needed_with_it": with_it["managers_total"],
                         "managers_needed_without_it": without_it["managers_total"]})
    return rows


def _manager_hours(access):
    return float(access.view("game_config")()["director_hours_per_year"])


def _workers_from(access, cmd, managers_hired):
    """Headcount to organise: an explicit `workers` or `hours` (a firm or state may ask about any size), else the staff."""
    if cmd.get("workers") is not None:
        return float(cmd["workers"]), "asked"
    if cmd.get("hours") is not None:
        return float(cmd["hours"]) / access.view("hours_per_person_year")(), "asked (worker-hours / hours per person-year)"
    staff = sum(access.view("staff")()["employees"].values()) - managers_hired
    return max(0.0, staff), "your staff, not counting managers this mod hired"


def register(api):
    parameters = load_parameters()
    api.reads("game_config", "hours_per_person_year", "techniques_held", "staff", "hours_available", "hire_check", "wage_bill")
    api.sends(FireStaff, HireStaff)
    manager_trade = parameters["manager_trade"]["value"]

    def hired(access):
        return int(access.memory().get("managers_hired", 0))

    @api.director_overhead
    def overhead(access):
        workers, _source = _workers_from(access, {}, hired(access))
        return apex_overhead_hours(workers, _manager_hours(access), parameters, set(access.view("techniques_held")()), hired(access))

    @api.command("hierarchy", group="labour", aliases=("span", "orgchart"),
                 summary="the layers of managers a workforce needs, and what each technology contributes",
                 usage=["bh_orghierarchy_r4k8:hierarchy", '{"cmd":"bh_orghierarchy_r4k8:hierarchy","workers":5000}',
                        '{"cmd":"bh_orghierarchy_r4k8:hierarchy","hours":100000}'],
                 options={"workers": "headcount to organise (default: your staff)",
                          "hours": "worker-hours a year to organise (instead of workers)"},
                 description="Read only. Span of control is the hours a manager can give to supervising divided by "
                             "the coordination hours one report costs; known technologies cut those hours. Managers "
                             "needed are workers / span, layer by layer, and each layer loses part of an order. "
                             "Spans and losses are labelled heuristics (span_data.json). Spends nothing.")
    def hierarchy(access, nodes, cmd, ended):
        workers, source = _workers_from(access, cmd, hired(access))
        known = set(access.view("techniques_held")())
        manager_hours = _manager_hours(access)
        result = plan(workers, manager_hours, parameters, known)
        pool = access.view("hours_available")["director_pool"]
        overhead_hours = result["managers_total"] * manager_hours
        return {
            "ok": True, "workers": workers, "workers_source": source,
            "span_of_control": round(result["span_of_control"], 1),
            "layers_of_management": result["layers"],
            "managers_by_layer_from_the_workers_up": result["managers_by_layer"],
            "managers_total": result["managers_total"],
            "apex_direct_reports": result["apex_direct_reports"],
            "manager_hours_a_year": round(overhead_hours, 1),
            "directed_hours_pool_this_year": round(pool, 1),
            "orders_reaching_workers_intact": round(result["order_fidelity"], 3),
            "known_channels": {channel: {"best_known": node, "coordination_factor": factor}
                               for channel, (factor, node) in result["factors"].items()},
            "technologies": technology_contributions(workers, manager_hours, parameters, known, nodes),
            "managers_this_mod_hired": hired(access), "manager_trade": manager_trade,
            "note": "Heuristic spans (see span_data.json); nothing here changes the game unless you run staff_managers.",
        }

    @api.command("staff_managers", group="labour",
                 summary="hire the managers the hierarchy needs, or release the surplus",
                 usage=['{"cmd":"bh_orghierarchy_r4k8:staff_managers"}',
                        '{"cmd":"bh_orghierarchy_r4k8:staff_managers","release":true}'],
                 options={"release": "let go managers this mod hired beyond what is now needed"},
                 description="Opt in. Tops up the managers hired through this command to the number the hierarchy needs "
                             "for your staff, through the ordinary hire path (fee, first year's wage, the labour "
                             "market's own supply limits). With release it lets go the surplus. It does not run by "
                             "itself; managers hired shrink the hours your own direct reports take from the pool.")
    def staff_managers(access, nodes, cmd, ended):
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        workers, _source = _workers_from(access, {}, hired(access))
        needed = plan(workers, _manager_hours(access), parameters, set(access.view("techniques_held")()))["managers_total"]
        memory = access.memory()
        have = int(memory.get("managers_hired", 0))
        if cmd.get("release"):
            surplus = have - needed
            if surplus <= 0:
                return {"ok": True, "released": 0, "managers_needed": needed, "managers_this_mod_hired": have}
            done, message = access.send(FireStaff(manager_trade, surplus))
            if done:
                memory["managers_hired"] = have - surplus
            return {"ok": bool(done), "released": surplus if done else 0, "what_happened": message,
                    "managers_needed": needed}
        shortfall = needed - have
        if shortfall <= 0:
            return {"ok": True, "hired": 0, "managers_needed": needed, "managers_this_mod_hired": have}
        before = access.view("staff")()["employees"].get(manager_trade, 0.0)
        # The market may allow fewer than asked; take the most it will give.
        count = shortfall
        while count > 1 and access.view("hire_check")(manager_trade, count)[2]:
            count -= 1
        done, message = access.send(HireStaff(manager_trade, count))
        if not done:
            return {"ok": False, "error": message, "managers_needed": needed}
        gained = int(round(access.view("staff")()["employees"].get(manager_trade, 0.0) - before))
        memory["managers_hired"] = have + gained
        return {"ok": True, "hired": gained, "asked": shortfall, "managers_needed": needed,
                "managers_this_mod_hired": memory["managers_hired"], "what_happened": message,
                "annual_wage_bill": round(access.view("wage_bill")(), 1)}
