"""A declared kind named in a civilisation's cast becomes a roster entry (cast_from_civilisations) and, when the roster is seeded, an actor of
that kind with its members (seed_cast). Its yearly turn is test_mod_actor_kinds."""
from sim.agents.api import ActorRegistry, ActorsState, cast_from_civilisations, declared_kind_classes, seed_cast, shipped_extensions

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

KIND = "test_acme_k3f9:elf"
EXTENSIONS = shipped_extensions()
EXTENSIONS.kinds.update(declared_kind_classes(
    {KIND: {"needs": {"food": 1.0}, "birth_rate": 0.04, "death_rate": 0.02, "famine_death_rate": 0.3, "trade": "labourer"}}))

civ = dict(S.load_civ("rome_100ad"))
civ["cast"] = dict(civ.get("cast") or {}, actors=[{"actor_id": "elves:one", "kind": KIND, "name": "elves", "params": {"members": 500.0}}])
home_country, entries, profiles = cast_from_civilisations(civ, [])
elf_entries = [entry for entry in entries if entry.actor_id == "elves:one"]
check("a declared actor in the home civilisation's cast becomes one roster entry of its kind, at home",
      len(elf_entries) == 1 and elf_entries[0].kind == KIND and elf_entries[0].country is None and elf_entries[0].params == {"members": 500.0}, entries)

registry = ActorRegistry(ActorsState(home_country=home_country), EXTENSIONS)
created = seed_cast(registry, home_country, elf_entries, profiles)
elves = registry.actors.get("elves:one")
check("seeding creates the declared kind's actor from the entry, with the members the entry gives",
      created == ["elves:one"] and elves is not None and elves.kind == KIND and elves.record.members == 500.0, (created, registry.actors))
check("seeding a second time creates nothing and leaves the actor alone", seed_cast(registry, home_country, elf_entries, profiles) == [] and elves.record.members == 500.0)
