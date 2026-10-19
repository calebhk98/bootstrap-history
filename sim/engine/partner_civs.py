"""One loaded record per partner civilisation for the whole game (the file is read, the mods applied and the
record checked once, not on every read of one field). Callers read the record and never write to it."""
from .data import load_civ


class PartnerCivsMixin:

    def partner_civ(self, civilization_id):
        """The civilisation `civilization_id` as `load_civ` returns it, kept for the game. Read-only: a caller
        that changes a record takes its own copy with `load_civ`."""
        loaded = self.__dict__.setdefault("_partner_civs", {})
        record = loaded.get(civilization_id)
        if record is None:
            record = loaded[civilization_id] = load_civ(civilization_id)
        return record
