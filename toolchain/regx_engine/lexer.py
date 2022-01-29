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
        self.table: LexerTable = LexerTable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j-~ns^=Uo6m0S<G~aiqlZ$fI8Tv|EpCj%=*H6-cjYj^ohJ_rwVMz|>|4CRop0{E?A#%B3;xP=7eFnsbuNJfZ}xMjVe9<lXM-#B2e(P82Ltb!}7Mj<-IJu@8}OHaAo0BX8Cw=N35QowBAIQF{cCrj5yp(Z_jm^{j)c`b3&}07idUTa7=2(7r6N7Sl5hS*4<VSldeULtB$(8Kb^z1NR+sn7L-7=oD~TgaQZ;FiifROu_m;-0wb=RO9)qpo?;~uG{yQWPLE#1jy~*>UJZhc+e$oK*o6w<cJ0$FqS_{O2={#^3wnSGCoV3ebkak00Dyn?E(M*K&&7JvBYQl0ssI200dcD""")
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
            name, match, t_type = self.matcher.match(input_str, pos)
            if not match:
                raise ValueError(f"Unexpected char '{current_char}' at line: {line} column: {column}")
            current_token = Token(name, match, t_type, line, column)
            match_len = len(match)
            pos += match_len
            column += match_len
            tokens.append(current_token)

        eof_token = Token(self.table.eof_symbol, self.table.eof_symbol, "", line, column)
        tokens.append(eof_token)

        return tokens
