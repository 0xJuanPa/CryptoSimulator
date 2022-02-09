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
        self.table: LexerTable = LexerTable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j-~%@S)Lj5T0S<6OX}TdWhWDT|XN#}($6?%v(qLIhWS_0LW<Ce&NwoPF1MtL`SwmPyo%hYJ8?tEwjNfymP&H42jgykMY5;BYhc`E`iB553JMS8k{Ty+80ANMWh}ve0Rchb4kNzE2g^_jv#s;q_960s1w16~gpgme@oj|_x+$t|e;WadzR*IzrE75S}dNNCSC@q5#Yr%s*J4fZ_9)BcP=fRBfdPEht`mnCM(g8U}4iOyG$Mc+9gjuk0#W=YX$9r6;RZ*?5II~<hI`@%%Qj!Y)b~IT)dIV2(Qu)W`Oa{}2ydE*{35!J7qFlxcQBYV6?IMWEsW3s!Y>JHuy6%~;s7Oj`jzJkGXlUZN_pEFZvcheD0Pjhh23%rCN$IekcJJU717(GZPj%1yp43D1Ah_(NKX1WQQDu2@7^`VZdVLa`D-#x@bm}E!ZJzz7?u;KVI*0oYy@n@;@ZC^$wXo$&tG02}0P?7AIxr4HVQ~(0hPtWMlQtIL{_AYN<w$zvkSOo$$cz1VouxFa$u<S3-HOc9ms`JNBZ~Q}_2p+A__`FEb|^`3W*8tilnW~?$xhnqhiFl3!gFLsJhM?H4}yTae0azWR(YWSgpGg*ZTa3S00Hm=xCQ_K)2%E`vBYQl0ssI200dcD""")
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
