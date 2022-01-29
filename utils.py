class EquivalentSet(set):
    class Grabber:
        def __init__(self, item):
            self.item = item
            self.capture = None

        def __eq__(self, other):
            res = hash(self) == hash(other)
            self.capture = other if res else None
            return res

        def __hash__(self):
            return hash(self.item)

    def get_equivalent(self, item):
        g = self.Grabber(item)
        super().__contains__(g)
        return g.capture


class PyReMatcher(MatchProvider):
    def __init__(self):
        self.matchers: Dict[str, tuple[str, str]] = dict()
        self.compiled: Pattern | None = None

    def add_matcher(self, sty: tuple[str, str, str]):
        if self.compiled is not None:
            raise Exception("Already Initialized")
        self.matchers[sty[0]] = sty[1:]

    def initialize(self):
        if self.compiled is None:
            regex_str = ""
            for name, matcher in self.matchers.items():
                regex = matcher[0]
                regex_str += ('|' if regex_str else "") + f"(?P<{name}>{regex})"
        self.compiled = re.compile(regex_str)

    def match(self, input_str, pos) -> tuple[str, str, str]:
        str_match = self.compiled.match(input_str, pos)
        name = str_match.lastgroup
        match = str_match[str_match.lastgroup]
        t_type = self.matchers[name][1]
        return name, match, t_type