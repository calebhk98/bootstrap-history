"""Complaint 103: a licence sold through the exchange can carry a royalty on the licensee's takings, paid to the holder
every year it operates the concern while the patent lives. Any holder (a firm, or a seat) can charge one."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import exchange, exchange_commands, licence, patent  # noqa: F401
from sim.agents.player_commands import CommandRejected

from .agents_fake_world import FakeWorld, make_node, total_money


class RoyaltyWorld(FakeWorld):
	registry = None

	def patent_entry(self, node_id):
		return patent.entry_among(self.registry.actors.values(), node_id, self.year)


def raises(call):
	try:
		call()
	except CommandRejected as reason:
		return str(reason)
	return None


world = RoyaltyWorld(year=100)
world.nodes["loom"] = make_node("loom")
world.registry = registry = ActorRegistry(ActorsState(home_country="home"))
holder = registry.add("firm:1", ActorRecord(kind="firm", money=100.0))
holder.record.patents["loom"] = {"granted": 90, "expires": 110, "licensees": []}
holder.knowledge.add("loom")
licensee = registry.add("firm:2", ActorRecord(kind="firm", money=1000.0))
licensee.knowledge.add("loom")
state_actor = registry.add("government:home", ActorRecord(kind="government", money=1000.0))

check("a royalty must go with a licence", raises(lambda: exchange.make_offer(holder, licensee, {"royalty": {"loom": 0.1}}, {}, world)))
check("a royalty is a share below one", raises(lambda: exchange.make_offer(holder, licensee, {"licence": ["loom"], "royalty": {"loom": 1.0}}, {}, world)))
offered = exchange.make_offer(holder, state_actor, {"licence": ["loom"], "royalty": {"loom": 0.1}}, {}, world)
check("only a firm has takings to share", "royalty" in (raises(lambda: exchange.accept(state_actor, offered["id"], registry.get, world)) or ""))

offered = exchange.make_offer(holder, licensee, {"licence": ["loom"], "royalty": {"loom": 0.1}}, {"money": 50.0}, world)
exchange.accept(licensee, offered["id"], registry.get, world)
check("the licensee owes the holder the agreed share", licensee.record.royalty_owed["loom"] == {"holder": "firm:1", "rate": 0.1}, licensee.record.royalty_owed)
before = total_money(registry.actors.values())
paid = licence.collect_patent_royalty(world, registry.get, licensee, "loom", 2000.0)
check("it pays that share of its takings", abs(paid - 200.0) < 1e-9 and abs(holder.money - 350.0) < 1e-9, (paid, holder.money))
check("the royalty moves through the ledger and conserves money", abs(total_money(registry.actors.values()) - before) < 1e-9)
licensee.money = 20.0
check("it never pays more than its purse", abs(licence.collect_patent_royalty(world, registry.get, licensee, "loom", 2000.0) - 20.0) < 1e-9)
world.year = 111
check("the royalty ends with the patent", licence.collect_patent_royalty(world, registry.get, licensee, "loom", 2000.0) == 0.0)
other = registry.add("firm:3", ActorRecord(kind="firm", money=100.0))
world.year = 100
check("a firm that owes nothing pays nothing", licence.collect_patent_royalty(world, registry.get, other, "loom", 2000.0) == 0.0)
