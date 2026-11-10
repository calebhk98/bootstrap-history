"""The producers the state's tax in kind can reach, worked out once a year: which stand on home tiles and make a good a harvest form
is paid in, with the goods each makes (`year_goods._tax_in_kind` reads it for every good's turn)."""
from typing import Dict, Iterable, Optional, Tuple

from .home_scope import has_partners, on_home_tile
from .producer_blocks import recipes_of, tiles_of

class HomeOutputs(dict):
    """producer id -> (its tile, the goods its recipe makes) for the producers the tax reaches; `known` holds every live producer the
    table was worked out for, so a producer it does not reach is not asked of the store again."""

    def __init__(self):
        super().__init__()
        self.known = set()


def taxed_goods(forms) -> Optional[frozenset]:
    """The goods the forms are paid in when every form is a harvest form (it assesses only those that made its good); None otherwise."""
    return frozenset(form.paid_in for form in forms) if all(form.basis == "harvest" for form in forms) else None


def reached(setup, tile: Optional[str], recipe_id: str, taxed, partners: Optional[bool] = None) -> bool:
    """Whether the tax in kind takes from a producer of this recipe on this tile."""
    recipe = setup.recipes[recipe_id]
    return not ((taxed is not None and taxed.isdisjoint(recipe.outputs)) or not on_home_tile(setup, tile, partners))


def home_outputs(setup, store, taxed) -> HomeOutputs:
    """Every producer of the store that the tax in kind reaches, in the order they entered, with its tile and its recipe's outputs."""
    partners = has_partners(setup)
    tile_names, recipe_names = store.names["tiles"].name_list, store.names["recipes"].name_list
    verdict: Dict[Tuple[int, int], bool] = {}
    found = HomeOutputs()
    for row in store.live_rows().tolist():
        found.known.add(store.ids[row])
        tile_number, recipe_number = int(store.table.tile[row]), int(store.table.recipe[row])
        key = (tile_number, recipe_number)
        if key not in verdict:
            verdict[key] = reached(setup, tile_names[tile_number], recipe_names[recipe_number], taxed, partners)
        if verdict[key]:
            found[store.ids[row]] = (tile_names[tile_number], tuple(setup.recipes[recipe_names[recipe_number]].outputs))
    return found


def reached_by(setup, store, taxed, producer_ids: Iterable[str], table: Optional[HomeOutputs]):
    """(producer id, tile, outputs) of the producers among `producer_ids`, in that order, that the tax in kind takes from. Those the
    year's table does not hold (or all of them, with no table) are asked of the store."""
    producer_ids = list(producer_ids)
    known = getattr(table, "known", ())
    asked = producer_ids if table is None else [each for each in producer_ids if each not in table and each not in known]
    own = {}
    for producer_id, tile, recipe_id in zip(asked, tiles_of(store, asked), recipes_of(store, asked)):
        if reached(setup, tile, recipe_id, taxed):
            own[producer_id] = (tile, tuple(setup.recipes[recipe_id].outputs))
    found = []
    for producer_id in producer_ids:
        entry = own.get(producer_id) if table is None or producer_id not in table else table[producer_id]
        if entry is not None:
            found.append((producer_id, *entry))
    return found
