"""Cash Shelter: lodge coin with a holder elsewhere, so a disaster that takes the founder's purse cannot take it.

Every hazard in the engine takes a share of the acting household's own purse (`capital`), plus, for a sack or
banditry, the portable share of its goods. Coin lodged with another actor through the ledger is not in that purse.
The holder is an ordinary actor with a purse of its own, so it pays the engine's guard cost on its coin and meets the
engine's theft on it, and it has a labelled chance of its own failure. A deposit is a claim on the holder's purse:
fees are taken from the claim, and a holder whose purse has fallen below its claims pays out pro rata.
"""
import json
import os

from sim.agents.api import ActorRecord, RecordedActor, edges, ledger

HERE = os.path.dirname(os.path.abspath(__file__))
FAILURE_CAUSE = "holder looted"
DEPOSIT_CAUSE = "coin lodged with a holder"
PAYOUT_CAUSE = "coin repaid by a holder"
CARRY_CAUSE = "carrying coin to or from a holder"
LETTER_CAUSE = "letter of credit honoured"
MAX_YEARS_SETTLED = 400


def _load_types():
    with open(os.path.join(HERE, "holder_types.json"), encoding="utf-8") as source:
        return json.load(source)


class Holder(RecordedActor):
    """A custodian: keeps coin for others and may fail. Its guard cost and theft come from the engine's yearly
    charges on every actor's purse; the failure draw is its own."""
    kind = "holder"
    declaration = {}

    def imitation_candidates(self, world):
        return []

    def imitation_worth(self, node_id, world):
        return 0.0

    def learn(self, chain, world):
        """A holder keeps no research tree."""

    def advance(self, world):
        declaration = self.declaration
        chance = float(declaration["failure_chance_per_year"])
        if chance <= 0.0 or self.money <= 0.0:
            return
        roll = world.rng_for(world.year, "cash_shelter_failure", self.actor_id)
        if roll.random() < chance:
            lost = self.money * float(declaration["failure_loss_share"])
            ledger.transfer(self, world.edge(edges.EDGE_THIEVES), lost, FAILURE_CAUSE)
            self.record.cause = "looted in year %d" % world.year
            self.record.last_logged_year = world.year


def register(api):
    types = _load_types()
    holders = types["holders"]
    letter_fee = float(types["letter_of_credit"]["fee_share_of_amount"])
    for name, declaration in holders.items():
        api.actor_kind(name, type("Holder", (Holder,), {"kind": api.qualified(name), "declaration": declaration}))

    def holder_id(name):
        return api.qualified("holder_" + name)

    def memory(sim):
        mod_state = api.state(sim.state.interface)
        return mod_state.setdefault("claims", {})   # holder name -> seat id -> {"amount", "settled_year"}

    def claim_of(sim, name, seat):
        return memory(sim).get(name, {}).get(seat)

    def total_claims(sim, name):
        return sum(entry["amount"] for entry in memory(sim).get(name, {}).values())

    def holder_actor(sim, name):
        return sim.view("cast")().get(holder_id(name))

    def ensure_holder(sim, name):
        actor = holder_actor(sim, name)
        if actor is None:
            actor = sim.view("cast")().add(holder_id(name), ActorRecord(
                kind=api.qualified(name), name=holders[name]["label"], founded_year=sim.year))
        return actor

    def solvency(sim, name):
        """Share of what it owes the holder could pay today from its purse (1 when it can pay all)."""
        actor = holder_actor(sim, name)
        owed = total_claims(sim, name)
        if actor is None or owed <= 0.0:
            return 1.0
        return max(0.0, min(1.0, actor.money / owed))

    def yearly_cost(sim, name, amount):
        """The holder's own yearly cost of keeping `amount` of coin: the engine's guard cost plus the engine's
        expected theft on it, at the holder's own visibility."""
        from sim.coin.api import COIN_GUARD_HOURS_PER_TONNE_YEAR, theft_exposure
        actor = holder_actor(sim, name)
        scale = sim.view("visible_scale")(sum(actor.workforce.values()), actor.money, actor.prominence(), 0.0) if actor else 0.0
        stolen = theft_exposure.expected_theft_loss(
            {"coin": amount}, {"coin": COIN_GUARD_HOURS_PER_TONNE_YEAR}, scale, sim.state_capacity, 0.0)
        return sim.view("coin_keeping_cost")(amount) + stolen

    def settle(sim, name, seat):
        """Take the custody fee for each year since the claim was last settled, from the claim itself."""
        entry = claim_of(sim, name, seat)
        if entry is None:
            return 0.0
        years = max(0, min(MAX_YEARS_SETTLED, sim.year - entry["settled_year"]))
        markup = float(holders[name]["custody_markup"])
        charged = 0.0
        for _ in range(years):
            fee = min(entry["amount"], yearly_cost(sim, name, entry["amount"]) * (1.0 + markup))
            entry["amount"] -= fee
            charged += fee
        entry["settled_year"] = sim.year
        return charged

    def carry_cost(sim, name, amount):
        tonnes = max(0.0, amount) * sim.view("coin_kg_per_unit")() / 1000.0
        return tonnes * float(holders[name]["carry_hours_per_tonne"]) * sim.labour.money_per_labour_hour()

    def arguments(cmd):
        words = str(cmd.get("text") or "").split()
        names = [word for word in words if word in holders]
        amounts = [word for word in words if word not in holders]
        for key in ("holder", "from", "to"):
            if cmd.get(key) and str(cmd[key]) not in names:
                names.append(str(cmd[key]))
        if cmd.get("amount") is not None:
            amounts = [str(cmd["amount"])]
        return names, amounts

    def amount_of(words, available):
        if not words:
            return None, "name an amount, or 'all'"
        word = words[-1].replace(",", "")
        if word.lower() == "all":
            return available, None
        try:
            value = float(word)
        except ValueError:
            return None, "%r is not an amount" % words[-1]
        return (value, None) if value > 0.0 else (None, "the amount must be greater than zero")

    def refuse(message, **fields):
        return dict({"ok": False, "error": message + " Nothing was changed."}, **fields)

    def choices():
        return sorted(holders)

    def stopped(ended):
        return refuse("the run has ended (%s)." % ended) if ended else None

    @api.command("deposit", group="money", summary="lodge coin with a holder elsewhere, out of reach of your own disasters",
                 usage=["bh_cashshelter_z6f2:deposit <holder> <amount|all>"],
                 options={"<holder>": "strongroom or merchant_house (see the exposure command)", "<amount>": "coin to lodge"},
                 description="Moves coin from your purse to the holder's purse through the ledger. Carrying it there costs "
                             "porters' and escorts' hours; keeping it costs a yearly fee taken from your claim; the holder "
                             "can lose coin to theft and fail, and then repays only what its purse can pay. A fire, a sack, "
                             "banditry, a plague or a treasury demand take from your own purse, not from the holder's.",
                 shape="text")
    def deposit(sim, nodes, cmd, ended):
        problem = stopped(ended)
        if problem:
            return problem
        names, amounts = arguments(cmd)
        if len(names) != 1 or names[0] not in holders:
            return refuse("name one holder.", choices=choices())
        name = names[0]
        household = sim.state.household
        carry_rate = carry_cost(sim, name, 1.0)
        amount, error = amount_of(amounts, max(0.0, household.capital) / (1.0 + carry_rate))
        if error:
            return refuse(error + ".")
        carry = carry_cost(sim, name, amount)
        if amount + carry > household.capital:
            return refuse("you hold %.0f; lodging %.0f also costs %.0f to carry." % (household.capital, amount, carry))
        holder = ensure_holder(sim, name)
        seat = sim.state.acting_seat
        settle(sim, name, seat)
        ledger.transfer(household, sim.view("legacy_edge_account")[edges.EDGE_COIN_GUARDS], carry, CARRY_CAUSE)
        ledger.transfer(household, holder, amount, DEPOSIT_CAUSE)
        entry = memory(sim).setdefault(name, {}).setdefault(seat, {"amount": 0.0, "settled_year": sim.year})
        entry["amount"] += amount
        return {"ok": True, "holder": name, "lodged": round(amount, 1), "carriage": round(carry, 1),
                "claim": round(entry["amount"], 1), "capital": round(household.capital, 1)}

    @api.command("withdraw", group="money", summary="draw coin back from a holder",
                 usage=["bh_cashshelter_z6f2:withdraw <holder> <amount|all>"],
                 options={"<holder>": "the holder", "<amount>": "claim to draw; the holder pays only what its purse can"},
                 description="Settles the custody fees owed, then asks the holder to pay. A holder whose purse is short of "
                             "everything it owes pays each claim in the same share, and the rest of the claim is lost. "
                             "Bringing the coin home costs the same carriage as taking it there.",
                 shape="text")
    def withdraw(sim, nodes, cmd, ended):
        problem = stopped(ended)
        if problem:
            return problem
        names, amounts = arguments(cmd)
        if len(names) != 1 or names[0] not in holders:
            return refuse("name one holder.", choices=choices())
        name, seat = names[0], sim.state.acting_seat
        entry = claim_of(sim, name, seat)
        if entry is None or entry["amount"] <= 0.0:
            return refuse("you have no claim on %s." % name)
        fees = settle(sim, name, seat)
        amount, error = amount_of(amounts, entry["amount"])
        if error:
            return refuse(error + ".")
        asked = min(amount, entry["amount"])
        share = solvency(sim, name)
        holder = holder_actor(sim, name)
        paid = min(asked * share, max(0.0, holder.money))
        household = sim.state.household
        if paid > 0.0:
            ledger.transfer(holder, household, paid, PAYOUT_CAUSE)
            ledger.transfer(household, sim.view("legacy_edge_account")[edges.EDGE_COIN_GUARDS], carry_cost(sim, name, paid), CARRY_CAUSE)
        entry["amount"] -= asked
        return {"ok": True, "holder": name, "asked": round(asked, 1), "paid": round(paid, 1),
                "written_off": round(asked - paid, 1), "fees_taken_from_claim": round(fees, 1),
                "holder_could_pay_share": round(share, 3), "claim_left": round(entry["amount"], 1),
                "capital": round(household.capital, 1)}

    @api.command("letter", group="money", summary="move a claim from one holder to another by letter of credit",
                 usage=["bh_cashshelter_z6f2:letter <from> <to> <amount|all>"],
                 options={"<from>": "the holder that issues the letter", "<to>": "the holder that honours it",
                          "<amount>": "claim to move"},
                 description="The issuing holder sends coin to the honouring holder through the ledger and keeps a fee; "
                             "your claim moves with it. The coin never passes through your own purse, so nothing of it is "
                             "exposed to your disasters on the way. The issuer pays only what its purse can.",
                 shape="text")
    def letter(sim, nodes, cmd, ended):
        problem = stopped(ended)
        if problem:
            return problem
        names, amounts = arguments(cmd)
        words = str(cmd.get("text") or "").split()
        ordered = [word for word in words if word in holders] or names
        if len(ordered) != 2 or ordered[0] == ordered[1]:
            return refuse("name two different holders, issuer first.", choices=choices())
        source, target = ordered
        seat = sim.state.acting_seat
        entry = claim_of(sim, source, seat)
        if entry is None or entry["amount"] <= 0.0:
            return refuse("you have no claim on %s." % source)
        settle(sim, source, seat)
        amount, error = amount_of(amounts, entry["amount"])
        if error:
            return refuse(error + ".")
        asked = min(amount, entry["amount"])
        share = solvency(sim, source)
        issuer = holder_actor(sim, source)
        fee = asked * letter_fee
        moved = min(max(0.0, asked - fee) * share, max(0.0, issuer.money))
        receiver = ensure_holder(sim, target)
        settle(sim, target, seat)
        if moved > 0.0:
            ledger.transfer(issuer, receiver, moved, LETTER_CAUSE)
        entry["amount"] -= asked
        arrived = memory(sim).setdefault(target, {}).setdefault(seat, {"amount": 0.0, "settled_year": sim.year})
        arrived["amount"] += moved
        return {"ok": True, "from": source, "to": target, "asked": round(asked, 1), "moved": round(moved, 1),
                "fee_kept_by_issuer": round(min(fee, asked), 1), "issuer_could_pay_share": round(share, 3),
                "claim_left_on_issuer": round(entry["amount"], 1), "claim_on_receiver": round(arrived["amount"], 1)}

    def theft_rows(sim, strength, order_holds):
        from sim.coin.api import COIN_GUARD_HOURS_PER_TONNE_YEAR, theft_exposure
        household = sim.state.household
        capacity, protection = (sim.state_capacity, sim.view("standing")()["protection"]) if order_holds else (0.0, 0.0)
        exposure = sim.view("household_exposure")()
        loss = theft_exposure.theft_loss_by_kind(
            exposure.values, {"coin": COIN_GUARD_HOURS_PER_TONNE_YEAR}, sim.view("household_visible_scale")(), capacity,
            protection, strength)
        cash = min(exposure.purse, sum(value for kind, value in loss.items() if kind not in ("goods", "land")))
        return cash, loss.get("goods", 0.0)

    @api.command("exposure", group="money", summary="what each disaster would take from your purse, and what you have sheltered",
                 usage=["bh_cashshelter_z6f2:exposure"],
                 description="Reads the engine's own hazard arithmetic for the purse you hold now: fire, banditry, a sack, "
                             "plague and debasement take a share of the purse (a sack and banditry also take the portable "
                             "share of goods); a treasury demand takes a share of the wealth the state can see. Then lists "
                             "each holder, your claim, what it could pay today and the fee a year. Dated hazards are not "
                             "listed here: the risk screen lists those.")
    def exposure(sim, nodes, cmd, ended):
        household = sim.state.household
        cash = max(0.0, household.capital)
        rows = []

        def row(kind, chance, cash_taken, goods_taken, basis):
            rows.append({"hazard": kind, "chance_per_year": chance, "takes_cash": round(cash_taken, 1),
                         "takes_goods": round(goods_taken, 1), "basis": basis})

        row("fire", sim.FIRE_ANNUAL_CHANCE, cash * sim.FIRE_CAPITAL_LOSS, 0.0,
            "FIRE_CAPITAL_LOSS of the purse; goods and land are untouched")
        banditry_cash, banditry_goods = theft_rows(sim, sim.BANDITRY_TAKE_STRENGTH, True)
        row("banditry", sim.BANDITRY_ANNUAL_CHANCE, banditry_cash, banditry_goods,
            "BANDITRY_TAKE_STRENGTH scaled by portability, guarding, visibility and the state's order")
        sack_cash, sack_goods = theft_rows(sim, sim.SACK_TAKE_STRENGTH, False)
        row("sack", None, sack_cash, sack_goods,
            "SACK_TAKE_STRENGTH with the state's order failed; chance comes from the dated hazards (risk)")
        row("plague", None, cash * sim.PLAGUE_CASH_LOSS_SHARE, 0.0,
            "PLAGUE_CASH_LOSS_SHARE times the staff share a wave kills, taken from the purse")
        row("debasement", None, cash * sim.REAL_EROSION_CASH_LOSS_SHARE, 0.0,
            "REAL_EROSION_CASH_LOSS_SHARE times the hazard's erosion, taken from the purse; coin held by a holder is "
            "still coin and is not spared the fall in the coin's worth")
        status = sim.view("confiscation_status")()
        visible = max(0.0, household.capital - max(0.0, getattr(household, "concealed", 0.0) or 0.0))
        row("treasury confiscation", status["chance_this_year"], visible * sim.CONFISCATION_CAPITAL_LOSS, 0.0,
            "CONFISCATION_CAPITAL_LOSS of the wealth the state can count (your purse less what you conceal); "
            "a holder's coin is not in your purse")
        seat = sim.state.acting_seat
        sheltered = []
        for name in sorted(holders):
            entry = claim_of(sim, name, seat)
            if entry is None or entry["amount"] <= 0.0:
                continue
            actor = holder_actor(sim, name)
            sheltered.append({
                "holder": name, "claim": round(entry["amount"], 1), "could_pay_share": round(solvency(sim, name), 3),
                "fee_per_year": round(min(entry["amount"], yearly_cost(sim, name, entry["amount"])
                                          * (1.0 + float(holders[name]["custody_markup"]))), 1),
                "holder_purse": round(actor.money, 1) if actor is not None else 0.0,
                "own_failure_chance_per_year": holders[name]["failure_chance_per_year"],
                "note": actor.record.cause if actor is not None and actor.record.cause else ""})
        total_sheltered = sum(item["claim"] * item["could_pay_share"] for item in sheltered)
        lines = ["purse: %.0f; sheltered (payable today): %.0f" % (cash, total_sheltered)]
        for item in rows:
            lines.append("%s: takes about %.0f of the purse and %.0f of goods%s" % (
                item["hazard"], item["takes_cash"], item["takes_goods"],
                "" if item["chance_per_year"] is None else ", chance %.1f%% a year" % (100.0 * item["chance_per_year"])))
        for item in sheltered:
            lines.append("held by %s: claim %.0f, it could pay %.0f%% today, fee %.0f a year" % (
                item["holder"], item["claim"], 100.0 * item["could_pay_share"], item["fee_per_year"]))
        return {"ok": True, "purse": round(cash, 1), "hazards": rows, "sheltered": sheltered,
                "sheltered_payable_today": round(total_sheltered, 1), "lines": lines}

    def claims_owed(sim):
        seat = sim.state.acting_seat
        return sum(entry["amount"] * solvency(sim, name) for name in holders
                   for entry in [claim_of(sim, name, seat)] if entry is not None)

    def seize_claims(sim, amount, taker):
        """A confiscation that has emptied the purse takes the rest from the holders, in the share they can pay."""
        seat, taken = sim.state.acting_seat, 0.0
        for name in sorted(holders):
            entry = claim_of(sim, name, seat)
            if entry is None or amount - taken <= 0.0:
                continue
            share = solvency(sim, name)
            claim_taken = min(entry["amount"], (amount - taken) / share) if share > 0.0 else 0.0
            paid = min(claim_taken * share, max(0.0, holder_actor(sim, name).money))
            if paid > 0.0:
                ledger.transfer(holder_actor(sim, name), taker, paid, "confiscation of a claim")
                entry["amount"] -= claim_taken
                taken += paid
        return taken

    api.provide("wealth_claims", lambda: (claims_owed, seize_claims))
