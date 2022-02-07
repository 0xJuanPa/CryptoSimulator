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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;BzGl;9USf0S<2oMlgnZTgI#|df4X&3V_#AN;P+T|4&MHaPom%@o+XjxD&d>3c0t&<MG<|1{6-ACksoYVG=B}@OhrVxT7XdksMd&*A!**BzMK)`A7)sMLyNwBBYC&@R9@j@ZZ4CS&6Dnmb`Z$?n$}YVp|5kYnuMJaSyQkbW7Gp@$nm2NJ>8i@xWHVfkhX+0*PLO=VMB#hGSyI>_baEpsn_}1F?L>T}dF4qJ@kiNVt+QHvgpxsh=+YSJz<()By|BIbST+(tp@D6SaU0<3-vb#XoCsi`{{)V@Ip)MO(n<KyFIaK_8Zxwci<^+4N-)s{{GiLLyuIH69ZAm)TVHzA^(3O4WwSi$~|T{>&$`x4s7a84Okia-p`Qhlq&HFPrWo2o`K^%ttjxU{TL@L0i4?&vLIePUG%=cDEiJ)3FC}Y(Q%6n>V>smQiB|HLPz(_o=oG#9$p`sI9N3q32>4#fQU30mv58d!q}EwL`^FHgy)@>oRGnIk8u@2sEXI90f;aH5f^;RK(IQF(5q4X%qOPP%H&QYQ0OrTNIq^s<iNtJ-u?Y>~oS93uQdE(qPthszJu_SDSt5+|2pQSDAGN#(Q)XXA_mH-*(b;@OUucpD)*IYWf&2pYtVHV<+uR*H|MLz{)G9Tb4lIRQW?3C@FQMa?{JoT`QZ0i0Bs#{Zt#$<?uMyZvQu-5fx#<4f45SXbeo{Hik8`W(`AuP70P19I87|a2>=rxioBo-r2Qptn>SX5K1a7=%C^I$sM0X$eRMF2APJG1$zKk!C)>K1{Np|Ur5Jdov#7o@84A&9~aC@5t^S~w8Rzr{+JIq{AIInMMXG)T6Fj)e?fI?=qwt?;8Ktr=b1nwz;}wKoxQN<@H}!-6pR7(%n1|b`R()nG@dka-(4|bYWv~g{Psj+&d;%BJdu!((V&AP6+;Db8}_SNB92K6`+C*sSYPk7VHe*qQBaoqgG|$lZv1BU#IoqrGu+DY3yo0odc9#243m=uce=?C^H42_-#cUc_%GN*)(C?DP=J90AB#Xf{*ZcU5b5t^k_m&bSM8t1RB21aJ`$;_t*h{HjU4lN#?(goyxR6E6C<S%!LJf_1G7epP)=wVxyIB_a9y-!mAnY-#*K`f;*+}feAQ|K@5&|yXwH8rI0HYZhvtTr@(v4MH=F$BAK5?lrMr&)Fr1+I=kZ&C!|J18(PTBOS2n9T$jg02K{y|h#OWua#K(0JP0Y^;;vjQlp_5T4r5dW`wXHqiGp^v?+G3c|70;`4yg~TpbZd5rfRP>oXg~>B?f$2sd1WgPPlHB>78SOl!>v45ZP}!*W2<6x>X>hfrJkur)hE;1XpH+P{-w3cX({rChd^#KI-oPNx0$mntt~!UmKgi%ZsfDjyYM_VV}8!k<u|u5+WDTjQBOiJKCw!2)TN6VLjH(nhr3K?57SC;*S?@;{rZM-qAjtJ#7j3<B)QjNKu=izP`qVyW3-K(_3Vx_p)|h7W^CHY$V}3mmTAO&WbXpKD9kP(_NC4LNI6}Dx@YmzOCzQ0uHqXIt?Krv>cHzBgc(?n8{oA)WhW(&*2;p2c?YWy<|Qx?$X~!*X=4(j9b&9N#CNsITOP-T6S8UScG`Fgq%y@*X%(UC^KYE#eDZ&!xmI@Gn!nY%>GLj;C^RJF%3YUWj73ujVZ%WwF#+ru*I$cyuN{RwG<`jh>A3c_yA3z&9!A8~lei0LEB&b!5cru@<q;d2q3norRWiWqKv))si|RO-4&_RWT?M66MeM-_;D88gB!LnQJK$OC*kl7hmEnjjlm9A2n=+KFt-T9IMyBA~DSu4IV!MLK9XLk7gQE{s`tX{>{h>vasi8Yw(Fsh`(R*9G)8@!fZ=xjj6M{VsSI3nRMR`?R`nV?RtbVzw(8riT5jfac?Z_nx5{t<)B-i<BhV?i-4m`j(m<y&+r?%ID!6$9OhX$nyPZWRv8<?CMHuxoNWppYfAmVf>8_oeZ10`U_4LX8m3H|i;SP!Ky-_iiIS%mrn1if;CU>x$?x{*K4Z3)#2>;2$F_x%CWp=c9jj4d0be|!jS1c<t7m!3u*F|`*QD^0hYVpgR7nBp7F%z*UEfY5D1{g;25#d41lN;I!Cq19@v0ve^`6^u>Dw)BRRLMoWkQ9COBJ{aCxOn;*`E#=!0mrAR*dRU__Vunt#I?)9Mgm69VzgR1-=5WwX&AdqZkk$dnNF}Usi5b<%y0Y3L$eg@5(iTE*hMJcF6GRk*Q7`E%f`ZDpC{H$St!y$U5@tGsKy+KslbcO)Z)UeH&SW|XEV<gi=Fs1Bwm#)G=*gWTI7uG&?V39+dqF0N?7ExN0W6}S3EA$LkXly~e`t$-+__bUR|1`ClkKygsnp5+JK#;A8mlJY9M;auNPN4Na6_3!{*V;ls7@iBK|bC_MC;`ZgM}8y{`~e7ZlMfNLUfhC{4B_;S=)j|FcqVny~l^s#aVje?T{mn@F)Va{lwcK*1l<W9iTBBmH_n?Gv2WkSq=@%s}??uWSuC$B5$@5A8URkfF9EpfZ1AKQ){X6k!EDijST+*gZf*>GvRa=uz#+=z-Rxtx_>L-qtr5qPu6N4S#;(~9hhftCQqIZIqn!%Uqzc$<c!MCz6Ob$7~S4j{;_Ihj9LwKZ3LmdF9$O0CwHwd2tRVbc)xVeYdPy|QE0!K$6ndYT^jt2Fct|E;lsPV2I78<(bmYFyra7i1e0N}2Y0|xZ7z&TRCFqunvznBxOb^kg2^%DOf-1<V|h>ac~dvAeUGbBhMdD;y9xTOJ5CNi{dq$_dF2X1XOJ};1J4a%64}*|bmmwt9X_@8wzOm1D2H=O{QYw!m)fx9D%{JnPpxv_)YeVs_=FwatmD=m>=4arkR1N9Ue@Y&=`Y)*aF2I*p`63t7UsbEKfkrKY+woD^V)7#uplw7b5_t?rKQ8V4zl0W)7^AGEZDp0D=+?p7^qR^n}`q0oL{Wc%89m!F+OSBdkGch-$kNhD@AqdUHHTbrf#c>=5T?j?ni{Zvp*~(%?DNa(5@Z|{B3GeS&ROooL^n7g-st246pb_^XDMA!O;K1!ehYa3BZ9t3;jQaE&DRSpSQPD!f-xJU`X3je<T-g3W;%Py~TT58VXhXlt+x(&B@H}`AvauK|x<&eI9m%T52*Fh)Ce_?`qQ$Bu_`^c;44DuuX-|R1*}4!YP}~5WOJG?cVr)z3aqT#%(YY+`x-8T_F1Y_+4+TJfjg(Z*0iW{|EAl9-#6!yS$;*nCP@G;s+Tylv2BwZyg!V@|F>FF%2Oit6K>+{ln=#zO?qWc$$Ga(=N%kp<O>l#?r@7XfvRSAi-``bpD*G-9sKDRzKIln8&HQ94C4Yz;-Pwdj|0Zv{K+d&!OBr6l3_++38j1h<sTxCO>6+N%^XyjZ|NZ2RNeb9og`pA1LOj?ONJLq+>)O|91L3viz}E#zFv%dzT55P&L4RzEY?G%v_;o`f#u+TVM3G>Wy?l%qU0c*n6*9KMz>ROVAy>oYAT)l{W#gL(g{ND7GLQh=gD6kEGMZGx4Qm+WKh7uu&f0zmi}WEE+Z2Ix~TC9|2A*i*ygcz3&8)*G7^GihTiOl@+lmd%-X_oX$|OcltJLf-66@3{R<^iW!2<CPHDoRN4hoFDrPRW{ZFA_o>_2VbnKs1)<m>TKLHy6piRFF3jKTCe$l2X`UdM!ZG_`z5{JvkFl@V<7gK8Qv%9y66~Ys&tr@cQ(u&Kqdwbm1fkmdsX!gXYH`UX+L|NSCSbuHv<HWwbbIpfiDDzG8sxATBm<5y5*DVzv{9~pVbG=tp|O`((pwT}h2fYlZqC5=ovqVDF(j}rC-)tRIHO8l*evlJ%#Wg&PCCE8y-@HT+ofcBhnyOTo1><=l{YvWI9by5!Y=#P&OyT7->Fig9{SAyvVCf`7WWIB00I0Lrse?vr=78{vBYQl0ssI200dcD""")

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
