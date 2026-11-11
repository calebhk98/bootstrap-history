"""`ProducerStore.to_plain` as it was: one row at a time through `_fields`."""


def plain_producers(store):
    store.compact()
    return {store.ids[row]: store._fields(row) for row in store.order().tolist()}
