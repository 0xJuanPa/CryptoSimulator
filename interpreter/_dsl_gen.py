import os.path
from enum import Enum, auto

from toolchain.frontend_generator import Grammar


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
    COMMENT = auto()

    ASSIGN = auto()
    DOT = auto()
    PLUS = auto()
    MINUS = auto()
    MULT = auto()
    DIV = auto()
    FLOORDIV = auto()

    AND = auto()
    OR = auto()
    GT = auto()
    GE = auto()
    LT = auto()
    LE = auto()
    EQ = auto()
    NEQ = auto()

    NOT = auto()
    NEG = auto()

    NONE = auto()
    NUMBER = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()
    IDENTIFIER = auto()

    # control statements
    FOR = auto()
    WHILE = auto()
    IF = auto()
    ELSE = auto()
    RETURN = auto()


dsl = Grammar()

non_term = "".split(",")

# epsilon terminal
eps = dsl.epsilon

# ignored terminals
space, lbreak, tab, sl_comment = dsl.symbol_emit(("space", " "), ("lbreak", "\n|\r\n"), ("tab", "\t"),
                                                 ("sl_comment", "#.*(\n|\r\n)"))

# groups terminals
o_par, c_par, o_brack, c_brack, o_brace, c_brace = dsl.symbol_emit(("o_par", "("), ("c_par", ")"), ("o_brack", "["),
                                                                   ("c_brack", "]"), ("o_brace", "{"), ("c_brace", "}"))

# general pourpouse keyword terminals
ifkw, elsekw, whilekw, funkw, retkw = dsl.symbol_emit(("if", "if"), ("else", "else"), ("while", "while"),
                                                      ("func", "func"), ("ret", "ret"))
# spec keywords terminals
traderkw, coinkw, eventkw = dsl.symbol_emit(("trader", "trader"),
                                            ("coin", "coin"), ("event", "event"))

# literals terminals
identifier, string, num = dsl.symbol_emit(("identifier", r"[A-Za-z][\dA-Z_-a-z]*"), ("string", "'[^']*'"),
                                          ("num", r"\d+|\d+[,.]\d+"))

# operators terminals
assign = dsl.symbol_emit(("assign", "="))

# unary operators terminals
not_, neg = dsl.symbol_emit(("not", "!"), ("neg", "-"))

# binary operatos priority 0
mul, div, fdiv, mod = dsl.symbol_emit(("mul", r"\*"), ("div", "/"), ("fdiv", "//"), ("mod", "%"))

# binary operatos priority 1
plus, minus = dsl.symbol_emit(("plus", r"\+"), ("minus", "-"))

# binary operatos priority 2
or_, and_ = dsl.symbol_emit(("or", r"\|"), ("and", "&"))

# binary operatos priority 3
eq, neq, gt, geq, lt, leq = dsl.symbol_emit(("eq", "=="), ("neq", "!="), ("gt", ">"), ("geq", ">="), ("lt", "<"),
                                            ("leq", "<="))

# splitter terminals
comma, dot, ddot = dsl.symbol_emit(("comma", ","), ("dot", "\."), ("ddot", ":"))

# initial NonTerminal
CryptoDsl = dsl.symbol_emit("CryptoDsl")
dsl.initial_symbol = CryptoDsl

# Nonterminals for language specs
TopLevelStList, TopLevelSt, EntDec, Entkwgrp, Opts, OptsList, Behavior, BehaviorList = dsl.symbol_emit(
    *"TopLevelStList,TopLevelSt,EntDec,Entkwgrp,Opts,OptsList,Behavior,BehaviorList".split(","))

# Non Terminals for Statements and Args
StatementList, Statement = dsl.symbol_emit(*"StatementList,Statement".split(","))

# Non Terminals for Keywords
If, Else, While = dsl.symbol_emit(*"If,Else,While".split(","))

# Non Terminals for Expressions
Expr, CmpExpr, ArithExpr, Term, Factor, Atom = dsl.symbol_emit(*"Expr,CmpExpr,ArithExpr,Term,Factor,Atom".split(","))

FunDef, Fcall, ArgList = dsl.symbol_emit(*"FunDef,Fcall,Args".split(","))

# Non terminals for built-in dataStructures
Map, MapElem, MapElems, Collection, CollElems = dsl.symbol_emit(*"Map,MapElem,MapElems,Collection,CollElems".split(","))

# Declaration and Assignation Non Terminal
Assign = dsl.symbol_emit(*"Assign".split(","))

# Return Non Terminal
Ret = dsl.symbol_emit("Ret")

# Production Rules BNF-Like Form

dsl.initial_symbol = CryptoDsl

# Initial Production Augmented Like
CryptoDsl > TopLevelStList

TopLevelStList > TopLevelStList + TopLevelSt \
| TopLevelSt

TopLevelSt > FunDef + lbreak \
| EntDec + lbreak

Entkwgrp > traderkw | coinkw | eventkw

EntDec > Entkwgrp + identifier + ddot + identifier + Opts + o_brace + BehaviorList + c_brace \
/ (ast.AgenDec, (0, 1, 3, 4, 6))

Opts > o_brack + OptsList + c_brack

OptsList > OptsList + comma + Assign \
| Assign \

BehaviorList > BehaviorList + Behavior / (ast.BehaviorList, (0, 1)) \
| Behavior / (ast.BehaviorList, (0,))

Behavior > identifier + o_brace + StatementList + c_brace / (ast.Behavior, (0, 2))

FunDef > identifier + o_par + ArgList + c_par + o_brace + StatementList + c_brace / (ast.FuncDec, ())

StatementList > StatementList + Statement \
| Statement / (ast.StatementList())

Statement > Expr + lbreak / ((0,),) \
| If \
| While \
| Assign + lbreak / ((0,),) \
| Ret + lbreak / ((0,),)

If > ifkw + Expr + o_brace + StatementList + c_brace / (ast.If, (1, 3, 4)) \
| If + Else / (ast.If, (1, 2))

Else > elsekw + o_brace + StatementList + c_brace(ast.Else, (2, 0))

While > whilekw + Expr + o_brace + StatementList + c_brace / (ast.While, (1, 3))

Ret > retkw + Expr / (ast.Ret, (1,)) \
| retkw / (ast.Ret,)

Assign > identifier + assign + Expr / (ast.Assign, (0, 2)) \
| identifier + assign + Map / (ast.Assign, (0, 2)) \
| identifier + assign + Collection / (ast.Assign, (0, 2))

ArgList > ArgList + comma + identifier / (ast.ArgList, (0, 2)) \
| ArgList + comma + Assign / (ast.ArgList, (0, 2)) \
| Assign / (ast.ArgList, (0,)) \
| identifier / (ast.ArgList, (0,))

# Expression Lang, dont have to elevate operands,parser already elevates them
Expr > Expr + or_ + CmpExpr / (ast.And, (0, 2)) \
| Expr + and_ + CmpExpr / (ast.Or, (0, 2)) \
| CmpExpr

CmpExpr > CmpExpr + eq + ArithExpr / (ast.Eq, (0, 2)) \
| CmpExpr + neq + ArithExpr / (ast.Neq, (0, 2)) \
| CmpExpr + gt + ArithExpr / (ast.Gt, (0, 2)) \
| CmpExpr + geq + ArithExpr / (ast.Geq, (0, 2)) \
| CmpExpr + leq + ArithExpr / (ast.Leq, (0, 2)) \
| ArithExpr

ArithExpr > ArithExpr + plus + Term / (ast.Sum, (0, 2)) \
| ArithExpr + minus + Term(ast.Minus, (0, 2)) \
| Term

Term > Term + mul + Factor / (ast.Mul, (0, 2)) \
| Term + div + Factor / (ast.Div, (0, 2)) \
| Term + fdiv + Factor / (ast.Fdiv, (0, 2)) \
| Term + mod + Factor / (ast.Mod, (0, 2)) \
| Factor

Factor > o_par + Expr + c_par / ((1,),) \
| neg + Atom / (ast.Not, (1,)) \
| not_ + Atom / (ast.Not, (1,)) \
| Atom

Atom > identifier / (ast.Identifier, (0,)) \
| string / (ast.String, (0,)) \
| num / (ast.Num, (0,)) \
| Fcall

Fcall > identifier + o_par + ArgList + c_par / (ast.Fcall, (0, 2))

# Lang Data structures
Collection > o_brace + CollElems + c_brace

CollElems > CollElems + comma + Expr(ast.CollElems(0, 2)) \
| Expr \
| eps

Map > o_brack + MapElems + c_brack

MapElems > MapElems + comma + MapElem / (ast.MapElems, (0, 2)) \
| MapElem \
| eps

MapElem > Expr + ddot + Expr / (ast.MapElem, (0, 2))

current_path = os.path.dirname(__file__)
dsl.write_lr1_parser(current_path)  # python 3.9
dsl.write_lexer(current_path)
