"""The year's dated hazards for every seat: each seat meets them with its own works, the world is hit once.

Per hazard: every seat resolves its causes and condition; seats lose staff, cash and sites by their own
exposure (own dice, own log); population, output, the coin and the society's values change once, at the
mildest figure any seat's works leave (sim/engine/hazard_merge.py). One seat runs the same draws in the same
order as a game with no other seat."""
from . import cause_book
from .data import money_word
from .hazard_merge import mildest_hazard


class ShockYearMixin:

    def _shocks(self, year, seats=None):
        """Dated catastrophes, read from the CIVILIZATION file, for `seats` (the seats still playing).

        One method per hazard kind, called in this order for every hazard whose window is open; the order
        fixes the sequence of self.rng draws, which save/load and the fingerprint depend on."""
        seats = list(self.playing_seats() if seats is None else seats)
        for hazard in self.civ.get("hazards", []):
            hazard_start, hazard_end = hazard.get("years", [0, 0])
            if not (hazard_start <= year <= hazard_end):
                continue
            met = {}
            for seat_id in seats:
                with self.act_as(seat_id):
                    kept = self._apply_event_causes(hazard, year, hazard_start)
                    if kept is not None:
                        kept = self._resolve_hazard_condition(kept, year, hazard_start)
                if kept is not None:
                    met[seat_id] = kept
            if not met:
                continue
            self._shock_staff_loss_seats(met, year)
            for seat_id in met:
                with self.act_as(seat_id):
                    self._shock_sack_chance(met[seat_id], year)
            self._shock_output_factor_seats(met, year)
            self._shock_real_erosion_seats(met, year)
            self._shock_values_seats(met, year, hazard_start, hazard_end)

    # ---- staff_loss: seats lose people and cash, the population is cut once -------------

    def _shock_staff_loss(self, hazard, year):
        """The acting seat alone meets a staff_loss hazard."""
        self._shock_staff_loss_seats({self.state.acting_seat: hazard}, year)

    def _shock_staff_loss_seats(self, met, year):
        if not any("staff_loss" in hazard for hazard in met.values()):
            return
        if not self.rng.random() < self.STAFF_LOSS_HAZARD_ANNUAL_CHANCE:
            return
        reports = {}
        for seat_id, hazard in met.items():
            if "staff_loss" in hazard:
                with self.act_as(seat_id):
                    reports[seat_id] = self._staff_loss_of_seat(hazard)
        world_hazard = mildest_hazard(met.values())
        raw = min(report["raw"] for report in reports.values())
        if world_hazard is not None and "staff_loss" in world_hazard:
            raw = self.staff_loss_exposure(world_hazard["staff_loss"])["before_defences"]
        wage_index_before = self.wage_index
        self._apply_population_mortality_shock(raw)
        for seat_id in reports:
            with self.act_as(seat_id):
                cause_book.record_wage_shock(self, met[seat_id].get("name", "a plague"), wage_index_before)
        # Refresh population and wage screens now, not at year end.
        self._refresh_demographic_indexes(year)
        for seat_id, report in reports.items():
            self.state.seats[seat_id].household.log.append((year, self._staff_loss_message(met[seat_id], report, raw)))

    def _staff_loss_of_seat(self, hazard):
        """What one wave takes from the acting seat's people and cash; returns the figures its message needs."""
        historical = hazard["staff_loss"]
        # National prevalence after the country's own medicine; the household is exposed to this, not to the
        # historical rate. Its own mitigations cut its risk only where the nation has not adopted them.
        exposure = self.staff_loss_exposure(historical)
        loss = exposure["loss"]
        household = self.state.household
        people_before = household.scholars + household.artisans + sum(household.employees.values())
        staff_before = self.labour.staff_snapshot()
        self.apply_staff_survival(1 - loss)
        household.directors_extra *= (1 - loss)
        self.labour.log_staff_reduction(hazard.get("name", "a plague"), staff_before)
        # Cash goes with the trade that stopped.
        cash = self.lose_capital(loss * self.PLAGUE_CASH_LOSS_SHARE, "plague losses")
        return {"historical": historical, "raw": exposure["before_defences"], "med_relief": exposure["national_relief"],
                "relief": exposure["relief"], "why": exposure["why"], "loss": loss, "cash": cash,
                "people_before": people_before}

    def _staff_loss_message(self, hazard, report, raw):
        """The log line for one seat; `raw` is the national toll the world took."""
        loss, why, relief, med_relief = report["loss"], report["why"], report["relief"], report["med_relief"]
        historical = report["historical"]
        hit = []
        if report["people_before"] > 0.05:
            if why and relief <= 0.25:
                hit.append("staff -%d%%, held off almost entirely by what you built (%s)" % (loss * 100, "; ".join(why)))
            elif why and relief <= 0.75:
                hit.append("staff -%d%% (softened by %s)" % (loss * 100, "; ".join(why)))
            else:
                hit.append("staff -%d%%" % (loss * 100))
        if report["cash"] > 0.5:
            hit.append("%s %s of takings lost while the trade stood idle"
                       % ("{:,.0f}".format(report["cash"]), money_word(self.civ)))
        if not hit:
            hit.append("you had nothing it could take")
        message = "%s: %s" % (hazard.get("name", "hazard"), ", ".join(hit))
        # Separate sentence so a spared household does not read the national toll as its own.
        if raw > 0.01:
            message += (". Empire-wide, population -%d%%%s - wages (and everything paid in them) stay dear until the "
                        "population does, either way"
                        % (raw * 100,
                           (" (the country's own public health has spread far enough to hold this below the "
                            "%d%% this would otherwise have been - %d%% softer; that is medical work you "
                            "built (%s) spreading through the country)"
                            % (round(historical * 100), round(med_relief * 100), self._national_sources_words()))
                           if med_relief > 0.02 else ""))
        elif med_relief > 0.02 and historical > 0.01:
            message += (". Empire-wide: the country's own public health (medical work you built: %s) has spread far "
                        "enough that this, historically a %d%% loss, barely registers"
                        % (self._national_sources_words(), round(historical * 100)))
        return message

    # ---- output_factor: war and its aftermath, the world's output floor ------------------

    def _shock_output_factor(self, hazard, year):
        self._shock_output_factor_seats({self.state.acting_seat: hazard}, year)

    def _shock_output_factor_seats(self, met, year):
        """Each seat's works set a floor the output factor falls to; the world takes the highest floor."""
        floors, reasons = {}, {}
        for seat_id, hazard in met.items():
            if "output_factor" in hazard:
                with self.act_as(seat_id):
                    relief, why = self.hazard_relief("output_factor")
                floors[seat_id] = self.output_floor(hazard["output_factor"], relief)
                reasons[seat_id] = why
        if not floors:
            return
        economy, scenario = self.state.economy, self.state.scenario
        before = economy.output_factor
        economy.output_factor = min(economy.output_factor, max(floors.values()))
        # Log only on first hit or after 20 years: avoid noise on recovery.
        said = scenario._said_output or {}
        name = next(hazard.get("name", "crisis") for hazard in met.values() if "output_factor" in hazard)
        if before > economy.output_factor and year - said.get(name, -99) >= 20:
            said[name] = year
            scenario._said_output = said
            for seat_id, why in reasons.items():
                self.state.seats[seat_id].household.log.append((year, "%s: trade and output fall to %d%% of normal%s" % (
                    name, economy.output_factor * 100,
                    " (your own strength holds off worse: %s)" % "; ".join(why[:3]) if why else "")))

    # ---- real_erosion: debasement, the coin once, each seat's held cash --------------------

    def _shock_real_erosion(self, hazard, year):
        self._shock_real_erosion_seats({self.state.acting_seat: hazard}, year)

    def _shock_real_erosion_seats(self, met, year):
        holders = {seat_id: hazard for seat_id, hazard in met.items() if "real_erosion" in hazard}
        if not holders:
            return
        economy, scenario = self.state.economy, self.state.scenario
        world_hazard = mildest_hazard(met.values())
        if world_hazard is not None and "real_erosion" in world_hazard:
            economy.money_real *= (1 - world_hazard["real_erosion"])
        lines = {}
        for seat_id, hazard in holders.items():
            with self.act_as(seat_id):
                relief, why = self.hazard_relief("real_erosion")
                household = self.state.household
                bite = hazard["real_erosion"] * self.REAL_EROSION_CASH_LOSS_SHARE * relief
                had = max(0.0, household.capital)
                self.lose_capital(bite, "debasement and real erosion")
                lines[seat_id] = (hazard, why, had - max(0.0, household.capital))
        if not scenario._said_debasement or year - scenario._said_debasement >= 15:
            scenario._said_debasement = year
            for seat_id, (hazard, why, lost) in lines.items():
                # Report the money lost held, not quoted costs (which reflect reality).
                self.state.seats[seat_id].household.log.append((year, "%s: the coin is worth %d%% less than it "
                    "was%s. Quoted costs are what a thing really takes to make, so they do not move; what debases "
                    "is the money in your chest, and this year it took %s%s"
                    % (hazard.get("name", "debasement"), (1 - economy.money_real) * 100,
                       "; you feel less of it (%s)" % "; ".join(why) if why else "",
                       "{:,.0f}".format(lost) if lost > 0.5 else "nothing, because you were holding none",
                       " denarii" if lost > 0.5 else "")))

    # ---- values: the society's beliefs shift once -------------------------------------------

    def _shock_values(self, hazard, year, hazard_start, hazard_end):
        self._shock_values_seats({self.state.acting_seat: hazard}, year, hazard_start, hazard_end)

    def _shock_values_seats(self, met, year, hazard_start, hazard_end):
        """Gradual shifts in what the society believes, spread evenly across the hazard's own window."""
        hazard = mildest_hazard(met.values())
        if hazard is None or "values" not in hazard:
            return
        span = max(1, int(hazard_end) - int(hazard_start) + 1)
        changed = {}
        for field, total_delta in hazard["values"].items():
            if field.startswith("_") or not isinstance(total_delta, (int, float)):
                continue
            if field not in self.value_weights:
                continue
            before = self.value_weights[field]
            self.value_weights[field] = max(self.VALUE_WEIGHT_FLOOR,
                                            min(self.VALUE_WEIGHT_CEILING, before + total_delta / span))
            if abs(self.value_weights[field] - before) > 1e-9:
                changed[field] = self.value_weights[field]
        # Log at start, end, and every 10 years: visible change without noise.
        if changed and (year == hazard_start or year == hazard_end or (year - hazard_start) % 10 == 0):
            line = "%s: the society's values are shifting (%s)" % (
                hazard.get("name", "hazard"), ", ".join("%s now %.2f" % (field, value) for field, value in sorted(changed.items())))
            for seat_id in met:
                self.state.seats[seat_id].household.log.append((year, line))
