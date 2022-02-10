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
    name: str
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
        self.table: LexerTable = LexerTable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j-~&nl=3M|l0S<AHB_~Ak$fI4=l@#oZ67EPJr|FQ4m<eF#V(fd%G3sXN+m8xIRd74B!(3;;ohz^~lfE#!u+XP2EqrooS?5C$ST1~LPqglIgO$&7)@otoW^eJ`x)6z1f(zXsV%BA2rtjMxIu!Yt37oWrs$AFSh%VLrpBMQR62b$o_Q2*Bc$Ik{5FMi>8c&Gbng}!q4zOXFt&z0l7Y@5Cb06GJp)sPL5|4}BO}>N^O$tWiLCr;9US$Y%sA*T8d40Wp-{X{>IPbcU_5qwVN(;Wq`rZm@R9=^1aJ9|NcnBCXfLIK~r*uS`UT96zbNv(i)m@T@Z8t9tbrPzsVeLeblzFI@f5TgNWIQi$<qW&2hLzv<csih&FXe=3fc=e_`tvU{6hQ``hT(C-p`dO)8+{)cQoH5eW=F4@ja*?@i~--Mh_dRGG%yQ|K=%QfWn+l1us2sAb5Vz{vkMk*&rqdDKDcJTBX7mz4rpfMQPCRN0RC`S6B@9il|VmaDZ+CQ?NTB)-6M$@dZa>;;d)v`+vG2#@ZWx?-X{a~69w50Y&D-Ks7yqt?AYR58mVk8lqa^OLPM7I0Ok9A<Tc)AWj{6N-vPUu58fsQlPa!aSYPeU?<j^20=BJo)c^nhZ9am`Tr~=^00Dvo%LV`dd(v#cvBYQl0ssI200dcD""")
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
