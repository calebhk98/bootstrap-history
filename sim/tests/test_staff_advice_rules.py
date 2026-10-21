"""The remedies named when a household is short of artisans or scholars (Complaint 640): called on sources and
callbacks built here, no game. Checks read the remedy records, not the wording."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.labour.staff_advice import staff_remedies

SOURCES = [("HIRE", "hire somebody"), ("workshop_first", "somewhere for them to work"),
           ("school_founded", "a school trains scholars"), ("BUY", "buy slaves")]


def advise(done=(), operating=(), visible=("workshop_first", "school_founded"), waiting=(), deficit=None,
           sources=SOURCES, ventures=("workshop_first", "school_founded")):
    return staff_remedies("artisans", sources, deficit, set(done), set(operating), lambda node: node in ventures,
                          lambda node: node in visible, lambda node: node in waiting,
                          lambda kind, count: "hire %d %s" % (count, kind))


def actions(steps):
    return [remedy for _sentence, remedy in steps]


steps = advise()
check("hiring is always offered, and so is buying",
      {"action": "hire", "node": None} in actions(steps) and {"action": "buy", "node": None} in actions(steps), steps)
check("an unbuilt institution the player can see is offered to build",
      {"action": "build", "node": "workshop_first"} in actions(steps), steps)
check("the remedies come in the order of the sources",
      [remedy["action"] for remedy in actions(steps)] == ["hire", "build", "build", "buy"], steps)
check("an institution the player has never heard of is not named",
      all(remedy.get("node") != "school_founded" for remedy in actions(advise(visible=("workshop_first",)))))
check("advice never points at a remedy waiting on the thing it supplies: it says build it after hiring",
      {"action": "build_after_hiring", "node": "workshop_first"} in actions(advise(waiting=("workshop_first",)))
      and {"action": "build", "node": "workshop_first"} not in actions(advise(waiting=("workshop_first",))))
check("an institution that is reachable is offered plainly once it no longer waits",
      {"action": "build", "node": "workshop_first"} in actions(advise(waiting=())))
check("a school built and then shut is offered back to reopen, not treated as covered",
      {"action": "reopen", "node": "school_founded"} in actions(advise(done=("school_founded",))))
check("a school built and running adds nothing to the advice",
      all(remedy.get("node") != "school_founded" for remedy in actions(advise(done=("school_founded",), operating=("school_founded",)))))
check("a built work that is not a concern cannot be reopened, so it is not offered",
      all(remedy.get("node") != "school_founded"
          for remedy in actions(advise(done=("school_founded",), ventures=("workshop_first",)))))
check("a built work shut or running is never offered to build again",
      all(remedy["action"] != "build" or remedy["node"] != "school_founded"
          for remedy in actions(advise(done=("school_founded",)))))
sized = advise(deficit=3.2)
check("the hire advice is sized to the whole people the household is short, rounded up",
      sized[0][0] == "hire 4 artisans", sized[0])
check("without a deficit the hire source says its own text", advise()[0][0] == "hire somebody")
check("a deficit of exactly three whole people asks for three", advise(deficit=3.0)[0][0] == "hire 3 artisans")
check("no sources, no remedies", advise(sources=[]) == [])
check("a source with only a node and nothing to build reads as nothing",
      advise(sources=[("workshop_first", "x")], visible=()) == [])
