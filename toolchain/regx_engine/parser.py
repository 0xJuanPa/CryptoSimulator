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
    class Action(Enum):  # inside the class couse weird behavior when deserialize and no time for investigating
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

    def expect(self, state):
        act = map(lambda x: x[1],filter(lambda x: x[0] == state, self._action.keys()))
        return set(act)


ReduceInfo = namedtuple("ReduceInfo", ["prod_left", "prod_right", "attribute"])


@dataclass
class ParserSymbol:
    id: Any
    content: Any = None
    dbg_syms: Any = None

    def __eq__(self, other):
        if isinstance(other, str):
            pass
        res = self.id == other
        return res

    def view(self):
        import graphviz
        import tempfile
        graph = graphviz.Digraph("pt", format="svg")

        def mkgrph(s: ParserSymbol):
            graph.node(str(id(s)), label=str(s.id))
            for chd in s.dbg_syms:
                if chd.dbg_syms:
                    graph.node(str(id(chd)), label=str(chd.name))
                    graph.edge(str(id(s)), str(id(chd)))
                    mkgrph(chd)
                else:
                    graph.node(str(id(chd)), label=repr(chd.content))
                    graph.edge(str(id(s)), str(id(chd)))

        mkgrph(self)
        graph.unflatten().view(tempfile.mktemp(".gv"))


class Parser:
    def __init__(self, ast_types):
        self.attributes_info = ast_types
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;CKrS3S9s|0S;{<uT;kbN>je#zL_tC#*xSN^SsF!18s$7b30F&k7@-R`$@$71C2(9ev&&gudXt}zj?nWAmZ4<P@Z6RwW(EyJX3!j61Y<YaV1oY5H4*h$eJE;ji^mfB8RH*hE;e&<_NA=CCQ6qq0|KfcsQZ^`#%^OQ+bBFWo-Q!#iN64mvRnk7d7<ega$t1L-K(t>W1F$MOt43r7{oEIrAj)5_|`ZvAoDV8Zq@474k!O89YFmlBE9im9S|a%^xWFqA<X(_mMh8r0;%V&}YsS9913a+OP>#^%><0p>tWB%f33xbT$MK)9ggq2en2o>}i0HI7OiX2Gr0iI1)WhU41@1x*2o>A?nPip3XY4-?n(kv8h3&<rtHni{o}r`C`To#uVT?Skq@lZ2=Pk^7pXoDpnX~Ji@$S-dzu~ZF}ZDjYa-&1Y81KQ=EsSN&(`uEvg}Lu%G3!jn^>`6;LKX*){-N=6?v{D6GTRtxCqtPwfZTs{ySI{nl;bMpX=vuFL<+u$L{jp?HY5Ql}58yv^Th5jRFGy8-866w*H%o2qndgejF$bjui<=@tP149{x@xz!;mp0jkfCk?amm}o?4UhUdfZ{|bTEfMd9sGSY@TPX>`{2S<vHAuio1|(wXITrO>RYCVToh&#TP2};X=W(gU$J+>kpIgV-eLgRiX;aJ0Mtb6u=T`dRbg(vgqbhgpLn`g~`;J4P^UXTVwkNB>Ko&qLabF1?!_{TfdfXDd0Mn}>7s3-?fDD<)0E3KL{FerGYBV*4RoE0P;nRfH)gcLLv#PJs(jxFf4!=f55V;OrpxOG6yo#j-lS1txK~DYE<HhMJpMRlAl7ELh$d3>&@lTG)c&+w=zyp!Z=z6A|UQ>X8DBy7dbyI9*!{9#PSiGprZ?`0A7^Ni@Bo8Y+P<oL}unf%r1-mGvZ_SEVZH0XKEEj7IM?Tl;emkGfcZeS|O)xW-Pc_L|E5p^1Q<fN++m)x&-c*tYL|NF7xy;|TQJ5S#J!XgxX87s45fiY6l@SX3aWPQCInl_Tb|y9WST|Btc|Gjr-5^awQd8DR!O?9n;UC|>C4fheq%o~sSySHFK=UK=ntpY_TOTdlOBl{#5%Agm<egq#-MN-EjyF05oe0#_Dj<!#697XIw7m;q{p&$MqwSX~b?q1SflZEz3Q9a{vg-FFB#U8)<@m||tf&@Laed?X-klNpooic!dDhq_q(|Ah2YB^LSUlyRzZi}RX0N>%z#@UW3)%Tzt2Siwn`}(-+3{%nVuV>bawFh+%kkd(K>#7O8o2ejehxHFaGD?f_pS~n;SeK%jz}B%#%#JXc12KD)(N`|GO+Ab29G{Bygqj6#&g^IL%yGBWPVbFzxXMx9dAuZaY~=x;=JIw=(P37pLad;%LGH8=tLKNB;Hwb3S3@zaO_t@D<%3P(C`@6O~I>p&sxBKonPDJHfH9W&!Y&)$75-O9ICh=`kU?!3!}u$o<crlU^-#6FdIY!hAcx-d6Qf{z0j4M;6R~2ihgO(YcGS_9VtCj)_D|U5I3m#bUa)u8qF&w4J)^p%YBP(qg)H{2Sz?d&y)jii`XXAFYgU1k5SBG#YV3A#NKXOw2c=clMu`}AFHjh-d451b8qk?o_tW5<A-@9rC-i2SO6!6a-K5oPCVTra-UL*7_Y&}`;FBb>JE#Q?|sb=sP(M8k|V9RrhWr@!BXHGH8dTtz^DrD!#Tg``JjD)T%a$;Geqdo6f;XMG*9QPO^jNHF4%0{+2ifqez2r{TVEo%Kr7HO7_yp5tzQ{b(`Z8-Gr<j&5Qm7lJ^fmGoH30`nH=jpOpAw;kg*@t6P?vQ!|1X)6suSrbe*!^%Ta=}h>fqrVndv}tEH*TO1_fjHSq#y4&8&o48Zc2(T#bFDKArOb<)pTRp~$8$XUzYZu{uslZ<rHY|6F0A^NJDJWeC)M3B33wa|UQ&+fgUM<pd%(I|(?58E8S=)$Se>nH-TTI?TuY%zK%qVx(Fipc!Q8V&uBZ=5)c^x3UVk^$ffHGvE7pZn0FPI5PwRP>O2TgA*mu|@4Z#del$Rh6B|o>X}cBaiWKL%H=#BS7ZX;pP4_E7+t^-|hpQ4`|=fBoNco%P@t0HZ}ykWRN8=yBr(yRxH;FoQfnXkDWefnG!NT`qfSL9dWI=p7x=7ktPxj$=SM%uFea!szPshy@0^+RAya$oRY{kc0Xm5QgNb5cX)u`OQS<^U)3<Z=lN-x9;u~?jDrdm->yp9z$pNe77t&SG7U-NT!6t}LlCdCcq1kh#aXahhb*nv5;kWFbhr=PDcii76iZR`9S+!pBJUE*rx%38oz3-)mlN>i7-)Uh`KF?LB|yRP5svY9ewjbbm+35himpJ&?i&BQM8mkgm!f@{@;h~Z=0igb1~v(AeE>ag4nI(p{Zy>#)1zc|J-}7~Hg|+rB9hkUFbFlw)5D*=1>Y<2mR;kDVac#DH@g}t5NY{#0}~S6VOoL}2`MI*-2~L_IB<Uq<KU|na6fTw<C8|Ea#=5z5OgSvciRQe>j>~qoR!acuxg_?iDlaRRD%aUMA805^tFn6n)i+uaJ)+2@ES-5%$4DDIs&Ic5RRB55EOVDcQ?BmE*5r3K@=cVe`~BBYR*$mQPgH5nAJRqgqNIU%d@=KX!n6cyQ&X%Zd&Y1;)7T({54Ta8)P)JN=SfFueY5xc$Xc-<^VR!L0@1l7VPC3-e0<RW5;x{H4t~YpJr6ghQ-RS;gp1nNX}2WsD5jc(zN~~;_YrW8|;2y3ro$8X)f>Pz@Y}b<k4ms_hk@f*1u8erO*7bJ!+ZAFSab+Pw8w8ahoxYEzNj2EPp_=3s015{a92s;+Vo9(agy!3mhn^D<xj0|Il~QmVyCC%2N`6Nsv1pj08tUi=)8S2{P%mkElKSSA3dP@Td9K=A_=4m%i>HBw1mkH-pS=(5LMN=^g`cW_`GLG~%s;*;Ch$k=HHiXwmPWuCF}&pJ5kEfnc#EI1o5Bl{09&nX2J3rpje`*03L)y{ArSr38z+_IQ+Y)k139a9skk`lb4%h-ftl#znpBk`HQnIuN<D$B-13kA4(RPH-N62kNWXe)Ve%favugStpXjhUrUh$mN$<T{d8joO^y(W<&3TbnRs7t1k=`{Kd&$EbBZ{D;v^p{TRn-^iIz8M>U!YOP>df-LZ~EvLu-*b4%*a<=2U3>fZ7ok?~HHCdWeni?;S^G->N&g2?^Jw%IoE$6}8{=f*-BN{$UE_9Di;M+oVs?4Jn3JTo}!QI@;@IPA_xX?$gAiY=Xw7#~kVjdyN%BbK=!LyY9epK*p?QuiTiOrlO6s#tuvejICubKU2{gZ>gKtU-DZs@q=AW;<WU79RSY9^|<v_)}Qx_t1~7AHFNcge2*ux%>W6V~f3k=*~GO*mWtKhudVsUNm3ikW3KV<*O2wym!ObNC&}CD*$aeaS%Ix*Eckb*7*;CcH)-mxX9}<p?_G&rnY>qw`~!lvyY>a6SQqzM9kAkm+N(V6FOC=QOC*yYh%qa+1Gc=ut3469cQ%eT-@Cnrez{VtTshBlZMrbwhmvdRkF`p7yyS59m;@FShtHSh!>0)osB{O;6gQ%-tUUXC{7nb<*1=jWkq6OK<kYJefEax&%a4q|2H8kOOffH7~z5rQ}k`6F<gzoQSZMLoLJ)f3GJ6C<q<@qVoNc)(48$jAQ!UAIB7z0u5us}{tB{;xmT{(Et5x!OH*@gD`GnzhT`0*3O#B>MWi#-Rr!yVnO>gi$!|Hu2{wsct*P7UFZkWs6woAa$(M%ykXj9R0%L%goz`#5x9S8Vzhah{33n|43@A@1sHfS)PCtB(vyp5RHE|feYiw?RQTQQs)UXIpLm9UuuwZfxldYn&yhK!_EQA*X%ptyecW}2!+Y4rtfOpagm|qt%Lb~;vB10hPi>Ir=ww^}n`s^0(aI0A8D3#jUgV`=})XRrxxu^J{c^21*Q%ty2&%WB`Do6mQoUO_BNu1Cgrf~!-4uV$!Vi5pmWY<{djUZyKkx!Y#=)*gb*14ffVh%&ya~lKT(3J%4$IkJTso$k&gaK`U1Rvp7Iy`c&zA0^G!7n;p;cgS8;}4Y1^^}WK^R~A%AkTf@?@e{h;k*W+Rx{#RkV^`KNWu!=6`m{_idaMG`zrqO;3_N2!2`Uk<-84k6L|lVscWhR1*8a)mAx?+Wi`y@D}8Qv@|8b%eMREC@fx~#hwUCo^99K$ZAXF`k}&;OJ!aK-tFQSv7+y^ypoh6eO7utmUf@sV0b0Psr>x{m$g+bLd<gPQ00000hM4G}B)_h#00E{NjPL;fAL0-#vBYQl0ssI200dcD""")

    def __call__(self, tokens: List[Any]):
        state_stack = [self.table.initial_state]
        symbol_stack = []
        cursor = 0
        while True:
            curr_tok = tokens[cursor]
            curr_state = state_stack[-1]
            action, content = self.table.action((curr_state, curr_tok))
            match action:
                case self.table.Action.SHIFT:
                    state_stack.append(content)
                    new_sym = ParserSymbol(curr_tok.name, curr_tok)
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
                    instance = _attribute_apply(content.attribute, popped_syms, self.attributes_info)
                    new_sym = ParserSymbol(content.prod_left, instance, popped_syms)
                    symbol_stack.append(new_sym)
                    goto = self.table.goto((curr_state, content.prod_left))
                    state_stack.append(goto)
                case self.table.Action.ACCEPT:
                    last_symbol = symbol_stack.pop()
                    assert last_symbol == self.table.initial_symbol  # just for fun
                    return last_symbol.content
                case _:
                    expected = self.table.expect(curr_state)
                    raise ValueError(f"Invalid Syntax Unexpected Token {curr_tok}, Expected: {expected}")


def _attribute_apply(attribute, popped_syms, info):
    ast_types = info
    if attribute:
        if len(attribute) == 1:
            if isinstance(attribute[0], int):
                project_index = attribute[0]
                instance = popped_syms[project_index].content  # project up
            elif isinstance(attribute[0], str):
                prod_class = attribute[0]
                arg = popped_syms[0].content if len(popped_syms) else None
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
        instance = popped_syms[0].content if len(popped_syms) else None  # project up
    return instance
