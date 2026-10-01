"""Complaint 97: a figure registers its components once, and `figures` / `why <figure>`
show last year, this year and the named causes, read from the engine's own functions."""
from .harness import *  # noqa: F401,F403

from sim.engine import figures as figure_registry
from sim.engine.proto import command_registry

HEADLINE = ("cash", "recurring_net", "income", "upkeep", "population",
            "literacy_general", "price_index", "hazard")


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


def played_sim():
    test_sim = sim(capital=1_000_000.0)
    started = next((node_id for node_id in test_sim.order
                    if NODES[node_id]["rev"] > 0 and test_sim.can_start(node_id)), None)
    if started:
        ask(test_sim, cmd="start", id=started)
    ask(test_sim, cmd="step", years=2)
    return test_sim


played = played_sim()
registered = set(figure_registry.FIGURES)
check("every headline figure is registered", set(HEADLINE) <= registered, sorted(registered))

listing = ask(played, cmd="figures")
check("figures with no name lists every registered figure",
      listing.get("ok") and {row["name"] for row in listing["figures"]} == registered, listing)

one = ask(played, cmd="figures", id="upkeep")
check("a figure reports last year, this year and the change",
      one.get("ok") and {"previous", "current", "change", "causes"} <= set(one), one)
check("this year's value is the engine's own function",
      abs(one["current"] - played.upkeep()) < 0.1, (one["current"], played.upkeep()))
check("the causes add up to the change",
      abs(sum(cause["contribution"] for cause in one["causes"]) - one["change"]) < 0.5, one)

income = ask(played, cmd="figures", id="income")
check("income is the engine's revenue", abs(income["current"] - played.revenue()) < 0.1, income)
check("every income cause names itself",
      all(cause.get("cause") for cause in income["causes"]), income)

cash = ask(played, cmd="figures", id="cash")
check("cash is the household's capital", abs(cash["current"] - played.capital) < 0.1, cash)
check("cash causes add up to the change, unexplained part named",
      abs(sum(cause["contribution"] for cause in cash["causes"]) - cash["change"]) < 0.5, cash)

fallback = ask(played, cmd="why", id="recurring_net")
check("why <figure> falls through to the figure inspector",
      fallback.get("ok") and fallback.get("name") == "recurring_net", fallback)

unknown = ask(played, cmd="figures", id="nonsense")
check("an unknown figure is refused with the list",
      not unknown.get("ok") and "upkeep" in str(unknown), unknown)

fresh = sim(capital=1_000_000.0)
before_any_year = ask(fresh, cmd="figures", id="upkeep")
check("before a year has passed there is no previous value and it says so",
      before_any_year.get("ok") and before_any_year["previous"] is None, before_any_year)


@figure_registry.figure("test_probe", label="probe", unit="units")
def _probe(test_sim):
    return {"value": 7.0, "components": {"alpha": 3.0, "beta": 4.0}}


try:
    probe = ask(played, cmd="figures", id="test_probe")
    check("a newly registered figure is explained with no list edited",
          probe.get("ok") and probe["current"] == 7.0
          and {cause["cause"] for cause in probe["causes"]} == {"alpha", "beta"}, probe)
finally:
    figure_registry.FIGURES.pop("test_probe", None)

check("figures is in the command registry", "figures" in command_registry.COMMANDS)
