"""`replaced(instance, **changes)`: `dataclasses.replace` for the plain records the year rebuilds thousands of
times. A dataclass with no `__post_init__`, no slots and no init-only or non-init fields is copied through its
attribute dictionary; any other class goes the long way."""
import dataclasses
from typing import Dict

_plain: Dict[type, object] = {}      # class -> its field names when it copies directly, else False


def _field_names(cls: type):
    """The field names when `cls` can be copied through its dictionary, else False."""
    if hasattr(cls, "__slots__") or hasattr(cls, "__post_init__"):
        return False
    fields = dataclasses.fields(cls)
    if any(not each.init for each in fields):
        return False
    for each in cls.__dict__.get("__annotations__", {}).values():
        if each is dataclasses.InitVar or isinstance(each, dataclasses.InitVar):
            return False
    return frozenset(each.name for each in fields)


def replaced(instance, **changes):
    cls = type(instance)
    names = _plain.get(cls)
    if names is None:
        names = _plain[cls] = _field_names(cls)
    if names is False or not names.issuperset(changes):
        return dataclasses.replace(instance, **changes)
    copy = object.__new__(cls)
    attributes = copy.__dict__
    attributes.update(instance.__dict__)
    attributes.update(changes)
    return copy
