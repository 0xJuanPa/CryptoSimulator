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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;C9vwe_a4T0S<b$LFOY6;li?xBVj951Cv$7#Xwol-75cUaA1~Ip#M4Jz#<n5x~6yksWV#T<Ono*lf)Ut0h=p+#@LGKM9#mg-DN0U*&xeckx*56FWpPi4ZaM>5ZfhXmYKKd3mbd)D)(coy=uP$nY!;jc-$y8V?Z_9y@Xn!IM#M(&PbXAeOfSe+ikgazje;bg{GD7ZX)f+`I7jF3K&b1bK?kw9?Me5qnZhh-525p*TQAAgEnL#4&CE^OkkQhMDZFO1#}%*Q9>#k=wQfsBYQ+U3A4HOkTHDp(!SzH)17qV-<u84O|mDfI`<6$7~<<7Es1Tp8M4>^XR>xSzi;nEbADkM0n|Y<ii9xicA<w0wzKIXGfoDGO5^h6FwPlGxydIVV4=mpBdc<(^W*aqcA8|PZG)x^{1~Icdo8`eoVP(W(Uf_v#3MM+RSjBT|4c$VcCGYmiTfs9#INOaZY|DeR@hk5Aj*!e@CAcrxpcHjkxm(YhWUz0L)h}ZJZ80Cxx|mH$}U+neAW8K*@6Wke4s&$=FpnCg-3GY4N#?AJ|VH$MaI4K)x`A>xG$7GNmD=y+&L`(&<6cCex!r=ta4NvI8&mXhCPJ9#R6%kUma1c!7sG}QBTVMZcL39uW$AUwi4ZVoOJDhVmo4FaEyEnkr~deDC}&ji(^<K@*>S$-B$i6B94fDO_K$i3AMr_ePH}HyA)G=o=he-kf5~z*kgmsUg3djI_=WWRsR}h-}pVPX&cDPu4qC!n~f>jRA7|j|Fbgc*T@4pg@uYMDWVxBWXbB<Oh5~Y=Lj)7{pYS<G(}?Y{(00ewD-kkn}~r)-Q(kru)-sslns$cK=u<IHL@!iy4n%r(u2C*lhT-$YgdEjcjJ!<OHut4`HmIVJ@2^T?Z8J&ybGxgC{Ja&Tc{SXMQBi?05M<nuFnXP-`vy=$DmJ(p^row#wt%uP(&ofb9ZuJZXAa~SS(^ZZNq;&8F$VEYeheRKWiFra-aIDN+EyO?sZsc)^qw2@pKAG?(t(J`X~t;uC3JAEkEB)P_!v@eDZ~u!hZ*{8%!mhNXc>#@Y3_g^yt;y0;l%_;^rO$;jRQaRR4INbsA+DM6aC;DlDy*s<$<KD>7NsKYhP7%q`H7Bm2iuyU#$Lz}(+#PNv4+kqRh4JEbDz<a#MEM-&((jMTIdDMG+6-+L(nH34I*=P1J3A>*4C;*(Kgg(*0HfHbanslE-NP#K>F{B2rXZNafI73Tm8CxC_?YPt^>F$@(6>_=RBC#Vv6V4%9~4^b$oLc;kOJ_sqTg6cFNSZj*Es4|jE(tQ703Hy9>t07?8DsQEy{(*j^C{o{>I`bj`K45aU_`G|`^?d;9&saNc1_9ssVY#p?pP(e%Bxa6U>46q!<B6(Dq(zE+fvudS$@<Fz(<{aNS^jtvK%U~jIn^oD8?~-(XWV%)8^Y5{!D2I8<G(Ae(xMh2-qVNxtPM&7{7GAQq7OX?c6*46+Sh{Ek8SQR0FwV^j%~lLO&{2W^z1ulpjXZ~Yq5Zj4=c*g)SIOv{PFsp>B6rt+Un#yXRE5_Z{*crRzAscC2^jE3H`ZHDuO_5!IbI~^5^9!Os`N@d@i+cb)O~(0<<#%amc)SB`(@bh+o@zZP(Hen8=0jExm-S(J@mn>9h9VE5aQtx-dj6A_<G{!SJY^YP?fB4l<9veaAojuRDd^{Yc1d4m1@*wq2mVQmq0$A@2<J<q>Nw85prUgf<8?%FlBV5J2kX=yXRvo!rtYzdly-B3_~<UT|UQm}^W#Z`4lN`)9W!#M}Fg6?itZHGcWMCxeW;YEe1X*lK?kd~_c?wvEAZs5TfycVI4p*d<to$ZJpYToqR5u$Dr`h?@hFGg;zSZD|zZVB1(#kKSN|O<<XDK6QWIC&^Xus<JZ%HwqyO9KuO^sRnW#U$^c1mUSqgxwfYrNF-LFx$}(S+tXa}gsNyK8D<0Wp|JE0W*Wxv2(&ZaBnEg7uy0>7SyxUH`8So-XFq<yj>QA7<q)j?aXfhIMVZ$I*HO|DNk5d>7q1sbOUKUKZOVjs9JGr8cQbhpmWRtMTi?hWe7PEuBuH#{i?(baIQ0qVa2NwaI~PB%B=1{o2W;<v;O;%MUf|2<i&^uexE<@ncTGB1#nPdHh4MSaCoVGRR5YoRci{m;^`X}Fp0a@Z@x<Ju>7&EjKz=v414O-UB-s2F`mX8KQt55SZffL21l7FWImRD;eFwqG4NCA<0(bZA=+C$SHr!fTeF+voz+t4xNU~nODFON!c1_DU+ie|+KW|AgkSLc1qX2~hN%nuxA_G_l;4M<N>ipRPR@kZLDBk~yHH}KLR8|?}=_{a4Gql2HJD6}16s!%TRO|5e$p(}cA;P*z|M$7pWcCj10#-^T6WdC{oMiMsAG<(svV?}?97A`LdtF1s&J6rGHV8oG6@#H+W$GOVx_;1vyPQSnu2BI^9o}`n_y^8a7kt2MY$>6rrve<fcm+q!K+<0r^Zzg5Y^-`3Aqk2!v$iblb-HgSYDl&;5eDO1cr39<B=UsXCzemwYlV0Jdz}4aUe{lVt9L!O1yT7a&8;)gZI&)rP5;u?v-Liu?D+0TtsqWUz^!TtZcdH4V6hK9u;q78`_in?Dd*SYaL<?oIx{*v?gi=Zhb@~n-LI;M?X9nQ&mx5nAj?q<QC>Qr(dwG_QWVkYXuP=EWP$v`*NQ8#y927>{xdK>QPUU)noM0#|22CxTit&)dvC;IfCMnHxTiN*z_%-v1O(tNe%!Hkk!6O07%EjwGL_)8ly+d$e971_JtX;q)wBIO(QztWh5?C}*4^zjjjf@gVo(P>@#FY4kmMrdAPly7fJdtl;LL$$lD|`kFz-h=vUXu+>q!1^WjO-J%2OCit5WAZXe`G#R9Y<=!tPfS4)bnu?xS!vQcy}eG{bZvvQw;Gnd25ZUO$t#a|wS|%U=xxd?S}**mfqC5g<M_DhGa1dh*QVdE*P<qL5o0HL7<S$gheul9QU<Y!9m-!80RL(;{9VTk{u4q2+nkJ8qnVE_z{iAq2pk{~Qx}_{Msm`9p#H;4D5!{EQLFGR>^ix<M<_KP8`mDXeHWmDcwqOv)w@OEy{!Kd$}<8HHQMpF}1`jY(CAF}Dva$q|V)Oa`5y$HpGaEfDJt(ox+~nL)F6LXb-BWcdCjam`sg+vz4CU1Zx&*M(&zZ5zuvW&hRi#;1IJurEE>+eSK0q3<f0>oEEuk<#*Mt7mX+>1fdyjgklTbLzL`@5F1Q_C_k6Y|NaY-agX+DE>K!938hw*kzASuoW%A!h*?9n_nxJq1Yj-F0dNS7o#9}uA_3kaJT)T7qvDCDLZn|vYdx<8b;YdrB0Fpxdap1fmCl*9$FUt-r{EytZfuIG9i>-rmx}FwpSRghkZC$)CS99pe<z$7?Ja~pW1)lxzLLg6rjmqZw(78DrboG6#4p=E41?uQ3p<zv*rkJE@scQQV77mKq<Cll1==PgF#-N#H|V;)i`GUgoTiMla84X{C#h!O+<50mQ7Ctmmv}urhp-(FdC0LC%g0i_1;wkFQM7fc9IOi6D>+CLuL7jThZv!;(!pEZcop$K(Dkav#b6`6S=<2$wp1*wDcjHL>%FExExw&ggXIfVIjS_b=ZNw`>YRC(J}BMPx-Lp^?sX{Zf&5cQfR7T@zpZQXBMH7HY;9}2*qALLNovX-Of9Sz<{L*)+-3>vm0AET{x$~4go#ph{~24DKiJte&)-d$l}m1F?M=E$wL9b)gzJNH1oCo<U1IeIa@Z})k%XSf0nLei5}xRIGyV@<WU<e<I&MSh2k<k@4Ngv>kT(4yXBqqRN0A@@89z>5X_tzwuxqczM9Bnj@gOy4k_Pr4Jh%av8n09M2UFetx}r}*F)+g+4?|L008(xpqEfOv<gkV7P53!m4L`3)TbKVY5mnv`!X|vKQkb8MU7N?$k>?6ZanrBG=!8pJ=-`aEq$JxkBUux$>D|ler}Pyc?bp~TN);SK@+V+@XS>pU!&hb#Ns(<b}B=fp_Xocd+1VA$2*6WT*-^TU;EnG8um*VRJ25SrZi#S1cgc@&x^{WCB8Lw?u-jtAmJ9zMU|uFyaSA;MEsx5EoqjBNB{r;+CEru8+M4Q00EmB*X;oSJT#`-vBYQl0ssI200dcD""")

    def __call__(self, tokens: List[Any],view=False):
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
                    if view:
                        last_symbol.view()
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
