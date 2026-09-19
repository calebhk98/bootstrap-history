# One historical disaster should be one expandable event

The 1519 invasion and the 410 Sack of Rome each manifested as several separate log entries: seizure, staff loss, project reset, knowledge loss, value changes, arrears, etc. Reconstructing "what just happened?" required scanning multiple entries.

## WHY IT MATTERS

A major catastrophe should be presented as a single comprehensible event. The current per-consequence fragmentation obscures the scope and interconnection of impacts and forces players to manually reconstruct the situation from multiple log lines.

## WHAT WOULD RESOLVE IT

Group by causal event:

```text
Spanish invasion — 1519
- population: ...
- staff: ...
- capital seized: ...
- projects reset: ...
- technologies forgotten: ...
- social/value changes: ...
```

Keep sub-events expandable for debugging.

## WHERE IT LIVES

Event generation and rendering logic in `sim/engine/proto/render_screens_big.py` or `render_screens_status.py`. Event aggregation would likely be in `sim/engine/` event system or hazard-related modules.

## Confidence

Design recommendation

## Cross-references

Related to the repetition audit (section 5, item 6: "Event fragmentation"). UX-010 in findings is this complaint. Also related to UX-011 (event severity needs visual hierarchy) and UX-012 (large completion waves summary-first).
