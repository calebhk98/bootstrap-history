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

