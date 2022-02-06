from abc import ABC
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


## EXPRESSIONS

class Expression:
    pass


class BinaryExpresion(Expression, BinaryAtom):
    pass


class UnaryExpression(Expression, UnaryAtom):
    pass


class String(UnaryExpression):
    pass


class Number(UnaryExpression):
    pass


class Identifier(UnaryExpression):
    pass


class Fcall(Expression):
    id: Identifier
    Args: ArgList = None


## OPERATORS

class BinaryOp(BinaryExpresion):
    pass


class UnaryOp(UnaryExpression):
    pass


## TOP LEVEL STATEMENTS


class TopLevelSt:
    pass

@dataclass
class AgentDec(TopLevelSt):
    name : Identifier
    subtype : Identifier
    options : OptList
    behavior_list: BehaviorList


@dataclass
class FunDef(TopLevelSt):
    id: Identifier
    params: ArgList
    body: StatementList


# STATEMENTS

class Statement:
    pass


@dataclass
class If(Statement):
    condition: Expression
    then_body: StatementList
    else_body: StatementList = None


@dataclass
class While(Statement):
    condition: Expression
    body: StatementList


class Assign(Statement):
    id: Identifier
    value: Expression


class Ret(Statement):
    value: Expression
