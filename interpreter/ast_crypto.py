from abc import ABC
from dataclasses import dataclass
from enum import auto, Enum

from toolchain.regx_engine.lexer import Token


# will wait because enum issue
class TOKEN_TYPE(Enum):
    # grouppers
    O_PAR = auto()
    C_PAR = auto()
    O_BRACKETS = auto()
    C_BRACKETS = auto()
    O_BRACES = auto()
    C_BRACES = auto()

    # sepparators
    LBREAK = auto()
    SPACE = auto()
    TAB = auto()
    SL_COMMENT = auto()

    DDOT = auto()
    DOT = auto()
    COMMA = auto()
    SEMICOLON = auto()

    PLUS = auto()
    MINUS = auto()
    MULT = auto()
    MOD = auto()
    FLOORDIV = auto()
    DIV = auto()

    AND = auto()
    OR = auto()
    GT = auto()
    GE = auto()
    LT = auto()
    LE = auto()
    EQ = auto()
    NEQ = auto()

    ASSIGN = auto()

    NOT = auto()
    NEG = auto()

    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # control statements
    FOR = auto()  # ?
    WHILE = auto()
    IF = auto()
    ELSE = auto()
    RET = auto()
    FUNC = auto()

    COIN_KW = auto()
    TRADER_KW = auto()
    MY_KW = auto()
    MARKET_KW = auto()


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


class ArgList(PList):
    pass


class StatementList(PList):
    pass


class ExpresionList(PList):
    pass


class OptList(PList):
    pass


## EXPRESSIONS

class Expression:
    pass


class Literal(Expression):
    def __init__(self, value: Token):
        match value.name:
            case TOKEN_TYPE.NUMBER:
                val = float(value.lexeme) if "," in value.lexeme else int(value.lexeme)
            case TOKEN_TYPE.STRING:
                val = value.lexeme
            case _:
                raise Exception("Not supported literal")
        self.value = val


class Identifier(Expression):
    def __init__(self, name):
        self.name = name.lexeme


class UnmanagedType(Expression):
    def __init__(self, val):
        self.value = val


@dataclass
class FunCall(Expression):
    name: Identifier
    Args: ExpresionList = None


@dataclass
class AttrRes(Expression):
    parent: Identifier
    attr: Identifier | FunCall


## OPERATORS

class BinaryOp(Expression, BinaryAtom):
    def __init__(self, x, y, op: Token):
        super().__init__(x, y)
        self.op: TOKEN_TYPE = op.name


class UnaryOp(Expression, UnaryAtom):
    def __init__(self, x, op: Token):
        super().__init__(x)
        self.op: TOKEN_TYPE = op.name


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


@dataclass
class Assign(Statement):
    left: Identifier
    value: Expression


@dataclass
class Ret(Statement):
    value: Expression


## TOP LEVEL STATEMENTS


class TopLevelSt:
    pass


@dataclass
class AgentDec(TopLevelSt):
    type: Token
    name: Identifier
    subtype: Identifier
    options: PList
    behavior_list: PList


@dataclass
class FunDef(TopLevelSt):
    name: Identifier
    body: StatementList
    params: ArgList = None


class Simulation(Atom):
    def __init__(self, top_level_sts):
        self.agents = []
        self.funcs = []
        for top in top_level_sts.elements:
            if isinstance(top, FunDef):
                self.funcs.append(top)
            else:
                self.agents.append(top)


class Context(dict):
    def __init__(self, parentctx=None):
        super().__init__()
        self.parentctx: Context = parentctx

    def __contains__(self, item):
        if super().__contains__(item):
            return True
        elif self.parentctx is not None:
            return item in self.parentctx
        return False

    def __getitem__(self, item):
        if super().__contains__(item):
            return super().__getitem__(item)
        elif self.parentctx is not None:
            return self.parentctx[item]
        raise KeyError("Not defined in context")

    def create_child_context(self):
        ctx = Context(self)
        return ctx
