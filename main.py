from typing import Dict

from toolchain.regx_engine import RegxEngine, RegxPattern


class RegxMatcher(MatchProvider):
    def __init__(self):
        self.matchers: Dict[str, tuple[str, str]] = dict()
        self.compiled: RegxPattern | None = None

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
        self.compiled = RegxEngine.compile(regex_str)

    def match(self, input_str, pos) -> tuple[str, str, str]:
        str_match = self.compiled.match(input_str, pos)
        name = str_match.lastgroup
        match = str_match[str_match.lastgroup]
        t_type = self.matchers[name][1]
        return name, match, t_type


rex: RegxPattern = RegxEngine.compile("(P+)")

m = rex.match("P")

print()
