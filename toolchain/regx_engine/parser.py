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
                    graph.node(str(id(chd)), label=str(chd.id))
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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;CQ?ZB3%GL0S<WzFX5vQ;li?xBVj951Cv$7#Xwol-75cUaA1~Ip#M4Jz#<n5x~6yksWV#T<Ono*lf)Ut4mW30DEu@3kIe^46niyw3fUryrf|L50QZDN;$jZfszY4H?u{g{=5?C2DC*XUcpj1GaVdT*;$r<ae;Y54E(j`xxW}auA+%BVdU=GUW;9O0vtXrZ%?<zTNnrtyqt&KTn={6fDG(CmxJbdu=<GPnrCW`$l)Eoko3iY;KPHD-7^)o*I6wHk7MY9zfd^7&4cqvQ$p3}c6#jxlA7b^PB|3&etv#uM_6C04=vRX+`<esDC35e=Z?gk5jL#_&l^@{-J$Bsv#FMd)8RZQTi7}K>>Pqoy*!>b!VYff4<_}9S1mC8|r$FJ_G>{f)MmukNvz&Z-`hCIFVez@nwxEVFO}_w#ih45h|KPq^ob#E;$^@sQ^qxDTCub>zi^#5yM;QUK$EUiYaWoV{G-G%B`WEFj>FlRhWv4mWUBkyYWT(&_lG*&t;OVBjN5QNx6(TVXaX<-z>3v^$uC=Y9h&$qDi44RK^o&cd-T(#8BW_-hJ*UugFPcE%<(V||*i3!C%LPX<?B<XGuhiI0yvvpK<JS^6nEpNH7%yUv@M#c)6uHXQYx()FHbtThgE(t?=r~}^Wno$20iv$+YKr=Q9V>0Da4^|z&_Ll&b*X8fY&on?FV~VrkI-P-GyUEoj)o_qsVsa_sj#g0Am7-JKs#-F18uQow8J7ZK(YJEl2ldwQ?4Pm3-(jgnIlYu;QCa&fKFz6$2J+Kk{WAM$bC-U{SCC@5Gzk{&)6jHX#9P|B?QO|%{R;FX>w~HPN7!@#}xKIx6}xZxK=ieE(B|0m=zW_SK*}m2F^FL68&U2f$Hq*({MgLK&@pDoik-23!Ygb`Q3H;1<b|+h6k2xY$VljphTco?`fr$>2cOw0o>L(J~w@c(p7J>5``VitwUO|@@{ycL%WP=x`9Mi<0FKch1)oK+7>C|Ms;?3fGx&MQiw-c=ifvrj##=K(*{q~pSC&)s!qpItq?6=k8Pe*%V4Ol+2zSkreJJSU;8A_NXA`^*}oji{k4Dsx}qdDY3tSA6QQOC3P7NV4vSourq02{?`TWZ@`J?REcYJ2A@Ai2`MFqP{@?Fd5I5<FAJ%nmhMqKOLcn(r7=joEwG`--6o_@DNFl>bf4#FKnHzzul>h+SMpAX<6mhBixph)yQ6Zb)<MDB=Lu+7}V<M1}5C0_)iF!`+KTHbnmjFX6CQ#Mg#(CFTHq%jR3Yf)thoayp=h~@-!N3@daAA5wHY!z?7TxMFYoZ%8b2*-QAM<rA-J8(0Z7jRjd|&e%rCq1&T)=9zzMqu-15tw~FbVr1g#<9UZ}9AVP5tJ#+xBda1}>a~>|*Js&)DR<i-!SU#4(i2W}%UzS_bw=H9Anr`Dmaj@7cSeps+?R&@#DtpweVPeHB`O;r5m%fdz{L{9QsyBt&89C#cudfEf5t3iIxCs~IbX+c+ftRQ$;SbdI-#O?(YY`WVH&>v)~c#)tO#sY(3x?Vpm+#(NtmcgChr-TiS=RP{qjuPW|tfBC&V?1N0{@KUVsXg^HFv>LeA^W=D5B<-DLu~_y~+uS1)i2z8KOrBu#l>|viy~A3Tqgk$>L+P^(CjR6z3vuxqu%*f5H`FCyM8xcBUTr7m2i1jd#b_XO{y$)1c4^!{M<SN6%`^yX^-1pRSb5tq_=U87wj2zL3gl;DiO|`QOM`^I!trijM%Q)nW|fkz9(-hCVs&pSxDtkE%5s^21WAO(N+Cy(-|N$vB28-d$@M`(1```9y+1wrVlC{rVBWB^OUp>=pMwOviU4nBpG>OOTt^v^w9m%~42{Y15Or#rRwWaI?2qe;Z&#EQ&O(jDdg}EO$D7a0@qlt<Ggg`E6ta-A+462AmjOfW$!4<9XK)X1BccV=$^-*cR`WUbmxNU-ET^)pNNM}lvpqHZmV+T?J|-oCD%%&QgcQ%J4N7CPuCO(6t?~0NK-Xq!q2lWFYP}4O-k^)Ih?&&9R|1D#IbYo__?*G^S=RSGf12i7DejZ`({>M#xfcMJ4S;v;w@sl0|HK1mV1h~y7E0$vQ)?T_`l>gj3Vc&^5pf>KBm#vBP>F9xYniHcm3&<CLlqg`mZV_;d#GR>ojf<;AZn;JJ#$`Rm#P<;ML8iHt+EA@o+h(8h<MAUY(>_km<GaKM$NqetyfjzVmuhPjfwrPejenZ^K!s=*$Xxab#6;WC*j_37|lweVIPV_n;NxCgeW{~#@Ty3G~WSxg`X*{ir^OHlCMeez(E>pZNcrJ4r26$jCw(C!e_zj762L#wX`?5o}IT5u#t$pf|&{QL=WSQFa=ZXeU%tp=59ZQ&@zhtoMTrVhXALPd;w@|QwSei`^TrJ)Q-oMd-R}359<?<C#1D6$na#thL4<Y+FMojgpl?52Bd+py$1-x2u-u<<WHK6-?F4&49?h*G|^1SNC=ALrs+r<H|MUnqgf6+<yA7tZf>MBSbC1M<mzMZ!u^uLpPqCr&K|8IAsytK|LUbvtH^E>`ls(QFJ2VGuK#sn3^s{LJ`2QYqog}jst@mWBww-OK~K_QRxQ1pw-j0UDu0zF82mhK0WyVgI;O48Uk`X5R?K%AVI9q|ZyY=ui~NM{m(Qcg1l1o-M1H_y+P}MMkE#-R3o@u%spak1r~`jWxghq(wjMGXXza0;q~Lf*<bl@{Vwb8GuhJDuE@8!#%+-X^rG1~us<oW7CGe<MrOuq)^fR_EqD)mxBF9&!y|7TI3k?RtAzKVy;LA-(XD@VY2Y$&v9vfLb4_^rtrp|*X0Pj9El$X}u{ycmpQtw<j6c|dVkQmmr>OT>CMG!W9S88fbgDCag55jR_+Sko2ENs03Tj;{xh=H!8Zaudr6q4h6BKoctE0AQZEP0#FMP<bn<dI0UkmlG{KDPspoxByq@pXm16{Bv?)|7zqjB`!iqB@jBOV(ROZB{X3WS<>O4V=rS&U$(gZ7G)i-hkqXXpQ{0emJ=)GX)RIU^Ia^K^k@hfP6;0$d1t4SoR4DEn2VU?@^L%D&c$ebR?gQ(eutQX~o?-mJII?<0O^;o@?Q&tKG*Is0^G{W|Lv)vcO>1LBB;AnL4NUlcGX>wab;IdB?7QcDXZ}cpiiC(6o;aW)Spnna$MwPECXqK|}Z^7;!6Qt0k)q@byMo|BolY=B5XJ8rwinxlR>YIqO26G$?*!d*x2xn<X-V&M*FFjkC7rDeGAIB;lig332!y04o6g$7uax&A^<07)fejWlMNhta!}I5c!e7oVQ|cXKz<&r=gWintx~`J{vC}p1@dMk4!PGY!I9w{>D6V|K1gx%An78W{CSwz`o{;$Bo$}pnpm@8!~$6es#`3LQ*)Y1)dU~7>-sW$a+T(;7>JIc=ngWaL&tTwTna2-od!Y7p33IUs!R_M?SsFh8PcHj2C9>cbQ8bf_M{(*X{iTNb8R%;WMpaE@Ys^%ra>dUb#vzA)jL|^)*fA@%EYIwO95-|D};e4-+t~t^zcCIOQ+&){QYH{*04zacf^Lor=QNy@~KDlwJsW7C&cAi(bcaFUlj%*Mt|U<y|F9y<^%Ay&7}xX&N7G<(F5cNLciVMr=ag6*if%86TKpm!E`Xog+jeOK&SJ(w#X(G4hlMX(5n7yX_s*``*Y_(FW<|E|O_ieY6=Zdoy?;HeB5P8#xm8K+)l`!k+P<9!7#Cqugjc^;a1dFOm|Ku1k^JvtQI3bs{($kmIo<aA8EUBoa`tw=!c&1Vs2v$vjE>$2O|HkJkc4&n}es=GZbEkmCaYD51D*@7-dWjuBCsgHM}%mk(v#2@M@=xz=w9$bf=fRGYHxH52g}5b~pa#X<^(7dovK5APE5fM#^-lTjyU-uhc<ka?{h^^G0i$)E096IE`>LP;VmA;zR|T3h_xJ`rfp=wh(_(+4`RUL98t&u!|~k4DX8gyp0K=~}NPu4a;$rcwbIg*fa>!1XtBg@K&|Bf4AaCT@_+=Xp7irQ*wQJ1q~0ZbEwv?n#rxyq^xxjQV&`M=AC6E)y=k`0v+X4hD4%@U9YH6yi*Ktlw)fdQENNc`%b=DF=giJF3)rfj#aPW|*3Pbv@)?)iZ=7%&{BR>Np|6THW$F0uu0)Q53DmHGN~;)>$?sSu`W>Z^m>#&tf#;1Qz$CZ^}X-o8&Y0?wHN;xmC~dZ$hI(QMv7oCp64$X&uQk!DacaU<j)gfl!WeNsg^wx_%*sU}lpcKshg-MP)~k*=~<|m;QWoAJQ;prOcJ!N{XpMe*ugtNM-4rr-Z!f+`z^#X=0S!PXGV_sb)T6oz(3X00F)lz3~A68kfL}vBYQl0ssI200dcD""")

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
