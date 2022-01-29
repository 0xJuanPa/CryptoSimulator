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


ReduceInfo = namedtuple("ReduceInfo", ["prod_left", "prod_right", "prod_class", "prod_args"])


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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;6>#LA6)=I0S<esqFW;M_~>_3{1#)*;wRWU81kq-@&yH!*9Ms-5)kdx1D1&2`2UrzD~?7Chij>#@!8^2-1yLHzHBl9ldDLEh?uL{#U`;Ya*r+Zk^?3)AMB(DwC*LN;LaXg*oR+d{|1cy|6_{q^Na-395rx{mFUJnnu?6rltoRnSlWm{eKF`2;c=H{F(g$ta_THA58TWG-<C9=ReUGU8qq-;M>e$#x}Tr)A3s%fYK`a#j^9Vls8$XaJdF8z@=+5Ys?-yEnC9};Y|>5kSUhLMiId!Uz6%Qfcs&6eGUX(H!g*S-T7au45Bp`cj;^Bghi=~JM&JmLbnzde8R5;ymeL}h%HNS|%soyH+M#L7jQ)Sm+9mZJi+!^Qc`#7@#oY1iC!LUL;v}i(fRzul3VO%-S64LNUuX+TQ#n|&2T-tlXs*7uuB*u2WN`;><>IC}(L6xWaAJmS=XnM;|M1NLZ|ZT)@ihwcHoa2O@kyP%xyW5La;oIrLP4clpd?iwd6>;n%eT%2rtJeot0=R2Pa~|Zxqt03|1(x|wC%T>(ip6N6L3Bi*aN^OqsZ>3-`31u$^DMUlU-mT7N~f-RNr@bILIZOOa;o;6<~4;c-cI&)ZwEBdL2fCEmuve#}0Qy&x$g8Vm9r66MHs85(cme#M*TLdQ*v^O*QwMZAG;J&@hGKhvU0)OCl-eY4v0WjCyo@)tZRkzC1d|1Mw{+eCwdlxwhETd2>Bliy4O5S;6uM5IA{1nr?DQ7;%9CuSr=HD4SDO(8UyA;86VKQvml{-Y~F>DCt4N)>z^}$-e^*P$`&FYWkt{{chmV;Wc<4bcz<n*b}#MF87{locx!b5(hY)^6t53@M%0TcZ~2k^}L#Ae7w71;e)n$0$7nH(bxE4iKvn~<niBw-?Jax(K_5YH~1lZGxu&JSw`5-+4!t5EV2&eJ+G>)TN|+BTz!Y{(BGBAr_{~-<tArE$qS_1mvUZ`0-~)*K#$TdV&M?d#V(KC&{>dpw+JQMix+5AW};zCq_Gsl*3H@flaQ%ytJ7C6J&<kT>y}?eo72sYYOia2kwo_yw^9E%wg!E?9Xb3@0`$CEA1sxbJJ6>4_w1~LV)XFkx5hVq|4r+VbGf_e#Tj7U!{$)hg2h>7;<g8`v^mz-(qvdBe2gb*g7tS?P8oMTQq69v7UB?29>ZaiNt$KH87H)2viII!p>1lW)21L*K(@>Pf%(prCP&FJujV=0a5~&S;!V>iYPmVY1||FHva}0Nz%;57%n~@N0S*PO=F_Q`w%^DHNw)sb4`c6G=Hty@8~?CBEzG^mrHeU&EW)4_8MGNW^uOKj?64|PZ@vi;y~gR*YQBv0-wLU~>@OCc^g!l*(lkH)YS`>bk%p5vYMnt?z~Ifi2*n3o!(ujc<CN@c5UZ(xczi?sg0UJ>Gz3V<r^kw@_eW*x8Q0}q2o+(R-Ig)1k+}<mmPdXI%&_pLeb<8utp21OMg`IO<Nj!%)!Uj_X{qm=Lb4_6D`^c)4tQ<cz2)&&Tn=_TzLKp81_Q6HD%7&zXTUIKS)2D=4L$p`$-%MIYcEu^KuVTA^Gna1y%>0lleZhULR8?oG+r$!lWOTXFdsi=@|On?drPyYkQ#{VryexO(I#+nOEYbPWm=asZHA?5-&bg11ida6*VZg00%AQ%!aEbJds9Y?O&^ag`J?*Z=BNAqrYUW|`TpTQNZx@kJFmX@3>AW39f0z}JyLIdnc8$=7k@5sd7CXw^Jj%I28wgvjrvwS^sVytEIx!nUPY+;6Gdxl-vfb;Ct&wI`lLq|So}>-6Pv5*>;iiy)Q36S;#7AU5uRcysf9D}vl$c(&$(Sr$ns7?+xryBNe$Sk(SXe#B!N!JLA~=4m6j%c@y9ilpsa5fQz{f0sw`pIm0u>2ivN!w`XSip|C{^*r3M^UzzcqT@1Ka*>o%|adn%@QCQquR*=X`r5b`{E=Ng%Yj?8n5!3J~PN@+%tc~#MAhOzHVNdz$-K;voVp_76QYxTi6j~C&QFTkV^-I+2sSawVu59<8dj*qvN-X1q+%8`UJ_)8VUe7|Y-l5)qHO0_cPVM_XbmFLK6Paw+O!#?=my)ZY-SpWiiM7_45&Gb~WZ}mF?PY?@A@hH6vG8K^61S=K8iOzbeweh$%VG&ImJ;^QuFC9I97<5?^ySYLkXqk=dZoj?zm4f>~OZ*K6?EaErge~l{%XU4(4YYKc=!058)~+_UpY}8{fZ-#-qd#k8%92%(keIbHIGcSkE)hJsRA*+=D$J6VF{@nVd#-j66YbX2%Xzo-Ub9R*q2}J&@&0yfnNJ$dfo+{#CCvEQN%JeO`CBJ(hLlkz%vJUS$b8?hmA<6CH-IvNXh6|KQDWU=LZ~R}YUYSxYwB{?$r6)r79m;hbt|=AU#C9Yq?jzN;sm&2c6T}q128GL>K%H(srK>UIE^n7JqVQ`4Jdhj?Wj&2ab23*vP@wT`_D#=`B6E2xRIZe6<AfCGa}N)<hCDZ+M|f$$OQk~_^@(8ES+gvP-4ANlg{OW2Poy*62TCsj`{ovl#s4-iQBSv5Y&52OfwHbVgc5r5UWJeZb8YEb_FiXP9dWk6S+Z_4$SeP9(I|mJ9GC0`Z+_7IpI>ch-@0d)2YM*Ae&uP=EbT`kzjpJG61-bVGHWYpGFZp|4gF`*#iq1vXOLL2*knIMu*o4&qvLhMu6<D{Pcf<Bc_tza>%}#>(wYO*PcnDV1z3Jv=XiCf)}d8k-})pl3YQ<l{j&c{EgKj@2P!BG!#hGgC(-HgOeaOd)0oYu7GpES)}bY`6-xC93<yC5(JCB`n1oC5lJ><4Cemuf0i*&xo0UAZ&lQKI8tI0q@7kP(VhBNlmW>wh|U2L(fu<MdoCt6fB)Zs5DCswZMHS<A1X#e!);}*q)D6Wa=T#@d2xybcRXBSukcMiKlK*1x8u{C5wOEh9m&=|Uu<qgeq)o2ZR`n=`VKrx{p_r)iMH5W8~99`|9X#XycJ)gA>aT27tUSuHKRt_00Fxa=8FLUO(++xvBYQl0ssI200dcD""")

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
                    popped_sym = []
                    for symbol in list(reversed(content.prod_right)):
                        popped_symbol = symbol_stack.pop()
                        state_stack.pop()
                        curr_state = state_stack[-1]
                        assert symbol == popped_symbol  # this is useless because stack is always viable prefix but..
                        popped_sym.append(popped_symbol)

                    popped_sym = list(reversed(popped_sym))
                    if content.prod_class and len(content.prod_args):
                        args = list(map(lambda i: popped_sym[i].content, content.prod_args))
                        instance = self.ast_types.__dict__[content.prod_class](*args)
                    else:
                        instance = popped_sym[0].content
                    goto = self.table.goto((curr_state, content.prod_left))
                    state_stack.append(goto)
                    new_sym = ParserSymbol(content.prod_left, instance)
                    symbol_stack.append(new_sym)
                case self.table.Action.ACCEPT:
                    last_symbol = symbol_stack.pop()
                    assert last_symbol == self.table.initial_symbol  # just for fun
                    return last_symbol.content
                case _:
                    raise ValueError(f"Invalid Syntax Unexpected Token {curr_tok}")
