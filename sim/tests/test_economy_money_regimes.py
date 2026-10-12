"""Each civilisation's money works as its own regime on the agent economy: England struck silver with a
mint charge, Norse weighed silver, Han and Rome struck coin, Mexica cacao beans. More metal mined
raises the money stock and the price level under struck and weighed money, and the mint holds the metal
of the money in circulation. Norse weighed silver is its own topic: it is a run of its own, and the suite
runs topics side by side."""
from .harness import *  # noqa: F401,F403
from .money_regimes_play import REGIME_OF, check_more_metal_raises_money, play


for civ_id, regime in sorted(REGIME_OF.items()):
    standard = S.load_civ(civ_id)["coin_standard"]
    check("%s's data names its money regime, %s" % (civ_id, regime), standard.get("regime") == regime, standard)
check("England's mint keeps a charge", S.load_civ("england_1300")["coin_standard"]["mint_charge_share"] > 0.0)
check("only a struck coin carries a mint charge in the data", all(
    "mint_charge_share" not in S.load_civ(civ_id)["coin_standard"] for civ_id, regime in REGIME_OF.items()
    if regime != "struck_coin"))
production = json.load(open(os.path.join(ROOT, "data", "production", "94_agri_organics_gaps.json")))["materials"]
check("Mexica's money is made of cacao, a good in the production catalogue",
      S.load_civ("mexica_1500")["coin_standard"]["material"] in production
      and "cacao_kg" in production["cacao_kg"]["outputs"])

check_more_metal_raises_money("england_1300")      # norse_900ad: test_economy_money_regimes_norse.py

money, _level, record, setup = play("mexica_1500", 1)
check("Mexica runs a year on cacao money with money and goods conserved",
      record.currency.regime == "commodity" and record.currency.backing_good == "cacao_kg"
      and money > 0.0 and record.book.check_conservation(1e-9).ok, record.book.check_conservation(1e-9).breaches[:3])
check("Mexica's cacao is produced and traded", any(volume > 0.0 for key, volume in record.volumes.items()
                                                  if key.startswith("cacao_kg|")))
