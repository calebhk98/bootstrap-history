"""Typed-line parsing for prospect: `prospect <tile> <material> <person_days>`."""
from . import typed


def parse_prospect(command, rest, words, nums, want_json):
    names = [str(word) for word in rest]
    if len(names) != 3:
        return None, "prospect takes a tile, a material and the person-days to spend: prospect <tile> coal 2000"
    try:
        person_days = float(names[2])
    except ValueError:
        return None, "prospect takes a tile, a material and the person-days to spend: prospect <tile> coal 2000"
    return {"cmd": "prospect", "tile": names[0], "material": names[1].lower(), "person_days": person_days}, None


typed._COMMAND_PARSERS.setdefault("prospect", parse_prospect)
