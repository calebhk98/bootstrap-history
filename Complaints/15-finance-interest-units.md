# Credit forecast labels an interest rate as annual interest

**Type:** Units/display bug  
**Priority:** Medium

## Player evidence

For a 63,636-den projected blast-furnace loan, the UI printed “interest per year on it: 6.9.” The state rate was 6.9%, while actual annual interest would be roughly 4.4k den.

## Suggested change

Show both `rate: 6.9%` and `estimated annual interest: ~4,391 den`.
