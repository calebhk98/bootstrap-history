"""The declared numbers of the polity module: how a society notices, protects, taxes and presses a household.

Priced-in-labour-hours figures are declared here as hours; the module reads them as money through `Polity.priced`."""
from sim.constants import declare

STATE_INTEREST_RELIGIOUS_ADJACENT_WEIGHT = declare(
    "STATE_INTEREST_RELIGIOUS_ADJACENT_WEIGHT", -0.9, kind="temporary_heuristic",
    unit="dimensionless (multiplies w_religious_rigidity)", source=None,
    confidence="D",
    why="How much a religiously rigid society's OWN interest in a technology "
        "is suppressed by that technology being religious_adjacent - "
        "negative because rigidity chills state interest in it rather than "
        "raising it, near but not equal to a full -1.0 offset. No source "
        "ties this specific fraction to any state's actual interest in "
        "religious matters; a real figure needs a model of how a state's "
        "own priorities are formed, not a hand-picked weight per trait.")
ALARM_WEIGHT_INEXPLICABLE = declare(
    "ALARM_WEIGHT_INEXPLICABLE", 10.0, kind="temporary_heuristic",
    unit="alarm points (multiplies w_magic_fear)", source=None,
    confidence="D",
    why="How alarming an effect a society has no category for is, before "
        "any defence - the largest of the per-trait weights here because "
        "alarm_of's own docstring says this is the thing that matters, not "
        "speed or money. No source measures a society's fright at an "
        "unexplained effect in these units; a real mechanism would derive "
        "alarm from what a specific society's own epistemic categories can "
        "and cannot explain, not from a fixed per-trait table.")
ALARM_WEIGHT_SPECTACLE = declare(
    "ALARM_WEIGHT_SPECTACLE", 4.0, kind="temporary_heuristic",
    unit="alarm points (multiplies w_magic_fear)", source=None,
    confidence="D",
    why="A visible spectacle alarms a magic-fearing society less than "
        "something truly inexplicable does - it is still explained by "
        "showmanship - so this sits at a fixed fraction of "
        "ALARM_WEIGHT_INEXPLICABLE. Tuned to feel proportionate, not "
        "derived from any source.")
ALARM_WEIGHT_RELIGIOUS_ADJACENT = declare(
    "ALARM_WEIGHT_RELIGIOUS_ADJACENT", 9.0, kind="temporary_heuristic",
    unit="alarm points (multiplies w_religious_rigidity)", source=None,
    confidence="D",
    why="How alarming a religious authority finds a religiously-adjacent "
        "effect, in the same invented units as every other weight in this "
        "table. No source; a real figure needs a model of a specific "
        "religious institution's own doctrine and its actual reaction to a "
        "specific claim, not one number for the whole category.")
ALARM_WEIGHT_STATUS_THREATENING = declare(
    "ALARM_WEIGHT_STATUS_THREATENING", 5.0, kind="temporary_heuristic",
    unit="alarm points", source=None, confidence="D",
    why="How alarming a technology that threatens the standing of an "
        "existing elite is, flat regardless of the society's own weights - "
        "unlike the other terms here, this one carries no `weights[...]` "
        "multiplier at all, which is itself an unexamined choice. Tuned "
        "game balance, not a measured social reaction.")
ALARM_WEIGHT_WEAPON_DEMOCRATISING = declare(
    "ALARM_WEIGHT_WEAPON_DEMOCRATISING", 6.0, kind="temporary_heuristic",
    unit="alarm points", source=None, confidence="D",
    why="How alarming a weapon that lets ordinary people fight on equal "
        "terms with an elite is, also flat regardless of the society's own "
        "weights - see military_leverage()'s own docstring for the other "
        "half of what this trait does. Invented game balance.")
ALARM_WEIGHT_LABOUR_SAVING = declare(
    "ALARM_WEIGHT_LABOUR_SAVING", 4.0, kind="temporary_heuristic",
    unit="alarm points (multiplies max(0, -w_labour_saving))", source=None,
    confidence="D",
    why="How alarming a labour-saving technology is to a society that "
        "specifically fears labour displacement (negative w_labour_saving) "
        "- zero for a society that does not. Tuned to sit alongside the "
        "other per-trait weights above, not measured.")
ALARM_FAMILIARITY_FLOOR = declare(
    "ALARM_FAMILIARITY_FLOOR", 0.12, kind="temporary_heuristic",
    unit="dimensionless (floor on 1 - familiarity)", source=None,
    confidence="D",
    why="However habituated a society becomes to the founder, alarm never "
        "falls below this floor - a full stranger is not read the same as "
        "a lifelong native however long the founder has been visible. "
        "Chosen so familiarity remains a strong, not total, defence; not "
        "derived from any measured habituation curve.")
ALARM_PROTECTION_FLOOR = declare(
    "ALARM_PROTECTION_FLOOR", 0.15, kind="temporary_heuristic",
    unit="dimensionless (floor on 1 - protection)", source=None,
    confidence="D",
    why="However protected the founder is by patrons, office and money, "
        "alarm never falls below this floor - protection can blunt "
        "suspicion, never erase it outright. Chosen for the same reason as "
        "ALARM_FAMILIARITY_FLOOR; not measured.")
MILITARY_LEVERAGE_SATURATES_AT = declare(
    "MILITARY_LEVERAGE_SATURATES_AT", 25.0, kind="temporary_heuristic",
    unit="founder-built military-branch nodes", source=None,
    confidence="D",
    why="How many founder-built military nodes reach full military "
        "leverage (1.0) - a little over a fifth of the tree's 111+ "
        "military branch, chosen (see this method's own docstring) so "
        "leverage cannot be maxed by a token gesture nor by treating "
        "the whole military branch as a strategy unto itself. Not "
        "measured against any historical count of decisive weapons.")
MILITARY_EQUIPMENT_ERA_CAMPAIGN_TEMPO_ENGAGEMENTS_PER_YEAR = declare(
    "MILITARY_EQUIPMENT_ERA_CAMPAIGN_TEMPO_ENGAGEMENTS_PER_YEAR", 6.0,
    kind="temporary_heuristic",
    unit="engagements/year", source=None, confidence="D",
    why="sim/world/military_logistics.py deliberately has no campaign-"
        "tempo model of its own (see its module docstring's WHERE THIS "
        "MODEL IS WRONG (d) and daily_supply_requirement_kg()'s "
        "engagements_per_day parameter) and takes one as a plain "
        "argument for exactly that reason; this is society.py's own "
        "placeholder for 'a modest campaigning season', standing in "
        "for the campaign-calendar mechanism (marches, sieges, battles "
        "at different intensities) that would derive a real figure. "
        "Six is an order-of-magnitude guess at 'a few real engagements "
        "a year, not one a week and not one a decade', with no source "
        "behind it - moving it changes military_equipment_burden_kg_"
        "per_soldier_per_year()'s reported number at full leverage but "
        "not its direction or its melee-tier floor.")
MILITARY_USEFULNESS_PROTECTION = declare(
    "MILITARY_USEFULNESS_PROTECTION", 0.09, kind="temporary_heuristic",
    unit="dimensionless protection points (multiplies patronage_weight "
         "* military_leverage)", source=None, confidence="D",
    why="Extra protection a patron gives a founder who can supply "
        "cannon or bastions, on top of the flat patron protection - "
        "gated on having a patron at all, since a founder with no "
        "buyer for it is not protected by knowing how to cast one. "
        "Tuned to be a real but secondary bonus alongside the patron "
        "tiers, not measured against any attested case.")
IDENTITY_COVER_PROTECTION = declare(
    "IDENTITY_COVER_PROTECTION", 0.12, kind="temporary_heuristic",
    unit="dimensionless protection points", source=None,
    confidence="D",
    why="What a respectable cover identity - books, a house, clothes, "
        "a secretary, a reputation for piety - is worth against "
        "accusation. See this method's own comment on what "
        "identity_cover actually buys; the figure itself is invented "
        "game balance.")
PRESSED_OFFICE_PROTECTION = declare(
    "PRESSED_OFFICE_PROTECTION", 0.10, kind="temporary_heuristic",
    unit="dimensionless protection points", source=None,
    confidence="D",
    why="The protection a pressed civic office buys, once the state "
        "has noticed the household - a burden and a shield at once, "
        "see office_report()'s own docstring. Sized similarly to the "
        "built protections above rather than measured against any "
        "attested decurionate privilege.")
REPUTATION_PROTECTION_CAP = declare(
    "REPUTATION_PROTECTION_CAP", 0.30, kind="temporary_heuristic",
    unit="dimensionless (maximum protection from reputation alone)",
    source=None, confidence="D",
    why="Ceiling on how much sheer personal reputation, independent of "
        "any patron or office, can protect a founder - so reputation "
        "alone cannot out-protect every built defence combined. "
        "Chosen to match the shape of the other protection caps in "
        "this method, not measured.")
REPUTATION_PROTECTION_SCALE = declare(
    "REPUTATION_PROTECTION_SCALE", 260.0, kind="temporary_heuristic",
    unit="reputation points per unit of protection", source=None,
    confidence="D",
    why="How fast reputation converts into protection, against "
        "REPUTATION_PROTECTION_CAP above. Reputation's own scale is "
        "itself invented (see STANDING_* in economy.py), so this "
        "denominator is a heuristic layered on a heuristic.")
BRIBERY_PROTECTION_CAP = declare(
    "BRIBERY_PROTECTION_CAP", 0.30, kind="temporary_heuristic",
    unit="dimensionless (maximum protection from bribery alone)",
    source=None, confidence="D",
    why="Ceiling on how much protection bribery, advocacy and piety "
        "can buy on their own, matching REPUTATION_PROTECTION_CAP so "
        "neither spendable defence dominates the other. Tuned, not "
        "measured against any attested bribe schedule.")
BRIBERY_PROTECTION_INCOME_SHARE = declare(
    "BRIBERY_PROTECTION_INCOME_SHARE", 0.6, kind="temporary_heuristic",
    unit="dimensionless (fraction of revenue treated as a full bribery "
         "budget)", source=None, confidence="D",
    why="What share of a year's revenue spent on bribes counts as a "
        "maximal bribery effort, the denominator bribes_ytd is judged "
        "against. No source ties a specific spending share to a "
        "specific bribe's actual effect on an accusation; a real "
        "figure needs a model of what a bribe could actually buy from "
        "a given magistrate.")
PROTECTION_CEILING = declare(
    "PROTECTION_CEILING", 0.92, kind="temporary_heuristic",
    unit="dimensionless (maximum total protection)", source=None,
    confidence="D",
    why="However many defences a household stacks, protection never "
        "reaches 1.0 - nothing makes a founder completely immune to "
        "accusation. Chosen to leave alarm_of's own protection floor "
        "(ALARM_PROTECTION_FLOOR) meaningful even at maximum "
        "protection; not measured.")
WITHDRAW_EVERY = declare(
    "WITHDRAW_EVERY", 12, kind="temporary_heuristic", unit="years",
    source=None, confidence="D",
    why="How long after withdrawing from public life the founder must "
        "wait before doing it again - being seen to retire twice in a "
        "short span is not retirement, it is a performance. A real "
        "figure needs a model of how quickly a specific society forgets "
        "a public retirement; this is a round number chosen to feel "
        "like a real cooling-off period, not derived from one.")
WITHDRAW_MIN_EMINENCE_FRACTION = declare(
    "WITHDRAW_MIN_EMINENCE_FRACTION", 0.5, kind="temporary_heuristic",
    unit="dimensionless (fraction of eminence_danger)", source=None,
    confidence="D",
    why="Below this share of the danger line, nobody has noticed the "
        "founder enough for withdrawing to buy anything - so the "
        "action is refused rather than silently wasting standing. "
        "Chosen to match the other half-danger-line thresholds this "
        "file uses (e.g. YOU ARE BECOMING CONSPICUOUS in core.py), not "
        "derived from a model of what makes someone worth withdrawing "
        "from.")
WITHDRAW_REPUTATION_RETENTION = declare(
    "WITHDRAW_REPUTATION_RETENTION", 0.5, kind="temporary_heuristic",
    unit="dimensionless (fraction of the gap above the standing floor "
         "kept)", source=None, confidence="D",
    why="Withdrawing moves reputation only halfway to the standing "
        "floor, not all the way to it - the work already done still "
        "stands for something. Chosen so withdrawal is a real, costly "
        "decision without being total self-erasure; not derived from "
        "any account of how quickly a real retirement was actually "
        "forgotten.")
WITHDRAW_EMINENCE_RETENTION = declare(
    "WITHDRAW_EMINENCE_RETENTION", 0.5, kind="temporary_heuristic",
    unit="dimensionless (fraction of eminence kept)", source=None,
    confidence="D",
    why="Withdrawing halves eminence outright, mirroring "
        "WITHDRAW_REPUTATION_RETENTION's own halving of the standing "
        "gap - the one lever this file gives against prominence "
        "should visibly work. Tuned to make the decision worthwhile, "
        "not measured.")
EMINENCE_HAZARD_SCALE = declare(
    "EMINENCE_HAZARD_SCALE", 90.0, kind="temporary_heuristic",
    unit="eminence points per unit of yearly ruin probability",
    source=None, confidence="D",
    why="How much eminence above the danger line it takes to add a "
        "full 100% to this year's chance of a prominence event - the "
        "same denominator core.py's step() uses when it actually rolls "
        "the dice, kept as one shared constant so the number quoted "
        "here can never disagree with the one that fires. Tuned so "
        "the risk climbs noticeably but not instantly past the line, "
        "not measured against any real rate of political destruction.")
EMINENCE_OUTCOME_CONFISCATION_SHARE = declare(
    "EMINENCE_OUTCOME_CONFISCATION_SHARE", 0.45, kind="temporary_heuristic",
    unit="dimensionless (share of prominence events)", source=None,
    confidence="D",
    why="Of the events prominence causes, the share that are property "
        "confiscation and forced retirement - shared with core.py's "
        "step(), which rolls against this same split. Invented "
        "proportions, not measured against any attested rate of each "
        "outcome for a fallen Roman grandee.")
EMINENCE_OUTCOME_PATRON_LOST_SHARE = declare(
    "EMINENCE_OUTCOME_PATRON_LOST_SHARE", 0.35, kind="temporary_heuristic",
    unit="dimensionless (share of prominence events)", source=None,
    confidence="D",
    why="Of the events prominence causes, the share that are a patron "
        "destroyed in someone else's quarrel - shared with core.py's "
        "step(). Invented, not measured.")
EMINENCE_OUTCOME_RUN_ENDS_SHARE = declare(
    "EMINENCE_OUTCOME_RUN_ENDS_SHARE", 0.20, kind="temporary_heuristic",
    unit="dimensionless (share of prominence events)", source=None,
    confidence="D",
    why="Of the events prominence causes, the share that end the run "
        "outright - the remainder after EMINENCE_OUTCOME_CONFISCATION_"
        "SHARE and EMINENCE_OUTCOME_PATRON_LOST_SHARE, shared with "
        "core.py's step(). Invented, not measured.")
EMINENCE_HAZARD_BASE_SCALE = declare(
    "EMINENCE_HAZARD_BASE_SCALE", 2.2, kind="temporary_heuristic",
    unit="dimensionless", source=None, confidence="D",
    why="Overall scale on the yearly prominence hazard - see this "
        "method's own docstring for why the mechanic exists at all "
        "(everything else saturates and left 200 successful runs out "
        "of 200 with nothing able to touch the founder). Tuned by "
        "measuring settled values against the danger line for two "
        "dice-free trials (see the 'A SIXTH OFF' comment below); not "
        "derived from any model of how quickly a real autocracy turns "
        "on a client.")
EMINENCE_DANGER_WEIGHT_DEFAULT = declare(
    "EMINENCE_DANGER_WEIGHT_DEFAULT", 0.5, kind="temporary_heuristic",
    unit="dimensionless", source=None, confidence="D",
    why="Fallback value for a civilisation file that does not set its "
        "own w_eminence_danger weight - a mid-scale default rather "
        "than zero, so a civilisation that forgot to set this is not "
        "silently immune to the mechanic. Not itself measured.")
EMINENCE_HAZARD_REPUTATION_SHARE = declare(
    "EMINENCE_HAZARD_REPUTATION_SHARE", 0.70, kind="temporary_heuristic",
    unit="dimensionless (weight in the hazard mix)", source=None,
    confidence="D",
    why="How much of the prominence hazard comes from reputation "
        "(squared, so it is dominated by the already-famous) versus "
        "visible wealth - reputation weighted heavier because being "
        "personally renowned is closer to what actually destroyed "
        "Sejanus, Seneca and Thrasea Paetus (see this method's own "
        "docstring) than mere money was. Tuned split, not fitted to "
        "any of those cases individually.")
EMINENCE_HAZARD_WEALTH_SHARE = declare(
    "EMINENCE_HAZARD_WEALTH_SHARE", 0.30, kind="temporary_heuristic",
    unit="dimensionless (weight in the hazard mix)", source=None,
    confidence="D",
    why="The complement of EMINENCE_HAZARD_REPUTATION_SHARE: how much "
        "of the prominence hazard comes from visible wealth alone.")
EMINENCE_REPUTATION_SCALE = declare(
    "EMINENCE_REPUTATION_SCALE", 100.0, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="Reference reputation this hazard treats as '1.0 famous' - "
        "reputation's own scale is itself invented (see STANDING_* in "
        "economy.py), so this normalisation is a heuristic layered on "
        "a heuristic.")
EMINENCE_WEALTH_VISIBLE_THRESHOLD_LABOUR_HOURS = declare(
    "EMINENCE_WEALTH_VISIBLE_THRESHOLD_LABOUR_HOURS", 5040000.0, kind="temporary_heuristic",
    unit="labour hours", source=None, confidence="D",
    why="Wealth treated as '1.0 visibly rich' for the prominence "
        "hazard, held as an amount of labour (a stock of labour-valued "
        "goods) so it follows what labour costs rather than the coin, "
        "and reused by eminence_report's own what_would_change_it note "
        "and by household_scale's HOUSEHOLD_WEALTH_SATURATES_AT comment "
        "as the smaller, personal-wealth line beneath that mechanic's "
        "much larger fiscal one. A round number marking enough personal "
        "wealth to be a courtier's envy, not measured against any "
        "specific attested fortune.")
EMINENCE_FAMILIARITY_RELIEF = declare(
    "EMINENCE_FAMILIARITY_RELIEF", 0.15, kind="temporary_heuristic",
    unit="dimensionless (fraction of hazard familiarity removes)",
    source=None, confidence="D",
    why="How much familiarity - the model's own measure of how "
        "unsurprising the founder has become - softens the prominence "
        "hazard. 'A SIXTH OFF, NOT A THIRD' below records that this "
        "was first tried at a third and measured, across three "
        "thousand run-years, to make the mechanic literally "
        "unreachable (every reported chance of ruin summed to 0.00); "
        "a sixth was chosen so a decades-long fixture of the city "
        "settles just under the danger line and one who has also "
        "reached the throne settles well over it - calibrated against "
        "that measurement, not derived from a model of habituation.")
HOUSEHOLD_HEADCOUNT_SATURATES_AT = declare(
    "HOUSEHOLD_HEADCOUNT_SATURATES_AT", 500.0, kind="temporary_heuristic",
    unit="employees+slaves+freedmen", source=None, confidence="D",
    why="Headcount at which household_scale()'s headcount term "
        "saturates at 1.0 - a round number chosen so the state's "
        "notice keeps climbing over most of a run's plausible staff "
        "size rather than maxing out early; not fitted to any "
        "specific historical household's size.")
HOUSEHOLD_WEALTH_SATURATES_AT = declare(
    "HOUSEHOLD_WEALTH_SATURATES_AT", 100800.0, kind="temporary_heuristic",
    unit="labourer-years of the opening wage", source=None,
    confidence="D",
    why="Capital at which household_scale()'s wealth term saturates - "
        "ten times X, deliberately: "
        "personal envy and fiscal scale worth an official's time are "
        "different, larger bars. See the comment above for the "
        "reasoning; the figure itself is chosen to fit the measured "
        "trajectories of two dice-free trials, not derived from a "
        "fiscal model.")
HOUSEHOLD_SCALE_HEADCOUNT_WEIGHT = declare(
    "HOUSEHOLD_SCALE_HEADCOUNT_WEIGHT", 0.45, kind="temporary_heuristic",
    unit="dimensionless (weight in household_scale mix)", source=None,
    confidence="D",
    why="How much household_scale() weights headcount - heaviest, "
        "because a state assessing a household for requisition counts "
        "workshops and granaries, not court gossip (see this method's "
        "own docstring). Tuned split, not fitted to any specific "
        "fiscal assessment.")
HOUSEHOLD_SCALE_WEALTH_WEIGHT = declare(
    "HOUSEHOLD_SCALE_WEALTH_WEIGHT", 0.35, kind="temporary_heuristic",
    unit="dimensionless (weight in household_scale mix)", source=None,
    confidence="D",
    why="How much household_scale() weights visible wealth - second "
        "heaviest, for the same reasoning as "
        "HOUSEHOLD_SCALE_HEADCOUNT_WEIGHT. Tuned, not measured.")
HOUSEHOLD_SCALE_EMINENCE_WEIGHT = declare(
    "HOUSEHOLD_SCALE_EMINENCE_WEIGHT", 0.20, kind="temporary_heuristic",
    unit="dimensionless (weight in household_scale mix)", source=None,
    confidence="D",
    why="How much household_scale() weights eminence (personal "
        "prominence) - smallest, because a household can be "
        "economically enormous and personally obscure, the exact gap "
        "this mechanic exists to close (see this method's own "
        "docstring). Tuned, not measured.")
STATE_NOTICE_THRESHOLD = declare(
    "STATE_NOTICE_THRESHOLD", 0.35, kind="temporary_heuristic",
    unit="dimensionless (state_notice, 0..1)", source=None,
    confidence="D",
    why="Below this, the state has bigger things to do than assess "
        "one household. Fitted so a Han dice-free trial crosses it "
        "around year 400-420, well before that trial's own year-551 "
        "goal, not in an epilogue after the tree is finished - a "
        "calibration choice against measured trajectories, not a "
        "derivation from a fiscal-capacity model.")
STATE_NOTICE_THRESHOLD_MILITARY = declare(
    "STATE_NOTICE_THRESHOLD_MILITARY", 0.20, kind="temporary_heuristic",
    unit="dimensionless (state_notice, 0..1)", source=None,
    confidence="D",
    why="Arms draw attention at a lower bar than general economic "
        "weight - 'a household that can make firearms in 400 AD Rome "
        "will be asked for them' does not wait for the household to "
        "also be rich - so this sits below STATE_NOTICE_THRESHOLD, "
        "paired with MIL_LEVERAGE_FLOOR_FOR_DEMAND rather than acting "
        "on notice alone. Tuned, not measured.")
MIL_LEVERAGE_FLOOR_FOR_DEMAND = declare(
    "MIL_LEVERAGE_FLOOR_FOR_DEMAND", 0.20, kind="temporary_heuristic",
    unit="dimensionless (military_leverage, 0..1)", source=None,
    confidence="D",
    why="Roughly one military-branch node done (military_leverage() "
        "reaches 0.20 at n=1 of 25 - see that method's own docstring): "
        "the FIRST working gun, not a standing army, is already "
        "enough for a state that can fight to want an accounting of "
        "it. Chosen to line up with military_leverage()'s own curve, "
        "not measured independently.")
MILITARY_DEMAND_COOLDOWN_YEARS = declare(
    "MILITARY_DEMAND_COOLDOWN_YEARS", 20.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Minimum gap between one military-supply demand and the next "
        "on the same household - long enough that it reads as an "
        "occasional levy rather than an annual tax. Round number, not "
        "derived from any attested requisition schedule.")
MILITARY_DEMAND_ANNUAL_CHANCE = declare(
    "MILITARY_DEMAND_ANNUAL_CHANCE", 0.10, kind="temporary_heuristic",
    unit="dimensionless (yearly probability once eligible)",
    source=None, confidence="D",
    why="Once a household is militarily useful and visible enough "
        "(military_demand_eligible), the yearly chance the state "
        "actually asks. Invented frequency, not fitted to any "
        "attested requisition rate.")
STATE_NOTICE_THRESHOLD_CONFISCATION = declare(
    "STATE_NOTICE_THRESHOLD_CONFISCATION", 0.75, kind="temporary_heuristic",
    unit="dimensionless (state_notice, 0..1)", source=None,
    confidence="D",
    why="Where the tail confiscation risk begins - see the comment "
        "above: calibrated so it is crossed only late (the final "
        "quarter to sixth of a run) in both measured dice-free "
        "trials, deliberately never lowered to make it bite earlier. "
        "A calibration choice against those trajectories, not a "
        "derivation from a state-capacity model.")
CONFISCATION_MAX_RATE = declare(
    "CONFISCATION_MAX_RATE", 0.28, kind="temporary_heuristic",
    unit="dimensionless (yearly probability at full notice)",
    source=None, confidence="D",
    why="Yearly confiscation probability once state_notice reaches "
        "1.0 (scaled down below that by _notice_over). Invented "
        "ceiling, not fitted to any attested confiscation rate for a "
        "fortune too large to go on taxing.")
CONFISCATION_CAPITAL_LOSS = declare(
    "CONFISCATION_CAPITAL_LOSS", 0.25, kind="temporary_heuristic",
    unit="dimensionless (fraction of capital seized)", source=None,
    confidence="D",
    why="Fraction of capital an outright confiscation takes. Tuned to "
        "be a real, painful loss without being a whole-fortune wipe; "
        "not sourced to any attested confiscation.")
REQUISITION_PROTECTION_DISCOUNT = declare(
    "REQUISITION_PROTECTION_DISCOUNT", 0.55, kind="temporary_heuristic",
    unit="dimensionless (fraction discounted at protection=1.0)",
    source=None, confidence="D",
    why="How much a fully-protected household bargains its "
        "requisition assessment down - a well-connected man negotiates "
        "his assessment down but does not buy exemption outright (see "
        "this method's own docstring). Tuned so protection is a real, "
        "substantial discount without erasing the state's claim; not "
        "measured.")
CONFISCATION_PROTECTION_LABELS = (
    "a patron and standing high enough to matter",
    "holdings too dispersed to be seized at a stroke",
    "too useful to the state to strip clean")
CONFISCATION_PROTECTION_DISCOUNT = declare(
    "CONFISCATION_PROTECTION_DISCOUNT", 0.5, kind="temporary_heuristic",
    unit="dimensionless (fraction discounted at protection=1.0)",
    source=None, confidence="D",
    why="How much a fully-protected household's confiscation risk is "
        "cut by a patron and general standing. Tuned to be a real, "
        "partial mitigation rather than a full defence - this is the "
        "treasury's own claim, not a courtroom accusation protection "
        "otherwise defends against - not measured.")
CONFISCATION_MILITARY_USEFULNESS_DISCOUNT = declare(
    "CONFISCATION_MILITARY_USEFULNESS_DISCOUNT", 0.4, kind="temporary_heuristic",
    unit="dimensionless (fraction discounted at military_leverage=1.0)",
    source=None, confidence="D",
    why="How much being militarily useful to the state mitigates "
        "confiscation risk - a state does not strip clean the one "
        "workshop that arms it (see this method's own docstring). "
        "Tuned, not measured.")
MILITARY_DEMAND_PROTECTION_DISCOUNT = declare(
    "MILITARY_DEMAND_PROTECTION_DISCOUNT", 0.4, kind="temporary_heuristic",
    unit="dimensionless (fraction discounted at protection=1.0)",
    source=None, confidence="D",
    why="How much a fully-protected household's military demand is "
        "discounted - a patron's standing softens even a demand that "
        "is not otherwise bargainable. Tuned, not measured.")
CONFISCATION_REPUTATION_LOSS = declare(
    "CONFISCATION_REPUTATION_LOSS", 6, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="Reputation lost when the treasury confiscates a fortune - "
        "being stripped of wealth by the state is itself a public "
        "humiliation. Tuned to be a real, noticeable hit alongside "
        "STANDING_* figures elsewhere in this engine; not measured.")
LEGITIMACY_FLOOR = declare(
    "LEGITIMACY_FLOOR", 0.5, kind="temporary_heuristic", unit="share of the state's reach", source=None,
    confidence="D",
    why="The least of its capacity a state keeps however far works have eroded the people's grant of authority: "
        "force and habit still collect something. A bound so the effect cannot null the state; its size is tuned.")
LEGITIMACY_CEILING = declare(
    "LEGITIMACY_CEILING", 1.25, kind="temporary_heuristic", unit="share of the state's reach", source=None,
    confidence="D",
    why="The most a state's reach is raised by works that win the people's consent, so that no purchase of "
        "praise makes a state stronger than a third more than its institutions alone; tuned.")
STATE_FUNDING_BASE_LABOUR_HOURS = declare(
    "STATE_FUNDING_BASE_LABOUR_HOURS", 50400.0, kind="temporary_heuristic",
    unit="labour hours/year at output_per_head=1, state_reach=1, pop_scale=1",
    source=None, confidence="D",
    why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
        "What an imperial patron is worth in direct funding at a "
        "reference civilisation size and state reach. No fiscal "
        "record backs this figure; a real answer needs a state budget "
        "model - tax revenue, the fiscus's own spending priorities - "
        "that this engine does not have, per CLAUDE.md 3.1's ban on "
        "asserting a state revenue outright.")
STATE_FUNDING_POP_SCALE_EXPONENT = declare(
    "STATE_FUNDING_POP_SCALE_EXPONENT", 0.4, kind="temporary_heuristic",
    unit="dimensionless exponent on pop_scale", source=None,
    confidence="D",
    why="How much faster a larger population's state can fund you, on "
        "a sub-linear curve so state funding does not simply track "
        "population one-for-one. Shape is plausible (bigger states have "
        "more surplus but not proportionally more to spare on one "
        "founder); the exponent itself is tuned, not fitted to any "
        "fiscal data.")
STATE_FUNDING_GOV_QUALITY_SCALE = declare(
    "STATE_FUNDING_GOV_QUALITY_SCALE", 25.0, kind="temporary_heuristic",
    unit="household.gov points per +100% funding", source=None,
    confidence="D",
    why="How much a better-governed household multiplies its own state "
        "funding. household.gov has no independent calibration of its "
        "own scale, so this denominator is picked to make the term feel "
        "proportionate rather than derived from anything.")
REPUTATION_DECAY_TOWARD_FLOOR = declare(
    "REPUTATION_DECAY_TOWARD_FLOOR", 0.97, kind="temporary_heuristic",
    unit="dimensionless (fraction of the gap above the standing floor "
         "kept per year)", source=None, confidence="D",
    why="How much of reputation's gap above the standing floor "
        "survives each year - reputation decays toward what a "
        "founder is actually known for (the floor), not toward zero "
        "(see comment above). A slow decay, tuned so novelty fades "
        "over decades rather than years; not measured against any "
        "attested reputation-decay rate.")
FAMILIARITY_CEILING = declare(
    "FAMILIARITY_CEILING", 0.9, kind="temporary_heuristic",
    unit="dimensionless (0..1)", source=None, confidence="D",
    why="Ceiling on familiarity, however long or publicly the founder "
        "has worked - a society never becomes fully unable to be "
        "surprised. Round figure, not measured.")
FAMILIARITY_PUBLICATION_WEIGHT = declare(
    "FAMILIARITY_PUBLICATION_WEIGHT", 0.5, kind="temporary_heuristic",
    unit="dimensionless (weight per spectacle/inexplicable node done)",
    source=None, confidence="D",
    why="How much each publicly astonishing thing the founder has "
        "done adds to familiarity's growth, relative to the passage "
        "of time (FAMILIARITY_TENURE_WEIGHT). Tuned, not measured.")
FAMILIARITY_TENURE_WEIGHT = declare(
    "FAMILIARITY_TENURE_WEIGHT", 0.25, kind="temporary_heuristic",
    unit="dimensionless (weight per year since year 100)", source=None,
    confidence="D",
    why="How much the mere passage of time (being a known fixture) "
        "adds to familiarity's growth, relative to specific "
        "publications (FAMILIARITY_PUBLICATION_WEIGHT). Tuned, not "
        "measured.")
SCANDAL_DECAY_RATE = declare(
    "SCANDAL_DECAY_RATE", 0.90, kind="temporary_heuristic",
    unit="dimensionless (fraction kept per year)", source=None,
    confidence="D",
    why="How much of last year's scandal survives, absent any fresh "
        "cause or bribery - scandal fades on its own, slower than "
        "market pressure but faster than reputation moves toward its "
        "floor. Tuned, not measured.")
EMINENCE_DECAY_RATE = declare(
    "EMINENCE_DECAY_RATE", 0.93, kind="temporary_heuristic",
    unit="dimensionless (fraction kept per year, before this year's "
         "hazard is added)", source=None, confidence="D",
    why="How much of last year's eminence survives before adding this "
        "year's prominence_hazard() - see society.py's eminence_report "
        "and prominence_hazard, which both reference this same rate "
        "(as self.EMINENCE_DECAY_RATE) so the reported settling value "
        "can never disagree with what actually accumulates here. "
        "Tuned so eminence settles at a level roughly proportionate to "
        "sustained hazard, not measured.")
AUTO_BRIBE_SCANDAL_THRESHOLD = declare(
    "AUTO_BRIBE_SCANDAL_THRESHOLD", 8, kind="temporary_heuristic",
    unit="scandal points", source=None, confidence="D",
    why="Scandal level above which the optimizer's standing bribery "
        "policy actually starts spending - below it, scandal is not "
        "yet worth buying down. Tuned, not measured.")
AUTO_BRIBE_CAPITAL_THRESHOLD_LABOUR_HOURS = declare(
    "AUTO_BRIBE_CAPITAL_THRESHOLD_LABOUR_HOURS", 40300.0, kind="temporary_heuristic",
    unit="labour hours", source=None, confidence="D",
    why="Minimum capital before the optimizer's bribery policy will spend at "
        'all, so a poor household is not bled dry bribing away scandal it might'
        ' survive anyway. Round number, not measured. Capital is a stock of '
        'labour-valued goods and coin, so the threshold is the hours of work it'
        ' represents.')
AUTO_BRIBE_CAPITAL_SHARE = declare(
    "AUTO_BRIBE_CAPITAL_SHARE", 0.12, kind="temporary_heuristic",
    unit="dimensionless (share of capital)", source=None,
    confidence="D",
    why="Ceiling on how much of current capital one year's bribery "
        "spend can be, so buying down scandal cannot alone bankrupt "
        "the household. Tuned, not measured.")
AUTO_BRIBE_COST_LABOUR_HOURS_PER_SCANDAL_POINT = declare(
    "AUTO_BRIBE_COST_LABOUR_HOURS_PER_SCANDAL_POINT", 5240.0, kind="temporary_heuristic",
    unit="labour hours per scandal point", source=None, confidence="D",
    why='What buying down one point of scandal costs, capping total spend '
        'alongside AUTO_BRIBE_CAPITAL_SHARE. Invented figure, not sourced to '
        'any attested bribe schedule. An official accepts a payment worth the '
        'work and risk he gives up, so the sum is the hours of unskilled labour'
        ' it buys.')
BRIBES_YTD_DECAY = declare(
    "BRIBES_YTD_DECAY", 0.7, kind="temporary_heuristic",
    unit="dimensionless (fraction kept per year)", source=None,
    confidence="D",
    why="How much of the running bribes_ytd total (itself the "
        "denominator update_protection() reads for the bribery "
        "protection term) survives into next year - a bribe's "
        "protective effect fades rather than accumulating forever. "
        "Tuned, not measured.")
BRIBE_SCANDAL_REDUCTION_LABOUR_HOURS_PER_POINT = declare(
    "BRIBE_SCANDAL_REDUCTION_LABOUR_HOURS_PER_POINT", 6050.0, kind="temporary_heuristic",
    unit="labour hours per scandal point removed (before bribability)", source=None, confidence="D",
    why='How much bribery spend it takes to remove one point of scandal, scaled'
        " further by this society's own bribability weight. Invented figure, "
        'not sourced to any attested bribe schedule. An official accepts a '
        'payment worth the work and risk he gives up, so the sum is the hours '
        'of unskilled labour it buys.')
SCANDAL_HAZARD_SCALE = declare(
    "SCANDAL_HAZARD_SCALE", 60.0, kind="temporary_heuristic",
    unit="scandal points per unit of yearly denunciation probability",
    source=None, confidence="D",
    why="How much scandal above the danger line it takes to add a "
        "full 100% to this year's denunciation chance - shared with "
        "the 'YOU ARE BEING TALKED ABOUT' warning text so the number "
        "quoted there can never disagree with the one that fires. "
        "Tuned, not measured against any attested denunciation rate.")
EMINENCE_CONFISCATION_CAPITAL_LOSS = declare(
    "EMINENCE_CONFISCATION_CAPITAL_LOSS", 0.55, kind="temporary_heuristic",
    unit="dimensionless (fraction of capital)", source=None,
    confidence="D",
    why="Fraction of capital the eminence-driven confiscation outcome "
        "takes - distinct from society.py's state-notice-driven "
        "CONFISCATION_CAPITAL_LOSS, this is the court's jealousy of a "
        "great man, unbribable by design (see prominence_hazard's own "
        "docstring). Tuned, not measured.")
EMINENCE_CONFISCATION_REPUTATION_LOSS = declare(
    "EMINENCE_CONFISCATION_REPUTATION_LOSS", 18, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="Reputation lost to an eminence-driven confiscation and forced "
        "retirement - the largest single reputation hit in this file, "
        "reflecting public disgrace on top of the property loss. "
        "Tuned, not measured.")
EMINENCE_CONFISCATION_RETENTION = declare(
    "EMINENCE_CONFISCATION_RETENTION", 0.45, kind="temporary_heuristic",
    unit="dimensionless (fraction of eminence kept)", source=None,
    confidence="D",
    why="Fraction of eminence kept after a confiscation and forced "
        "withdrawal - the outcome itself lowers prominence sharply. "
        "Tuned, not measured.")
EMINENCE_PATRON_LOSS_RETENTION = declare(
    "EMINENCE_PATRON_LOSS_RETENTION", 0.5, kind="temporary_heuristic",
    unit="dimensionless (fraction of eminence kept)", source=None,
    confidence="D",
    why="Fraction of eminence kept after a patron is destroyed in "
        "someone else's quarrel - a smaller drop than "
        "EMINENCE_CONFISCATION_RETENTION since the founder's own "
        "position is not directly struck. Tuned, not measured.")
EMINENCE_PATRON_LOSS_REPUTATION_LOSS = declare(
    "EMINENCE_PATRON_LOSS_REPUTATION_LOSS", 10, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="Reputation lost when a patron is destroyed - smaller than "
        "EMINENCE_CONFISCATION_REPUTATION_LOSS since the disgrace is "
        "the patron's, not directly the founder's. Tuned, not "
        "measured.")
REPUTATION_CEILING = declare(
    "REPUTATION_CEILING", 100.0, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="The top of the reputation scale this engine uses throughout "
        "(REPUTATION_EASE_SCALE in economy.py reads reputation "
        "against this same implicit ceiling). A scale choice, not a "
        "measured social fact.")

# ---- reputation and standing: a scoreboard, not yet a social mechanism ----
#
# None of the numbers below are measured facts about anything; they are a hand-tuned scoring function for "how well known and
# well regarded are you", invented because no lower-level model of patronage, gossip or audience reach exists yet. A real
# mechanism would derive standing from who actually knows what you have done and how far that spreads through a real social
# network (patrons, students, guild membership, literacy and travel time all bound how far reputation can propagate).
STANDING_BASE_FLOOR = declare(
    "STANDING_BASE_FLOOR", 0.5, kind="temporary_heuristic",
    unit="reputation points (dimensionless)", source=None, confidence="D",
    why="The reputation floor of someone who has founded and finished "
        "nothing yet - not zero, because arriving with a plan and a "
        "household is itself a small, visible fact. A real mechanism would "
        "derive this from how a stranger is actually perceived on arrival "
        "in a given society, not assign a flat starting score.")
STANDING_PER_SQRT_EARNED = declare(
    "STANDING_PER_SQRT_EARNED", 0.55, kind="temporary_heuristic",
    unit="reputation points per sqrt(finished works)", source=None,
    confidence="D",
    why="How much each additional finished, ungranted work adds to standing, "
        "on a sqrt curve so the first few matter far more than the "
        "hundredth. The sqrt SHAPE is a real claim (reputation saturates, it "
        "does not accumulate linearly); the 0.55 coefficient is simply "
        "tuned until the early game felt right. A real mechanism needs a "
        "model of who hears about a given work and how impressed they are.")
STANDING_SCANDAL_PENALTY_PER_POINT = declare(
    "STANDING_SCANDAL_PENALTY_PER_POINT", 0.5, kind="temporary_heuristic",
    unit="reputation points lost per point of household.scandal",
    source=None, confidence="D",
    why="How much a point of scandal erodes standing, one-for-one at half "
        "weight. Scandal itself has no source model (who spreads it, how "
        "fast, whether it fades) so this coefficient is a placeholder for "
        "that whole missing mechanism, not a measured rate of anything.")
REPUTATION_EASE_SCALE = declare(
    "REPUTATION_EASE_SCALE", 120.0, kind="temporary_heuristic",
    unit="reputation points per unit of ease (dimensionless denominator)",
    source=None, confidence="D",
    why="How much reputation it takes to make everything else roughly "
        "twice as easy (rep_factor = 1 + reputation/120). No independent "
        "source; a real figure needs a model of what reputation actually "
        "buys (lower prices, faster favours, less friction) instead of one "
        "shared multiplier standing in for all of them at once.")
