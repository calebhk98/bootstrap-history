"""Goods markets, raw-material supply, electricity and freight.

Split out of economy.py (see that file's own docstring for why): this is
the "what does it cost to buy, and what can you sell" half of the
economy, covering four subjects that all end up answering a pricing or
scarcity question rather than a production-capacity one -

  - the goods market for finished, sold concerns (cloth, preserved food,
    print, cameras, ... - elasticity, floors, cross-elasticity between
    your own concerns, the income effect of cheap staples on discretionary
    spending);
  - raw-material supply and demand (the nine hand-named commodities and
    the generic mechanism generalising to the rest of the 162 tracked
    materials, stock vs flow, material throttling);
  - electricity as a physical quantity (generation, demand, the same
    worst-binding-constraint throttle iron and copper already use); and
  - freight (moving a material from where it comes from to the buyer,
    and the wire-chain report).

MarketMixin is composed into EconomyMixin (economy.py) alongside the
other economy sub-mixins; see that file for the composition and for the
grouping evidence (CLAUDE.md's naming/heuristic-labelling conventions
apply here exactly as they did before the split - nothing about the
rules a number or a comment follows has changed, only which file it
lives in).
"""
import collections, json, math, os

from .data import hard_pre, haversine_km, WAGES
from . import commodities as _commod
from constants import declare

from world import transport as freight_physics


class MarketMixin:

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
        rows.sort(key=lambda kv: kv[1])
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

    # ---- raw material supply ------------------------------------------------
    CHARCOAL_PER_HA = declare(
        "CHARCOAL_PER_HA", 0.75, kind="engineering_estimate",
        unit="tonnes charcoal/hectare/year, sustainable coppice yield",
        source="Order-of-magnitude figure for a sustainably managed "
               "coppice under traditional charcoal-burning practice; the "
               "same figure this module's own resource_throttle() "
               "docstring cites ('a hectare of coppice yields about 0.75 "
               "tonnes of charcoal a year').",
        confidence="C",
        why="Converts hectares of owned woodland into tonnes/year of "
            "charcoal - the single binding constraint that decides whether "
            "a blast furnace can run at all, per this file's own charcoal "
            "commentary.")
    # How much of the empire's annual output you can actually BUY. This is not
    # one number: charcoal is bulky, crumbles when carted, and is therefore a
    # LOCAL commodity no matter how much of it the empire makes in total, while
    # coal is barely used by anyone so you can have almost all of it.
    # gold's 0.01 is not re-guessed: it is commodities.json's own gold entry
    # (market_share, already reasoned there against the same imperial-mint
    # scarcity that makes MARKET_SHARE["silver"] this low), so the two files
    # agree on how tightly a private buyer can get at the metalla's gold.
    _MARKET_SHARE_WHY = (
        "What fraction of the empire's whole annual national output of "
        "this material an ordinary buyer with no special standing can "
        "actually reach, before patronage multipliers (see "
        "_material_market_tonnes) apply. Bulk, transportability and how "
        "concentrated ownership of the resource is (imperial mints and "
        "metalla versus an ordinary quarry) all matter physically, but no "
        "attested Roman market-share figure exists for any of these "
        "materials; each is reasoned by hand from those physical "
        "properties, not measured.")
    MARKET_SHARE_CHARCOAL = declare(
        "MARKET_SHARE_CHARCOAL", 0.002, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D",
        why=_MARKET_SHARE_WHY + " Charcoal specifically is bulky and "
            "crumbles when carted, so it is treated as almost entirely "
            "a local commodity regardless of total empire-wide output.")
    MARKET_SHARE_IRON = declare(
        "MARKET_SHARE_IRON", 0.03, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D", why=_MARKET_SHARE_WHY)
    MARKET_SHARE_COPPER = declare(
        "MARKET_SHARE_COPPER", 0.03, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D", why=_MARKET_SHARE_WHY)
    MARKET_SHARE_LEAD = declare(
        "MARKET_SHARE_LEAD", 0.03, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D", why=_MARKET_SHARE_WHY)
    MARKET_SHARE_TIN = declare(
        "MARKET_SHARE_TIN", 0.05, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D", why=_MARKET_SHARE_WHY)
    MARKET_SHARE_SILVER = declare(
        "MARKET_SHARE_SILVER", 0.01, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D",
        why=_MARKET_SHARE_WHY + " Held low specifically because "
            "silver mining was heavily imperial-mint property, which "
            "MARKET_SHARE_GOLD's own sourced figure also reflects.")
    MARKET_SHARE_COAL = declare(
        "MARKET_SHARE_COAL", 0.50, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D",
        why=_MARKET_SHARE_WHY + " Held high specifically because coal "
            "was barely used by anyone in this period, so almost all "
            "of the (small) national output is available to a buyer.")
    MARKET_SHARE_SALTPETRE = declare(
        "MARKET_SHARE_SALTPETRE", 0.0, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D",
        why=_MARKET_SHARE_WHY + " Zero specifically because there is "
            "no open saltpetre market at all in this period; it is "
            "made in nitre beds, not bought (see build_nitre).")
    MARKET_SHARE_GOLD = declare(
        "MARKET_SHARE_GOLD", 0.01, kind="temporary_heuristic",
        unit="fraction of national output",
        source="commodities.json's own gold entry (market_share), "
               "already reasoned there against imperial-mint scarcity - "
               "reused here rather than re-guessed so the two files "
               "agree on how tightly a private buyer can reach the "
               "metalla's gold.",
        confidence="C", why=_MARKET_SHARE_WHY)
    MARKET_SHARE = {
        'charcoal': MARKET_SHARE_CHARCOAL,
        'iron': MARKET_SHARE_IRON,
        'copper': MARKET_SHARE_COPPER,
        'lead': MARKET_SHARE_LEAD,
        'tin': MARKET_SHARE_TIN,
        'silver': MARKET_SHARE_SILVER,
        'coal': MARKET_SHARE_COAL,
        'saltpetre': MARKET_SHARE_SALTPETRE,
        'gold': MARKET_SHARE_GOLD,
    }

    # ---- GENERALISING BEYOND THE 9 HAND-NAMED COMMODITIES --------------------
    #
    # data/review/COMMODITY_DYNAMISM.md, an audit run directly against
    # this engine: 149 of the 162 distinct material keys the tech tree uses
    # (about 92%) had a price read once from prices.json at load time and
    # never revisited for scarcity, surplus or anything else, because
    # MATERIAL_CHECKS/MARKET_SHARE above only ever named 13 keys by hand.
    # Its own worked case was aluminium: "no mine, no supply lever of any
    # kind... nothing in economy.py even contains the string aluminium."
    #
    # The fix below is NOT a per-material rule. It is a generic fallback that
    # activates for any material key this file has no curated entry for,
    # using the one number every material already has: its own book price in
    # prices.json (every material key a node's `mat` dict names MUST have a
    # prices.json entry already, or data.py's own load() would have raised
    # building `_material_cost` in the first place - so this genuinely
    # covers all 162, not just the ones anyone thought to add). A cheap,
    # plentiful material gets assumed to have a large national output and a
    # wide buyable share; a dear, rare one gets less of both - fitted, not
    # guessed, from the curated figures the 9 tracked commodities already
    # carry: iron (1.0 den/kg) is rated 82,500 t/yr, copper (4.0) 15,000,
    # gold (3,440) 9. log(output) against log(price) across those three
    # (four orders of magnitude in price) fits close to output =
    # 82,500 / price**1.1 - which reproduces gold's real 9 t/yr to within
    # 20% despite the fit never having seen gold's number, because scarcity
    # and price genuinely do move together, not because gold is special.
    # This is exactly the standard COMMODITY_DYNAMISM.md sets: "a commodity
    # nobody anticipated must behave correctly because the mechanism is
    # supply and demand, not because somebody wrote a rule for it."
    GENERIC_OUTPUT_ANCHOR_T_PER_YR = declare(
        "GENERIC_OUTPUT_ANCHOR_T_PER_YR", 82500.0, kind="engineering_estimate",
        unit="tonnes/year at price=1 denarius/kg", source=
        "Fitted (log-log regression) from resources.json's own curated "
        "empire outputs for iron (1.0 den/kg -> 82,500 t/yr), copper "
        "(4.0 -> 15,000 t/yr) and gold (3,440 -> 9 t/yr) - see the class "
        "comment above for the fit and its cross-check against gold's own "
        "number, which the fit never saw.",
        confidence="C",
        why="The anchor point of a fitted output-vs-price curve used to "
            "guess national output for any of the 149 material keys this "
            "file has no curated resources.json figure for. A real answer "
            "needs an actual output figure per material, which is exactly "
            "what data/production/'s coverage work is building toward "
            "replacing this fallback with.")
    GENERIC_OUTPUT_PRICE_EXPONENT = declare(
        "GENERIC_OUTPUT_PRICE_EXPONENT", 1.1, kind="hardcoded_outcome",
        unit="dimensionless exponent on price", source=
        "Same three-point log-log fit as GENERIC_OUTPUT_ANCHOR_T_PER_YR.",
        confidence="C",
        why="How fast national output falls as a material's own book price "
            "rises, in the fitted fallback curve - scarcity and price "
            "moving together is a real, general economic regularity; this "
            "specific exponent is fitted to three commodities and "
            "extrapolated to every other material, which is the honest "
            "limit of what three points can support.")
    GENERIC_OUTPUT_FLOOR_T_PER_YR = declare(
        "GENERIC_OUTPUT_FLOOR_T_PER_YR", 5.0, kind="temporary_heuristic",
        unit="tonnes/year (minimum)", source=None, confidence="D",
        why="Safety floor so an extremely expensive material's fitted "
            "output never rounds to a market that supplies literally "
            "nothing. Not fitted; a defensive bound on the formula above.")
    GENERIC_OUTPUT_CEILING_T_PER_YR = declare(
        "GENERIC_OUTPUT_CEILING_T_PER_YR", 400000.0, kind="temporary_heuristic",
        unit="tonnes/year (maximum)", source=None, confidence="D",
        why="Safety ceiling so an extremely cheap material's fitted output "
            "never runs away to an implausible national output. Not "
            "fitted; a defensive bound on the formula above.")

    def _commodity_ledger(self):
        """The 9 curated commodities from commodities.json, as a
        CommodityLedger, cached on the CLASS (not the instance): the file
        does not change mid-run and building it involves a JSON load, the
        same reasoning _material_commodity_map below uses. Used two ways:
        as the reverse index from a material key to a curated commodity id
        (cast_iron_kg means "iron" there even though MATERIAL_CHECKS has
        never listed it), and, for the 4 curated-but-never-priced
        commodities this file's own MARKET_SHARE has never named (cloth,
        wool, cotton, copper_wire), as the SOURCE of national output and
        market share instead of the generic price-only guess below - see
        _generic_national_output_t_per_yr's own comment for why real,
        sourced data beats a formula wherever it already exists."""
        cached = getattr(MarketMixin, "_commod_ledger_cache", None)
        if cached is None:
            cached = MarketMixin._commod_ledger_cache = _commod.CommodityLedger()
        return cached

    def _material_commodity_map(self):
        """material key -> curated commodity id, from commodities.json's
        own material_keys lists. Cached on the class for the same reason
        as _commodity_ledger."""
        cached = getattr(MarketMixin, "_material_commod_map_cache", None)
        if cached is None:
            cached = {}
            for commodity_id, commodity in self._commodity_ledger().commodities.items():
                for material_key in commodity.get("material_keys", []):
                    cached[material_key] = commodity_id
            MarketMixin._material_commod_map_cache = cached
        return cached

    def _material_prices(self):
        """The flat per-kg book price for every material key in
        prices.json, read directly rather than threaded through Sim's
        constructor - the same pattern commodities.py's own
        load_commodities() already uses for its own file. Cached on the
        class: prices.json does not change mid-run."""
        cached = getattr(MarketMixin, "_material_prices_cache", None)
        if cached is None:
            raw = json.load(open(os.path.join(_commod.ROOT, "data", "prices.json")))
            cached = {material_key: value["p"] for material_key, value in raw["purchase_prices_denarii"].items()
                     if isinstance(value, dict) and "p" in value}
            MarketMixin._material_prices_cache = cached
        return cached

    def _book_price_per_kg(self, tag):
        """Denarii/kg for a raw material key (aluminium_kg, straight out of
        prices.json) or a curated commodity id (cloth, straight out of
        commodities.json's own base_price - the two files agree by
        construction, see commodities.json's own `_doc.reused_from`). None
        if this file cannot price it at all, which should not happen for
        any material key the tech tree actually uses (see the class
        comment above)."""
        prices = self._material_prices()
        if tag in prices:
            return prices[tag]
        commodity = self._commodity_ledger().commodities.get(tag)
        if commodity:
            price = float(commodity.get("base_price_denarii_per_kg", 0.0) or 0.0)
            return price or None
        return None

    def _material_tag(self, mat_key):
        """Which (commodity id, supply-pool tag) a raw material key draws
        on, generalised beyond the 13 keys MATERIAL_CHECKS names by hand.

        Three tiers, most-specific first: MATERIAL_CHECKS (the 9 originally
        tracked commodities, unchanged); commodities.json's own
        material_keys grouping (iron_bloom_kg and cast_iron_kg both mean
        "iron" there, cloth_bag_kg and linen_kg both mean "cloth," though
        none of MATERIAL_CHECKS above has ever listed any of them); and,
        for the material nothing has ever named, its own bare material key
        as a one-member commodity of itself - "aluminium_kg" becomes the
        commodity "aluminium_kg" (its own price identifies it; no reverse
        lookup needed). This is the actual generalisation
        COMMODITY_DYNAMISM.md's finding describes: 149 of 162 material
        keys got no price response at all because nothing but membership
        in a 13-entry hand list was ever asked.
        """
        pair = self.MATERIAL_CHECKS.get(mat_key)
        if pair:
            return pair
        cid = self._material_commodity_map().get(mat_key, mat_key)
        return (cid, "mine:" + cid)

    def _generic_national_output_t_per_yr(self, tag):
        """National output for a commodity/material this file has no
        curated resources.json figure for - the MARKET half of supply (see
        _material_market_tonnes). Prefers real data over a guess wherever
        real data exists: if `tag` is one of the 4 commodities.json defines
        but MARKET_SHARE has never priced (cloth, wool, cotton,
        copper_wire), this reads THAT commodity's own national/manufacturing
        output through CommodityLedger.country_output() - which already
        knows a built power loom raises cloth output, or cyanidation raises
        gold's, per commodities.json's own `produced_by` multipliers. That
        is COMMODITY_DYNAMISM.md's own third finding wired in for real:
        "a genuinely general elasticity-based price function... sitting
        unconnected." Only a material with no curated home at all (silk,
        glass, the acids and dyes and alloys) falls through to the generic
        price-derived formula documented on GENERIC_OUTPUT_ANCHOR_T_PER_YR
        above."""
        ledger = self._commodity_ledger()
        if tag in ledger.commodities:
            return ledger.country_output(tag, built=self.household.done)
        price = self._book_price_per_kg(tag)
        if price is None or price <= 0:
            return self.GENERIC_OUTPUT_CEILING_T_PER_YR
        out = self.GENERIC_OUTPUT_ANCHOR_T_PER_YR / (price ** self.GENERIC_OUTPUT_PRICE_EXPONENT)
        return max(self.GENERIC_OUTPUT_FLOOR_T_PER_YR,
                   min(self.GENERIC_OUTPUT_CEILING_T_PER_YR, out))

    def _generic_market_share(self, tag):
        """What fraction of _generic_national_output_t_per_yr an ordinary
        buyer (no special standing) can reach, for a commodity/material
        MARKET_SHARE has no curated figure for. Same two-tier preference as
        the output figure: a commodities.json commodity's own market_share
        (cloth 0.5, wool 0.4, cotton 1.0 trade-only, copper_wire 0.6) where
        one exists; otherwise a generic curve fitted the same way
        GENERIC_OUTPUT was - rarer, dearer materials are held closer (gold
        0.01, silver 0.01) and cheap bulk ones are wide open (coal 0.50) -
        clamped well inside that observed range since this is a default
        for a material nobody has separately reasoned about, not a
        specific claim."""
        ledger = self._commodity_ledger()
        if tag in ledger.commodities:
            return float(ledger.commodities[tag].get(
                "market_share", self.GENERIC_MARKET_SHARE_LEDGER_FALLBACK))
        price = self._book_price_per_kg(tag)
        if price is None or price <= 0:
            return self.GENERIC_MARKET_SHARE_NO_PRICE_FALLBACK
        return max(self.GENERIC_MARKET_SHARE_FLOOR,
                   min(self.GENERIC_MARKET_SHARE_CEILING,
                       self.GENERIC_MARKET_SHARE_SCALE
                       / (max(price, 0.01) ** self.GENERIC_MARKET_SHARE_PRICE_EXPONENT)))

    GENERIC_MARKET_SHARE_LEDGER_FALLBACK = declare(
        "GENERIC_MARKET_SHARE_LEDGER_FALLBACK", 0.03, kind="temporary_heuristic",
        unit="fraction of national output", source=None, confidence="D",
        why="Fallback market share for a curated commodities.json commodity "
            "that names no market_share field of its own - a middling, "
            "unremarkable buyable fraction picked so a missing field does "
            "not silently become 'unbuyable' or 'unlimited'.")
    GENERIC_MARKET_SHARE_NO_PRICE_FALLBACK = declare(
        "GENERIC_MARKET_SHARE_NO_PRICE_FALLBACK", 0.20, kind="temporary_heuristic",
        unit="fraction of national output", source=None, confidence="D",
        why="Fallback market share for a material this file cannot even "
            "price at all - deliberately generous (wide open) since a "
            "material with no price data has no basis for restricting it "
            "either; a placeholder rather than a reasoned figure.")
    GENERIC_MARKET_SHARE_SCALE = declare(
        "GENERIC_MARKET_SHARE_SCALE", 0.08, kind="engineering_estimate",
        unit="dimensionless scale on the price-fitted market-share curve",
        source="Fitted the same way GENERIC_OUTPUT_ANCHOR_T_PER_YR was, "
               "against the curated MARKET_SHARE figures for gold/silver "
               "(0.01, rare and dear) and coal (0.50, cheap and open).",
        confidence="C",
        why="Scale of the price-fitted curve giving a generic material's "
            "market share when nothing more specific is known. Same honest "
            "limit as the output fit: three curated points fitted and "
            "extrapolated, not a measurement for any specific material.")
    GENERIC_MARKET_SHARE_PRICE_EXPONENT = declare(
        "GENERIC_MARKET_SHARE_PRICE_EXPONENT", 0.4, kind="engineering_estimate",
        unit="dimensionless exponent on price", source=
        "Same three-point fit as GENERIC_MARKET_SHARE_SCALE.",
        confidence="C",
        why="How fast a generic material's buyable share shrinks as its "
            "price rises - rarer, dearer materials are held closer by "
            "whoever controls them, a real and general pattern; the "
            "specific exponent is fitted to three commodities.")
    GENERIC_MARKET_SHARE_FLOOR = declare(
        "GENERIC_MARKET_SHARE_FLOOR", 0.01, kind="temporary_heuristic",
        unit="fraction of national output (minimum)", source=None,
        confidence="D",
        why="Clamp so the fitted generic market-share curve never reaches "
            "a literal zero for an ordinary buyer, however dear the "
            "material - a defensive bound, not a reasoned floor.")
    GENERIC_MARKET_SHARE_CEILING = declare(
        "GENERIC_MARKET_SHARE_CEILING", 0.35, kind="temporary_heuristic",
        unit="fraction of national output (maximum)", source=None,
        confidence="D",
        why="Clamp so the fitted generic market-share curve stays well "
            "inside the observed range of the curated figures it was "
            "fitted from, per this method's own docstring ('a default for "
            "a material nobody has separately reasoned about, not a "
            "specific claim') - a defensive bound, not a reasoned ceiling.")

    def _normalize_material_name(self, mat):
        """Accept either spelling when a player names a material: the
        short curated name a mine has always used ("iron"), or the exact
        material key the tree itself uses ("aluminium_kg") - a player who
        has only ever seen `why` quote "aluminium_kg" in a bill of
        materials should not have to guess it needs no suffix, and the
        seven original short names must keep working exactly as before."""
        mat = str(mat or "").strip().lower()
        if not mat or mat in self.MINE_CAPEX_PER_T_YR:
            return mat
        prices = self._material_prices()
        if mat in prices or mat in self._commodity_ledger().commodities:
            return mat
        for suffix in ("_kg", "_g"):
            cand = mat + suffix
            if cand in prices:
                return cand
        return mat

    # Coke and charcoal are not interchangeable at one kg for one kg. A charcoal
    # blast furnace burns about 3 kg of charcoal per kg of iron; a coke furnace
    # burns about 1.6 kg of coke, and coke is about 1.6 kg of coal, so 2.56 kg
    # of coal. Switching fuel therefore MOVES the demand to a different material
    # at 0.85 of the mass, and that is the whole reason coke mattered: not that
    # it is better fuel, but that coal is dug and charcoal has to be grown.
    COKE_PER_CHARCOAL = declare(
        "COKE_PER_CHARCOAL", 0.85, kind="engineering_estimate",
        unit="kg coal-equivalent demand per kg of charcoal it replaces",
        source="Blast-furnace fuel consumption ratios: roughly 3 kg "
               "charcoal per kg of iron by the charcoal route, versus "
               "roughly 1.6 kg coke (itself roughly 1.6 kg of coal) per kg "
               "of iron by the coke route - see the comment above for the "
               "arithmetic (2.56 kg coal / 3 kg charcoal is approximately "
               "0.85).",
        confidence="C",
        why="Converts a node's charcoal demand into the equivalent coal "
            "demand when coke is the chosen fuel - the actual substitution "
            "that decided whether an industrialising civilisation is bound "
            "by grown fuel or dug fuel.")

    def chosen_fuel(self, k):
        """Which fuel this node would actually burn, given what you have.

        The tree had a fuel OR-group on the blast furnace and a hard-coded
        4,500 tonnes of charcoal in its material list. The group was decorative:
        picking coke changed the quality factor and left the charcoal demand
        exactly where it was, so the model could never show the one substitution
        that actually decided industrial history.
        """
        for group in (self.nodes[k].get("req_any") or []):
            if "fuel" not in str(group.get("group", "")).lower():
                continue
            best, pick = 0.0, None
            for opt, qual in (group.get("options") or {}).items():
                have = opt in self.household.done or opt not in self.nodes
                if have and float(qual) > best:
                    best, pick = float(qual), opt
            if pick and ("coke" in pick or "coal" in pick):
                return "coke"
        return "charcoal"

    def annual_material_demand(self):
        """Tonnes per year of the materials that actually bind, from work in hand."""
        demand = collections.Counter()
        for node_id in sorted(self.household.active):
            node = self.nodes[node_id]
            span = max(1.0, float(node.get("build_yrs") or node.get("yrs") or 1.0))
            coke = self.chosen_fuel(node_id) == "coke"
            for material, quantity in node["mat"].items():
                if coke and material in ("charcoal_kg", "firewood_kg"):
                    demand["coal_kg"] += float(quantity) * self.COKE_PER_CHARCOAL / span / 1000.0
                    continue
                demand[material] += float(quantity) / span / 1000.0     # kg -> tonnes per year
        # A furnace does not eat charcoal only while it is being built. It eats
        # charcoal every year it runs, forever. Omitting that was why forest
        # ownership never mattered in the model and always mattered in reality.
        for node_id in self.done_in_order():
            node = self.nodes[node_id]
            if node["up"] <= 0 or not node["mat"]:
                continue
            span = max(1.0, float(node.get("build_yrs") or node.get("yrs") or 1.0))
            coke = self.chosen_fuel(node_id) == "coke"
            for material, quantity in node["mat"].items():
                if coke and material in ("charcoal_kg", "firewood_kg"):
                    demand["coal_kg"] += (self.STANDING_MATERIAL_DRAW_SHARE * float(quantity)
                                           * self.COKE_PER_CHARCOAL / span / 1000.0)
                    continue
                demand[material] += self.STANDING_MATERIAL_DRAW_SHARE * float(quantity) / span / 1000.0
        return demand

    STANDING_MATERIAL_DRAW_SHARE = declare(
        "STANDING_MATERIAL_DRAW_SHARE", 0.5, kind="temporary_heuristic",
        unit="fraction of a node's build-time material draw rate, per year "
             "of standing operation", source=None, confidence="D",
        why="A finished, running installation - a furnace, a workshop - "
            "goes on consuming its listed material every year it operates, "
            "not only while being built (see the comment above: 'a furnace "
            "does not eat charcoal only while it is being built'). This is "
            "the ongoing rate as a fraction of the build-time rate, reused "
            "identically for electrical demand in _electricity_demand_kw() "
            "and _node_annual_tonnes() below. The DIRECTION is a real "
            "physical claim (standing operation consumes fuel/electricity "
            "continuously); the specific half-rate is an invented "
            "placeholder - a real figure needs a per-process duty cycle or "
            "throughput figure this tree does not carry.")

    # Which raw material keys (as they appear in a node's `mat` dict) draw on
    # which tracked commodity, and how "your own supply of it" is computed.
    # Factored out of resource_throttle so material_price_factor() below reads
    # the identical figures rather than a second guess at them.
    #
    # copper_wire_kg and wire_drawn_kg were UNTHROTTLED before this: 36 real
    # nodes (the whole el2_ electrical branch, plus gp_magnet_wire_enamelled,
    # hom_piano, en_rotary_converter...) drew drawn copper wire and none of it
    # ever competed with copper_kg for the same finite copper supply. This is
    # precisely the gap COMMODITIES.md section 7 names as "the real test":
    # wire is copper, drawn, and data/world/commodities.json's own
    # copper_wire recipe (a 5% drawing loss) already says so -- see
    # wire_chain_report() below, which asks that exact question against this
    # civilisation's real copper numbers via commodities.py's
    # propagate_demand(). gold_kg (fin_central_bank's 1000 kg, tx2_watch_case,
    # the gold-leaf electroscope) was also untracked despite Sim.open_mine
    # already supporting a gold mine (MINE_CAPEX_PER_T_YR) and
    # resources.json already carrying an empire gold figure (9 t/yr) --
    # nothing wired the two together. gold_g (LEDs, transistors: 1-20 grams)
    # is NOT added here, still: annual_material_demand() assumes every *_kg
    # key is kilograms, so a *_g key divided by 1000 would read as a
    # thousandth of what it is. That used to be "an error too small to
    # matter... but wrong in principle." It now matters: resource_throttle()
    # routes every *_g key through the LAB-SCALE stock path instead (see its
    # own comment and LAB_SCALE_SUFFIX below), which corrects the grams/
    # kilograms reading at the one place that was ever misreading it, rather
    # than by adding gold_g to this dict (that would make grams of gold
    # compete with fin_central_bank's tonnes for the same ANNUAL FLOW, which
    # is precisely the stock-vs-flow confusion this path exists to undo).
    MATERIAL_CHECKS = {
        "charcoal_kg": ("charcoal", "forest1"),
        "firewood_kg": ("charcoal", "forest4"),
        "iron_bar_kg": ("iron", "mine:iron"),
        "iron_ore_kg": ("iron", "mine:iron"),
        "coal_kg":     ("coal", "mine:coal"),
        "copper_kg":       ("copper", "mine:copper"),
        "copper_wire_kg":  ("copper", "mine:copper"),
        "wire_drawn_kg":   ("copper", "mine:copper"),
        "lead_kg":     ("lead", "mine:lead"),
        "tin_kg":      ("tin", "mine:tin"),
        "silver_kg":   ("silver", "mine:silver"),
        "gold_kg":     ("gold", "mine:gold"),
        "nitre_kg":    ("saltpetre", "nitre"),
    }

    FIREWOOD_PER_CHARCOAL_MASS_RATIO = declare(
        "FIREWOOD_PER_CHARCOAL_MASS_RATIO", 4.0, kind="engineering_estimate",
        unit="kg raw firewood per kg-equivalent of charcoal (dimensionless)",
        source="Traditional charcoal-burning loses most of the wood's mass "
               "as volatiles and water during carbonisation; a roughly "
               "four-to-one wood-to-charcoal mass ratio is the commonly "
               "cited order of magnitude for earth-kiln and pit methods.",
        confidence="C",
        why="A hectare of coppice yields several times more mass as raw, "
            "unconverted firewood (the 'forest4' tag, firewood_kg's supply) "
            "than it does as charcoal (the 'forest1' tag) from the SAME "
            "wood, because charcoal-making itself consumes most of the "
            "mass. This is the ratio between those two yields.")

    def _own_material_supply(self, tag):
        """Tonnes a year of a tracked commodity you supply yourself, not
        bought from anyone: mines you sank, woodland you bought, nitre beds
        you built. See MATERIAL_CHECKS for which tag means what."""
        if tag == "forest1":
            return self.household.forest_ha * self.CHARCOAL_PER_HA
        if tag == "forest4":
            return self.household.forest_ha * self.CHARCOAL_PER_HA * self.FIREWOOD_PER_CHARCOAL_MASS_RATIO
        if tag == "nitre":
            return self.household.nitre_bed_m2 * self.NITRE_YIELD_T_PER_M2
        if tag.startswith("mine:"):
            mat = tag[5:]
            # DEPLETION AND TECHNOLOGY, not the nominal tonnage you sank
            # capital into. mine_capacity is a historical record of what
            # you PAID for; what a working actually YIELDS this year is
            # that, discounted by how worked-out it is and multiplied by
            # whatever mining technology has done to counter that -- see
            # mine_depletion_factor() and mining_tech()'s own comments.
            yld, _cost = self.mining_tech(mat)
            return (self.mine_capacity.get(mat, 0.0)
                    * self.mine_depletion_factor(mat) * yld)
        return 0.0

    def _material_market_tonnes(self, emp_key):
        """Tonnes a year of `emp_key` the empire's market will sell you, at
        your current standing. The MARKET half of resource_throttle()'s
        `supply`; material_price_factor() reads it too.

        GENERALISED: resources.json's empire_output_100ad table and this
        file's own MARKET_SHARE only ever named a handful of materials by
        hand, so a material without an entry there used to answer 0 tonnes
        a year - not "unknown," an actual hard zero, which is why
        material_price_factor() had to bail out before ever reaching this
        function at all (see its own comment). A real figure, when one
        exists, is used unchanged; _generic_national_output_t_per_yr and
        _generic_market_share supply a reasoned default for everything
        else, so a material nobody named still has a market rather than
        not existing.
        """
        emp = self.res["empire_output_100ad"]
        entry = emp.get(emp_key)
        national = entry.get("t_per_yr", 0) if entry is not None else (
                   self._generic_national_output_t_per_yr(emp_key))
        share = self.MARKET_SHARE.get(emp_key)
        if share is None:
            share = self._generic_market_share(emp_key)
        # How much of a market you can command is a function of STANDING, not
        # just of money. A stranger buys at the margin; a man with senatorial
        # backing buys through their agents; a holder of imperial patronage
        # has the fiscus itself as a supplier, and the metalla were largely
        # imperial property. Charcoal is exempt because no amount of standing
        # makes a bulky crumbling fuel travel further than it can travel.
        if emp_key != "charcoal":
            if self.running("patron_imperial"):     share *= self.MARKET_STANDING_PATRON_IMPERIAL
            elif self.running("patron_senatorial"): share *= self.MARKET_STANDING_PATRON_SENATORIAL
            elif self.has("citizenship"):       share *= self.MARKET_STANDING_CITIZENSHIP
            share = min(share, self.MARKET_STANDING_SHARE_CEILING)
        # GEOLOGY, NOT DEMOGRAPHY. This used to be `* self.pop_scale`:
        # mineral availability scaled by population, so Norse Scandinavia
        # got 2.3% of Rome's coal because it has 2.3% of the people, and
        # England in 1300 got 7%, when England is precisely where the
        # coal actually is. A coalfield does not care how many people
        # live near it. mineral_scale() derives this instead from the
        # regions this civilization actually holds and can trade with
        # (see _compute_mineral_scale). Charcoal stays on pop_scale: it
        # is not mined, it is a local wood market, and THAT genuinely
        # does track how much local economic activity there is to buy
        # firewood from.
        scale = self.pop_scale if emp_key == "charcoal" else self.mineral_scale(emp_key)
        market = national * share * scale
        # Bengal saltpetre: an existing annual sea route, not a nitre bed.
        # This is the single most useful thing in the geography file.
        if emp_key == "saltpetre" and self.running("exp_trade_route_extend"):
            market += self.SALTPETRE_TRADE_ROUTE_TONNES_PER_YR
        return market

    MARKET_STANDING_PATRON_IMPERIAL = declare(
        "MARKET_STANDING_PATRON_IMPERIAL", 6.0, kind="temporary_heuristic",
        unit="multiple on buyable market share", source=None,
        confidence="D",
        why="How much further an imperial patron's standing opens the "
            "market for a tracked material, on the reasoning that the "
            "fiscus itself becomes a supplier and the metalla were largely "
            "imperial property. The direction is a real institutional "
            "fact; the sixfold size is tuned game balance, not derived "
            "from any attested imperial-supply share.")
    MARKET_STANDING_PATRON_SENATORIAL = declare(
        "MARKET_STANDING_PATRON_SENATORIAL", 2.5, kind="temporary_heuristic",
        unit="multiple on buyable market share", source=None,
        confidence="D",
        why="As MARKET_STANDING_PATRON_IMPERIAL, for a senatorial patron - "
            "buying through their agents rather than the fiscus itself. "
            "Tuned, not derived.")
    MARKET_STANDING_CITIZENSHIP = declare(
        "MARKET_STANDING_CITIZENSHIP", 1.4, kind="temporary_heuristic",
        unit="multiple on buyable market share", source=None,
        confidence="D",
        why="What plain citizenship, with no patron at all, is worth over "
            "a stranger buying at the margin. Tuned, not derived.")
    MARKET_STANDING_SHARE_CEILING = declare(
        "MARKET_STANDING_SHARE_CEILING", 0.60, kind="temporary_heuristic",
        unit="fraction of national output (maximum, any buyer)",
        source=None, confidence="D",
        why="However much standing multiplies a buyer's reach, nobody but "
            "the state itself commands the whole national market for a "
            "material - this caps even an imperial patron's buyer well "
            "short of monopolising it. The cap's own level is a plausible "
            "round number, not derived from an attested ceiling.")
    SALTPETRE_TRADE_ROUTE_TONNES_PER_YR = declare(
        "SALTPETRE_TRADE_ROUTE_TONNES_PER_YR", 60.0, kind="temporary_heuristic",
        unit="tonnes/year", source=
        "geography.json's Bengal saltpetre sea-route entry, reused here as "
        "'the single most useful thing in the geography file' per the "
        "comment above - the ROUTE'S existence is a geography fact, but "
        "this file has no independent attested annual tonnage for it.",
        confidence="D",
        why="How much extra saltpetre a year an extended trade route to "
            "Bengal makes available, on top of the ordinary market. The "
            "route is real; the specific tonnage is an invented, plausible "
            "figure standing in for an actual historical trade-volume "
            "record.")

    def _demand_by_supply_tag(self, demand):
        """Group MATERIAL_CHECKS demand by (emp_key, tag) -- i.e. by which
        SHARED supply it actually draws on -- instead of leaving it split by
        raw material key.

        Before this, resource_throttle() and material_price_factor() both
        checked each material key against the WHOLE of its supply
        independently: iron_bar_kg's need was compared to the full iron
        supply, then iron_ore_kg's need was compared to that SAME full
        supply again, as though each had it to itself. A plan needing 5 t/yr
        of ore and 4 t/yr of bar against a 6 t/yr supply passed both checks
        (neither 5 nor 4 alone exceeds 6) while actually needing 9 -- fifty
        per cent more than there is. Adding copper_wire_kg and wire_drawn_kg
        to MATERIAL_CHECKS without fixing this would have made it worse: a
        wire-heavy electrical age could show copper as fully supplied by
        three separate lies at once. Grouping by (emp_key, tag) sums every
        material key that draws on the SAME pool (iron_bar_kg + iron_ore_kg;
        now copper_kg + copper_wire_kg + wire_drawn_kg) while keeping
        charcoal_kg and firewood_kg separate, because they draw on the same
        forest at DIFFERENT yields per hectare (forest1 vs forest4, see
        _own_material_supply) and are not simply additive tonne-for-tonne.
        sorted(): a Counter keyed by tuples is still a dict, and the
        determinism convention here is to iterate sorted regardless of
        whether dict insertion order already happens to be safe, so a caller
        cannot inherit a bug by copying this pattern into a place where it
        is not.

        GENERALISED: this used to iterate MATERIAL_CHECKS's own 13 keys and
        look each one up in `demand`, so any OTHER key `demand` carried was
        silently never looked at - not grouped wrong, simply never
        consulted, which is the exact gap COMMODITY_DYNAMISM.md measured
        (149 of 162 material keys). annual_material_demand() was already
        generic over every material key a node's `mat` dict names; this now
        is too, routing each one through _material_tag (curated grouping
        where one exists, the material's own bare key otherwise) instead of
        only the hand-listed 13.
        """
        by_tag = collections.Counter()
        for mat, amt in sorted(demand.items()):
            if amt:
                by_tag[self._material_tag(mat)] += amt
        return by_tag

    # ---- stock vs flow -----------------------------------------------------
    #
    # A playtester who won the game put this more sharply than anything in
    # the design notes: "If I require 20 grams of gold for a device, creating
    # a tonne/year mining operation should obviously be ridiculous.
    # Realistically, I would just buy 20 grams. This argues strongly for
    # separating stock inventories from annual production capacity."
    #
    # Everything above this point (MATERIAL_CHECKS, _own_material_supply,
    # _material_market_tonnes) answers in TONNES PER YEAR, a flow, and
    # nothing anywhere carried a balance across years: a mine's surplus
    # output in excess of what that year's building programme used simply
    # evaporated rather than banking (the gap DOCS_VS_ENGINE.md ranked #3,
    # "nothing you produce outlives the year you produced it"). That is one
    # half of the fix - a running stock, in tonnes, that PRODUCTION and
    # MARKET PURCHASES feed and CONSUMPTION draws down, carried on the Sim
    # instance across the whole run (lazily, like _material_demand_cache
    # below it: MarketMixin does not own Sim.__init__).
    #
    # The other half is the playtester's actual complaint: a handful of
    # material keys in this tree are authored in GRAMS, not kilograms
    # (caesium_g, diamond_g, germanium_g, gold_g, indium_g,
    # phosphor_bronze_g, platinum_g - every *_g key in use, see
    # COMMODITY_DYNAMISM's audit), because whoever wrote chm_catalyst_concept
    # or point_contact_transistor meant a benchtop quantity, not a shipment.
    # No list of "laboratory materials" is hand-picked here - the *_kg/*_g
    # distinction is the tree's OWN, already-general convention for exactly
    # this (see the MATERIAL_CHECKS comment above), so it generalises the
    # same way _material_tag already does: any future node that needs a
    # gram-scale quantity of anything gets this for free by being written
    # with a *_g key, the same way it already gets priced by
    # _book_price_per_kg without anyone adding it to a list. A *_g key's
    # demand is met from stock - and, whatever stock cannot cover, bought
    # outright on the spot, uncapped by mine or market flow - and NEVER sets
    # `binding`: buying a gram of something is a purchase, not a capacity
    # call, so it is never the reason a year's work is throttled. A *_kg
    # key's demand is unchanged in kind: it still has to clear the same
    # flow check as before, just against a supply that now includes
    # whatever is banked in stock, not only this year's flow.
    LAB_SCALE_SUFFIX = "_g"

    def _material_stock(self):
        """Tonnes of each tracked commodity (by emp_key) carried over from
        previous years - the stock half of stock vs flow. Lazily created on
        first use and then kept for the life of the Sim: MarketMixin is a
        mixin, not __init__, and a fresh Counter is exactly what a household
        that has banked nothing yet should read as having. It is included in
        save_state()'s SAVE_FIELDS, so a resumed household retains the tonnes
        it actually produced or purchased.

        Deliberately a plain Counter, not commodities.py's own `Ledger`
        (also "a stock, not a flow," by its own docstring): Ledger works in
        kilograms and by commodity id, keyed for a module core.py still does
        not import; everything around resource_throttle() already works in
        TONNES and by emp_key, and the accounting below (own production vs
        market headroom, lab-scale vs industrial) needs that arithmetic
        inline, not behind add()/remove(). Reaching for Ledger here would
        buy a second unit system and a cross-module dependency, not a
        simpler mechanism - the "what was decided" COMMODITIES.md already
        documents for why commodities.py stays a library Sim calls into for
        specific answers (wire_chain_report's propagate_demand) rather than
        a second source of truth Sim's own state has to agree with."""
        stock = getattr(self.household, "_material_stock_ledger", None)
        if stock is None:
            stock = self.household._material_stock_ledger = collections.Counter()
        elif not isinstance(stock, collections.Counter):
            # A RESUMED SAVE HANDS THIS BACK AS A PLAIN DICT. It is in
            # SAVE_FIELDS so that a reloaded game is the same game - without it
            # a resume silently restarted at zero stock and played differently
            # from the run that was saved, the same class of fault as a fog
            # that could be rewound by reloading. JSON has no Counter, so
            # promote whatever came back before anything adds to it.
            stock = self.household._material_stock_ledger = collections.Counter(stock)
        return stock

    def material_stock_t(self, emp_key):
        """Tonnes of `emp_key` currently banked - the STOCK half of stock vs
        flow, which is the thing a player asking "how much iron do I actually
        own" wants. The `materials` command, trading actions, and resource
        throttle all read this same ledger.
        """
        return self._material_stock().get(emp_key, 0.0)

    MATERIAL_TRADE_SELL_SHARE_OF_BUY = declare(
        "MATERIAL_TRADE_SELL_SHARE_OF_BUY", 0.80, kind="temporary_heuristic",
        unit="fraction of the buy price (dimensionless)", source=None,
        confidence="D",
        why="The bid-ask spread on trading a raw material back to the "
            "market - a merchant's margin, real in kind (nobody buys and "
            "sells at the identical price) but not sized against any "
            "attested pre-industrial commodity spread.")

    def material_trade_quote(self, material):
        """Current buy/sell quote for one tonne of a material commodity."""
        material = str(material or "").strip().lower()
        per_kg = self._book_price_per_kg(material)
        if per_kg is None:
            return None
        buy = per_kg * 1000.0 * self.price_index * self.material_price_factor(material)
        return {"material": material, "buy_per_tonne": buy,
                "sell_per_tonne": buy * self.MATERIAL_TRADE_SELL_SHARE_OF_BUY,
                "market_available_tonnes_per_year": self._material_market_tonnes(material)}

    def buy_material_stock(self, material, tonnes):
        quote = self.material_trade_quote(material)
        tonnes = float(tonnes)
        if not quote or tonnes <= 0:
            return 0.0
        # The market figure is an annual flow ceiling, not an infinite shop.
        tonnes = min(tonnes, quote["market_available_tonnes_per_year"])
        cost = tonnes * quote["buy_per_tonne"]
        if tonnes <= 0 or cost > self.household.capital:
            return 0.0
        self.household.capital -= cost
        self._material_stock()[quote["material"]] += tonnes
        self.household._stock_throttle_sig = None
        return tonnes

    def sell_material_stock(self, material, tonnes):
        quote = self.material_trade_quote(material)
        tonnes = float(tonnes)
        if not quote or tonnes <= 0:
            return 0.0
        sold = min(tonnes, self.material_stock_t(quote["material"]))
        if sold <= 0:
            return 0.0
        self._material_stock()[quote["material"]] -= sold
        self.household.capital += sold * quote["sell_per_tonne"]
        self.household._stock_throttle_sig = None
        return sold

    def materials_report(self):
        """Stocks, annual flows, demand, and current trade values."""
        demand = self._demand_by_emp_key()
        materials = set(self._material_stock()) | {pair[0] for pair in self.MATERIAL_CHECKS.values()}
        materials |= {commodity for commodity in self.mine_capacity}
        rows = []
        for material in sorted(materials):
            quote = self.material_trade_quote(material)
            if not quote:
                continue
            annual_demand = sum(value for _tag, value in demand.get(material, ()))
            own = sum(self._own_material_supply(tag) for emp, tag in self._own_production_tags()
                      if emp == material)
            rows.append({**quote, "stock_on_hand_tonnes": self.material_stock_t(material),
                         "own_production_tonnes_per_year": own,
                         "current_demand_tonnes_per_year": annual_demand,
                         "stock_covers_years_at_current_demand": (
                             self.material_stock_t(material) / annual_demand
                             if annual_demand > 1e-9 else None)})
        return rows

    def _throttle_demand_split(self, demand):
        """`demand` (annual_material_demand()'s raw material-key Counter)
        split into two (emp_key, tag) -> tonnes/yr Counters: industrial
        (unchanged from before - still a flow demand that has to clear
        _own_material_supply + _material_market_tonnes, now plus stock) and
        lab (drawn from stock or bought outright, never throttled - see the
        class comment on LAB_SCALE_SUFFIX above).

        Deliberately NOT _demand_by_supply_tag(): that function is also read
        by material_price_factor() and everything built on it
        (material_market_factor, material_market_summary, wire_chain_report)
        for PRICING, which this pass does not touch - a gram of gold still
        nudges the price of gold exactly as much as it did before. Only the
        CAPACITY question (can this be done at all, or does it wait on a
        mine) changes here, so only resource_throttle() reads this. Fixes,
        in passing, the *_g unit bug the MATERIAL_CHECKS comment names:
        annual_material_demand() divides every raw key by 1000 assuming
        kilograms, which is correct for a *_kg key and 1000x too large for a
        *_g one (a bare quantity already in grams) - corrected here, once,
        at the one place that was ever misreading it.
        """
        industrial, lab = collections.Counter(), collections.Counter()
        for mat, amt in sorted(demand.items()):
            if not amt:
                continue
            tag = self._material_tag(mat)
            if mat.endswith(self.LAB_SCALE_SUFFIX) and not mat.endswith("_kg"):
                lab[tag] += amt / 1000.0
            else:
                industrial[tag] += amt
        return industrial, lab

    def _own_production_tags(self):
        """(emp_key, tag) for every material you currently produce yourself,
        whether or not anything is demanding it THIS year.

        Without this, a mine sunk ahead of need - dug this year for a
        furnace that starts next year - never appears in `industrial` or
        `lab` at all (both are built from DEMAND, and there is none yet),
        so resource_throttle()'s own loop never visits its tag and its
        output is never banked: the exact evaporation DOCS_VS_ENGINE.md's
        #3 describes, just the zero-demand edge of it rather than the
        partially-used one the main loop already banks correctly.
        `self.mine_capacity` is keyed by emp_key already (core.py's own
        auto-mine opens `self.household.binding`, which IS an emp_key - see
        MATERIAL_CHECKS), so "mine:" + that key is exactly the tag
        _own_material_supply already knows how to read, curated commodity
        or not."""
        out = {(material, "mine:" + material) for material, capacity in self.mine_capacity.items() if capacity > 0}
        if self.household.forest_ha > 0:
            out.add(("charcoal", "forest1"))
            out.add(("charcoal", "forest4"))
        if self.household.nitre_bed_m2 > 0:
            out.add(("saltpetre", "nitre"))
        return out

    # ---- electricity: a physical quantity, not a capability flag ----------
    #
    # THE GAP THIS CLOSES. cap_power_electric, cap_power_grid, cap_power_steam
    # and cap_power_water are capability nodes whose own NAMES narrate a scale
    # ("kW scale", "MW scale", "portable, hundreds of kW", "tens of kW on one
    # shaft" - see tech_tree.json) and nothing anywhere ever turned that prose
    # into a tracked watt. Two consequences, both real: a player who wanted a
    # generation/demand/reserve-margin display could not be given one (the
    # `capacity` command's power section said so outright), and - worse -
    # electrolytic aluminium, the electric arc furnace, zone refining and a
    # zinc smelter's own ancillary load all list `power_grid` in their `pre`
    # and are charged nothing whatsoever for the electricity that prerequisite
    # implies they need. The aluminium/rubber/etc. MATERIAL gating audit
    # (MATERIAL_GATING.md) closed exactly this shape of hole for MATERIALS
    # two days before this was written; this closes it for the one input
    # that check does not see, because a material key has always been
    # something `mat` can name and a watt never was.
    #
    # THE MODEL. Two sides, matched the way every other tracked commodity in
    # this file is: GENERATION (a rated kW contributed by every prime-mover
    # and generator node you have actually finished building - see
    # generation_breakdown_kw) and DEMAND (a kW drawn by every operating or
    # under-construction concern whose own prerequisite closure requires
    # cap_power_electric, cap_power_grid, or the literal power_grid node -
    # see _electricity_demand_kw). resource_throttle() below folds the two
    # together into the SAME worst-binding-constraint arithmetic iron and
    # copper already use, rather than inventing a second scarcity vocabulary:
    # electricity can become `self.household.binding`, appears in `self.household.shortages` the
    # same way "iron" or "saltpetre" already do, and reports itself through
    # the same `throttle_binding`/`why` machinery. It does NOT go through the
    # stock-banking half of that function (see the comment where it is
    # folded in, below) because a rated kilowatt is a RATE, not an inventory:
    # unlike a mine's unworked ore, a kilowatt of unused generating capacity
    # this year does not stockpile for next year, and unlike every other
    # tracked commodity, there is no market anywhere in this model that will
    # sell you a shortfall of electricity - you either generated it or you
    # did not.
    #
    # WHERE THE NUMBERS CAME FROM, AND WHERE THEY ARE A JUDGEMENT CALL.
    #
    # GENERATION: the tree's OWN cap_power_* names/notes state an order of
    # magnitude, never an exact figure - "tens of kW", "kW scale", "hundreds
    # of kW", "MW scale" (see POWER_ANCHOR_KW immediately below). Turning
    # "tens" into 30, "hundreds" into 300 and "MW scale" into 3,000 is a
    # judgement call, made explicitly here rather than smuggled into a bare
    # number with no comment: each is the geometric-ish midpoint of the
    # decade the tree's own prose names. cap_power_electric's "kW scale" is
    # deliberately smaller than cap_power_water's "tens of kW", not a
    # contradiction: cap_power_electric's own note is "one dynamo on the
    # millpond shaft you already built... enough for arc lights,
    # electroplating, a laboratory" - a small slice of an existing shaft's
    # mechanical output diverted through a dynamo, not the shaft's whole
    # output turned electrical. Every node in GENERATION_LOCAL_NODES/
    # GENERATION_GRID_NODES/TRANSMISSION_NODES/MECHANICAL_PRIME_MOVER_CHAINS
    # was found by grepping the whole tree for every node whose id, name or
    # `cat` names a prime mover or an electrical generator (water_prime,
    # steam_prime, electrical_gen, wind_prime, power_station, grid_operations,
    # plus the dynamo/alternator family by name) - a closed, enumerable set
    # today the way the 162 material keys MATERIAL_CHECKS started against
    # never was, so curating it by hand here costs the same one line per
    # future generation node that MATERIAL_CHECKS already costs per future
    # tracked commodity. Deliberately EXCLUDED from that set: dynamo/
    # alternator WINDING VARIANTS (el2_dynamo_series/shunt/compound_wound,
    # el2_alternator_rotating_field) and small auxiliary machines (en_exciter,
    # en_three_phase_gen, en_rotary_converter) - these refine or condition an
    # existing generator's output (regulation, phase, AC/DC conversion) and
    # do not represent a second, additional installation; counting them
    # would double the same generator's rating for every regulation upgrade
    # bought on top of it. Also excluded, for the mirror-image reason: the
    # water-wheel/turbine and steam-turbine FAMILIES are each a linear
    # upgrade chain at one site (undershot -> overshot -> breastshot ->
    # poncelet -> fourneyron -> francis -> kaplan; impulse -> curtis ->
    # reaction), not seven separate wheels - MECHANICAL_PRIME_MOVER_CHAINS
    # reports whichever is the BEST one you have finished, not their sum,
    # and (see generation_breakdown_kw's own note) is informational only:
    # it is not summed into electrical generation at all, because a bare
    # water wheel or steam turbine with no dynamo or alternator attached
    # turns nothing electrical, and that gate is already the existing `pre`
    # graph's job (dynamo's own prerequisites already include
    # water_power_scale; en_alternator's already include cap_power_steam).
    #
    # DEMAND: only two nodes get an individually-researched, real-world-cited
    # specific energy (ELECTRICAL_PROCESSES) - Hall-Heroult aluminium
    # electrolysis (13-17 kWh per kg of aluminium, historical/modern range;
    # applied to electrolysis_industrial's own bauxite_kg draw at a 4.5:1
    # bauxite-to-aluminium mass ratio, Bayer process) and a submerged-arc
    # ferroalloy/carbide furnace (several thousand kWh per tonne of product
    # is the real range; applied to arc_furnace_ferroalloys' own iron_ore_kg
    # draw at a simplifying 1:1 ore-to-product mass assumption, since the
    # tree carries no separate output-mass field for this node - flagged
    # here as the one approximation in this pair). Everything else this
    # file found gated on cap_power_electric/cap_power_grid/power_grid in
    # its own prerequisite closure (81 further nodes: workshop electronics,
    # vacuum-tube and radio equipment, welding, battery charging, the
    # semiconductor line itself, and zinc_industry_scale's own ancillary
    # load, whose actual smelting energy is charcoal/coal-fired per its own
    # note, not electrical - see GENERIC_ELECTRIC_LOAD_KW) gets ONE shared,
    # flat, modest figure rather than a hand-picked number apiece - the same
    # curate-the-important-cases-and-generalise-the-rest shape
    # _generic_market_share/_generic_national_output_t_per_yr already use
    # for materials, chosen so this file does not re-acquire the "13 hand-
    # named commodities out of 162" gap COMMODITY_DYNAMISM.md measured, in a
    # new unit.
    #
    # NOTES TOO VAGUE TO USE, NAMED HONESTLY: no node anywhere in the tree
    # carries a wattage or an output-mass figure for zone_refining, mfg_
    # anodising, met_electro_refining, or any of the mt2_*_electrolysis/
    # electrowinning nodes - their own `mat` dicts name reagents (graphite,
    # sulfuric acid, sulfur, lime) at bench-to-pilot quantities, not a
    # product mass a specific-energy figure could be applied to
    # defensibly. Each falls back to GENERIC_ELECTRIC_LOAD_KW rather than a
    # number invented to look more precise than the data supports.
    HOURS_PER_YEAR = declare(
        "HOURS_PER_YEAR", 8760.0, kind="physical_constant",
        unit="hours/year (365-day year)", source="365 days x 24 hours.",
        confidence="A",
        why="Converts an average continuous kilowatt draw into an annual "
            "energy total (and back), the same role HOURS_PER_DAY plays in "
            "sim/world/agriculture.py. Deliberately the plain 365-day "
            "figure, not 365.25: this file has no use for leap-year "
            "precision at kilowatt-scale estimates.")

    _POWER_ANCHOR_WHY = (
        "Turns the tech tree's own prose description of a generation "
        "node's scale ('tens of kW', 'kW scale', 'hundreds of kW', 'MW "
        "scale' - see tech_tree.json) into an actual kilowatt figure "
        "resource_throttle() can compare demand against. Each is the "
        "geometric-ish midpoint of the decade the tree's own note names - "
        "a judgement call made explicitly, per the class comment above, "
        "rather than a specific rated capacity for any specific machine.")
    POWER_ANCHOR_KW_WATER = declare(
        "POWER_ANCHOR_KW_WATER", 30.0, kind="temporary_heuristic",
        unit="kW", source="tech_tree.json note: 'tens of kW on one shaft'.",
        confidence="D", why=_POWER_ANCHOR_WHY)
    POWER_ANCHOR_KW_ELECTRIC = declare(
        "POWER_ANCHOR_KW_ELECTRIC", 10.0, kind="temporary_heuristic",
        unit="kW", source="tech_tree.json note: 'kW scale' - smaller "
               "than cap_power_water's own because this node is one "
               "dynamo diverting a slice of an existing shaft's output, "
               "not the shaft's whole output turned electrical (see "
               "the class comment above).",
        confidence="D", why=_POWER_ANCHOR_WHY)
    POWER_ANCHOR_KW_STEAM = declare(
        "POWER_ANCHOR_KW_STEAM", 300.0, kind="temporary_heuristic",
        unit="kW", source="tech_tree.json note: 'portable, hundreds of kW'.",
        confidence="D", why=_POWER_ANCHOR_WHY)
    POWER_ANCHOR_KW_GRID = declare(
        "POWER_ANCHOR_KW_GRID", 3000.0, kind="temporary_heuristic",
        unit="kW", source="tech_tree.json note: 'MW scale'.",
        confidence="D", why=_POWER_ANCHOR_WHY)
    POWER_ANCHOR_KW = {
        'cap_power_water': POWER_ANCHOR_KW_WATER,
        'cap_power_electric': POWER_ANCHOR_KW_ELECTRIC,
        'cap_power_steam': POWER_ANCHOR_KW_STEAM,
        'cap_power_grid': POWER_ANCHOR_KW_GRID,
    }

    # Standalone local generators: each an actual, distinct machine, so
    # multiple different ones (a dynamo AND a wind generator) add.
    GENERATION_LOCAL_NODES = {
        "dynamo": "cap_power_electric",
        "en_wind_electric": "cap_power_electric",
        "en_alternator": "cap_power_steam",
    }
    # Grid-scale generating STATIONS (power_station category) - distinct
    # from power_grid itself, which is transmission/distribution only (its
    # own `pre` is wires, substations, transformers and steel; no generator
    # anywhere in it - confirmed by reading it).
    GENERATION_GRID_NODES = {
        "en_hydroelectric_station": "cap_power_grid",
        "en_thermal_station": "cap_power_grid",
    }
    TRANSMISSION_NODES = {
        "power_grid": "cap_power_grid",
    }
    # Mechanical prime movers, informational only (see the class comment):
    # each list is one upgrade CHAIN at a single site, so only the best
    # member you have finished counts, never the sum of the chain.
    MECHANICAL_PRIME_MOVER_CHAINS = {
        "water": (("en_undershot_wheel", "en_overshot_wheel", "en_breastshot_wheel",
                   "en_poncelet_wheel", "en_fourneyron_turbine", "en_francis_turbine",
                   "en_kaplan_turbine", "en_pelton_wheel"), "cap_power_water"),
        "steam": (("en_steam_turbine_impulse", "en_steam_turbine_curtis",
                   "en_steam_turbine_reaction"), "cap_power_steam"),
    }

    def generation_breakdown_kw(self):
        """What this civilisation can actually generate and transmit, in
        real kilowatts, right now - local (workshop-scale) generation, grid-
        scale generating stations, grid transmission capacity, and the best
        mechanical prime mover on each site (informational; see the class
        comment above for why mechanical power is never summed into
        electrical generation directly). `total_kw` - local plus grid - is
        what resource_throttle() checks electrical demand against.
        """
        local_kw = sum(self.POWER_ANCHOR_KW[tier]
                       for nid, tier in sorted(self.GENERATION_LOCAL_NODES.items())
                       if nid in self.household.done)
        grid_kw = sum(self.POWER_ANCHOR_KW[tier]
                     for nid, tier in sorted(self.GENERATION_GRID_NODES.items())
                     if nid in self.household.done)
        transmission_kw = sum(self.POWER_ANCHOR_KW[tier]
                              for nid, tier in sorted(self.TRANSMISSION_NODES.items())
                              if nid in self.household.done)
        mechanical_kw = {}
        for fam, (chain, tier) in sorted(self.MECHANICAL_PRIME_MOVER_CHAINS.items()):
            mechanical_kw[fam] = (self.POWER_ANCHOR_KW[tier]
                                  if any(nid in self.household.done for nid in chain) else 0.0)
        return {
            "local_kw": local_kw,
            "grid_kw": grid_kw,
            "transmission_kw": transmission_kw,
            "mechanical_kw": mechanical_kw,
            "total_kw": local_kw + grid_kw,
        }

    def generation_capacity_kw(self):
        """The one number resource_throttle() needs: total_kw, cached."""
        return self.generation_breakdown_kw()["total_kw"]

    # Hall-Heroult aluminium electrolysis: 13-17 kWh/kg aluminium is the
    # historical-to-modern range; 15 (the midpoint) is used. Bayer process
    # bauxite yield is roughly 4-5 t bauxite per t aluminium (ore grade and
    # process losses vary); 4.5 (the midpoint) is used, so the constant
    # below is kWh per kg of BAUXITE (electrolysis_industrial's own `mat`
    # key), not per kg of aluminium the tree never states a mass for.
    ALUMINIUM_KWH_PER_KG = declare(
        "ALUMINIUM_KWH_PER_KG", 15.0, kind="engineering_estimate",
        unit="kWh/kg aluminium",
        source="Hall-Heroult aluminium electrolysis: 13-17 kWh/kg is the "
               "historical-to-modern range; taken at the midpoint.",
        confidence="B",
        why="Specific energy of electrolytic aluminium production, applied "
            "to electrolysis_industrial's own bauxite draw via "
            "BAUXITE_PER_ALUMINIUM_KG to give electrical demand per kg of "
            "bauxite, the tree's own material key for this node.")
    BAUXITE_PER_ALUMINIUM_KG = declare(
        "BAUXITE_PER_ALUMINIUM_KG", 4.5, kind="engineering_estimate",
        unit="kg bauxite per kg aluminium",
        source="Bayer process bauxite yield is roughly 4-5 t bauxite per t "
               "aluminium, varying with ore grade and process losses; "
               "taken at the midpoint.",
        confidence="B",
        why="Converts aluminium's own specific energy (ALUMINIUM_KWH_PER_KG) "
            "into energy per kg of BAUXITE, since electrolysis_industrial's "
            "own `mat` dict draws bauxite_kg, not an aluminium mass the "
            "tree never states.")
    # Submerged-arc ferroalloy/carbide furnaces: several thousand kWh per
    # tonne of product is the real range for this FAMILY of processes
    # (ferrosilicon, ferrochrome, calcium carbide - all listed in
    # arc_furnace_ferroalloys' own note) - far higher than plain scrap-steel
    # EAF remelting (a few hundred kWh/t), because this node is specifically
    # the carbide/ferroalloy family, not steel remelting. Applied to the
    # node's own iron_ore_kg draw at a simplifying 1:1 ore-to-product mass
    # assumption - the one approximation in this pair, disclosed because the
    # tree carries no separate output-mass field for this node.
    FERROALLOY_KWH_PER_KG_ORE = declare(
        "FERROALLOY_KWH_PER_KG_ORE", 5.0, kind="engineering_estimate",
        unit="kWh/kg ore (1:1 ore-to-product mass assumed)",
        source="Submerged-arc ferroalloy/carbide furnaces run several "
               "thousand kWh per tonne of product for this process FAMILY "
               "(ferrosilicon, ferrochrome, calcium carbide); several "
               "thousand kWh/t is roughly several kWh/kg.",
        confidence="C",
        why="Specific energy for arc_furnace_ferroalloys, applied to its "
            "own iron_ore_kg draw at a simplifying 1:1 ore-to-product mass "
            "assumption - the disclosed approximation in this pair, since "
            "the tree carries no separate output-mass field for this node.")
    # Anything else gated on cap_power_electric/cap_power_grid/power_grid
    # that this file cannot characterise individually - a modest generic
    # workshop load, the same order of magnitude as cap_power_electric's own
    # anchor and a full order of magnitude under the two curated heavy loads
    # above, so an uncharacterised node's demand is present but never
    # dominant.
    GENERIC_ELECTRIC_LOAD_KW = declare(
        "GENERIC_ELECTRIC_LOAD_KW", 15.0, kind="temporary_heuristic",
        unit="kW", source=None, confidence="D",
        why="Flat electrical demand assumed for any node gated on "
            "generated electricity that this file cannot characterise "
            "individually (see ELECTRICAL_PROCESSES for the two that are). "
            "Deliberately modest - the same order as cap_power_electric's "
            "own anchor, a full order of magnitude under the two curated "
            "heavy loads - so an uncharacterised node's demand is present "
            "but never dominant. Not measured for any specific process.")

    ELECTRICAL_PROCESSES = {
        "electrolysis_industrial": ("bauxite_kg",
                                    ALUMINIUM_KWH_PER_KG / BAUXITE_PER_ALUMINIUM_KG),
        "arc_furnace_ferroalloys": ("iron_ore_kg", FERROALLOY_KWH_PER_KG_ORE),
    }

    # cap_power_electric/cap_power_grid are the CAPABILITY flags; power_grid
    # is the literal transmission node some tier-5 process nodes name in
    # `pre` directly without ever naming the capability flag too (arc_
    # furnace_ferroalloys, zinc_industry_scale - see the class comment).
    # All three are treated as "this node needs generated electricity",
    # because that is what each one actually means physically, regardless
    # of which of the three a given node's author happened to write down.
    _ELECTRICITY_GATE_TOKENS = frozenset(
        {"cap_power_electric", "cap_power_grid", "power_grid"})

    def _electricity_load_node_ids(self):
        """Every node id whose own prerequisite closure needs generated
        electricity - computed once, from self.nodes (the static tree, not
        this run's state), and cached for the Sim's whole life; nothing
        here changes as a run progresses. A single memoised recursion over
        hard_pre(), not one closure() walk per candidate node: this file's
        own MATERIAL_GATING precedent (a cycle-safe visited-set walk of the
        whole tree once) is the reused shape, not the per-node closure()
        calls _power_status/_material_capacity_rows make elsewhere for a
        handful of rows at a time.
        """
        cached = getattr(self, "_electricity_load_ids_cache", None)
        if cached is not None:
            return cached
        tokens = self._ELECTRICITY_GATE_TOKENS
        memo = {}

        def gated(k, on_stack):
            if k in memo:
                return memo[k]
            if k in tokens:
                memo[k] = True
                return True
            if k in on_stack or k not in self.nodes:
                # Cycle guard: hard_pre's own single-option req_any edges are
                # acyclic tree-wide (see closure()'s own comment), but this
                # walk is defensive of that invariant rather than trusting
                # it silently - an unexpected cycle answers "not gated"
                # rather than recursing forever.
                return False
            on_stack.add(k)
            result = any(gated(parent_id, on_stack) for parent_id in hard_pre(self.nodes, k))
            on_stack.discard(k)
            memo[k] = result
            return result

        # UPKEEP IS NOT THE TEST OF WHETHER WORK DRAWS POWER. This required
        # up > 0 as a proxy for "a real installation rather than a technique",
        # which was reasonable on its own and wrong in combination with an
        # earlier decision: upkeep was deliberately stripped from 1,096
        # technique nodes, because a technique is not a going concern you
        # maintain. The two together hid 118 electricity-gated nodes that draw
        # material - MORE than the 111 that were kept - including
        # zone_refining, single_crystal and mfg_anodising, which are about as
        # electrical as this tree gets and sit squarely on the road to the
        # goal. A zone refiner melting a germanium boat by induction is
        # consuming kilowatts whether or not the tree charges it rent.
        #
        # The upkeep test survives where it is genuinely the right question -
        # see the caller, which applies it to the STANDING draw of something
        # already built and running. Work in hand draws power because the work
        # is happening, not because it pays rent.
        ids = {node_id for node_id, node in self.nodes.items()
              if node.get("mat") and gated(node_id, set())}
        self._electricity_load_ids_cache = ids
        return ids

    def _node_annual_tonnes(self, k, mat_key):
        """Tonnes/yr of mat_key ONE node draws, using the exact per-node
        annualisation annual_material_demand() applies when it sums this
        across every node in one pass - factored out so the curated
        electrical processes below can ask for a single node's own draw
        (electrolysis_industrial's bauxite, not the tree-wide bauxite total
        - iron_ore_kg in particular is drawn by many non-electrical nodes,
        and reusing the tree-wide total would attribute every blast furnace
        and forge's ore to arc_furnace_ferroalloys' electric arc)."""
        node = self.nodes.get(k)
        if node is None:
            return 0.0
        quantity = float((node.get("mat") or {}).get(mat_key, 0.0))
        if quantity <= 0:
            return 0.0
        span = max(1.0, float(node.get("build_yrs") or node.get("yrs") or 1.0))
        if k in self.household.active:
            return quantity / span / 1000.0
        if k in self.household.done and float(node.get("up") or 0) > 0:
            return self.STANDING_MATERIAL_DRAW_SHARE * quantity / span / 1000.0
        return 0.0

    def _electricity_demand_kw(self):
        """Average continuous kW drawn by work in hand - the electrical
        mirror of annual_material_demand(), in kilowatts instead of tonnes.
        `sorted()` throughout: this feeds a float sum, and set/dict
        iteration order is not guaranteed stable across PYTHONHASHSEED
        values (see this file's own determinism convention elsewhere)."""
        total = 0.0
        curated = self.ELECTRICAL_PROCESSES
        for node_id, (mat_key, kwh_per_kg) in sorted(curated.items()):
            t_per_yr = self._node_annual_tonnes(node_id, mat_key)
            if t_per_yr <= 0:
                continue
            total += (t_per_yr * 1000.0 * kwh_per_kg) / self.HOURS_PER_YEAR
        for node_id in sorted(self._electricity_load_node_ids() - set(curated)):
            node = self.nodes.get(node_id)
            if node is None:
                continue
            if node_id in self.household.active:
                total += self.GENERIC_ELECTRIC_LOAD_KW
            elif (node_id in self.household.done and float(node.get("up") or 0) > 0
                  and node_id in getattr(self.household, "operating", ())):
                # STANDING draw, where upkeep IS the right question: a thing
                # that costs nothing to keep is not an installation humming
                # away in the background, and one that is built but shut draws
                # nothing either.
                total += self.STANDING_MATERIAL_DRAW_SHARE * self.GENERIC_ELECTRIC_LOAD_KW
        return total

    RESOURCE_THROTTLE_FLOOR = declare(
        "RESOURCE_THROTTLE_FLOOR", 0.05, kind="temporary_heuristic",
        unit="fraction of full pace (minimum)", source=None,
        confidence="D",
        why="A material or electricity shortfall slows work rather than "
            "stopping it dead - a shortage is a real cost, not a wall a "
            "player cannot work around at all. The floor's own level (work "
            "always creeps forward at at least 5% pace) is a game-design "
            "choice, not derived from any real bound on how slow "
            "under-resourced work can go.")

    def resource_throttle(self):
        """How much of this year's planned work the materials will actually support.

        Charcoal is the one that bites, because it is not mined, it is GROWN.
        A hectare of coppice yields about 0.75 tonnes of charcoal a year, and a
        single blast furnace making 300 tonnes of iron eats 900 tonnes of it. If
        you have not bought the woodland, the furnace idles.
        """
        # CACHED for material_price_factor(). project_cost() now calls that
        # once for every candidate node `available` considers, every year,
        # for every active project, and annual_material_demand() is
        # O(active + done); recomputing it from scratch on every one of those
        # calls is the quadratic blowup this codebase already had to fix once
        # for done_in_order() (see its own comment). Good for one step(): a
        # query between steps reads the demand as of the last one, which is
        # already true of price_index, self.economy and self.household.throttle itself.
        self.household._material_demand_cache = self.annual_material_demand()
        industrial, lab = self._throttle_demand_split(self.household._material_demand_cache)
        stock = self._material_stock()
        # IDEMPOTENT WHEN NOTHING HAS ACTUALLY CHANGED. protocol.py's own
        # `why` handler calls this twice in a row to build one message
        # (s.binding, then s.resource_throttle() again for the percentage)
        # with nothing mutated in between - read-only from its point of
        # view, which it always was before this, because there was nothing
        # here a second call could consume. Now there is: the stock this
        # function draws down must be spent once per genuine recomputation,
        # not once per CALL, or a query asked twice double-depletes it and
        # answers its own two calls with two different numbers. Keyed on the
        # CONTENT that feeds the computation below, including the year. A new
        # year is a new production flow and must bank another year's unused
        # mine output; repeated queries within that year must not. A test,
        # or a player, building a mine or a nitre bed mid-year and asking
        # again in the SAME year must see the new answer immediately, not a
        # stale replay - see test_regressions.py's own
        # "...and stops once your own supply covers the need", which does
        # exactly that). Unchanged content means replaying the cached
        # (worst, who) is not a shortcut, it is the actual answer.
        # ELECTRICITY. Computed here, not inside the stock loop below (see
        # the class comment on _electricity_demand_kw/generation_breakdown_kw
        # for why it never touches `stock`), but its have/need both have to
        # be part of the signature: dynamo, en_alternator and the other
        # generation nodes all carry mat={} (a capability/machine node, not
        # a material purchase), so finishing one changes generation_capacity_
        # kw without changing `industrial`/`lab`/mine_capacity/forest_ha/
        # nitre_bed_m2/stock at all - the exact case the cache below would
        # otherwise silently replay a now-stale (worst, who) for.
        elec_need = self._electricity_demand_kw()
        elec_have = self.generation_capacity_kw()
        sig = (self.year, tuple(sorted(industrial.items())), tuple(sorted(lab.items())),
               tuple(sorted(self.mine_capacity.items())), self.household.forest_ha,
               self.household.nitre_bed_m2, tuple(sorted(stock.items())),
               elec_need, elec_have)
        if sig == getattr(self.household, "_stock_throttle_sig", None):
            self.household.throttle, self.household.binding = self.household._stock_throttle_cache
            return self.household.throttle
        worst, who = 1.0, None
        # RESOURCE_THROTTLE_FLOOR (declared below): work never fully stops
        # for a shortage - a shortfall slows a project instead of halting
        # it dead, so a bottleneck is a real cost rather than a stuck game.
        if elec_need > 1e-9 and elec_have < elec_need:
            fraction = max(self.RESOURCE_THROTTLE_FLOOR, elec_have / elec_need)
            if fraction < worst:
                worst, who = fraction, "electricity"
        all_tags = set(industrial) | set(lab) | self._own_production_tags()
        for emp_key, tag in sorted(all_tags):
            ind_need = industrial.get((emp_key, tag), 0.0)
            lab_need = lab.get((emp_key, tag), 0.0)
            # Two different things, kept separate on purpose: OWN_AND_STOCK
            # is physically yours - a bed you built, a mine you sank, a
            # surplus banked from an earlier year - and can BANK again if
            # unused this year. `market` is a standing offer (how much the
            # empire's market would sell you, not what you bought), and
            # choosing not to buy it this year does not make it yours to
            # keep: banking unused MARKET headroom as though it were
            # inventory was the bug this split exists to avoid (a material
            # with a large generic market figure and no demand for years
            # would otherwise accumulate thousands of tonnes nobody ever
            # produced or paid for).
            own_and_stock = stock.get(emp_key, 0.0) + self._own_material_supply(tag)
            have = own_and_stock + self._material_market_tonnes(emp_key)
            # Lab-scale first, and unconditionally: drawn from whatever is
            # banked or flowing in this year, topped up by a direct purchase
            # this function never checks capacity for - "I would just buy
            # 20 grams," exactly. It can never be what sets `worst`/`who`.
            lab_drawn = min(lab_need, have)
            have -= lab_drawn
            consumed_ind = 0.0
            if ind_need > 1e-12:
                if have < ind_need:
                    fraction = max(self.RESOURCE_THROTTLE_FLOOR, have / ind_need)
                    if fraction < worst:
                        worst, who = fraction, emp_key
                    consumed_ind = have
                else:
                    consumed_ind = ind_need
            # BANK THE REST OF WHAT WAS YOURS. Own production (and prior
            # stock) this year that neither draw actually touched goes back
            # into stock rather than evaporating - the other half of the fix
            # (DOCS_VS_ENGINE.md #3). Capped at own_and_stock, never at the
            # larger `have`, for exactly the reason in the comment above.
            stock[emp_key] = max(0.0, own_and_stock - lab_drawn - consumed_ind)
        self.household.throttle, self.household.binding = worst, who
        # Stored AFTER mutation, against stock as this call actually left
        # it - so an immediate repeat call's sig (computed from that same,
        # now-settled stock) matches and replays rather than spending again.
        self.household._stock_throttle_sig = (sig[0], sig[1], sig[2], sig[3], sig[4],
                                     sig[5], tuple(sorted(stock.items())),
                                     sig[7], sig[8])
        self.household._stock_throttle_cache = (worst, who)
        if who:
            self.household.shortages[who] += 1
        return worst

    def project_resource_throttle(self, k):
        """Material throttle applicable to one active project.

        ``resource_throttle`` still performs the portfolio-level supply and
        stock accounting and identifies the binding pool.  The resulting
        scarcity must only slow work that draws from that pool, however; paper
        research does not become short of saltpetre because a gunpowder project
        is.  Consumers of the scarce pool share its aggregate factor, while
        projects with no matching input retain their full labour pace.
        """
        factor = self.resource_throttle()
        binding = self.household.binding
        if factor >= 0.999 or not binding:
            return 1.0
        if binding == "electricity":
            return factor if k in self._electricity_load_node_ids() else 1.0
        node = self.nodes.get(k) or {}
        coke = self.chosen_fuel(k) == "coke"
        for mat in (node.get("mat") or {}):
            effective_mat = ("coal_kg" if coke
                             and mat in ("charcoal_kg", "firewood_kg") else mat)
            # Gram-scale purchases never participate in the flow throttle.
            if effective_mat.endswith(self.LAB_SCALE_SUFFIX) \
                    and not effective_mat.endswith("_kg"):
                continue
            if self._material_tag(effective_mat)[0] == binding:
                return factor
        return 1.0

    def _cached_material_demand(self):
        """annual_material_demand(), reusing resource_throttle()'s cache when
        there is one. See the comment there."""
        cached = getattr(self.household, "_material_demand_cache", None)
        return cached if cached is not None else self.annual_material_demand()

    def _cached_demand_by_tag(self):
        """_demand_by_supply_tag() of the current cached demand, computed
        once and reused for the rest of this tick.

        material_market_factor() now weighs EVERY material key a project
        buys (see its own comment on why it must, now that this is general
        rather than 13 hand-named keys), which means material_price_factor()
        can be called several times for one project_cost() call, and
        project_cost() itself is already called once per candidate node
        `available` considers, every year (see project_cost's own comment
        on why nothing here can afford to be quadratic). Grouping the
        demand dict is the one part of that path that is not already O(1),
        so it is done once per tick and kept, keyed by the demand dict's
        identity so a new tick (a new annual_material_demand() result)
        invalidates it automatically rather than by a second flag that
        could drift out of step with the first.

        THE CACHE ENTRY HOLDS `demand` ITSELF, NOT JUST `id(demand)` - the
        same defence `sim/engine/proto/nodes.py`'s own id()-keyed cache
        documents and takes, for the identical reason. `id()` is only
        unique among objects that are still alive: annual_material_demand()
        returns a brand-new Counter every call, the OLD one is dropped as
        soon as resource_throttle() overwrites self.household._material_demand_cache
        with the next year's, and CPython hands a freed small object's
        address to the very next same-sized allocation often enough that a
        later tick's Counter regularly landed at the exact address an
        earlier tick's had. `cached[0] == id(demand)` then read as true for
        two DIFFERENT ticks' demand, and this cache quietly replayed a
        stale grouping under a fresh year - the fourth `done_in_order()`-
        class bug (see that method's own docstring for the first three),
        found by bisecting `sim/repro_nondeterminism.py` back from a
        project's ph_left through project_cost() and material_market_factor()
        to material_price_factor() reading exactly this. Comparing `is
        demand` against a STRONG REFERENCE kept alongside the cached
        result, instead of comparing two bare integers, keeps that old
        Counter alive for as long as this cache entry might still be
        checked against it, so its address cannot be recycled into a false
        match while the entry is live - the collision is structurally
        impossible, not just unlikely, exactly as the nodes.py comment
        argues for the same shape of cache.
        """
        demand = self._cached_material_demand()
        cached = getattr(self.household, "_demand_by_tag_cache", None)
        if cached is not None and cached[0] is demand:
            return cached[1]
        by_tag = self._demand_by_supply_tag(demand)
        self.household._demand_by_tag_cache = (demand, by_tag)
        return by_tag

    # ---- freight: moving a material from where it comes from to you ------
    #
    # sim/world/transport.py derives what an ox team hauling a cart actually
    # costs per tonne-km from animal metabolism, rolling resistance and a
    # road surface - real physics, no price anywhere in it (see that
    # module's own NOT A MONEY FIGURE section for why). Until now nothing in
    # this engine ever called it: material_price_factor() below priced every
    # tracked material purely on SCARCITY (demand pressing on the empire's
    # market) and never asked how far the marginal tonne actually had to
    # travel to reach this household. CLAUDE.md SS3.1's own worked example -
    # a Roman soldier's cost must fall out of, among other things, transport,
    # not be looked up - is exactly this gap: Egypt's grain and Rome's grain
    # were the same book price here regardless of the thousand-odd
    # kilometres of open water between them.
    #
    # THE CROSSING. geography.json's own per-region `minerals` table (read
    # by mineral_scale()/_compute_mineral_scale() in geography.py to decide
    # how much of iron/coal/copper/lead/tin/silver/saltpetre you can BUY)
    # already says which of this game's 22 regions actually produce each of
    # those seven materials, with real latitude/longitude on every region.
    # This is the first place that same geography is also asked what buying
    # the material should COST: find the nearest region that has it, price
    # an ordinary ox-cart haul from there with transport.py's own per-
    # tonne-km figures, and fold the result into material_price_factor() as
    # a markup on the book price - see material_freight_factor()'s own
    # docstring for exactly why a markup, not an added denarii figure.
    #
    # WHY THIS MATERIAL SET AND NOT OTHERS. Extending this to gold, or to
    # commodities.json's own curated wool/cotton/coffee, was deliberately
    # left alone: geography.json's `minerals` table is the ONLY per-region
    # location data this engine carries at global (not just Roman-province)
    # coverage - commodities.json's "regions" field for those was written
    # Rome-centric (its `iron` entry alone lists only Roman provinces, none
    # of geography.json's other 16 regions, even though geography.json's own
    # `minerals` table credits China with more iron abundance than any
    # Roman province has) - using it for a non-Roman civilization would
    # invent a worse-than-nothing answer ("Han China must import all its
    # iron from across the world") from data that was never meant to
    # describe Han China at all. One clean, globally-consistent source beats
    # a wider crossing built on a source that only covers part of the map.
    #
    # WHAT THIS DELIBERATELY DOES NOT DO. It does not touch located_
    # materials (gutta percha, natural rubber, platinum) - geography.
    # material_cost_factor() already prices those from geography.json's own
    # reach-based multiplier (see project_cost()'s use of it above), and
    # that crossing is not flat or absent, only differently sourced (a
    # hand-set multiplier calibrated to Rome rather than transport.py's
    # physics); redoing it was out of this task's scope and out of
    # geography.py, which this file does not own. It does not model sea
    # freight at all, even though the whole reason this task exists is that
    # water is roughly an order of magnitude cheaper than land per tonne-
    # mile: transport.py has no seagoing-hull mode (its CALM_WATER surface
    # is an animal-towed canal or river barge, explicitly not a sailing
    # ship - see that module's own WHAT THIS MODULE DOES NOT DO), so a
    # region reachable only across open water is still charged the full
    # land-cart rate for the whole great-circle distance - a real
    # overstatement for a genuinely coastal shipment, and a named
    # limitation rather than a hidden one: inventing a sea-lane network and
    # a hull that does not exist in this project would be exactly the
    # "made-up distance... wearing a plausible face" CLAUDE.md SS3.1 warns
    # against. Left for the module that eventually gives transport.py a
    # real seagoing-hull mode. It also does not amortise the cart's own
    # capital cost or wear (transport.py's own vehicle_wear_fraction_per_
    # tonne_km) into the price: there is no market price for a cart
    # anywhere in prices.json to convert that fraction into denarii, so
    # this prices feed and driver time only, which UNDERSTATES the true
    # cost - a conservative simplification, named per CLAUDE.md SS3.4, not
    # a hidden one.

    LAND_FREIGHT_TEAM_SIZE = declare(
        "LAND_FREIGHT_TEAM_SIZE", 2.0, kind="engineering_estimate",
        unit="draught oxen",
        source="transport.py's own headline example throughout that "
               "module's docstring, __main__ block and test suite "
               "(draught_freight_physical_inputs(OX, 2, CART, ...)); reused "
               "here rather than a second, unrelated team size invented for "
               "this one crossing.",
        confidence="C",
        why="How many oxen pull the cart this crossing prices ordinary "
            "market freight with. Paired with DIRT_TRACK, not PAVED_ROAD or "
            "MUD, because transport.py's own docstring calls dirt track "
            "'the ordinary, unimproved-road case most freight in this "
            "period actually moved over' - the middle case, not either "
            "extreme.")

    # Which existing book price and wage this crossing reuses to turn
    # transport.py's physical quantities (feed kilograms, driver hours) into
    # denarii - see material_freight_cost_per_kg()'s own docstring for why
    # each was chosen and what it approximates. Plain strings, not declare()
    # (declare() is for numbers; these are which EXISTING number to read).
    FREIGHT_FEED_PRICE_MATERIAL = "wheat_kg"
    FREIGHT_DRIVER_WAGE_TRADE = "labourer"

    def _land_freight_physical_inputs(self):
        """Cached FreightPhysicalInputs for LAND_FREIGHT_TEAM_SIZE oxen
        pulling a two-wheeled cart on an ordinary dirt track - see the class
        comment above for why this specific team/vehicle/surface. Cached on
        the CLASS, the same pattern _material_prices() above already uses:
        none of animal, vehicle, surface or team size changes during a run,
        so there is nothing here to recompute per call."""
        cached = getattr(MarketMixin, "_land_freight_inputs_cache", None)
        if cached is None:
            cached = MarketMixin._land_freight_inputs_cache = (
                freight_physics.draught_freight_physical_inputs(
                    freight_physics.OX, int(self.LAND_FREIGHT_TEAM_SIZE),
                    freight_physics.CART, freight_physics.DIRT_TRACK))
        return cached

    def _material_source_regions(self, material):
        """Regions geography.json's own per-region `minerals` table credits
        with real abundance of `material` (iron, coal, copper, lead, tin,
        silver, saltpetre - mineral_scale()'s own tracked set; see
        geography.py's _compute_mineral_scale, which reads this exact same
        field for the QUANTITY question). Nothing here is invented for
        freight: it is the same geology this file already uses to decide
        how much of a material you can buy, now also asked what buying it
        should cost."""
        return [region_id for region_id, region in self._regions.items()
                if float((region.get("minerals") or {}).get(material, 0.0)) > 0.0]

    def material_freight_distance_km(self, material):
        """Great-circle kilometres from this civilization's own home
        centroid to the NEAREST region that actually produces `material` -
        the same "source from the easiest deposit, not a fixed one" logic
        material_reach() already uses for located materials, reused here
        rather than reinvented.

        Zero if any region this civilization already HOLDS produces the
        material at all: "home is home", exactly region_reach()'s own rule
        for a home region regardless of geometry, applied here to the same
        effect - a material you already mine somewhere in your own
        territory costs nothing extra to move WITHIN it, by this module's
        simplification.

        None if geography.json has no located-region data for `material` at
        all (everything outside the seven tracked minerals - see
        _material_source_regions). CLAUDE.md SS3.1 is explicit that an
        unknown distance is not licence to invent one, so this returns
        "unknown" rather than a guess, and material_freight_cost_per_kg()
        charges nothing rather than something imaginary when it sees that.

        Cached on the household: this civilization's geography does not
        change during a run, so the underlying haversine arithmetic only
        needs to happen once per material, not once per project per year -
        the same reasoning _material_stock()'s own lazy cache uses, next to
        it in this file."""
        cache = getattr(self.household, "_freight_distance_km_cache", None)
        if cache is None:
            cache = self.household._freight_distance_km_cache = {}
        if material in cache:
            return cache[material]
        regions = self._material_source_regions(material)
        if not regions:
            distance_km = None
        else:
            home_regions = set(self.civ.get("home_regions") or [])
            if home_regions & set(regions):
                distance_km = 0.0
            else:
                home_lat, home_lon = self._home_centroid
                distance_km = min(
                    haversine_km(home_lat, home_lon,
                                 self._regions[region_id]["lat"],
                                 self._regions[region_id]["lon"])
                    for region_id in regions)
        cache[material] = distance_km
        return distance_km

    def material_freight_cost_per_kg(self, material):
        """Denarii per kilogram to haul `material` from the nearest place it
        actually comes from to this household, by two-ox cart on an
        ordinary dirt track. Zero if material_freight_distance_km() cannot
        place the material at all, or places it at distance zero (already
        produced somewhere this civilization holds) - see that method's own
        docstring for both cases.

        THE MONEY CONVERSION transport.py deliberately leaves undone (see
        its own NOT A MONEY FIGURE section): feed_kg_per_tonne_km times a
        book price for animal feed, plus driver_hours_per_tonne_km times an
        unskilled wage, both read from this file's OWN existing book-price
        and wage tables rather than new ones invented for this crossing -
        the same numeraire (an hour of unskilled labour) sim/solve_prices.py
        already uses, per transport.py's own docstring pointing at it.

        FEED PRICE IS A LABELLED STAND-IN. transport.py's own FEED_ENERGY_
        DENSITY_KCAL_PER_KG declaration describes the ration it costs
        against as hay-heavy, and this project has no hay or fodder price
        anywhere in prices.json - FREIGHT_FEED_PRICE_MATERIAL (wheat_kg) is
        the closest book price that exists, and wheat is dearer per
        kilogram than real fodder, so this reads as a conservative
        (upper-bound), not measured, feed cost.

        VEHICLE WEAR/CAPITAL IS NOT INCLUDED. transport.py's own vehicle_
        wear_fraction_per_tonne_km has no market price to convert it into
        money - nothing in prices.json prices a cart - so this understates
        the true cost of the haul. Named here and in the class comment
        above, not hidden.
        """
        distance_km = self.material_freight_distance_km(material)
        if not distance_km:
            return 0.0
        inputs = self._land_freight_physical_inputs()
        feed_price_per_kg = self._book_price_per_kg(self.FREIGHT_FEED_PRICE_MATERIAL) or 0.0
        driver_wage_per_hour = WAGES.get(self.FREIGHT_DRIVER_WAGE_TRADE, 0.0)
        denarii_per_tonne_km = (inputs.feed_kg_per_tonne_km * feed_price_per_kg
                                 + inputs.driver_hours_per_tonne_km * driver_wage_per_hour)
        denarii_per_tonne = denarii_per_tonne_km * distance_km
        return denarii_per_tonne / 1000.0

    def material_freight_factor(self, emp_key):
        """Multiplicative markup material_price_factor() applies on top of
        its scarcity curve, from what transport.py's freight physics say it
        costs to haul `emp_key` here - see material_freight_cost_per_kg()'s
        own docstring for the mechanism, and material_freight_distance_km()'s
        for why an unlocated material gets exactly 1.0, never a guess.

        A MARKUP ON THE BOOK PRICE (1.0 + freight / book_price), not a
        standalone added charge, because a markup is what project_cost()
        and material_trade_quote() both actually multiply against: node
        `_total_cost` and a material's per_kg are already the RAW book
        value, and every other adjustment this file stacks onto that value
        (civ_cost_factor(), material_cost_factor(), this function's own
        scarcity curve) is exactly this shape - a factor, not an addend -
        so freight has to enter the same way to compose correctly rather
        than silently double- or under-counting when several of these
        multiply together in project_cost().
        """
        book_price_per_kg = self._book_price_per_kg(emp_key)
        if not book_price_per_kg or book_price_per_kg <= 0:
            return 1.0
        freight_per_kg = self.material_freight_cost_per_kg(emp_key)
        if freight_per_kg <= 0:
            return 1.0
        return 1.0 + freight_per_kg / book_price_per_kg

    def material_price_factor(self, emp_key):
        """What buying MORE of this tracked commodity costs beyond the flat
        catalogue price, from how hard current demand leans on the empire's
        market for it, versus how much of your own supply makes that market
        unnecessary, TIMES what transport.py's freight physics say it costs
        to haul it here from the nearest place it actually comes from (see
        material_freight_factor() above - 1.0, no change, for a material
        this civilization already produces somewhere in its own territory,
        or that geography.json has no location data for at all).

        FINDINGS_ROUND2 section R: MARKET_SHARE was a supply ceiling with no
        price response at all -- buying up to it cost the same per tonne as
        buying one kilogram -- and nothing made owning your own supply make
        the material CHEAPER, only available. Both halves are here: `need`
        and `_material_market_tonnes(emp_key)` are resource_throttle()'s own
        figures, so demand approaching the market ceiling raises the price on
        the same saturating curve labour_price_factor uses (negligible at a
        fifth of the ceiling, roughly double at the whole of it); owning
        enough of your own extraction (mine_capacity, forest_ha,
        nitre_bed_m2) to cover the need removes the premium rather than
        merely making the tonnes exist. This is the actual mechanism behind
        "the price of iron fell because supply rose": opening a mine lowers
        what iron costs YOU, specifically because you stop having to buy it
        at the margin.

        Groups demand the same way resource_throttle() now does
        (_demand_by_supply_tag): the same "checked each key alone" gap
        applied here too, understating the price pressure of a wire-heavy
        electrical age on copper by looking at copper_kg's share in
        isolation from copper_wire_kg's.

        GENERALISED: this used to return exactly 1.0, immediately, for any
        commodity id not already sitting in the hand-written MARKET_SHARE
        dict above - the actual mechanism by which COMMODITY_DYNAMISM.md's
        149 inert material keys never moved at all ("the function's own
        code explains why... it returns 1.0 immediately"). That early
        return is gone: `market` now falls back through
        _material_market_tonnes' own generic default, so an arbitrary
        commodity id (curated or not) reaches the same saturating curve
        the 9 originally-tracked ones always used.
        """
        market = self._material_market_tonnes(emp_key)
        worst = 1.0
        # GROUPED BY emp_key, ONCE A TICK, not scanned-and-filtered from the
        # whole by-tag dict on every one of THIS function's own calls. See
        # _demand_by_emp_key's comment: this is the same "called once per
        # material a project buys, once per candidate node, every year"
        # volume _cached_demand_by_tag() was already added to answer, one
        # level further in. Only max() is taken below, order-independent,
        # so - as with _cached_demand_by_tag's own dict - no sort is needed
        # for the result to be deterministic.
        for tag, need in self._demand_by_emp_key().get(emp_key, ()):
            if need <= 0:
                continue
            supply = max(1e-9, self._own_material_supply(tag) + market)
            share = min(self.MATERIAL_PRICE_DEMAND_SHARE_CAP, need / supply)
            worst = max(worst, 1.0 + self.MATERIAL_PRICE_PRESSURE_SCALE * share * share)
        return worst * self.material_freight_factor(emp_key)

    MATERIAL_PRICE_DEMAND_SHARE_CAP = declare(
        "MATERIAL_PRICE_DEMAND_SHARE_CAP", 1.5, kind="temporary_heuristic",
        unit="dimensionless (demand / available supply, maximum)",
        source=None, confidence="D",
        why="Ceiling on how far demand-over-supply can push the price "
            "pressure curve below, so a wildly oversubscribed material "
            "does not blow the price multiplier up without bound. A "
            "defensive cap, not a market-clearing figure.")
    MATERIAL_PRICE_PRESSURE_SCALE = declare(
        "MATERIAL_PRICE_PRESSURE_SCALE", 0.9, kind="temporary_heuristic",
        unit="dimensionless coefficient on (demand share)^2", source=None,
        confidence="D",
        why="How hard buying near or above the market's available supply "
            "of a material pushes its price up - a quadratic curve, per "
            "this method's own docstring, 'negligible at a fifth of the "
            "ceiling, roughly double at the whole of it'. The quadratic "
            "SHAPE is a real modelling choice (price pressure should "
            "accelerate near scarcity); the coefficient is tuned to hit "
            "that 'roughly double' target, not derived from an observed "
            "price-response curve for any real material market.")

    def _demand_by_emp_key(self):
        """_cached_demand_by_tag(), grouped by emp_key - the grouping
        material_price_factor() actually wants. Cached the same tick-
        scoped way _cached_demand_by_tag() itself is, INCLUDING keeping a
        strong reference to `demand` in the cache entry rather than
        comparing bare `id()` integers - see that method's own comment for
        why a bare id() is not safe here (a freed Counter's address gets
        reused often enough that two different ticks compared equal by
        allocator luck alone, which is what made this pair of caches the
        fourth `done_in_order()`-class non-determinism bug, not a
        hypothetical one). A new tick produces a new annual_material_demand()
        result, which invalidates both caches together automatically."""
        demand = self._cached_material_demand()
        cached = getattr(self.household, "_demand_by_emp_key_cache", None)
        if cached is not None and cached[0] is demand:
            return cached[1]
        grouped = {}
        for (emp_key, tag), need in self._cached_demand_by_tag().items():
            grouped.setdefault(emp_key, []).append((tag, need))
        self.household._demand_by_emp_key_cache = (demand, grouped)
        return grouped

    def material_market_factor(self, k):
        """A project's price pressure from the materials it buys, weighted
        by how many kilograms of each -- the same weighting `_material_cost`
        already uses implicitly by summing kilogram costs.

        GENERALISED: every material key a node names now gets weighed in,
        not only the 13 MATERIAL_CHECKS ever listed by hand. Before this,
        a project buying nothing but glass, silk or aluminium got exactly
        1.0 back - not a small effect, no effect, because the `continue`
        below skipped every one of them (see COMMODITY_DYNAMISM.md: "it
        simply skips any material key not in MATERIAL_CHECKS"). Skipping
        was correct only in the sense that this file could not yet answer
        a price for those materials; now it can (_material_tag /
        material_price_factor's own generalisation), so it does.
        """
        mat = self.nodes[k].get("mat") or {}
        if not mat:
            return 1.0
        total_kg, weighted = 0.0, 0.0
        for material, quantity in sorted(mat.items()):
            emp_key = self._material_tag(material)[0]
            quantity = float(quantity)
            total_kg += quantity
            weighted += quantity * self.material_price_factor(emp_key)
        return (weighted / total_kg) if total_kg else 1.0

    def material_market_summary(self):
        """Every raw material currently carrying a real price premium
        because your own demand is leaning on what the market will sell -
        the generalised, aggregate version of material_price_factor(), the
        way goods_market_summary() already is for goods_market_factor().

        A PLAYER MUST SEE IT. Before this pass a material's price response
        was invisible even for the 9 tracked commodities (nothing
        aggregated it for `money`) and non-existent for the other 149; now
        that every material key responds (see material_price_factor's own
        comment), a player whose project costs rose because they are
        buying a lot of one thing, or fell because they sank their own
        mine in it, needs a place that says so in aggregate, not just a
        per-project `why`.
        """
        demand = self._cached_material_demand()
        if not demand:
            return None
        rows, seen = [], set()
        for mat in sorted(demand):
            if demand[mat] <= 0:
                continue
            emp_key = self._material_tag(mat)[0]
            if emp_key in seen:
                continue
            seen.add(emp_key)
            factor = self.material_price_factor(emp_key)
            if factor > 1.05:
                rows.append((emp_key, factor))
        if not rows:
            return None
        rows.sort(key=lambda kv: -kv[1])
        worst = rows[0]
        return ("%d material%s trading above book price because your own "
                "demand is leaning on what the market will sell: worst is "
                "%s at %d%% of book. Sinking your own mine or production "
                "capacity in it brings this back down, the same way it "
                "does for iron - 'quote mine %s' shows the price"
                % (len(rows), "" if len(rows) == 1 else "s",
                   worst[0], round(worst[1] * 100), worst[0]))

    def wire_chain_report(self, wire_t_per_yr):
        """Would THIS shortfall in copper wire actually be a copper shortage,
        or is the wire-drawing bench itself the bottleneck? Named against a
        real link in the tree (el2_three_wire_distribution_system alone
        wants 5 t of copper_wire_kg in one build; the whole electrical
        branch wants far more), because resource_throttle()'s `binding` can
        only ever say "copper" -- it has no notion that copper_wire_kg is
        COPPER, manufactured, not a second independent shortage.

        This is `commodities.py`'s `CommodityLedger.propagate_demand()`
        (COMMODITIES.md section 7, "the real test": a chained shortage
        attributed to whichever link actually broke), handed THIS
        civilisation's actual reachable copper -- resource_throttle()'s own
        `_own_material_supply("mine:copper") + _material_market_tonnes
        ("copper")` -- via `supply_override`, instead of
        commodities.json's own separate national estimate. The two
        happen to agree for Rome (both read from the same
        resources.json/economy.py MARKET_SHARE figures) but would not for a
        civilization with a different mineral_scale, which is exactly why
        overriding with the live number rather than trusting the static one
        matters.
        """
        supply_t = (self._own_material_supply("mine:copper")
                    + self._material_market_tonnes("copper"))
        ledger = _commod.CommodityLedger(supply_override={"copper": supply_t})
        return ledger.propagate_demand("copper_wire", max(0.0, float(wire_t_per_yr)))

    # Two denarii the square metre, which is the figure step() has always used
    # (spend / 2.0) written down where a quote can read it. A nitre bed is a
    # heap of dung, straw and ash turned for two years; it is cheap to lay and
    # slow to yield, which is exactly why nobody builds one until they are
    # already short.
    NITRE_COST_PER_M2 = declare(
        "NITRE_COST_PER_M2", 2.0, kind="temporary_heuristic",
        unit="denarii/square metre", source=
        "The figure step() used before this was given a proper `quote` "
        "path (spend / 2.0), carried forward unchanged so buying a bed the "
        "new way costs exactly what the old automatic policy always paid.",
        confidence="D",
        why="Cost to lay one square metre of nitre bed. Not sourced to any "
            "attested saltpetre-works price; a carried-forward implementation "
            "constant.")
    NITRE_YIELD_T_PER_M2 = declare(
        "NITRE_YIELD_T_PER_M2", 0.0008, kind="temporary_heuristic",
        unit="tonnes saltpetre/square metre/year", source=None,
        confidence="D",
        why="How much saltpetre one square metre of nitre bed yields a "
            "year. No attested nitre-bed yield figure backs this; it is "
            "sized only to be 'cheap to lay and slow to yield' (see the "
            "comment above), a qualitative target rather than a measured "
            "rate.")

    def build_nitre(self, m2):
        """Lay down nitre beds. Saltpetre is not dug and not grown; it is made.

        There was no way for a player to do this at all. The only thing that
        laid a bed was step(), which took five per cent of your capital every
        year you were short, said nothing, and did it whether or not you had
        turned the automatic policies off. A shortage the game will not let you
        act on is not a constraint, it is a wall.
        """
        m2 = float(m2)
        if m2 <= 0:
            return 0.0
        cost = m2 * self.NITRE_COST_PER_M2 * self.price_index
        if cost > self.household.capital:
            return 0.0
        self.household.capital -= cost
        self.household.nitre_bed_m2 += m2
        return m2

    NITRE_SHORTAGE_SAFETY_BUFFER = declare(
        "NITRE_SHORTAGE_SAFETY_BUFFER", 1.20, kind="temporary_heuristic",
        unit="multiple on the bare tonnage deficit", source=None,
        confidence="D",
        why="Extra bed recommended over the bare measured deficit, so a "
            "tiny later change in the portfolio does not put the player "
            "straight back into shortage. Twenty per cent is a round, "
            "plausible safety margin, not derived from how much the "
            "portfolio typically moves.")

    def shortage_remedy(self, binding):
        """One sentence on what would end this shortage, in things you can type.

        The throttle message used to name the material and the percentage and
        stop, which tells a player they are stuck without telling them it is
        fixable. Every binding constraint in the model has exactly one answer;
        this is that answer, said out loud.
        """
        if not binding:
            return ""
        if binding == "charcoal":
            need = max(0.0, self.annual_material_demand().get("charcoal_kg", 0.0)
                       / 1000.0 - self.household.forest_ha * self.CHARCOAL_PER_HA)
            hectares_needed = max(1.0, round(need / max(self.CHARCOAL_PER_HA, 1e-9)))
            return ("Charcoal is grown, not bought: about %s more hectare%s of "
                    "coppice would cover it ('buy forest %d', roughly %s "
                    "denarii). Ask the price first with 'quote forest %d'."
                    % ("{:,.0f}".format(hectares_needed), "" if hectares_needed == 1 else "s", hectares_needed,
                       "{:,.0f}".format(hectares_needed * self.FOREST_COST_PER_HA * self.price_index),
                       hectares_needed))
        if binding == "saltpetre":
            demand = self.annual_material_demand().get("saltpetre_kg", 0.0) / 1000.0
            available = (self.household.nitre_bed_m2 * self.NITRE_YIELD_T_PER_M2
                         + self._material_market_tonnes("saltpetre")
                         + self._material_stock().get("saltpetre", 0.0))
            deficit = max(0.0, demand - available)
            # Twenty per cent headroom prevents a tiny change in the portfolio
            # putting the player straight back into shortage, without turning a
            # one-tonne deficit into the old fixed sixteen-tonne recommendation.
            square_meters = max(100, int(math.ceil(
                deficit * self.NITRE_SHORTAGE_SAFETY_BUFFER
                / max(self.NITRE_YIELD_T_PER_M2, 1e-12) / 100.0)) * 100)
            return ("Saltpetre is made in nitre beds, not mined: you are about "
                    "%.2f tonnes/year short. With a 20%% safety buffer, 'buy "
                    "nitre %d' lays enough bed at %.4f tonnes per square metre "
                    "per year (about %s denarii)."
                    % (deficit, square_meters, self.NITRE_YIELD_T_PER_M2,
                       "{:,.0f}".format(square_meters * self.NITRE_COST_PER_M2
                                       * self.price_index)))
        if binding in self.MINE_CAPEX_PER_T_YR:
            dem = self.annual_material_demand()
            # SAME GROUPING resource_throttle() uses (_demand_by_supply_tag):
            # copper's shortfall can now come from copper_wire_kg or
            # wire_drawn_kg as much as from copper_kg itself (36 electrical
            # nodes draw drawn wire), and this sentence would otherwise name
            # a "you are X tonnes short" figure that silently excluded them.
            keys = {"coal": ("coal_kg",), "iron": ("iron_bar_kg", "iron_ore_kg"),
                    "copper": ("copper_kg", "copper_wire_kg", "wire_drawn_kg"),
                    "lead": ("lead_kg",), "tin": ("tin_kg",),
                    "silver": ("silver_kg",),
                    "gold": ("gold_kg",)}.get(binding, ())
            short = max(0.0, sum(dem.get(material_key, 0.0) for material_key in keys)
                        - self.mine_capacity.get(binding, 0.0))
            tonnes_short = max(1.0, round(short))
            return ("The market will not sell you enough %s, so you have to dig "
                    "it: %s. 'quote mine %s %d' for the price, then 'buy mine "
                    "%s %d'. A shaft takes a few years to come into production."
                    % (binding,
                       ("you are about %s tonnes a year short"
                        % "{:,.0f}".format(short)) if short >= 1.0
                       else "your own workings already cover the demand you have "
                            "today, so this is the market, not you",
                       binding, tonnes_short, binding, tonnes_short))
        return ("Nothing you own supplies %s and the market is out of it; the "
                "work waits until something upstream of it is built."
                % binding)
