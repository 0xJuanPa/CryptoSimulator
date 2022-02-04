from typing import Dict, List, Tuple

from toolchain.regx_engine import RegxPattern, RegxEngine
from . import ast_crypto as ast
from .lexer import MatchProvider, Lexer
from .parser import Parser
from .visitor import visitor


# this MatchProvider is a re matcher have to modify it cause capturing groups will not be implemented at the moment
class RegxMatcher(MatchProvider):
    def __init__(self):
        self.matchers: Dict[str, tuple[str, str]] = dict()
        self.compiled: List[Tuple[str, RegxPattern]] | None = None

    def add_matcher(self, sty: tuple[str, str, str]):
        if self.compiled is not None:
            raise Exception("Already Initialized")
        self.matchers[sty[0]] = sty[1:]

    def initialize(self):
        if self.compiled is None:
            self.compiled = []
            for name, matcher in self.matchers.items():
                regex = matcher[0]
                pattern = RegxEngine.compile(regex)
                self.compiled.append((name, pattern))

    def match(self, input_str, pos) -> tuple[str | None, str | None, str | None]:
        name = None
        match = None
        for name, matcher in self.compiled:
            match = matcher.match(input_str, pos)
            if match:
                break
        t_type = self.matchers[name][1]
        return (name, match, t_type) if match else (None, None, None)


class Interpreter:
    @visitor
    def run(self, prog: str):
        lexer = Lexer(RegxMatcher())
        parser = Parser(ast)
        tokens = lexer(prog)
        pr = parser(tokens)
        print()
