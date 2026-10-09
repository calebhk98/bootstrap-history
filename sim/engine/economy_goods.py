"""The goods market: cloth, preserved food, print, cameras - price that moves.

Split out of economy_market.py (see economy.py's own docstring for the
whole split's history): every method here answers what a FINISHED,
SOLD good actually earns once the market around it has had time to
react - elasticity, a floor beneath which the price never falls, how
many years that reaction takes (tau), cross-elasticity between two of
your own concerns competing in the same category, and the income
effect of cheap staples freeing up spending on everything else.
Covers: goods_reach_factor() (how much of the population you can
actually reach); _goods_category_state()/_nodes_in_cat()/
_goods_category_ratios()/goods_category_price_ratio() (the shared
per-category state several of the others read); essential_price_ratio()
(the staples side of the income effect); invest_farm()/
build_worker_housing() (buying down that same essential price and
housing cost); income_factor() (turning the price ratio into
discretionary spending power); goods_category_factor() and
goods_category_factor_with_entrants() (the price itself, for the
concerns actors run).

GoodsMixin is composed into EconomyMixin (economy.py) alongside the
other economy sub-mixins; see that file for the composition and for
the grouping evidence. CLAUDE.md's naming/heuristic-labelling
conventions apply here exactly as they do everywhere else in the
engine, regardless of which file a method lives in.
"""
from sim.constants import declare
from . import money_units
from sim.unit_conversions import PERCENT_SCALE
from sim.agents.api import edges


class GoodsMixin:

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

    def goods_reach_factor(self):
        """How much further than a purely local market your goods can travel,
        and so how fast you saturate the market you can reach.

        The brief asks for this explicitly: market size "should depend on...
        how far your goods can travel." Reuses the exact signals
        _material_market_tonnes() already uses for the OPPOSITE direction (how
        far your BUYING reach extends) - a patron's name, citizenship, a
        standing trade route, a railway, a telegraph - because a network that
        gets you more iron also gets your cloth to more buyers; it would be an
        odd model that widened one side of the ledger with these flags and not
        the other. Capped, like every other compounding multiplier in this
        file (MARKET_SHARE, material_price_factor), so five flags together do
        not multiply into an implausible number.
        """
        reach = 1.0
        reach = self.effect_factor("reach", reach)
        return min(reach, self.REACH_CEILING)

    REACH_CEILING = declare(
        "REACH_CEILING", 3.0, kind="temporary_heuristic",
        unit="multiple on market reach (maximum)", source=None,
        confidence="D",
        why="Cap on how far compounding every reach flag together can "
            "extend a market, so five flags at once do not multiply into an "
            "implausible number - the same defensive-cap pattern MARKET_SHARE "
            "and material_price_factor use elsewhere in this file. The cap's "
            "own value is picked for plausibility, not derived.")

    def _goods_category_state(self, cat):
        """(n_active, world_age, cfg) for a goods category: every one of
        YOUR OWN concerns currently operating in it, and how long the
        oldest of them has been open. None if this is not a goods category
        at all, or you operate nothing in it.

        THE FIX FOR ZERO CROSS-ELASTICITY. COMMODITY_DYNAMISM.md measured
        it directly: two identical looms, same age, both showed a revenue
        factor of 0.7840 - "bit-for-bit identical... neither affected the
        other at all," because the old formula's only inputs were one
        node's own age and the civilization-wide scalars, with no shared
        state for "how much of this is already being made." n_active below
        is that shared state: every concern in the category counts toward
        the SAME total supply, so a second loom genuinely competes with
        the first rather than each independently pretending to have the
        market alone. world_age uses the OLDEST still-operating concern
        (max, not min, over each member's own age) so a lone producer's
        day-one factor is unchanged (see goods_market_factor's own
        docstring for why that identity matters): with one concern, this
        is exactly the age that concern's own private clock always used;
        with several, it is when this player's presence in the category
        began, which is the right reference point for "how long has
        outside diffusion had to work on this market."
        """
        cfg = self.GOODS_CATEGORIES.get(cat)
        if not cfg:
            return None
        # Result cached per (cat, year, operating version). Key safe via
        # self.year (step), _operating_ver (add/discard), opened_year (open_venture).
        scenario = self.state.scenario
        projects = self.state.projects
        key = (scenario.year, self.household.operating_version, self.actor_market_version())
        cache = getattr(self.household, "_goods_cat_state_cache", None)
        if cache is None or cache[0] != key:
            cache = (key, {})
            self.household._goods_cat_state_cache = cache
        bucket = cache[1]
        if cat in bucket:
            return bucket[cat]
        ages = []
        # Walk nodes_in_cat cache, test membership in operating.
        for node_id in self._nodes_in_cat(cat):
            if node_id not in projects.operating:
                continue
            started = (getattr(projects, "opened_year", None) or {}).get(node_id)
            if started is None:
                started = projects.done_year.get(node_id, scenario.year)
            ages.append(max(0.0, scenario.year - started))
        # firms and governments selling into the category share the same demand
        sellers = len(ages) + self.actor_concerns_in(cat)
        if not sellers:
            bucket[cat] = None
            return None
        result = (sellers, max(ages, default=0.0), cfg)
        bucket[cat] = result
        return result

    def _nodes_in_cat(self, cat):
        """Every node key that carries this goods category, in the tree's
        own (stable, insertion) order - independent of PYTHONHASHSEED and
        never changing after load, so this is built once per run and
        reused. See _goods_category_state's own comment for why this
        exists."""
        cache = getattr(self, "_nodes_by_cat_cache", None)
        if cache is None:
            cache = {}
            for node_id, node in self.nodes.items():
                category = node.get("cat")
                if category:
                    cache.setdefault(category, []).append(node_id)
            self._nodes_by_cat_cache = cache
        return cache.get(cat, ())

    GOODS_TAU_POP_SCALE_EXPONENT = declare(
        "GOODS_TAU_POP_SCALE_EXPONENT", 0.5, kind="temporary_heuristic",
        unit="dimensionless exponent on pop_scale", source=None,
        confidence="D",
        why="How much faster a goods market re-equilibrates in a larger "
            "civilisation - a bigger market plausibly absorbs and adapts "
            "to new supply faster, but this specific sub-linear exponent "
            "is tuned rather than fitted to any market-size-versus-"
            "diffusion-speed data.")
    def _goods_category_ratios(self, cat, extra=0):
        """(price_ratio, qty_ratio, n_active) for a whole category, shared
        by every concern that sells into it - the actual mechanism
        goods_market_factor() and goods_category_price_ratio() both read,
        so the two cannot drift apart. None if nothing of this player's is
        currently operating in the category AND `extra` is 0.

        `extra`: how many MORE concerns to price in as already sharing this
        category's total supply, beyond what you currently operate - 0 for
        every caller before this, 1 for goods_market_factor_if_opened()'s
        "what would a NEW one earn on its own day one, given the ones
        already running" question. Kept as a parameter on the one function
        that already owns this formula, rather than a second copy of it that
        could drift from this one, per this file's own convention elsewhere
        (see goods_market_factor's docstring on why goods_category_price_
        ratio() reads this same function instead of reimplementing it)."""
        # Cached value: (price_ratio, qty_ratio, n_active) or None per (cat, extra)
        # Dependencies: self.year, pop_scale, economy, household._operating_ver, household._done_ver
        # Invalidated by: _operating_changed(), _done_changed(), step() year/pop_scale/economy updates
        # Not serialized because: pure transient derived state recomputed on load
        scenario = self.state.scenario
        projects = self.state.projects
        economy = self.state.economy
        shared_key = (
            scenario.year,
            getattr(self, "pop_scale", 1.0),
            economy.output_per_head,
            self.household.operating_version,
            self.household.done_version,
            self.actor_market_version(),
        )
        cache = getattr(self.household, "_goods_category_ratios_cache", None)
        if cache is None or cache[0] != shared_key:
            cache = (shared_key, {})
            self.household._goods_category_ratios_cache = cache
        bucket = cache[1]
        pair_key = (cat, extra)
        if pair_key in bucket:
            return bucket[pair_key]

        category_state = self._goods_category_state(cat)
        if category_state is None:
            bucket[pair_key] = None
            return None
        n_active, world_age, cfg = category_state
        n_active += extra
        reach = self.goods_reach_factor()
        tau = max(1.0, cfg["tau"] * (self.pop_scale ** self.GOODS_TAU_POP_SCALE_EXPONENT) / reach)
        world_supply = 1.0 + world_age / tau
        total_supply = world_supply * n_active
        eta = cfg["eta"]
        price_ratio = max(cfg["floor"], min(1.0, total_supply ** (-1.0 / eta)))
        qty_ratio = min(total_supply, price_ratio ** (-eta))
        result = (price_ratio, qty_ratio, n_active)
        bucket[pair_key] = result
        return result

    def goods_category_price_ratio(self, cat):
        """The price this category's market currently pays, as a fraction
        of its day-one figure (1.0 = day one; falls toward the category's
        own floor as supply catches up). None if you operate nothing in
        it - "we do not know," not "assume 1.0" - see essential_price_ratio
        for the caller that turns that None into a neutral default.
        Independent of any one node, unlike goods_market_factor(node_id): this
        is the market-wide number income_factor() below needs, since a
        player's disposable income depends on what food costs in general,
        not on one specific cannery."""
        ratios = self._goods_category_ratios(cat)
        return None if ratios is None else ratios[0]

    def essential_price_ratio(self):
        """A stand-in for 'the cost of living', averaged over every
        ESSENTIAL category (today: just `processing`, food) the player
        currently operates a concern in. 1.0 (neutral) if none - this
        model only ever learns food got cheaper because the player's own
        preserving/processing capacity made it so; it has no independent
        notion of a national food price. That is a real scope limit
        (COMMODITY_DYNAMISM.md's own finding about population elsewhere in
        this file: "this is a solo-player economic simulation... not a
        multi-agent market"), stated rather than hidden behind a default
        that looks like data.
        """
        ratios = [self.goods_category_price_ratio(category)
                  for category in sorted(self.ESSENTIAL_CATEGORIES)]
        ratios = [ratio for ratio in ratios if ratio is not None]
        market_ratio = sum(ratios) / len(ratios) if ratios else 1.0
        # Household-backed farms supply staples even before a processing
        # concern exists. Diminishing returns reach the same 0.55 floor as the
        # established food market rather than making subsistence free.
        farm_ha = max(0.0, getattr(self.household, "farm_hectares", 0.0))
        farm_ratio = max(self.HOUSEHOLD_FARM_PRICE_RATIO_FLOOR,
                         1.0 / (1.0 + farm_ha / self.HOUSEHOLD_FARM_HECTARES_HALF_EFFECT))
        return min(market_ratio, farm_ratio)

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

    FARM_LABOUR_HOURS_PER_HA = declare(
        "FARM_LABOUR_HOURS_PER_HA", 1500.0, kind="temporary_heuristic",
        unit="labour hours per hectare", source=None, confidence="D",
        why="Purchase price of one hectare of productive farmland for the "
            "household's own staple supply. Not tied to FOREST_COST_PER_HA "
            "or to any attested land price; an independent, invented "
            "figure for a different land use.")
    FARM_COST_PER_HA = money_units.PricedInLabourHours("FARM_LABOUR_HOURS_PER_HA")
    HOUSING_LABOUR_HOURS_PER_PLACE = declare(
        "HOUSING_LABOUR_HOURS_PER_PLACE", 12000.0, kind="temporary_heuristic",
        unit="labour hours per place", source=None, confidence="D",
        why="Cost to build one place of durable worker housing. Not "
            "sourced to any attested construction cost; an invented figure "
            "sized to make the lever meaningful without being free.")
    HOUSING_COST_PER_PLACE = money_units.PricedInLabourHours("HOUSING_LABOUR_HOURS_PER_PLACE")
    TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT = declare(
        "TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT", 24000.0, kind="temporary_heuristic",
        unit="labour hours per seat", source=None, confidence="D",
        why="Cost to found one seat of a named trade school (see "
            "labour.py's consumer of this figure, outside this file's "
            "scope). Not sourced to any attested cost of pre-industrial "
            "vocational training.")
    TRADE_SCHOOL_COST_PER_SEAT = money_units.PricedInLabourHours("TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT")

    def farm_price_per_hectare(self):
        """What one hectare of farmland costs now (`buy farm`, `quote farm`)."""
        return self.FARM_COST_PER_HA * self.price_index

    def trade_school_price_per_seat(self):
        """What one trade-school seat costs now (`buy school`, `quote school`)."""
        return self.TRADE_SCHOOL_COST_PER_SEAT * self.price_index

    def invest_farm(self, hectares):
        """Buy productive farmland that lowers the household staple price."""
        hectares = float(hectares)
        cost = hectares * self.farm_price_per_hectare()
        household = self.state.household
        if hectares <= 0 or cost > household.capital:
            return 0.0
        self.pay_edge(edges.EDGE_LANDOWNERS, cost, "farmland bought")
        economy = self.state.economy
        holdings = self.state.holdings
        holdings.farm_hectares = (getattr(holdings, "farm_hectares", 0.0) or 0.0) + hectares
        return hectares

    def housing_price_per_place(self):
        """What one place of worker housing costs now (`buy housing`, `quote housing`, room advice)."""
        return self.HOUSING_COST_PER_PLACE * self.price_index

    def build_worker_housing(self, places):
        """Add durable worker housing and relieve household crowding."""
        places = float(places)
        cost = places * self.housing_price_per_place()
        household = self.state.household
        if places <= 0 or cost > household.capital:
            return 0.0
        self.pay_edge(edges.EDGE_BUILDERS, cost, "worker housing built")
        household.worker_housing_places = (getattr(household, "worker_housing_places", 0.0) or 0.0) + places
        return places

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

    def income_factor(self):
        """How much extra (or, in principle, less) a population has to
        spend on everything that is NOT a staple, from how cheap staples
        currently are.

        The brief's own framing, almost verbatim: "when the public has
        less money, they buy less. So if the price of food goes down, the
        price people would be willing to pay for diamonds or records would
        go up." That is a real, textbook mechanism (an income effect: money
        freed up by a cheaper necessity gets spent on everything else) and
        this is the one channel this model can see it through - see
        essential_price_ratio()'s own comment for the honest scope limit.
        Neutral (1.0, no effect either way) whenever the player runs no
        essential concern, so a run that never touches food processing
        behaves exactly as it did before this pass - see the class comment
        on GOODS_CATEGORIES for why that identity matters to the test
        suite. Clamped defensively in case ESSENTIAL_CATEGORIES ever grows
        to more than one category and their ratios compound oddly; with
        today's single essential category (processing, floor 0.55) the
        clamp never actually binds (1.0 + 1.0*(1-0.55) = 1.45).
        """
        # Cached value: float multiplier on discretionary revenue
        # Dependencies: year, pop_scale, economy, household _operating_ver, _done_ver, farm_hectares
        # Invalidated by: any change to essential category supply or household farm_hectares
        # Not serialized because: pure transient derived state recomputed on load
        scenario = self.state.scenario
        economy = self.state.economy
        holdings = self.state.holdings
        projects = self.state.projects
        shared_key = (
            scenario.year,
            getattr(self, "pop_scale", 1.0),
            economy.output_per_head,
            self.household.operating_version,
            self.household.done_version,
            getattr(holdings, "farm_hectares", 0.0) or 0.0,
            self.actor_market_version(),
        )
        cache = getattr(self.household, "_income_factor_cache", None)
        if cache is not None and cache[0] == shared_key:
            return cache[1]

        ratio = self.essential_price_ratio()
        factor = max(self.INCOME_FACTOR_FLOOR, min(self.INCOME_FACTOR_CEILING,
                     1.0 + self.INCOME_ELASTICITY * (1.0 - ratio)))
        self.household._income_factor_cache = (shared_key, factor)
        return factor

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


    def goods_category_factor(self, cat):
        """What one seller's revenue in a goods category has become relative to
        the day-one figure, once the whole category's supply (the founder's
        concerns and every actor's) is shared out: price times quantity over
        the number of sellers, lifted or dampened by the income effect."""
        projects = self.state.projects
        scenario = self.state.scenario
        economy = self.state.economy
        holdings = self.state.holdings

        # Cached value: category-level operating revenue factor
        # Dependencies: shared_key and household farm_hectares
        # Invalidated by: changes to operating, done, year, pop_scale, economy, farm_hectares
        # Not serialized because: transient derived state recomputed on demand
        shared_key = (
            scenario.year,
            getattr(self, "pop_scale", 1.0),
            economy.output_per_head,
            self.household.operating_version,
            self.household.done_version,
            getattr(holdings, "farm_hectares", 0.0) or 0.0,
            self.actor_market_version(),
        )
        cache = getattr(self.household, "_goods_mkt_op_factor_cache", None)
        if cache is None or cache[0] != shared_key:
            cache = (shared_key, {})
            self.household._goods_mkt_op_factor_cache = cache
        bucket = cache[1]
        if cat in bucket:
            return bucket[cat]

        ratios = self._goods_category_ratios(cat)
        if ratios is None:
            bucket[cat] = 1.0
            return 1.0
        price_ratio, qty_ratio, n_active = ratios
        factor = price_ratio * qty_ratio / n_active
        if cat not in self.ESSENTIAL_CATEGORIES:
            factor *= self.income_factor()
        bucket[cat] = factor
        return factor


    def goods_category_factor_with_entrants(self, cat, entrants):
        """One seller's revenue in a goods category relative to day one once `entrants` more
        sellers share the category's demand: the clearing price falls as supply rises."""
        ratios = self._goods_category_ratios(cat, extra=entrants)
        if ratios is None:
            return 1.0
        price_ratio, qty_ratio, n_active = ratios
        factor = price_ratio * qty_ratio / n_active
        if cat not in self.ESSENTIAL_CATEGORIES:
            factor *= self.income_factor()
        return factor
