"""The resource throttle: how much of the year's planned work the materials and electricity support, and what a shortage
tells the player.

A reading is worked out by `rules.throttle_reading` from the stock as it stood when the year's accounting began, so the
year's own output banks once however often it is read. `throttle_quote` answers from it without changing anything;
`apply_throttle` takes the same reading and banks it."""
import collections
from typing import Any, List, NamedTuple, Optional, Tuple

from sim.ledger.api import BankStock
from sim.markets.api import NoteDraw, ResetDraws
from sim.reporting.api import RecordEvent

from . import rules
from .channels import READING
from .constants import LAB_SCALE_SUFFIX, RESOURCE_THROTTLE_FLOOR


class Inputs(NamedTuple):
    """Everything a reading depends on, gathered once."""
    industrial: Any
    lab: Any
    opening: Any
    electricity_need: float
    electricity_have: float
    signature: Tuple


class Throttle:
    """Needs: year, held_goods, goods_stock_opening, mine_capacity, forest_hectares, nitre_beds, active_project_ids,
    tree_nodes, shortage_remedy_plan. Sends BankStock, ResetDraws, NoteDraw, RecordEvent."""

    def throttle_inputs(self, demand: Any) -> Inputs:
        needs = self.needs
        industrial, lab = rules.throttle_demand_split(demand, self.material_pool)
        stock = needs.held_goods()
        opening = needs.goods_stock_opening()
        electricity_need = self.electricity_demand_kw()
        electricity_have = self.generation_capacity_kw()
        signature = (needs.year(), tuple(sorted(industrial.items())), tuple(sorted(lab.items())),
                     tuple(sorted(needs.mine_capacity().items())), needs.forest_hectares(),
                     needs.nitre_beds()["square_metres"], tuple(sorted(stock.items())), electricity_need, electricity_have,
                     stock.writes)
        return Inputs(industrial, lab, opening, electricity_need, electricity_have, signature)

    def read_throttle(self, inputs: Inputs) -> rules.ThrottleReading:
        return rules.throttle_reading(inputs.industrial, inputs.lab, self.own_production_tags(), inputs.electricity_need,
                                      inputs.electricity_have, inputs.opening, self.own_material_supply, self.market_tonnes,
                                      RESOURCE_THROTTLE_FLOOR)

    def portfolio_quote(self) -> Tuple[float, Optional[str]]:
        """(the pace, the pool that binds it) as the books stand, nothing changed. A reading the last take already made
        with nothing changed since is replayed."""
        readings = self.readings
        inputs = self.throttle_inputs(self.annual_material_demand())
        if inputs.signature == readings.throttle_sig:
            return readings.throttle_cache
        reading = self.read_throttle(inputs)
        return reading.pace, reading.binding

    def project_pace(self, node_id: str, pace: float, binding: Optional[str]) -> float:
        """The portfolio's pace for one project: it slows only the work that draws on the pool that binds; paper research
        does not become short of saltpetre because a gunpowder project is."""
        if pace >= 0.999 or not binding:
            return 1.0
        if binding == "electricity":
            pools = {"electricity"} if node_id in self.electricity_load_node_ids() else set()
        else:
            node = self.needs.tree_nodes().get(node_id) or {}
            pools = rules.input_pools(node.get("mat") or {}, self.chosen_fuel(node_id) == "coke",
                                      lambda material: self.material_pool(material)[0], LAB_SCALE_SUFFIX)
        return rules.shared_throttle(pace, binding, pools)

    def throttle_quote(self, node_id: Optional[str] = None) -> Tuple[float, Optional[str]]:
        """(the material pace of the portfolio or of one project, the pool that binds the portfolio) as a screen asks about
        it. Nothing is banked, counted or noted."""
        pace, binding = self.portfolio_quote()
        if node_id is None:
            return pace, binding
        return self.project_pace(node_id, pace, binding), binding

    def apply_throttle(self, command: Any) -> float:
        """Take the year's reading: bank what it leaves, note the market's draw and count the shortage."""
        readings = self.readings
        demand = readings.held = self.annual_material_demand()
        inputs = self.throttle_inputs(demand)
        if inputs.signature == readings.throttle_sig:
            self.seat.throttle, self.seat.binding = readings.throttle_cache
            pace = self.seat.throttle
        else:
            reading = self.read_throttle(inputs)
            needs = self.needs
            needs.send(BankStock(reading.banked))
            needs.send(ResetDraws())
            for commodity, tonnes in reading.draws:
                if tonnes > 0:
                    needs.send(NoteDraw(commodity, tonnes))
            self.seat.throttle, self.seat.binding = reading.pace, reading.binding
            stock = needs.held_goods()
            # stored against the stock as the reading left it, so an immediate repeat replays instead of spending again
            readings.throttle_sig = inputs.signature[:6] + (tuple(sorted(stock.items())),) + inputs.signature[7:9] + (stock.writes,)
            readings.throttle_cache = (reading.pace, reading.binding)
            if reading.binding:
                self.seat.shortages[reading.binding] += 1
            pace = reading.pace
        self.bump_seat(READING)
        if command.node_id is None:
            return pace
        return self.project_pace(command.node_id, pace, self.seat.binding)

    # ---- the standing shortage ----

    def slowed_projects(self) -> List[str]:
        """The active projects the standing shortage slows, in id order; none when nothing running draws it."""
        return [node_id for node_id in self.needs.active_project_ids()
                if self.throttle_quote(node_id)[0] < 1.0]

    def note_shortage(self, material: str, throughput: float) -> bool:
        """Record this year's shortage; True when it deserves a fresh event."""
        self.seat.shortage_condition, news = rules.noted_shortage(self.seat.shortage_condition, material, throughput,
                                                                  self.needs.year())
        return news

    def shortage_conditions(self) -> List[dict]:
        """The standing shortage as rows for the state screen, empty when none."""
        condition = self.seat.shortage_condition
        if not condition:
            return []
        return rules.condition_row(condition, self.needs.year(), self.material_shortfall(condition["material"]))

    def step_shortage_notes(self, seat_id: Any = None) -> None:
        """Tell the player what a standing material shortage costs: the full message only when it is new or has moved
        materially, and only while a running project draws the material."""
        seat = self.seat
        slowed = self.slowed_projects() if seat.throttle < 0.6 and seat.binding else []
        if slowed:
            if self.note_shortage(seat.binding, seat.throttle):
                names = ", ".join(self.needs.tree[node_id]["name"] for node_id in slowed[:3])
                remedy = self.needs.shortage_remedy_plan(seat.binding, None)["text"]
                self.needs.send(RecordEvent.of("material_shortage", "SHORT OF %s: %s running at %d%% of plan. %s" % (
                    rules.material_words(seat.binding).upper(), names, seat.throttle * 100, remedy)))
        else:
            seat.shortage_condition = None

    # ---- what the engine says about the remembered readings ----

    def forget_readings(self, command: Any) -> None:
        readings = self.readings
        readings.annual = readings.held = readings.by_tag = None

    def restore_readings(self, command: Any) -> None:
        held = self.seat.material_demand_at_last_throttle
        readings = self.readings
        readings.annual = readings.by_tag = None
        readings.held = None if held is None else collections.Counter(held)

    def capture_readings(self, command: Any) -> None:
        held = self.readings.held
        self.seat.material_demand_at_last_throttle = None if held is None else dict(held)

