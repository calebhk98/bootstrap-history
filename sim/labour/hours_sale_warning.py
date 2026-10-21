"""The warning a sale of the founder's own hours carries when it would starve a project in hand."""


def starved_projects(wanted, hours_left):
    """[(project id, hours it still wants)] for the projects that want more of the founder's hours this year than are left
    after a sale, the hungriest first. `wanted` is {project id: hours still wanted}."""
    short = {project_id: hours for project_id, hours in wanted.items() if hours > hours_left + 0.5}
    return sorted(short.items(), key=lambda item: -item[1])


def starving_warning(wanted, hours_left):
    """A sentence naming the (up to two) projects a sale leaves short of the founder's hours, or None when none is short."""
    short = starved_projects(wanted, hours_left)
    if not short:
        return None
    named = short[:2]
    more = len(short) - len(named)
    bits = ["%s (wants about %.0f more of your hours this year)" % (project_id, hours) for project_id, hours in named]
    return ("this leaves only %.0f of your own hours for the rest of the year, and %s: %s%s. Nothing is lost - what it does "
            "not get this year it gets next - but if that is not what you meant, work fewer hours. Selling them anyway is a "
            "fair move if it is cash you need right now."
            % (hours_left, "it still wants more than that" if len(short) == 1 else "these still want more than that",
               "; ".join(bits), (", and %d more" % more) if more else ""))
