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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;CK-Xyj=i50S;}NW@Gy2+V)$EnmbN##S|M*Np=Hm6BK6b@u$<aeBwG65W^mCYAVKyf7{zhy9w>g<38oqD)IfRX2{jQ8l-%}n3t%f8N5?E37z3I-W5j(f3Fdo0&xaW&ORONNfwM7VpKXC>#DX7Zkp285%gnD>T}m>&Qh_I1Gcs+lN$sQ<|^xQ=)AyI9;1DdHU<!1bMb4j3ALgpUBTIudMs^8<V6k;+irr18H^6$wC(!hEk}5>7cmO64@5>k(DZm?V&wo#YgkvGVyc2tg~NC#BaAed#V7!S@_GfuDBg6DuX^5ls8DMh)`b5vp_!!48faG!40e(<B1<wE*_hQb=1~&fGC=ju={`adg<`{Jf}y(!gDbHQsaTO0>!2{HAPj$rh0${lF`o}kqr(8HdkY`T)FFr-*>}K-Ec^E_k5|vzG{HPQ%wCySP{!!>M4~eB?&dOF&b!C|I_;ofpOH=pyDhM8oCZ0Ogie2Eit6^AD~ys3MMozwTt`*B?Rs<qG&zeA3I&?k<(|{SfrO0mYx9D2e%aPW77n$JAJ?WW_d2m7QE^t#npx;o9*~Z>M7Q`CxQ-7g%U~p$H&nMuREJ#qQrWo8;dkHH!Y+=O;1r#ix9#n1&``3hx&#<K9{Tyu{?~OX!$ht49A^#nSsfAwby(yX1?)lgF369FC_2T*%L%Pl(vQa~M`u(@t|Rl!#Lk+oj^b397ro>I8XPTjP=jgSl}qWHsUfg0hezM_1ec~+B;<^lnrjy$Kk3sI{CRB0+Vq7HxqA|jGhD!Qw{R<gp@q*RgXsAq%p#-6uhwzfJj$3)Gvm9eBH|~$+46!Y!05H^-uvp!DWgs<Id<>9AzwZhL|iv=GAM;WDA1bQccSy)(l~t<M(|mPzQqq%UDlyo<+wD}P|Nq3VH*CKoC2t8Jf-3DGIJ{L3>+<jv8MY5=a0=;L+FlM)_MT07X1&+*Mmh3?eYQ}GO+dCBKT|uY+@`U645I&Yl<U!x&>`=rDCqcahmQQJ!lHL;^0kH(Luq;rJ0I7*G3j#LiY`nIG*yb6J0MltSL4nxJe6obn2V~LjwUn<D%T^Kw9#H<`opwPXU;%Zpv&&$jQA(%0QBbb6=$j799>Pr~YP6!m;t{_B;$d9s}OVW+Xa#w5<{9+j6%hTG=&;e(cXZZ}DDxE2hgmiYt&7iNaW~u)tz3gDjOO7pkB{mGDn^1rD=|y5yRMGLXy<OA?*pyR=Y36)&eqtD6u%6+U?(K)^m&_2nAwu5ITG_rs#(2F$CR_<3BFAU^&QJ0y3e@b%Z^Sx)27I<+aVz~QEJ(I_Sd3D{rGxX{{>uE_J^T|DT-!nBe!P!4dsnDun2s#Z_V05VQMRLvKau=)0r?Ucm=S~H5S+iw9-H?R~h3vbGCvrS8al&FR&Ew^6pmTJ0TqaV0X`^9n`skgz>a@F%!+q}G@p^%H3Y8XF&E9T<UKQz!ocD=iq7y4rn>eC(9%R+GI(lc4MO5?f*4R#ghdN^2&O2$LXFI{vU{&Qm%K|VvQus!Wxd_4dQ9W_MXmq(Vbhvf+Wk9k32klN(J8rNGi_OUUJ^BFd(%8~rfQ+>6VT!}7NM;LY^4COhRN^N8V0exqk<bS=#U_l}lP)k5rKEgE&r3J~ZpgKKMG9my{G%i{!^I0{;%OHV4Zr`0&g$B5)D)mrB4{idDJYDf?4mV5FWheSzE^ToMB$Q_O7=iJMNJL*-b;?oYrus$T1n%eI0{};pdMf?6adb?kgqgA?7YUoNx5e$M8ZHK{4Oe0iC*n7>+F8l+VGpNAu)}!=s`oC$-5-DcS_D|%l*b<T(%7of;Evv7CtK}>F|~OW=m3WPdZxRQyNkV^(<et9(^_zhLcG>(*to}t+@T4#tQ_XX^S&?Q2e|Ro6Fp}0W`Gs*hc@VgOJzhu-tIU<rgZ^WzdJBp0f4A*F}*Sqc`rO=P#e;&R(UF{)9GweF!C3gs{w>T!p5Oam1v_d+M=M3lHG7%ZM2_EF2KJ^bGjQ9{1|dB&>M{VjP6MyINa?giB|%y&?4h1$bmULAUtc?*~ySI_bFor@Vo14a=(vDFikP^e2sLT$rwilt;@~^?iWHze;WPxOIMy4bUS59tvr_(L+_b9tCZ%v{me$-8Q8Y)P=}+fjCeKs2{r9ks${S4YUX+X-*TBavThd`Pe3;5GPNjw!M>AdqtM+!z5V;VB<p_l7Im3^;<0M|&sS_>jbK{rY`stZQ$6QJjLR#jbuXXc+&(IXRzjaPhxqV}r3iJ`D=8p*Q$`QtSAPFP=jHJGTP=yF4T{NcnR{7^3JeSKIczc0SgGG=1#?BSR@{QFp@&YY56QX)sQZgF<~_6+ZZ@=PW%J;>`{Wx;F}8RG98L3maYl2M;Rx+yu``-c;T|onAav_1Dn4}4flcj{aK4#m8o<T4`1$%O@<#ngqRdGfEe3t+&IGa|w?GLtc``_We#b`Wj%6;Y*KsY<5nys`gqaDpYZcCbr4KR;S{w81TbrgomMlp5Bfr9f;QSjeiyo$`23VPmr(xhQ3bM=8n2covrzUYw@WMyFgN<=b`-+AMX7ilnY$)}-B1`>wN$Ckp!Mq72u3Utp`@gOvMfk1meQq%SRN1*s)d6aj-x~fRAiUtzgDQAc`qy;fTTJi+SIfZNopoxiIS+0H8t$*{2?$L4Wia%FW$)fX%gR?IKHCqCobsmqC7H|yt4bTeuu4#viZ(e0cl)%Db~%gd?G&@7=uXy!0U=qbZa2%X<KQF$F8m|FRCIg;2?A<{o<^n-tb-GqfwVayJD+q#>T>Y8osT$g^2J`@iKnoCslwD(z7bd@Qch2JRI=w|%bQ~7N-J=dqJo^@Z5W8>vlNE3D2fK)5p6bqjTb%TQu)Djp{f}Y_?DSBL}~dzYxy9gaoMkno=qy;7vE1I07u!O2n#q94}ni!HEXOkbyjEP@)*8j6uPz`=&_-dovbi`H@v<+phz<ZD7C~0@p4wJ1;&x6TG=|7vlA(>KYTd`r(lMwA7!D+O}nI@irjx()EAwg<dIf3{)zh}W(-p2BBW_N89oYUbx%Sf+VqtAO(u`W55u35tdBagD-xFtge>oNCa4~XFk6YG?i0&0AHVFE0B28LjwwYW_`)@IpRqM=mmSEL0l%jJyUU%Z(j{$d2vFBCu0K--yE-E&PhEpED)TH+L^UD&d1}lc-vv<rK2#OWB5*U>5EJy~c5rtJuzKXz#drP!i}z<7F5(Hj)3TGySfW@ZDw!;x<g?;-^7f<w?R78g>H4wyI)HaBSx0?A47evoy&(asi`lU`zoe>`t<qL{V-B5tLOUz8%C~7qgq5D;91cvUAOCG0l419!Dg8P)2kkmg=WGwl8LL$7vd%tvLh|GOS#{7TR{`V*k|uK>wrTzyfPIdMU>vc@Ag9PskahRJOalGy{s6bA*#VK~B4iJ8?5{Hw?6GlCPAkAUf?AUxxZZ9^*d)0zt3!FRcZZ4CpP};wpKJc1v%4oFT}i>t1vk?{JnR=w1eSzh;9R=<kpB19opAWs{zSF@un{mlsNx*g(B{Gu46FT-uf!hK8zc#+YQeR)MXw5)&_|vV?snC04l?HC*Wmu70wQ}zmfzHY_e;8dBQMMw5h1jMkH|pxGzWm6zHwqX$@P6;7&5gzn+49biTgQ`z--LQk)}Yu)?S39+e|81pV(9F2d)mK*Us-Bl&R1{3rRT=;|+64)^vMIlY=pvA|XUD9G`KrWjoamB>keI^HewKy^bniG0{6cpe`JL-m&ixYpM*z;(e$SYn!j}LjA<c+sCJMQeD+LgB9C5*oniHIqn)|&--CF>=$WFVt?arSzYt$q=8ZWqmsMSMcteT7ERTbg@`|V+Xj6vNKGu_zdg;9PejySp9$j{i3K<;uhgvwuIx?wA{@Z0`XquQZ$84Kh+n6%pfY!^(n(lfIQ{aL%Zqvs4+_qMf%-2^Gs7(8(UTYSffl)U<pI%HY`a2<9blv8HA`2QW-@0sueeEbx}}Bi;GhwP?vjAgvCoIWpLEQxQGv44t#xY*3|*x&2;d85USjWNa;{;BIZ6rvN;lt1oJn#|6B{QlxFYD!jVoXMW_O$nZiBHdBwdJ_&HneseX+wSPMl2ETJ3;}o~;AhnJ{Vkb`~CT$%shigOXpsHwt-!lJ~Rf>D%gMX{I|~YMA1j_aOoo1(_b)LY{qqw^6|py;OA@7Me!@)qj4ysN^iN00Gz;lJEfl($rq-vBYQl0ssI200dcD""")

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
                        last_symbol.dbg_syms.view()
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
