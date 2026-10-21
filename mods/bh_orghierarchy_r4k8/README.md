# Organisational Hierarchy (`bh_orghierarchy_r4k8`)

Feature: `Complaints/closed/104-directed-hours-need-organisational-hierarchy.md`. Directed work at scale needs
layers of managers; the cost should follow from a span-of-control rule, not from a flat effectiveness penalty.

## What it adds

Two code commands and an overhead on the directed-hours pool (no technologies, recipes, trades, constants, needs or
civilisations; the shipped game is unchanged unless the mod is allowed):

* `bh_orghierarchy_r4k8:hierarchy` (aliases `span`, `orgchart`), read only. Shows the hierarchy a workforce would need:
  span of control, layers, managers per layer, the manager hours that consumes against the directed-hours pool, the
  share of an order that survives the layers, which channel technologies are known, and for every listed technology
  the span and managers needed with and without it. `workers` or `hours` (worker-hours a year) ask about any size,
  so a firm or a state can read its own; the default is the player's staff.
* `bh_orghierarchy_r4k8:staff_managers`, opt in. Tops up managers to the number the rule needs by hiring them through
  the ordinary `sim.labour.hire` path (fee, first-year wage, the labour market's own supply limit); `release: true`
  lets the surplus go. It never runs by itself.

Turn on: `python3 sim/simulator.py mod-allow bh_orghierarchy_r4k8` (consent is local), then play any civilisation and
send `{"cmd":"bh_orghierarchy_r4k8:hierarchy","workers":5000}`.

## The rule

Span = a manager's supervising hours / the coordination hours one direct report costs per year. Managers over `W`
workers are `ceil(W / span)`, and the same rule applies to those managers until one apex actor directs the last layer.
Technologies cut the coordination hours per report along four channels (record keeping, messaging, measurement,
copying); the best known technology per channel counts and channels multiply. Messaging also cuts the loss per layer.
The technologies are shipped tree nodes (ledger, double entry, bureaucracy, tabulator, relay and stored-program
computers, semaphore, electric telegraph, telephone exchange, trunk lines, radio, statistics, statistical office,
control charts, printing press, typewriter); an id the loaded tree lacks is ignored.

## Labelled heuristics (`span_data.json`, each with `retire`)

Supervising share of a manager's hours; coordination hours per report; order loss per layer; every technology's
channel factor; the manager trade (`scribe`, since the shipped trades have no manager). All are placeholders for a
task model of orders, reports and corrections. No flat cap on hours exists anywhere.

## Known limits

* The overhead binds through `api.director_overhead`: the hours the apex spends on its own direct reports (reports
  times the coordination hours one costs, cut by the known technologies) count as committed. Managers hired with
  `staff_managers` take reports off the apex, lowest layer first. `staff_managers` stays a command: it spends the
  player's money, so no phase hires for them (a policy switch in `data/ui/policies.json` would be the way).
* No corruption, error-risk or response-delay mechanics beyond the order-loss figure.
* Hired managers are scribes, who also work as scribes; the mod only counts the ones it hired.
* The default headcount is the player's hired staff; free labour, deputies and state staff are not counted.
