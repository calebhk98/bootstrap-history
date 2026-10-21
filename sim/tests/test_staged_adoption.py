"""Complaint 491: awareness, staged adoption, contact triggers, technique levers and the actor's own stock in the gate."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import adoption, awareness, government_levers, research_gate
from sim.agents.api import ActorRecord, Firm
from sim.agents.government import Government
from sim.agents.research import diffuse

from .test_research_every_actor import ResearchWorld


class ContactWorld(ResearchWorld):
	"""A stand-in world with a settable contact volume and margin, and a treasury the levers are read from."""

	def __init__(self, volume=0.0, margin=10.0, half_life=0.001):
		super().__init__(half_life=half_life)
		self.volume = volume
		self.margin = margin
		self.demonstrated_nodes = {"tech"}
		self.treasury = Government("government:home", ActorRecord(kind="government", money=1000.0))
		self.government_actor = self.treasury

	def contact_volume(self, place_a, place_b):
		return self.volume

	def exposure(self, node_id, location):
		return 0.0

	def concern_margin(self, node_id):
		return self.margin


def firm(name="firm:1", money=1000.0):
	return Firm(name, ActorRecord(kind="firm", money=money, founded_year=100))


def years_until_aware(world, years=200):
	holder, learner = firm("firm:1"), firm("firm:2")
	holder.knowledge.add("tech")
	for year in range(years):
		world.year = 100 + year
		awareness.spread([holder, learner], world)
		if "tech" in learner.aware:
			return year
	return None


# ---- awareness -----------------------------------------------------------------------------
check("hazard rises with contact volume and is zero with none",
	  awareness.hazard(0.0) == 0.0 and awareness.hazard(1.0) < awareness.hazard(5.0) < 1.0)
check("with no contact an actor never learns a technique exists", years_until_aware(ContactWorld(volume=0.0)) is None)
slow, fast = years_until_aware(ContactWorld(volume=0.05)), years_until_aware(ContactWorld(volume=5.0))
check("more contact makes an actor aware sooner", slow is not None and fast is not None and fast < slow, (slow, fast))

world = ContactWorld(volume=0.0)
learner = firm("firm:2")
check("a technique someone has shown is closed to an actor that has not heard of it",
	  not awareness.knows_it_exists(learner, "tech", world))
check("a node no one has shown is open to pioneering", awareness.knows_it_exists(learner, "deep", world))
check("the research gate refuses an unaware actor with its cause",
	  [refusal.cause for refusal in research_gate.refusals(learner, "tech", world)] == ["unaware"])
learner.aware["tech"] = 100
check("once aware, the gate opens", research_gate.refusals(learner, "tech", world) == [])

holder, other = firm("firm:1"), firm("firm:2")
holder.knowledge.add("tech")
world = ContactWorld(half_life=0.001)
diffuse([holder, other], world)
check("unaware actors do not learn through diffusion", "tech" not in other.knowledge)
other.aware["tech"] = 100
diffuse([holder, other], world)
check("an aware actor learns by diffusion", "tech" in other.knowledge)

world = ContactWorld(volume=0.0)
holder, learner = firm("firm:1"), firm("firm:2")
holder.knowledge.add("tech")
holder.record.location = "far"
awareness.record_contact(learner, "far", 50.0)
awareness.spread([holder, learner], world)
check("a contact event (route, conquest, migration) raises awareness on the receiving side", "tech" in learner.aware)
check("a contact counted once fades by half", abs(learner.contacts["far"] - 25.0) < 1e-9)

# ---- staged adoption -----------------------------------------------------------------------
check("the gap is relative, signed and bounded",
	  adoption.margin_gap(3.0, 1.0) == 0.5 and adoption.margin_gap(1.0, 3.0) == -0.5 and adoption.margin_gap(0.0, 0.0) == 0.0)
check("a positive gap grows a share along a logistic, a negative one shrinks it",
	  adoption.next_share(0.1, 0.5) > 0.1 and adoption.next_share(0.1, -0.5) < 0.1)
check("a share stays between none and all", adoption.next_share(0.99, 1.0) <= 1.0 and adoption.next_share(0.01, -1.0) >= 0.0)
check("a bigger gap grows the share faster", adoption.next_share(0.1, 0.8) > adoption.next_share(0.1, 0.2))
check("a share of nothing never starts without a trial", adoption.next_share(0.0, 1.0) == 0.0)


def run(world, actor, years):
	events = []
	for _ in range(years):
		events += adoption.advance_actor(actor, world)
		world.year += 1
	return events


world = ContactWorld(margin=10.0)
adopter = firm()
adopter.knowledge.add("tech")
adopter.aware["tech"] = 100
events = run(world, adopter, 1)
check("an actor that knows a paying technique tries it on a pilot share", events == ["trying:tech"] and
	  adoption.stage_of(adopter, "tech") == "trying" and adoption.share_of(adopter, "tech") < 0.1, events)
run(world, adopter, 40)
check("the trial passes and the share grows towards all of production",
	  adoption.stage_of(adopter, "tech") == "adopted" and adoption.share_of(adopter, "tech") > 0.3, adopter.adoption)

world = ContactWorld(margin=-10.0)
sceptic = firm()
sceptic.knowledge.add("tech")
sceptic.aware["tech"] = 100
check("a technique that does not pay is not tried", run(world, sceptic, 5) == [] and "tech" not in sceptic.adoption)

world = ContactWorld(margin=10.0)
world.unsold["tech"] = ["tool"]
blocked = firm()
blocked.knowledge.add("tech")
check("a trial is refused for materials neither sold nor held", adoption.trial_refusals(blocked, "tech", world) == ["materials_unsold"])

# ---- the actor's own stock in the gate -----------------------------------------------------
needs = {"tool": 2.0}
check("a material no one sells blocks the start when the actor holds none",
	  research_gate.materials_short_of_stock(needs, lambda material: False, lambda material: 0.0) == ["tool"])
check("the actor's own stock covers it", research_gate.materials_short_of_stock(needs, lambda material: False, lambda material: 2.0) == [])
check("a seller covers it without stock", research_gate.materials_short_of_stock(needs, lambda material: True, lambda material: 0.0) == [])
stocked = firm()
stocked.record.stores["tool"] = 3.0
check("an actor reads its own record's stock", stocked.held_tonnes("tool") == 3.0 and stocked.held_tonnes("other") == 0.0)

# ---- the state's levers --------------------------------------------------------------------
context = government_levers.LeverContext(techniques={"tech"})
state = Government("government:x", ActorRecord(kind="government"))
change = government_levers.set_lever(state.record, {"lever": "trial_subsidy", "name": "tech", "value": 50.0}, context)
check("a state sets a trial subsidy through the lever command", change["after"] == 50.0 and state.record.levers["trial_subsidy"]["tech"] == 50.0)
refusal = government_levers.set_lever(state.record, {"lever": "tech_mandate", "name": "nope", "value": 0.5}, context)
check("a mandate on an unknown technique is refused with its cause", getattr(refusal, "cause", None) == "unknown_name")
refusal = government_levers.set_lever(state.record, {"lever": "tech_mandate", "name": "tech", "value": 1.5}, context)
check("a mandated share beyond all production is refused", getattr(refusal, "cause", None) == "value_out_of_range")

world = ContactWorld(margin=-10.0)
world.treasury.record.levers["trial_subsidy"] = {"tech": 50.0}
trier = firm()
trier.knowledge.add("tech")
trier.aware["tech"] = 100
before_state, before_firm = world.treasury.money, trier.money
run(world, trier, 2)
check("a subsidised trial starts though the technique does not pay, and the subsidy comes out of the treasury",
	  adoption.stage_of(trier, "tech") == "trying" and before_state - world.treasury.money > 0.0
	  and abs((before_state - world.treasury.money) - (trier.money - before_firm)) < 1e-9, (world.treasury.money, trier.money))
run(world, trier, 4)
check("an unpaying subsidised trial is never adopted for a subsidy alone",
	  adoption.stage_of(trier, "tech") != "adopted")

world = ContactWorld(margin=-10.0)
world.treasury.record.levers["tech_mandate"] = {"tech": 0.6}
ordered = firm()
ordered.knowledge.add("tech")
ordered.aware["tech"] = 100
run(world, ordered, 6)
check("a mandate holds the share at the ordered level whatever the margin",
	  adoption.stage_of(ordered, "tech") == "adopted" and adoption.share_of(ordered, "tech") >= 0.6, ordered.adoption)

world = ContactWorld(margin=10.0)
world.treasury.record.levers["trial_subsidy"] = {"tech": 5000.0}
trier = firm()
trier.knowledge.add("tech")
trier.aware["tech"] = 100
run(world, trier, 2)
check("a state pays no more than its treasury holds", world.treasury.money >= 0.0, world.treasury.money)
