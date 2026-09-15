# Zero-duration capabilities require a year boundary

**Type:** Interaction/timing mismatch  
**Priority:** Low

## Player evidence

`cap_measure_temp` had zero cost, zero founder-hours, zero calendar floor, and no failure chance, but its dependent capability remained unavailable until a turn boundary. A zero-cost platinum capability showed the same pattern.

## Suggested change

Complete truly instantaneous projects immediately, or label them as resolving at the next annual tick.
