# `capacity` is essential but omitted from main help

**Status:** closed

**Type:** Discoverability  
**Priority:** Medium
**Audit (2026-09-18): RESOLVED, verified.** `capacity` is now listed in `help commands` (`sim/ui/proto/help.py`) with an explicit annual-throughput-vs-durable-stock distinction, and a separate `materials` command/report now covers durable stock on hand. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

The command was only discovered through an error message. It exposes material throughput, demand/surplus, power, project constraints, trade capacity, financing, and the resource throttle; `help commands` did not list it.

## Suggested change

Add `capacity` to the main command index and explain that materials are modeled as annual throughput, not a warehouse inventory.
