"""The local labour market: who is out there, how much of them this
household can reach, and what leaning on a trade recently does to its price.

Split out of labour.py (see that file's own docstring for why). These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and moved verbatim.

labour_pressure/_add_labour_pressure/labour_price_factor and its
after-hiring forecast are "the market responds to demand, and to supply" -
the same saturating-price idea market_pressure already applies to slaves
(see labour_bondage.py), extended to ordinary hiring. trade_available,
found_trade_school and _trade_market_class decide whether a trade can be
had here AT ALL and which reachable-population class it falls in, which
market_supply, reachable_trade_population and national_trade_population -
the actual depth of that market, this household's own reach into it, and
the whole country's rough total - all read from. TOWN_POPULATION_REFERENCE
and TRADE_DENSITY size the one provincial town this household's own labour
market represents; SCHOLAR_ENGAGEMENT_FRACTION, SCRIBE_ENGAGEMENT_FRACTION
and MERCHANT_DENSITY are the same idea for the trades literacy already
bounds. population_report and home_town_population_estimate are what the
'population' command shows, built entirely from the numbers above.
effective_scholars and scholar_hands_available answer "how many scholars
can this household actually put to work this year", the population-side
half of the same question hours_you_can_call_on (labour_training.py)
answers for craft hours.
"""
from .data import (TRADES_ABSENT, TRADE_NOTES, WAGES, trade_family)
from sim.constants import declare


class PopulationMixin:
    """The labour market this household draws on: its depth, its price
    response to recent hiring, and the population estimates behind both -
    see this module's own docstring for why these subjects sit together.
    """


    # ---- the market responds to demand, and to supply ----------------------
    # FINDINGS_ROUND2 section R: market_pressure already does this for slaves
    # - buying in bulk bids the price up, it remembers between purchases, and
    # it decays - and nothing else in the economy had an equivalent. This is
    # the labour half: the same saturating idea, extended honestly rather than
    # copied, and self-contained (decayed on READ rather than decremented once
    # a year in step(), which lives in core.py, so nothing outside this file
    # has to know this exists). 0.6x a year, the same rate market_pressure
    # decays at (0.55, near enough) - mostly gone in three years.
    LABOUR_PRESSURE_DECAY_RATE = declare(
        "LABOUR_PRESSURE_DECAY_RATE", 0.6, kind="temporary_heuristic",
        unit="fraction of remembered pressure surviving per year",
        source=None, confidence="D",
        why="How fast a burst of recent hiring or commissioning stops "
            "moving the price of a trade - the same rate this file's own "
            "comment says market_pressure decays at for slaves (0.55, "
            "'near enough'), reused for labour rather than fitted "
            "independently. Mostly gone in three years; a real figure "
            "would come from how fast a local labour market actually "
            "recovers from a demand shock, which nothing here measures.")

    def labour_pressure(self, trade):
        rec = getattr(self.household, "_labour_pressure", None)
        rec = rec.get(trade) if rec else None
        if not rec:
            return 0.0
        hours, year = rec
        age = max(0.0, self.year - year)
        return hours * (self.LABOUR_PRESSURE_DECAY_RATE ** age)

    def _add_labour_pressure(self, trade, hours):
        pressures = getattr(self.household, "_labour_pressure", None)
        if pressures is None:
            pressures = self.household._labour_pressure = {}
        pressures[trade] = (self.labour_pressure(trade) + max(0.0, hours), self.year)

    LABOUR_PRESSURE_SHARE_CAP = declare(
        "LABOUR_PRESSURE_SHARE_CAP", 1.5, kind="temporary_heuristic",
        unit="dimensionless (pressure / market_supply)",
        source=None, confidence="D",
        why="Caps how much of the price-pressure curve a single burst of "
            "hiring can reach, so leaning on a trade harder and harder does "
            "not send its price to infinity. The curve shape (saturating, "
            "not linear) is a real claim about markets; where exactly it "
            "saturates is tuned.")
    LABOUR_PRICE_PRESSURE_COEFFICIENT = declare(
        "LABOUR_PRICE_PRESSURE_COEFFICIENT", 0.9, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="How much a fully-leaned-on trade's price roughly doubles by: "
            "at share=1.0 this term alone adds 0.9 to the multiplier. "
            "material_price_factor uses the identical curve for the same "
            "reason (see this function's own docstring); the coefficient "
            "itself is tuned to feel like a real but survivable premium, "
            "not fitted to an observed labour-market price response.")

    def _labour_price_factor_from(self, pressure, supply):
        """The one curve behind labour_price_factor - split out so a forecast
        can share it exactly rather than recomputing it (see
        labour_price_factor_after_hiring)."""
        supply = max(1.0, supply)
        share = min(self.LABOUR_PRESSURE_SHARE_CAP, pressure / supply)
        return 1.0 + self.LABOUR_PRICE_PRESSURE_COEFFICIENT * share * share

    def labour_price_factor(self, trade):
        """What hiring, commissioning or keeping MORE of this trade costs
        beyond the wage table, from how hard you have recently leaned on its
        local supply.

        `market_supply(trade)` is the ceiling: everyone this trade could put
        to work here, including everyone you already employ. Recent pressure
        taken as a share of that ceiling is negligible at a fifth of it and
        roughly doubles the price at the whole of it - the same curve
        `material_price_factor` uses for the same reason. Because the ceiling
        itself grows when you teach the trade a bigger workforce, or when an
        institution or literacy widens it, the SAME recent pressure buys a
        smaller premium once the supply behind it is bigger: teaching fifty
        machinists is what makes hiring the fifty-first one cheap again, not
        merely possible.
        """
        return self._labour_price_factor_from(self.labour_pressure(trade),
                                               self.market_supply(trade))

    def labour_price_factor_after_hiring(self, trade, hire_count=1.0):
        """What labour_price_factor(trade) becomes the INSTANT you hire n
        more - not the market as it stands, the hire you are contemplating.

        This is the number `hire` itself effectively charges from the moment
        the new people are on the books (see wage_bill, which applies the
        CURRENT labour_price_factor to every head of a trade, not only the
        newest one): a Norse player was quoted "a year of one: 525" for a
        scholar, hired one, and the standing wage bill came to 847.92 - 61%
        more - because that one hire pushed labour_price_factor for scholars
        from 1.0 to 1.615 against a near-empty local supply. The quote and
        the bill were never inconsistent; the quote just priced the market
        as it stood, one command before the player's own action moved it.

        Genuinely simulates the hire rather than re-deriving market_supply's
        formula a second time (which differs for a taught-only trade): adds
        n to employees[trade], reads the real market_supply(trade) back, and
        undoes the change. labour_pressure needs no such trick - it is a
        running total, not a function of current headcount - so n more
        hours are simply added to it, exactly as _add_labour_pressure would.
        """
        hire_count = max(0.0, hire_count)
        if hire_count <= 0:
            return self.labour_price_factor(trade)
        add_hours = hire_count * self.HOURS_PER_PERSON_YEAR
        before = self.household.employees.get(trade, 0.0)
        self.household.employees[trade] = before + hire_count
        try:
            supply_after = self.market_supply(trade)
        finally:
            if before:
                self.household.employees[trade] = before
            else:
                self.household.employees.pop(trade, None)
        pressure_after = self.labour_pressure(trade) + add_hours
        return self._labour_price_factor_from(pressure_after, supply_after)

    def effective_scholars(self):
        """You are your own natural philosopher; everyone else is hired."""
        return self.household.scholars + (1.0 if self.founder_alive else 0.0)

    def scholar_hands_available(self):
        """Scholars you can actually put on a project this year: the ones on
        your own staff, yourself, plus the ones whose time you have already
        bought under contract.

        THE SAME FIX craft_hands_available() GOT, ARRIVING LATE. That
        function's own comment records the bug: a gate that read the payroll
        alone, so work you had already paid an outside shop to do could not
        satisfy the requirement - and the refusal's advice was to go and
        commission it. `commission` could not unblock the gate that
        recommended commission.

        It was fixed for craft trades and never extended to scholars, so the
        identical defect survived for them and was reported as
        Complaints/34: buying labourer hours works, buying SCHOLAR hours
        does nothing. Reproduced against the live protocol - a 2,000-hour
        scholar commission succeeded, took the money, and left the refusal
        byte-identical.

        A year of a scholar's time IS a scholar, for the purpose of whether
        you may attempt a thing that needs one. Buying the work rather than
        the person is the whole point of `commission`, and it is what
        somebody in this position actually did.
        """
        contracted = sum(hours for trade, hours
                         in getattr(self.household, "contract_hours", {}).items()
                         if trade_family(trade) == "scholar")
        return (self.effective_scholars()
                + contracted / self.HOURS_PER_PERSON_YEAR)

    def trade_available(self, trade):
        """Can this trade be had here at all, at any price?

        Rome has masons and plumbers in abundance and no machinists whatever.
        An absent trade is not expensive, it is absent, and the only way to have
        one is to teach somebody the trade yourself.
        """
        if trade not in TRADES_ABSENT:
            return True
        return (trade in self.household.trades_created
                or getattr(self.household, "trade_schools", {}).get(trade, 0.0) > 0)

    def found_trade_school(self, trade, seats):
        """Create durable local training capacity for one named trade."""
        if trade not in WAGES or not self.trade_available(trade):
            return False, ("the trade must exist before a school can reproduce "
                           "it; teach or discover %s first" % trade)
        seats = float(seats)
        cost = seats * self.TRADE_SCHOOL_COST_PER_SEAT * self.price_index
        if seats <= 0 or cost > self.household.capital:
            return False, "cannot afford that trade school"
        self.household.capital -= cost
        schools = getattr(self.household, "trade_schools", None)
        if schools is None:
            schools = self.household.trade_schools = {}
        schools[trade] = schools.get(trade, 0.0) + seats
        self.household.trades_created.add(trade)
        return True, None

    def _trade_market_class(self, trade):
        """Which reachable-labour-pool class a trade falls in - read ONCE,
        here, so market_supply's own hiring ceiling and
        national_trade_population's country-wide estimate (used by the
        'population' command) cannot say two different things about the
        same trade. See TRADE_DENSITY for what each class is worth, and
        why, and TOWN_POPULATION_REFERENCE for the town size it is a
        fraction OF.

        Unchanged in substance from the keyword/list check this replaced;
        only pulled out to one place instead of being reasoned about twice.
        """
        note = TRADE_NOTES.get(trade, "").lower()
        if "abundance" in note or "abundant" in note or "numerous" in note:
            return "abundant"
        if "scarcest" in note:
            return "scarce"
        if trade_family(trade) == "scholar":
            return "scholar"
        if trade in ("labourer", "artisan", "carpenter", "mason", "potter", "smith",
                 "sailor", "miner", "furnaceman"):
            return "common"
        return "uncommon"          # glassblowers, engravers, opticians' forebears

    # HIRING A HANDFUL OF SMITHS MUST NOT MOVE THE STANDING WAGE. A market
    # supply pool sized for a single provincial town, not the whole country,
    # would make hiring five smiths where thousands actually exist move the
    # price a lot, because the pool itself is the size of a hamlet -
    # something the game needs to say out loud rather than leave a player to
    # infer (see the 'population' command, and the framing note in `hire`,
    # `labour` and each civ's opening briefing). Buying ten slaves is a
    # DIFFERENT wall - household_room, this household's own capacity to
    # feed, house and supervise people, checked in hire() below and nothing
    # to do with market_supply - and is correctly left alone: a household of
    # one cannot run ten slaves without somewhere to put them, in any
    # economy, however deep its labour market runs.
    #
    # TOWN_POPULATION_REFERENCE is the size of the single market this
    # household's reach actually represents, at full population scale (Rome
    # itself, pop_scale == 1.0) - not the whole country, which is exactly the
    # thing this game needs to say out loud rather than leave a player to
    # infer (see the 'population' command, and the framing note in `hire`,
    # `labour` and each civ's opening briefing). ANCHORED, not invented: the
    # album of the fabri tignuarii of Ostia (CIL XIV 4569, dated 198 AD)
    # records about 350 quinquennial members of one building-trade guild in a
    # town usually put at the order of 50,000 people (Meiggs, "Roman Ostia",
    # 2nd ed. 1973, ch. on the plebs and the collegia) - call it 0.7% of the
    # town registered in ONE common craft. A floor, not a ceiling: guild
    # rolls undercount apprentices, slaves, women in the associated trades
    # and anyone who never joined.
    #
    # It shrinks with pop_scale exactly the way hired_hours_cap_base already
    # does ("a civilization of 1.5 million cannot field what one of 65
    # million can" - hired_cap()'s own comment) - a smaller civilisation's
    # own provincial towns are smaller too, which is a separate and
    # defensible claim from how big ONE of them is.
    TOWN_POPULATION_REFERENCE = declare(
        "TOWN_POPULATION_REFERENCE", 50000.0, kind="engineering_estimate",
        unit="people, at pop_scale=1.0",
        source="Meiggs, 'Roman Ostia', 2nd ed. 1973 (the album of the "
               "fabri tignuarii of Ostia, CIL XIV 4569, dated 198 AD, "
               "records about 350 quinquennial members of one "
               "building-trade guild in a town usually put at the order "
               "of 50,000 people).",
        confidence="C",
        why="The size of the ONE provincial town this household's labour "
            "market represents, at full population scale - not the whole "
            "country. Anchored on a real attestation (guild membership as "
            "a share of a town of known rough size), used as a floor "
            "rather than a precise census figure since guild rolls "
            "undercount apprentices, slaves and women in the trade. This "
            "sizes a MARKET, not a historical outcome the simulation is "
            "meant to reproduce - see this constant's own long comment "
            "above for the full derivation.")

    # What SHARE of that town plies each class of trade - feeding BOTH
    # market_supply's ceiling for 'abundant' and 'common' (the classes the
    # break report was actually about) and national_trade_population's
    # country-wide estimate for every class. 'scarce', 'uncommon' and
    # 'scholar' keep their PRE-EXISTING, separately-tuned hiring ceilings
    # below (0.08 x base, 0.25 x base, and the literacy-bound 0.35 x base
    # literate_capacity's own docstring explains at length) - this fix
    # targets the trades that were wrongly sharp, not the ones that are
    # correctly so, and changing a density entry for those three classes
    # moves only what 'population' reports the COUNTRY holds, never this
    # household's hiring cap or the regression coverage tuned against it
    # (FINDINGS_ROUND2 section R's millwright checks, literate_capacity's
    # own scholar-ceiling checks).
    #
    #   common:    anchored directly on the Ostia figure above.
    #   abundant:  the trades the wage table's OWN notes call abundant or
    #              numerous (mason, plumber, sailor) - set higher again,
    #              matching the stronger language, still no more than an
    #              order of magnitude's worth of judgement on top of a real
    #              attestation.
    #   uncommon, scarce: NO COMPARABLE FIGURE FOUND for engraver,
    #              glassblower, master (uncommon) or for millwright, which
    #              its own note already calls "the scarcest useful trade
    #              you can hire" (scarce). These two are honest
    #              order-of-magnitude placeholders for the population
    #              report only, smaller than an attested trade and smaller
    #              again for the one the game already singles out as
    #              rarest - not research, and said so here rather than
    #              dressed up as data.
    _TRADE_DENSITY_WHY = (
        "Share of TOWN_POPULATION_REFERENCE plying a trade of this class - "
        "'common' is anchored directly on the Ostia guild figure "
        "(TOWN_POPULATION_REFERENCE's own citation); 'abundant' is set "
        "higher again to match the wage table's own language calling "
        "those trades abundant or numerous, still within an order of "
        "magnitude of the real attestation; 'uncommon' and 'scarce' have "
        "NO comparable figure found for the trades in them and are "
        "honest, explicitly-labelled order-of-magnitude placeholders, not "
        "research - see this table's own long comment above.")
    TRADE_DENSITY_ABUNDANT = declare(
        "TRADE_DENSITY_ABUNDANT", 0.014, kind="engineering_estimate",
        unit="fraction of the town's population", source=None,
        confidence="C", why=_TRADE_DENSITY_WHY)
    TRADE_DENSITY_COMMON = declare(
        "TRADE_DENSITY_COMMON", 0.007, kind="engineering_estimate",
        unit="fraction of the town's population",
        source="CIL XIV 4569 (see TOWN_POPULATION_REFERENCE): about 0.7% "
               "of the town registered in one common building trade.",
        confidence="C", why=_TRADE_DENSITY_WHY)
    TRADE_DENSITY_UNCOMMON = declare(
        "TRADE_DENSITY_UNCOMMON", 0.001, kind="temporary_heuristic",
        unit="fraction of the town's population", source=None,
        confidence="D", why=_TRADE_DENSITY_WHY)
    TRADE_DENSITY_SCARCE = declare(
        "TRADE_DENSITY_SCARCE", 0.00015, kind="temporary_heuristic",
        unit="fraction of the town's population", source=None,
        confidence="D", why=_TRADE_DENSITY_WHY)
    TRADE_DENSITY = {
        "abundant": TRADE_DENSITY_ABUNDANT,
        "common": TRADE_DENSITY_COMMON,
        "uncommon": TRADE_DENSITY_UNCOMMON,
        "scarce": TRADE_DENSITY_SCARCE,
    }
    # scholar and scribe are bound by literacy, not by town population (see
    # literacy_factor, literate_capacity) - their NATIONAL estimate uses the
    # same idea applied to the literate pool instead of the town: what
    # fraction of the people who can read at all make their living reading
    # and writing for others, rather than simply being a literate landowner,
    # priest or advocate. Neither fraction is a count anyone published; both
    # are deliberately small because the trades themselves are (Rome's own
    # literate_capacity("scholar") tops out at 5.9 reachable before any
    # institution trains more). merchant is excluded from LITERATE_TRADES on
    # purpose (see that set's own comment - "an agent working on commission is
    # not, in this period, chiefly a reader") so it gets a plain urban density
    # instead, also with no specific count found.
    SCHOLAR_ENGAGEMENT_FRACTION = declare(
        "SCHOLAR_ENGAGEMENT_FRACTION", 0.002, kind="temporary_heuristic",
        unit="fraction of (literacy_elite x population)", source=None,
        confidence="D",
        why="What fraction of the literate, propertied population makes "
            "its living as a scholar for hire, rather than simply being a "
            "literate landowner, priest or advocate. No published count "
            "exists for this; deliberately small, consistent with "
            "literate_capacity('scholar') topping out at 5.9 reachable "
            "for Rome before any institution trains more.")
    SCRIBE_ENGAGEMENT_FRACTION = declare(
        "SCRIBE_ENGAGEMENT_FRACTION", 0.05, kind="temporary_heuristic",
        unit="fraction of (literacy_general x population)", source=None,
        confidence="D",
        why="As SCHOLAR_ENGAGEMENT_FRACTION, for scribes drawn from the "
            "wider general-literacy pool rather than the propertied elite.")
    MERCHANT_DENSITY = declare(
        "MERCHANT_DENSITY", 0.004, kind="temporary_heuristic",
        unit="fraction of urban population", source=None, confidence="D",
        why="Merchant density, treated like an ordinary craft density "
            "(TRADE_DENSITY) rather than a literacy-bound one, because "
            "merchant is deliberately excluded from LITERATE_TRADES (an "
            "agent working on commission is not, in this period, chiefly "
            "a reader). No specific count found; an order-of-magnitude "
            "placeholder.")

    TAUGHT_TRADE_SUPPLY_MULTIPLIER = declare(
        "TAUGHT_TRADE_SUPPLY_MULTIPLIER", 1.5, kind="temporary_heuristic",
        unit="dimensionless multiplier on your own employees' hours",
        source=None, confidence="D",
        why="For a trade this society had no word for until you taught it "
            "(TRADES_ABSENT), the market this household reaches is only "
            "the people you trained plus the ones they have since trained "
            "themselves - approximated as half again your own headcount's "
            "hours, standing in for that second generation, rather than "
            "modelling who-taught-whom explicitly.")
    SCARCE_TRADE_HIRING_SHARE = declare(
        "SCARCE_TRADE_HIRING_SHARE", 0.08, kind="temporary_heuristic",
        unit="fraction of hired_hours_cap_base", source=None,
        confidence="D",
        why="Hiring ceiling share for the 'scarce' trade class (today, "
            "just millwright, this tree's own 'scarcest useful trade you "
            "can hire') - tighter than TRADE_DENSITY_UNCOMMON's already-"
            "tight share. Pre-existing, separately-tuned figure kept as "
            "the fix that widened 'abundant'/'common' left it (see "
            "TRADE_DENSITY's own comment on why these three keep their "
            "own tuning).")
    UNCOMMON_TRADE_HIRING_SHARE = declare(
        "UNCOMMON_TRADE_HIRING_SHARE", 0.25, kind="temporary_heuristic",
        unit="fraction of hired_hours_cap_base", source=None,
        confidence="D",
        why="As SCARCE_TRADE_HIRING_SHARE, for the 'uncommon' class "
            "(glassblowers, engravers, masters).")

    def market_supply(self, trade):
        """Hours a year of this trade the local labour market can actually supply.

        THIS IS ONE TOWN'S MARKET, NOT THE COUNTRY'S - the household this
        game puts you in charge of draws on one town's labour, the way a
        real Roman, Han or Norse founder would have. See
        TOWN_POPULATION_REFERENCE's own comment for why that is a
        defensible modelling choice and TRADE_DENSITY for how big 'one
        town's worth' of each trade actually is; national_trade_population
        answers the country-wide question this number is not trying to.
        """
        if not self.trade_available(trade):
            return 0.0
        base = self.cfg["hired_hours_cap_base"] * (self.POP_SCALE_FLOOR_SHARE
                                                     + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self.pop_scale))
        school_hours = (getattr(self.household, "trade_schools", {}).get(trade, 0.0)
                        * self.HOURS_PER_PERSON_YEAR)
        if trade in TRADES_ABSENT:
            # Only the people you taught, plus the ones they have taught since.
            return (self.household.employees.get(trade, 0.0) * self.HOURS_PER_PERSON_YEAR
                    * self.TAUGHT_TRADE_SUPPLY_MULTIPLIER
                    + school_hours)
        cls = self._trade_market_class(trade)
        if cls in ("abundant", "common"):
            # A REAL TOWN'S WORTH, not base's village-sized share of it (see
            # this function's own docstring and the comment above
            # TOWN_POPULATION_REFERENCE for the full account and its
            # citation).
            town = self.TOWN_POPULATION_REFERENCE * (self.POP_SCALE_FLOOR_SHARE
                                                       + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self.pop_scale))
            cap = town * self.TRADE_DENSITY[cls] * self.HOURS_PER_PERSON_YEAR
        elif cls == "scholar":
            cap = base * self.SCHOLAR_MARKET_SHARE   # literate men are a small fraction of anywhere
        elif cls == "scarce":
            cap = base * self.SCARCE_TRADE_HIRING_SHARE
        else:
            cap = base * self.UNCOMMON_TRADE_HIRING_SHARE   # uncommon: glassblowers, engravers, masters
        if self.running("school_founded"):
            cap *= 1.0 + self.SCHOOL_FOUNDED_HIRING_COEFFICIENT * self.institution_units("school_founded") ** self.HIRING_MULTIPLIER_EXPONENT
        if self.running("patron_imperial"):       cap *= self.PATRON_IMPERIAL_HIRING_MULTIPLIER
        if self.running("academy_network"):
            cap *= 1.0 + self.ACADEMY_NETWORK_HIRING_COEFFICIENT * self.institution_units("academy_network") ** self.HIRING_MULTIPLIER_EXPONENT
        if self.running("interchangeable_parts"): cap *= self.INTERCHANGEABLE_PARTS_HIRING_MULTIPLIER
        # A trade that needs reading cannot be bought past how many people
        # here can read (FINDINGS_ROUND2 section Q). scholar and scribe are
        # the only literate trades that reach this branch - the taught ones
        # (engineer, chemist, machinist, optician) are all in TRADES_ABSENT
        # and returned above, bounded instead by literate_capacity() in
        # train().
        if trade in self.LITERATE_TRADES:
            cap *= self.literacy_factor(trade)
        return (cap + self.household.employees.get(trade, 0.0) * self.HOURS_PER_PERSON_YEAR
                + school_hours)

    def reachable_trade_population(self, trade):
        """What this household's own labour market actually holds of this
        trade, your own employees included - the 'population' command's
        "within your reach" column; see national_trade_population for the
        other half of the same question.

        scholar and scribe read literate_capacity() INSTEAD OF market_
        supply(): that is the real wall hire() and train() enforce for
        them (see _literate_wall_refusal - "this household's reach into
        the labour market for %ss will not stretch past %.1f"), floored
        at 1.5 so a literate person always exists somewhere, which market_
        supply's own formula is not floored to. Showing the smaller,
        unfloored market_supply figure here would make Norse scribes read
        as "0.2 within your reach" when the game will in fact let a
        player hire one - exactly the kind of false "nobody's there"
        reading literate_capacity's own floor exists to prevent.
        """
        if trade in ("scholar", "scribe"):
            return self.literate_capacity(trade)
        return self.market_supply(trade) / self.HOURS_PER_PERSON_YEAR

    def national_trade_population(self, trade):
        """A rough ESTIMATE of how many people ply this trade across the
        WHOLE COUNTRY - not this household's reach (reachable_trade_
        population, above) and not a second population model: the same
        TRADE_DENSITY this file's own market_supply reads, applied to the
        country's urban population instead of to one town, because a
        craft trade is overwhelmingly a town trade (see civ['urban_
        fraction'], which core.py already reads for pop_scale). 0.0 for a
        trade that does not exist in this society at all - trade_
        available() already says so.

        Every number this returns is explicitly an estimate and the
        'population' command says so on the screen; nobody has published a
        trade-by-trade occupational census of Rome, Han China or Viking-age
        Scandinavia, and TRADE_DENSITY's own comment already says, for two
        of its four classes, that no comparable figure was found at all.
        """
        if not self.trade_available(trade):
            return 0.0
        # self.population.total (sim/world/demography.py's age-cohort
        # model) IS this civilisation's actual running headcount, and must
        # be read directly rather than reconstructed from civ["population"]
        # (a fixed config number) times a ratio of two scalar fields
        # (pop_scale/_pop_scale_base) - that reconstruction would be the
        # one place in the engine trying to answer "how many people are
        # actually here" as a headcount built entirely out of ratios.
        pop = self.population.total
        urban = pop * float(self.civ.get("urban_fraction", 0.0))
        if trade == "scholar":
            return pop * float(self.civ.get("literacy_elite", 0.0)) * self.SCHOLAR_ENGAGEMENT_FRACTION
        if trade == "scribe":
            return pop * float(self.civ.get("literacy_general", 0.0)) * self.SCRIBE_ENGAGEMENT_FRACTION
        if trade == "merchant":
            return urban * self.MERCHANT_DENSITY
        if trade in TRADES_ABSENT:
            # engineer, chemist, machinist, optician, electrician: taught
            # into existence by you alone (trade_available already checked
            # this is now true), so "the country's" population of the trade
            # IS what you have taught - there is no wider pool to estimate.
            return self.household.employees.get(trade, 0.0)
        return urban * self.TRADE_DENSITY.get(self._trade_market_class(trade), 0.0)

    def home_town_population_estimate(self):
        """How big the single town TOWN_POPULATION_REFERENCE represents
        actually is for THIS civilisation, at its current pop_scale - the
        number the 'population' command shows next to the country's own,
        so a player can see "one household, one town" for themselves
        instead of inferring it from a refusal. An estimate, said as one:
        this engine has no named city for the founder to stand in, only
        the abstraction hired_hours_cap_base and this constant already
        are (see TOWN_POPULATION_REFERENCE's own comment).
        """
        return self.TOWN_POPULATION_REFERENCE * (self.POP_SCALE_FLOOR_SHARE
                                                  + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self.pop_scale))

    def population_report(self):
        """Everything the 'population' command (protocol.py) shows, worked
        out here rather than in the command layer: the country's own
        numbers (population, urban_fraction - already loaded for
        pop_scale, see core.py), the size of the one town this household
        actually reaches, and - per trade - the three-way comparison that
        is the whole point of this command: how many exist in the
        country, how many are within reach, how many you employ, and what
        share of the reachable pool that is.

        This has to say both at once: a bare "market can supply 22,500
        hours" says nothing about whether that is most of the trade or a
        rounding error against it, and leaves "the labour market is the
        size of a village" unanswered.
        """
        # self.population.total (the age-cohort model) is the direct
        # answer for `pop`, not a reconstruction-by-ratio (see
        # national_trade_population's own comment, just above).
        # `reference_pop`/`scale_from_baseline` are kept as the screen's
        # own "before simulated changes" comparison, not as inputs to
        # `pop`.
        reference_pop = float(self.civ.get("population", 0.0))
        pop = self.population.total
        scale_from_baseline = (pop / reference_pop) if reference_pop else 1.0
        urban_frac = float(self.civ.get("urban_fraction", 0.0))
        trades = []
        for trade in sorted(WAGES):
            national = self.national_trade_population(trade)
            reach = self.reachable_trade_population(trade) if self.trade_available(trade) else 0.0
            have = self.household.employees.get(trade, 0.0)
            trades.append({
                "trade": trade,
                "exists_here": self.trade_available(trade),
                "estimated_in_the_country": round(national, 1),
                "within_your_reach": round(reach, 2),
                "you_employ": round(have, 2),
                "share_of_the_reachable_pool_you_employ":
                    round(have / reach, 4) if reach > 1e-9 else None,
            })
        return {
            "civilisation": self.civ.get("name", self.civ.get("id", "")),
            "population": round(pop),
            "reference_population_before_simulated_changes": round(reference_pop),
            "population_change_from_reference": round(scale_from_baseline - 1.0, 4),
            "urban_fraction": round(urban_frac, 3),
            "urban_population_estimate": round(pop * urban_frac),
            "the_town_you_actually_operate_in": {
                "estimated_population": round(self.home_town_population_estimate()),
                "note": ("an ESTIMATE, not a place this game names: you are one "
                        "household drawing on one town's labour market, not the "
                        "whole of the country above - see what_this_means, below."),
            },
            "trades": trades,
            "what_this_means": (
                "Every hiring limit and every wage move in this game is sized "
                "to ONE household's reach into ONE town's labour market, not "
                "to the %s people counted above. A trade's 'within your "
                "reach' figure is what that market can actually supply you; "
                "'estimated in the country' is the whole civilisation's rough "
                "total, for scale. Both are explicit ESTIMATES, not a census - "
                "see labour.py's TRADE_DENSITY for what is cited and what is a "
                "placeholder. Buying people (a slave, a freedman) is bounded "
                "separately, by this household's own room to feed, house and "
                "supervise them ('labour' shows that ceiling) - NOT by how "
                "deep any market runs. One thing the two columns will look "
                "like they disagree about, and do not: for a SPECIALISED "
                "trade - an engraver, a glassblower, a millwright - the "
                "reachable figure is far tighter than the country total "
                "divided by the number of towns would suggest, because a "
                "specialist does not practise in every town and the ones who "
                "do are not all for hire. The common crafts are the ones "
                "sized straight off a town's own population."
                % "{:,.0f}".format(pop)),
        }