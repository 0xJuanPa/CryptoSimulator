import base64
import lzma
import pickle
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Any, List


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


class LRtable(Serializable):
    class Action(Enum):
        SHIFT = auto()
        REDUCE = auto()
        ACCEPT = auto()

    def __init__(self):
        self.initial_symbol = None
        self.initial_state = None
        self._action: Dict[(Any, str), (LRtable.Action, Any)] = dict()
        self._goto: Dict[(Any, str), Any] = dict()

    def action(self, key: (Any, str), new_value=None):
        if new_value is None:
            return self._action.get(key, (None, None))
        if key in self._action and (saved_value := self._action[key]) != new_value:
            raise ValueError(f"Conflict {saved_value[0]}-{new_value[0]}")
        self._action[key] = new_value

    def goto(self, key: (Any, str), value=None):
        if value is None:
            return self._goto[key]
        self._goto[key] = value


ReduceInfo = namedtuple("ReduceInfo", ["prod_left", "prod_right", "attribute"])


@dataclass
class ParserSymbol:
    id: Any = id
    content: Any = None

    def __eq__(self, other):
        if isinstance(other, str):
            pass
        res = self.id == other
        return res


class Parser:
    def __init__(self, ast_types):
        self.ast_types = ast_types
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;75819bEuG0S<J*l!Sl^`~jQ;bv;gdl?-cEc04pLht97n2@x6MTM|lM-iaAnC*67#V3`+fPxcry;VB29NHzrG4bITO55gwo-LVhJ__P?~Q2Zw@IDhVx!Wq%%H(Ig$O#3YFu3LLcM@cPjl=%)7;EF?CHO-AczH-%)ZF4V-WA=cq+2-&uRDqYWnuYFOO!IpXG$Ji&@BskbP6!0{uF|1XY*X{{;H{yk$j_^<BV@Cj*p_{M!v60K$TKvb;?GOVcwvdSW{4_iz!LBwZIql7e8<m&1lChOZ9N%hU4BLkk?v~qQ#yM<arZ02`O=qeWeY*~z|Ah>jIdG1G&|F?@~-QeXJm>ZY+89tFzY^N<^!cBvvXQD-C`BT<2fLk6R-8r*0sYc>>!u^joA$oS1Fz6SZEz+NVgG^(7W47#F6vdPSVCO9}=%n#*8_yy4xSK?BG1rOpzO8N0tGGzzd7i16S{4&my(7d(bXdv*j`(RAdO<ENXOQ2?Kj_zc_v}5|sCh%n*)r<xL?Sb*yiYG7XKx%NHL~lY_%xbcy|=4fcz~p^XOa^8H}`J)8&FhfxP0(>{7w={Jp%U>9+{-t~1p#-eg8uhl2f_d3v6N-dQt1fcvW)d8OKo9=`wwGUI}PNCX;w+L#agB6M~hcDu%#Sh5U%WUkw-!OOVc7kjbKX&P#tCF}Mg-S8TX-ZIgSD4VW<~c$0aQnU<SAEL#uWmp+otM3<Tm$QIT0vdxL@Fy=eGAt^XS$F#mQo0=C+(S2lyg<^uy3qdE>Rm0R88W$a)&@>I{=tDIc`WHzBfk|dn;N9kMmuN!`!f^j0#vV=x#)lVY2T7h=SDEEDf`@f55q>Ku}BHak}p1YuS6;UB`T8$zllESbd)B#{gJLto}DcUAXpa{He77bEPx~+6qtAJ1-R71M4SG(;GGSePFn`j+(0Q5mfdwh=iA`d{}28sy_l3?*Qayi`X<eK!XeaGZnC4?b6n!XXUJ;agQ@?`%;b0$hM|`XtcI=Jg#p&N;p?go)5UVzPWj`E$qnEHJhI2W_!p#{Z;@kBXGt~4mFV9;UBlW*wqoUHR+Lh6R_>sd9x;aVdP>nGjHPUJk*XcjK>CHGVS%XTXwP6ueju2B7Zf-C+m3pN1^h_zQ9rj^VzK~5Kwuq1!i9*r$5oo<*C(hM(|EYLe+zTUu07|RI82ugJ^&^A57EkH!^&naY^yHZ_wSy23BFW#-N!mr)C2J*BBdj<(I0QdY#nZ%UhI5RuTdFOh?Dgd^XasP7en&dmbr+v_S{kV|+91vtru{3#8_1L}hcWC!2=mlMd2Q1j8~Au_l>b{2x{Dm>eUb5z|<E>;Z%@aoNz>18hrU5PUqi*^{LZUuK*<t5vn;@Iugb?7?skn=c_;F>7fHePXS+5g)CS^AH1++dP6G$=xC9LNW*y7D93<!!%_lcMgDX3fL<bf$jhSm<UGRItecIry56nbDBT_3g2)yA5eyz?G2R-y>S~n5cd`4S|lHvJE78fdL8k`%Pw$)dj#zJ`1n9@^&PO!6oAn;!>XxlDR{0@F!L|s;IcG>)t4Q8o!z%q>-B@cPsUo-<4k}ZI>x#1vqm{pD<^_d!ekTTwSs=+sU1}`V*4b<E@JOXwCb__q)FV~XZa6MXOh+O?ebMdO5-l?rqIc_H4X~d|A>|`*2M}1HO{)bDD&z6bw%o(15<YYpp0$I@@U%W_jN1X*O0NrBO{aL&~V*QO-*WhR+k$_^s?a7=XPKMHul$l7m5#GKt^+s=81;{Y<d1sc86D$4k6nX>L;s*G8uPtDd3T%VVN+p3RSg<tC*|ebd=>#FBlSr=ll2FLx!LiKn!%>a<=TdL3io8;e&|e9VFrh7u5?4Z^4&}7GpFfil$2`=A@=(XuW1TfEVlOL06(0TeiQ)F<-Yl74Q!aN3U8xHyEm`**3z~(Pt`SN|FMmEvsxg^`bn~OMm^b0%2`0wG!;W<QjS@ALGwZetS|Kt*NOYKs^=I9<0_{eCg2?7#)gDRCgSfBNQ1343k}1XJu}RA#$P65*c`|;Y{fyTc?HK!~wHvc-kjw37wk@Fhd*&S>9L=eFby0PiN~5eUM{U!2|^__OqE{`~0h#PNIF=as?14wZ32Ss;85lNwWh`+JXOG*@M(wcug6;_0uroQB@Ph@<R7S<md|t^O6}^90<LxJ98P=5W(M#@lD2}&F?^S`{A66?{6Cm=NucDBYBW*Jy0<a$Hd_{0d@+3GK=%Aiah)*2FS#?Xx`uz=gh*9o}v+<nwAi_7;YZk!dYB1WFlnG&yu_d|HLIQp?83j5aGonI3>f}?;_eY_WN9i-qw~Fz|eV~-G(LxEbX#jf#zTAXTnN4Bd6jISHU^hA18YRhS#L~Fspt>=$BcRRmC8RH@g_OEoUV<?eQ(5Oc-T2L8O^NT7FUj!B}2bCnTax6JxPyB$Hh`RhR}8D)}*-p2ZTa@Bu3}k>lJr-~kgLEca$k&rF|*<h8U`q^*N*Zb|q|mLp8JC|L-{tRS?T(Co~N%TFjtg)jv5rEa3DRmZ?~reo{8E`XAY04F7y%);lEEDb1P0K1D06vBp_QUn&H4dmt$OTFlc{;a^HlRsBtzkDG&DbdC^+R=hz2D!y~!4I7Rlk|aAc32rr%5kD^i8Xkr_15=#=6fiDfsjjhO34o$%!Fo4J1T`ki`?9+e<~o3b+q-+m!l{nNFXo)j2?tctyJ69O+%X+j4$2*G=%6vN*KrA_00zUCO{LW*L*Uw7Vt<+I%<q}Q>8&u;Qddslo`b3K`zEQlHZlW1ZGO4UlFJUEf)3E9{V(ASA<2fbo*~s{}7k~Do*3jG<m+P3jEhQ2uR7w^plNF;L9JbBEG=d!Doa%c;vPa{ty?12$w2nzT^OmOtV-VU%SAs#m5g9FRR0@7=ugcbP0*i<auf%Ks2{|u?@@VNO>o^8h}srKZb}B9<^mtfFNoF0MEMz6m7vbBDF*P%s?9_IiztW3RQZ+i2a}ov$YkVs7pE{000006s0Qh&Z__v00FrY`;Gws@5E<EvBYQl0ssI200dcD""")

    def __call__(self, tokens: List[Any]):
        state_stack = [self.table.initial_state]
        symbol_stack = []
        cursor = 0
        while cursor < len(tokens):
            curr_tok = tokens[cursor]
            curr_state = state_stack[-1]
            action, content = self.table.action((curr_state, curr_tok))
            match action:
                case self.table.Action.SHIFT:
                    state_stack.append(content)
                    new_sym = ParserSymbol(curr_tok.id, curr_tok)
                    symbol_stack.append(new_sym)
                    cursor += 1
                case self.table.Action.REDUCE:
                    content: ReduceInfo
                    popped_syms = []
                    for symbol in list(reversed(content.prod_right)):
                        popped_symbol = symbol_stack.pop()
                        state_stack.pop()
                        curr_state = state_stack[-1]
                        assert symbol == popped_symbol  # this is useless because stack is always viable prefix but..
                        popped_syms.append(popped_symbol)
                    popped_syms = list(reversed(popped_syms))
                    instance = _attribute_apply(content.attribute, popped_syms)
                    new_sym = ParserSymbol(content.prod_left, instance)
                    symbol_stack.append(new_sym)
                    goto = self.table.goto((curr_state, content.prod_left))
                    state_stack.append(goto)
                case self.table.Action.ACCEPT:
                    last_symbol = symbol_stack.pop()
                    assert last_symbol == self.table.initial_symbol  # just for fun
                    return last_symbol.content
                case _:
                    raise ValueError(f"Invalid Syntax Unexpected Token {curr_tok}")


def _attribute_apply(attribute, popped_syms, info):
    ast_types = info
    if attribute:
        if len(attribute) == 1:
            if isinstance(attribute[0], int):
                project_index = attribute[0]
                instance = popped_syms[project_index].content  # project up
            elif isinstance(attribute[0], str):
                prod_class = attribute[0]
                arg = popped_syms[0].content
                instance = ast_types.__dict__[prod_class](arg)
            else:
                raise Exception("Attribute Not Supported")
        elif len(attribute) == 2:
            prod_class, args_map = attribute
            args = list(map(lambda i: popped_syms[i].content, args_map))
            instance = ast_types.__dict__[prod_class](*args)
        else:
            raise Exception("Attribute Not Supported")
    else:
        instance = popped_syms[0].content  # project up
    return instance
