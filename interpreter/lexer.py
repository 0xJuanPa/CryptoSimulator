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
    name: str
    lexeme: str
    type: str
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
    def __init__(self, match_provider: MatchProvider):
        self.table: LexerTable = LexerTable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j-~$H%%3T0J0S<lHNxo^NL+1f`PJ1i=m2B}G?Aif<6YLCIlYwC*d#Q)jc6mMG(^);Rz;WT)BBLGg6phpbYpt<0)y4tMEJ2XcW~$QN4WrhYFO6f2K^hENr~@}$RugPy88n2f?JF&rUbxv(3T)xi#7!LSXczt9pk6*W9JH#~4uJX@(WAC2f3k6mN(_cp@NvR!DOnYBZUeBA942C|y3ac?;Oq9IitX{~;Eh*I)=^&YkFiWBQyrcd1iGJ*f}Qyp$NX+Lviin%BS+I2r%h#yD#lP$0v|$gYW3WIq5e><-Nq&Tr;X$xDL1VV&aV(-SvIq;!il=nk5$Rjrp<wJU)k!WmG+{T{%?O}UA!(WwTZpe_g*tOVDV*D?QJl|5kiY-OadocP(dGfFlSuW;}pfe*7)C`mt7mPVTDL$y-~IJlH1ZxQitEw*#|TpqY#uGDPkImuf1v(RD%Y?wVLixFbMb~v>HMd>gdkmZ#d#jLj4RZqYn4}7@<@)%-*OzHG_gf9z1}aLzJ0|ak*LKc>8fy(ekbw`HlDWtO%gVvPRau+Bt0GcSE#+oX4=D(G&|;JcmJPPO6FvA7nTy@AYW)x&QzG`i1S+`Fmyq00HI$hz0-v^t6a*vBYQl0ssI200dcD""")
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
