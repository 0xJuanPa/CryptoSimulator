import os.path

import ast_crypto as ast
from toolchain.frontend_generator import Grammar

dsl = Grammar()

# epsilon terminal
eps = dsl.epsilon

### EXPLANATION
# regex engine very limited with no capture groups and lookaheads so I used priority of definition to avoid complexity
# besides I can "or" all lexeme regexes like "(r)|" and the engine will match greddier I started
# doing it with named groups but I was not satisfied adding match:name just in the content of the state I wanted tags
# of entry of the group and tags for finish so I may have all prefix subgroups.
# I couldnt continue to mantain the old impl had to abort it and switch to other topics


# general pourpouse keyword terminals
ifkw, elsekw, whilekw, retkw, funkw = dsl.symbol_emit((ast.TOKEN_TYPE.IF, r"if "), (ast.TOKEN_TYPE.ELSE, r"else "),
                                                      (ast.TOKEN_TYPE.WHILE, r"while "),
                                                      (ast.TOKEN_TYPE.RET, r"ret "),
                                                      (ast.TOKEN_TYPE.FUNC, r"func "))
# spec keywords terminals
traderkw, coinkw, mykw, marketkw = dsl.symbol_emit((ast.TOKEN_TYPE.TRADER_KW, r"trader "),
                                                   (ast.TOKEN_TYPE.COIN_KW, r"coin "),
                                                   # if I want them as keywords have to match  dot cause no lookaheads
                                                   (ast.TOKEN_TYPE.MY_KW, r"my."),
                                                   (ast.TOKEN_TYPE.MARKET_KW, r"market."))

# ignored terminals
lbreak, tab, sl_comment, space = dsl.symbol_emit((ast.TOKEN_TYPE.LBREAK, "\n|\r\n", True),
                                                 (ast.TOKEN_TYPE.TAB, "\t", True),
                                                 (ast.TOKEN_TYPE.SL_COMMENT, "#[^\n\r]*", True),
                                                 (ast.TOKEN_TYPE.SPACE, " ", True))

# groups terminals
o_par, c_par, o_brack, c_brack, o_brace, c_brace = dsl.symbol_emit((ast.TOKEN_TYPE.O_PAR, r"\("),
                                                                   (ast.TOKEN_TYPE.C_PAR, r"\)"),
                                                                   (ast.TOKEN_TYPE.O_BRACKETS, r"\["),
                                                                   (ast.TOKEN_TYPE.C_BRACKETS, r"\]"),
                                                                   (ast.TOKEN_TYPE.O_BRACES, r"\{"),
                                                                   (ast.TOKEN_TYPE.C_BRACES, r"\}"))

# literals terminals
identifier, string, num = dsl.symbol_emit((ast.TOKEN_TYPE.IDENTIFIER, r"[A-Za-z][\dA-Z_a-z]*"),
                                          (ast.TOKEN_TYPE.STRING, r"'[^']*'"),
                                          (ast.TOKEN_TYPE.NUMBER, r"\d+|\d+[\.]\d+"))

# unary operators terminals
not_ = dsl.symbol_emit((ast.TOKEN_TYPE.NOT, r"!"))

# binary operatos priority 0
exp, mul, mod, fdiv, div, = dsl.symbol_emit((ast.TOKEN_TYPE.EXP, r"\^"), (ast.TOKEN_TYPE.MUL, r"\*"),
                                            (ast.TOKEN_TYPE.MOD, r"%"),
                                            (ast.TOKEN_TYPE.FLOORDIV, r"//"), (ast.TOKEN_TYPE.DIV, r"/"), )

# binary operatos priority 1
plus, minus = dsl.symbol_emit((ast.TOKEN_TYPE.PLUS, r"\+"), (ast.TOKEN_TYPE.MINUS, r"\-"))

# binary operatos priority 2
or_, and_ = dsl.symbol_emit((ast.TOKEN_TYPE.OR, r"\|"), (ast.TOKEN_TYPE.AND, r"&"))

# binary operatos priority 3
eq, neq, gt, geq, lt, leq = dsl.symbol_emit((ast.TOKEN_TYPE.EQ, r"=="), (ast.TOKEN_TYPE.NEQ, r"!="),
                                            (ast.TOKEN_TYPE.GT, r"\>"), (ast.TOKEN_TYPE.GE, r"\>="),
                                            (ast.TOKEN_TYPE.LT, r"\<"), (ast.TOKEN_TYPE.LE, r"\<="))

# special terminals
assign, semicolon = dsl.symbol_emit((ast.TOKEN_TYPE.ASSIGN, r"="), (ast.TOKEN_TYPE.SEMICOLON, r";"))

# splitter terminals
comma, dot, ddot = dsl.symbol_emit((ast.TOKEN_TYPE.COMMA, r"\,"), (ast.TOKEN_TYPE.DOT, r"\."),
                                   (ast.TOKEN_TYPE.DDOT, ":"))

# initial NonTerminal
CryptoDsl = dsl.symbol_emit("CryptoDsl")
dsl.initial_symbol = CryptoDsl

# Nonterminals for language specs
TopLevelSt, TopLevelStList, EntDec, Entkwgrp, KwResolv, Opts, OptsList, Behavior, BehaviorList = dsl.symbol_emit(
    *"TopLevelSt,TopLevelStList,EntDec,Entkwgrp,KwResolv,Opts,OptsList,Behavior,BehaviorList".split(","))

# Non Terminals for Statements and Args
StatementList, Statement, Body = dsl.symbol_emit(*"StatementList,Statement,Body".split(","))

# Non Terminals for Keywords
If, While, Ret = dsl.symbol_emit(*"If,While,Ret".split(","))

# Non Terminals for Expressions
Expr, ExpressionList, CmpExpr, ArithExpr, Term, Factor, Exp, Atom = dsl.symbol_emit(
    *"Expr,ExpressionList,CmpExpr,ArithExpr,Term,Factor,Exp,Atom".split(","))

FunDef, ArgList, FunCall = dsl.symbol_emit(*"FunDef,Args,FunCall".split(","))

# Declaration and Assignation Non Terminal
Assign, AttrResolv = dsl.symbol_emit(*"Assign,AttrResolv".split(","))

Identifier = dsl.symbol_emit(*"Identifier".split(","))

# Shorthands for operators
Op_prec0, Op_prec1, Op_prec2, Op_prec3, Op_prec4, Op_prec5 = dsl.symbol_emit(
    *"Op_prec0,Op_prec1,Op_prec2,Op_prec3,Op_prec4,Op_prec5".split(","))

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

KwResolv > mykw | marketkw

EntDec > Entkwgrp + Identifier + ddot + Identifier + Opts + o_brace + BehaviorList + c_brace \
/ (ast.AgentDec, (0, 1, 3, 4, 6))

Opts > o_brack + OptsList + c_brack / (1,)

Behavior > Identifier + Body / (ast.BehaviorDef, (0, 1))

FunDef > funkw + Identifier + o_par + ArgList + c_par + Body / (ast.FunDef, (1, 5, 3))

OptsList > OptsList + comma + Assign / (ast.OptList, (0, 2)) \
| Assign / (ast.OptList,)

ExpressionList > ExpressionList + comma + Expr / (ast.ExpresionList, (0, 2)) \
| Expr / (ast.ExpresionList,) \
| eps / (ast.ExpresionList,)

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

While > whilekw + Expr + Body / (ast.While, (1, 2))

Ret > retkw + Expr / (ast.Ret, (1,)) \
| retkw / (ast.Ret,)

Assign > Identifier + assign + Expr / (ast.Assign, (0, 2)) \
| AttrResolv + assign + Expr / (ast.Assign, (0, 2))

# Expression Lang, dont have to elevate operands,parser already elevates them
# Shorthands for operator precedence
Op_prec5 > or_ | and_
Op_prec4 > eq | neq | gt | geq | lt | leq
Op_prec3 > plus | minus
Op_prec2 > mul | div | fdiv | mod
Op_prec1 > minus | not_
Op_prec0 > exp

Expr > Expr + Op_prec5 + CmpExpr / (ast.BinaryOp, (0, 2, 1)) \
| CmpExpr  # throw up

CmpExpr > CmpExpr + Op_prec4 + ArithExpr / (ast.BinaryOp, (0, 2, 1)) \
| ArithExpr  # throw up

ArithExpr > ArithExpr + Op_prec3 + Term / (ast.BinaryOp, (0, 2, 1)) \
| Term  # throw up

Term > Term + Op_prec2 + Factor / (ast.BinaryOp, (0, 2, 1)) \
| Factor  # throw up

Factor > Op_prec1 + Exp / (ast.UnaryOp, (1, 0)) \
| Exp  # throw up

Exp > Atom + Op_prec0 + Atom / (ast.BinaryOp, (0, 2, 1)) \
| Atom  # throw up

Atom > Identifier \
| o_par + Expr + c_par / (1,) \
| string / (ast.Literal,) \
| num / (ast.Literal,) \
| FunCall \
| AttrResolv \
| KwResolv + FunCall / (ast.AttrRes, (0, 1))

AttrResolv > KwResolv + Identifier / (ast.AttrRes, (0, 1))

FunCall > Identifier + o_par + ExpressionList + c_par / (ast.FunCall, (0, 2))

Identifier > identifier / (ast.Identifier,)

current_path = os.path.dirname(__file__)  # python 3.9
dsl.write_lr1_parser(current_path)
dsl.write_lexer(current_path)
