# Goods no technique in reach makes and no partner sells are priced as if imported from nowhere, so households want them

**Status:** closed - pinned by sim/tests/test_one_goods_market.py and sim/tests/test_market_records_ownership.py

`priced_goods_table` falls back to the mature-technique table for a good nothing in reach makes, standing for an import (a labelled transitional shortcut). Rome prices pepper and cassia this way. With foreign partners modelled, that import is imaginary: households' seasoning need goes active and wants pepper at a price no seller offers, and the demand is never met (see 350).

Fix: a good is offered by a modelled seller (home technique or a partner, priced at its cost, freight and merchants' terms) or it cannot be had and its need draws no spending; remove the mature fallback for goods once partners can supply them.
