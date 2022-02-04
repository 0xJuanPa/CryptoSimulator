import string
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import chain

from toolchain.automaton import Automaton, State

try:
    from .lexer import Token
except ImportError:
    from lexer import Token

INVALID = {"", ""}
RESERVED = set(iter(".*+?()[]{}^\\<>"))
ALPHABET = set(iter(string.printable)) - RESERVED - INVALID
DIGITS = set(iter(string.digits))
NONDIGIT = ALPHABET - DIGITS


def shorthand_resolver(s: str):
    match s:
        case ".":
            alpha = ALPHABET
        case "d":
            alpha = DIGITS
        case "D":
            alpha = NONDIGIT
        case _:
            alpha = s
    return alpha


def multi_transition_simple_automata(alpha):
    res = Automaton()
    state = State()
    final = State(final=True)
    res.add_state(state)
    res.add_state(final)
    for char in alpha:
        state[char] = final
    return res


@dataclass
class Atom(ABC):
    @abstractmethod
    def eval(self):
        pass


@dataclass
class UnaryAtom(Atom, ABC):
    first: Atom | Token


@dataclass
class BinaryAtom(Atom, ABC):
    first: Atom | Token
    second: Atom | Token


class Alternation(BinaryAtom):
    def eval(self) -> Automaton:
        left = self.first.eval()
        right = self.second.eval()
        res = left | right
        return res


class Concatenation(BinaryAtom):
    def eval(self) -> Automaton:
        left = self.first.eval()
        right = self.second.eval()
        res = left + right
        return res


class KleeneStar(UnaryAtom):
    def eval(self) -> Automaton:
        first: Automaton = self.first.eval()
        res = first.lazy()
        res = res.repeat()
        return res


class KleenePlus(UnaryAtom):
    def eval(self) -> Automaton:
        first: Automaton = self.first.eval()
        first0 = first.get_copy()
        first1 = first.get_copy()
        res0 = first0 + first1.lazy()
        res = res0.repeat()
        return res


class Maybe(UnaryAtom):
    def eval(self) -> Automaton:
        first: Automaton = self.first.eval()
        res = first.lazy()
        return res


class Group(UnaryAtom):
    def eval(self) -> Automaton:
        res = self.first.eval()
        return res


class NamedGroup(BinaryAtom):
    def eval(self) -> Automaton:
        name = self.first.eval()
        res: Automaton = self.second.eval()
        for st in res.final_states:
            st.content = {name}
        return res


class PositiveSet(UnaryAtom):
    def eval(self) -> Automaton:
        content = self.first.eval()
        res = multi_transition_simple_automata(content)
        return res


class NegativeSet(UnaryAtom):
    def eval(self) -> Automaton:
        content = self.first.eval()
        alha = ALPHABET - content
        res = multi_transition_simple_automata(alha)
        return res


class Char(UnaryAtom):
    def eval(self) -> Automaton:
        content = self.first.lexeme
        res = multi_transition_simple_automata([content])
        return res


class EscapedOrShorthand(BinaryAtom):
    def eval(self) -> Automaton:
        if self.first.lexeme == "\\" and self.second.lexeme != ".":
            content = self.second.lexeme
            alpha = shorthand_resolver(content)
        else:
            # special case escaped dot
            alpha = {self.second.lexeme}
        res = multi_transition_simple_automata(alpha)
        return res


### Cst like entities for better performance and less headaches

class MixedRange(BinaryAtom):
    def eval(self) -> set:
        proc = []
        for part in (self.first, self.second):
            cnt = None
            if isinstance(part, EscapedOrShorthand):
                if part.first.lexeme == "\\" and part.second.lexeme != ".":
                    content = part.second.lexeme
                    cnt = shorthand_resolver(content)
                else:
                    cnt = {part.second.lexeme}
            elif isinstance(part, Token):
                cnt = {part.lexeme}
            proc.append(cnt)
        left, right = proc
        left = self.first.eval() if left is None else left
        right = self.second.eval() if right is None else right
        res = set(chain(left, right))
        return res


class Range(BinaryAtom):
    def eval(self) -> set:
        left = self.first.lexeme
        right = self.second.lexeme
        if ord(left) > ord(right):
            raise Exception("Does Not Support Inverted Classes")
        chars = [chr(x) for x in range(ord(left), ord(right) + 1)]
        res = set(chars)
        return res


class MultiCharName(BinaryAtom):
    def eval(self) -> str:
        right = self.first.lexeme
        left = self.second.eval()
        res = right + left
        return res


class SingleCharName(UnaryAtom):
    def eval(self) -> str:
        res = self.first.lexeme
        return res
