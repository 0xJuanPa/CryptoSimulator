import os.path

import ast_crypto as ast
from toolchain.frontend_generator import Grammar

dsl = Grammar()

# epsilon terminal
eps = dsl.epsilon

# ignored terminals
lbreak, tab, sl_comment, space = dsl.symbol_emit(("lbreak", "\n|\r\n", True), ("tab", "\t", True),
                                                 ("sl_comment", "#[^\n\r]*", True), ("space", " ", True))

# groups terminals
o_par, c_par, o_brack, c_brack, o_brace, c_brace = dsl.symbol_emit(("o_par", r"\("), ("c_par", r"\)"),
                                                                   ("o_brack", r"\["),
                                                                   ("c_brack", r"\]"), ("o_brace", r"\{"),
                                                                   ("c_brace", r"\}"))

# general pourpouse keyword terminals
ifkw, elsekw, whilekw, funkw, retkw = dsl.symbol_emit(("if", r"if "), ("else", r"else "), ("while", r"while "),
                                                      ("func", r"func "), ("ret", r"ret "))
# spec keywords terminals
traderkw, coinkw = dsl.symbol_emit(("trader", r"trader "), ("coin", r"coin "))

# literals terminals
identifier, string, num = dsl.symbol_emit(("identifier", r"[A-Za-z][\dA-Z_a-z]*"), ("string", r"'[^']*'"),
                                          ("num", r"\d+|\d+[\.]\d+"))

# special terminals
assign, semicolon = dsl.symbol_emit(("assign", r"="), ("semicolon", r";"))

# unary operators terminals
not_ = dsl.symbol_emit(("not", r"!"))

# binary operatos priority 0
mul, fdiv, div, mod = dsl.symbol_emit(("mul", r"\*"), ("fdiv", r"//"), ("div", r"/"), ("mod", r"%"))

# binary operatos priority 1
plus, minus = dsl.symbol_emit((ast.TOKEN_TYPE.PLUS, r"\+"), ("minus", r"\-"))

# binary operatos priority 2
or_, and_ = dsl.symbol_emit(("or", r"\|"), ("and", r"&"))

# binary operatos priority 3
eq, neq, gt, geq, lt, leq = dsl.symbol_emit(("eq", r"=="), ("neq", r"!="), ("gt", r"\>"), ("geq", r"\>="),
                                            ("lt", r"\<"),
                                            ("leq", r"\<="))

# splitter terminals
comma, dot, ddot = dsl.symbol_emit(("comma", r"\,"), ("dot", r"\."), ("ddot", ":"))

# initial NonTerminal
CryptoDsl = dsl.symbol_emit("CryptoDsl")
dsl.initial_symbol = CryptoDsl

# Nonterminals for language specs
TopLevelSt, TopLevelStList, EntDec, Entkwgrp, Opts, OptsList, Behavior, BehaviorList = dsl.symbol_emit(
    *"TopLevelSt,TopLevelStList,EntDec,Entkwgrp,Opts,OptsList,Behavior,BehaviorList".split(","))

# Non Terminals for Statements and Args
StatementList, Statement, Body = dsl.symbol_emit(*"StatementList,Statement,Body".split(","))

# Non Terminals for Keywords
If, While, Ret = dsl.symbol_emit(*"If,While,Ret".split(","))

# Non Terminals for Expressions
Expr, ExpressionList, CmpExpr, ArithExpr, Term, Factor, Atom = dsl.symbol_emit(
    *"Expr,ExpressionList,CmpExpr,ArithExpr,Term,Factor,Atom".split(","))

FunDef, ArgList, FunCall = dsl.symbol_emit(*"FunDef,Args,FunCall".split(","))

# Declaration and Assignation Non Terminal
Assign, AttrResolv = dsl.symbol_emit(*"Assign,AttrResolv".split(","))

Identifier = dsl.symbol_emit(*"Identifier".split(","))

# Shorthands for operators
Op_prec0, Op_prec1, Op_prec2, Op_prec3, Op_prec4 = dsl.symbol_emit(
    *"Op_prec0,Op_prec1,Op_prec2,Op_prec3,Op_prec4".split(","))

# Production Rules BNF-Like Form

dsl.initial_symbol = CryptoDsl

# Initial Production Augmented Like
# Tried to follow python philosophy of no epsilon productions but give up

CryptoDsl > TopLevelStList / (ast.Simulation,)

TopLevelStList > TopLevelStList + TopLevelSt / (ast.PList, (0, 1)) \
| TopLevelSt / (ast.PList,)

TopLevelSt > FunDef \
| EntDec

# spec keywords shorthand
Entkwgrp > traderkw | coinkw

EntDec > Entkwgrp + Identifier + ddot + Identifier + Opts + o_brace + BehaviorList + c_brace \
/ (ast.AgentDec, (0, 1, 3, 4, 6))

Opts > o_brack + OptsList + c_brack / (1,)

Behavior > Identifier + Body / (ast.FunDef, (0, 1))

FunDef > funkw + Identifier + o_par + ArgList + c_par + Body / (ast.FunDef, (1, 5, 3))

OptsList > OptsList + comma + Assign / (ast.OptList, (0, 2)) \
| Assign / (ast.OptList,)

ExpressionList > ExpressionList + comma + Expr / (ast.ExpresionList, (0, 2)) \
| Expr / (ast.ExpresionList,) \
| eps

BehaviorList > BehaviorList + Behavior / (ast.PList, (0, 1)) \
| Behavior / (ast.PList,)

ArgList > ArgList + comma + Identifier / (ast.ArgList, (0, 2)) \
| Identifier / (ast.ArgList,) \
| eps / (ast.ArgList,)

StatementList > StatementList + Statement / (ast.StatementList, (0, 1)) \
| Statement / (ast.StatementList,)

Statement > Expr + semicolon \
| If \
| While \
| Assign + semicolon \
| Ret + semicolon

Body > o_brace + StatementList + c_brace / (1,)  # project first

If > ifkw + Expr + Body / (ast.If, (1, 2)) \
| ifkw + Expr + Body + elsekw + Body / (ast.If, (1, 2, 4))

While > whilekw + Expr + Body / (ast.While, (1, 3))

Ret > retkw + Expr / (ast.Ret, (1,)) \
| retkw / (ast.Ret,)

Assign > Identifier + assign + Expr / (ast.Assign, (0, 2)) \
| AttrResolv + assign + Expr / (ast.Assign, (0, 2))

# Expression Lang, dont have to elevate operands,parser already elevates them
# Shorthands for operator precedence
Op_prec4 > or_ | and_
Op_prec3 > eq | neq | gt | geq | lt | leq
Op_prec2 > plus | minus
Op_prec1 > mul | div | fdiv | mod
Op_prec0 > minus | not_

Expr > Expr + Op_prec4 + CmpExpr / (ast.BinaryOp, (0, 2, 1)) \
| CmpExpr  # throw up

CmpExpr > CmpExpr + Op_prec3 + ArithExpr / (ast.BinaryOp, (0, 2, 1)) \
| ArithExpr  # throw up

ArithExpr > ArithExpr + Op_prec2 + Term / (ast.BinaryOp, (0, 2, 1)) \
| Term  # throw up

Term > Term + Op_prec1 + Factor / (ast.BinaryOp, (0, 2, 1)) \
| Factor  # throw up

Factor > o_par + Expr + c_par / (1,) \
| Op_prec0 + Atom / (ast.UnaryOp, (1, 0)) \
| Atom  # throw up

Atom > Identifier \
| string / (ast.String,) \
| num / (ast.Number,) \
| FunCall \
| AttrResolv \
| Identifier + dot + FunCall / (ast.AttrRes, (0, 2))

AttrResolv > Identifier + dot + Identifier / (ast.AttrRes, (0, 2))

FunCall > Identifier + o_par + ExpressionList + c_par / (ast.FunCall, (0, 2))

Identifier > identifier / (ast.Identifier,)

current_path = os.path.dirname(__file__)  # python 3.9
dsl.write_lr1_parser(current_path)
dsl.write_lexer(current_path)
