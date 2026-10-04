# Gold has one hand-sluicing route and no deposit-priced alternative

**Status:** partly - gold draws from its deposits (hydraulic Las Medulas route with aqueduct capital, lode route); the limited ornament supply (325) and a hand-placer deposit remain

`gold_kg` is hand ground-sluicing and amalgamation at a stated placer grade, about 13,000 labour hours per kg. The deposits (`data/world/deposits.json`) hold Las Medulas hydraulic gravel and Dacian vein gold, which `sim/world/deposits.py` prices at roughly 170 and 8,750 hours per kg, and the Roman empire's gold came mostly from the first (Pliny NH 33.66-78). Gold is not drawn from them, so the solved gold price is the hand route's, not a supply curve's. Add the hydraulic and lode routes as techniques (or draw gold from the deposits like galena) and check the gold-to-silver ratio (about 42 now, with silver itself too cheap; see 305, 333). Also open from 325: a limited ornament supply per year.

## Update (silver-gold-data-fixes)

`gold_kg` is now hydraulic ground-sluicing of Las Medulas gravel (`gold_gravel_kg`, aqueduct build hours as capital); `gold_lode_kg` is the lode route from Dacia (`gold_lode_ore_kg`, dressed at the shared rate). Both gold ores are in `RENT_BEARING_ORE_MATERIALS`, so the price is the marginal gold deposit's. The fixed 0.3 g per cubic metre placer route is gone. Gold to silver ratio is a check only: `python3 sim/engine/solve_prices.py --civ rome_100ad --why gold_kg` and `--why silver_kg`. Open: the ornament supply limit (325), riffle and lode recoveries (conf D), and any hand-placer deposit.
