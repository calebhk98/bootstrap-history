"""The `market` command: what the game already knows about prices, goods
saturation and wages, on one screen."""

from ..market_report import DEFAULT_MATERIAL_PAGE, market_report
from .command_registry import command


def _whole_number(cmd, key, default):
    try:
        return int(cmd.get(key, default))
    except (TypeError, ValueError):
        return default


@command("market", group="money",
         summary="goods saturation, material prices and wages in one screen",
         usage=["market", "market offset 40 limit 40", "market json"],
         options={"offset / limit": "page through the materials table",
                  "json": "the raw reply"},
         description="Per goods category your concerns sell into, the share of the quoted "
                     "figure being earned and which concerns compete; the buy price of every "
                     "material the game can price and whether you supply it yourself; and a "
                     "year's wage for every trade. Same numbers as 'ventures', 'quote "
                     "material' and 'labour <trade>'.")
def _cmd_market(sim, nodes, cmd, ended):
    return market_report(sim, offset=_whole_number(cmd, "offset", 0),
                         limit=_whole_number(cmd, "limit", DEFAULT_MATERIAL_PAGE))
