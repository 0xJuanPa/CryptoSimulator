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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;B*NLBV7PM0S<lr_`Kr~;li?xBVj951Cv$7#Xwol-75cUaA1~Ip#M4Jz#<n5x~6yksWV#T<Ono*lf)Ut0h=p+#@LGKM9#mg-DN0U*&xeckx*56FWpPi4ZaM>5ZfhXmYKKd3mbd)D)(coy=uP$nY!;jc-$y8TwovN1xBBt|93t0B%ev(zb5)=?8WpF%#)X#n8ifvenJHV9*xGcP>D2{%4FTAak4btPGKv!wXNcHUYg4cgtOPWHRm5O*ym@12f#+lpCsOxuO+=TBSwB8xw5>fY!QaJn%BsQc$Uom@F<dd=+7-|_m09_{oDna5lmAGWi|qXvK--rZx%O!uK}D{r8xM^G7EOxY`S(BwFf}Q@C~JtcKO5(XQDj?v$C4{X0@J(U>vN`W<Zs@kW!OwrRSrF&=un}uUGJn3x=WN_uj+Wox#c<nfCO;>nnY>Qd_udlh4%oKH{r_J<1y!yK<6VP=E7K3;rCw`|wBIw}jmq8eE|C&{xu}VR~vYlM7nlAco9Q(`#gK=b|f_(XeDFi!q;~#bl!lk!xR$gx2%hR$hay7(T~KQ%u(A8KP+;0tn<%|MbgB;Kv_CICicKK8|L7iTKF#jBTC1icEUvnfL#MF7%@haN*O?7WiDN@!a^8?OP8|^(t`+sQ7qvq$|%o9boul>WoeK6feQ@_*)bDr8sijkaRI14@>4(L|XPn(y+NsmsJ0P!R*UZ6?w`QvD)TrD5_k%Q@>~d`F@OfX>SDrwS^{CxDru-@gzgi3aii5DcGX<IO;|`@qODQ#PN}XtiYWp?dP&>L5ioa1Cg?|Ng;TEN~$jW?T@#{rw1g45{|EpZGqz_E=y8@ZDN@z={BQBG;JPdAA&UdTupU4NMr0!dZC+pBH?G^ReCC&0OUn)^Fa%_0TPtX8cHx4ecRthA%>Ro7Djo2zlv;A_<ud`=0Hki!M%lg-=iuFN4<mQn8!|d<^3uIx4T4)NL>QbX?b}RNSz>)ojGiI!f$%u0?3(+YW^4hwEaQ!QOpzA*RAdLXsO0PCk#*YJg{%Gj)VT6G*1HCvog~kK0J1*8l!Z&7=2+7)jk!za?8cl*t_=m22+F)hHs_6GjnpRqVv8Qre9%meL;|)QKBSzAtfMDi;Wl4Z`6f^?e*DpbiK1Q`ppg0z$$voIqQ!*G97K0Z(I7@K_v{t892RHLE-&6mwdknQ*EtvwMjKr`I&$(8tyzW-f{G~^3*ChQSQyP(8~>p)zn&~u{}ZKzO7Nxas}>c66r2v6py?qhUD~O9uy*IX>=lTLn-itSQ(c3iN6QNdZNFE49;T-Mo&X^laFQX#!i`ekU?Rs@BbPCqogErH7bkwK(Qfj!-L>aR7LBJu!(w0<1>)9i-Ke0RJZ%f+rqfGOT+05E6ySz!wR(+h~akudv2DjcL*S;@MG2Ljon&(`(*Q4IaJw^0rT3yY?N7hhr-?bUMgu=YyLosGsXQ(4xHk_YSEknGK`&GmwF1&faB7RucMQ#mz<FW>P#y}W4ECYPHyl~eA^vmn%lPG0OG|*jkg|O^J&jrwfDbB-%W1c^U->*Nqp07n!Dy<H0Hni>2j!vORI08B!O0GYZ(>y6viQG=tokbLeq9m1Ty_LBRYgQWcQ4Na<)TKW&zP^Hp+IIAoc!cCVCr0NbBCzDtSyyKS^2QZ7pX{QDb<RhFDPv9L2G@F>>OCGOF44qrTVffk8+A@yzUl#R0pD=_8Cr8|jFy$bxHC-Z~v~0Jyu<86D761o1CD>F*42U3_}>p&?Mj#^9f_zB|UDN*>x2@;&bTCC9x){)bG6aiU58U?jE^9^_DM3I|z({JaW(VO$+Ye=j#HL(=9WxqYJv)zqgcSA2n!N^y&LE29pb9yduQ+1q=VOVD{V*dzyE44&9Bw0I^%4ae6^T{Q<4j%yh^VJ+R4s<kVwl4H{c*FntiusL6-S~zu>ogOOiDp)I#{V0sZQ0y^Bpn^M_KA~@sCphHC+RWI_wBCs&2?YLIcP_t~4fbO}XX{%dq<Itvax8bjq*Y=g?Nc<R)7u5^qEHTU(5`<t5yx#zCDw+riz+~pNs8I=R&K=CQ^}4D9euFqwNyNMikeP!T<nSn@hwq>kH2}&5$Y*4vxV{9-G?A&Qmf{R83ofXRz)~zW>n%VV2(<MYSd1$b#wdmk5821{iodV--q)YQpe+mxib?lgDLze3D;0=Qx%6|@K%QpJoj06{35wms$FDTTb%Q|7)PKA-!RufGvS9%F)9#tm;%RFZN$}9NBr{Oxm#rP**PMoJ>RfvsqZ=(>e_guS6=775hSUzzx!9g$pL=1ib?izv{@M>wrK{Pr*Kc9;^i6OYi)G$Z%2}(w0_GX*UK8qZ%>fJA&P&p4cxW)qpoWGMt8W`Y)r<JRB`)qHxdtf<<Lm_`E7--ZBTTDLz|HpGIXsaHzIw*bUboKnUn(tKEFwu$Ag1{+c}EeS<nzv{Agik%s(`CbA@nP1WCCIPY3S8!?H^u`Pjrm(hij+ao}#cDu55(%!SEMM+aJrHEUxB;E73j%t`dwHQA-AGL<K28f!_b(Mhv3(s50-IUlVt{%G|W4?lK$FLzIjiMTU@;AlRu`s$dyCg1tv^P^NRMrhRV6`QuXe`F)**932b?3NFiA`;Uh^0a(DI<F{_h}Nb7x*1mG>)r<(Z8$l8^6Z}r?<FX6AvHoYAP1QSC$_d2aHd5$8S<*B&k1aUnPNg&PK79xh)rCbe$$`@y99tU=PA#_?56ns`6+Q101+xt)t{XbAc+u-TI9VeSeCd7NSP*%gb(u`)XpN%NBVM*Xr<oiAI^&S4?H70H3W*e<;tiC?8cpc&mmmLwC#}80t4G>X>6LiQAiOrZ@KXd+f*gMySX%4iavTYrhmTes+UoKj%v1+H{D_xSt7x={)A{e!(W`X7sQTYH!Fyt>fqqDkJq(OQ4DnHwe7af<xJ=cNtD-WqlrmW2`d(TGd54a`I8;Yi~OJ7)31CJ-Z@fuyuit->VuvW)~`KHEB26N2XW?H9dZxC=}V+&3twMMNooj1=~Y{&DMy%nGB5#zXZ+2oD9bP*QAA;MuH$7jjB!o5Kt^hzv|Y55=lmE66u;yvMD5v^e#!;)@ON+yRw48hP*27z825)|G=U;^+v}7^!px|$OSULd+3seP=}pk$=;sM!?ttl+d~yb>J7G2@PX)^eP0I|;-AC*JoGyG6pBF8{FwZS1v-^ch*&<|*%4KhAv3C)<+C>Vdjns8dx#h6t<+?IuI%hSTzrx?u@D;k>vO02^NDDxlg3g$8zgB;>dsZ3Pt>x5iZ<v_#VJV*>^T6J%u^6aqt`flbVpjG0k({#NOnhC6+cTwXA#%jvEuayuB}Ct*&=;`Sr*mGNfCb1xJ|kjZs=#!wVtfLA_vou@RQK}!4_u+QHPN?A<LOUpWa$l90+y_WwR9%_>ZkXSO^lMw*foOhM@1`nWIWZ>k$>HmsaPZiA?Ld6aj0$f0@BIs@`tb1f0MDNq@^r(Um4mv537Tx9eu-<>Uzu&LOTFnE$YUn{H#x48XJzg0NhiFu!t7PU)#UIJ3Hh2D{?o?W@P%epk2%m>(9;xOzV?ZzX)s+HWjZcVc}GsWu?tEWv$%$Zk3b%M6Q<NMn#zBCu5^Qmg%PYLqVEGtEj&kg{=rLRmg5>B(QVB$e`iZadxUWZ}HDImaD^Hs6KT*G&`;PV6aCU!I55d;sv2_k$Z=zrUZ*7WB2O8+;c}*3GkEPhiE~vqZPBpVS9G_#>~ZqnUL?gJWosXHy`X1hiX|a;4g?hi~Q0Q&FQApq;Y>0mZtpq#&7MQ1n1t#rmE&sFjq5NGD9v`FX@|jme(O{mni)^ZvkbknmH3rDIa>8^oFRGgEnY!fZIjSA|v;iK^+*yQKSI0DpRWQ?uUc%tUKt-V^DD7Mf@(yE3_O(Up5<FYc_S&P65`hpXhkIpCuk_TVNhmnFQS0WVvU7;ba90RW8;T#H9gP`SV-{WMbinFt6V&2}c@cv;zPD%l4;S{wszb00F-kis%6VI8RqZvBYQl0ssI200dcD""")

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
