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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;Y<=BBwYYN0S;|f@Xd>FE6RpTFOD`a4BnrU1BpLW7S3^L$i|{j%98m*9{jxrc&nnu<MAf8$y6)i$&5e)tpac%--fa%UC7ETjBMeP<di=3`@Xe8<8X5b15#)0%=3=jXP7dwpUgh!tT5FPN(7HP5l>N}1Uk@b9P0%-OGr`N-YP35q3Vccl`Cp_NLjvOyj%~Aa*Koz0a)DAX6IgqGlhp3CchSDtkcw;))X&XahC_0_479=@h{3vo^bozJSB|L7%~H^p~6kQEv!qx3=Eagw6{&0gG`g|D*IoA7NZ6aVEHq&R;9iL2C}|`%TTG#U6$LP*{l?Bk`5O4C<fapU7%A$g<pM?BZXB|41#YKmO;_dyRCo%fOb@EFda`4Ms3G_XaBw3%gos+IK=44Y}Tk0Y~ff7zb?m=QLd+Xl)r@o#^C38Q|tf6-d&9QzHa|2E~x?<bIB+!?TXs{)BJ1qo}*5E$UbOtu``0&@4nBeF0AeYOL<`%sd`u!odP{8|AZ#(p0KDaksFoo$aMId;Y#Y%d?ehgV)W+O4*@<yY?L5ujt_8X#S)vUvrK4(#4l-WTb%bB{8}gnH;GQSUQ-LBznEJ@@WK2a1189>&W`H&DfgjszF!>oYe8N?KrMO3+P$bkY<LDJP?wV5o;BPEKEFCoNpjlaGLgl%bLB3iGAf`kTz^9lG<G7KT?N@!_($)rE=ba>o61AHJS#|@55S8AM((+4)XVjq`!nfb3#!=BgR{F|b{AeF6&!3%|MqpPC}&yQ<>o$X!`W-A^p_|C3hdtpUFk&<j#-KSB4v5ER^1IOiBwI$Yl<%jUtiu;1h0ijmc+~9W&S>7B5t~mUwZfpbbrk^&99m%qIit+20Guy@CGXNuJk@RistVY*;@#I5Id!Q$E`|qCXI#F*_sZQU^8EV?g|D5NMnx&d9FC*Z!CpmZG2HY;K+-o_4q1b_*7@HenWNvjH%B!10`$z^Y2aeY1_~;j#jtBHAwjHQGx@VT14O$`s_`cZaYZZd3BP<X5_41%~qPqP`M|;nT9#laDKDM2umlq&Ra!k7@P+)_pJVF^kwy-Z6!<*9430%i|;+g4KGhjt`$;l0mrmDweg=D;K3#5NO((#mOy}Y<!xAVjGp6$y}LCZGaJ0Fn2px*?Rs09U}T9wv$aLht6nh;geJtXY%o_<6?VnHxoL89{g;zlJLDr{Y+oV}6yY$R8}?bd{dJ5in;B*r(7J$s|8;?twYU-$2`(_5%!^&xAiG;duI1<A#Wa3M_Q${P_I1l1EU=U7efd#x&|QOQ>MC<@^<tAa060cFK+{AqwKIWDzfRp=GK)02US>E;J=akd711Uay9+z9iol?Sln}k0KK<AZSiQg02do37%_#nR^)TIBjA?wF*fd2v31fpUz%9nD#CB20{A=*6*tVYrAmxjaCs=sdLJ&|IybjCI3=?SrxDO3Qp*fna`&+sG@soerX9dGp?q9i#a!DeYSqwyG0)SLvkAiJ{r}8`BF<)PlCo|nfm6uox;K%}_4?k~oFUDFKmtaXwwq(8|9<y+_b|@CTykY!cDhnfSc<7gT5A#lDYC4v|pmaZcMB?SpyWC@L*zHr$ft>Vm3i;z{CjbVcj|}0I2OcvD_Bwp+x)#Q*Aa&O<q$OabIqY6+a|laOar`n3<wiL(NK@w#pv2lD_F6gTi`Tw1AD9-b_Is`CL)YwckkDs|5<5bXrg$@!=c&+$KN?rgpkK~aF&^JBUk__SY{;Z4a>os?H3V0u$mGE#Y-kk=5Q`lTeh)_+gu`kR8u5@MF3pe-F_=FZopu#DJ~F55ct(1aocON^XQ9#s5Yv=017ZgVRN41Ywonl0IfIOk;5>X&5>0GUK$W#PKh<t*n>LVspw)#94z=uu2jO=Z4;R1p@*r+`ajcuwDoomKYlA@;gmJt$(Si#KIHq0Og0RBr4W#eB&5k~R`SF5S?WbZyN-`6ns3NW={aRi|dUqcPQ(62eiWD}C`w)fpp|ri=70w6Vn%>A#DceZkVcN=lyVK-`oe}ehsnS7?R;K>gBNou@p}3VWKIQxd?`GGj#(1HbfE_tpCP^rvJcs61mL}-PJ3SL!cMSGSV6?6rMY*)@W#gp$b@hA>B$cZ^oj^A_2sbae@e5#pmy5Z&L#6LWc^#nMzC~}*y`W*<0Qys?>DX!WD*}ax(lKx5ERc`}2$g>#DLfd0N8VBe^HfyEqcjq=z-|>Mv$@KZW7bdPf`CChU&I~8A#&@k=!0AK)(zpJX7*7^98IYP^4+55u>4yC|Fd`Un>9g?QAAc013L1$yH%`eg%esRg$C?(?Q96<7*`^{XY$7H8ByN>YOIfl3}`qK9KcjE9U+h9r+ESh2cSGWcnFa|`sr5wj3LUF9?j5X;Sx6t{&_)%ke}Ib3qgOtuWpRT^~U+;;qGLNZDq{|4OM1EVCzac2LMSShxv734m1+s;{)5Fh48rT(iN6Qm{HlGhC*t0%%|6i5a`b|%fCU45Q==1cnsch%)VGriX^?Oi^iAu@A|~iik1Hn%h-(N7m$P0_Vlapc*>yf-z#$Ggf~2TQ=kj4)fEnUWa;~SsFGyYHffA-gr%#|*uLJ*PwH$5+nLe5TX~0ciElS!=p_YyK)Mfr20D!lxeptA=_>v0x*kJLdTy<Q5e3LY*{5_sHHaKAE>!m@|KX^m3e4qEJ8RS^FBXmBZ{vv7sm&I@?1~`09HCStVUX@cATP|aYb>(tgFm;rOB4o+epzi@j%)J}p8?`cKyC&|Bzy%lA16%fqC*a2dC_bbM2_<(8U>I(Nb!15m=6Rxm2}OCRON6}Dy-7g;ne+Voi!Uz_>{E2r&06j4#}W`DkOI#@au*A?V(f9>P$ns_0n1E6_kv-OJP}4c-Tb;MAbY3dJ0V_tad!2Zzrfe`qofT`ZJV+l$RT;ef9y+_@{48LL%dM(t<FQx)lZv2ckerZo8q-6jzm4k#^`{<7iEd(7N;u%^A}oc^`_H-J0-t&nX~Z!O3U#%D<3F+-!jDMdN3W)3Pu;tMvCuk)4?%)_{h^8l3;xe6+=P1cF;{!Cz^hwha=Rmky5T@m>zTmX)63$OBnS?9;VxrtSH-d@Jq2f1#y0iiNmtCoK&J!oQ(c9%DWHDcgdR8lo!un`-H9q6AcH5)DXQfVta|pZ23zb{hGh-M8bmUkPsJN>?;_Ga;BcM^*j;@$$_kIQP7rKXuRzaP=XfRKnjt9x*sHBn<}tXYl%2(!uy6u+_1hd*=7${uEX$-Kq6ADMFD>0_NnjUaUS`8D3pjgrSx;R$mTqKW^u~`AS1#bLJsLzK9=F0FQ4hFUVuQV#4<nUO1o4TQV70alU)a*`>v;>JObRc$|KLu|jAxUv$cT;Nt(6UHCG8g?8=?F?s?yN#i-S@@K(vkDCo2S&@zs_M-SKab&sWP2&I-gcuF!Q1Av2#>M`2B{)TB&;y$%;DW8MZu?$T8T9RXC0~5RgDNo5s<^wOGD|mpy@@E4M1;^^chm+DFBMXT#nc=98Z5tIyl+Q#h!M>UXCsoU50dTan0nb1x2$6h&83Mr3KuCle?Mw`Q7sPwM#|^s6i6WEGMQqI+;Jk?{G-U3(_lC7DSV($#P0N=O^}kPmF_tYfPR+w4BJb~nY|71s_`m_>gw3`bwpBjl6wC~s$vjMDncdbfu3U%4}%Su=vkDjR=kX$MX`lQjZ-r;K*WncSO)vY)L7;KsJdPv`!CHn*0aOX_J;B8h(TI^$$ZmtypV>201ji_e2vqo;_{3WtCGEgKJ%YwSInHsZRNi$+BSik8a#&MwL#i~Vu21Xwo>Y8L{H^(9(rGmlLRDLuHRMGL8WuX0LFnt#SDpx>p6*4nitQ72Cg{JrTi+p=;E?N$_abVbzMSSEUQL4YZtLZ%dFrG4Iue_<WI<$xW@Z#atr|T=lg3~vvOsbM-+80%wy-Bo@OwNqtELML5WHH&sVKl0-d-|U5;eD3|X+NFvaK?fInA;LI=ZMB=XcoxD^jA*l`&RXm~=@8(s)to&8-|PU=93raIQLp{!<UuBYTag0K7Ona51^{Ltw}Q}S-qv?D}a7b++fp%A0=V{*~fPppKS`y94gU=4t7|K+GH+f6Y2#FRe-Wa)&+abWP&STa~BB65QOLTmSaWg+E`B|Q=d{j;M~GN(`DN*Z0GuikTRX1p)~`dn3bIXm=&<LvE*BEujs&fQ0j->brYzrf<}7R@qQ1ORR>?Cf_$)g1|h+0%Txht0N;j4j;N>$!Otay2&Vz^XYVU|r7RmOf%U#-0(!AW9DH&^@sf=S5S$CLNrj??PUXnhG01xa(^8&HR0#b%O2dN9By|UZDZWF9?9fqT(WM-pK*kegZ~$Jt`c&l+Q*m=BH+Y%GgTVl`xF-O*+KDcoucP?uw3CiDdO@**%2ULALnKvYQvEu@EnxV+%xBV+0T%$bJ?~@2+%y7N7#~U6Nj%3V~78FveNf%yMfI6InDvG+;``<*9!7r_mXW)@;zF`_aUnYNrTXlcXZ~qfA1V634LdH?}#~QBQE}+*8sOW$d?_-(+#3)FX7WM|jft6$5vAN)Ht*DY#5g7_j3n?Mrl5Jv5e`RJhO&JIe+2Mi?$t)F^g|k})tM|9$Th6a=?XX01g@$XLFUZL)OLlyFTVzd1TCO={=D>}v}&!}_}fuqBp??UA3c&<%10A`B#hdZuRzuMj@mDvU#p+nutcl`r$0@q}KPPrf7gootUCpLrd_5Uu^P$^ecF?wfgn^d?fpr-XDN-kxud+&JZXpX&ad5=AI`D$(`KCB=-CS7$J3?o-)1sUAG$$EOfp@<pGyft~`TnpPtXPhxV*?D-dyNo<3<_NgE8CBjOb6XDEfz*rBOXlk8aM=sg5xinkDt-L2~P)9z+GU>h@g#l#M=X&2Wb(WoZ{?i05t8^;*$8lqI=x;#!gg5v<CZV%)@`Enb4g5A+(Hu1sf^{8!0-tdR2SnYbq+1G5=K%&&l8VbT79s$paKYjC)}_>5E0CMyCO?t$Wx`RMrPAa&{c^Dna>t%{IPFUjgK<G%U{IvVN8P%}@RTp`c2b~ik$?RA*L$_(lUvs)R`945hNoQOj2oc0@#(t9E2+N@7SA`w__SJ?@ihI<plsGi-)F<B9*%fC4k-W97~2WY5SokLaN;DICY}@hbbiL`PF+LHNoFwO+>8ONI^-fp?T@39(moOa*}%8@Wo%+|iW=z_C6=ntee&|lal9|mbdM?UG7G-G$wV$96+vC^GpXJ=i(T?!5?QrggWttcd}mziWt6)ts>G3+Eu_7x!Due4h=Bg+zfK$+a9CJU8?r#VZ_y7#Z6(}v{XS?HZOD+Lb^vfV%0o?qiRXO&ICA~AN-hfdt!dR0lwA{gmnvaonXC#Hm+J>HT%kq5nh(}_w`y|YxF6)KNE15Ww2~TWJhP4<*4J0-LABI$$6Zg!t-w+^``XpUXFZI6lG-Pd*_)g$%3{o0>Ig0NKTJD0t7sEWQPbr`2^NC~C4E(X8`lMi-@8fW)>zgeVd{3|p7(s}^>CcU2c_3mdI9(zlEjU>_XRp)=w2uOw>l4xTBLx50+#4NIe#cqIg}$YA)ZTlWue#>G))^o24N4d5i|oQ0?lAZ#dlePcCh^<)+zSyNq}H_b~#{0O?a^;QT;Y!sMI;28XYq1q_)2^5JKJ*!MCLoZcKNnY<@wnNz5CagIs5rQ5!jpl@^u*k$i*I$dA9%y4`N?#V<9G{B`BCtPD2OhQ9|_w!3|O0^NlvmgxlEne+AE^wIlE$9m7Vx9~^s3Tgha;qTRKBcZ__0zddL7*XGOq2?VG+^lL)(UvWB%P_+2LWU^($04%hnC{J&F-b+#N+5>UWjzVejeNa%^G)%GZH1cVvo=ya-Rab+Jz<Kj9)ua^<LsG_G;hfJ@reK&1`3la)L~u(zcbT6$!#Cu<Pl=sPEJxAvA}tWg|-}7WH`enrsfP|E7RIhNs|LMUxY2L4|?Fv80SNZhH@Tq^j6~;dumPOnDz7<(5>Ld%S3IV6S#_9(owj&JzcwM&qeX*YBfan6AcwcM5}sVkazFMqseeWvX~l{(R}R!Qy4UKg`-ccY{jlw!qN;yI7E&C=?*%$38R_y6iqV*U`Gp(Hq1$`C7E63jsTK3Zue(T<ljLPW+ivdQ$&_>9OLcz(5|I)KYL>TKaU{-R=Cxy4K4A*+U)UF!-;KQD~FrXq)nF^O^bpIlxxp(^q4nc7ptF%qBX7R<zs~C&x)!P1xvpBaB2gTFiHF%=vcs2F)jezr~k7uOe;FPG%I$|-A26~Sn}@?Xie*xO97#rXT4<HR$GTuvxJBU_Im26Ay;wktRvjTJB|*U<#r#<QBgy3DQ>K-kIE5{HWX0rO;4!C-c}C6dF)c~GXT4sE>kV=H2!w7WLC5cTGj9i^X61SWijDSSIiXKDI8}EQ{;y(f&e7aIlI&!JfI3D%HB#&K7Al6n{d}|)Qkau;u8x=YGLNXIqnjk@np!qdKh~<l0&&zx@593YLF^<F+pENv|;>t^6MCrK;Q~zQnwTt282KNw4r=qmO=^O7;vc+`F<Y;M7W@=`704<IXFI0VP@1ouS3#g!cf1zJ?4B~d`5TAnTok0Ey?x-x>KL*$E*pFUykr!m9-`?)dLV!O8n`6V|-~ki`xojr!%w7t%a&YRKLb4+YVg8obL=YR?Eb*Qh+_7omE|&v1B_(UZ<B4Nb|SiJLjmFSKJB^Gqw}OHJ*PwsC{O`K*ef&Ejz#bQ-~<!Cl4n8j&&e__+z*Xi(`UVwk)EOgI~aUK>S`EBGV#kvTryXZM5#vwfd)%Gn1+^bg>-NYH{AH(jdF81?4YxDM?aZ7TZFhm6b}P@D*R%tjCDbvW*v<kBZrk#V25nsM5v$N47OPy0HD&JO9!Uv~q#$Hcx)f@M)Y1A0>kD9ogZ>)X=nr2&mcA0tW$Albh5nL#-E<A&xhNi|hF|a_9v1AtBHeetPc*)ZNQ8U8N>_N<0Etl|Pb$S`Zr!<>O}g>87L5YS+g3b<FKd)PQvq7L0v^DpoK`-k4A~NrBz=b)Jq(u(xF7l_$6=Q-!OoPew3(VU*!~I`(`pGtTrgpVwMeNQjMr75Ciw>QgEE^WY)7ezpdM;-#i7Fp3)c#<-gh8P5K>o;dhVsUU~~H2o={exXV9vUVlU{w<F1Y!$2hS23OQm;acx*_`RPt#}*Rdj&hPVtVk5+SQzj{%_%z?$bI8mZ3oVb1S1<Y+uW(Q(UPol<@?v%34X+{SRJxsK7)r<6rtz@F+Q2YABtVzTvCqP#`Q54Zs+>GFEOF<<UW}2z<lWoE`#}7&+5xZJSpba1!~o?R}h91wOAb_Ihksmn~n4;3fFLsX-*j+;ZEFc|Uhf6`1@=K5dR|2URw!L7(D5m(eYXGf!oJ?X)7|!le)}9Oz$fgL&?9;(-Exj);lh={^c4U@HYRyL|r)jgFd5ojl>k8j~o)*Vrwz4SBx69^D?bxqvbb;OMi*?X~VXW7tQ1j)X)D14^(d7ovJfGZ7I5_C#MR3zA0&<Ig7zA;i_AFt9{5ec7NxB)=RV2*#_>mL`6bBB_`Md>Dy)lrRI-?mdgHDeLn600dE}!c30Jagl@G*L0cMPG?A!B`3k*F^nLl8_JUvn~C2(6%GDqq~r|%V`Bfq?ffs3!~2#SK#{6A3$65BfqZSv#_c5HH(;U3AqINcYCs*&#QfNMR*@JCslv9XB>o1g*9_4xJ>!Df2XaY9z+D?;*ibcN_p4ztoYSwMUy%R_#HKU{SYXyqAxB5+4*u)_(9<0_5yevt%}nH`!{0MOK5w5di|4{F)TNqjnNgL5i`i(?H?*Ccq4Jf0KRq0OdC(ZSk(rspsjsL9X9E$SM_S_Qa^hc!HMcbE_M3u;76csXuiS@`gSX||OT6XHhFwzIY;h=h&b9uVnXGL*c%LiaL-?fLsB3zFEQpjPZR%aFRrO^^#x|S>u|p_Jhs|Qw@}%f1jG*xWoSNJQD;MGILdU~|)<W}tjWlTrQh612aBIza92L^b`Gpu&2Z7X{%s-i3Jf4Y%bD_qN-m&8|G>KUfMGFfk<{3>47_T}zLP}~raNX~_Lxq0;XSiB|_(~VJ&oAqY5xDNJy9PZa7eZ)F@-mNpNJZf|Ize)VuGgO@oPHTw<WtP}_j9uT<Am;zEP3(b=PEarb%#tPu}miIb4dntJx8#|s0o#jI<u97wpWj2lippbjHl49o9vdM59Ya=Qi4fs{t06(9qComC^;9sVeE2UaJ~#=J}96UOZaQhTAnkCp;TmazpMT8)&HayeC72{l1R>Rg^BxYo{*$by%#UVSy`0_-kEyZ;^ErakzB}-cL2o}mYWh*=UT)HbPS(qqTv5dI3()RI+q5K^T>bdoMm?9v&)!pQTdU~f|tutCz1-OT-WLcvLgeKm$6MO??Br-%TD8Oes#C34F%OGXWcIhw5@do+O@MP`Q^es=bN~2zH!xmS2$Qa0<Z#)Q1&iN^E8(T2^i=G&65^b8sE-RkxIzkMi|<-4{5NOH8q|JUxtfv_})<^pNd7q+;6r>E6B@z`Su+OJ{2&Wlt-S{9G{2(#)&b~(G%HVHo}a@2b4Zu-f9EX7e|ygl!m5qY7rUN?fu^|-t)CrY6(>9<2`_46O|rhSg?;>0e;k=Barb*rhmwN7ER5;bLXtE48I#fb7~fPMv%`g>D!?+&R9;WY*DdF-}8#N4U@jSRTRMw;xPcpQ{1aW4diY~ekqi}%Dz4%fTzhpDqJAC(VXz4oG60u!&K@G2ZCg+P&G==IUPc~o#MM<dpZzjS1_5#S*jWEXy>5w$U`@}IBDbjPwtjVB~SXYXF9Ic<MbAnDv<Ib-Zw0HXo{DGz%((IygKa{_QA}ff*ygH-K5XEJ+vQetvy10uL_)F)@-M-Fnz3>T4EYG)yRVpfuOd~c<R|U%LM?{pUQ0V);M*C8SQW*27DlS5f`;Pz)3A~SaNBNx6~HbJknWCm}5DrR}2Y<E^a7AqKIn^!L+7H>zSbtT0K<?@R)goo|LH_9zRvWTHuuFTscEmxU(I;jpS_fI`W@Os|P;^fi6t;kG()7K#u%?d4v~y>=(17QN<x4x!(0hvG)6CUN_onR;gFL7LmHdbu83FUGvU%I?|x&6JJFe{7@}v3-}B$dE^Vi(;-yxi=ay2@_D$f=sh0~>U$?p1dqJh#W&1}cPsNk_K-`No(uts#w|g{i*7Y?aI3W5bjj}_2u2S(sMH{poIpBr+c6;h&ld;rzICm2J=A^Fwr_knQGizRu-^hTn0W-kV;fuJ4^Bv+Kv8{wpb<WLm@iIh99*50(j#42+GP7D51aT7EC(zC$*|D?&^4b;Wg*xV!{ikz9AjN)?ljouXSYf2h-I^ubo2EcH|b=vC)oTN;aS1v{bInM+r=0U{I$YH8Z&J2&k}nzb+&`9TG1oiUmFCo?Bg83iLVYM2wpvT)0<EW0ZzVm9yeVwGNuh{Al3?&FX@6Co3;iF@_;G&#c($p+CaB-SiHAuxXBxdeed82Ua8jaj$Np59w3h#{2`1)R_pbX!9y@Ujmxn9EChV<`9aCQYDU|8A2HyepF)UfLU5uj1sv_F9tC}<laRZcPc7bac{c4B$7QUU^i+FRD)Kgv_F;X7_=qgHw!}fc5$T}OdeOG%5F$X)wsNoVT-?-Q4@o26Gx5$;W>gYcCmj~kr=_WuQa<*a{J!Uk4lzDehphMjrg8IBV1gc5U-yhL1GxD>ta-AWm;}XG)i)%8g0Q~l&rwS(@_)%=bCe0+-+s6$B<U?Jwe_n2oRxa{?@}h1C3`>5K_CVzn5dqwd2#tGCu?xQWA)XpwEv~I|2INh5T-)Qs6G?1&qXD;F}2^t_<b<k%0s_kjf(=cr5mM@bkX$BM&81rE)h<Tp^#VdKG9<Cbj=cx2EOQ7rZZ4o3SsPdU}Ok?hUe%HcuPGPP2$=v+_hLX8pupv!p3PITAE`)6kKfJN{q<?_SbH)`bzM`eKgdVvb|_K{VHA<$Tim%fYBm*h8ms}99>3b!todi1z<?YA-Sp6Boq9B-O&oWG0xHwU-HI`BnOOUN1%?Q49+Kltkycud33E<3DpI~HOrcT*y@r_l7BGohq+;MJ_;#i(3kOWZNDOn`|DzFP1--zZG@$QT*U=3<wpSye>IH_o$vQvFr*8j0`G#t$=~W2@A6A~6WhmJ6K1m>kB!utx>;jktFNKpk0=#14T)K~CjcaBniEovR`kro3H+So$B8?_5%oa4+u5h4r#Tk+hkk!#UCBInI8Ap&I%SX-r<Zb3mZjS6?1e(TnCo#m6nR^~3A3&-5%LI4@rr{mohDOM47x#BS0OIB-WU)gOz|D;dBE<Tx1>%t?Qu>{dY=)j3hQ5TuCc-jYgYeo1&pYV$DMdgxpYkcggd-w8QvT$vxYsb)UPvwZA|b(29LNjVy&y+i}!PLt-E_Uqc_K68<HxqF}}v^B;YTu*<UqOx)k2Zw*=kZ>aL+S!m9ixGT$#7DAb#tivq;Stvm?iD-5FRGzQrwBWEmok7uU$|7OaLvm<pBA<-oF=Uq5T%uKr>YWuy9ndA*|C2ye8gyTzs_It`qU%UVS#w3!3(QJ8300F>2lb8hnXTi*?vBYQl0ssI200dcD""")

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
