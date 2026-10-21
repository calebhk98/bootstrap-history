"""Complaints 103, 185, 287: an actor chooses what to do with an invention (keep it secret, publish it), and
how hard it is to copy and how long it takes to be believed follow from that choice. Complaint 640: the rules
are called on a stub game and plain nodes built here; licensing, saving and the command on a whole game are in
test_invention_disclosure_scenario."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403

from sim.engine.society_disclosure import DisclosureMixin
from sim.engine.visibility import copy_difficulty_of, years_to_be_believed

# --- how hard an invention is to copy from sight.
check("a declared copy visibility gives its reciprocal as difficulty", copy_difficulty_of({"copy_visibility": 0.25}) == 4.0)
check("without one, difficulty is the number of trades and materials the know-how needs",
      copy_difficulty_of({"lab": {"smith": 5.0, "mason": 3.0, "idle": 0.0}, "mat": {"iron": 2.0, "wood": 0}}) == 3)
check("a node that needs nothing is still at least as hard as one", copy_difficulty_of({"lab": {}, "mat": {}}) == 1)
check("more trades make it harder to copy",
      copy_difficulty_of({"lab": {"a": 1.0, "b": 1.0, "c": 1.0}}) > copy_difficulty_of({"lab": {"a": 1.0}}))

# --- how long a running concern takes to be believed.
check("a published invention is believed at once", years_to_be_believed("publish", 5.0, 0.1) == 0.0)
check("an invention on the default needs the proof years", years_to_be_believed("default", 5.0, 0.1) == 5.0)
check("a secret takes the proof years over the share that leaks, so it takes longer",
      years_to_be_believed("secret", 5.0, 0.25) == 20.0)
check("a licensed one is kept as shut as a secret", years_to_be_believed("license", 5.0, 0.25) == 20.0)
check("the harder to copy, the longer a secret is in being believed",
      years_to_be_believed("secret", 5.0, 0.1) > years_to_be_believed("secret", 5.0, 0.25))


# --- choosing what to do with an invention.
class _DisclosureGame(DisclosureMixin):
    REPUTATION_CEILING = 10.0

    def __init__(self, made=("alpha",), granted=(), reputation=1.0):
        self.nodes = {"alpha": {}, "beta": {}, "gamma": {}}
        self.state = types.SimpleNamespace(
            projects=types.SimpleNamespace(done=set(made) | set(granted), granted=set(granted), disclosures={}, operating=set()),
            scenario=types.SimpleNamespace(year=120), household=types.SimpleNamespace(reputation=reputation))

    def reputation_gain_of(self, node):
        return 2.0


_game = _DisclosureGame()
check("an invention with no choice made is on the default", _game.disclosure_of("alpha")["mode"] == "default")
check("choosing secret is accepted for an invention the founder made", _game.disclose("alpha", "secret")["ok"])
check("...and is recorded", _game.disclosure_of("alpha")["mode"] == "secret")
check("choosing for something the founder has not made is refused", not _game.disclose("beta", "secret")["ok"])
check("choosing for something that is not a node is refused", not _game.disclose("not_a_node", "secret")["ok"])
check("choosing for a granted technology (not made by the founder) is refused",
      not _DisclosureGame(granted=("gamma",)).disclose("gamma", "publish")["ok"])
check("a mode that is not a choice is refused", not _game.disclose("alpha", "gift")["ok"])
check("'default' is not a choice to make", not _game.disclose("alpha", "default")["ok"])

_reputation_before = _game.state.household.reputation
_published = _game.disclose("alpha", "publish")
check("publishing is accepted, raises the publisher's reputation and notes the year",
      _published["ok"] and _game.state.household.reputation == _reputation_before + 2.0
      and _game.disclosure_of("alpha")["published_year"] == 120, (_published, _game.state.household.reputation))
check("publishing cannot be taken back", not _game.disclose("alpha", "secret")["ok"] and _game.disclosure_of("alpha")["mode"] == "publish")
check("publishing again earns nothing more", not _game.disclose("alpha", "publish")["ok"]
      and _game.state.household.reputation == _reputation_before + 2.0)
_near_ceiling = _DisclosureGame(reputation=9.5)
_near_ceiling.disclose("alpha", "publish")
check("reputation from publishing stops at the ceiling", _near_ceiling.state.household.reputation == 10.0, _near_ceiling.state.household.reputation)
check("the listing carries every invention of the founder's with its mode",
      [(row["id"], row["mode"]) for row in _game.disclosure_listing()] == [("alpha", "publish")], _game.disclosure_listing())
