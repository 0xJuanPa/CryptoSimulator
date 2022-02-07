from typing import Dict, List, Tuple

from toolchain.regx_engine import RegxPattern, RegxEngine
from . import ast_crypto as ast
from .lexer import MatchProvider, Lexer
from .parser import Parser
from .semantics import SemanticStaticChecker
from .tree_interpreter import TreeInterpreter


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


class SimulationInterpreter:
    def __init__(self,built_ins,agent_templates):
        self.built_ins : dict = built_ins
        self.agent_templates : dict = agent_templates
        self.lexer = Lexer(RegxMatcher())
        self.parser = Parser(ast)
        self.static_checks = SemanticStaticChecker(built_ins.keys(),agent_templates)
        # self.tree_interpreter = TreeInterpreter()

    def interpret_simulation(self, prog: str):
        '''
        returns a tuple of coin agents and traders agents with overrided behaviors
        '''
        tokens = self.lexer(prog)
        simulation : ast.Simulation = self.parser(tokens)
        self.static_checks.s_check(simulation)

        coins = []
        traders = []

        for funcs in simulation.funcs:
            # add to context
            pass

        for agn in simulation.agents:
            agn: ast.AgentDec
            templateclass = self.agent_templates[agn.type]
            opts = self.tree_interpreter(agn.options)
            instance = templateclass(agn.name,**opts)

            for behavior in agn.behavior_list.elements:
                behavior : ast.FunDef
                wrapped = self.tree_interpreter.wrap(behavior)
                instance[behavior.name] = wrapped

        return coins,traders