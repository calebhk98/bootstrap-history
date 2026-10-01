"""Things an actor will not do: a persistent exclusion list the automatic starters honour.

Methods of Sim, a mixin only so they live in a file of their own. The list
is `state.projects.excluded`, saved with the game. An entry is a node id,
`category:<category>` or `trait:<trait>`.
"""

CATEGORY_PREFIX = "category:"
TRAIT_PREFIX = "trait:"


class ExclusionsMixin:

    def exclusion_entry_known(self, entry):
        """Whether an exclusion entry names a node, a category or a trait that exists."""
        if entry.startswith(CATEGORY_PREFIX):
            return any(node.get("cat") == entry[len(CATEGORY_PREFIX):] for node in self.nodes.values())
        if entry.startswith(TRAIT_PREFIX):
            return any(entry[len(TRAIT_PREFIX):] in node.get("traits", ()) for node in self.nodes.values())
        return entry in self.nodes

    def exclusion_reason(self, node_id):
        """Why the actor excluded this node, in words, or None when it is not excluded."""
        excluded = self.state.projects.excluded
        if not excluded:
            return None
        node = self.nodes.get(node_id, {})
        if node_id in excluded:
            return "you excluded it by name"
        category = node.get("cat")
        if CATEGORY_PREFIX + str(category) in excluded:
            return "you excluded the category %s" % category
        for trait in node.get("traits", ()):
            if TRAIT_PREFIX + trait in excluded:
                return "you excluded everything with the trait %s" % trait
        return None
