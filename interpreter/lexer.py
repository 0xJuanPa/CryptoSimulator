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
        self.table: LexerTable = LexerTable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j-~*BYo?QSy0S<Ojwd6Q4zEuSCF-y2?FfGHPehL&it#{|0IoQ#m4fF@+Nz?5k&r(JoQG{l@BgSWByjXgv@}Qd7VSR`EA5}ilJhHpF@P2Ts13I{RKVs3YY2-Hpmd^hF9jSco=Fmg$zmI0mD+)L!`=qTBU_Fve-=gf*e#W2S5MiS+Vvh7$!R%Q>6!wfp9>;v9>$;ibC7$SAp`N2!QUeGn<?si$L}h1>lkuFhJLFmZEr1L1%kqj)`nM)hB|QFtfJ?Dg8V&F{W4X8`$toeTvu--6M#dl+m1ye=zvKNW@{{^Cd-VFBbv@uY_vhgLk@0@|Ne;C$1PQ_Of`3(s`p7$2CO8Pd6<B$rfMzoo2jy=)#-NQ)J!^rBUE~*@mN=%U5xapv_sv0Eke8J1ST18mVLeCJ9?~*%elApqRE3iwVM{_i%qXTl=}3p2^i!ivIv5f<gED=R)T4)SRs91#Ja*aC@BNQv&?5u4{c+GfaixM*6iC4*6h5LHJ|&!wMzMV&$mZNN_yD>Lolc)Q5E};a^#1){h5!HnLCDTm3fsQ900FuKlLr6*(Z(K?vBYQl0ssI200dcD""")
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
