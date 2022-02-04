import os.path

import ast_regex as ast
from toolchain.frontend_generator import Grammar

rx = Grammar()
# TODO implement TOKEN ENUMS FOR NAMES
# Terminals
# special symbols
alt, star, plus, minus, ask, acc, esc, dot = \
    rx.symbol_emit(*list(zip(*[iter(r"alt,|,star,*,plus,+,minus,-,ask,?,acc,^,esc,\,dot,.".split(","))] * 2)))

# grouppers
o_par, c_par, o_bra, c_bra, gt, lt, p = \
    rx.symbol_emit(*list(zip(*[iter(r"o_par,(,c_par,),o_bra,[,c_bra,],gt,>,lt,<,p,P".split(","))] * 2)))

# special one that will be recognized in ComplementDummy Matcher
char_ = rx.symbol_emit(("char", "", ""))

# Non Terminals
Regex, ConcatenationRx, ClosureRx, AtomRx, GroupRx, PositiveSetRx, NegativeSetRx \
    , EscapedOrShorthandRx, SetItemsRx, SetItemRx, CharRx, NameRx = \
    rx.symbol_emit(*"Regex,ConcatenationRx,ClosureRx,AtomRx,GroupRx,PositiveSetRx,NegativeSetRx,"
                    "EscapedOrShorthandRx,SetItemsRx,SetItemRx,CharRx,NameRx".split(","))

ReservedSymbol = rx.symbol_emit("ReservedSymbol")

rx.initial_symbol = Regex

ReservedSymbol > alt | star | plus | minus | ask | acc | esc | dot | o_par | c_par | o_bra | c_bra | gt | lt

Regex > Regex + alt + ConcatenationRx / (ast.Alternation, (0, 2)) \
| ConcatenationRx

ConcatenationRx > ConcatenationRx + ClosureRx / (ast.Concatenation, (0, 1)) \
| ClosureRx

ClosureRx > AtomRx + star / (ast.KleeneStar, (0,)) \
| AtomRx + plus / (ast.KleenePlus, (0,)) \
| AtomRx + ask / (ast.Maybe, (0,)) \
| AtomRx

AtomRx > GroupRx \
| PositiveSetRx \
| NegativeSetRx \
| EscapedOrShorthandRx \
| CharRx

GroupRx > o_par + Regex + c_par / (ast.Group, (1,)) \
| o_par + ask + p + lt + NameRx + gt + Regex + c_par / (ast.NamedGroup, (4, 6))

NameRx > char_ + NameRx / (ast.MultiCharName, (0, 1)) \
| char_ / (ast.SingleCharName, (0,))

PositiveSetRx > o_bra + SetItemsRx + c_bra / (ast.PositiveSet, (1,))

NegativeSetRx > o_bra + acc + SetItemsRx + c_bra / (ast.NegativeSet, (2,))

SetItemsRx > SetItemsRx + SetItemRx / (ast.MixedRange, (0, 1)) \
| SetItemRx / (ast.MixedRange, (0, 0))

SetItemRx > char_ + minus + char_ / (ast.Range, (0, 2)) \
| EscapedOrShorthandRx \
| char_

EscapedOrShorthandRx > esc + char_ / (ast.EscapedOrShorthand, (0,1)) \
| esc + ReservedSymbol / (ast.EscapedOrShorthand, (0,1)) \
| dot / (ast.EscapedOrShorthand, (0,0))

CharRx > char_ / (ast.Char, (0,)) \
| p / (ast.Char, (0,))

current_path = os.path.dirname(__file__)

rx.write_lr1_parser(current_path)  # python 3.9
rx.write_lexer(current_path)
