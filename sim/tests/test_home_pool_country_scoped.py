"""The home pool of a trade is left what the home country's actors do not employ: a foreign actor's staff come from that
country's labour, so they are not subtracted from home (Complaint 649)."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState

registry = ActorRegistry(ActorsState(home_country="home"))
registry.add("firm:home", ActorRecord(kind="firm", workforce={"smith": 3.0}))
registry.add("firm:nowhere", ActorRecord(kind="firm", country=None, workforce={"smith": 2.0}))
registry.add("firm:abroad", ActorRecord(kind="firm", country="abroad", workforce={"smith": 7.0}))

home_staff = registry.home_staff_fte("smith")
check("the home count takes home actors and actors with no country", abs(home_staff - 5.0) < 1e-9, home_staff)
check("the home count leaves out one actor's own staff",
	  abs(registry.home_staff_fte("smith", excluding="firm:home") - 2.0) < 1e-9)
check("a foreign actor's own exclusion changes nothing at home",
	  abs(registry.home_staff_fte("smith", excluding="firm:abroad") - 5.0) < 1e-9)
check("the country's count takes only its actors",
	  abs(registry.staff_fte_in_country("smith", "abroad") - 7.0) < 1e-9)
