"""The technologies a civilisation opens knowing: exactly what its record declares, refused when any is not in the tree."""


def declared_starting_techs(civ, nodes):
    """The civilisation's declared starting technologies. Refuses a corrupt opening rather than dropping an unknown one:
    silently dropping it would run a different scenario without telling anyone."""
    starting_techs = civ["starting_techs"]
    missing = sorted(tech_id for tech_id in starting_techs if tech_id not in nodes)
    if missing:
        raise ValueError("civilization %r lists unknown starting technologies: %s"
                         % (civ.get("id", "?"), ", ".join(missing)))
    return starting_techs


def grant_starting_techs(projects, starting_techs, done_changed):
    """Everything declared is done and granted (not earned), and `done_changed` is told after each is added."""
    for tech_id in starting_techs:
        projects.done.add(tech_id)
        done_changed()
        projects.granted.add(tech_id)
