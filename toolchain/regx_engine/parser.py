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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;BmJLSX}@>0S<V#p7CQ4;li?xBVj951Cv$7#Xwol-75cUaA1~Ip#M4Jz#<n5x~6yksWV#T<Ono*lf)Ut4mW30DEu@3kIe^46niyw3fUryrf|L50QZDN;$jZfszY4H?u{g{=5?C2DC*XUcpj1GaVdT*;$r<ahRZu{m+0XgQCJhHCN-+6@1_U~22vpXJcPYHs7y8AVWl~F0^sc8(T)AR`h({XdV;wgUT=3fUin*jRLsJh=%Bn$M)_A`#OC<P$CLE)8+L}%H30rUBU98tnrFRhUFI2D6q#Ypo{0WVUB9q*Z0I3(8+`qc%d$DT2F+7b(WES*p~^;fatyV|hDCWOTaI1({QR-YMfZHwNJzj1vPCs|Kw-r&!0p(;!(t|cMcUx&hNFt)r)dSb0_b98m$u0C4ryFXz^3r!vycQdkD3OP#8zPsNtC{>^+xp(QbCBC$(VTn(i`i}Ewv!pIHwYCkaN)S6DgsA>bMx3e<4}u*w9tJyGyvUT`u<pO5o%AcsuZ>(T-pt`pi{F{1=+)YTJ?~K;5@v9yD2(i81UUs@JfQ!E1wA!o<$b^3@)yuTsUcs~%e)d^uis;pGfnI^Dv`kY8pUuF;tB(VOvw^c&F}aesP{)OE|XyeJG`nGz8Ea(Y;=RwkG)`Gx#tp_hT^ivei1ZOfAaX>dfXxD&76ibrs-Wkf8gXvU;cl&Sh)hru<H<@%j#V_QVDB)SeocNQT&np_z_k>YR>+?p^CjxR^?a(hh6mj;O~ZoIz9BIj(vgHDvyevqdAPE@VwAUrGcjvuC3p{ZO=Dn_}PU69A*D`GVsJ8+|Gr9GZ9@^NGJbam?Z&I1GW@GZ>x_%R#bT?pjtjLN;CXj#V!8enuj&2TQoDB2`2IdzQSQ6=>sqvite1ayD)p^(C9u9bMvvmle7uvI*FJx0ojM`EgUW#vxN8sbOlRQR%mpYN2^{U_8mUEh4?6Yo$m73?ow1a8?Ku0dLws>bsOK8^dKPB?wf3|*~!^Zs^9;{<t^G&txfb7$j+-#Jr~WATl4^mSvh?#iI41%AM%sH%f*9PErz|5(U8z|Fcp(HoRYnX&Zhmmy8O`lMf_G86;4H<WfvU}j={Cj*JHc{=HZ%3IDwF8!I2x%xrgb%O2BOq}rk!dIpYajdZ^-1nF#*c^6ESH`?mIsl*Rj>>*zKsE#77;nuf<I9r}xK-;#<cEN0U032#7a+$-&!eKBo(czavCZGSJM~tqql5HWFaarOZ&8q$0bw>6aw=`vD#?lfhFn5QDJ`{SVSLUkxY$O5TD*sba`WS|HmRNi$id}aN2OsX_Hr%{{oGJVT^Px-rovcUNg*RTK%!I_<d1Uo2U17U{eA6fhvsF|p*Ry_za(W_bZUtoUkwco0*O=V62Tiv0b~W{C(L4A>z?7I77@iLD68Ocb>rK5iv$=0tpxqi9+w$}(<4*ta@sJA>JHFWCwdT(l^%Iasl8qFSyy5)?>ja77ermUW%bhu9VtbawHK6|J_F_=1u0q;VK!sE+OuNvzF?r=vHS#qk*0y!Y7o%H#3bZ^k?j9sb4EddW;i7H0qW|u)DHGvRMLA;69(8QUpP%mF%`oS^f^ov<1>G9UdAGiypXoAt7jEpFcOCq?>u3D1D^dt_b2JJ%8bdt*)&RJYM+RH?c`GGI(5e;pb^VE$`BYf%_?$;^!10lW~P+o7sgh~()kPvs4n*oOp_%d7t}<+(bN+N#^GEiTDD()Zb`pD0d$++^dI5>CHWm@V0zrbgKIV7*QN4LKi{DuC3>4Vm-)!`I>sm#Y86k72lLbo4f4T#a{kfBOs)mp`36|?@HrV)Z*@m6v{#!f6zXHQeDZ}<2f0Y(wh!~@3gBQ_P|q47=%hqueSLL>p$PPs(=7HhTkviQoZR`HL6*&K7hioZqqbtaj8Q!+VAWmo&HJxdOTXp?<pN+NZG<FHfFTx&H+j7iCAeFGi6qnoyi!?&v59Qw+*ak|--5daa&7uq3l6*%nzhdpTv$*?T*HAYtv7>Isn@Ue?R<!JfTU&<Tl*?7eZ9IWwk;E+_m>vT*#x3Y25%_ENN?(cJ9=355WbK_$J;w(OWejHuD~2ehZ;66^(UsD>2u6((qbd`<LM{J{Vcp(!<d?CnMLOfXf}-V*=ybj7&92$hJO1^0^B>ge5-+#AYsfivXo=G0eQbV>mR*!6qj-!)?kS(g5~*3o;hgMg}UO{lxpRSfPHLA_hw{GsJgJ6hjwM<`JeU1#r+Uv8F%RQmN=J|&MSe=CK!J_6=51*!m$BYU{yD`ffRV6`7BXe_oV1Y3A|`s8#*{izts|OD2H8>jLFbGV(*ItMkxZPmF4Jrj0IL~0-(bUyvecS;}Ml%`_+)}x{(UJ8VImVu8!1;$siDPdj#_R>6N};joXgGvme%|b~F1rZ5Y86JqB*tGL2@aj1eL<l{$nAK^5}pEQ&b#3h4CZDE)?W@-`2WtKs<;nqaYBM$KJ~Oa7j~U!1rG(H@Z>!uWxAvDRS<Xk!h=R1RjpjO?njvBs81(N8|n<7;24B+2N*9!d=1&!BT^M~4NKEyI=%;Vh#tns-w*EHkx>RM+}xj)LYUH9|?XOnR?$DHM%P%PL})vYk1J_33R+5Z}TDOn9+;)BnoEM6pERMg^C*^$5lg-w#eY?+Q!)>&7Qhf!?VGA5m9kZ<#9A9F8vYQDYkq+=8Fd1NK1`D~`-gTK+*fV9{-ya-*!*i)IZnb(IN|8bz{WVyCp{S~_W#xdz4nJbFHcGeS5WQ_l;K3`{MJDb{SwnsTp!iL@t$$UTuy3eb|J7^u=eM<C2s2Et6EsFxadRu1g6j0DmoM(B9f7nyq2nIL6@IYR4bMb!#TnnmB3H=NyAsL^L)_U8N-v|_LgZL7Oxetr3XFQ}mQRDNc#WTwCuY0}fESd-*)9$U8Baqm!p`~i$89tT0%_=B4Ap2O;u*mvbC@_w$a?pr{KZgr!(geJP4=Ac@ndKSk~dds+WIQ?FEY*2;}B`L=Ov$vX|xcA>wEFp(A+-?lo!5+0U@LG53S4S=_*B4E7{AX5m`gH)@z?5Z_W4HE-3qK>zLrELTFqaLNP~f<dF3T&v;H?#htR^mAjmDWowU<}!-!648jF44L)M4o2!1EKJtbqj#cxv7Y@=E19ycVLy3#|nFP}QQBvSdn1TY*GhKTLU>={o(`KHuT%A5nA}PGveJ|Mx@WRyau<W$Z7))Py>|*Lb!QeVm*INLa|0BYY$h@Ocg$!KGV06-j}->4M{Ftd6T}p-@LzUR)lnX>5^g2Ku|L2b(SL$(7NkEb2|j-n&^ea&ON#nTLb;w__`OgSIqzZNo~X>lD75no2<~&z|$XYOWcoxlMqctWVwAjix@~@s9V5eu%^F3DV21q^CN+U(aV4+7pH;+1gR#&`9WYbr-Z?OPBUEz-bX8n~2lrH=5bHR$?!i8K?LdVE*v|BqASa19gcxN{A>D$s~#7vgh5wvFT>2@XW3)OGF}2<{ebFupxKKbj8O~S+y?ps?_ZO`EbB3Z1=JA+;%|r-4*C_G<1XhZtX{bOi38`LQ*=-Z%>r!1UYqyOu96<CB8k$^Lou9u$do@>CzkHB)fn>u~vFt=+<qmjsf@m(6vr!y5^f*!mNeY49@@3^xZntzjbyBTXnC)SjCkq)Dulr-N5tQK5@7abd@_$z;xA{M_$hA73&Zg-4Jx?@LvVW3wVv8>nxt1F~mH&da*`Rtfge8f%hlb-_bb$v}U0VQY&j800HzCxZ?o;J=BlLvBYQl0ssI200dcD""")

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
