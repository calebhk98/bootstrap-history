# Funding UI should distinguish four different concepts more aggressively

Early Rome play repeatedly exposed the difference between these four funding concepts, which are often conflated under a single "funding capacity" headline:

- cash on hand
- credit available now
- sustainable annual surplus
- total multi-year commitment or future installments

## Why it matters

A headline "funding capacity" can look like money that may be safely committed immediately when it is not. Players can mislead themselves into overcommitting if these concepts are not clearly distinguished.

## What would resolve it

Display all four together in a clear hierarchy:

```text
CASH ON HAND: 45,000
CREDIT AVAILABLE: 30,000
IMMEDIATE CAPACITY: 75,000

Sustainable annual surplus: 12,000/year
Multi-year projects already committed: 200,000 over 10 years
```

This makes it explicit what can be spent now versus what requires future revenue to sustain.

## Where it lives

Likely in `sim/engine/proto/state.py` where the main state view is built, and `sim/engine/economy.py` where spending power is calculated.

**Confidence:** Design recommendation
