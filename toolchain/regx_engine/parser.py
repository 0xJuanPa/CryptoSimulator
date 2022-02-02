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
        self.attributes_info = ast_types
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;6(}vm0bWp0S;{qp*6bcVRbqJN8GJ?1QgMjB#xA#e(8d|(fxoKoj1+h1Uw%E-g#6dr|yNw^^1j)yE`-A`_xB#nNg*YTC6rUHEea-6pMudHwFvlU?>f4P=zV_R094LwaPoI0uM-QdzsfVDr*S1HmJH{>Y|Q<k)Cj6RYJxExc0kQrBH@y-dJ(n-fmafR$VWFg_F@#tYAL-aqQb!UdB_99D(N+qkjTuDaCzOD$c3yM8t?ndW?`Esk2M+z2-{nLeWb)1}@)!24-8XpT0kJpXV0c@G(chp}2)Lpjh&iKtCSNUP3IvK0RJxq&5CVV)ZjFJ$ZBu3ua&<izwF#xuk?H>#>B*pQICGZ>ks)4|0<>IiMG-l#TM%rI31L*i%mTQ@_EYexr#~+(1Bii+*<&D0&1bgdY#~UnL+xP0z+hy~a%W;!1aWePsLN!<*Wh=OsXe%%@(imeFzW6H%Lki~z<TKXtjrRUlM}JVCiYcDl~)N~|fdKdvMVX4J+5DY}Z_`d~IwW~@ZNnm%~4^Q|~);x+w~%8|40+u^@Eeak({<duTsS0!{K_SceK>_}50Nok$K(q~S8&}?WFVP7>`M)EW;Q5OoHKjg?{P1-zDZNd^V@?UT`ab+pQ$N}JL-&AbjI|I1ZM~*wCIX^ofe`%##k@V}-1@Bs49o)GhHFo604n|LKCM<4<@Ra1H`avXGQvT{!!Y3rwJg38=vB%kDNU^?(bWnTf%F$nAbaF+TN;@wle@FOpX)v_bEVZWVtXWMt!^m@)R#IO-RuldZKr7fDPwKb^aiQ)fY4;5lQoUq%G!6O!JG+^oP;;FRIJtKxqdu*IVh!M#xI!{xQ#%WtBdwt!wx^ZSBIH34`b^xgJYrg_d7R9ZG#Sr!&4i;ICZ`dD`c(PCSj-eO`28iAdON#pd}xQ7N-64j7#|HGWkv`#`U^^KjYfGQ4FmE0Hs!UpxMweimT>~hpmI&H!8WnI?S?KBcmJ7jCpM{E6|*&U4j*7yR^Dy&w&*zPqH~;7E#0@jx3>}6v;Q^2CU1TZp?;@H2o|y_Xq9k=Pi9pWrJdf5uIs--B0iyf<4PZoqP_^@sm&)Zi!Fsb3jz-Hfoamjh>;(1el=<jhCpW;UOjkgDzl;7M>#YBIx#-QbskkY2e0iI%4Xu;-ArHr{&f2*#1HjpmAyO}j<P+q=?FgBdE!>K>i<~=4oJ$b7rtlL`z~@l2GB2%lJOW94v-;y7T-4)_~{9CMz&HlsxqZ-{4nfpC$yX;xp|nF=<q4Rk7Th3BC!Vro&ty?Z%<KSjI1G&+ThEtps?N9m$3mq_co|tG*{UM!bV-~(T4i4Re3E)p+Ic&!?%+8(4x;nC$TCq%jisf?8V-7%0)5gWp(9^V8Msc2jjm3lg@XD&GwMHT4apyE<>{6iv4Mn(Jkc&F@F?KI-`L&E_={q;LciEev>PN)!(4YVS^6JqHmjfL;+j~H*$^LNg|k~;^=S}1xVXG6cj<Ft+%ov9z$5@Cud2X6`NHG5P#~@kFS`|rryHc@2J_aF25p9;+AZ#e>;ZqcKE6Ttkz2KldZDU&(qdE>+Q;mH`577fkOe=f%+-+sK)%+DiA2;+}me1hShGTq4EP?|CHMw1&ozFZrmp}@9`S|=Az*l{n@m{N0RU$xyBTyg%lN{COmlBqQc>oDvI>V2GocFuo?7o2OssY7TJGq(~nGlGS=AYA%%VOuTircFsq`*kh@WB+pXJ3N>Qyy>mLqr!mG5qNO~w9A?MCNb9jA;b)1q9cfXtH1ibH-&M>sPYDc_0OxySM1b;bb0$=(lZ7W~g(TGH(PF`%NvFH_h1K!)ZZr(-T8dmLq1QQy43|@8>^msUnAz9+#ux~xlQAT^pWD4kL7l&TG*BJ}#hwvr=(9Dg+gwx{$A4D$1^|8&i!eoXi88B=B;7$&egSQi=yT7{*T_5|PG|Dk~;H){Na7GANr~Fo;K^TT>grZ4n;vd?zivCkS5X?%SbgU34*F(G7X|${bAOX<}CtRI}8Nh1sXPrX(Zm{)6Bo6iFD%QMAP%fSFtj|@%UPmd@-+(^eoCt9o;7C}B0<|{OMv-=*l6*8B{I#$I6TNUI;Gf2Zs!{QRaR9WUoN$z_^5d^I;B9mk$J9AC?+am6PwJvh5<qcfI1yAKYwmfv^myfM$s;F^*u!OTgcznMB7`Jd$jiihd<#Dbj-mQ%Y)THzro<d}AgWV$y39YXa}pBopG>)SKw<E*SgYLIIWa-%3(NV)xnhg<K(n|MiFTa$$KjAs6V0AO%S`ZInLVhHxma^W$yx#jX3D~X<m{GBzTumB#9a1+c{ia?mmc=w%<Q~AG{ox~PGj_~#aSE44a&<`s$8hLeFYOYWixD?#XY$-2V#q*&zQ6?i!C|vUF97lv+}+u=$p)qNcD`(Cu<El9+G3#KV3B|W-_yt1%LpFpq*X-CbRpJ=Tczh(20d00lj~J<>j08-cR8PIW1|`6F5xt*}utn$K=;Sol;Nw!!)hdLkweFdSN3R)_xgz{_dmm;&NvN?TY0gWL)FhlMgR<3HKQ1>xhhaHepMnCQsuYPWO{{zt^5rhANAHE=8B7EK+lDN<wTpI~+E^fSjKQKSR;&5s$ar{ma@NLhigt%~OzpkqFFufB~Z3|Ne;Wc%<={YO8go#JlT)fF&O4jW-`ucC0)ZHJ}gu(YA72-pUuKM~_%5mNvHns^kFAiOA39IAN5tQWx2yEL!tBKg*-V^$U~l9Jc=vRjL0wU7Tt&`_iLM6IMl7PIW7LcCPOK1ZRlbLx=z6u!CQNhqh0}uKQYXkr#kM$*Ojr6Id-(p*B!z)d?1^g-vH=j$%Gt+ZckdTs)Ek9+ZmPh&z?zX@iqDjs{ip9?s=%LLqu7%20Q`n)*dlJYIqtiukO_93ba^q=nK$WJ6f!rv2(m_xURHvV0aeba8LrjzEW=G4GU*@J$ssg?0VX@v9~$qCBm?wR$U6U;AZ!|H<9I6cUkJx<AWu732s>2;YwKq4g*FFtyoe-03s02}NO)MZYy!S-az6v>ZG+d++~}OfzouTQ)aH;+s$My0Lc6>uSOZO|x)PlzF6gjbK!5A(*TQAp!24_X#e6iow;ZZl3(VCt^%%{#mi#yJwJKm;T6;NSDEIP<Y_Z1II33k`H}FjXJi@000004|T#s39cU^00FTRi;4jNa%W=tvBYQl0ssI200dcD""")

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
                    instance = _attribute_apply(content.attribute, popped_syms,self.attributes_info)
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
