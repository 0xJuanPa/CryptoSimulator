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
    def __init__(self, built_ins, agent_templates):
        self.built_ins: dict = built_ins
        self.agent_templates: dict = agent_templates
        self.lexer = Lexer(RegxMatcher(), ast.TOKEN_TYPE)
        self.parser = Parser(ast, ast.TOKEN_TYPE)

    def interpret_simulation(self, prog: str, market):
        '''
        returns a tuple of coin agents and traders agents with overrided behaviors
        '''
        tokens = self.lexer(prog)
        simulation: ast.Simulation = self.parser(tokens)
        static_checks = SemanticStaticChecker(self.built_ins.keys(), self.agent_templates)

        static_checks(simulation)  # todo remove funcs as 1st class ctz maybe

        coins = []
        traders = []

        ctx = ast.Context()
        for func in simulation.funcs:
            func: ast.FunDef
            ctx[func.name.name] = func

        for name, func in self.built_ins.items():
            ctx[name] = func

        ctx[ast.TOKEN_TYPE.MARKET_KW] = market
        tree_interpreter = TreeInterpreter(ctx)

        for agn in simulation.agents:
            agn: ast.AgentDec
            templateclass = self.agent_templates[agn.subtype.name]
            opts = tree_interpreter(agn.options)
            instance = templateclass(agn.name.name, **opts)

            for behavior in agn.behavior_list.elements:
                behavior: ast.FunDef
                childctx = ctx.create_child_context()
                childctx[ast.TOKEN_TYPE.MY_KW] = instance
                wrapped = tree_interpreter.make_native(behavior, childctx)
                setattr(instance, behavior.name.name, wrapped)
            if agn.type == ast.TOKEN_TYPE.COIN_KW:
                coins.append(instance)
            else:
                traders.append(instance)
        return coins, traders
