"""Whether a pool a concern draws on can still run out, given who is in it."""

NEED_FLOOR = 0.005


def closure_at_risk(need, room, hired_held, founder_fixed):
    """A concern drawing `need` of a pool is on notice when the pool's `room` (the people in it, the founder and the
    closing slack, less what running concerns use) could shrink under it. Only hired people leave: with a founder who
    cannot leave, the room left after losing every hired one is guaranteed, so no closure comes from attrition."""
    return need > NEED_FLOOR and not (founder_fixed and room - hired_held >= 0)
