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
        if isinstance(other, SentenceForm) or isinstance(other, AtrributedSentenceContainer):
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
        # https://stackoverflow.com/questions/27522626/hash-function-in-python-3-3-returns-different-results-between-sessions
        return hash(self.name)

    def __eq__(self, other: "Symbol"):
        return hash(self) == hash(other)

    def __repr__(self):
        return f"{self.name}"


class Terminal(Symbol):
    def __init__(self, name: str, match: str, extra=None):
        super().__init__(name)
        self.match = match
        self.extra = extra


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
        # the case eps + eps + eps will not be managed oistrich technique
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
        res = f"{self.left_part} -> {self.right_part}" + (f" {{{self.attribute}}}" if self.attribute else "")
        return res

    def __hash__(self):
        return hash((self.left_part, self.right_part))

    def __eq__(self, other):
        return hash(self) == hash(other)


class LRitem:

    def __init__(self, production: Production, dot_pos: int = 0, lookaheads: Iterable[Symbol] = None):
        self.production = production
        self.dot_pos = dot_pos
        if isinstance(self.production.right_part[0], Epsilon):  # trick to make epsilon items as reduce items
            self.dot_pos += 1
        self.lookaheads = tuple(sorted(set(lookaheads if lookaheads is not None else list()), key=hash))

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
        """get copy of item whithout lookahead  (lr0 or center)"""
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
    def __init__(self, attribute_encode=None, attribute_apply=None):
        if not isinstance(attribute_encode, Callable):
            self.attribute_encode = Grammar._attribute_encode
        if not isinstance(attribute_apply, Callable):
            self.attribute_apply = self._attribute_apply
        self.eof: EOF = EOF()
        self.epsilon: Epsilon = Epsilon()
        self.terminals: List[Terminal | EOF] = [self.eof, self.epsilon]
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
                    extra = s[2] if len(s) > 2 else None
                    sym = Terminal(s[0], s[1], extra=extra)
                    res.append(sym)
                    self.terminals.append(sym)
                case _:
                    raise TypeError("Invalid type")
        return res if len(res) > 1 else res[0]

    def _get_first(self, item: [SentenceForm] = None, allow_eps=True) -> set[Terminal]:

        def calc_firsts_of_sentence(sentence_form):
            calc = set()
            for i, yi in enumerate(sentence_form):
                sub_sentence = SentenceForm(yi)
                first_yi = self._cached_firsts[sub_sentence]
                calc.update(first_yi)
                if self.epsilon not in first_yi:  # advance while epsilon in firsts
                    break
                if i != len(sentence_form) - 1:
                    calc.remove(self.epsilon)  # will get epsilon from the last or not get it
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

    def _get_lr1_goto(self, items: Iterable[LRitem], symbol: Symbol) -> tuple[LRitem]:
        goto = tuple(sorted(set(item.advance_dot() for item in items if
                                item.peek_nxt_symbol() is not None and symbol == item.peek_nxt_symbol()), key=hash))
        return goto

    def _get_lr1_closure(self, items: Iterable[LRitem]) -> tuple[LRitem]:
        # lr1 closure is get all .Nonterminal items with theri lookaheads
        closure = deque(items)
        canonical: Dict[LRitem, LRitem] = {i.get_as_item_lr0(): i for i in items}
        while closure:
            item = closure.popleft()
            next_symbol = item.peek_nxt_symbol()
            if isinstance(next_symbol, NonTerminal):
                calc_lookaheads = set()
                for sf_plh in item.remain_with_each_lkahead():
                    local_first = self._get_first(sf_plh, allow_eps=False)  # as follow cant contain eps
                    calc_lookaheads.update(local_first)
                for prod in next_symbol.associated_productions:
                    lr0_itm = LRitem(prod)
                    if (itm := canonical.get(lr0_itm, None)) is None:
                        itm = LRitem(prod, 0, calc_lookaheads)
                        canonical[lr0_itm] = itm
                        closure.append(itm)
                    else:
                        itm.lookaheads = tuple(sorted(set(chain(itm.lookaheads, calc_lookaheads)), key=hash))
        res = tuple(canonical.values())
        return res

    def write_lexer(self, path) -> None:
        table = LexerTable(eof="$", linebreaker="\n", spacer=" ")
        for t in filter(lambda s: not (isinstance(s, Epsilon) or isinstance(s, EOF)), self.terminals):
            table.append((t.name, t.match, t.extra))
        serial_str = table.get_serial_str()
        lexer_file = inspect.getfile(LexerTable)
        parser_content = open(lexer_file).read().replace("REPLACE-ME-LEXER", serial_str)
        out_path = os.path.join(path, "lexer.py")
        newp = open(out_path, "w")
        newp.write(parser_content)
        newp.close()

    @staticmethod
    def _attribute_encode(attr):
        if attr:
            if len(attr) == 2:
                cls_name = attr[0].__name__
                cls_args = attr[1]
                return cls_name, cls_args
            if isinstance(attr[0], int):
                return (attr[0],)
            elif isinstance(attr[0], type):
                return (attr[0].__name__,)
            else:
                raise Exception("Attribute Not Supported")
        return None

    # do not decorate with static method this is just a scaffold
    def _attribute_apply(attribute, popped_syms, info):
        ast_types = info
        if attribute:
            if len(attribute) == 1:
                if isinstance(attribute[0], int):
                    project_index = attribute[0]
                    instance = popped_syms[project_index].content  # project up
                elif isinstance(attribute[0], str):
                    prod_class = attribute[0]
                    arg = popped_syms[0].content if len(popped_syms) else None
                    instance = getattr(ast_types, prod_class)(arg)
                else:
                    raise Exception("Attribute Not Supported")
            elif len(attribute) == 2:
                prod_class, args_map = attribute
                args = list(map(lambda i: popped_syms[i].content, args_map))
                instance = getattr(ast_types, prod_class)(*args)
            else:
                raise Exception("Attribute Not Supported")
        else:
            instance = popped_syms[0].content if len(popped_syms) else None  # project up
        return instance

    def write_lr1_parser(self, path: [str | None] = None) -> None:
        """
        Generates an LR1 Shif-Reduce Parser for the Gramamr using attribute coder and attribute applier supplied or def
        If no arg is provided visualizes the dfa
        """
        table = LRtable()
        table.initial_symbol = self.initial_symbol.name

        # Augment Grammar Always
        S0 = self.symbol_emit(f"{self.initial_symbol}'")
        S0 > self.initial_symbol
        self.initial_symbol = S0

        transition_symbol_resolver: Callable[[LRitem], Any] = \
            lambda subset: sorted(set(ns for x in subset if (ns := x.peek_nxt_symbol()) is not None), key=hash)

        state_maker: Callable[[Any], int | Any] = lambda subset: State(None, final=True, content=subset)
        goto_func = self._get_lr1_goto
        closure_func = self._get_lr1_closure
        initial_value = [LRitem(next(iter(self.initial_symbol.associated_productions)), lookaheads=[self.eof])]
        dfa = Automaton.powerset_construct(initial_value, goto_func, closure_func, state_maker,
                                           transition_symbol_resolver)

        if path is None:
            dfa.view()
            return

        table.initial_state = dfa.initial_state.name
        for state in dfa.states:
            state_content: Iterable[LRitem] = state.content
            for item in state_content:
                if item.is_reduce:
                    prod = item.production
                    if prod.left_part == self.initial_symbol:
                        table.action((state.name, self.eof.name), (LRtable.Action.ACCEPT, 0))
                    else:
                        for symbol in item.lookaheads:
                            symbol: Symbol
                            attribute = self.attribute_encode(prod.attribute)
                            right_part_dbg = [s.name for s in prod.right_part if s != self.epsilon]
                            reduce_info = ReduceInfo(prod.left_part.name, right_part_dbg, attribute)
                            table.action((state.name, symbol.name), (LRtable.Action.REDUCE, reduce_info))
                else:
                    symbol = item.peek_nxt_symbol()
                    if isinstance(symbol, Terminal):
                        table.action((state.name, symbol.name), (LRtable.Action.SHIFT, state[symbol.name].name))
                    else:
                        table.goto((state.name, symbol.name), state[symbol.name].name)

        print(f"Automaton States Count:{len(dfa.states)}")
        print(f"Actions:{len(table._action)} Gotos:{len(table._goto)}")

        serial_str = table.get_serial_str()
        parser_file = inspect.getfile(ReduceInfo)
        scaffold_cnt = open(parser_file).read()
        attrib_src = inspect.getsource(self.attribute_apply)
        unindented = inspect.cleandoc(attrib_src).replace("\n", "\n" + " " * 4)
        code = scaffold_cnt.replace("def _attribute_apply(attribute, popped_syms, info): pass", unindented)
        code = code.replace("_attribute_apply", self.attribute_apply.__name__)
        parser_content = code.replace("REPLACE-ME-PARSER", serial_str)
        out_path = os.path.join(path, "parser.py")
        newp = open(out_path, "w")
        newp.write(parser_content)
        newp.close()
