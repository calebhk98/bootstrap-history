"""Living stock held as a material: what an actor holds, and what a node needs it to hold.

Stock (silkworm eggs, a founding herd, planting stock) is a quantity of a material in an
actor's ledger, kept in tonnes by the material's ledger key like any other stock. A node
may name `holds`, {material: units}, and cannot begin while the actor holds less. Nothing
here names a material or a civilisation; what is held and what is needed are data.
"""


def unheld(held_tonnes_of, holds, tonnes_per_unit_of):
    """[(material, units short)] for the materials in `holds` the actor holds too little of.

    `held_tonnes_of(material)` is the actor's stock in tonnes; `holds` is {material: units}.
    """
    short = []
    for material, units in sorted((holds or {}).items()):
        shortfall = float(units) - held_tonnes_of(material) / tonnes_per_unit_of(material)
        if shortfall > 1e-12:
            short.append((material, shortfall))
    return short
