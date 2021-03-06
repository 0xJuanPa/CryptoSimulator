from typing import Dict

from toolchain.automaton import Automaton
from . import ast_regex as ast
from .lexer import Lexer, MatchProvider
from .parser import Parser


class DummyComplementMatcher(MatchProvider):
    def __init__(self):
        self.matchers: Dict[str, str] = dict()

    def add_matcher(self, sty: tuple[str, str, str]):
        self.matchers[sty[1]] = sty[0]

    def initialize(self):
        pass

    def match(self, mathcstr, pos) -> tuple[str, str, str]:
        char = mathcstr[pos]
        if char in self.matchers:
            return (self.matchers[char], char, "")
        else:
            return (self.matchers[""], char, "")


class RegxMatch:
    def __init__(self):
        self._groups = dict()
        self.lastgroup = None
        self.match: str = ""

    def __getitem__(self, item):
        return self._groups.get(item, None)

    def __setitem__(self, key, value):
        self._groups[key] = value
        self.lastgroup = key

    def __repr__(self):
        res = f"0:{self.match} grp:{self._groups.items()}"
        return res


class RegxPattern:
    def __init__(self, compiled):
        self.compiled: Automaton = compiled

    def match(self, input_str: str, pos=0) -> str:
        curr_state = self.compiled.initial_state
        match = ""
        while pos < len(input_str):
            char = input_str[pos]
            if char not in curr_state.transitions:
                break
            curr_state = curr_state[char]
            match += char
            pos += 1
        return match if curr_state.final else None


class RegxEngine:
    def __init__(self):
        self.tokeizer = Lexer(DummyComplementMatcher())
        self.parser = Parser(ast)

    def compile(self, regex_str) -> RegxPattern:
        tokens = self.tokeizer(regex_str)
        reg_ast = self.parser(tokens)
        nfa = reg_ast.eval()
        dfa = nfa.get_dfa()
        res = RegxPattern(dfa)
        return res
