"""Stand-in games for the screens' rules.

`StandIn` answers only the views a test names; a view asked for that the test did not give is an error naming it, and a
command sent is kept in `sent` and answered with `answers.get(type(command))`.

    game = StandIn(year=1301, tree_nodes=NODES)                              # a table view: its value
    game = StandIn(visibility=lambda node_id, memo=None: node_id in seen)     # a quote or keyed view: a function

`Game` is a plain namespace of facts under the names the game once held them (`capital`, `done`, `nodes`, `credit_limit()`);
the views the screens now read answer from them, so a rule is tested on plain values."""
from types import SimpleNamespace


class _Answer:
    def __init__(self, value):
        self.value = value

    def __call__(self, *arguments, **keywords):
        return self.value(*arguments, **keywords) if callable(self.value) else self.value

    def __getitem__(self, key):
        return self.value(key) if callable(self.value) else self.value[key]


class StandIn:
    def __init__(self, answers=None, **views):
        self._views = views
        self.sent = []
        self.answers = answers or {}

    def view(self, name):
        if name not in self._views:
            raise KeyError("the stand-in game was given no view %r" % name)
        return _Answer(self._views[name])

    def send(self, command):
        self.sent.append(command)
        return self.answers.get(type(command))


METHOD_OF_VIEW = {
    "colonies": "colony_rows", "committed_cost": "committed_spend", "concern_sale_quote": "quote_concern_sale",
    "coverage": "coverage_nodes", "demand_by_supply_tag": "_demand_by_supply_tag",
    "diffusion_report": "world_diffusion_report", "disease_burden": "_disease_burden",
    "effect_terms": "_effect_terms", "electricity_demand": "_electricity_demand_kw",
    "farm_land_price": "farm_price_per_hectare", "generation_breakdown": "generation_breakdown_kw",
    "generation_by_tier": "installed_generation_kw_by_tier", "goods_category_ratios": "_goods_category_ratios",
    "held_goods": "_material_stock", "material_demand": "annual_material_demand",
    "material_shortfall": "material_shortfall_t", "own_production_tags": "_own_production_tags",
    "own_supply_by_commodity": "demand_and_own_supply_by_material", "partners": "partner_countries",
    "practice_set": "_practice_set", "prerequisite_message": "missing_prereq_message",
    "purchase_quote": "material_purchase_cost", "resource_throttle": "peek_resource_throttle",
    "revenue_estimate": "revenue", "schooling_flow": "_schooling_flow", "start_check": "start_reason",
    "visibility": "is_visible", "visible_to_player": "_visible_to_player",
}

FACT_OF_VIEW = {
    "cast": "actors", "demographic_flows": "_last_demographic_step", "event_log": "log",
    "hours_per_person_year": "HOURS_PER_PERSON_YEAR", "last_start": "materials_paid_at_last_start",
    "legacy_geography": "geography", "legacy_world_map": "world_map", "material_checks": "MATERIAL_CHECKS",
    "mine_works_materials": "MINE_OPEX_MATERIALS", "staff_capacity_sources": "STAFF_CAPACITY_SOURCES",
    "techniques_forgotten": "forgotten",
}

KEYED_OF_VIEW = {
    "goods_quote": "material_trade_quote", "goods_stock": "material_stock_t",
    "material_market_tonnes": "_material_market_tonnes", "material_own_supply": "_own_material_supply",
    "material_pool": "_material_tag",
}

METHOD_OF_COMMAND = {
    "AdvanceSociety": "advance_society", "AnswerOffer": "seat_answer", "ApplyForPatent": "seat_patent",
    "ApplyTechEffects": "apply_tech_effects", "AutoOpenVentures": "auto_open_ventures", "Bribe": "bribe",
    "BuildHousing": "build_worker_housing", "BuildWay": "build_way", "BuyMaterial": "buy_material_stock",
    "CarryOutTransfers": "carry_out_transfers", "CloseLapsedDependents": "close_lapsed_dependents",
    "ClosePartnerBooks": "close_partner_books", "CloseUnstaffedVentures": "close_unstaffed_ventures",
    "DisbandArmy": "disband_army", "Disclose": "disclose", "DrawDeposit": "draw_deposit", "EndRun": "_catastrophe",
    "FoundBank": "seat_found_bank", "HandOverSeat": "hand_over_seat", "LoseCapital": "lose_capital",
    "MakeOffer": "seat_offer", "MothballWork": "mothball_work", "NoteActorHomeTrade": "note_actor_home_trade",
    "NoteActorTrade": "note_actor_trade", "NoteCargoLeg": "note_cargo_leg", "OpenMarketBook": "_open_market_book",
    "OpenVenture": "open_venture", "OrderArmy": "order_army", "PostBounty": "post_bounty", "RaiseArmy": "raise_army",
    "RecallArmy": "recall_army", "ReopenRestaffedVentures": "reopen_restaffed_ventures",
    "RestoreWork": "restore_work", "RollOut": "roll_out", "SellConcern": "sell_concern",
    "SellMaterial": "sell_material_stock", "SettleTraderCargo": "settle_trader_cargo",
    "SettleWithState": "settle_with_state", "StartProject": "start_project", "StopProject": "stop_project",
    "SurviveStaff": "apply_staff_survival", "WithdrawFromPublicLife": "withdraw_from_public_life",
}

# views that are one fact of the game held under the name the game once used for it
ATTRIBUTE_OF_VIEW = {
    "acting_balance": "capital", "techniques_held": "done", "techniques_granted": "granted", "active_projects": "active",
    "legacy_fog": "fog", "tree_nodes": "nodes", "game_config": "cfg", "civilisation": "civ", "legacy_order": "order",
    "legacy_fuzzy_estimates": "fuzzy_estimates", "techniques_revealed": "revealed", "techniques_forgotten": "forgotten",
    "horizon_end_year": "end_year", "acting_seat": "acting_seat",
}
# views that are one field of the game's state record
STATE_OF_VIEW = {"legacy_seats": "seats", "acting_seat": "acting_seat"}
# views that are a record of several facts
RECORDS = {
    "founder": {"alive": "founder_alive", "life_left": "life_left", "dead_reason": "dead_reason", "policy": "policy"},
    "goal": {"node": "goal", "year": "goal_year", "years": "goal_years"},
    "standing": {"reputation": "reputation", "scandal": "scandal", "protection": "protection", "familiarity": "familiarity",
                 "scandal_last_year": "scandal_last_year"},
    "debt_status": {"insolvent_years": "insolvent_years", "credit_frozen_until": "credit_frozen_until",
                    "bondage_debt": "bondage_debt", "bondage_years_left": "bondage_years_left", "interest_paid": "interest_paid"},
    "automation": {"manual": "manual", "bounty_set": "bounty_set"},
    "patronage": {"founder_age": "founder_age", "deputies_carry_the_work": "deputies_carry_the_work"},
}


class FactViews:
    """`view` and `send` over an object that holds the facts as attributes."""

    def view(self, name):
        if name == "year" and not hasattr(self, "year") and hasattr(self, "state"):
            return _Answer(lambda: self.state.scenario.year)
        if name in STATE_OF_VIEW and not hasattr(self, ATTRIBUTE_OF_VIEW.get(name, name)) and hasattr(self, "state"):
            return _Answer(lambda: getattr(self.state, STATE_OF_VIEW[name]))
        if name in RECORDS:
            fields = RECORDS[name]
            return _Answer(lambda: {key: getattr(self, attribute, None) for key, attribute in fields.items()})
        if name in ATTRIBUTE_OF_VIEW and hasattr(self, ATTRIBUTE_OF_VIEW[name]):
            return _Answer(lambda: getattr(self, ATTRIBUTE_OF_VIEW[name]))
        if name == "start_check" and hasattr(self, "can_start"):
            return _Answer(lambda node_id, ignore_trade=False, memo=None, why=True: (
                (self.can_start(node_id), None) if not why or not hasattr(self, "start_reason")
                else self.start_reason(node_id, ignore_trade, memo, why)))
        for table in (METHOD_OF_VIEW, KEYED_OF_VIEW, FACT_OF_VIEW):
            attribute = table.get(name)
            if attribute is not None and hasattr(self, attribute):
                return _Answer(lambda attribute=attribute: getattr(self, attribute)) if table is FACT_OF_VIEW else \
                    _Answer(lambda *arguments, attribute=attribute: getattr(self, attribute)(*arguments))
        if hasattr(self, name):
            held = getattr(self, name)
            return _Answer(held)
        raise KeyError("the stand-in game was given no view %r (nor an attribute of that name)" % name)

    def send(self, command):
        name = METHOD_OF_COMMAND.get(type(command).__name__)
        if name is not None and hasattr(self, name):
            return getattr(self, name)(*vars(command).values())
        self.__dict__.setdefault("sent", []).append(command)
        return getattr(self, "answers", {}).get(type(command))


class Game(FactViews, SimpleNamespace):
    """A namespace of facts that answers views."""
