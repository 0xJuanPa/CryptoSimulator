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
        self.table: LexerTable = LexerTable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j-~$r@(_H{S0S;}vaKw9+zf}42j23Z9<ueiEL^PQ9oN}j97t<i*Ct^@+x9Cp5#p2z<dIyLolH@nK9r}in$J0Sgl9Mhd!C=n?G(NU7qWR-%hxDgU(#*Uj{W}~)7iEJ^L9l?T<M1TbX$rzBft0v}f^Vx0F-Xp}2Km2!WBN{zGmSdY0pdkE9iY_)vOAe}bNlVA0m2b*eqtxl#GAT&f0yPn5S>EN>B5dXpqoDWvT>EIturNJ@s|}hdnN0t{4dBD^~V<68RjW~oFM{nUnvY|FfADRowr$l`JJoUU+aPFg#a2wgc%|b@?u>;xM+_Y-Z27Ow$@we-PeM1dd{H?_s>04jP#Yg)h`MmG>JpdQRb!0__rj4R}z62?5koy>q?=7Ro96F-C^-)=iu}Yk(lSK?QrnV+tK&+7g)M`eyF!v&wKHlFUL$w`EV`FPfgr?OQpge<X03q+OiD-iHE(OtkSyVFx%@rlZp9hd6L5{#hrSPZ!?AASMKM<W4RPFCRf88w^r(Gc*vY!sfTB7?|fa1XdmPEU;bQqGJ{<7bS<`Dg)LUcNQc{DIL9EPLbaiwW#j2Xj-OdyESCUy;55$^f7UjgnZ({uYyJQLSyg{Vo8GOs00Hj<lm-9*8x2TRvBYQl0ssI200dcD""")
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
