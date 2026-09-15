# Trade-hours status falsely reports machinists as booked

**Type:** Status/constraint bug  
**Priority:** High

## Player evidence

`master_screw` and later `micrometer_gauges` said machinist hours were booked elsewhere despite `portfolio` showing demand below supply, `oversubscribed: false`, and no competing machinist project. The project later progressed normally.

## Impact

A player may hire/train unnecessary workers or incorrectly stop a viable project.

## Suggested check

Make the per-project waiting reason use the same allocation data as `portfolio`; add a regression test for demand < supply.
