"""The structured half of a refused `start`: which blocker kind and which check refused."""


def refusal_fields(sim, node_id):
    """{"blocked_kind", "blocked_cause"} for the first blocker; a start that passed the gate but still
    failed (a precaution the node does not offer) has cause no_precaution."""
    blockers = sim.view("start_blockers")(node_id)
    if blockers:
        return {"blocked_kind": blockers[0]["kind"], "blocked_cause": blockers[0]["cause"]}
    return {"blocked_kind": None, "blocked_cause": "no_precaution"}
