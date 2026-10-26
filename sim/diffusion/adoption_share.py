"""What share of a set of the founder's techniques some actor holds."""


def held_share(technique_ids, held):
    """The fraction of `technique_ids` found in `held`; nothing when there are no techniques to hold."""
    technique_ids = list(technique_ids)
    return sum(1 for node_id in technique_ids if node_id in held) / len(technique_ids) if technique_ids else 0.0
