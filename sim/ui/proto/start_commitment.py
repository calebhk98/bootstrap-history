"""The aggregate warning a `start` reply carries when work in hand together owes more than the cash held."""


def stacked_commitment(committed, cash, projects_in_hand, capacity_of):
    """The total promised, the cash held, the draw on credit between the projects and the real ceiling, once more
    than one project is in hand and what they still owe together exceeds the cash held; None when there is nothing
    to warn of. `capacity_of` is asked for the ceiling only when there is a warning."""
    cash = max(0.0, cash)
    if committed <= cash or projects_in_hand <= 1:
        return None
    return {"you_have_promised": round(committed, 1), "across_projects_in_hand": projects_in_hand,
            "you_currently_hold": round(cash, 1), "likely_to_draw_on_credit_between_them": round(committed - cash, 1),
            "your_real_ceiling_if_it_comes_to_that": round(capacity_of(), 1)}
