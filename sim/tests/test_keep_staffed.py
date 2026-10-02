"""keep_staffed: complaint 126 (name the concerns that must stay staffed through attrition)."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.typed import parse_typed

CONCERN = "mirror_amalgam"   # needs a glassblower foreman


def _lost_foreman_sim():
    """A household running CONCERN whose only glassblower has just died."""
    test_sim = sim(capital=5_000_000)
    test_sim.trades_created.add("glassblower")
    test_sim.done.add(CONCERN)
    test_sim.operating.add(CONCERN)
    test_sim._done_changed()
    test_sim.employees.pop("glassblower", None)
    test_sim._resync_pools()
    return test_sim


def _dispatch(test_sim, line):
    cmd, refusal = parse_typed(line)
    check("typed %r parses" % line, cmd is not None, refusal)
    return S._agent_dispatch(test_sim, NODES, cmd) if cmd else {}


# Baseline: without the flag the closure rule shuts the unsupervised concern.
control = _lost_foreman_sim()
control.step()
check("unflagged concern closes when its foreman is gone",
      CONCERN not in control.operating, control.employees)

# The command sets and clears the flag and is listed.
flagged = _lost_foreman_sim()
reply = _dispatch(flagged, "keep %s staffed" % CONCERN)
check("keep <id> staffed is accepted", reply.get("ok") is True, reply)
check("...and the flag is recorded on the projects state",
      CONCERN in getattr(flagged.state.projects, "keep_staffed", set()), reply)
listing = _dispatch(flagged, "ventures")
check("ventures shows the flagged concern",
      CONCERN in (listing.get("keep_staffed") or []), listing.get("keep_staffed"))
bare = _dispatch(flagged, "keep")
check("bare keep lists what is flagged", CONCERN in (bare.get("keep_staffed") or []), bare)
refused = _dispatch(flagged, "keep no_such_concern staffed")
check("an unknown id is refused", refused.get("ok") is False, refused)

# The yearly step hires what the flagged concern needs before the closure rule.
flagged.step()
check("flagged concern stays open through the loss of its foreman",
      CONCERN in flagged.operating, dict(flagged.employees))
check("...because a glassblower was hired",
      flagged.employees.get("glassblower", 0.0) >= 0.5, dict(flagged.employees))
check("...and the log says why",
      any("keep_staffed" in message for _year, message in flagged.log), flagged.log[-6:])

# Off clears it, and the flag survives a save/load round trip.
flagged2 = _lost_foreman_sim()
_dispatch(flagged2, "keep %s staffed" % CONCERN)
from sim.engine.saveload import save_state, load_state
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "keep.json")
    save_state(flagged2, path)
    restored = sim(capital=1.0)
    load_state(restored, path)
check("the flag is part of the saved state", CONCERN in getattr(restored.state.projects, "keep_staffed", set()))
off = _dispatch(flagged2, "keep %s off" % CONCERN)
check("keep <id> off clears the flag",
      off.get("ok") is True and CONCERN not in getattr(flagged2.state.projects, "keep_staffed", set()), off)
flagged2.step()
check("once off, the concern closes again", CONCERN not in flagged2.operating)

# Within cash: a flagged concern is not hired for when the household is broke.
poor = _lost_foreman_sim()
poor.state.household.capital = -poor.credit_limit()  # in arrears to the limit: nothing left to spend
_dispatch(poor, "keep %s staffed" % CONCERN)
poor.step()
check("no cash, no hire: the rule does not conjure people",
      poor.employees.get("glassblower", 0.0) < 0.5, dict(poor.employees))
