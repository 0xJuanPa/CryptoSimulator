import os.path
from enum import Enum, auto

import ast_crypto as ast
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
space, lbreak, tab, sl_comment = dsl.symbol_emit(("space", " ", True), ("lbreak", "\n|\r\n", True), ("tab", "\t", True),
                                                 ("sl_comment", "#.*(\n|\r\n)", True))

# groups terminals
o_par, c_par, o_brack, c_brack, o_brace, c_brace = dsl.symbol_emit(("o_par", r"\("), ("c_par", r"\)"),
                                                                   ("o_brack", r"\["),
                                                                   ("c_brack", r"\]"), ("o_brace", r"\{"),
                                                                   ("c_brace", r"\}"))

# general pourpouse keyword terminals
ifkw, elsekw, whilekw, funkw, retkw = dsl.symbol_emit(("if", r"if"), ("else", r"else"), ("while", r"while"),
                                                      ("func", r"func"), ("ret", r"ret"))
# spec keywords terminals
traderkw, coinkw, eventkw = dsl.symbol_emit(("trader", r"trader"),
                                            ("coin", r"coin"), ("event", r"event"))

# literals terminals
identifier, string, num = dsl.symbol_emit(("identifier", r"[A-Za-z][\dA-Z_a-z]*"), ("string", r"'[^']*'"),
                                          ("num", r"\d+|\d+[,\.]\d+"))

# special terminals
assign, semicolon = dsl.symbol_emit(("assign", r"="), ("semicolon", r";"))

# unary operators terminals
not_ = dsl.symbol_emit(("not", r"!"))

# binary operatos priority 0
mul, div, fdiv, mod = dsl.symbol_emit(("mul", r"\*"), ("div", r"/"), ("fdiv", r"//"), ("mod", r"%"))

# binary operatos priority 1
plus, minus = dsl.symbol_emit(("plus", r"\+"), ("minus", r"\-"))

# binary operatos priority 2
or_, and_ = dsl.symbol_emit(("or", r"\|"), ("and", r"&"))

# binary operatos priority 3
eq, neq, gt, geq, lt, leq = dsl.symbol_emit(("eq", r"=="), ("neq", r"!="), ("gt", r"\>"), ("geq", r"\>="),
                                            ("lt", r"\<"),
                                            ("leq", r"\<="))

# splitter terminals
comma, dot, ddot = dsl.symbol_emit(("comma", ","), ("dot", r"\."), ("ddot", ":"))

# initial NonTerminal
CryptoDsl = dsl.symbol_emit("CryptoDsl")
dsl.initial_symbol = CryptoDsl

# Nonterminals for language specs
TopLevelStList, TopLevelSt, EntDec, Entkwgrp, Opts, OptsList, Behavior, BehaviorList = dsl.symbol_emit(
    *"TopLevelStList,TopLevelSt,EntDec,Entkwgrp,Opts,OptsList,Behavior,BehaviorList".split(","))

# Non Terminals for Statements and Args
StatementList, Statement, Body = dsl.symbol_emit(*"StatementList,Statement,Body".split(","))

# Non Terminals for Keywords
If, While = dsl.symbol_emit(*"If,While".split(","))

# Non Terminals for Expressions
Expr, CmpExpr, ArithExpr, Term, Factor, Atom = dsl.symbol_emit(*"Expr,CmpExpr,ArithExpr,Term,Factor,Atom".split(","))

FunDef, Fcall, ArgList = dsl.symbol_emit(*"FunDef,Fcall,Args".split(","))

# Non terminals for built-in dataStructures
Map, MapElem, MapElems, Collection, CollElems = dsl.symbol_emit(*"Map,MapElem,MapElems,Collection,CollElems".split(","))

# Declaration and Assignation Non Terminal
Assign = dsl.symbol_emit(*"Assign".split(","))

#
Identifier = dsl.symbol_emit(*"Identifier".split(","))

# Return Non Terminal
Ret = dsl.symbol_emit("Ret")

# Production Rules BNF-Like Form

dsl.initial_symbol = CryptoDsl

# Initial Production Augmented Like
CryptoDsl > TopLevelStList / (ast.Program,)

TopLevelStList > TopLevelStList + TopLevelSt \
| TopLevelSt

TopLevelSt > FunDef + semicolon \
| EntDec + semicolon

Entkwgrp > traderkw | coinkw | eventkw  # spec keywords shorthand

EntDec > Entkwgrp + Identifier + ddot + Identifier + Opts + o_brace + BehaviorList + c_brace \
/ (ast.AgentDec, (0, 1, 3, 4, 6))

Opts > o_brack + OptsList + c_brack / (1,)

Behavior > Identifier + Body / (ast.Behavior, (0, 2))

FunDef > Identifier + o_par + ArgList + c_par + Body / (ast.FunDef, (0, 2, 5))

OptsList > OptsList + comma + Assign / (ast.OptList, (0, 2)) \
| Assign / (ast.OptList,)

BehaviorList > BehaviorList + Behavior / (ast.BehaviorList, (0, 1)) \
| Behavior / (ast.BehaviorList,)

ArgList > ArgList + comma + identifier / (ast.ArgList, (0, 2)) \
| identifier / (ast.ArgList,)

StatementList > StatementList + Statement / (ast.StatementList, (0, 1)) \
| Statement / (ast.StatementList,)

Statement > Expr + semicolon \
| If \
| While \
| Assign + semicolon \
| Ret + semicolon

If > ifkw + Expr + Body / (ast.If, (1, 2)) \
| ifkw + Expr + Body + elsekw + Body / (ast.If, (1, 2, 4))

While > whilekw + Expr + Body / (ast.While, (1, 3))

Ret > retkw + Expr / (ast.Ret, (1,)) \
| retkw / (ast.Ret,)

Assign > identifier + assign + Expr / (ast.Assign, (0, 2))
# | identifier + assign + Map / (ast.Assign, (0, 2)) \
# | identifier + assign + Collection / (ast.Assign, (0, 2))

# Expression Lang, dont have to elevate operands,parser already elevates them
Expr > Expr + or_ + CmpExpr / (ast.And, (0, 2)) \
| Expr + and_ + CmpExpr / (ast.Or, (0, 2)) \
| CmpExpr  # throw up

CmpExpr > CmpExpr + eq + ArithExpr / (ast.Eq, (0, 2)) \
| CmpExpr + neq + ArithExpr / (ast.Neq, (0, 2)) \
| CmpExpr + gt + ArithExpr / (ast.Gt, (0, 2)) \
| CmpExpr + geq + ArithExpr / (ast.Geq, (0, 2)) \
| CmpExpr + leq + ArithExpr / (ast.Leq, (0, 2)) \
| ArithExpr  # throw up

ArithExpr > ArithExpr + plus + Term / (ast.Sum, (0, 2)) \
| ArithExpr + minus + Term / (ast.Sub, (0, 2)) \
| Term  # throw up

Term > Term + mul + Factor / (ast.Mul, (0, 2)) \
| Term + div + Factor / (ast.Div, (0, 2)) \
| Term + fdiv + Factor / (ast.Fdiv, (0, 2)) \
| Term + mod + Factor / (ast.Mod, (0, 2)) \
| Factor  # throw up

Factor > o_par + Expr + c_par / (1,) \
| minus + Atom / (ast.Neq, (1,)) \
| not_ + Atom / (ast.Not, (1,)) \
| Atom  # throw up

Atom > Identifier \
| string / (ast.String, (0,)) \
| num / (ast.Number, (0,)) \
| Fcall  # throw up

Fcall > identifier + o_par + ArgList + c_par / (ast.Fcall, (0, 2))

Identifier > identifier / (ast.Identifier, (0,))

Body > o_brace + StatementList + c_brace / (1,)  # project first

# # Lang Data structures
# Collection > o_brace + CollElems + c_brace / (1,)
#
# CollElems > CollElems + comma + Expr(ast.CollElems(0, 2)) \
# | Expr \
# | eps
#
# Map > o_brack + MapElems + c_brack / (1,)
#
# MapElems > MapElems + comma + MapElem / (ast.MapElems, (0, 2)) \
# | MapElem \
# | eps
#
# MapElem > Expr + ddot + Expr / (ast.MapElem, (0, 2))

current_path = os.path.dirname(__file__)
dsl.write_lr1_parser(current_path)  # python 3.9
dsl.write_lexer(current_path)
