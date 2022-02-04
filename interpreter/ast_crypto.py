from abc import abstractmethod, ABC
from dataclasses import dataclass

from toolchain.regx_engine.lexer import Token


@dataclass
class Atom(ABC):
    # @abstractmethod
    def eval(self):
        pass


@dataclass
class UnaryAtom(Atom, ABC):
    first: Atom | Token


@dataclass
class BinaryAtom(Atom, ABC):
    first: Atom | Token
    second: Atom | Token


class PList:
    def __init__(self, plist, elem=None):
        self.elements = []
        if isinstance(plist, PList):
            self.elements.extend(plist.elements)
        elif plist is not None:
            self.elements.append(plist)
        if elem is not None:
            self.elements.append(elem)


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


class Assign(BinaryAtom):
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


class OptList(PList):
    pass


class TopLevelList(PList):
    pass

class BehaviorList(PList):
    pass


class ArgList(PList):
    pass


class StatementList(PList):
    pass

class ExpresionList(PList):
    pass


class AgentDec:
    pass


class Behavior:
    pass

@dataclass
class FunDef:
    id : Identifier
    params : ArgList
    Body : StatementList
