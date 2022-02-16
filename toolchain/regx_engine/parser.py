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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;BxE>xLp810S<g1WbY#o;li?xBVj951Cv$7#Xwol-75cUaA1~Ip#M4Jz#<n5x~6yksWV#T<Ono*lf)Ut0h=p+#@LGKM9#mg-DN0U*&xeckx*56FWpPi4ZaM>5ZfhXmYKKd3mbd)D)(coy=uP$nY!;jc-$y8V?Z@-uqEruYaGm~gG*!y^mEAx0o*`r`hXV04g^RlLni;8Dwvq@h4me$^7SDOwo|-z+F8{GVl+QR`jVoyE;8ZZVg|T}%XL&hFgo@V09tzC;Jxt^>+xETDZ^`HK7St^j$bs|+<uxbpvRl#5%rqe+3B^utgyiGI4U{?i<@$?CzLa0_zxfg(mKyaa%Ng`D&R~!{_s=2g-<Lik2+{(7rd0{yHwgCfn{C+l$>U}cRi&*YK245g-{z3&)9KJI0DB3Y*04&M6j&%NsVw%6-Pj&A!@7tpYWhOs2bTIbn=6CKpvzb%E6_}`7UA^J=hE$3b?3a&59kS&1WJc`cs)3EDVI5&BYOSM>9|Mx&xy*vChao{df+>wY`Kd_Yw2jOcq5XGkhZQWZQt}zRQpn8?&Ce_jj6@!p0<s40GRWr>M-JfLDBe{@cC?l9L-J-HMStA`w=o%RLubcHjRMxMe^jvMKoDRDmImTeUC*SpP*^>l~6olr0u>v}@_=^}UDm(!Jy7@$;fOiRZ)@EeYpmZOoFU(PZjQWrkvRP0XgNkdxtafSw|(kIh5rWL<@F#vrs^C=6-OPGC)Ya?REoGZ!N^o$6vWz{$bRBv)}rz3b3Ja~{NjqQBn|o5P!^AhyhNr32y##q>1bD4lmNj&s7S{CZG1QJ3qe$uT%W$Vot{xrr%7x3{q^bj@Ac0Zyq<B9<}|s<<I%GNS$iu$?WJ`_avA8RKNHxi{@OnBglth@A0j=HDm#b`*j}3oEV2T1Ih39jmKo>ef<iT^qe{a)Vg4)6Yn^LjpN5nXNC*z^81A7m<8{n`}~1l(U1Pi+f4xMM<f@BeQ;~C^$$9$navqf&$~|#s{@S-<mU})bck5@ryo{W1`I%l4*t0@P-11N}|wN{3)O*)wGvG*v*Y{EZmdJ_UsB>v2^6@`(u|z_R-7S-&hpt8)sj)|4-Y{XrDftVPz~R+w$`=0V}x)&-V4e&v~4qb5#7V|NGkl<(YDR=ywOKGy%P=E%j$$4yy$GXIElQ6pCREsTW~i+B_{4>JZ7PCOdV*(gPn&ei3X|mGcm#9Cr1MF5e7`j@+R&tyhlRD(rZV9#H+&(3$Gy$64VqzF&hblmVULc0LUD5vGcGMJ}Ndhrr;>{&fTNJ#<+^W)1sEPJ&y?qm}9E?&V0dXs*pneG6$yrgTAW3$h{2#)|8+#tj@fg21<lGsn3UC-jhfXt*i2c%r1T2q8l2;g#r}FA~IeYQKPGYY(K{+iD!T&X1Tz+A&0#IVwOxrssa7*A7-sg;TKt+E~v03o>OWKJQ~pisBYz9Bxz9ec(Ps)rO@C%|}S*ydsSeZAwil=r%k;dvxzWD<?JqV=^CYyI^>1>=5p&Ze2hIZzX2zh#^xRx-ayCsKSo@kB2$fT}$J=d*)dHi!e5ltwd3VZ}k_v=gLO?;f`G*<2*@o5raFdFQG+mjAsQ1pH}F`0CxUO7wjyEP}TUWQNsFNFK6P;y>l2$sU!tx;6yioiW9jq7`wgLvYJ;!=Zx2}MtfT?D*3Jaxt0;t;g6iz`A6@%f5Fz#b+DCu*TqTI*|F`~qHOmEr_$v#%Md_YmI~Z7>`ZMGi6U|>$FR2@RX$7MEsJOyCd<zK=v^`Z;~pp3vt#N<QZ3UV{v9^!9FxBRvh%;G(Rut7`7{G%PnxnCp(mopE1X%CptON9v~M973t+1J*%hV%Q$c8~#tfIlN+eI>M_94BvZyUnqfHB37&lkEVBTi>bxqHGSm0boE0PWI$|Ka6L#Y`^!>wf8%+s^)y7X-c<XnZl6NVY6OX#U1Defsrd>nnZi$W)u?QgK)1@8INJM50;wzjS74%5#ntU8@q-1sO3^YfBJqI<b94vVG3b0|h`^~Ix|(X3_r9+P<)xxCeX+zRP2<t!*$Wx!awhu3hRZ0HjT=ejd_TB!(b@B1s$*Fg0;&}kGDscsdC^x9_;#@E&l7x0t{@`<Wn3`chq328_l8i(oE0jANZ_=e$JFIlHZzg*L^sFy=&u%jYzPP?LT*vRK#DWaOOE~m3G(IrH3lO9cHgqz)9#6~mT<3?mffiLjh9+w;TdtqNn0u1KaPoTnsh6tcxi+FArYr1wj(52I%btTjHw{{`=n{!bcl*+IF>sxGvQAAP&4`vpl7;M^opwPi{0@2CF%h`I7GH6KCV*X;LYfRiB0J1}bTzwxxGR=&}P}z!TFz}D{3=6o<KgQW)VC0*vUlQIi%owyrPQ3m~pzrs^YOzpRWeG@H81#lwpa&=B+#Uh{BW{4=hF4t#CI*gadwF>^k9|Goe?s+={p>>wQ#7d}j?{42Csu5gTfJ@<u{Pr$c<$q&N+0H|x>fCZ0<<m3PLzEzKENE)FGu-`D>`J3#cG!LyZ9hsP1s<_g&C?1pGkjpK`ZW4m5e#cary@dnD0%asAc-C91iCfZu0{4)wO4qlPWU~90uO-K|4L(%Yz&SJ~kj$Pq$*gE2E<=aW~p+=L@adjo2<VCY~_lk*4u@BBPAsen~693gY#>zvGl@9kVj+P;&bgOOcxSKha&(wt^0^jZ+4kYd~NV9*Hk7Q9UwgK{$K`<5qd*1uyFG22LKS6L*kQhs`Vkp`a2Yl?x$t=^D1CN4e<L`bE9Jqkp;7RDVBK2KOk!(iPJ|im+*MMUrMV#m0hN_y0;B`wlkrs*@&V4LtSWDaoNIMh`{%02VxjOK+Uyc2kzGSlu1s?f2T>waoG!L1%^u)x!lf_IeRYp5Zj=^jB-Cepuv=`_4zH-AC6r$fxB*dQrqvB(6<<H+(;#Wh1>lmu7B$OQ}2@4qhsCj7@TnrrEUo*jKFmrlVx)#FMId9TxRSX~WyhY{{3wD-_Bh7@SFRL(R1=i-1C-2O|yM*(nSh!<ZXhDaaNwM{?L#O#tBJj#P>vcwwi`9(5T8HL;U*qdduHV!}_$`U|eVK#n<a{?oi97jwlTx<esgE?*US43!742n4iID4}8WV|c^L+eg0D5q^e;;khl<w`fTBa@c640L_D0!k<g<JY^(iOV)OdJ~E+c$Xxb3dBMo%6K8h`9^M94UtrB}jb(o=-4l)FM)_>Vi{;FBUHO>v{8;XLG_`bE<AUpR>gEfd7{;=PUIBe%@PD}8706#y&=F;7IQ{iDSHKYZ%^24?!+oOp7NB);F(5dkqv-ZCL2<>e2n~6Y>$SD`Q!L4|=ZB=_B0Db5m_Rw(tEfID=JtfG4MB_tyiGUNp>57&?K2bW(XnU%N&G!SgVG1}!?c{PyQyw5Z1rBU&$3`Q1(5K&bxJZ0=fV);raFPF13qSNL(;_()x$56#q~MX-tpqx!VfN*9RhmiD)TCybQryb*2j`;8~Dxu6l(nE&i>={FzXMxeU8>%SLhyXw>Q?oS-;vnHYirc&d|~Br7(zZ`=<=d1t9gcd-FaLom%l6-qmTOvbu;)vPmeYNRQ3!bgu*s<S>4tBZQVn(3GCoksY{)IgG4WrP=P>0@l<O8S_7dDKwiXyL9F=V32Qo-zo0I05zDV^WYEvpRZjVJ&>W{ffndQ8+r%jR9wwaN(J8X+PRx(vM_P@XiUh-b4u};aLCy(mmDXHDbb?%Q?8hdJ|t%Pc>n0F^0_{1l{s5<J&DAxeS2|$L^o-dSf}AeL9Jkix4^n%<Orh)gf*w4_cYD9*dNRv=H`D8tTyiC$Xz0&(vnvij=hyT+^*v8L7^$IP;L6;VAGP1ksSa4-6X~kcN+_|00Gn&?d1UgnR^`yvBYQl0ssI200dcD""")

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
