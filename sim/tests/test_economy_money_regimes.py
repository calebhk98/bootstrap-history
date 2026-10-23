"""SCENARIO: each civilisation's money works as its own regime on the agent economy: England struck silver with a mint
charge, Han and Rome struck coin, Mexica cacao beans. More metal mined raises the money stock under struck money, and the
mint holds the metal of the money in circulation. The regimes named in the data are test_money_regime_data_rule; that
money reaches prices is test_money_reaches_prices. Norse weighed silver is its own topic: it is a run of its own, and
the suite runs topics side by side."""
from .harness import *  # noqa: F401,F403
from .money_regimes_play import check_more_metal_raises_money, check_more_metal_raises_price_level, play


check_more_metal_raises_money("england_1300")      # norse_900ad: test_economy_money_regimes_norse.py

money, _level, record, setup = play("mexica_1500", 1)
check("Mexica runs a year on cacao money with money and goods conserved",
      record.currency.regime == "commodity" and record.currency.backing_good == "cacao_kg"
      and money > 0.0 and record.book.check_conservation(1e-9).ok, record.book.check_conservation(1e-9).breaches[:3])
check("Mexica's cacao is produced and traded", any(volume > 0.0 for key, volume in record.volumes.items()
                                                  if key.startswith("cacao_kg|")))

check_more_metal_raises_price_level("england_1300")     # whole-economy validation, red while the opening is unsettled (473)
