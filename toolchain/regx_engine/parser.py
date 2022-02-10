import base64
import io
import lzma
import pickle
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Any, List


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
        act = map(lambda x: x[1], filter(lambda x: x[0] == state, self._action.keys()))
        return set(act)


ReduceInfo = namedtuple("ReduceInfo", ["prod_left", "prod_right", "attribute"])


@dataclass
class ParserSymbol:
    name: Any
    content: Any = None
    dbg_syms: Any = None

    def __eq__(self, other):
        res = self.name == other
        return res

    def view(self):
        import graphviz
        import tempfile
        graph = graphviz.Digraph("pt", format="svg")

        def mkgrph(s: ParserSymbol):
            graph.node(str(id(s)), label=str(s.name))
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
    def __init__(self, ast_types, tokens_type=None):
        if tokens_type:
            globals()["TOKEN_TYPE"] = tokens_type
        self.attributes_info = ast_types
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;CG)4xLp810S<==88EnQ$2%RvHCb1iNf>ij$7O@lcHhmUOt(CZV#FE1$?h9<No#NPMx~OVK>f<sPSXAm8;LX0A+55WaH%ms#J5Nf$79q9&7s86x5gP$9Ohd7q@lk364w!7V_II#i^zk_O0~QSbojQfM>Ybczg}4jUmLNv`(->DV;1J&V{!@pOI^x7JkpF)nc<S{=?=U1p0_-3(}8RcX8II<617iSbUN+p@C!@Z%2SBChGeh1%V)@ebu-FODnLb-C7(m4UqQTkqKE>;->|YASkGY3%v!fyIu$n(Kk-fEiqUTyuP<!1?+0`URnX=0IQ-T^WyFL3^WW$DCW<P?OYUuFY6gO#2>8;hDUR2-{)&w?tGx^HEC_MAy8--11lz;x7j2uT^zZ7Kxz~gkKX)$&V83nW^Yb%cOiXPW)1~x_%_Rhr<gFp3lS2;WkK<P7;idQF>}G0r6WS*?>%2CtJ_u1>gin<U9)Rb%B=Fuxn-i2)qP-BS(8sL6J<8<!iVR{~r)$s=rIWNa&l}XWWMA{<W**02CY^3H(km0DmD1p5#*S`(XR|nXyA)I}3b#>060ld6Eei;_w~TN8Ngv%br@|%)W4Nf5LVpK?4i!?V#1@QHiC!S2(Yw!tXO(&l1{7xi04iGH;*hxv`mF!sorvQu5oV1`{x`#ZKK5L?00b7qN&fxH^sdS2ORs8KytDG~a}c&f>!QYdSu-LIPv=hAHyqemO}v%+r$)+j3n^PvSFWm`9M#JsPp?MC;^BdmuW}P=*!W8Cvm(evN$Nm`HgCw4OIqVQc-|<5D4`5g_sc(}(&&_zBf(kqC#BnuWwM85N7)Gp-2LS(BeS|I<3baOd#x%0e6=kHr90dPTw>7l^t3pAVGS<PCG7&9>Aw6rLw4x5V&xx&^-iqz@ttdC=&|^WnI;!r59Ii$g?uH0=P;#;@$_MzJ}rhwMT~0-aB*Yqe4>P2?3PJxm3tgKSkbsalW`y(thfiA>X$tNA0~!sgW22>l|hAAZB#6P0lnU@<UfGfW5?kNFD#?sk~yhlFj-XMqzI+-&dvFL1HV+GeROWOhS2W2r+UuqAowBf+uURr4ebuVmU>qPZWGP^p+GF36>Tdf?4j<XrCWH$-~0>}#wxo)>xQ>P=FIIMvSzgC=qf8TOF|K~&i9me)NG$QqCTNHD^YQx+43ETUrs<s=9Wo3w%De|GOoP#JLu(tW%R;O*hfN7`k->kA37}Dxr}lVZYB5Ltn!LHaB~MVhSOcud)Miqo|@#(_!d_DXUjG$_|<YgIO|Ehpu6`%9OxxSxys}aEF3{Yc&(@lnIS|+P4=wrmXj5x)WS!*=qF?17mvMbd(SLG*AO8gfk=H_bjrYq3Y75@uWsTym&A3xw}DM4eaKY~9(*@BB4XY@lceA5Jk`c%EYTr5RXwOsr>{%^F<dPO(vk~GrbQzHtX4D(&6P#5ga<9N1!6C^*b0jVpBIJfgw>y*RM`676htRr@?aw%+WX>HhD2YZZr5EUl>f#RD0U=%9efvs8qdDD9y%9FJYx)9@{4VDlQ!vRlGP^IaP>TsllvHEf02*7Sf!gz1ull2TXy%3g(<1vT%Ey!D@rIWe7NClm%2G;CgI+JgB=@ln34RzNV(WLKF%Yd4_ntVlb4ax5QINPvul6G=Br#1-ml+=kjLJdRM6lBD+lad2t+i@?%QW4$an-h$pU~KJ{$`(qm$f}Z`)#neR#ClGx+ULi-U)wHxoYzi=ac~yweouR*XBWW^`}_6Iw{9!Cy+frOW=MhNpl;uGJUE`Co=DN{`0%nz8$dewlPSRY8m??l|gBH@cK}Y1u&)jq*`QMQb+K_Q!tGZ7?He;wx<Es-XOdAcr-qEB4GhutMZGpumi%tx(1Gbs`-s!WJ*X<;o!P>5k&VWknRTG%?LDKsCN*6qfZ;t8jZb<jU>XX5LNyeoO=o&oN7J6C4mT;NE8)m`(P$xhO)mF@B?pp4{Szgygc6sH=0Fz^g-{*UBJ!rzzjop4cJ+MZM}AxWrp^RPZmRg{({r*R9I65FQFd))7s|hNb`B$FsEBu2V9U-DR1nru?;Bt5$1+ZJpP`xmkjaz2Hzg<Ialjg$q^swckd+ZO|@9a8AMCv4nl9{M@|hXYe`e+PD=W&E)Ih<vhVey21Csz*-}R^cas!-1;G`;LkhWm;#gk9_@gPlPEZ%4+_~{DGd=u7AUOB3zsL~yU^YEq*4@<I*lIEOAMJ7WL&AS>BcEU=)w<w#N$-tuHlLIrTAe)S{p4Ir7-UNI9KmuGrUyuo*ZaO*}-lgcOSMckHm3u%+b--lT}HqcT=!Z!wR|q;@?v6xL2H1wyr@V4$<w)lJyPq)b^fO;JGzQXnROVfo!WN5<$2Sq>=s?7buU1h|Tobo=F7d=z#&^=jWS6<Io%81S_@5XJ-ilDYIU%W!?zjs+!m5@43qUDpn#sNsqb9=^&G)z{IdvQZ7z<+k*~cih9TW!@vayfzPVk?>WyfsmaLhq)vL!fR<gwNkpCcb4NE+ytoY%gTSu*w^RQ>1?<^%bF~EtqVgB**X;@taJknz>rq@z5P{c_Spi6}!GAE@)kV4k&IVf;8(a&^D}lLXZbb_aKW`<0CcB?lp=a)4DbcrxOSLhA3%UQ%1HSOFV^HNoq&8c3?S~T<1ivN`h_+nZ6g+NMYvY56ZN6!emhOKs1hE@yJppYlroS;jy4TvPRkdNDK!S3mt4(Kim;*WL@*zZBd|lhjHwf=-yqWX|z-lkcWn6{)j40sb%_qpT<uINL+}OeR2v(#WvjsoLe?kDN=&r&(v1EQorJn84{D?kG9U78hC*eEzr*Z7v%S6WFH3d$YmWh#`Y3(PPTp*NoSlEjwE?j9!Ivfqic(HRuHZ_sf{1#U5mnuMh?gCruG-aOQci8UZ7lhmkPN);<KRT@rgLBecI3`$5JNfV4Ib53D*oi+=(ATRq)@0QB-6WU$J_G@dCtrJ4K8Izras2CS7D|%9-U}gX_@7uiE&1lxl5l*bQh1s<L1UPo;`(TZyk_&LM&dnw4q;nq<w0}pSPt|OyC(kXQMG=6=4{K<HhR4Nv_HJx6+k$M>=mkOfPg`jg1d#12osZrww5!fUZ)7JWqPDPE)k}75ft124z9G_p_hOvhlUkuq#)Ha6VI@I2IKXM!;zolQ8u4Q79FqhguyU|k*F@bNt|TWW0+_U&U8SkHz4`m0W{+<79$m>h_~S@<YFjWRe8dpjl}-eFtPDb;n{gB@07caSSn3I>+2dpktk&qWaMCooa@&@#x4|I4RZRTF|<kMBOVoQf!-}eVs>$^x&y~6!KcBn_DB^<%^-y=v1;}O7&5G|BrZ6oir+R`qQ$JKm|;u&#lQ}yujZgp#l}pwrHfrt0tF0%m9iqYj0V>9)zXV&Zl_uJUnAE#Br4L4lqdW|MPN*N{lWJ{zcGYzZM7n&G6fe)Y~^iV#Fx@bzQCs~$Nwn`e>9j-LTVm%5{$u_La4bVC^|7q_KWFcS8TMR0+KXCR%|S5vU~=YWa~912s1vZaHQL9CmA8eM=B4tqPM<OQGpDB#89h7m@|aw&0)!FmwjCQhFwXnyU>WW>w#&XJ8+ZQU#-xt3zD51&Zhz8BwbvxsoP9@l(+Rb;24mAZ$Q&5JymnC)V_?wZ%=y0uFhqW?!v?$EM|X1qKZ?U9MQh<MSZXIarZRTDB=z?u=FqK6n-xD)A-A;|EcFev+HK9pw|J;VZ-M)1MzCW;F0SR)HRXl95F*~)%n9|`C@+gwXTc(J^HZ{S|nbz`ZhYFw!syPx0Nd`w(ib?5J68RRO`5QN3EFteD&7fB~aaw-S0Tb^9I(~$`V4*`(}F!XN0(){1T<ALibqhWN($)VGc?CG*s`D)69SBi_FP~eqcJpTc@<lby}GTK^5xVlMSx<ZSSq5s}I2h*PYaUI}QN=HOobQm<Bd%e3u6p=gJBGY%oU2p1)wXLHau94j6GY_=c(q^9F|N(j@LUIDLF>8FF@rpQ=90MF`vEhQa@n>dwu@dhvdM+?Aj}2((`ckuIy#BE_;9=@S=Q@X+>W#J+i`X}z!$Th6RR8R|#X>OsJo{f^iREELd93H>9{K5_1DL=fZS8m+DTOH7HY4a1c72)6FB7~FbJ8G}5brD~(aIXs?|MLekp1J1!*_z<;207SUSkT^5YJ;G@U$*8IT!9!HG%HAm<00Gn)pzi?y&cMXcvBYQl0ssI200dcD""")

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
                    assert last_symbol == self.table.initial_symbol  # just for fun :(
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
                instance = getattr(ast_types, prod_class)(arg)
            else:
                raise Exception("Attribute Not Supported")
        elif len(attribute) == 2:
            prod_class, args_map = attribute
            args = list(map(lambda i: popped_syms[i].content, args_map))
            instance = getattr(ast_types, prod_class)(*args)
        else:
            raise Exception("Attribute Not Supported")
    else:
        instance = popped_syms[0].content if len(popped_syms) else None  # project up
    return instance
