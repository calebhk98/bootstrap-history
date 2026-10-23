"""The greedy loop of `rush`: begin candidates in the order given until a limit, a cap or the founder's hours say stop."""
from sim.engine.ui_port import plain_number



def begin_in_order(candidates, nodes, limit, hours_budget, director_pool, cost_left_of, cap_refusal, begin):
    """Walk `candidates` and begin each that fits. Returns (started rows, not-started rows, hours owed, total cost, total draw).

    `cost_left_of(node_id)` is the money still owed to begin it; `cap_refusal(cost, draw, cost_so_far, draw_so_far, hours,
    hours_so_far)` is the reason it breaks a cap or None; `begin(node_id, annual_draw)` is (True, started row) or (False, why).
    The founder's hours owed by what has started may not pass `hours_budget` once something has started."""
    started, not_started = [], []
    hours_owed = total_cost = total_draw = 0.0
    for node_id in candidates:
        if limit is not None and len(started) >= limit:
            break
        cost_left = cost_left_of(node_id)
        annual_draw = cost_left / max(1.0, nodes[node_id]["yrs"])
        cap_reason = cap_refusal(cost_left, annual_draw, total_cost, total_draw, nodes[node_id]["ph"], hours_owed)
        if cap_reason:
            not_started.append({"id": node_id, "name": nodes[node_id]["name"], "why": cap_reason})
            continue
        if started and hours_owed + nodes[node_id]["ph"] > hours_budget:
            not_started.append({
                "id": node_id, "name": nodes[node_id]["name"],
                "why": "not begun: the %d things already started this turn owe %s of your hours, and you have about %s a year. "
                       "Beginning more would not make them go faster, only leave them all standing still"
                       % (len(started), plain_number(hours_owed), plain_number(director_pool))})
            continue
        began, outcome = begin(node_id, annual_draw)
        if began:
            hours_owed += nodes[node_id]["ph"]
            total_cost += cost_left
            total_draw += annual_draw
            started.append(outcome)
        else:
            not_started.append({"id": node_id, "why": outcome})
    return started, not_started, hours_owed, total_cost, total_draw
