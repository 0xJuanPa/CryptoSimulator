import inspect
import os.path
from collections import deque
from itertools import chain
from typing import Union, Dict, Iterable, Callable, Any, List

from toolchain.automaton import Automaton, State
from .scaffold.lexer_scaffold import LexerTable
from .scaffold.parser_scaffold import LRtable, ReduceInfo


class Symbol:
    def __init__(self, name: str):
        self.name: str = name

    def __add__(self, other) -> "SentenceForm":
        if isinstance(other, Symbol):
            res = SentenceForm(self, other)
        elif isinstance(other, AtrributedSentenceContainer):
            res = AtrributedSentenceContainer(SentenceForm(self) + other.sentence, other.attribute)
        else:
            raise TypeError(f"Invalid type: {type(other)}")
        return res

    def __or__(self, other) -> "DisyuntiveForm":
        if isinstance(other, SentenceForm):
            res = DisyuntiveForm([SentenceForm(self), other])
        elif isinstance(other, Symbol):
            res = DisyuntiveForm([SentenceForm(self), SentenceForm(other)])
        else:
            raise TypeError(f"Invalid type: {type(other)}")
        return res

    def __truediv__(self, other):
        if not isinstance(other, Symbol):
            res = AtrributedSentenceContainer(SentenceForm(self), other)
            return res
        else:
            raise TypeError(f"Invalid type: {type(other)}")

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: "Symbol"):
        return hash(self) == hash(other)

    def __repr__(self):
        return f"{self.name}"


class Terminal(Symbol):
    def __init__(self, name: str, match: str, type_=None):
        super().__init__(name)
        self.match = match
        self.type = type_


class Epsilon(Terminal):
    def __init__(self):
        super().__init__("€", "")


class EOF(Terminal):
    def __init__(self):
        super().__init__("$", "")


class NonTerminal(Symbol):
    def __init__(self, name: str, grammar: "Grammar"):
        super().__init__(name)
        self.grammar_ref: Grammar = grammar
        self.associated_productions: List[Production] = list()

    def __gt__(self, other) -> None:
        match other:
            case Symbol():
                prod = Production(self, SentenceForm(other))
            case SentenceForm():
                prod = Production(self, other)
            case DisyuntiveForm():
                for sf in other:
                    self.__gt__(sf)
                return
            case AtrributedSentenceContainer():
                prod = Production(self, other.sentence, other.attribute)
            case _:
                raise TypeError(f"Invalid type: {type(other)}")
        if self.grammar_ref.initial_symbol is None:
            self.grammar_ref.initial_symbol = self
        if prod.attribute and prod in self.grammar_ref.productions:
            raise ValueError(f"Production {prod} already in grammar")
        self.associated_productions.append(prod)
        self.grammar_ref.productions.append(prod)


class SentenceForm(tuple):
    def __new__(cls, *symbols: Symbol):
        # filter all epsilons cause x+eps=x except if is only epsilon
        arg = symbols if len(symbols) == 1 else list(filter(lambda s: not isinstance(s, Epsilon), symbols))
        t = tuple.__new__(cls, arg)
        return t

    def __repr__(self):
        res = " ".join(map(repr, self))
        return res

    def __add__(self, other: Union[Symbol, "SentenceForm"]):
        if isinstance(other, Symbol):
            res = SentenceForm(*(list(self) + [other]))
        elif isinstance(other, SentenceForm):
            res = SentenceForm(*(list(self) + list(other)))
        elif isinstance(other, AtrributedSentenceContainer):
            res = AtrributedSentenceContainer(self + other.sentence, other.attribute)
        else:
            raise TypeError(f"Invalid type: {type(other)}")
        return res

    def __or__(self, other: Union[Symbol, "SentenceForm"]):
        if isinstance(other, Symbol):
            res = DisyuntiveForm([self, SentenceForm(other)])
        elif isinstance(other, SentenceForm) or isinstance(other, AtrributedSentenceContainer):
            res = DisyuntiveForm([self, other])
        else:
            raise TypeError(f"Invalid type: {type(other)}")
        return res


class AtrributedSentenceContainer:
    def __init__(self, sentence, attribute):
        self.sentence: SentenceForm = sentence
        self.attribute = attribute

    def __or__(self, other: Union[Symbol, "SentenceForm"]):
        if isinstance(other, Symbol):
            res = DisyuntiveForm([self, SentenceForm(other)])
        elif isinstance(other, SentenceForm) or isinstance(other, AtrributedSentenceContainer):
            res = DisyuntiveForm([self, other])
        else:
            raise TypeError(f"Invalid type: {type(other)}")
        return res

    def __repr__(self):
        res = f"{self.sentence} {{{self.attribute}}}"
        return res


class DisyuntiveForm(list):
    def __or__(self, other):
        if isinstance(other, SentenceForm) or isinstance(other, AtrributedSentenceContainer):
            self.append(other)
        elif isinstance(other, Symbol):
            self.append(SentenceForm(other))
        else:
            raise TypeError(other)
        return self

    def __repr__(self):
        res = " | ".join(map(repr, self))
        return res


class Production:
    def __init__(self, non_terminal: NonTerminal, sentence: SentenceForm, attribute=None):
        self.left_part: NonTerminal = non_terminal
        self.right_part: SentenceForm = sentence
        self.attribute = attribute

    def __repr__(self):
        res = f"{self.left_part} -> {self.right_part} {{{self.attribute}}}"
        return res

    def __hash__(self):
        return hash((self.left_part, self.right_part))

    def __eq__(self, other):
        return hash(self) == hash(other)


class LRitem:

    def __init__(self, production: Production, dot_pos: int = 0, lookaheads: Iterable[Symbol] = None):
        self.production = production
        self.dot_pos = dot_pos
        self.lookaheads = frozenset(list(lookaheads) if lookaheads is not None else list())

    @property
    def is_reduce(self):
        return self.dot_pos == len(self.production.right_part)

    def peek_nxt_symbol(self) -> Symbol | None:
        if not self.is_reduce:
            return self.production.right_part[self.dot_pos]

    def advance_dot(self):
        if not self.is_reduce:
            return LRitem(self.production, self.dot_pos + 1, self.lookaheads)

    def get_as_item_lr0(self):
        res = LRitem(self.production, self.dot_pos)
        return res

    def remain_with_each_lkahead(self):
        remaining = self.production.right_part[self.dot_pos + 1:]
        remaining_sentences = [SentenceForm(*(remaining + (lh,))) for lh in self.lookaheads]
        return remaining_sentences

    def __hash__(self):
        return hash((self.production, self.dot_pos, self.lookaheads))

    def __eq__(self, other: "LRitem"):
        return hash(self) == hash(other)

    def __repr__(self):
        item_right = " ".join(map(repr, self.production.right_part[:self.dot_pos])) + "."
        item_right += " ".join(map(repr, self.production.right_part[self.dot_pos:])) + ", "
        item_right += "/".join(map(repr, self.lookaheads))
        res = f'{self.production.left_part} -> {item_right}'
        return res


class Grammar:
    def __init__(self):
        self.eof: EOF = EOF()
        self.epsilon: Epsilon = Epsilon()
        self.terminals: List[Terminal | EOF] = [self.eof]
        self.non_terminals: List[NonTerminal] = []
        self.productions: List[Production] = list()
        self.initial_symbol: NonTerminal | None = None
        self._cached_firsts: Dict[SentenceForm, set[Terminal]] | None = None

    def symbol_emit(self, *sym: Iterable[tuple | str]) -> Symbol | Iterable[Symbol]:
        res = []
        for s in sym:
            match s:
                case str(s):
                    sym = NonTerminal(s, self)
                    res.append(sym)
                    self.non_terminals.append(sym)
                case tuple(s):
                    typ = s[2] if len(s) > 2 else None
                    sym = Terminal(s[0], s[1], type_=typ)
                    res.append(sym)
                    self.terminals.append(sym)
                case _:
                    raise TypeError("Invalid type")
        return res if len(res) > 1 else res[0]

    def _get_first(self, item: [SentenceForm] = None, allow_eps=True) -> set[Terminal]:

        def calc_firsts_of_sentence(sentence_form):
            calc = set()
            for fsymbol in sentence_form:
                sub_sentence = SentenceForm(fsymbol)
                first_r = self._cached_firsts[sub_sentence]
                calc.update(first_r)
                if self.epsilon not in first_r:
                    break
            return calc

        if self._cached_firsts is None:
            self._cached_firsts = {SentenceForm(s): ({s} if isinstance(s, Terminal) else set()) for s in
                                   chain(self.terminals, self.non_terminals)}
            change_happened = True
            while change_happened:
                change_happened = False
                for production in self.productions:
                    left_part, right_part = SentenceForm(production.left_part), production.right_part
                    calculated = calc_firsts_of_sentence(right_part)
                    change_happened |= right_part not in self._cached_firsts or len(
                        calculated - self._cached_firsts[left_part]) != 0 \
                                       or len(calculated - self._cached_firsts[right_part]) != 0
                    self._cached_firsts[left_part].update(calculated)
                    self._cached_firsts[right_part] = self._cached_firsts.get(right_part, calculated) | calculated

        res = calc_firsts_of_sentence(item)
        res2 = res if allow_eps else res - {self.epsilon}
        return res2

    def _get_lr1_goto(self, items: Iterable[LRitem], symbol: Symbol) -> frozenset[LRitem]:
        goto = frozenset(item.advance_dot() for item in items if symbol == item.peek_nxt_symbol())
        return goto

    def _get_lr1_closure(self, items: Iterable[LRitem]) -> frozenset[LRitem]:
        # lr1 closure is get all .Nonterminal items with theri lookaheads
        closure = deque(items)
        new_items: Dict[LRitem, LRitem] = {i.get_as_item_lr0(): i for i in items}
        while closure:
            item = closure.popleft()
            next_symbol = item.peek_nxt_symbol()
            if isinstance(next_symbol, NonTerminal):
                lookaheads = set()
                for sf_plh in item.remain_with_each_lkahead():
                    local_first = self._get_first(sf_plh, allow_eps=False)  # as follow cant contain eps
                    lookaheads.update(local_first)
                for prod in next_symbol.associated_productions:
                    lr0_itm = LRitem(prod)
                    if (itm := new_items.get(lr0_itm, None)) is None:
                        itm = LRitem(prod, 0, lookaheads)
                        new_items[lr0_itm] = itm
                        closure.append(itm)
                    else:
                        itm.lookaheads = frozenset(chain(itm.lookaheads, lookaheads))
        res = frozenset(new_items.values())
        return res

    def write_lexer(self, path) -> None:
        table = LexerTable(eof="$", linebreaker="\n", spacer=" ")
        for t in self.terminals:
            table.append((t.name, t.match, t.type))
        serial_str = table.get_serial_str()
        lexer_file = inspect.getfile(LexerTable)
        parser_content = open(lexer_file).read().replace("REPLACE-ME-LEXER", serial_str)
        out_path = os.path.join(path, "lexer.py")
        newp = open(out_path, "w")
        newp.write(parser_content)
        newp.close()

    def write_lr1_parser(self, path: str) -> None:
        transition_sym_mapper: Callable[[LRitem], Any] = lambda it: [] if (ns := it.peek_nxt_symbol()) is None else [ns]
        state_maker: Callable[[Any], int | Any] = lambda subset: State(None, final=True, content=subset)
        goto_func = self._get_lr1_goto
        closure_func = self._get_lr1_closure
        table = LRtable()
        table.initial_symbol = self.initial_symbol.name
        self.augment()
        initial_value = [LRitem(next(iter(self.initial_symbol.associated_productions)), lookaheads=[self.eof])]
        dfa = Automaton.powerset_construct(initial_value, goto_func, closure_func, state_maker, transition_sym_mapper)
        table.initial_state = dfa.initial_state.id
        for state in dfa.states:
            items: Iterable[LRitem] = state.content
            for item in items:
                if item.is_reduce:
                    prod = item.production
                    if prod.left_part == self.initial_symbol:
                        table.action((state.id, self.eof), (LRtable.Action.ACCEPT, 0))
                    else:
                        for symbol in item.lookaheads:
                            symbol: Symbol
                            if prod.attribute:
                                cls_name = prod.attribute[0] if isinstance(prod.attribute[0], str) or bool(
                                    prod.attribute[0]) is False else prod.attribute[0].__name__
                                cls_args = prod.attribute[1]
                            else:
                                cls_name = None
                                cls_args = None
                            right_part = list(map(repr, prod.right_part))
                            reduce_info = ReduceInfo(str(prod.left_part), right_part, cls_name, cls_args)
                            table.action((state.id, symbol.name), (LRtable.Action.REDUCE, reduce_info))
                else:
                    symbol = item.peek_nxt_symbol()
                    if isinstance(symbol, Terminal):
                        table.action((state.id, symbol.name), (LRtable.Action.SHIFT, state[symbol.name].id))
                    else:
                        table.goto((state.id, symbol.name), state[symbol.name].id)

        serial_str = table.get_serial_str()
        parser_file = inspect.getfile(ReduceInfo)
        parser_content = open(parser_file).read().replace("REPLACE-ME-PARSER", serial_str)
        out_path = os.path.join(path, "parser.py")
        newp = open(out_path, "w")
        newp.write(parser_content)
        newp.close()

    @property
    def is_augmented(self):
        return len(self.initial_symbol.associated_productions) == 1

    def augment(self):
        if self.is_augmented:
            return
        S0 = self.symbol_emit(f"{self.initial_symbol}'")
        S0 > self.initial_symbol
        self.initial_symbol = S0