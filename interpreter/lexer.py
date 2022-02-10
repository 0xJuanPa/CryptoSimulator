import base64
import io
import lzma
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class TOKEN_TYPE(Enum):
    pass


class Serializable:
    class Finder(pickle.Unpickler):
        def find_class(self, __module_name: str, __global_name: str):
            return super().find_class(__name__, __global_name)

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
        pickler = Serializable.Finder(io.BytesIO(serial))
        table = pickler.load()
        return table


@dataclass
class Token:
    name: str | TOKEN_TYPE
    lexeme: str
    extra: str
    line: int
    column: int

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other


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
    def __init__(self, match_provider: MatchProvider,tokens_type= None):
        if tokens_type:
            globals()["TOKEN_TYPE"] = tokens_type
        self.table: LexerTable = LexerTable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j-~)mIn_U1v0S<LX87Rdlnp@kRgQ->W0Ov+Za-KAQ`-#pUnB~w|B5@Vm;u_IHTf}s%g3Q^Mo(o16*zHYcX7sO~wx;G!cE0dTX<631p}?p}2#WzaT)L<GPD?jw9xKD@n(Ur?Hao8KSkTVCdsRUYP)qFaHUQG{8~xCoRSNfVw0ssE@6Ge9Y~(H=vwVO!kFa}njM6%<sW+bXek+m5k7j!#Zu&{%^a|mC!h9$ea?D6mFyr(MzG<0FJD=I+vR}%BRcU2#jvO9HH^Yt;ICu~qnxg>B_5bUu!h>7-*SlxY!%I`fBZ5+VOBa66I~ophKO&a@9$uE|c&0I?Wk8eZrwB_Z850H%dC$==$_`y{c{CC>3J<{Vxk#E_sEh#Pj$e`I|E1Y7S@Vf`88enSGvjX@n0;2tSh&f=({<F(woXr(uw65aiF0K%mJw6P67cK+Wam^#o|93U=JA@JJSuDVz*N3R9D#FNNM%!hG&2jK;d7qL;l0wz&b6|E|30m9fht;SKB@$fGt}b&4E6lrZkPn6HUIzsLr3r{Ba%@&00FlHg9iWrkb;?cvBYQl0ssI200dcD""")
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
