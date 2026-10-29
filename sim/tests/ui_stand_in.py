"""Stand-in games for the screens' rules.

`StandIn` answers only the views a test names; a view asked for that the test did not give is an error naming it, and a
command sent is kept in `sent` and answered with `answers.get(type(command))`.

    game = StandIn(year=1301, tree_nodes=NODES)                              # a table view: its value
    game = StandIn(visibility=lambda node_id, memo=None: node_id in seen)     # a quote or keyed view: a function

`Game` is a plain namespace of facts under the names the game once held them (`capital`, `done`, `nodes`, `credit_limit()`);
the views the screens now read answer from them, so a rule is tested on plain values."""
from types import SimpleNamespace

from .seat_views_stand_in import seat_views


class _Answer:
    def __init__(self, value):
        self.value = value

    def __call__(self, *arguments, **keywords):
        return self.value(*arguments, **keywords) if callable(self.value) else self.value

    def __getitem__(self, key):
        return self.value(key) if callable(self.value) else self.value[key]


class _HeldBy:
    """A set that holds what the stand-in's `has` says it holds."""

    def __init__(self, has):
        self.has = has

    def __contains__(self, node_id):
        return bool(self.has(node_id))


class _KeyedRecord:
    """A keyed view whose value for a key is a record of the answers of several methods asked of that key."""

    def __init__(self, build):
        self.build = build

    def __getitem__(self, key):
        return self.build(key)


class _Table:
    """A view built from facts at the time it is read."""

    def __init__(self, build):
        self.build = build

    def __call__(self):
        return self.build()

    def __getitem__(self, key):
        return self.build()[key]


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
    "legacy_economy": "economy", "legacy_labour": "labour",
    "legacy_geography": "geography", "material_checks": "MATERIAL_CHECKS",
    "mine_works_materials": "MINE_OPEX_MATERIALS", "staff_capacity_sources": "STAFF_CAPACITY_SOURCES",
    "techniques_forgotten": "forgotten",
}

KEYED_OF_VIEW = {
    "goods_quote": "material_trade_quote", "goods_stock": "material_stock_t",
    "material_market_tonnes": "_material_market_tonnes", "material_own_supply": "_own_material_supply",
    "material_pool": "_material_tag",
}

METHOD_OF_COMMAND = {
    "ReviewVentures": "review_ventures",
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
    "WithdrawFromPublicLife": "withdraw_from_public_life",
}

# views that are one fact of the game held under the name the game once used for it
ATTRIBUTE_OF_VIEW = {
    "acting_balance": "capital", "techniques_held": "done", "techniques_granted": "granted", "active_projects": "active",
    "fog_of_war": "fog", "tree_nodes": "nodes", "game_config": "cfg", "civilisation": "civ",
    "legacy_fuzzy_estimates": "fuzzy_estimates", "techniques_revealed": "revealed", "techniques_forgotten": "forgotten",
    "horizon_end_year": "end_year", "acting_seat": "acting_seat",
}
SEAT_VIEWS = frozenset({"registered_seats", "seat_list", "seat_country", "seat_kind", "seat_holder", "ended_seats"})
# views that are one field of the game's state record
STATE_OF_VIEW = {"acting_seat": "acting_seat"}
# keyed views whose value for a key is a record of several methods' answers for it
KEYED_METHOD_RECORDS = {"stock_status": {"gates": "stock_gates", "needed_by": "stock_needed_by"}}
# views that are a record of the answers of several methods
METHOD_RECORDS = {
    "literacy_ceiling": {"literacy_general": "literacy_ceiling_general", "literacy_elite": "literacy_ceiling_elite"},
    "patronage": {"founder_age": "founder_age", "deputies_carry_the_work": "deputies_carry_the_work"},
    "diffusion_index": {"venture": "diffusion_index", "information": "information_diffusion_index"},
}
# views that are a record of several facts
RECORDS = {
    "founder": {"alive": "founder_alive", "life_left": "life_left", "dead_reason": "dead_reason", "policy": "policy"},
    "goal": {"node": "goal", "year": "goal_year", "years": "goal_years"},
    "standing": {"reputation": "reputation", "scandal": "scandal", "protection": "protection", "familiarity": "familiarity",
                 "scandal_last_year": "scandal_last_year"},
    "debt_status": {"insolvent_years": "insolvent_years", "credit_frozen_until": "credit_frozen_until",
                    "bondage_debt": "bondage_debt", "bondage_years_left": "bondage_years_left", "interest_paid": "interest_paid"},
    "automation": {"manual": "manual", "bounty_set": "bounty_set"},
}


# views and commands the labour model once answered, by the method of the stand-in `labour` object that does
LABOUR_METHOD_OF_VIEW = {
    "wage_bill": "wage_bill", "headcount": "headcount", "effective_scholars": "effective_scholars", "staff_advice": "staff_advice",
    "base_tile": "base_tile", "farm_share_of_hours": "farm_share_of_hours", "settlement_tiles": "settlement_tiles",
    "household_room": "household_room", "supervision_room": "supervision_room", "supervision_room_from": "supervision_room_from",
    "room_advice": "room_advice", "wage_work_this_year": "wage_work_this_year", "sole_supervisors": "sole_supervisors",
    "idle_specialists": "idle_specialists", "population_report": "population_report", "workforce_report": "workforce_report",
    "craft_trades_report": "craft_trades_report", "home_town_population_estimate": "home_town_population_estimate",
    "training_hours_per_person": "training_hours_per_person", "hire_check": "hire_check", "commission_check": "commission_check",
    "train_check": "train_check", "trainee_wage_bill": "trainee_wage_bill", "work_for_wages_dry_run": "work_for_wages_dry_run",
    "hours_you_can_call_on": "hours_you_can_call_on", "literacy_capacity": "literate_capacity", "market_supply": "market_supply",
    "trade_available": "trade_available", "base_annual_wage": "base_annual_wage", "wage": "wage_per_hour",
    "market_supply_split": "market_supply_split", "hours_reserved": "hours_reserved",
    "trade_headcount_pending": "trade_headcount_pending", "literacy_factor": "literacy_factor",
    "relocation_quote": "relocation_quote", "slave_quote": "slave_quote",
}
LABOUR_ATTRIBUTE_OF_VIEW = {"labour_market": "market", "literate_trades": "LITERATE_TRADES", "slave_base_price": "SLAVE_BASE_PRICE"}
LABOUR_POOL_METHOD = {"director_pool": "director_pool", "director_committed": "director_hours_committed",
                      "craft_hands": "craft_hands_available", "scholar_hands": "scholar_hands_available", "hired_cap": "hired_cap"}
LABOUR_METHOD_OF_COMMAND = {"HireStaff": "hire", "FireStaff": "fire", "TrainStaff": "train", "CommissionHours": "commission",
                            "WorkForWages": "work_for_wages", "BuySlaves": "buy_slaves", "Manumit": "manumit",
                            "FoundTradeSchool": "found_trade_school", "MoveBase": "move_base"}


class FactViews:
    """`view` and `send` over an object that holds the facts as attributes."""

    def view(self, name):
        if name == "project_order" and hasattr(self, "order"):
            return _Answer(lambda: tuple(self.order))
        if name == "year" and not hasattr(self, "year") and hasattr(self, "state"):
            return _Answer(lambda: self.state.scenario.year)
        if name in SEAT_VIEWS and not hasattr(self, name) and hasattr(getattr(self, "state", None), "seats"):
            return _Answer(seat_views(self.state)[name])
        if name in STATE_OF_VIEW and not hasattr(self, ATTRIBUTE_OF_VIEW.get(name, name)) and hasattr(self, "state"):
            return _Answer(lambda: getattr(self.state, STATE_OF_VIEW[name]))
        if name == "hours_available" and hasattr(self, "director_pool"):
            return _Answer(lambda pool: getattr(self, LABOUR_POOL_METHOD[pool])())
        if name == "techniques_held" and not hasattr(self, "done") and hasattr(self, "has"):
            return _Answer(_HeldBy(self.has))
        if name == "capability_sets" and hasattr(self, "CAPABILITY_INSTITUTIONS"):
            return _Answer(lambda: (self.CAPABILITY_INSTITUTIONS, getattr(self, "SCALABLE_INSTITUTIONS", frozenset())))
        labour = self.__dict__.get("labour")
        if labour is not None:
            if name == "hours_available" and any(hasattr(labour, method) for method in LABOUR_POOL_METHOD.values()):
                return _Answer(lambda pool: getattr(labour, LABOUR_POOL_METHOD[pool])())
            if name in LABOUR_METHOD_OF_VIEW and hasattr(labour, LABOUR_METHOD_OF_VIEW[name]):
                return _Answer(getattr(labour, LABOUR_METHOD_OF_VIEW[name]))
            if name in LABOUR_ATTRIBUTE_OF_VIEW and hasattr(labour, LABOUR_ATTRIBUTE_OF_VIEW[name]):
                return _Answer(getattr(labour, LABOUR_ATTRIBUTE_OF_VIEW[name]))
        if name == "resource_throttle" and (hasattr(self, "peek_project_resource_throttle") or hasattr(self, "peek_resource_throttle")):
            return _Answer(lambda *node: self.peek_project_resource_throttle(*node) if node else self.peek_resource_throttle())
        if name == "done_year" and not hasattr(self, "done_year"):
            return _Answer(lambda: {})
        if name == "horizon_end_year" and not hasattr(self, "end_year") and hasattr(self, "cfg"):
            return _Answer(lambda: self.cfg["start_year"] + self.cfg["horizon_years"])
        if name in KEYED_METHOD_RECORDS and any(hasattr(self, method) for method in KEYED_METHOD_RECORDS[name].values()):
            fields = KEYED_METHOD_RECORDS[name]
            return _KeyedRecord(lambda key: {field: getattr(self, method)(key) if hasattr(self, method) else None
                                          for field, method in fields.items()})
        if name in METHOD_RECORDS and any(hasattr(self, method) for method in METHOD_RECORDS[name].values()):
            fields = METHOD_RECORDS[name]
            return _Table(lambda: {key: getattr(self, method, lambda: None)() for key, method in fields.items()})
        if name in RECORDS:
            fields = RECORDS[name]
            return _Table(lambda: {key: getattr(self, attribute, None) for key, attribute in fields.items()})
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
        if type(command).__name__ in ("ReorderProjects", "RestoreProjectOrder") and hasattr(self, "order"):
            from sim.projects import order_rules
            self.order[:] = (order_rules.place_sequence(self.order, self.view("active_projects")(), command.node_ids)
                             if hasattr(command, "node_ids") else command.order)
            return None
        labour = self.__dict__.get("labour")
        method = LABOUR_METHOD_OF_COMMAND.get(type(command).__name__)
        if labour is not None and method is not None and hasattr(labour, method):
            return getattr(labour, method)(*vars(command).values())
        name = METHOD_OF_COMMAND.get(type(command).__name__)
        if name is not None and hasattr(self, name):
            return getattr(self, name)(*vars(command).values())
        self.__dict__.setdefault("sent", []).append(command)
        return getattr(self, "answers", {}).get(type(command))


class Game(FactViews, SimpleNamespace):
    """A namespace of facts that answers views. The facts answer first; a `view=` function given answers the rest."""

    def __init__(self, view=None, **facts):
        super().__init__(**facts)
        self.__dict__["_given_view"] = view
        self.__dict__.setdefault("sent", [])

    def view(self, name):
        try:
            return FactViews.view(self, name)
        except KeyError:
            given = self.__dict__.get("_given_view")
            if given is None:
                raise
            return given(name)


from .ui_stand_in_names import FACT_OF_VIEW_MORE, METHOD_OF_COMMAND_MORE, METHOD_OF_VIEW_MORE  # noqa: E402

for _table, _more in ((METHOD_OF_VIEW, METHOD_OF_VIEW_MORE), (FACT_OF_VIEW, FACT_OF_VIEW_MORE), (METHOD_OF_COMMAND, METHOD_OF_COMMAND_MORE)):
    for _name, _old in _more.items():
        _table.setdefault(_name, _old)
