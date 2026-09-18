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
discretionary spending power); goods_market_factor()/
goods_market_factor_if_opened()/goods_market_note()/
goods_market_summary() (the price itself, one concern and all of
them).

GoodsMixin is composed into EconomyMixin (economy.py) alongside the
other economy sub-mixins; see that file for the composition and for
the grouping evidence (CLAUDE.md's naming/heuristic-labelling
conventions apply here exactly as they did before the split - nothing
about the rules a number or a comment follows has changed, only which
file it lives in).
"""
from constants import declare


class GoodsMixin:

    # ---- goods-producing concerns: a market, not a fixed number --------------
    #
    # Every OTHER concern in this file pays the tree's flat `rev` for ever,
    # scaled only by the ramp above and this society's prices. A playtester's
    # question was exactly the case that breaks: an automated loom should make
    # an enormous margin the day it opens, because handlooms are everywhere and
    # power looms are not, and that margin has to erode as the rest of the
    # world catches up, cushioned by the fact that cheaper cloth pulls in
    # buyers who could not afford cloth before. `commodities.py` already has a
    # bounded, elastic price built for exactly this worked example (see
    # COMMODITIES.md section 4.2), but it is a standalone module Sim has never
    # imported - its own header says so - because it reasons in tonnes against
    # a national output table and has no notion of "years since you personally
    # opened this," or "how rich a population you can reach": Sim already has
    # both (opened_year, pop_scale, self.economy). This reuses commodities.py's
    # IDEAS - a bounded, elastic price, and the loom's own twenty-times figure
    # - natively, rather than bolting a tonnage model onto a system that has
    # never tracked a single tonne of anything. Wiring commodities.py itself
    # into Sim is the larger integration COMMODITIES.md section 11 describes
    # and explicitly defers.
    #
    # SCOPE IS DELIBERATELY NARROW. Only categories that are a tangible good
    # sold to a broad population get this: cloth (`textiles`), preserved food
    # and drink (`processing`), books and print matter (`printing`), cameras
    # and film (`photography`). Mining, instruments, transport and every
    # institution keep the flat figure - a mine's output already has its own
    # supply-and-price machinery below (MARKET_SHARE, material_price_factor)
    # answering a different question (what it costs YOU to buy ore, not what
    # a workshop earns selling a finished good), and a school or a patron is
    # exactly what the brief asked to leave alone.
    #
    # NUMBERS AND WHERE THEY CAME FROM, per category:
    #   eta (price elasticity of demand: how much buying responds to price):
    #     textiles 0.65 - apparel-demand studies typically put clothing's
    #       own-price elasticity in the 0.6-1.0 range, moderately elastic,
    #       neither a staple nor a luxury; picked at the inelastic end of that
    #       range so the early erosion the brief asks for is actually visible
    #       - at exactly 1.0 (unit elastic) revenue would sit dead flat as
    #       price moved, which demonstrates nothing. [C]
    #     processing 0.35 - agricultural-economics estimates for food-at-home
    #       demand (the USDA's Economic Research Service puts most packaged
    #       food categories around 0.2-0.6) cluster low: people keep eating
    #       whether or not canned milk or refined sugar gets cheaper. [C]
    #     printing 0.80 - discretionary but not a luxury in the pre-mass-media
    #       world these nodes describe; picked close to, but under, unit
    #       elastic. [C]
    #     photography 1.60 - camera and film equipment is squarely a luxury
    #       good throughout the period this applies to; luxury-goods demand
    #       studies commonly cite elasticities above 1.5 (fine goods and
    #       jewellery studies often land in the 1.5-2.5 range). [C]
    #   floor (price never falls below this fraction of the tree's own
    #     figure, however saturated the market): textiles and printing start
    #     from the bound already chosen for cloth (the one tracked commodity
    #     textiles maps to) in commodities.json, 0.35, nudged up to 0.40;
    #     processing starts tighter still, 0.45, because preserved food has a
    #     harder cost floor (a tin and the heat to seal it cost what they
    #     cost) and a harder ceiling on how much cheaper it can get before
    #     people just use raw ingredients instead, nudged up to 0.55;
    #     photography starts from coffee's bound in commodities.json, the one
    #     other luxury good that file prices, 0.5, nudged up to 0.55. Every
    #     nudge is the SAME finding: measuring this against the 700-year
    #     Monte Carlo runs (see the change's own report) showed a civilization
    #     already winning on the earlier, harsher floors on the edge of the
    #     700-year horizon (han_china_100ad, 2 of 10 seeds) losing every one
    #     of them once a goods concern's long-run earnings fell as far as the
    #     first pass had them fall. A model that turns a marginal win into a
    #     loss is not "more realistic," it is miscalibrated against a game
    #     this game already plays close to the edge of - so every floor here
    #     moved up by 0.05-0.1 from its first-pass figure, softening how much
    #     of the day-one margin is eventually given up, while leaving the
    #     shape of the curve (an early, visible decline) untouched.
    #   tau (years for the market to visibly respond to a new supply):
    #     textiles 35 - Britain's handloom weavers went from the dominant
    #       technology to a shrinking minority over roughly thirty to forty
    #       years, the 1810s to the 1850s; that is the number used for how
    #       long a cloth market takes to re-equilibrate around a new loom, at
    #       the slower end of that range for the same reason the floors moved
    #       - see above. Processing, printing and photography use a longer 40
    #       [C]: no equally specific diffusion-speed citation exists for
    #       those, so a longer, explicitly illustrative period stands in for
    #       one, and the same 700-year-horizon finding argued for slower
    #       rather than faster.
    #
    # EXTENDED, data/review/COMMODITY_DYNAMISM.md's second and third
    # findings. Two gaps in the original four categories, both measured
    # directly against a live Sim:
    #
    # (a) ZERO CROSS-ELASTICITY. "One loom at age 20 earns factor 0.7840.
    #     With a second identical loom running: 0.7840. With ten: 0.7840."
    #     goods_market_factor() used each concern's OWN age as a private
    #     clock standing in for "how saturated is the market" - a real
    #     number for a lone producer, but a fiction once a second producer
    #     (yours, or - per this file's existing goods_reach_factor comment
    #     - the rest of the world's) exists, because nothing summed what
    #     they were jointly supplying. Fixed below by pricing off the
    #     CATEGORY's total supply (every concern you operate in it, not one
    #     node's private clock) rather than one node's own age in isolation.
    #
    # (b) NO REAL CONSUMER ECONOMY. The brief's own richest idea: "when the
    #     public has less money, they buy less. So if the price of food
    #     goes down, the price people would be willing to pay for diamonds
    #     or records would go up." That is an ordinary income effect
    #     (cheaper necessities free up spending on everything else, the
    #     same logic behind Engel's law) and this file had no channel for
    #     it at all - `processing` (food) and, say, `photography` (a
    #     luxury) moved on completely independent clocks. The brief also
    #     named the actual businesses this should cover - "alcohol, or
    #     wine... food like pizza... gambling, casinos... books, card
    #     games, movies, phonographs, record players, newspapers" - and
    #     grepping the tree for them turns up real, revenue-bearing nodes
    #     (fud_distillation_spirits, fin_gambling_house, fin_racecourse,
    #     fin_theatre_business, hom_printed_books, hom_playing_cards_printed,
    #     if_tin_foil_phonograph, prn_radio_broadcasting,
    #     fin_newspaper_business...) that were earning the tree's flat
    #     figure for ever, the same as an aqueduct. `essential` below marks
    #     which categories are necessities (only `processing`, food, so
    #     far - the one the brief's own worked example is about) and
    #     income_factor()/essential_price_ratio() below implement the
    #     effect: a discretionary category earns more as the player's own
    #     essential-goods concerns get cheaper, and is neutral (no effect,
    #     not a penalty) when the player runs none. See those methods' own
    #     comments for the mechanism and its honest scope limit.
    #
    # NEW CATEGORY NUMBERS, same [C] estimation method as the original
    # four (see the class comment above for how those were reasoned):
    #   fermentation (alcohol - brewing, distilling, vinegar) 0.55/0.45/35:
    #     alcohol demand studies commonly cite elasticities of roughly
    #     0.3-0.9 (a consumption habit, not a nutritional necessity, but
    #     also not as freely substitutable as a camera); floor and tau
    #     follow processing's "real cost floor" and textiles' diffusion
    #     pace respectively, as the closest existing anchors.
    #   leisure (toys, games, puzzles, books, instruments) 1.10/0.45/35:
    #     hobby and entertainment goods are usually cited above unit
    #     elasticity but below photography's fine-goods range.
    #   sound (phonograph, gramophone, radio broadcasting) 1.30/0.50/35:
    #     a luxury technology good, the same reasoning as photography but
    #     slightly less extreme - audio reached a mass market somewhat
    #     faster, historically, than the camera did.
    #   media (newspapers, advertising, lending library, telegraph
    #     business) 0.85/0.40/35: an information good, close to printing's
    #     own 0.80.
    #   commerce (inns, hotels, restaurants, department stores, trading
    #     posts, coffeehouses) 1.00/0.45/30: unit-elastic hospitality and
    #     retail demand (commonly cited 0.8-1.3); a shorter tau because a
    #     service business's custom is understood to shift faster than a
    #     manufacturing good's.
    #   entertainment (gambling, lotteries, theatre, professional sport,
    #     racecourses - cat values "luxury", "spectacle" and "law" in the
    #     tree, which is where fin_gambling_house, fin_lottery,
    #     fin_theatre_business, fin_racecourse and fin_professional_sport
    #     actually live) 1.80/0.50/35: the single most discretionary
    #     bucket here, above photography, matching how elastic gambling
    #     and spectator-entertainment demand is usually cited to be.
    #   personal (perfume, cosmetics, toiletries) 1.10/0.45/35: ordinary
    #     personal-luxury demand, the same order as leisure.
    # `essential` is omitted (defaults False, i.e. discretionary) on every
    # category except processing; textiles is left discretionary too,
    # deliberately - clothing is not modelled as a nutritional necessity
    # here, only food is, matching the brief's own worked example exactly.
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
    # Which of the categories above are necessities, for income_factor()
    # below. Kept as its own set rather than scattering an `essential`
    # check across every reader, matching the class's own convention of
    # naming a scope decision once rather than repeating the condition.
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
        if self.has("citizenship"):                reach *= self.REACH_CITIZENSHIP
        if self.running("patron_senatorial"):      reach *= self.REACH_PATRON_SENATORIAL
        if self.running("patron_imperial"):        reach *= self.REACH_PATRON_IMPERIAL
        if self.running("exp_trade_route_extend"): reach *= self.REACH_TRADE_ROUTE_EXTENDED
        if self.running("railway"):                reach *= self.REACH_RAILWAY
        if self.running("telegraph_electric"):      reach *= self.REACH_TELEGRAPH
        return min(reach, self.REACH_CEILING)

    REACH_CITIZENSHIP = declare(
        "REACH_CITIZENSHIP", 1.15, kind="temporary_heuristic",
        unit="multiple on market reach", source=None, confidence="D",
        why="How much further citizenship extends a goods market's reach. "
            "Reuses the same flag _material_market_tonnes() already reads "
            "for the buying side, but the specific multiplier here is a "
            "separate, tuned guess, not derived from any attested trade "
            "network model.")
    REACH_PATRON_SENATORIAL = declare(
        "REACH_PATRON_SENATORIAL", 1.3, kind="temporary_heuristic",
        unit="multiple on market reach", source=None, confidence="D",
        why="As REACH_CITIZENSHIP, for a senatorial patron's network. "
            "Tuned, not derived.")
    REACH_PATRON_IMPERIAL = declare(
        "REACH_PATRON_IMPERIAL", 1.6, kind="temporary_heuristic",
        unit="multiple on market reach", source=None, confidence="D",
        why="As REACH_PATRON_SENATORIAL, for the imperial tier. Tuned, not "
            "derived.")
    REACH_TRADE_ROUTE_EXTENDED = declare(
        "REACH_TRADE_ROUTE_EXTENDED", 1.3, kind="temporary_heuristic",
        unit="multiple on market reach", source=None, confidence="D",
        why="What an extended trade route is worth to how far finished "
            "goods can travel to buyers. Tuned, not derived.")
    REACH_RAILWAY = declare(
        "REACH_RAILWAY", 1.35, kind="temporary_heuristic",
        unit="multiple on market reach", source=None, confidence="D",
        why="What a railway is worth to market reach for goods, mirroring "
            "the same flag's cost-side effect in mining_tech(). A real "
            "figure would come from actual freight-cost and travel-time "
            "reductions a railway buys, which this file does not model.")
    REACH_TELEGRAPH = declare(
        "REACH_TELEGRAPH", 1.15, kind="temporary_heuristic",
        unit="multiple on market reach", source=None, confidence="D",
        why="What the electric telegraph is worth to market reach - "
            "information about demand and price travelling faster than "
            "goods themselves, a real effect with an invented size here.")
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
        # RESULT CACHED PER (cat, self.year, operating's version), because
        # the walk below is still called far more often than its answer can
        # possibly change. A 150-year rome_100ad profile of 150 optimizer
        # steps found this called 75,748 times - 505 times per simulated
        # year - for the same reason the comment below already explains
        # (goods_market_factor() once per operating concern, income_factor()
        # again for the essential category, from every one of those calls):
        # nothing that changes what this function returns happens between
        # most of those calls in the same year.
        #
        # WHY THIS KEY IS SAFE, exhaustively:
        #   self.year only ever changes at one place in the whole engine
        #   (core.py's step(), `self.year += 1`, once per step) - so it is
        #   constant for the entire year's worth of calls this is trying to
        #   collapse, and a NEW year always gets a different key, never a
        #   stale hit.
        #   self.household.operating's membership is the other input read below (the
        #   `for m in ...: if m not in self.household.operating` test); `_operating_ver`
        #   is a plain counter bumped by _operating_changed(), which the
        #   _InvalidatingSet backing self.household.operating (see that class's own
        #   comment, top of file) fires on EVERY .add/.discard/.update/...
        #   from any of the nine-odd call sites across core.py/projects.py/
        #   economy.py/society.py - the exact mechanism _cap_factor's own
        #   cache already trusts for the same set, and it carries the same
        #   one accepted gap that one already has (see _operating_changed's
        #   own docstring): a caller that replaces self.household.operating with a
        #   bare set() rather than going through _reset_operating() stops
        #   this counter, same as it already stops _cap_factor. Not a new
        #   risk.
        #   `opened_year` (read below via `started`) is never mutated
        #   anywhere except projects.py's open_venture, and there only ever
        #   in the same call, immediately after, as `self.household.operating.add(k)`
        #   - grep the engine for "opened_year" and it is the only
        #   assignment site outside __init__'s empty {} and load_state's
        #   generic setattr (which itself calls _reset_operating(), and so
        #   _operating_changed(), right after setting it - see that
        #   function's own comment on why that ordering matters). So
        #   `_operating_ver` changing is a SUPERSET of every way
        #   `opened_year` can change: it cannot go stale on its own.
        #   `done_year` is read here only as a fallback for a member of
        #   `operating` whose opened_year entry is somehow still missing -
        #   which the paragraph above shows never happens along either real
        #   path into `operating` (open_venture always sets it in the same
        #   breath; restore() requires the node to already be mothballed,
        #   which means it went through open_venture earlier). The one place
        #   this fallback is actually reachable is a test fixture that adds
        #   directly to `operating` without ever opening anything - and that
        #   still bumps `_operating_ver` through the identical hook, so even
        #   there this cache is not stale, only (like the code before this
        #   change) reading done_year's default of self.year for a node that
        #   was never truly opened.
        key = (self.year, getattr(self.household, "_operating_ver", 0))
        cache = getattr(self.household, "_goods_cat_state_cache", None)
        if cache is None or cache[0] != key:
            cache = (key, {})
            self.household._goods_cat_state_cache = cache
        bucket = cache[1]
        if cat in bucket:
            return bucket[cat]
        ages = []
        # WHICH NODES CAN EVER BE IN THIS CATEGORY IS FIXED AT LOAD TIME,
        # so walk that (small, cached-once) list and test membership in
        # `operating` instead of sorting and filtering the whole operating
        # set on every single call. `cat` never changes after the tree is
        # loaded, so this cache needs no invalidation. Profiling a 300-year
        # single-seed run found this function alone (the `sorted(self.
        # operating)` scan) costing more self time than any other in the
        # engine - 7.1s of 34.4s total, called 1.5 million times because
        # goods_market_factor() calls it once per operating concern, and
        # income_factor() (reached from the SAME call, for every
        # non-essential concern) calls it again for the essential
        # category. Only max() and len() are taken from `ages` below, both
        # order-independent, so dropping the sort changes no result. See
        # PERFORMANCE.md.
        for node_id in self._nodes_in_cat(cat):
            if node_id not in self.household.operating:
                continue
            started = (getattr(self.household, "opened_year", None) or {}).get(node_id)
            if started is None:
                started = self.household.done_year.get(node_id, self.year)
            ages.append(max(0.0, self.year - started))
        if not ages:
            bucket[cat] = None
            return None
        result = (len(ages), max(ages), cfg)
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
    GOODS_TAU_ECONOMY_EXPONENT = declare(
        "GOODS_TAU_ECONOMY_EXPONENT", 0.25, kind="temporary_heuristic",
        unit="dimensionless exponent on self.economy", source=None,
        confidence="D",
        why="As GOODS_TAU_POP_SCALE_EXPONENT, for how much a more "
            "developed economy speeds a goods market's re-equilibration - "
            "plausible in direction, tuned in size.")

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
        category_state = self._goods_category_state(cat)
        if category_state is None:
            if extra <= 0:
                return None
            # NOTHING OF YOURS IS RUNNING YET, so there is no world_age to
            # inherit - the honest answer for "day one of the first concern
            # in a category" is the tree's own figure, exactly what
            # goods_market_factor() already returns for that case. Do not
            # invent a supply/age pair out of nothing to answer `extra` here;
            # let the caller's own bare 1.0 fallback (goods_market_factor_
            # if_opened) handle it, the same way goods_market_factor() does.
            return None
        n_active, world_age, cfg = category_state
        n_active += extra
        reach = self.goods_reach_factor()
        tau = max(1.0, cfg["tau"] * (self.pop_scale ** self.GOODS_TAU_POP_SCALE_EXPONENT)
                  * (self.economy ** self.GOODS_TAU_ECONOMY_EXPONENT) / reach)
        world_supply = 1.0 + world_age / tau
        total_supply = world_supply * n_active
        eta = cfg["eta"]
        price_ratio = max(cfg["floor"], min(1.0, total_supply ** (-1.0 / eta)))
        qty_ratio = min(total_supply, price_ratio ** (-eta))
        return price_ratio, qty_ratio, n_active

    def goods_category_price_ratio(self, cat):
        """The price this category's market currently pays, as a fraction
        of its day-one figure (1.0 = day one; falls toward the category's
        own floor as supply catches up). None if you operate nothing in
        it - "we do not know," not "assume 1.0" - see essential_price_ratio
        for the caller that turns that None into a neutral default.
        Independent of any one node, unlike goods_market_factor(k): this
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

    FARM_COST_PER_HA = declare(
        "FARM_COST_PER_HA", 75.0, kind="temporary_heuristic",
        unit="denarii/hectare", source=None, confidence="D",
        why="Purchase price of one hectare of productive farmland for the "
            "household's own staple supply. Not tied to FOREST_COST_PER_HA "
            "or to any attested land price; an independent, invented "
            "figure for a different land use.")
    HOUSING_COST_PER_PLACE = declare(
        "HOUSING_COST_PER_PLACE", 600.0, kind="temporary_heuristic",
        unit="denarii/place", source=None, confidence="D",
        why="Cost to build one place of durable worker housing. Not "
            "sourced to any attested construction cost; an invented figure "
            "sized to make the lever meaningful without being free.")
    TRADE_SCHOOL_COST_PER_SEAT = declare(
        "TRADE_SCHOOL_COST_PER_SEAT", 1200.0, kind="temporary_heuristic",
        unit="denarii/seat", source=None, confidence="D",
        why="Cost to found one seat of a named trade school (see "
            "labour.py's consumer of this figure, outside this file's "
            "scope). Not sourced to any attested cost of pre-industrial "
            "vocational training.")

    def invest_farm(self, hectares):
        """Buy productive farmland that lowers the household staple price."""
        hectares = float(hectares)
        cost = hectares * self.FARM_COST_PER_HA * self.price_index
        if hectares <= 0 or cost > self.household.capital:
            return 0.0
        self.household.capital -= cost
        self.household.farm_hectares = getattr(self.household, "farm_hectares", 0.0) + hectares
        return hectares

    def build_worker_housing(self, places):
        """Add durable worker housing and relieve household crowding."""
        places = float(places)
        cost = places * self.HOUSING_COST_PER_PLACE * self.price_index
        if places <= 0 or cost > self.household.capital:
            return 0.0
        self.household.capital -= cost
        self.household.worker_housing_places = getattr(self.household, "worker_housing_places", 0.0) + places
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
        ratio = self.essential_price_ratio()
        return max(self.INCOME_FACTOR_FLOOR, min(self.INCOME_FACTOR_CEILING,
                   1.0 + self.INCOME_ELASTICITY * (1.0 - ratio)))

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

    def goods_market_factor(self, k):
        """How a goods-producing concern's revenue has moved, relative to
        the day it opened, as the market it sells into fills up - shared
        with every OTHER concern selling the same kind of good, and lifted
        or dampened by how cheap the essentials market has made staples if
        this good is a discretionary one. See _goods_category_state's own
        comment for the cross-elasticity fix and income_factor's for the
        income effect; this function's job is only to turn those into one
        node's own revenue multiplier.

        Exactly 1.0 for a LONE concern on the day it opens, by
        construction (n_active=1, world_age=0, no essential concern
        running -> income_factor=1.0), so a player who opens one loom
        still earns the tree's own figure on the first turn, unchanged
        from before this pass - the brief's own original requirement.
        A SECOND concern in the same category, though, does not reset to
        1.0 even on ITS day one if the first is already mature: it is
        entering a market that already has supply in it, which is
        precisely what "compete" has to mean.

        Price then moves along an ordinary constant-elasticity demand
        curve against the category's SHARED total supply (see
        _goods_category_ratios): quantity sold varies as price ** (-eta),
        so solving for the price that clears exactly `total_supply` gives
        price_ratio = total_supply ** (-1/eta), clamped at the floor;
        quantity sold is the smaller of what supply can make and what
        that price will move. Revenue is price times quantity, both
        relative to day one - but quantity is now a SHARED total, split
        evenly across every concern currently selling into the category
        (`/ n_active`), because that total is what the whole category's
        combined capacity finds buyers for, not what any one concern
        alone would.
        """
        cat = self.nodes[k].get("cat")
        if k not in self.household.operating:
            return 1.0
        ratios = self._goods_category_ratios(cat)
        if ratios is None:
            return 1.0
        price_ratio, qty_ratio, n_active = ratios
        factor = price_ratio * qty_ratio / n_active
        if cat not in self.ESSENTIAL_CATEGORIES:
            factor *= self.income_factor()
        return factor

    def goods_market_factor_if_opened(self, k):
        """What goods_market_factor(k) would read on the day you actually
        opened k, if you opened it today - unlike goods_market_factor(k)
        itself, which answers a flat 1.0 for anything not yet `operating`
        because it has no day-one to measure yet, and every screen that
        lists a not-yet-opened concern (`ventures`'s "you know how but have
        not opened", `why`) reads that 1.0 as "the tree's own figure is what
        this would earn." For the FIRST concern in a category that is true.
        For a SECOND one it has never been true - see goods_market_factor's
        own docstring, which already says a second concern "does not reset
        to 1.0... it is entering a market that already has supply in it" -
        and nothing before this function let a player see that BEFORE
        opening it and finding out the hard way, which is exactly what two
        independent playtesters (Han, England) reported: revenue quietly
        far below what they had been shown, with no warning at the moment
        the decision to open was actually made.

        None for anything not a goods category. 1.0 - the honest, unhedged
        answer - when nothing of yours operates in this category yet: a
        real first mover really does get the tree's own figure, the same
        identity goods_market_factor() itself preserves.
        """
        cat = self.nodes[k].get("cat")
        cfg = self.GOODS_CATEGORIES.get(cat)
        if not cfg:
            return None
        if k in self.household.operating:
            return self.goods_market_factor(k)
        ratios = self._goods_category_ratios(cat, extra=1)
        if ratios is None:
            return 1.0
        price_ratio, qty_ratio, n_active = ratios
        factor = price_ratio * qty_ratio / n_active
        if cat not in self.ESSENTIAL_CATEGORIES:
            factor *= self.income_factor()
        return factor

    def goods_market_note(self, k):
        """One sentence on why THIS concern's earnings have moved (or, for
        one not yet opened, WOULD move) from the tree's own figure - so a
        player sees why a concern that opened at 400 a year now earns 280,
        instead of being left to notice the number changed and guess why
        (the brief's own example, in the brief's own words). Also says when
        competition, not just time, is the reason - the brief's own second
        question ("do two looms compete") answered on the one screen a
        player actually reads.

        WORKS BEFORE YOU OPEN IT, not only after. It used to return None for
        anything not yet `operating`, which meant the one moment a player
        could still choose differently - before committing capital to a
        second concern in an already-saturated category - was the one moment
        this said nothing at all. Two playtesters (Han, England) each
        reported market saturation eating a large, unexplained share of
        gross revenue; neither had anything on screen, before or after
        opening, that named it. See goods_market_factor_if_opened's own
        comment for the mechanism this now surfaces early.
        """
        cat = self.nodes[k].get("cat")
        cfg = self.GOODS_CATEGORIES.get(cat)
        if not cfg:
            return None
        opened = k in self.household.operating
        factor = (self.goods_market_factor(k) if opened
                  else self.goods_market_factor_if_opened(k))
        if factor is None or abs(factor - 1.0) < 0.01:
            return None
        node = self.nodes[k]
        quoted = node["rev"] * (self.venture_ramp(k) if opened else 1.0) * self.price_index
        now = quoted * factor
        floor_factor = cfg["floor"] ** (1.0 - cfg["eta"])
        direction = ("fallen, because supply of it - yours and everyone "
                     "else's - has grown faster than demand"
                     if factor < 1.0 else
                     "risen, because the cheaper it got the more buyers it "
                     "found")
        category_state = self._goods_category_state(cat)
        n_active = (category_state[0] if category_state else 0) + (0 if opened else 1)
        n_active = max(1, n_active)
        if opened:
            bits = ["the tree quotes %s a year for this; it actually earns "
                    "about %s now. The price this market pays has %s since "
                    "you opened it. It will settle at roughly %s a year "
                    "once that market saturation runs its course, not at "
                    "nothing - there is always a floor price and a floor of "
                    "buyers this kind of good keeps"
                    % ("{:,.0f}".format(quoted), "{:,.0f}".format(now), direction,
                       "{:,.0f}".format(quoted * floor_factor / n_active))]
        else:
            # THE WARNING BEFORE THE DECISION, not the postmortem after it.
            # `quoted` here is the tree's own figure exactly as `ventures`
            # and `why` already show it for anything not yet opened, so a
            # player reading this alongside that figure sees the same number
            # this note is about to tell them not to expect.
            bits = ["the tree quotes %s a year for this, and 'ventures'/'why' "
                    "show that same figure - but %d of yours already sell "
                    "into this market, so this would open already reduced by "
                    "market saturation, at about %s a year, not %s"
                    % ("{:,.0f}".format(quoted), n_active - 1,
                       "{:,.0f}".format(now), "{:,.0f}".format(quoted))]
        if n_active > 1:
            bits.append("%d concern%s of yours %s selling into this same "
                        "market at once and share what it will pay - each "
                        "one takes home a smaller slice than it would alone"
                        % (n_active, "" if n_active == 1 else "s",
                           "would be" if not opened else "are"))
        if cfg.get("essential"):
            bits.append("this is a necessity: people keep buying it "
                        "whatever it costs, which is why it barely moves "
                        "with price")
        elif self.essential_price_ratio() < 0.99:
            bits.append("food has gotten cheaper in your hands, which "
                        "leaves people more to spend on a good like this "
                        "one")
        if factor < 1.0:
            # THE WAY OUT, not only the diagnosis. This is a shared-total
            # mechanism scoped to ONE category (GOODS_CATEGORIES/
            # _goods_category_state): a concern in a different category is
            # not competing for the same buyers at all and keeps the tree's
            # own figure, which is the honest answer to "what do I do about
            # this" and was missing from every screen this appears on.
            bits.append("a concern in a DIFFERENT goods category is not "
                        "competing for these same buyers and is not reduced "
                        "by this at all")
        return ". ".join(bits)

    def goods_market_summary(self):
        """Every operating goods concern whose earnings have moved from the
        tree's own figure, worst first - the aggregate version of
        goods_market_note(), for `money` rather than one concern at a time.

        ALSO THE TOTAL, not only the worst row. Two playtesters (Han,
        England) each watched market saturation eat a large share of gross
        revenue by measuring it themselves against a total they had to
        reconstruct on their own - this screen told them which single
        concern was worst hit and never added the pieces up, so "the market
        is taking some of what I earn" never became a number a player could
        actually read against their own revenue. This is not a new
        mechanism and not a bug in the existing one: goods_market_factor()'s
        floors are exactly what GOODS_CATEGORIES documents, and several
        concerns competing in the same category is exactly the situation
        this file's cross-elasticity fix (see _goods_category_state) was
        written to represent honestly. It is a real, intended effect that
        simply had no total attached to it anywhere a player would read.
        """
        rows = []
        quoted_total = actual_total = 0.0
        for node_id in sorted(self.household.operating):
            cfg = self.GOODS_CATEGORIES.get(self.nodes[node_id].get("cat"))
            if not cfg:
                continue
            factor = self.goods_market_factor(node_id)
            node = self.nodes[node_id]
            quoted = node["rev"] * self.venture_ramp(node_id) * self.price_index
            quoted_total += quoted
            actual_total += quoted * factor
            if abs(factor - 1.0) > 0.01:
                rows.append((node_id, factor))
        if not rows:
            return None
        rows.sort(key=lambda entry: entry[1])
        worst = rows[0]
        cats_sharing = sorted({self.nodes[node_id].get("cat") for node_id, _factor in rows
                               if (self._goods_category_state(self.nodes[node_id].get("cat")) or (1,))[0] > 1})
        note = ("%d concern%s selling into a market that has moved since it "
                "opened: %s is at %d%% of the tree's own figure, because "
                "supply of what it makes has grown since it opened. "
                "'ventures' says the same thing for each one"
                % (len(rows), "" if len(rows) == 1 else "s",
                   worst[0], round(worst[1] * 100)))
        if cats_sharing:
            note += (". You are running more than one concern selling into "
                     "the same market in: %s - they are competing with each "
                     "other, not just with time" % ", ".join(cats_sharing))
        # THE NUMBER THAT WAS MISSING: total denarii a year, and what share
        # of these concerns' own quoted figures that is - the "47% of gross
        # revenue" a player has to be able to read directly, not infer.
        gap = quoted_total - actual_total
        if quoted_total > 0.5 and abs(gap) > 0.5:
            pct = round(100.0 * abs(gap) / quoted_total)
            if gap > 0:
                note += (". Altogether, market saturation is taking about %s "
                         "a year from these concerns - %d%% of what their own "
                         "quoted figures add up to. It does not recover on "
                         "its own: opening ANOTHER concern in a category you "
                         "are already saturating makes this worse, not "
                         "better, while a concern in a category you do not "
                         "yet run keeps the tree's own figure"
                         % ("{:,.0f}".format(gap), pct))
            else:
                note += (". Altogether, these concerns are earning about %s "
                         "a year MORE than their own quoted figures add up "
                         "to (%d%%) - cheap, saturated essentials have left "
                         "buyers with more to spend on the rest"
                         % ("{:,.0f}".format(-gap), pct))
        return note

