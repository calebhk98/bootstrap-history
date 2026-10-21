"""Which of the ids a typed name matches the player may be offered."""


def candidates_the_player_may_see(candidates, is_visible, goal, operation, exact_ids):
    """`candidates` kept to what the player has heard of, so a name never offers a hidden id to choose between. The
    goal's own exact name keeps the one exception its id already has, on `why` alone: `exact_ids` are the ids whose
    name is exactly what was typed, so a vague guess at the goal stays refused."""
    return [node_id for node_id in candidates
            if is_visible(node_id) or (node_id == goal and operation == "why" and node_id in exact_ids)]
