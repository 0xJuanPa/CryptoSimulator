import os.path

from ast_regex import Group, PositiveSet, NegativeSet, Char, Alternation, Concatenation, KleeneStar, KleenePlus, Maybe, \
    MixedRange, Range, EscapedOrShorthand, SingleCharName, MultiCharName, NamedGroup
from toolchain.frontend_generator import Grammar

rx = Grammar()

non_term = "Regex,ConcatenationRx,ClosureRx,AtomRx,GroupRx,PositiveSetRx,NegativeSetRx,EscapedOrShorthandRx,SetItemsRx,SetItemRx,CharRx,NameRx".split(
    ",")
Regex, ConcatenationRx, ClosureRx, AtomRx, GroupRx, PositiveSetRx, NegativeSetRx, EscapedOrShorthandRx, SetItemsRx, SetItemRx, CharRx, NameRx = \
    rx.symbol_emit(*non_term)

term = list(
    zip(*[iter(
        r"alt,|,star,*,plus,+,minus,-,ask,?,acc,^,dot,.,esc,\,o_par,(,c_par,),o_bra,[,c_bra,],gt,>,lt,<,p,P".split(
            ","))] * 2))
alt, star, plus, minus, ask, acc, dot, esc, o_par, c_par, o_bra, c_bra, gt, lt, p = rx.symbol_emit(*term)
char_ = rx.symbol_emit(("char", "", ""))

rx.initial_symbol = Regex

Regex > Regex + alt + ConcatenationRx / (Alternation, (0, 2)) | ConcatenationRx

ConcatenationRx > ConcatenationRx + ClosureRx / (Concatenation, (0, 1)) | ClosureRx

ClosureRx > AtomRx + star / (KleeneStar, (0,)) \
| AtomRx + plus / (KleenePlus, (0,)) \
| AtomRx + ask / (Maybe, (0,)) \
| AtomRx

AtomRx > GroupRx \
| PositiveSetRx \
| NegativeSetRx \
| EscapedOrShorthandRx \
| CharRx

GroupRx > o_par + Regex + c_par / (Group, (1,)) \
| o_par + ask + p + lt + NameRx + gt + Regex + c_par / (NamedGroup,(4,6))

NameRx > char_ + NameRx / (MultiCharName,(0,1))  \
| char_ / (SingleCharName, (0,))

PositiveSetRx > o_bra + SetItemsRx + c_bra / (PositiveSet, (1,))

NegativeSetRx > o_bra + acc + SetItemsRx + c_bra / (NegativeSet, (2,))

SetItemsRx > SetItemsRx + SetItemRx / (MixedRange, (0, 1)) | SetItemRx / (MixedRange, (0, 0))

SetItemRx > char_ + minus + char_ / (Range, (0, 2)) \
| EscapedOrShorthandRx \
| char_

EscapedOrShorthandRx > esc + char_ / (EscapedOrShorthand, (1,)) \
| dot / (EscapedOrShorthand, (0,))

CharRx > char_ / (Char, (0,)) \
| p / (Char, (0,))

current_path = os.path.dirname(__file__)

rx.write_lr1_parser(current_path)  # python 3.9
rx.write_lexer(current_path)
