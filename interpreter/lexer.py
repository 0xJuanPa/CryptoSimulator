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
        self.table: LexerTable = LexerTable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j-~+M&u3Z2?0S<U!qkHM4L+1f`PJ1i=m2B}G?Aif<6YLCIlYwC*d#Q)jc6mMG(^);Rz;WT)BBLGg6phpe97b=71`GsbJ#OBHJ3nVle?ZQUO9o16PIF_;)izDEfE=f4YegSd58-feIfPyl8A2mdo=jbq7^7ry9-96B#y?6?$p?B7@%32Hl|9u`LpWu7kQ(zCpRCsxSxWwy!Nz2?e=&qlo#4_6Afd({0-#);#Gkwf5k9?m8<&81?$;`E6}p6C0g9w19K43kKb87WnbHo1R8E(6W|5IXQE*po&{Eg`CW@#P9<E$X(;yM;+^f7b)EWKr<)YX75Nnm!2j6GBJl@~tTz$LS*p4!i=tN^u-cxd^9wUZ2Bvj)#q+*xl#(|MMem?>_B3RsAaFA8I!9m8>IbG|#1l>txkXEMXEfV0srI{pc1nuonw6V4qr52aXEHQL(-*8chf?EYG=tV0))>htI(4L;ib#$UVE@V1G9XzL+I8n;ZB!wD(uu2HiozDSIA_|+cn4{RHW6;fN6sU5?JT&YxT!1I=9V9vH8`EcPvz1I&00000foPts;Of5i00GJavj+eGE@TcqvBYQl0ssI200dcD""")
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
