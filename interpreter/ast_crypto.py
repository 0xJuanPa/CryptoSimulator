from abc import abstractmethod, ABC
from dataclasses import dataclass

from toolchain.regx_engine.lexer import Token


class OptList:
    pass

class BehaviorList:
    pass

class ArgList:
    pass


class StatementList:
    pass

class Program:
    pass


class AgentDec:
    pass

class Behavior:
    pass

class FunDef:
    pass

@dataclass
class Atom(ABC):
    @abstractmethod
    def eval(self):
        pass

@dataclass
class UnaryAtom(Atom, ABC):
    first: Atom | Token


@dataclass
class BinaryAtom(Atom, ABC):
    first: Atom | Token
    second: Atom | Token


class String(UnaryAtom):
    pass


class Number(UnaryAtom):
    pass

class Identifier(UnaryAtom):
    pass

class Fcall(BinaryAtom):
    pass



class If(BinaryAtom):
    pass

class While(BinaryAtom):
    pass

class Ret(UnaryAtom):
    pass

class FunDec(BinaryAtom):
    pass

class Assign:
    pass


class Eq(BinaryAtom):
    pass

class Neq(BinaryAtom):
    pass

class Gt(BinaryAtom):
    pass

class Geq(BinaryAtom):
    pass

class Lt(BinaryAtom):
    pass

class Leq(BinaryAtom):
    pass

class Sum(BinaryAtom):
    pass

class Sub(BinaryAtom):
    pass

class Mul(BinaryAtom):
    pass

class Div(BinaryAtom):
    pass

class Fdiv(BinaryAtom):
    pass

class Mod(BinaryAtom):
    pass

class And(BinaryAtom):
    pass

class Or(BinaryAtom):
    pass

class Not(UnaryAtom):
    pass

class Neg(UnaryAtom):
    pass









