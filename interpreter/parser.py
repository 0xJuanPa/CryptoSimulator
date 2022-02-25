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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;u+p3Qe6N*0S;{*So@k!X(!_$dkC`jWrr3R=U*#h26E`Nq<yw#DvT+=UzIDL7`}m<0`c&cMIVm)q%ttB#GJ>^Lxl&?KpnI%q;AA35|MNiX<&TPiC9=s0cwaE7bba%;NR&>pSL`+wLfFudHgj<VEYbz5J8`ErbIBsv>V#QHt(~6X)34k8iLCs87$~Lo25zQ_+PNe(&&bQIH`ER-uAc0yVZ`JYK-f2Y^m6lHzHpj5c%|{7pm=>w3D<o3Vxzf0}rjDFS02(+x#OnHkik#s2V=Pf#f5xQ%P0<NoaZI(sKpPF^yNfv?1ZlA!{&@Ocl}%?2^4Y1VGzkW-{p~!jglT8#+{0YKJJ|{Uq-E?>Si%JFSx}(cSflI-&`F(?`cem1)wN5#@HwvF@MFz0(+Qi@*%7(w4dHJ6J&JCh34XCt5vD1B@FjtSSz6oK&*a>*PcQd<!66c!WH8d-n~Pk{gmI8KJ~sxe`1sRD4AaVr#_t3E%2ZO80ggH|`7^wE}l6wDkNl@3b+Dwql{inoX>|+Ee-PFsDxpLqW6ef)HW(ukik#+AlbKuTwp^rWs5|<?jLDL|iGcAHGq~esH#`YZ^+C6NJN+t%+zK|IK*gbrPc_f`q-XWTfMo*oj<)%dkn#mpn(I>5@(B&PGOUQDfH`cXx7fhe{Hs9#a5Cqf)z%5_#<wie0w6@Tk8vn~2z^@Yjfi?v}Y2&5MSKP5gUNW@fW}v*cOh5%3%>M6{d2$&uTrUJR9xJ7(qSqEl(9dV^mbww$=Ni86hEXV*OfAvK2+l6ExiVE8t%IM0I`E5r8n{Y^Tk`<lnyVMhm-9^rtakc?r9k!j8Epnh{LWU3v{1e_jz8Lp1Z$<tV^C$Yhm(UfFcF)uPkz?1V>&=;s^T308|Sz_*6v0tVe5ONqE?p7Na3i1PPxT&4hr5JQzni?k#gUSZ=B+J>c@5nH-%angDP=>AaSW2LgliXg}p9dsD5xaKKxPb4Gh&+ePAld;dg3R`#8(8xP_$CrjaB)4W;spzD*G!h!Vw(p8N3ikZSBt=M2a7skMtF{@H1DCx1Z5c^d`;s~tsT5pP_P+mQ0eh5;NKRHJaBQszB(hkpHJHi<blQXbpW-@gN!PDphfU3gpd@<B$Xk+eV^uFRUqyJec+whIg5Qd%qykpTFE%JQvd$21wwDOMvokq35~4P{}<+5ebo|;?Gs})bqLXM?qocz!|E|O36|0Ux2k>#iOT2VHamm5g*8Xw@x@b2EYE*q1Q#6+lSZJ^-R`lUhZtf?!RqZR+qH#A_v~bbQ|y{LMiyOW?UFBE100s?hZm*syn~$zMIWFDQ!AnL&$>53d%`A)`yuBmJU5JjSV7$2PduzVPe8bPrVIjEL~Ir@mBNGk8Xg+9T5$zkBl|;t!B&^ANyArLngrw(taQeY#-yE#aLT4OXCR2;j95rGgi7{0E+KELNLx*_$!D&`GV$fbPYVoTtXlQOIrYG*VedqDRcwW4V{r^o_9r^fFc-Awd5N>L9tcTckBmtppa3-gi#EJRR`W9-#Lsdb>(Xw2<&L`Fb2?h2823637R+08yyi{_;ed^Bz!m<G#w16AOA(^1e7Vc^EMF=})YTPQxL6^2o<Xhep^-C&Vj*><x48<fC?dwdRK*P%wwdjSMje5qdL|a8p=HS0YNihSll7xfIGGjm)=pgJ2dIt>)eb!@QGWv3n;%tG=vwnKl|rZNS6q|uFZ;#BVh>%SN`i7kRPkv-nQAu6b}=z+s?aa<Jlp@vKdm=Xy(XbVwTt~8=ChFA7Kgr&KWXEj5}71l<*H!Wc34UHVf0us0{uxdwaERKh@XX}lzA(&co3QWgoB?{cqKo(_&}C`wi<SM>@U-Nf5>*vv$)VxKkp!RS83l$FE-E$^l24&yAbF_>+<SCXo`az=4g6RoE>~c5ovQtL1`m)))Ju)vo>siGIw2F5$Rg2+>cO0`X&+3`ggQ4zT3beQH&@nYWO+FPxR{XtS!JSbwbN4w|F`4>1Q9M7?O~IzzbQZdISfr+c*#;M}3YFtDp>>9I<~#9HnbiUvBBE!)W$Pc+9)L)zX;{&t_8znY^EfUKpdp^xOCoZUx|=>Y^ov6R{fkhM5<qS*o)54qU7fB6OLm%4;1S)aAl&()(((j4{EfoOv!X(-u}oKFE6kh(fhj6IOP$lnA*0pz7rfa9%ty+4zNusT*n?RIc)@1RJTq-8$(i6W`w{8fQPx)t|E}vzGs!mE$l2SQ1ZtYt-R5;kt6iqJCNjea`M_AGa;n@}v5bO$54<d#I3k<Aod9FR|~O(S<xSTu5i*5@r+dIGF6hIn0~@+kwOliU*D_w6bxdZG9{_IQc&xEdlkggpS_ymv~fq(AyXoiZo4s#Hj?ulCVl=f4as1Q^eJe%I;z3Fq`p@xn2qt0pF~Kvc?A_EkmWH0q&7?ypf*-H+NFAZb5ybt|6gL1NE4_SWncHbZlA`Sm4NGIQpAa4cbj9h4;LO#@7of$l`VBX0Ok~nABs^TFzYrm{!JzgF=#!iY#D*_Ev2Duoz;3Zx#LuLu&b2LtZF!2&qKZiD&d>(tGwuBysKW+i@$p_*;<hnq$Wpung}M<~*rnqr6VX2JigrcGWslyUrMmfP#-72E#I5-_7)hs#JJ1Jpx#fY@n3Yv=%wzom0umzxBqfpsSiVyndVMq{ORjnL?yYc=x_bM%4#y44&V^?e^o8KP^gGH*~o!D4TtccJf52R_C*;pky~`hZ0Md1P(`aiVdxtyvucnf(TUguWLEz_DO}jhXCdu+uq%ty0<*qwqLdZh=Hm~ts6HJxO1BjN7#QEJ~z0UxN>BN_zclUx9s@Rq3O($K#hqJY2xw-#A@=cs&N|!tXyB=hlUjHRQHPBGL4nM|7D*+vySM&d{fYU{nt@xt$Qn}e)7~(XlelAS>$fFM_Eh5kl&=}w{JeDm;pZ@(;IwKmTs1s)hJ3j<LkPyexUsPkKYslA>8HQm6YmF8iL8UaCD79Sf>STbx~dDYih_bsdd@|o8Mhx;lJ;eJ6vx&iOfa$h_6stOYODF7x;wkf6lA@?3ud7vZ?m;a`LEH63RMKTrRPYGxWRA!xZ#q+gvt4N5j1d3uR&2s3S#jFzaFt*0n=<s(yBh4Gai{<iS62M0RxK)g{rMyX-l&yX|z-Y7k5}nHY7t+Z9W|&0&~*kErf|-@x?Q@DRyeTkv}c!>lL@kUjAtTMq^TWHw0&M_im#?sGT7L;siZXurb`jK#pAnKhX3>QF=t*(y}JfTRE@JGpon04hV5cNMHEN86v~tZ1m)Zk=+uat<yvm2c|=co!bzH~dzDs*3APIxe~RyLQ>rN5NMzQ))yEJMb@JzJAv3XD(0>`P?kOc3G~-wc@vUKl-Br$Jhd#MRwdd?%v<?&~KzpN#o3HwhIUtRnjUHxQQxU8U2MWw6N5RprjM0GU^zJ`Qwgi9(DRop}<F{jE8VEB2ZXpQxh(k4%Zu<+h|f9Ul(X?O8?IVFb^wt0EENiCu)AGCH=n=1ub&Z#hLp=7j1b9;{Yk!<1{wvv8=^Dl}pU*87He^kU})DRyX-P#F$7wNw*!qBzOqu&A$;621x@zF3>d{fT=EpSDv-{(Nxl^>mcA`Y^h<vh5B>*iN9%vqpXU{&mb1#Vl)X_*##m6_z>6~x!y$@1ll#)kLU5X<K95Pmzc#akn?;#UX&hM=n#(b`0o=0I9&9aQA~9ouKS(uICMgwJMTgaoVj@T09l;)={PkcT#I)yDM`O&M2<=eajW_53x`GH4Os!epoK_!4V=fo-?4B=#MEJ4vt74*7!(m?Aj$;$BOD*ulY4w5h8xM2NO#|Nr=%JRe|(^tSsREA+Q<RCI>|?AMAop7x5jKg!@9W1hYHu%{f&PQn~m)hh-a-h(LbJ#`KfvhDC<Mt-?d!n_J8R>_MqT%!~TOYIQHSSlTiVpnlXghHTWJd(a_l<01!n9Pl{12?;~`S%hjDbt+S)tGjC$Jc>}>9;0sPj#g49T@5JJMt-GJrdqOZMCD)#!Ho(vpjH%}M)~_7RL@DAH$YvGr(=;7EU<Tk(T%FzpMU0~vqRgkT6HN6-#lK!xl?<cZ&Gz0$zWli@`W)ue{J5dXgw8WgU3hYF{>0_wkAVL2Y(pBKOtEb1Pm@TcBqF{v|Nq4(R1N${{OSOfKR;zM&%faD1<m|osLS&!fc?ZDEMd$^8zRIWw2~+LlLTpWEFUydb`6t-UjCTY3LnH(KI)N2Q#WxHGyf6s!e}(Y%GYU+E~;(K!mkB+z~5Dx=1TUHoX(bH)xlTYJU>i%Q6Yn{C+IwYl{J;7*a}rNQ`jPiBpT&!3Mg$s$LVj$RIceL0`SiF3~>#P^@3#1?u25}`AAGnhkuFR2i@Hn5f6Ox<EB$bE?2z#f*y4`i0_BS?a#*u&K(|wK=D=zWVdAzx7CCFRly08LR^L5W^NZO2Z%z2=deNPX=#3+cZ^ULPqzXaU5>i;4iYhQXdta6R~R>>f?sKbqtn&Gj!W12?PJOymFnpWE9Ax9-id}`8|A$ln@rQYTn0pB!18{iGzU*GAU;d=44=5nl63f&JfB(TOJl5Ul3Mzcj^kkh!IJw-JY_rELF+)r`bH&3`-Qsuy5**Nk5Z(Os%R-W3{n6|f^57#s^ND4bomQ;gtewVOnw>>w*sqY(K)hU#RHWi*qd`!&q3JEXfN4qAIZ~xc-mru2A|({CX76DcSJM`4OR=n8B;E-fIwYcqit8=C2<aQ7d}GUWlnwg7XzW<bktJVRU8~)y!G6Cy8J)J#k1d05823o0r`S<N9dOu(G=G#u<8D~$%~dEXEeeCJ{vBe-fwB4+*=}YcQSwcB>~CaxV`uKB9J978shFBHAEkzSDa;mRrBI9uIOYE1y*mfRH^`gDId!$Pct8j+ohjoCM{7nh^HeD0bg(G%0k)&0WX4kHKtw8&u!~~7(ul1{Y?G|n@ufGXkitUp|)6jUY(p&J+*#(_Ak`udT8y{RlccEh!aN)zW=Za*IOUU%+Vsh(BRlIAUAfD^~tU$R=jAmDh*Ye*b6YI0pC}tW)m)IDS(lHP;IGH0=kl7fr>3M_PgM?K2;%WwAoM)&>L5?06fa&9r2}q?WV?~8a9)V^)UbV4pGNevWVH|{HspD2Rq|*as-4#<)=ft{(?AywB5Y=K71cj4RnTGe^k1A*kIL%uZU&s1^Vm8VPqO}Y?=$MEi5m#S0kGu+7OJ@`syJiOLdi*%Zgm0UQwma(kD7K7jn{x7R@ZH`uEgt`YiIp!Ecd*uZ!$*rNHgZHmSd8?vq_0_pp3Sy#sR{@~wgs<U9PPyaZisa~dCfekk-}%I)&LKSr@&b!-K=?T`o?VW=f${WV(v2OTFU%P5_P$VFce)pXT|v`Pua(M)p(LH^(eMmSW?@r~oEba@wRstm*)xSFh>=Wb^1+wy2D;gph>jsvhhM|Q>f5_Xxk!q-x$WeCr^sgIu=#jO%kGmbBb(V-(Q8jDRg9Vm$Jk^L0C{4#@{G5z~xXS~bY(<NlrCb5G9NHl{8WYovxbJOqLknw8E&&Gw4tRbAbR6lN1PW$95;hC5Ve5ILu=g8t2&kGjlF@V1XQFS4yj|J*-kHo6^=Phber=_Q*A|%r`dmQX2w=)^O$s`&;f1~%q-u9y~x#*QvbcX@EICS+}@$iLNo<gKT`;|4z;V+LL7|lNU{i|-PNcUf*{KSpc&7&k^mhA>I#5RU~nYp?@s}qjbTX%6*Ny(-lZf$rw>!aRH2L6WyYkwm)&M02_39AcrP18E;$k?}LZU8j^*D9XIie_!+(290pg=wVCkq*QgxcUOA89yf8L0*1r@80ey-XozmVIgo-mla@jF-;my{K}%Weqi0dbMjpGM|P9yZT6BBFwUilXe7fbCKxhPy(+$Vm^r;C#QZGbQi&2~5!JJ$qH^W25;fMRls@+|&xaihu6ocWz!|YYE>8BOcT!P~*%$hz>>>*p<8kfQR>_5cyQ4+6XFSQGb<qS4zmcMw@3DJdG<otcK-g2r`08Ztx$CrL$H7lg25>EPMBeUPWW`+P-&>B?Y<QyDA+$*n+=SekoQ0-sXBV<8l|v$bMBrR!WqPb4vHkY{BLphplSXmb%_SaywoJ0xy=<#)a@pnSb*GmOp#WDzg=uW^UrVy<h#U{10rxfUCnTq7fgzz(Z~QY<MqFvoBHPL=JNKZ*MGMs)2&WfL1js%Zy)yq3rC>c}hq)8b!=JtfWa%9wM=GP0;F6_NqawZTqwMo>O-uEMP04%>Y;cC+J}+9m3A%38-&<!K)avKLR+(<e?dc8d{=HYx12Yv)^ldPa*`AgIduzorrf?pki%uv88Y*EDE(Cjd^8Y)VZWGzoAF-81H0u<qJTd4dwbH+&*O-oK)tme;Y9w6dIy)85a?0qi^C~*6nL@57s4j-yjlCGrlvbgLPimOwTDzk0k}5bO#%|GbYKq-FdJ{HRDFC77XYdK#<M!O?XvwE2A)`2{_j)r(!S}$*3F+jpT3D;^4NA_O2R8m0Mc8})cinG>9*+twY(OcJB4q8CqT==_y4^%ZyT84%?gz5b8e9b%ND?7l2&JE`&{0xh&JJdcW7+Z?ETwNo`TtrauxJ(V2|i?i2cK&vVK94I;iO1Rl?h0wV~(nj#3F%XkQ~piq9NM><XG<=Ic&3l7kS3!TqupHg4QiY7FnM;(hZ%7#`gmYBTPQYp)?12nfA<rbBl$<X$N3aS^^S`4LGC_B1Nfm9xaA+Ew~gaj$?8h40=1HF)%-p=7`GGb~;TUy=9yt1cb*Prtg6UlM|LRoC-?lE79=*j``&*5H_mT3w44h$t>RrcW+r*l~^FF8k5<i000c=$G!za1@#vF99p%LfpG1g#{zt?*y0(8Cu!{>iVvDC5%@Ia`t^HC5%QYvq9GswRxs=AHXKRQxKxVky8x5_yUn*Wyf{0dqg_Ui@2OC|Dc>!d0hhx=a`|ACR&ekudM}bF>hdj3$6l+dU<2qUnLxOHm6%EfNt(}%m!nRlc<@I#1v2Yiv~O50;MWUalbPB)s0q!9eD~ZAlR=H!^?K}eFr}abl+KON{KTrEch6<ytjwK;)>zeR*ief~T)vLp43>#@<C*rA2fqGm^3%3a_;0ZIRtEvPWtLsBmR~Kc_dK|AA=qbqO&q<bt<~GCV}qcgPhP<KXDR}i=yy|m0p8USY(X*=cthk6wC$Mfv6fZH@>jziW?~w9P`ZGkC!%NrXQ|%W=yL_dT_LMJ7_@aZ^*3w#f$bzSwnD-MrN?mfqyvxgw0&c34amyhipG6xn0>;y3yq3vB<oQ-D9;!v!h41kX{$Hm?)cS&j5L2|ll`MVJb~7I#qvGydy<^b{Q0?zo1`V5;;%3-eiM{^tu_Ch@Hf&5G`Ink#xNF}aay!Op%T-FxTm5}RI0oGsTu&MD<76BJ{>@{feh<h>$NBf(1@K_=|^@r@p$7-qUIu(PwZ4<7)<cZIY=n@sT-L2KmG;-vK%IGa(LU`>Gk>=zYEG8R@iTo*u%T;mPqSS9}v;hASiOK#w$8(Bc|omf7%RhM|EJ0TFZKMv%(332$8m5RJ=`5(K+=<2l7wlDC&`$g|<sTaRtwAn*(N4q64hZoi2J~<`9@c;Hx6j`@Sfz(RI2xD_t;7d;M@jn+26M*)#WF-5D2DV<k{3p*Ozo3ss|!nR)K$O#^HTOCO0vZunB$7<-s`@Ad5OZJ^bxkd!mb#_C?C@ibIgZhX6Zbf%YGh`U*Stc$Xu0shi?=>A|egUD6^AOD{mE3S(SDAUSB<Pp<s*u{NkgxtlW{$Z-X$bK=L^$pl0J?M6PO+1-9ti!rz9x8Z-P^?=b>_61ZMk{xunu$41I^{Y^5um}nEwztJW=Pq51*+0x3?*aQ+Zzdzg$3igHAnFO5odM~d@GtE00D>8OQGX4p@jj!#Ncs2lM8&JJ9iOW5sXv|ate2NhpOKGpYpNBu;^%{RVuXJ6FSO-LUSB;Y$<EXzp5+i{1jJ(6>Ye-W|j~)H$2;_5iS46Xp<j)qKYPxC_VKi8P3aFjzTGi>1F|4^~b`|eP=!uCQx8q9ZTDIs^`KYCMMd6k{Y=BE^oq={Gh$huf^`68-CP$Ru)c3a{Ce9QKKRJygz59*hL)O$o#z(*o`^M3?@$p52)1Epkt<S9A{H_%{{qeR3*f$f8DCK+oud(4`}1fvDPvlEF=QK08{PddLXm~_0d_NHMEq9-f4S+p>!~FREgKQInRwo>vPdvr9oF6?F)HFhx&y=8)Mqn#J1ihXD@LgqV!S1d$L;(b2ghenuOTJb(y0t=FB#Q#*kv77H^ayR8;VFbyRp9eCjIBi)G;P2(6>@e=%+kZYW6v=Ic1JiJ7Ydjpzk#w$U<Kj!Qm`BM|kFdVmsrUN2q}6_me_^Q<!*ddnFO|J)@d_=Ha`$NU8AaW9<F0H@G)_9~W0{D8iG$;Rt-10!4^W6kSSmdx%hx1}czk9+Z%I&!5E6Bf&00v#;Eymo&Q7$ZhiQ)L)I!}DlyYqCzf%=D~vtZ@_I==UaY=2A58!QiQ*E@>~t*y(Yi-SdSx<XY)X+ok)%JOr)9bRj-u!E)MO&_)%@&!*Bq0KCfOX9!)Zh|hWUk?XF@y!(UUV;;$C)tQ^3d+#fr+HAo7bXVKGLh{uLMY_zEG(!n25AG5RR4-l(%=R+1rJ1U;4fbkU>q@2lV00J?j+pX&6<?6bQx(b9YXHo1Ou^9q5P8A|Jiuz&-cW)HgNP1L0oNB6s-YAgxn~ki7ysUn4#bM7*3%wdmd5=&ntu6wSR1xN>%<CsJ-ibfJs@Y4<M;TNC#%`_O;+-a;__fAHSNq&QW6-@LVU%ontRD3@w$%TeJ)t%Da)mWl+Q#RU0;{nZJ|Yr>eyuZfgu3LnpSKd$*5Afa#&k1FAn&~KDe%*rK>4H-=YhtR!jx_d3U^rc9`hrFR`zj{y9)-<6ja<H^BsG^g1g#2@6Se5U{va0Bc{^OQd+;Z8i4QtR|z}l_-<nh}>&c^z#kNSR^Xsv+c!+^NQ*80~I)O?)yLIPO&))^EC&8&fDNI6Z<bcY>k{E+#jwIysO;boyFJ0jqTo~ryaoDF|>BS?o)vJM}v#UDj+~O%hmV;c_}c&r^t8xvCF%QaH1<~9O11yV@$}zxcI;ZQaK4XpO#kK9>+45J>UFda9&?`!L|@(&UbaFd+=KHMl5PM8yk_qMMh3O!*rYBYo6HY-Lr-?LSvQb!pZXI*H`iO-XkA{h)6p4g!pI>!I2<dI&+<pSe=mOTtdXogYME-T76@Y7f?5=s(lOH$gv~8J>V@SZ#c?fl(AI_)khhK{23UdCLG+9(Y?35Tu7$If%4v5p5KKQKA$5^tgC%D%p0~g!1N4JTS&8!r_#UhIC4-8^C>myJ|=iNeBd2K=GP*ecfp<|TP$i&<?RX>c;fi32zraP58_j*yzUuns~{2Q>y*(yaH8y$2W$sv@nR_kw<2I<r@e}+jF+N`@}jnJf2Gb}|CVD_yBn6FWS)%?lDnx!k;g^EIq^+x8?!$S>eXDV;jN#%Jq-_#wbDZBBBDUgU?FHMgPcjqPevQJ#hJerApQTIiM@zN_ryyGcUUD>tOAM|Ys^-?lsG2GC)vEHgk~r?Y8J26G*^ReP{1%#!+4^;r_YoQlmRL%-61-)mG$NUNs8T%3<vb_<`${x0zeT5E)X-@@q4g~^u@uK{pu4eKONT{6ke@K2-<h|CYKQzp`jvzh;ykjM>yZNTz4(!sRL?<Un;GzgnC`i|Bf60t^@rX%b)w@K^eo21Y<--ru_w{U(Ih=aX#cRCE&(DDCn^rM=Js3Vn&n)#zJ$p35Zr#Y90hGM|^AB%@}6QK4_$6GPY~TWVR6H=CG~9^a?7Gj028AJb`0Iqt|0BFQQ9M{i#xo1%0ICBYd=t0=3VKV$wqdV3TK%)@cLgkLTsjHmfZP#kF;4D1a>5ER#e!KMq?Pl^2PF2DU2n2Mw(a%k)3gD>@3#RK9169&rb?>U?MA`c6dboExAvG}}CZ#jcZ}3&?-(U4J1%H+nxynsRoLN!H)pQ<U%EqeTrCI_;7?>`YNw4#Rc3eCPk0za0{a(}egJqrIL9v&p9q-W+YBMI{$41RBS*E@AF3O`Fpl$Xdf#hW6!^RFARe`l&pgp-V++d`MHs&9Siq_&!3iX-Ce0`)Mptp;A7|VShyfNIGBp?M)moZSviHg<w-0Ku<o!rtcAqP@&uiDM+4pEcAh=k<T_`0b@m`6PPeNl08v$D@t|d2bsackBr(*C+t&&*}dTOSDh=94?^dU?&rL`0UnkY&;dFyg&%{tOYs5neXk>x7p^6$5c4&P%xWY`WX&bKy0pE2P-;Rcg<9*(L8@d+pGTXC1=m(d?ko`#nPK-~%16c9e{k%X(k&caTj*IF%6O;DOh&!%Y=VZm1hP2^IMdo3J#{}l94;*j#X?Z9`^Nz+Nrkot-%Kf5aSkEK(c>rU8;42?0NzGJsG2`sUR_}YzljLJ|IYODHHvy0UYbF_E`)wR!qP!QlaGi(N^)@uDDgP3B~&~5PRms;Ga-gs9|W%O`p$JpQfc1j6x2_C_f{iZ?6e3A@QB8mgC|O5I}ZkrU1I=~^b-&?2LTE2Qb9<g++F8DrF|>Q@E14*vGM|fxQ@ZiAvQ=&Q*rttL785Qu%3h21zNEcT$=SIoG53hMsUUS;xZBdxPM{)SFmpPH1@3Q{__@CRkjr@pd`v50J~;;E)P%U8^t?0YU)MNGZ#Tq#je)B0p%^&7cJdJih6goOZJYD4$oob$C^F&GZICYA}`bOMTq%4uMTY{^t9G7b}>ge2hO;bvb7aD(DfxjTM!8q*HIcvyIlOKmP`eP7c2o`n9@GyYZtWSl{JD8fqLFe20s9aSaSk?meU1#6OFZt2N=la$qv$6n^z9?DIfO9>7!DFVJ_}E8Z*V=n02eLYB}AmkB09%JGCBQXw>V;6S89q-~1rWN8;bfFKVo~EAHDjN*ga66;Y9yB9YNTN;;Gofu(TqaCyOJq`OS;U+sOi+iBtCzve5E3U05EFDZ%qB`>gSGZc!|N?P0q9WOl!^e|RCnHOxWGpPYnsSz~OODPymYrH=K+3?`N)H5%pfC6Cyt(6t=DwinFHwi~I_rG!XC!%XYl!@+z%Y1fEkgwCY_#ra1U`<Zf{VPhQ#pQZ4W2WD>QMYB3gaF2rZHZ4!2hG1^za_Jjfw3u@a-HPAPGf6Kl^ohD`7W;0rXid~Je!jzMPk5>>{WL_9IxbEbk<0@$IH2BMj=gZ1I}F9OOxi{qb4ppENA9ni>q;-!Fp`r>Bidt=--AlRNULc0slP>jfY(09ftM%!<g}XeJ}DU@Osa}QrkcELu)=TeAt@sZI|`5_<T9pa*f8Kr4sifm37-$YS6<ImL%;irQuxMigz2B@RA;5;o6gH%B~qyW{YdI0Dg7kuPqY-I)VK>k1idg_LAQNJ>@Z(>yPD!*)f=4nYv{uRJX87QjYI1M{uP|%p5!>Dv}C{gHL;3pB2BsL|y@oBFP2y;wLcfx(B_#{LKPP&ywTc)1eTdhAZg8fO?4sdoJZl=&pahtT<uL&mABL@`}@MxAE!))p8bZlFd>;Y&Ih#Ms7mNE_^(G_U7&m39bm`wesYR%b~fn#BWhZfrh}0eD+Y>{Hf=stI-3zKjRjBjn(7(AcGE~DYgswKiw}j+O2+3{jmnmsRFYiha_6W^d+7x64Flvh-9hAWCiF#%=yTlXDl=Jwx6Q!OnK+C$<;yk?2IB*ckfhAqIsb$35vy>wM)LvcDFV8Jg9r7tG(Ba=a+N=ir_NES=*T-($}z+L|=Lz)YXJQ>UiV8GdEMvt_9U*#a3W8$TRs^IxV_czc$7uHhl?4I0!RK*#m}E0c5AnIEyR{@<G$-6{j<ZSFmC|^y+DqIr&utfseQ&VF)Au>1_;~v1~veDJ*XV`FODQN6vU{J18inLnFBXbV$yeL}lsk&b)AIJe?%P*s*~EN+G-ZHw;x>URhbBERx0o`kCG?lxDivHDwNDVI@THMf7V-Wh4h4JiT>t^pSntC32V|Zg-Ok8Q2sSSbY>Y>;Eygxts@!8V1nc_*)5@nWl(SlTFFAf!T|_90mXe+L8P;P<L1`vN>8C`_wppGo(Bl_WS;zhGN58GU$5%)Q8n!QMd8!98|mcucN^3E3;iNX7Eb@V&|@B=5@jTLEF$0YNQrpe^GAXbnDJ@3RmSvmIN{L5{=d{jLOzf3^Z!d<;K;*!pZ)j@a?XU_RoO}$s7m4NAg9FR^}%dkNTlB95ZUH&biHmHhAdM3bn!jBcLZL*2p9#!u=!eL$vUjbk&RH$LUskQv{=)btwjC^v;1e=q;<!4sPy4pr#c#50$UL$haN~e=x@+QFsoQ+vpN>W;S$dy}ez{oFPE@l7>O1F5zgAuwOso0)5XNGzfEd1I&8f`U3veN(M@;7z67(0WSYgCLUg~gc&cmu0tQ7uG;;*%FUD@5iwq2VoG~6#%76sE&ABF2N|ane%4S5El;@xiQKu5-eW<3)mM^L-xFGE?K_AW`W?OOxU%YA>e_^vYQsBO30AwW_mE%j`5(EuPKRcOUaa#!qmJ%nx>Sc+)DHsdUp5^VHJ@JDbE=+;H%lI)!dgQTEX4LkU{}z^ohb4xw=F#N>l(2ckTD$ijVHmPxTIkcHi+0EY@M6&g0IUgypsQW-D0muog&KtHYKt&PDv2G##O74)hX?g6PdeeMiX{<Tj2_pkJRwD*gI5JW~)`sVA;+$skv0B5|+H`9NKsIL*XCQt*M}T#WlLf2V*Cc+OXsg_C<ti7L6OYVB1F~`WYj*PA7Zyv-}zoa}zRIK4tj8*f<VOx_3Ms=S;`OIvhQ@U13;?-qDsa@#0l49b+`T0tm@9e9kz|A@WF*HPfQWQ@i^2`r_*$^=A}F>&rM_4A9+SIBuf#{^^I8L{4@D=k{%;0t#-LJw#EK-5D<IO5+oy<G9HfaDRrBN$tK)x#~Q2Q%pyT#?ZLdJGNAk9X$Rn<Ia%m*=;1E3vlshBuggX(=i-M+zn_4{cZtUcT&^i$)&kcPwGKCO%zu&RArOk4V99iVcsIPOwGOd@<$P9q>QQM2cCS(?lthk$<F#UV>>b)6qO$)H`zqE#Phbhe6Au6V$OZaRWf2_bSf18IpE&_0~Qa}F=eOsg(}}ImwtBn=A@($FkIwN<c~O>iclXf<io#zFB*&wRR73JJqyZ$je%s+dHj~BPtCw@EnY?eE<0gP4_A%+E|MJ5XO?PUgC-mwdwauMH~;_uCDMg`ba(Eb00Hh$-?In+Y6AYIvBYQl0ssI200dcD""")

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
