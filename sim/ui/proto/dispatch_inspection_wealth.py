"""The mines, capacity, portfolio, economy, changes and population commands."""

from .command_registry import command
from .economy import (_agent_capacity, _agent_changes, _agent_economy,
                      _agent_mines, _agent_portfolio)


@command("mines", shape="bare", group="overview", aliases=("workings", "mine", "pits"),
         summary="your own workings",
         usage=["mines"], options={},
         description="Each mine you own: output, upkeep and what limits it. Buy with "
                     "buy mine, shut with close.")
def _cmd_mines(sim, nodes, cmd, ended):
    # See _agent_mines above: the one place this arithmetic is written,
    # shared with `capacity`, so the two screens cannot drift apart.
    return _agent_mines(sim)



@command("capacity", shape="bare", group="overview",
         aliases=("overview", "industry", "dashboard", "infrastructure", "power"),
         summary="why active projects move at their present pace",
         usage=["capacity"], options={},
         description="Annual material throughput and shortages, trade-hour demand and "
                     "supply, power, staffing and finance. Throughput is this year's "
                     "flow; durable unused material is shown separately by materials "
                     "as stock on hand.")
def _cmd_capacity(sim, nodes, cmd, ended):
    return _agent_capacity(sim, nodes, cmd)



@command("portfolio", group="overview",
         summary="every active project and what limits it",
         usage=["portfolio", "portfolio <blocker kind or trade>", "portfolio all", "portfolio offset:K", "portfolio json"],
         options={"json": "the raw reply", "<group>": "only the projects behind one blocker kind or trade",
                  "all": "every project row", "offset:K / limit:N": "page position and size"},
         description="The founder hours each project actually gets this year and why, "
                     "the reason it is not moving faster, and each hired trade's "
                     "demand against supply.")
def _cmd_portfolio(sim, nodes, cmd, ended):
    return _agent_portfolio(sim, nodes, cmd)



@command("economy", group="money", aliases=("prices", "econ"),
         summary="what things cost and what you can trade",
         usage=["economy", "economy full"], options={"full": "every row"},
         description="Current values of goods and inputs as this economy prices them.")
def _cmd_economy(sim, nodes, cmd, ended):
    return _agent_economy(sim, cmd)



@command("changes", group="overview", aliases=("diff", "recap", "summary"),
         summary="what changed lately",
         usage=["changes", "changes <years>"],
         options={"<years>": "how far back to compare (default 5)"},
         description="A recap of the last few years: what completed, what moved in "
                     "money, people and the society.")
def _cmd_changes(sim, nodes, cmd, ended):
    return _agent_changes(sim, nodes, cmd)



@command("population", group="society",
         aliases=("demographics", "census", "pop"),
         summary="the country's numbers and your reach",
         usage=["population"], options={},
         description="The country, the one town your household reaches, and per trade "
                     "how many exist, how many are within reach and how many you "
                     "employ. Country-wide and reach figures are estimates.")
def _cmd_population(sim, nodes, cmd, ended):
    return {"ok": True, **sim.labour.population_report()}
