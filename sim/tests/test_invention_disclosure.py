"""Complaints 103, 185, 287: an actor chooses what to do with an invention (keep it secret, publish it), and
how hard it is to copy and how long it takes to be believed follow from that choice. Complaint 640: the rules
are called on the diffusion module over views and plain nodes built here; licensing, saving and the command on a whole game are in
test_invention_disclosure_scenario."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.diffusion.api import Disclose, copy_difficulty_of
from sim.diffusion.module import Diffusion
from sim.diffusion.state import DiffusionSeat
from sim.polity.state import PolitySeat
from sim.tests import polity_host
from sim.engine.visibility import years_to_be_believed
from sim.polity.api import GainReputation
from sim.tests import module_harness

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
class _DisclosureGame:
    """The diffusion module of a seat that made `made`, was granted `granted` and chose nothing yet."""

    def __init__(self, made=("alpha",), granted=()):
        self.done = set(made) | set(granted)
        self.module = module_harness.build(Diffusion, seat=DiffusionSeat(), views={
            "tree": {"alpha": {}, "beta": {}, "gamma": {}}.get, "techniques_held": lambda: self.done,
            "techniques_granted": lambda: set(granted), "operating": lambda: set(), "year": 120,
            "reputation_gain_of": lambda node_id: 2.0})

    def disclose(self, node_id, mode):
        return self.module.disclose(Disclose(node_id, mode))

    def disclosure_of(self, node_id):
        return self.module.disclosure(node_id)

    def reputation_gained(self):
        return [command.amount for command in module_harness.sent(self.module) if isinstance(command, GainReputation)]


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

_published = _game.disclose("alpha", "publish")
check("publishing is accepted, raises the publisher's reputation and notes the year",
      _published["ok"] and _game.reputation_gained() == [2.0] and _game.disclosure_of("alpha")["published_year"] == 120,
      (_published, _game.reputation_gained()))
check("publishing cannot be taken back", not _game.disclose("alpha", "secret")["ok"] and _game.disclosure_of("alpha")["mode"] == "publish")
check("publishing again earns nothing more", not _game.disclose("alpha", "publish")["ok"] and _game.reputation_gained() == [2.0])
_standing = PolitySeat(reputation=9.5)
polity_host.build(seat=_standing, legacy_constant=lambda name: {"REPUTATION_CEILING": 10.0}[name]).gain_reputation(GainReputation(2.0))
check("reputation from publishing stops at the ceiling", _standing.reputation == 10.0, _standing.reputation)
check("the listing carries every invention of the founder's with its mode",
      [(row["id"], row["mode"]) for row in _game.module.disclosure_listing()] == [("alpha", "publish")], _game.module.disclosure_listing())
