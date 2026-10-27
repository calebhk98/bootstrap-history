"""Print cross-class reference counts and topic coupling for Sim methods. Run from the repository root."""
import ast, collections, inspect, re, sys, textwrap
sys.path.insert(0, ".")
from sim.engine.core import Sim
definer = {}
for klass in Sim.__mro__:
    if klass is not object:
        for name, value in vars(klass).items():
            if callable(value) or isinstance(value, (property, staticmethod, classmethod)):
                definer.setdefault(name, klass)
topic_rules = [("steps", r"^(year_steps|step_phase_|year_run|shock_year|core$)"),
    ("projects", r"^(projects|project_|blockers|failure_|planner|path_search|completion|capital_builds|seat_builds)"),
    ("seats", r"^(seat_|state_seat|founder_sales|cash_|goals|fog|win_)"),
    ("markets", r"^(prices|solve_prices|making_cost|long_run|rent_standin|solve_cache|goods_market|market_|incumbent|producer_costs|entry_cost|wage_|money_units|real_|economy_goods|economy_cost)"),
    ("node_money", r"^(node_|industry_|concern_)"),
    ("foreign_coin", r"^(foreign_|economy_freight|domestic_haul|trader_cargo|coin_|theft_|route_dues)"),
    ("economy_port", r"^economy_port"), ("economy_old", r"^economy"),
    ("labour", r"^(labour_port|staff|projects_staffing|payroll|apprentice)"),
    ("geography", r"^(geography_port|ways|works|held_works|colonies|mine_|food_|soil_|regional_|urban_|demographic)"),
    ("society", r"^(society|interest_groups|legitimacy|benefactions|hazard_|visibility|world_hazards|campaign|revolt|captives|forward_disease)"),
    ("living_stock", r"^(living_stock|food_relief|defence_stores)"), ("mods", r"^(mods|mod_)"),
    ("properties", r"^core_properties"), ("mechanics", r"^(mechanics|techniques|material_|capability)")]
def topic(klass):
    module_name = klass.__module__.split(".")[-1]
    return next((label for label, pattern in topic_rules if re.search(pattern, module_name)), "other:" + module_name)
cross_class = collections.Counter(); by_topic = collections.Counter(); field_readers = collections.defaultdict(set)
for klass in Sim.__mro__:
    if klass is object or not klass.__module__.startswith("sim."):
        continue
    tree = ast.parse(textwrap.dedent(inspect.getsource(klass)))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            if node.attr in definer:
                by_topic[(topic(klass), topic(definer[node.attr]))] += 1
                if definer[node.attr] is not klass:
                    cross_class[(klass.__name__, definer[node.attr].__name__)] += 1
            else:
                field_readers[node.attr].add(klass.__name__)
print("cross-class references", sum(cross_class.values()), "class pairs", len(cross_class))
print("inside one topic", sum(count for (source, target), count in by_topic.items() if source == target), "of", sum(by_topic.values()))
inbound = collections.Counter()
for (source, target), count in by_topic.items():
    if source != target:
        inbound[target] += count
print("inbound by topic", inbound.most_common(8))
print("fields read by four or more classes", sorted(name for name, readers in field_readers.items() if len(readers) >= 4))
