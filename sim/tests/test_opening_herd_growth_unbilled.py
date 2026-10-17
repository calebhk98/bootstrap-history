"""The opening herds are kept by the herd producers (their recipes pay the labour), so the founder is not billed
for their growth; only head beyond the producers' is the founder's to raise (Complaints/558)."""
from .harness import *  # noqa: F401,F403

HERDS = ("cattle_kg", "goat_kg", "sheep_kg")
game = sim(civ="han_china_100ad", capital=1e6)
billed = []
real_pay = game.pay_growth_labour
game.pay_growth_labour = lambda material, units: billed.append((material, units)) or real_pay(material, units)

game.step_living_stock()
check("raising the society's own opening herds is billed to nobody",
      not [row for row in billed if row[0] in HERDS and row[1] > 0.0], billed)

del billed[:]
game.grant_stock("sheep_kg", 1000.0)
game.step_living_stock()
check("head the founder adds beyond the producers' is raised at the founder's expense",
      any(material == "sheep_kg" and units > 0.0 for material, units in billed), billed)
