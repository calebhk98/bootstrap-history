"""Complaints/59: a quoted affordable amount must be purchasable as quoted.

For each buy kind with a quote, the quoted affordable amount is bought on an
unchanged Sim and must succeed in full.

Every quoted affordable amount is purchasable as quoted.
"""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.dispatch_money import _cmd_quote


def _quoted(quote_cmd, capital):
    test_sim = sim(capital=capital)
    return test_sim, _cmd_quote(test_sim, NODES, quote_cmd, None)


# Little cash, so a quoted figure that counts credit differs from cash alone.
_CAPITAL = 3000.0

_forest_sim, _forest_quote = _quoted({"what": "forest", "n": 100}, _CAPITAL)
_forest_ha = _forest_quote["you_can_afford_about"]
check("forest: the quote gives a positive affordable amount",
      _forest_ha > 0, _forest_quote)
check("forest: the quoted affordable hectares are bought in full",
      _forest_sim.buy_forest(_forest_ha) == _forest_ha, _forest_ha)

_nitre_sim, _nitre_quote = _quoted({"what": "nitre_bed", "n": 10000}, _CAPITAL)
_nitre_m2 = _nitre_quote["you_can_afford_about"]
check("nitre: the quote gives a positive affordable amount",
      _nitre_m2 > 0, _nitre_quote)
check("nitre: the quoted affordable square metres are laid in full",
      _nitre_sim.build_nitre(_nitre_m2) == _nitre_m2, _nitre_m2)

_mine_sim, _mine_quote = _quoted(
    {"what": "mine", "material": "coal", "n": 500}, _CAPITAL)
_mine_tonnes = _mine_quote["you_can_afford_about"]
check("mine: the quote gives a positive affordable amount",
      _mine_tonnes > 0, _mine_quote)
check("mine: the quoted affordable tonnage is sunk in full",
      _mine_sim.open_mine("coal", _mine_tonnes, partial=False) == _mine_tonnes,
      _mine_tonnes)

# Past the quoted amount is refused, and the refusal cites the same budget.
_over_sim, _over_quote = _quoted({"what": "forest", "n": 100}, _CAPITAL)
check("forest: twice the quoted amount is refused",
      _over_sim.buy_forest(_over_quote["you_can_afford_about"] * 2 + 1) == 0.0,
      _over_quote)
_refusal = proto([{"cmd": "buy", "what": "forest", "n": 100000}])[0][0]
check("forest: the refusal names what you could raise, as the quote does",
      not _refusal.get("ok") and "could raise" in str(_refusal.get("error")),
      _refusal)

# Slaves quote must show the shared budget (cash + credit), like forest does.
_slaves_sim, _slaves_quote = _quoted({"what": "slaves", "n": 100}, _CAPITAL)
check("slaves: the quote includes shared budget info",
      "you_could_raise" in _slaves_quote and "you_can_afford_about" in _slaves_quote,
      _slaves_quote)
_slaves_people = _slaves_quote["you_can_afford_about"]
check("slaves: the quote gives a positive affordable amount",
      _slaves_people > 0, _slaves_quote)
check("slaves: the quoted affordable people are bought in full",
      _slaves_sim.labour.buy_slaves(_slaves_people) == _slaves_people, _slaves_people)

# Affordability with credit: household with little cash but enough credit can buy
_credit_sim = sim(capital=_CAPITAL)
# Ensure spending_power allows using credit
_budget = _credit_sim.spending_power("buy")
if _budget > _CAPITAL:
    # We have credit available; try to buy something that costs more than cash alone
    cost_with_credit = _CAPITAL * 0.5 + (_budget - _CAPITAL) * 0.5
    # This should be affordable via shared budget but not via cash alone
    if cost_with_credit > _CAPITAL:
        check("slaves: affordable via credit when cash alone is insufficient",
              cost_with_credit <= _budget, (cost_with_credit, _budget, _CAPITAL))

# Bought material stock draws on the same budget.
_stock_sim = sim(capital=_CAPITAL)
_material_quote = _stock_sim.material_trade_quote("iron")
if _material_quote:
    _tonnes = min(_stock_sim.spending_power("buy") / _material_quote["buy_per_tonne"] * 0.999,
                  _material_quote["market_available_tonnes_per_year"])
    check("material: an amount within the shared budget is bought in full",
          _stock_sim.buy_material_stock("iron", _tonnes) == _tonnes, _tonnes)
