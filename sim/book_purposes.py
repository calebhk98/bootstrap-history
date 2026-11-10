"""A posting's purpose as numbers: a template and the thing it names.

"sale of wheat_kg" is the template "sale of " and the reference "wheat_kg"; "consumption" is the template "consumption" and the
empty reference. The book never reads a purpose, it only adds up goods moved per (good, purpose) and quotes the purpose in a
refusal, so the pair is what a kernel carries and `decode` gives the text back exactly for the boundary.

A text that starts with one of REFERENCE_PREFIXES splits there; any other text is a template of its own. Templates and
references are `IdTable`s (saved with the book), so a purpose text nobody foresaw still works: it becomes a new template.
Reference 0 is the empty text, which every template without a reference uses."""
from typing import Dict, Optional, Tuple

from sim.book_index import SECOND_FIELD_BITS, THIRD_FIELD_BITS
from sim.book_types import BookError
from sim.compiled_tables.ids import IdTable

REFERENCE_PREFIXES = ("sale of ", "wages for ", "carriage of ", "tax:", "state ")
NO_REFERENCE = 0     # the reference id of the empty text


def split_text(text: str) -> Tuple[str, str]:
    """(template text, reference text): the text splits after the first of REFERENCE_PREFIXES it starts with."""
    for prefix in REFERENCE_PREFIXES:
        if text.startswith(prefix):
            return prefix, text[len(prefix):]
    return text, ""


class Purposes:
    def __init__(self):
        self.templates = IdTable("purpose")
        self.references = IdTable("reference", [""])
        self._split: Dict[str, Tuple[int, int]] = {}

    def encode(self, text: str) -> Tuple[int, int]:
        """(template id, reference id) for the purpose text, admitting what is new."""
        found = self._split.get(text)
        if found is None:
            template, reference = split_text(text)
            found = (int(self.templates.admit([template])[0]), int(self.references.admit([reference])[0]))
            if found[0] >= 1 << SECOND_FIELD_BITS or found[1] >= 1 << THIRD_FIELD_BITS:
                raise BookError("the book cannot number so many purposes")
            self._split[text] = found
        return found

    def find(self, text: str) -> Optional[Tuple[int, int]]:
        """(template id, reference id) for the purpose text, or None when the book never numbered either part (nothing is admitted)."""
        template, reference = split_text(text)
        template_number, reference_number = self.templates.find(template), self.references.find(reference)
        return None if template_number is None or reference_number is None else (template_number, reference_number)

    def encode_many(self, texts) -> Tuple[list, list]:
        """The template ids and the reference ids of the purpose texts, in order (what `encode` gives each, as two lists)."""
        split = self._split
        templates, references = [], []
        for text in texts:
            found = split.get(text)
            if found is None:
                found = self.encode(text)
            templates.append(found[0])
            references.append(found[1])
        return templates, references

    def decode(self, template: int, reference: int) -> str:
        """The purpose text for a (template id, reference id) pair."""
        return self.templates.name(template) + self.references.name(reference)

    def state(self) -> dict:
        return {"templates": self.templates.state(), "references": self.references.state()}

    @classmethod
    def from_state(cls, state: dict) -> "Purposes":
        purposes = cls()
        purposes.templates = IdTable.from_state("purpose", state["templates"])
        purposes.references = IdTable.from_state("reference", state["references"])
        return purposes
