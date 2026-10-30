"""The goods categories' price curves and the numbers behind the income effect.

Each goods category (textiles, processing, printing, ...) has a constant-elasticity demand curve with a floor and a time
constant for how fast new supply is absorbed; one seller's revenue is the category's price times volume over the number of
sellers (rules.py). Every figure is a declared heuristic until a household budget model derives it."""
from sim.constants import declare

# ---- goods-producing concerns: a market, not a fixed number --------------
# Bounded, elastic price curves (eta, floor, tau) per category: textiles,
# processing, printing, photography, plus fermentation, leisure, sound,
# media, commerce, entertainment, personal. Cross-elasticity via category
# totals. Income effect via essential_price_ratio() (food frees up spending).

GOODS_ETA_TEXTILES = declare(
    "GOODS_ETA_TEXTILES", 0.65, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source="Apparel-demand studies typically put clothing's own-price elasticity in the 0.6-1.0 range, moderately elastic, neither staple nor luxury; picked at the inelastic end so the early revenue erosion the brief asks for is actually visible.",
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_TEXTILES = declare(
    "GOODS_FLOOR_TEXTILES", 0.4, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source="Cloth's own floor in commodities.json (0.35), nudged to 0.40 after measuring this against 700-year Monte Carlo runs (see the class comment above for which civilisation's outcome that nudge protected).",
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_TEXTILES = declare(
    "GOODS_TAU_TEXTILES", 35.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source="Britain's handloom weavers went from the dominant technology to a shrinking minority over roughly thirty to forty years, the 1810s to the 1850s; taken at the slower end of that range after the same Monte Carlo calibration.",
    confidence='C',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_PROCESSING = declare(
    "GOODS_ETA_PROCESSING", 0.35, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='USDA Economic Research Service estimates put most packaged-food demand elasticities around 0.2-0.6; people keep eating whether or not processed food gets cheaper.',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_PROCESSING = declare(
    "GOODS_FLOOR_PROCESSING", 0.55, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source='Preserved food has a harder real cost floor than cloth (a tin and the heat to seal it cost what they cost); started at 0.45, nudged to 0.55 after the same Monte Carlo calibration as textiles.',
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_PROCESSING = declare(
    "GOODS_TAU_PROCESSING", 40.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source="No diffusion-speed citation exists for food-processing technology specifically; a longer, explicitly illustrative period than textiles' cited figure stands in for one.",
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_PRINTING = declare(
    "GOODS_ETA_PRINTING", 0.8, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='Discretionary but not a luxury in the pre-mass-media world these nodes describe; picked close to, but under, unit elastic.',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_PRINTING = declare(
    "GOODS_FLOOR_PRINTING", 0.4, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source='Same cloth-anchored floor family as textiles (0.35 nudged to 0.40); printed matter has no independently cited floor of its own.',
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_PRINTING = declare(
    "GOODS_TAU_PRINTING", 40.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source='No diffusion-speed citation for print technology specifically; the same illustrative 40-year figure as processing stands in for one.',
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_PHOTOGRAPHY = declare(
    "GOODS_ETA_PHOTOGRAPHY", 1.6, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='Camera and film equipment is squarely a luxury good throughout the period this applies to; luxury-goods demand studies commonly cite elasticities above 1.5.',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_PHOTOGRAPHY = declare(
    "GOODS_FLOOR_PHOTOGRAPHY", 0.55, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source="Coffee's own floor in commodities.json (0.5), the other luxury good that file prices, nudged to 0.55 after the same calibration pass.",
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_PHOTOGRAPHY = declare(
    "GOODS_TAU_PHOTOGRAPHY", 40.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source='No diffusion-speed citation for camera technology specifically; the same illustrative 40-year figure as processing stands in for one.',
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_FERMENTATION = declare(
    "GOODS_ETA_FERMENTATION", 0.55, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='Alcohol demand studies commonly cite elasticities of roughly 0.3-0.9 - a consumption habit, not a nutritional necessity, but not as freely substitutable as a camera either.',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_FERMENTATION = declare(
    "GOODS_FLOOR_FERMENTATION", 0.45, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source="Follows processing's 'real cost floor' reasoning as the closest existing anchor, without its own independent citation.",
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_FERMENTATION = declare(
    "GOODS_TAU_FERMENTATION", 35.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source="Follows textiles' cited diffusion pace as the closest existing anchor, without its own independent citation.",
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_LEISURE = declare(
    "GOODS_ETA_LEISURE", 1.1, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source="Hobby and entertainment goods are usually cited above unit elasticity but below photography's fine-goods range.",
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_LEISURE = declare(
    "GOODS_FLOOR_LEISURE", 0.45, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source="Follows processing's cost-floor reasoning as the closest existing anchor, without its own independent citation.",
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_LEISURE = declare(
    "GOODS_TAU_LEISURE", 35.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source="Follows textiles' cited diffusion pace as the closest existing anchor, without its own independent citation.",
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_SOUND = declare(
    "GOODS_ETA_SOUND", 1.3, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='A luxury technology good, the same reasoning as photography but slightly less extreme - audio reached a mass market somewhat faster, historically, than the camera did.',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_SOUND = declare(
    "GOODS_FLOOR_SOUND", 0.5, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source="Between photography's and the entertainment bucket's floors, without its own independent citation.",
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_SOUND = declare(
    "GOODS_TAU_SOUND", 35.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source="Follows textiles' cited diffusion pace as the closest existing anchor, without its own independent citation.",
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_MEDIA = declare(
    "GOODS_ETA_MEDIA", 0.85, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source="An information good, close to printing's own 0.80 elasticity, without its own independent citation.",
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_MEDIA = declare(
    "GOODS_FLOOR_MEDIA", 0.4, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source='Same cloth-anchored floor family as textiles and printing, without its own independent citation.',
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_MEDIA = declare(
    "GOODS_TAU_MEDIA", 35.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source="Follows textiles' cited diffusion pace as the closest existing anchor, without its own independent citation.",
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_COMMERCE = declare(
    "GOODS_ETA_COMMERCE", 1.0, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='Unit-elastic hospitality and retail demand is commonly cited in the 0.8-1.3 range.',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_COMMERCE = declare(
    "GOODS_FLOOR_COMMERCE", 0.45, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source="Follows processing's cost-floor reasoning as the closest existing anchor, without its own independent citation.",
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_COMMERCE = declare(
    "GOODS_TAU_COMMERCE", 30.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source="Shorter than the other categories' tau because a service business's custom is understood to shift faster than a manufacturing good's - a reasoned but not separately cited adjustment.",
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_LUXURY = declare(
    "GOODS_ETA_LUXURY", 1.8, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='The single most discretionary bucket this file prices, above photography, matching how elastic gambling and spectator-entertainment demand is usually cited to be (this category covers gambling, lotteries, theatre, professional sport and racecourses).',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_LUXURY = declare(
    "GOODS_FLOOR_LUXURY", 0.5, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source="Between photography's and the entertainment bucket's floors, without its own independent citation.",
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_LUXURY = declare(
    "GOODS_TAU_LUXURY", 35.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source="Follows textiles' cited diffusion pace as the closest existing anchor, without its own independent citation.",
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_SPECTACLE = declare(
    "GOODS_ETA_SPECTACLE", 1.8, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='Same entertainment-bucket reasoning as `luxury` above - this file splits the same real-world bucket (gambling, theatre, sport) across three `cat` values the tree happens to use.',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_SPECTACLE = declare(
    "GOODS_FLOOR_SPECTACLE", 0.5, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source='Same as `luxury` above.',
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_SPECTACLE = declare(
    "GOODS_TAU_SPECTACLE", 35.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source='Same as `luxury` above.',
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_LAW = declare(
    "GOODS_ETA_LAW", 1.8, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='Same entertainment-bucket reasoning as `luxury` above.',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_LAW = declare(
    "GOODS_FLOOR_LAW", 0.5, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source='Same as `luxury` above.',
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_LAW = declare(
    "GOODS_TAU_LAW", 35.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source='Same as `luxury` above.',
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")
GOODS_ETA_PERSONAL = declare(
    "GOODS_ETA_PERSONAL", 1.1, kind="temporary_heuristic",
    unit="price elasticity of demand (dimensionless)",
    source='Ordinary personal-luxury demand (perfume, cosmetics, toiletries), the same order as `leisure`.',
    confidence="C",
    why="How much buying of this category's goods responds to price - the price elasticity of demand in a constant-elasticity curve. A real figure needs actual buyers in THIS simulated economy, with budgets and substitutes, competing for this good - a real DEMAND side, which ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2 does not yet cover (it solves the cost/production side of pricing; nothing in this project yet models a buyer's budget or preferences) - rather than a point value borrowed from an unrelated real-world market and a real-world period.")
GOODS_FLOOR_PERSONAL = declare(
    "GOODS_FLOOR_PERSONAL", 0.45, kind="temporary_heuristic",
    unit="fraction of day-one price (dimensionless)",
    source="Follows processing's cost-floor reasoning as the closest existing anchor, without its own independent citation.",
    confidence="D",
    why="The price this market's good never falls below, however saturated - the floor of a constant-elasticity demand curve. Real cost floors exist (a good cannot sell below its own production cost forever) but this file has no production-cost model behind any of these categories, so the number is asserted rather than computed from one, and nudged, on top of that, to keep an existing game outcome from flipping (see the class comment above).")
GOODS_TAU_PERSONAL = declare(
    "GOODS_TAU_PERSONAL", 35.0, kind="temporary_heuristic",
    unit="years to visibly re-equilibrate",
    source="Follows textiles' cited diffusion pace as the closest existing anchor, without its own independent citation.",
    confidence='D',
    why="Years for this category's market to visibly respond to a new supply - how fast a shared category saturates. Diffusion speed is a real, measurable social phenomenon (see the textiles citation) but most categories here have no citation of their own and reuse textiles' or processing's number by analogy, which is a placeholder for a real technology-diffusion model, not a finding about this specific good.")

GOODS_CATEGORIES = {
    "textiles": {"eta": GOODS_ETA_TEXTILES, "floor": GOODS_FLOOR_TEXTILES, "tau": GOODS_TAU_TEXTILES},
    "processing": {"eta": GOODS_ETA_PROCESSING, "floor": GOODS_FLOOR_PROCESSING, "tau": GOODS_TAU_PROCESSING, "essential": True},
    "printing": {"eta": GOODS_ETA_PRINTING, "floor": GOODS_FLOOR_PRINTING, "tau": GOODS_TAU_PRINTING},
    "photography": {"eta": GOODS_ETA_PHOTOGRAPHY, "floor": GOODS_FLOOR_PHOTOGRAPHY, "tau": GOODS_TAU_PHOTOGRAPHY},
    "fermentation": {"eta": GOODS_ETA_FERMENTATION, "floor": GOODS_FLOOR_FERMENTATION, "tau": GOODS_TAU_FERMENTATION},
    "leisure": {"eta": GOODS_ETA_LEISURE, "floor": GOODS_FLOOR_LEISURE, "tau": GOODS_TAU_LEISURE},
    "sound": {"eta": GOODS_ETA_SOUND, "floor": GOODS_FLOOR_SOUND, "tau": GOODS_TAU_SOUND},
    "media": {"eta": GOODS_ETA_MEDIA, "floor": GOODS_FLOOR_MEDIA, "tau": GOODS_TAU_MEDIA},
    "commerce": {"eta": GOODS_ETA_COMMERCE, "floor": GOODS_FLOOR_COMMERCE, "tau": GOODS_TAU_COMMERCE},
    "luxury": {"eta": GOODS_ETA_LUXURY, "floor": GOODS_FLOOR_LUXURY, "tau": GOODS_TAU_LUXURY},
    "spectacle": {"eta": GOODS_ETA_SPECTACLE, "floor": GOODS_FLOOR_SPECTACLE, "tau": GOODS_TAU_SPECTACLE},
    "law": {"eta": GOODS_ETA_LAW, "floor": GOODS_FLOOR_LAW, "tau": GOODS_TAU_LAW},
    "personal": {"eta": GOODS_ETA_PERSONAL, "floor": GOODS_FLOOR_PERSONAL, "tau": GOODS_TAU_PERSONAL},
}
# Essential categories for income_factor(); kept centralized.
ESSENTIAL_CATEGORIES = frozenset(
    cat for cat, cfg in GOODS_CATEGORIES.items() if cfg.get("essential"))

REACH_CEILING = declare(
    "REACH_CEILING", 3.0, kind="temporary_heuristic",
    unit="multiple on market reach (maximum)", source=None,
    confidence="D",
    why="Cap on how far compounding every reach flag together can "
        "extend a market, so five flags at once do not multiply into an "
        "implausible number - the same defensive-cap pattern MARKET_SHARE "
        "and material_price_factor use elsewhere in this file. The cap's "
        "own value is picked for plausibility, not derived.")

GOODS_TAU_POP_SCALE_EXPONENT = declare(
    "GOODS_TAU_POP_SCALE_EXPONENT", 0.5, kind="temporary_heuristic",
    unit="dimensionless exponent on pop_scale", source=None,
    confidence="D",
    why="How much faster a goods market re-equilibrates in a larger "
        "civilisation - a bigger market plausibly absorbs and adapts "
        "to new supply faster, but this specific sub-linear exponent "
        "is tuned rather than fitted to any market-size-versus-"
        "diffusion-speed data.")

HOUSEHOLD_FARM_PRICE_RATIO_FLOOR = declare(
    "HOUSEHOLD_FARM_PRICE_RATIO_FLOOR", 0.55, kind="temporary_heuristic",
    unit="fraction of day-one staple price (dimensionless)", source=None,
    confidence="D",
    why="Floor on how cheap household-grown staples can make food, "
        "deliberately matched to the processing category's own "
        "GOODS_FLOOR_PROCESSING so a household's own farm and the "
        "established food market saturate toward the same floor rather "
        "than making subsistence free. Same honest limit as that "
        "floor's own declaration: asserted, not computed from a "
        "production-cost model.")
HOUSEHOLD_FARM_HECTARES_HALF_EFFECT = declare(
    "HOUSEHOLD_FARM_HECTARES_HALF_EFFECT", 120.0, kind="temporary_heuristic",
    unit="hectares of household farmland for half the price effect",
    source=None, confidence="D",
    why="How many hectares of household-owned farmland it takes to "
        "roughly halve the household's own staple price, on a "
        "diminishing-returns curve. Tuned game balance, not derived "
        "from an actual yield-per-hectare model - contrast with "
        "sim/world/agriculture.py, which derives an equivalent number "
        "from seed rate, fold return and labour instead of asserting "
        "one.")

INCOME_ELASTICITY = declare(
    "INCOME_ELASTICITY", 1.0, kind="temporary_heuristic",
    unit="fraction of an essential's price drop passed through as extra "
         "discretionary spending power (dimensionless)",
    source=None, confidence="C",
    why="How much a fully-saturated essential's cheapness (price_ratio "
        "at its own floor) can move discretionary spending. 1.0 means "
        "'as much extra spending power as the essential's own price "
        "drop, one-for-one' - deliberately modest (not the >1 "
        "multiplier a strict income-effect model of Engel curves would "
        "license) because this model can only see ONE essential "
        "category's price moving, not a whole household budget. A real "
        "figure needs an actual household budget with several goods in "
        "it and real demand curves, which nothing in this project - "
        "including ENDOGENOUS_COSTS_AND_DOMAINS.md's Part 2, which "
        "covers production-cost pricing rather than consumer demand - "
        "yet models.")

INCOME_FACTOR_FLOOR = declare(
    "INCOME_FACTOR_FLOOR", 0.7, kind="temporary_heuristic",
    unit="multiple on discretionary revenue (minimum)", source=None,
    confidence="D",
    why="Defensive floor on the income effect if essentials ever get "
        "more expensive than day one, so a bad harvest cannot be read "
        "as crashing every discretionary business to nothing. Not "
        "reached under today's single essential category, per this "
        "method's own docstring; a placeholder bound rather than a "
        "measured one.")
INCOME_FACTOR_CEILING = declare(
    "INCOME_FACTOR_CEILING", 1.8, kind="temporary_heuristic",
    unit="multiple on discretionary revenue (maximum)", source=None,
    confidence="D",
    why="Defensive ceiling on the income effect in case "
        "ESSENTIAL_CATEGORIES ever grows and several ratios compound - "
        "see this method's own docstring. Not reached today; a "
        "placeholder bound, not a measured one.")

