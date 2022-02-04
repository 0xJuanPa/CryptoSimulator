import base64
import lzma
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Serializable:
    def get_serial_str(self) -> str:
        compressor = lzma.LZMACompressor()
        serial = pickle.dumps(self, fix_imports=True)
        serial = compressor.compress(serial)
        serial += compressor.flush()
        serial = base64.b85encode(serial).decode("ascii")
        return serial

    @staticmethod
    def deserialize(serial):
        decompressor = lzma.LZMADecompressor()
        serial = base64.b85decode(serial)
        serial = decompressor.decompress(serial)
        table = pickle.loads(serial, fix_imports=True)
        return table


@dataclass
class Token:
    id: str
    lexeme: str
    type: str
    line: int
    column: int

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other


class MatchProvider(ABC):
    @abstractmethod
    def add_matcher(self, sty: tuple[str, str, str]):
        pass

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def match(self, mathcstr, pos) -> tuple[str, str, str]:
        pass


class LexerTable(list, Serializable):
    def __init__(self, eof, linebreaker, spacer):
        super(LexerTable, self).__init__()
        self.eof_symbol = eof
        self.line_breaker = linebreaker
        self.spacer = spacer


class Lexer:
    def __init__(self, match_provider: MatchProvider):
        self.table: LexerTable = LexerTable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j-~$u^(_H{S0S;}?5IlR8zf}42j23Z9<ueiEL^PQ9oN}j97t<i*Ct^@+x9Cp5#p2z<dIyLolH@nK9r}in$1<}XeugbL7$ictQ&%N2@g7IXaA~0T6%4RgvA-BY^N!mhtNPG?S=Jxk{RI0q`cv|HfHERzwQ`J||AfQx@2p#?o0we3OY^jKCbEKO#+Bb{1mq^E>SJ2?N|C3@xEjFPZ;cht!u8;^UCdQNT!%tEERTTUB;_pYLN%S)3i0rr`DR^`gnG>eoLo-V(OX1vi`Jmkr9+uq`_$wyC@4pgSKmgzmc1>SngqY!C>w%Db-)$JBA)rEMo-UHIkx~ZGXdD42aDgXOrsX&?6c4H=P;JN<(t75dhZ|DrGD;}d@<Lc(NZits_aG4z$)c+JV<N0wp7n4lWQ_G2KMOy$cd*wRGO#X7ou1~=){m`pB7kw|BC>=`*!<0%XV#Afm^(aa~3K<hhfqr^VnV(*wnllNKBj`YUxSM{>S5cvILQH+`GxE*XTMD2XP-()05u>y+osfiqb!tJ*n9W!MVB&yy&in(rV*}iQwCTjkmLY$~6FDZ%D1eV(J`Y2uSEe?@hz5(0Y26s*Ek+cqze>#IOJWlaqB7P}B2P00Hj<l?DI+erojXvBYQl0ssI200dcD""")
        self.matcher: MatchProvider = match_provider
        for t in self.table:
            if t[0] != self.table.eof_symbol:
                self.matcher.add_matcher(t)
        self.matcher.initialize()

    def __call__(self, input_str: str) -> [Token]:
        tokens = []
        line = column = 1
        pos = 0
        input_len = len(input_str)
        while pos < input_len:
            current_char = input_str[pos]
            if current_char == self.table.line_breaker:
                line += 1
                column = 0
            if current_char == self.table.spacer:
                column += 1
            name, match, skip = self.matcher.match(input_str, pos)
            if not match:
                raise ValueError(f"Unexpected char '{current_char}' at line: {line} column: {column}")
            current_token = Token(name, match, skip, line, column)
            match_len = len(match)
            pos += match_len
            column += match_len
            if not skip:
                tokens.append(current_token)

        eof_token = Token(self.table.eof_symbol, self.table.eof_symbol, "", line, column)
        tokens.append(eof_token)

        return tokens
