"""What finishing a piece of work actually does.

_complete() is the single largest method in projects.py's original file
(see that file's own docstring for why this lives separately) - what a
finished (or, on the risk roll, a failed) attempt does to `done`, tech
effects, standing, scandal, state interest, and the staff a handful of
institutions grant on completion. The HAZARD_COUNTERS table that follows it
in the class body is a distinct but related subject: it is not read by
_complete() itself, but by society_hazards.py's `_shocks` (self.HAZARD_
COUNTERS - see that file), and it lists exactly the completed technologies
that blunt a hazard's effect, so it belongs beside the other consequence of
having finished something rather than in any of this split's other files.

These are methods of Sim; they are a mixin only so that they can live in a
file of their own.
"""
from constants import declare


class CompletionMixin:
    FAILURE_RESET_SHARE = declare(
        "FAILURE_RESET_SHARE", 0.4, kind="temporary_heuristic",
        unit="fraction of founder-hours and of total cost", source=None,
        confidence="D",
        why="What a failed attempt costs and leaves still to do: forty "
            "per cent of the node's founder-hours are to do again, and "
            "forty per cent of its total cost (money-scaled) is lost - "
            "the SAME figure used for both, and used again to build the "
            "log message's own '%d%%' so the number cannot drift from "
            "what the arithmetic actually charges (see this method's own "
            "comment on the '40, NOT 60' bug, where the message once said "
            "sixty while the code charged forty). Tuned penalty, not "
            "measured against any real cost of a failed technical "
            "programme.")
    REPUTATION_GAIN_BASE = declare(
        "REPUTATION_GAIN_BASE", 0.6, kind="temporary_heuristic",
        unit="reputation points, per completed technology", source=None,
        confidence="D",
        why="The baseline standing any completed technology earns, before "
            "state interest or visible revenue add anything further. "
            "Tuned game balance, not measured.")
    REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT = declare(
        "REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT", 0.5, kind="temporary_heuristic",
        unit="reputation points per point of positive state_interest",
        source=None, confidence="D",
        why="How much extra standing a technology the state actually "
            "welcomes earns, on top of REPUTATION_GAIN_BASE - only the "
            "positive side of state_interest counts here (state "
            "opposition is priced elsewhere, in start_reason's own "
            "gates, not by shrinking a reward). Tuned, not measured.")
    REPUTATION_GAIN_REVENUE_BONUS = declare(
        "REPUTATION_GAIN_REVENUE_BONUS", 1.2, kind="temporary_heuristic",
        unit="reputation points, if the node earns any revenue",
        source=None, confidence="D",
        why="Visible, useful, revenue-earning work builds standing faster "
            "than obscure laboratory work of equal difficulty - a real "
            "and annoying fact about how credibility accrues (this "
            "method's own comment), captured here as a flat bonus rather "
            "than a function of the revenue's actual size. Tuned, not "
            "measured.")
    REPUTATION_CEILING = declare(
        "REPUTATION_CEILING", 100.0, kind="temporary_heuristic",
        unit="reputation points", source=None, confidence="D",
        why="The top of the reputation scale this engine uses throughout "
            "(REPUTATION_EASE_SCALE in economy.py reads reputation "
            "against this same implicit ceiling). A scale choice, not a "
            "measured social fact.")
    GRANT_STAFF_FREEDMAN_ARTISANS = declare(
        "GRANT_STAFF_FREEDMAN_ARTISANS", 8, kind="temporary_heuristic",
        unit="artisans, granted once on completion", source=None,
        confidence="D",
        why="How many artisans a freedman staff hands over outright on "
            "completion, when auto_hire is off (a manual player's own "
            "mode) - a ONE-TIME grant, distinct from labour.py's "
            "STAFF_ARTISANS_FREEDMAN_STAFF (the ongoing institutional "
            "ceiling that same node also feeds; the two figures are not "
            "required to match and do not). Declared as the INT the "
            "source wrote: _grant_staff adds it straight into a float "
            "accumulator, so nothing downstream needs it to already be a "
            "float, and there is no reason to widen it. Tuned game "
            "balance, not measured.")
    GRANT_STAFF_SCHOOL_SCHOLARS = declare(
        "GRANT_STAFF_SCHOOL_SCHOLARS", 4, kind="temporary_heuristic",
        unit="scholars, granted once on completion", source=None,
        confidence="D",
        why="As GRANT_STAFF_FREEDMAN_ARTISANS, for school_founded's "
            "one-time scholar grant.")
    GRANT_STAFF_ACADEMY_SCHOLARS = declare(
        "GRANT_STAFF_ACADEMY_SCHOLARS", 10, kind="temporary_heuristic",
        unit="scholars, granted once on completion", source=None,
        confidence="D",
        why="As GRANT_STAFF_FREEDMAN_ARTISANS, for academy_network's "
            "one-time scholar grant.")
    GRANT_STAFF_ACADEMY_ARTISANS = declare(
        "GRANT_STAFF_ACADEMY_ARTISANS", 10, kind="temporary_heuristic",
        unit="artisans, granted once on completion", source=None,
        confidence="D",
        why="As GRANT_STAFF_FREEDMAN_ARTISANS, for academy_network's "
            "one-time artisan grant.")

    def _complete(self, node_id):
        node = self.nodes[node_id]
        _risk_this_attempt = self.effective_risk(node_id)
        if self.rng.random() < _risk_this_attempt:
            _yrs_before = self.household.active[node_id]["yrs"]
            self.household.failed_attempts[node_id] += 1
            self.household.active[node_id]["ph_left"] = node["ph"] * self.FAILURE_RESET_SHARE
            # THE CALENDAR CLOCK IS NOT WIPED: a failed attempt must not
            # reset the multi-year diffusion clock to zero, restarting the
            # whole process from nothing. Even ONE failed attempt already
            # does real social groundwork (workshops retooled, a workforce
            # that has seen it once, a regulator who already sat through
            # the pitch), so the first failure already banks a real share
            # of the elapsed clock, not zero - it is the risk term above,
            # not this one, that has nothing to show after only one
            # failure. What this banks keeps growing, with diminishing
            # returns, as failed_attempts[node_id] grows, and is capped well
            # short of the whole clock (RETRY_CALENDAR_CAP) so a retried
            # programme is only ever readier, never instantly ready.
            _retain = self._retry_calendar_retain(node_id)
            self.household.active[node_id]["yrs"] = _yrs_before * _retain
            _lost = node["_total_cost"] * self.FAILURE_RESET_SHARE * self.cost_money_factor()
            self.household.capital -= _lost
            # SAY SO: a failed attempt must announce itself in the log - a
            # cost you cannot see is a cost nobody is paying attention to,
            # which is the same as not charging it.
            # THE LOGGED PERCENTAGE MUST MATCH WHAT WAS ACTUALLY CHARGED:
            # ph_left is set to FAILURE_RESET_SHARE of the FULL hours, so
            # the message has to build its own percentage from that same
            # constant rather than a separately hardcoded number that can
            # drift out of sync with it.
            # AND NOW SAY WHAT WAS LEARNED, in the same breath as the loss -
            # a player who has just been told a program failed should also be
            # told, in the same sentence, that the next attempt is not a
            # repeat of this one: the engineering is better understood
            # (chance of failure quoted for next time) and some of the
            # groundwork survives (years already banked toward the next
            # attempt's own floor).
            _next_risk = self.effective_risk(node_id)
            _banked = self.household.active[node_id]["yrs"]
            self.household.log.append((self.year,
                             "FAILED at %s: it did not work. %d%% of the hours "
                             "are to do again (%s of your own) and %s is gone. "
                             "Attempt %d. What went wrong is now understood well "
                             "enough that the next attempt's chance of failing "
                             "this way is %d%%, down from the %d%% this attempt "
                             "just faced, and %.1f of the %.1f years already "
                             "spent count toward next time's wait."
                             % (node["name"], round(self.FAILURE_RESET_SHARE * 100),
                                "{:,.0f}".format(node["ph"] * self.FAILURE_RESET_SHARE),
                                "{:,.0f}".format(max(0.0, _lost)),
                                self.household.failed_attempts[node_id] + 1,
                                round(_next_risk * 100),
                                round(_risk_this_attempt * 100),
                                _banked, _yrs_before)))
            return
        del self.household.active[node_id]
        self.household.bountied.discard(node_id)
        # A FINISHED PROJECT CANNOT BE GIVEN MORE HOURS. Unlike stopping or
        # halting one - both of which carry what was already paid forward
        # if the player starts the same id again, see start_project's own
        # `_paid_now` - there is no "again" once it is done, so a standing
        # order aimed at this id would otherwise sit in `allocate`'s list
        # for ever, pointed at nothing.
        self.household.hour_allocations.pop(node_id, None)
        self.household.done.add(node_id)
        self._done_changed()
        self.household.done_year[node_id] = self.year
        # A technology changes the society that built it. Only for work YOU
        # completed: a society is not altered by owning something it always had.
        self.apply_tech_effects(node_id)
        self.reveal_from(node_id)
        # Visible, useful, State-approved work builds standing. Obscure laboratory
        # work does not, however important it is, which is a real and annoying fact
        # about how credibility actually accrues.
        gain = (self.REPUTATION_GAIN_BASE
                + self.REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT * max(0.0, self.state_interest(node))
                + (self.REPUTATION_GAIN_REVENUE_BONUS if node["rev"] > 0 else 0.0))
        self.household.reputation = min(self.REPUTATION_CEILING, self.household.reputation + gain)
        self.household.scandal += self.alarm_of(node)
        self.household.gov += self.state_interest(node)
        # _grant_staff, NOT a bare += on self.household.scholars/self.household.artisans:
        # _resync_pools(), which step() calls unconditionally every year,
        # always treats self.household.scholars and self.household.artisans
        # as computed purely from self.household.employees, so a bare
        # direct addition here would be overwritten out of existence the
        # very next time it runs. See _grant_staff.
        #
        # ONLY WITHOUT auto_hire: with it on - the optimizer's default, off
        # for a player - staff_capacity() already counts this same
        # institution toward sc_cap/ar_cap and step()'s smoothing grows
        # self.household.scholars/self.household.artisans toward that ceiling on its own; the
        # long civilization runs are calibrated against that smoothing alone
        # (see core.py, "1. staff"). Granting it a second time here as well
        # would double-count every one of these three institutions against
        # a tree calibrated to open up much more slowly.
        if not self.policy.get("auto_hire", not self.manual):
            if node_id == "freedman_staff":     self._grant_staff(artisans=self.GRANT_STAFF_FREEDMAN_ARTISANS)
            if node_id == "school_founded":     self._grant_staff(scholars=self.GRANT_STAFF_SCHOOL_SCHOLARS)
            if node_id == "academy_network":    self._grant_staff(scholars=self.GRANT_STAFF_ACADEMY_SCHOLARS,
                                                              artisans=self.GRANT_STAFF_ACADEMY_ARTISANS)
        if node_id == "mining_concession":  pass
        # SAY THAT IT IS NOT YET RUNNING: completing something that could be
        # a going concern does not start it earning, and a player who is
        # not told will reasonably conclude the money is broken rather
        # than that they have not opened the doors.
        if self.is_venture(node_id) and not self.policy.get("auto_open", not self.manual):
            self.household.log.append((self.year, "completed: %s. You know how; nothing "
                                        "is earning yet - 'open %s' to run it"
                                        % (node["name"], node_id)))
        else:
            self.household.log.append((self.year, "completed: " + node["name"]))
        if node_id == self.goal and self.household.goal_year is None:
            self.household.goal_year = self.year

    # -- shocks -------------------------------------------------------------
    # WHAT YOU CAN DO ABOUT HISTORY.
    #
    # A game that tells you on turn one exactly which disasters are coming
    # has to let some completed technologies counter them - a mine that
    # arms Rome against a raid, a medicine that blunts a plague - findably,
    # not as hardcoded checks nowhere the player can see. Hazards are not
    # weather. They are the thing the whole programme is for.
    #
    # Each entry is (node id, how much of the harm it removes, what it is).
    # They compound, and none of them takes a hazard to zero on its own: no
    # amount of sanitation stops a plague, it decides how many of your people
    # are still alive at the end of it.
    _HAZARD_COUNTER_WHY = (
        "How much of this hazard one mitigating technology removes, "
        "compounding with every other counter for the same hazard and "
        "never reaching zero on its own (no amount of sanitation stops a "
        "plague; it decides how many people are still alive after). The "
        "MECHANISM this technology relieves this hazard through is real "
        "and named at its own declaration; the specific fraction removed "
        "is tuned game balance sized so the hazard remains real even "
        "fully countered, not measured against any historical mortality, "
        "sack or currency-debasement reduction.")
    HAZARD_STAFF_LOSS_SANITATION_ANTISEPSIS = declare(
        "HAZARD_STAFF_LOSS_SANITATION_ANTISEPSIS", 0.30, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="boiled water, handwashing, clean wounds", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_MED_QUARANTINE_SANITATION = declare(
        "HAZARD_STAFF_LOSS_MED_QUARANTINE_SANITATION", 0.30, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="quarantine, clean water, sewage", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_GERM_THEORY = declare(
        "HAZARD_STAFF_LOSS_GERM_THEORY", 0.25, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="knowing what is actually killing them", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_MD2_ISOLATION_HOSPITAL = declare(
        "HAZARD_STAFF_LOSS_MD2_ISOLATION_HOSPITAL", 0.20, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="the sick kept apart from the well", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_MED_VACCINATION_PROGRESSION = declare(
        "HAZARD_STAFF_LOSS_MED_VACCINATION_PROGRESSION", 0.45, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="variolation and then vaccination", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_MD2_VACCINE_SMALLPOX = declare(
        "HAZARD_STAFF_LOSS_MD2_VACCINE_SMALLPOX", 0.40, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="smallpox vaccine", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_MD2_VACCINE_PLAGUE = declare(
        "HAZARD_STAFF_LOSS_MD2_VACCINE_PLAGUE", 0.35, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="plague vaccine", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_MD2_VACCINE_TYPHOID = declare(
        "HAZARD_STAFF_LOSS_MD2_VACCINE_TYPHOID", 0.20, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="typhoid vaccine", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_MD2_SAND_FILTRATION = declare(
        "HAZARD_STAFF_LOSS_MD2_SAND_FILTRATION", 0.15, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="filtered water", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_SOAP_HARD = declare(
        "HAZARD_STAFF_LOSS_SOAP_HARD", 0.10, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="hard soap, in quantity", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_MED_NURSING_PROFESSION = declare(
        "HAZARD_STAFF_LOSS_MED_NURSING_PROFESSION", 0.12, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="people trained to nurse the sick", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_PLAGUE_PREPAREDNESS = declare(
        "HAZARD_STAFF_LOSS_PLAGUE_PREPAREDNESS", 0.35, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="a plan made before the plague", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_CROP_ROTATION = declare(
        "HAZARD_STAFF_LOSS_CROP_ROTATION", 0.15, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="fields that do not fail together", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_AG2_SILAGE_SILO = declare(
        "HAZARD_STAFF_LOSS_AG2_SILAGE_SILO", 0.10, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="fodder that keeps through a bad winter", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_STAFF_LOSS_FUD_CANNING_APPERT_METHOD = declare(
        "HAZARD_STAFF_LOSS_FUD_CANNING_APPERT_METHOD", 0.10, kind="temporary_heuristic",
        unit="fraction of staff-loss hazard removed",
        source="food that keeps", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_MIL_TRACE_ITALIENNE = declare(
        "HAZARD_SACK_MIL_TRACE_ITALIENNE", 0.45, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="angled bastion walls no ram or ladder answers",
        confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_MIL_BASTION = declare(
        "HAZARD_SACK_MIL_BASTION", 0.30, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="a bastioned enclosure", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_MIL_CONCRETE_FORTIFICATION = declare(
        "HAZARD_SACK_MIL_CONCRETE_FORTIFICATION", 0.30, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="concrete fortification", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_MIL_MATCHLOCK = declare(
        "HAZARD_SACK_MIL_MATCHLOCK", 0.25, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="firearms in the hands of your own people", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_MIL_FLINTLOCK = declare(
        "HAZARD_SACK_MIL_FLINTLOCK", 0.35, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="reliable firearms", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_MIL_ARTILLERY_PIECE = declare(
        "HAZARD_SACK_MIL_ARTILLERY_PIECE", 0.30, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="guns on the walls", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_GUNPOWDER = declare(
        "HAZARD_SACK_GUNPOWDER", 0.15, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="corned powder", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_PATRON_IMPERIAL = declare(
        "HAZARD_SACK_PATRON_IMPERIAL", 0.30, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="a patron with soldiers", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_ACADEMY_NETWORK = declare(
        "HAZARD_SACK_ACADEMY_NETWORK", 0.40, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="the work is in too many places to burn", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_SACK_ENDOWMENT_LAND = declare(
        "HAZARD_SACK_ENDOWMENT_LAND", 0.15, kind="temporary_heuristic",
        unit="fraction of sack-chance hazard removed",
        source="land nobody can carry away", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_OUTPUT_ENDOWMENT_LAND = declare(
        "HAZARD_OUTPUT_ENDOWMENT_LAND", 0.30, kind="temporary_heuristic",
        unit="fraction of output-factor hazard removed",
        source="land that yields whoever is emperor this year",
        confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_OUTPUT_CROP_ROTATION = declare(
        "HAZARD_OUTPUT_CROP_ROTATION", 0.20, kind="temporary_heuristic",
        unit="fraction of output-factor hazard removed",
        source="you feed yourself", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_OUTPUT_WATER_POWER_SCALE = declare(
        "HAZARD_OUTPUT_WATER_POWER_SCALE", 0.20, kind="temporary_heuristic",
        unit="fraction of output-factor hazard removed",
        source="power that does not come by ship", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_OUTPUT_CIV_ROAD_PAVED = declare(
        "HAZARD_OUTPUT_CIV_ROAD_PAVED", 0.10, kind="temporary_heuristic",
        unit="fraction of output-factor hazard removed",
        source="your own roads", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_OUTPUT_FIN_MARINE_INSURANCE = declare(
        "HAZARD_OUTPUT_FIN_MARINE_INSURANCE", 0.15, kind="temporary_heuristic",
        unit="fraction of output-factor hazard removed",
        source="losses spread rather than borne", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_EROSION_OWN_GOLD = declare(
        "HAZARD_EROSION_OWN_GOLD", 0.55, kind="temporary_heuristic",
        unit="fraction of real-erosion hazard removed",
        source="your own gold, dug not minted", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_EROSION_OWN_SILVER = declare(
        "HAZARD_EROSION_OWN_SILVER", 0.35, kind="temporary_heuristic",
        unit="fraction of real-erosion hazard removed",
        source="your own silver", confidence="D", why=_HAZARD_COUNTER_WHY)
    HAZARD_EROSION_ENDOWMENT_LAND = declare(
        "HAZARD_EROSION_ENDOWMENT_LAND", 0.40, kind="temporary_heuristic",
        unit="fraction of real-erosion hazard removed",
        source="wealth held as land, not as coin", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_EROSION_FIN_BIMETALLISM = declare(
        "HAZARD_EROSION_FIN_BIMETALLISM", 0.25, kind="temporary_heuristic",
        unit="fraction of real-erosion hazard removed",
        source="a standard the coin can be held to", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_EROSION_FIN_ASSAY_OFFICE = declare(
        "HAZARD_EROSION_FIN_ASSAY_OFFICE", 0.20, kind="temporary_heuristic",
        unit="fraction of real-erosion hazard removed",
        source="you can prove what metal is in a coin", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_EROSION_MET_FIRE_ASSAY = declare(
        "HAZARD_EROSION_MET_FIRE_ASSAY", 0.15, kind="temporary_heuristic",
        unit="fraction of real-erosion hazard removed",
        source="you can assay ore and coin yourself", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_COUNTERS = {
        "staff_loss": [
            ("sanitation_antisepsis", HAZARD_STAFF_LOSS_SANITATION_ANTISEPSIS, "boiled water, handwashing, clean wounds"),
            ("med_quarantine_sanitation", HAZARD_STAFF_LOSS_MED_QUARANTINE_SANITATION, "quarantine, clean water, sewage"),
            ("germ_theory", HAZARD_STAFF_LOSS_GERM_THEORY, "knowing what is actually killing them"),
            ("md2_isolation_hospital", HAZARD_STAFF_LOSS_MD2_ISOLATION_HOSPITAL, "the sick kept apart from the well"),
            ("med_vaccination_progression", HAZARD_STAFF_LOSS_MED_VACCINATION_PROGRESSION, "variolation and then vaccination"),
            ("md2_vaccine_smallpox", HAZARD_STAFF_LOSS_MD2_VACCINE_SMALLPOX, "smallpox vaccine"),
            ("md2_vaccine_plague", HAZARD_STAFF_LOSS_MD2_VACCINE_PLAGUE, "plague vaccine"),
            ("md2_vaccine_typhoid", HAZARD_STAFF_LOSS_MD2_VACCINE_TYPHOID, "typhoid vaccine"),
            ("md2_sand_filtration", HAZARD_STAFF_LOSS_MD2_SAND_FILTRATION, "filtered water"),
            ("soap_hard", HAZARD_STAFF_LOSS_SOAP_HARD, "hard soap, in quantity"),
            ("med_nursing_profession", HAZARD_STAFF_LOSS_MED_NURSING_PROFESSION, "people trained to nurse the sick"),
            ("plague_preparedness", HAZARD_STAFF_LOSS_PLAGUE_PREPAREDNESS, "a plan made before the plague"),
            ("crop_rotation", HAZARD_STAFF_LOSS_CROP_ROTATION, "fields that do not fail together"),
            ("ag2_silage_silo", HAZARD_STAFF_LOSS_AG2_SILAGE_SILO, "fodder that keeps through a bad winter"),
            ("fud_canning_appert_method", HAZARD_STAFF_LOSS_FUD_CANNING_APPERT_METHOD, "food that keeps"),
        ],
        "sack_chance": [
            ("mil_trace_italienne", HAZARD_SACK_MIL_TRACE_ITALIENNE, "angled bastion walls no ram or ladder answers"),
            ("mil_bastion", HAZARD_SACK_MIL_BASTION, "a bastioned enclosure"),
            ("mil_concrete_fortification", HAZARD_SACK_MIL_CONCRETE_FORTIFICATION, "concrete fortification"),
            ("mil_matchlock", HAZARD_SACK_MIL_MATCHLOCK, "firearms in the hands of your own people"),
            ("mil_flintlock", HAZARD_SACK_MIL_FLINTLOCK, "reliable firearms"),
            ("mil_artillery_piece", HAZARD_SACK_MIL_ARTILLERY_PIECE, "guns on the walls"),
            ("gunpowder", HAZARD_SACK_GUNPOWDER, "corned powder"),
            ("patron_imperial", HAZARD_SACK_PATRON_IMPERIAL, "a patron with soldiers"),
            ("academy_network", HAZARD_SACK_ACADEMY_NETWORK, "the work is in too many places to burn"),
            ("endowment_land", HAZARD_SACK_ENDOWMENT_LAND, "land nobody can carry away"),
        ],
        "output_factor": [
            ("endowment_land", HAZARD_OUTPUT_ENDOWMENT_LAND, "land that yields whoever is emperor this year"),
            ("crop_rotation", HAZARD_OUTPUT_CROP_ROTATION, "you feed yourself"),
            ("water_power_scale", HAZARD_OUTPUT_WATER_POWER_SCALE, "power that does not come by ship"),
            ("civ_road_paved", HAZARD_OUTPUT_CIV_ROAD_PAVED, "your own roads"),
            ("fin_marine_insurance", HAZARD_OUTPUT_FIN_MARINE_INSURANCE, "losses spread rather than borne"),
        ],
        "real_erosion": [
            ("_own_gold", HAZARD_EROSION_OWN_GOLD, "your own gold, dug not minted"),
            ("_own_silver", HAZARD_EROSION_OWN_SILVER, "your own silver"),
            ("endowment_land", HAZARD_EROSION_ENDOWMENT_LAND, "wealth held as land, not as coin"),
            ("fin_bimetallism", HAZARD_EROSION_FIN_BIMETALLISM, "a standard the coin can be held to"),
            ("fin_assay_office", HAZARD_EROSION_FIN_ASSAY_OFFICE, "you can prove what metal is in a coin"),
            ("met_fire_assay", HAZARD_EROSION_MET_FIRE_ASSAY, "you can assay ore and coin yourself"),
        ],
    }
