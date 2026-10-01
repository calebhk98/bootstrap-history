# `tx2_silkworm_stock` has `sea_monsoon_route` as its prerequisite, so Han holds an Indian Ocean route node to hold its own silkworm

**Status:** closed - `tx2_silkworm_stock` takes the monsoon route or the new `tx2_silkworm_native_stock` (`req_any`); Han holds the native stock and no longer `sea_monsoon_route`

`tx2_silkworm_stock` ("through the Asian trade route") lists `sea_monsoon_route`
as a prerequisite because it was written for a Roman founder acquiring eggs.
Han holds the node now only so the chain's prerequisite check is met; it holds
it in no other sense, and it may change Han's reach by sea.

## What it would take

A prerequisite that says "silkworm eggs reachable" (a source-region node, or
a `req_any` of the Asian route and sericulture-holding origin), so a civilisation
that already has the worm does not need a sea route. Remove `sea_monsoon_route`
from Han's `starting_techs` once the node allows it.

Checked: Han's reach by region and its route to Rome are identical before and after; no other node Han holds listed `sea_monsoon_route` in `pre`. Starting techs are not required to be prerequisite-closed (`test_civilisation_prerequisites` pins known violations), but that test only reads `pre`, so `req_any` options are not checked there.
