# Rio Tinto's jarosite silver route is missing

**Status:** partly - a Rio Tinto jarosite deposit and a lead-flux smelting recipe exist, both conf D; the grade, the lead flux quantity and the collector recovery need the paper

Rio Tinto's Roman silver came largely from jarosite and gossan ores, smelted with added lead as a collector (Anguilano et al. 2010, ArcheoSciences 34, read by the research agent). The model carries Rio Tinto only as a deep hard copper deposit, so this route, a large part of Iberian silver, does not exist. What it would take: a jarosite deposit and a recipe that consumes lead flux, with a sourced grade (the 0.2% silver figure seen so far is from an abstract, not the paper). Source review: `Complaints/reports/silver-mining-and-minting-review.md`. Related: 291, 349.

## Update (silver-gold-data-fixes)

Added the deposit `rio_tinto_jarosite` (ore type jarosite, grade 2 kg per tonne, conf D from an abstract) and the recipes `jarosite_ore_kg` and `silver_jarosite_kg`, which consumes `lead_kg` as the collector flux (Anguilano et al. 2010). Open: the paper's own grade, the added lead quantity, collector recovery and the deposit's share of Iberian silver (a placeholder carved from `hispania_silver`); no rent is charged on jarosite ore; hearth wear is not charged.
