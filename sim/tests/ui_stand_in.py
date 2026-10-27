"""A stand-in game for the screens' rules: `view(name)` answers from the values a test gives, so a rule is called on plain values.

    game = StandIn(year=1301, tree_nodes=NODES)                       # a table view: its value
    game = StandIn(visibility=lambda node_id, memo=None: node_id in seen)   # a quote or keyed view: a function of its arguments

A view asked for that the test did not give is an error naming it. A command sent is kept in `sent` and answered with
`answers.get(type(command))`."""


class _Answer:
    def __init__(self, value):
        self.value = value

    def __call__(self, *arguments, **keywords):
        return self.value(*arguments, **keywords) if callable(self.value) else self.value

    def __getitem__(self, key):
        return self.value(key) if callable(self.value) else self.value[key]


class StandIn:
    def __init__(self, answers=None, **views):
        self._views = views
        self.sent = []
        self.answers = answers or {}

    def view(self, name):
        if name not in self._views:
            raise KeyError("the stand-in game was given no view %r" % name)
        return _Answer(self._views[name])

    def send(self, command):
        self.sent.append(command)
        return self.answers.get(type(command))
