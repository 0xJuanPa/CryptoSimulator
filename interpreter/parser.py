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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;Z08+%Uu9K0S;{$t{u%=x~#|q3Hz-!-dfNKIsLjaNtrmy5$H)!qoTBFc9U<Q71sDpG*a|GAIM_J0<nDDf2wj#ETlrWsxh5ECc8wS)HgoH=yVk8g>j4fLPf1j%_B@F{y}Gvj)gOi{`$kAJkSdnycPWi$VUmnZFgP7<lX?M@F^Izsk_-ZurA36NF3})MJTd{Z`<DPTdmV^sDMHZ<S$Re(zQ4bmlVL*#m<JOS0E6cV%O*?hehX~jcFjl-6QV?&DQ`l=%FIl(YPR}&?ub)kr9e58)DmH3%nomr8T;Uhgf9xFu%?W%-M(!$-s?LvP`p<PMy>?-GMh}jYIm6f#CKjE37hA8%)qYV)bKlM41q!fsAfUw0)-r6tR2IX+YBfq3<cnjfmTxd?ROZExaSXQt`i>P8eDaBOJC~1c+^+SbJ&vBgJQk6sdCc_R}`)S>^cznZy09_R&?D@5HMCl<!IjQ<HR!{+FCxnm=}sj^ti5(|%MB?}`}cYfQ8YEmh!=aE!RL4mtd+sL5BryaMn`(CeX*atdmNSX_UB6#R{>H;AvZe!?^6Gct32^I#CxWD#mmDO#K>*<qmcJFXMCg^dLvYR~Z^H5cR?DnQ*_t`OQ^0~bj`FaNg-*XIg#OIIIk;N<TQlc=Spx(X_5R;7q*p^q;$mRHewYZyn(n6&MC*!a)jS!R(5(dCHZ>PVh-_vE)=Z*c|4MqK1I<`NNBe(RfGsco%kWfUV$jEGA9zh`c)jorCk@f?L7(i$=%TrROu5NowfoRRTNp;^x6$)2B7#sluFC_XV7F^*TjDmC5I3lPY2uQN^S65sK6nM;{J!!iNO;ySJTK0_iLCLb%B3;9((W@R=KN2!Id>q4;qNe`;SXDrfzp$5DTux(FXNN1-ZEXQ_v-=%eB7K_cp({VMQ3;Y8I?YR2MMwyCZlKHLnVuT1flTe(HY8$xy&(=Diy-3;upRn6gfvP9&nF8|6=8S>LJ4eA|H()p?MOe-Te+gnNS|_)!8M+@6J<V6$a+<6ZY_=WX4?(!$4Nf1IhPD?iPiXl(a3LkVxh!}+3l~{0QWt?pv#?A@{tmH7xNWX%%QMNQKS>-Ee6QvZ0N=E?f6dY<1dtquVpj@R=H`L9lR$#=Dd@XO-nhN`W7l1f4!F)%7(mwGDi3z2b&nqpyGunrhBZ_LkravZv!FjUzFJb&8?)>VqB7d5tZcV5eKpmPPR4=j0@OpmPmuwj5jx4DD?M^YT{>DAzBwXcjxBM@Qooozt)PauQz>?H$&u(!jnvngOZ}5$vtgxbYK~Ukc=j2slmw$_)S5h*7TF3*!9fik6!%t&iu(|Aq5APRwWhMT&z)FHxJB6mb$>v#XozQV?hnTjv6N)q@5BrJE&*AWuMs|jp}2+!GE-|B-?5R+2&Ft%OQGe!nS)FQD(d(I5o*;|B=<G+F`XbO@gElRw^alO)5nl&6!{Ca&25<M`b_Y;xieG&`nuts<SFJoWEf#46ejy1-rFKQ8E|QFu$$Jn9;SD9&R9SiUx7HGT~3uh3gMjr653GDV};J;)ra{mY4rs8)|p-f9li8U<&owz&HUoKF-`8N_6S@b9c}s-$swYym++~wz;7x7f@!v4a|-V!@Z;&CkRX?#b5t%d^0A1{53?+yt%5No*>-jPN+SV_3Gwj@NGPd*y3_G03$hvQta@1}AbfVKvTkG3&I{#g4#>1_|C2<!C(0xT@oeL9VAeYk(f67@uKob;_#-N$`6q|yK`JGKB`Y)p8fF1tDwr{k2@7y*ZFHaT2)}<cs8EneOel{mnQ)zjBm+Jnheg~9LXy^#0*?ZlhbRLUrp3BDZ96aSw1n)MYX87xmzV;@z)(OA7muX*g}I7jZ=Q*%C^T=-{)?a+yL{gdCQjs_@|QM0g{H8V?Tg+=hw<>o+QCm<vWHd&4RY=5#^MzhW~^ly<cJbGX!=c@Kez*pDRKm460I8)$<Q2<wyGZ?1u#m)f57=QV1RS>`u`Db2k5(9KVt?il++NP&9o14Xk22OLK*rXDeWEp2<}yR2GE}$2RF`wdakUSsuXe3Q$>4LJU8sYh_knbP(?7i@$e$#Ot$A;iH5PWeHiA3rEY^wln_Gbn`2Hfbyj+7@L}xFKh))4+pxb&ou-ezFF}uzjJ5hYbl1K}#v;J8GMt?xYxydSJf3UmNRt+bF{6}p6ZIY=8TwW7$zwVcAh-Cd?rqKwIi=-Oou0V&J>731m{40~=)vCLM6ZG-S+0e3KFYt+l%tE~5YZDKe?0OD`1qR!3@j8kMYI~SCE-R{ObO`lhVOpl9zvZOEqc5?Z0~waL{*6`vM{aqp%?`$FCSKyIupL=l4*y<wdymQzzy56#N<O$hC_{V=rCK6MrDN}j)+E{z_NM7Gbg+P%_5{lNpB?DSs2%b8B&Nh-PvarHBB0{?-C`i`8JIAm^S6p@}#zS-qq(%a98s>-;CVM`UjDmxN(Zp<42xjlP*4|^~KoMeE3(;Qn4Ru(-AQpl9cSTb3DU-tGHVf>{!wH0HOK?(-BuI=b8F9wx#{pqr|K!S=5xKk$Y^PEAjkWUf*{Gz*`8(#ITZ#1UkmxLH`6VA6%E^yEuoo_z0D=M)(=|rQHg>eF>@%F8&B8IKm^MJp%7tysNLjll&`BKMTtx&YXTolQKU7lIZf*bwxnB(X6JP?klU{pjH}}h^&*d2_PFr$Fcb}9|J&>z9hYAMx-g94)`%MfnH2aQXC5d^@xxAW{g9$zv-HJsbMgvWM@e)B?3F7LuhCpEY<*jErxAFE36q25YIA<5&2TG+Ae~8NOcx_#*L&XD5$WI3@J1&Nb`+qIOE{!Kyhq86<!3!?SD8dNG~#@S_>j%UDLMjp1%kW(6G>0e~-W96@0QTA@H;#B7?@j?%yY9jwtQn`43rahCu~Ec!HExg49gkBAk=J$n!l@!8F?r3h&S*Oxi(Nw1H6$S?1lGC!&A;o)Ior3=X!8gyYK&nSMrl!?WeTsPhytS3*lCTzH3CzyAGhlqzf9uY88y24=%L92Olhnz89{lxDN3?CR_rHb#Eq{?Wf-hdWhqksee>IV{7JGaO(O%y+?KtcFjszRx(B0p>Yl6f-@FL@tjzXNVS5jvp?w%1Yc1hutbHQ*A>X8&&XSwhL9N?$bO902AJ`{jBXV2dB%(8$mxPw7U{Unq7&?*Fzi=E>UiA5x3sfNMclrV!J8b7dcS)a=p1dYp|*I<x-emQ6~=Oj@awVxh|^I4@#csK_W8RwLfRvm$!Xb|Dk1yHA&Kq)=SawK`BbDCwM$fyhmII(g<8)M8EcSp?HWuEcz?YpJ2vCfr)i|KT3xG{i1X%)t?T+UlzKZp&RV_l-?}p=alfDVANA<AYUf#qC~>FvSdKRcqZ(!6RLBYp&D`zkOK&>^p~=n#S%~R|C7!=Sew^dhe^Cu^yEQY-?y_ldNv*PJx`#;fV~ak)R#MDK!!1`tEntQ_RzPj)P*mpL5@gy@&EyPv15_J0z>mbpVQzg)s{t=4L15K;w?j^cYd@G2jrwdbY|*KCCxyFyLEpI5nA!K`8|RifIt#UWf*e}2i2VLV%7tXKW#dyPlBa0)KU+KW#z6k(M~H|^Wj$2nTg4W`D3xdr{a|xPXaswTZlih7*C^Or#>l7T}$_@lqWaiLF#0g5S*+==wwToTeu@R+w7wzyR3PNEgu3&kWY0w+6bI1MdzL>!Ve++oHID2&Jj`IzudX;qCFs67D`Gx{SOZ`y$KBaZ}&`(hKhYq`eUAnd(s}9N_hl>NCd3Djxl+q*3ELQ&=X%YeUOTYCPz|T!eA6br0oGhwDt=hQUo97f0(`wAIcKLSCpm0fBwVWr{|>*OlzK(J5YR*&!HG$=Dj70*fEi``MHRIgf}C4w6E~b=HI{9xga8So>GTgfjxn6lxfWril=^_WwbVxRNDoo1C~_HVV7)7-tRr?URWt*U$Q(Wq07798{wXk(%vp9!)Z+WRGt8UNL&j(!QNgmEn}7$XHS6fmn&B@fPrgV7K}g3dQ_%e0+e!JX2eY8X}Pld{PuL=sz$$l(pjkgr5#T2=CtEh1F&ndWh|nj!R1jj#@Fkmf4?H)1}j52wd7IB#efTPQk#twSl%H)U-)r=`_rX(xQ#QJ9GDeQHE57vw8mfDvO|>O4@~%}D?=ifDhy~p*>35D`f|TN#58`8j2h_K36B&kav@M*PJb4h+AtOcfNw^I{?Zil9<I5ZMplFGEBEMjAbV6PJj(jYUuQ61PSLdWdLyAq@x<wV$yYXu>e`AU&4G*D_fnpK_0^5+efIFOHLczg{F?7-U`V{!2DY~OpqdehmfB(5xY*;0=PN__{lK?hE5|Z9jEbEA3?c@Xixu~_mM!`E&$v6ZQ^~eVrbW!N0TaUY``an$w8cgsX*`3o<PKom-MO*a9bI9QeK2qsIOR+3z?)ettdws3;)gcu68#hJlChnNw0**Cf-goPu2!Ca)r~@TBlnij#jut62k4%%0f?(+MbZpw0t<uSWk#$UfUje!*Ao~1<9~6Ld{91~tnYtm$5l61F{qmw>FgEN;YVa{9(qMCNecFL%E^j_8Rp$ciX%#u=LXdm#09eWk;RU9H?jX7juX25yCJR;Bd?Nqu;7lGxlqiWfhof5uz9rC)bCsLyVY6532QnhZ+ZGBPvzvn5dLwgGX&6eE)c=uOzQf*mD9VFED!z`|5Q_@eBeju2hOFZjv{<u3RX9wQ6Z{<<E^h?e2Zo=FoOE&3r?p@=Iw$#<EvrBVI_-o@=LS;bj|45yW+VUta2NR^s&G53vpEacv7JeT<0dQnz=puMJxDi^33eLF;z&Re6DUwXl;<RXIILfbV&(vKEJw{t$Ux))Nf71v4C{`WPG@WE#g$X?&_@#MzZ#-&gffur-TjL?(RUr{#GO`H7?vpFwCIE1ZIzoH9V6(&<HQU7Uc<jD#q`eEJ0VfXnCxb-p0-XcDehC;bq>U+e!#&u@)P#GR5h3k={$1+X>Hc=)kpY?tQ2l$6bb-P@$9>Kd~&f)Plogw@C$qw<Ro6NXGWR9!M*ldy>VWYW*o<d(w(~F!$-O<|f`vIkOAgWtUOu8CuLe=?FOwyP!SQQ+PqO?QmkSQL^ed;{)%6VWy1&sSL22V4ixnlK*M8UZpCN$M;MGj{ovqwgKW?drd7Ds#d}L;yDdcmu2fv{cv$X|9;-DL1a^Gei2TW{y<S2xPHVNl_L}+gokYWC7IP#F=W>4G;XmHxDj)H$$A(?X!^q(>QrBiYHXTXy__1eZZ7xKt@}Kq!jgNRBTnb^KRamD)pen74J+Wa`~9m7EyDYC+xQ15&{cdR_kAvD>yR3S*juEQekZg?+RIGxfXJTiisl?1`P88wn`6>+u{xp1biVa`=8qugMH-t%yP+8K>JWHeHbmPwW4QqNbf7y3wW^v;yxuauy3RQFOT^@|OpjxdsP9;zA{mHICSYInxRc1*XN#6%w_mPx;VYRE28$J^+6%_HTIX`GKCG#kPRsNeCCfDT%$)E3RGy34p_GaFfL|Mj0+3Co6crE<VdMnpXu=L3ZR*-yB<Ek0YL%ZcL(nf6hiS+trIPg|_Ol<BIGJL%*NZ3Yrpnd=<@&5E&T$<(qsj_mYq(ru;uF;AG4uf~@W*CFoM^R(JK!2E)%BHIeW7OX)B^QW%ezr`@*D%ShdBHCk-D2PQFSyRVUJ@Vgj=(fzf@E60?|LroQirF#4hqUT?6E#5++>4m@FWB{3rqJrY`&I8zRxyIL?TgH94LR?YUuUcNBEsAN0>DUG%94<}L3}vAuoKhbC(yW;~@@3jBVtGh6C3)Ui>bu-zqz`k%CkO4m6d9aPEOzyN|O6n~CA`9C++ygB!kjxR}1v%s6$$v}yt$q{@QMr<j7DD4~f`vyTyXZ_B`s5C-l+vLAstti6;&tyLxNo-nw7SzDN8e5dfH`|xDzAg7w&etPyZkY~LWTBqj+GH0lVJni*U1&CVC^}c^Qh1~T%6N7`8bBFEuKLa;s{<b|3!W6qgxl<39j)Sk<NX8n8Z=R%hX*C-7Hr6U0o~DRt20iBASO~w@%s2=qUhHQX?8nTm2bv_^Pew-HO0eq3=#yu)T|6_U2&DX?f5qj)wDNR;ByK)@RkHiibJ@BuQXEQ%~|f?P<#ZvcfkkoJ3)2JsKCC1#>Y{J%e|Pem<tKGE{t1&K2`Dzp`1bb14xeQf4aqMDG47kBF58oHQv}6Ow6|l0|fIgIJoixy4g++FwRWIFToF2y+|AzFnikMs2#lMS>}M&>H@TEu&C0MmlBfhZQoHV)fPOJx)I0Q-*HBU#AmeoT}-q_?~NvNWz-%m`kRW_*TL3p)N6?fM;Z-Bb*V*0ZwG>l)X0#)T^-!%CzJ2ISLt9!y*F*KDW*)fR>RY%^jw-V2>cyRHLdE=si@izsoQ(aNc*4>`oTW62P@zZ{K_ygtYRXjc3|^)PEkn%wi?YkiCs#6>8R7a*Zn|o1Xn>!x;;F~tgsy_&<H2;-8c7|wlD$(EtH)SfrkAfH)EF>gzC8ypRbxHEf--62~QePHLN{dWNCj1K(W<zk8tb_gfGv6g%#!gL!?VLUkHmtTa2f|EVjXU)MY8ks&<i)5X{WBq0iNgO8bK#{(7|Q8j(}hp`M;F``Y59JkUAhU#EF6x-FY=9*WYlq$1PQn+R?%84f#7;(9B)c$9pzToP|T8&9?<>v3{xorc+}AdLt=Wr-#8dG^Y6Noq>5aHMP(kHK3&6O}wDAZb8uI%${NK~8|4#nLm+CDD3?zYwKT_x=F8h~<&>v*(}rerHz^7Mbk_AMnU>lj+VS3@#{ynLL!K0@7U>Cd@BbCSqu8gWd!tkNTmP!%+<)Osqx!;@EcPU<5VR+1VZW=hX@S`WfeETU63*Gt$qP=l@i<d}pr>F6`z+-a(%718Z;(6~lT5svarQluj<uPzhWVreS`}WRC2WspL)&;G3nV*4*5}rH0$=2Q0LQ{%`&DE^=w}(_=I|Y?Jpe#@*wk2N#Cg7p9aU8^c)MOZ;!`-Ro#&WTO?}I#2<F7c1E$j$B3E&O?m_iOq+*Vx=W@k4l7SE-pc~_F^(b`!f<IN<Q4^Vd7`<&6@%~>B(OMWOrMsy~(+@gb8Fdz;;8762(R`*GBk?=R!#b=6cOR=A?S6%owPNI!j)K+sKqKm9*T#H)!`fa^-+p8hSbhAH#_iR7}@&AguKzsWoG#YHIraLOV8d@3Ki<1g3&ZfZ18>>!NXCL#sp(=U4=`78TpX>azmUN3Hm>D|MYeSxh4gPlSdO;ihaV$@0q#e@o_OMoCNa-5#io)UFN&uhYBfeuvx^Q!88}7$=nAT7scP*VLN|^&n*ZG1;(IQ6jd7+f<%dbaleOFcUvfmRjWwU{z~!K>~)Y>u^pxO9}`F(6E8i8is#UMm3p<$gOz}(Uz^W$<AT}2tKX_vFS`do~sUZF5@fOoQ|-a*Y&7Sw2F;jUfh9HEUI6t;n0g->qfT=I*HLwA!`w01wAI<DVa`yHt~vS3;|o%ai0>aHuF!E(OQ&{y+F139-Unui))B4y5*nlw&Q*(=e6XMyVYfTL^?5y`}+q4!(kqJ_8d>HpDbY68J8P+Wpa}3GQrg*_5?nW;$YRr;&UU@*i<f6s{^Eg^$_wbf+rqJX4oCG2Y)2JaZSf<GG_JY7EzA%Be((@8Xml;-o1ASUjx5NpJ)%O0h<+Fg!<UEJ&lJP^ukbQ*kF@vXya7Sd#^sDOXDwTn%%kbrPccf6zIPCQw|UvT89ljh-Dz5pv)nK`VOkg05scXBCbt6?144?4nsR2TdXpX)w4{84pBC%s-KW7h&?D4IG?PG23Kg%uJ$NRo_1bFr_Bmf<e*V)K-E0R1c1K;9;a>M2Z0lU1YbP;Fg1Ww_-w$8lztn594VMp^I<Y-zAu~%yMb2VP1tx_k`sTq;-W<Xs)ve`t}Ml{rJ!<h*wDQyerYHI(pFm)AoMIGWtd&I5eDT4!NubnCJQPl?IGmz+iB&!O52^wZ3frg5gzMu*_ga!*Pwc~edPS5it-Og!aSj)yv}MaCey;zeRcdA!08k0ge+Od6+aak8ybasarlz;d4e3^u<IV>vn^K@4~hr+;p4(V_}^OVqcN?ip-P}k=4R+Z9bRka5BwGM1ci}s>{?Ll{&kOL1!h1=jCUN)&#b()h4nYYOr{R`-|JL&<J$QF@preGYyXYk^$7$9Hy&&BS7^K-f6xfT)Tr>&Aks`Bu@`g}s}m#Wq8=%Rl@2Y+rb>HJM%Vdv1#kKCxBIxQM$RkUQFW^n5`td<&V9mKvN-}Oivk&^ORIjuXckxyi<{AXA^KU-?o2kCXtkUYpfQi%<N+jGdDgaH5><u&?Bm)k65=TMSYDkL=Q$5t7&^1u2B|kbJhRZ$IzeM!|H(PCxjHNI6X|vaND!jD>%gUy-pbYpmlCLqhbXm&oF$M!S+<G&ERqD4tJ0>1qI-+C5Oq(M3ukn?YDq=nU?hmSuC%pgGMH=zgcj*I%Ov5k=iOUr9G4p=?(1lu09Yvy#g?u?o+pwqcTE>Ca98BFXEYw)Fj?@NdinPu{RQic8rid#@A+1%98uQ>0%mtjzO0}R75nnT<Zpx0@7<B>lmJ?WM5Ia*yDvh9DT85a`Px=X+jFlCnZB^5Q)aQiCuji+_%q8#AqkrfB`~G}`L1_k508W!1B&^CX+IruIer!m*gf?y|KJ^h35u;)OfjGmpGa<EzAm`3xp0~zR>>4ozGe)MJ~Q}UbUD*8o=3$2+MZ1GJczFaWIn)!pcJDB<P49WbawrtFkGU&vk%O88cO-<rb59r@v)*2dw9dP<KH{pNO1*`Gl#3q00knT5Uz4MH32<4MWlKrYZy9ZtO`AAZS4EUrF{a-0<jE;NY5)K%Auo#c2h<KFq+j*wxYw=JA<|?Iv7Uju!Qat|J!eE=RIyZ3CetKq?heC@FU>1neKcnbKbyI3)DCGpjImlTZ*C?zY(Y@h4*?IcUMXVI^zkogyMMPBLMo6M{}Qbs@Mhv1{-ex`cg027)LP(aA*!QgCp*70eEHO+x<mN&P!*@F+SgdI=I*rJ&ogpKsb_4SX#zjWJi`4dSBKeg%p~26@Cn;C#SsaUSERY0nA%67NIhaL!=zABaE{)QWW|5*>BMP6?ES<p;nxpsS};ahLMPtepg$5i7G8!I5?IS`+H_PULIV|At&9D(*smSeJ8CS=r(=OL)W2kgZ*8q`DkDqXx^#7Fe38fqkn6fd7B8tMOeh<-c**}TNz~iHF)g`d-vrO`-NC3bLKcGAm;H06r~nFirfg#l2=@lJ7pBinW);bXxAKRL^RorSFrlx%9BWf^LN>!<}B^CZ_$yWl0^g6UCK$R*5mqOUzItsXSzM#$U_7Ps}6zr&VZG(@kUzgdYd=bCgI!t?e!o(js@&g?@u94+p`P%yOk7wW8a+p_VeN|w3Kns|4m1zE|8`OQX26nld{S86Lc(eb7QWUgAp=TxHpQ)2OylD$N?4oz<#RWhWUD{l5<k$v!z#{puBOFD)2{NuIY$=Fr}RBO?#2`V%>UL6hk@y;%?rfi2p(o?+<;Cnh<+Rc~|5Y64_4t-Smdiv-Q<FRb{<NL-Lza_JQZ~E>8Dv!@7K{$MUxXZL`Bk={VeB3&hi^^@IJS<M9q4R^_WKm*RP;-e+fCCFB-Mf5=E4Gs#SQ6DdQ-a4jPn6>383xIY>L&-#-6bfKuQHFKf;>7q>Ow*pWC*1GQ8MCIUGBs&zJA52S!AaBO4<|CMlOd$*a3KNKv$;9azjZ>E$%iwUD)>cR3%*%Xz+Yvh6*pGudBFle|Z7u)+aN=bIw1_2A00HMa(3%ARiUvZpvBYQl0ssI200dcD""")

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
