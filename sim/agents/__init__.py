"""Economic actors: things that own money, staff and know-how, and decide.

`Actor` is the shared base. `Household` is the founder's, `Government` a
country's state, `Firm` an independent business. Each decides through a
`Policy`, so a player, an AI or a mod can drive any of them. Outside code
imports from `sim.agents.api` only. Design: `docs/architecture/ACTORS.md`.
"""
