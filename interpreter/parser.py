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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;QrAV#$5nF0S<a-Zzba^%ADs`yCf<V^qXH=y8&afNyG+?xH6;DJGXcDqtsCC7A@lS?a<mB9EQqP6p!XVEMJ_niwgm)x!*1;9;TE=2sGrcZK4wES0Xadv=5ozJDtkve=$2`%aRl^5<>>GXLpA2jn2TNGp;uy-^JGZpC1`FCgfPdNSm4$3^ZCx53K%pvUvw1NRn7op-5M+!9UKSTZ#WUlk5Ox17T=BBEsCB?6Wx|zLj~<KY+Be(9h~cu-O#yhR#WMu#7C}Q=bbn-4N3ia7rAe#5?=B0{|6r>9+e2$W6_4Do*g12tWI7C&==}+~RuC*B55*am`NOS24_F0r`R7NE%@3gqfkF>ul^4JvDz_kt8oU`ZitPAdoskVhENa_DJLqJ4;PYqa~`1ObCyj9v!uxU-rBG>xVM^ot=;X`jPfr&ECGxGh~(rLP^=pnD#3+A84+rdw#rFYPySrRW@0vOT&5bO6$%5Bf0X(w`F!?#;nLGc@KlMIfZk6Q8x_sNpk`wwA=5X9|<ufcGTjZiTi?-ptn1hI3eLOr{V@9Xj>J!vSA{?slF#1tY&)g@Y{DP1^R^7avKS4Ygmab5K|ykZXm!@`_H);X1#9Qs0rJpb)H2M9Hd)d>1vUmA$PNL^)5Fp)R8_OfRKf$VfDkcoNKL_zco(0sbRnoU`V4GMR4}?38!T9y1zDJ;^$8t?ePIa2}plJDoX_oR8!a{DYu;r3MSJG_EV0WL{yq=Z9U&}Rc=AU;~q$_i^l)hhS|eR+Fy!95t38tk6xZE5zeX>S~lt>C4JECp?3KcF3v|tpW>vFm;4Me7+ne_$bq-s%4D|^!pH7lLnx8W&>gS7){1`8zfdjLSfGfIKcw)RCe7?VCYqeL&$=~sKWp_n>%2t}Rg@|*WjVF9W$lktXu%bOf&QZMuMhZ);>{vldXUb>rSN_O3gYWr6HSwfkVKTCvj_5fZI>M>I<4V(!(S=$2I|HR7k6JC<ufI&Kq>JqwkZkp1r?Ax`!p#G%Jk%xlDRh4r1-Vl2EjWV>QjLSlX#x-jbc-1<GVQ&_0V7-HwFg-T7PineQ|v4qA2`^kN%dRM#UZOqc?vV+~~^amh1!&v@Ch{+r#k86SdymIl?dsQwzzS`|PR@FLRImoG|Z?0leB*Sbf|C@NlcqU$286t1Xi`zW5(12|!jE&E-SHG$6{PUIb`o4n>Jd0$*IMAEHdGeoo(LE_E@w#@f0D0sA)h`U1@5Zd>eLtvvMI6cnUTsk-Ygu>9|TOzP%;qtFtK>K1^zDe}R-1SG@oUXe(@$Ukrfo8o)3vXOOxVe3M#AFVj4I+aqr<r5h9^RBg<u~lt?bxnuaxXGzij;A-Do>Yr?j5jq@^M3Tcbeo2X8fW%&AKp0*M^D?Y&Fp?kg|^XDoIDr~#b81P3Obm2ZDCRvOA&!5Y|VKj#C8a-9zF{Xdiu}JPE@@1<94XfJVQW3U;KiJBX^VMXsC?sCHfAP^4045GKW%F=b$le>GPCn)I}P23Dfo|iK8ZM`;3IMtj}xT0fg6j9TTeoS~{GXpU*hL)|-L!u6Lh(CL1a<R&*>#+jKdnkt4&59$r?E!br62N@c@3QdV3SATP*VRhVS<K+>nZX>u^QeY1qI-c`%%l5h<O9YeM9$p{!AQYLb!MyLH;ib;Nz8MW=ME=h4alj&mAOLpM%kKiB=j8WAvp7IWXj923!2A}?5)Ke-k-Jy8JwfA5HSda&0W92RI0FrfR1y78GsIV}5C2I8|lf0M6VgykhwAa|)9j$_4>Z&#kZayGuJ0w|(wh>jRVqr$wJKHc;)hPBIeTqDlW`0C#y%<Weh_cQF*nI+o<P9tU@NcwhvdK~ueaQ0+PZKJMmS9(3>thFyTcik<3ApCo`sMg{Z{Lt%%ln`CSGAoiG#+L$n5o#@<;Y-$Iwg*1AAjG33LOSVU8vOxl$uC2K}ktr(j!+kGmb4%&vZ}&|C>mLIOii#h(j6?Q};0^!4u-G?xSm2+wgU3y-w$w7O#8QWlhnfY)h|rP`W0ZN$%O${+%MpbAo}r0S|Nq!mpmp0Ceu~n{82j8PzGs-Iq$n#Irl4qoc2D)Dt6oR)k>jDigomG<FlNOsJMW%yL|YGYL2K@WTZz+w{)EQ2$H1+#T*$8)wIQ07<||{21S;MV`u+U+}dL>`FBsAeA}B%x2!EQXR94%)N}9N9!MEST<mvK&dU|5nJ?}I}&1KG&_}MmXF%ZGYWmEPiFAiRnyy4#^3ZsUb!*1SNE-O08zn<@aeUGJZoJq2T)|l<c*9EH5AE}5vgAR$9i#3s^E?w5MfOchtsZ`&y79z%ziEA$420)B!K%T5#8sDW<N{;rFQmm;&l^(8N38gw_YE{lY0!lW>%*go=3Gj8K6mBQ|cUpj%RYQsB(OCd_M!uK@6P|SmV7(=%3(<IVF)C%H$8-u!?<HW*Jla?MftTCOnrY&*-YG%5wYNrsftwd=+?JkB~BLD(NzcPbY~CdEKXyK^%q&Capkjws|KFpGYn9v?!WsWlkHu!N=cb%}FE`db8qReC;<RF)Xn?D!Rm7JR>E!l>rhTO>;g3LolJG26lz>Xzcgjo6n2DX>zi~_j4uR9iWl+ktCwt->j_JP}36=q=4>1Y8qWAlB0j;)oMPp3hA`q<Yk~O)JHc4X55jsDr4AwmRZJnMhwfP#tEld(iF8NW1>FaA)vou-5pskLj3u%#Ob!grS`MzjkRth?NB_C8f)3YXU50vSUT9M@!-|_{4Z7YBKvzROu}|LY49WCkF8rgwy|x1qfaX7^xe0s1mK2AE@?~!ov91~pGUv39AE8)j{JvAC})z?(>-Hrlb8E83cD{_lY3_0#+e>N<2xZl(eT1H$e}P+J`v;~xc@H`C|RF>3;K5$u2Ettv9{`0B!|dTU*#kOX3?7dkFj76w8#OR{Na~b*=75f23E?1F?2Xs$tI82EQ)_td_$PrnOZ+dK7`{ffQf&<R1D<w-wUX5lK~nxx|#Y8BX?ea?|_oOgcGO`k|V{ESZ9HerIQpmc%KJEfw?&)ui@b+0Z9R@2fSfF7A~p~Fd^<B`E<JN-Qlp-ISgs3dYdw!AYl+jMa-L9ZTaK=ptHXi(^&u885=;WV>LeGv^nOqo+h`U^>)Z2PQ~RG^%cI?9#i`Q2CNHJXaFo-q!~);T-aR6vC$=Lx^X3t?V9SeX772BQuApXiBCHBhCiyn$L{Eui)~zxQk`>|(XF$y2yd|?{FfjBjgNJK*PPjkr84!h6wt80<&b?-VBo9Q4LKV`j5EQk**CwSb%#jKMz^|g+HNU8lcH*cns!R;bd?I=!Q0<f<|#h(jT$WsgnNWcCZAm&<BOBiC0-76>Oj|~z&*c^E>0~<Z{cY+3W$#N71K|GY}!$#)Vbot=Vint&vnWcl9epyZ$T8PlvlE+_R(*C^sk7^Tryn(vSsHTPNp731{G25JL2Ggs$yi$+w=TQ<I;$WLP{W@7FTJx8<pZ#voY`F^KTWnN|4`P*I$&~W(Xm>pIE6$6LzT%HqtGr6zy0Y1nGY15d6JP{1fgxm-KyR9k*p)E*4(gkx|uHevI3x#}ZprYQj%wqN1`ILOl3K&@cw*WpROe`zBeZGW#6U(EJG8IL%Ku8-iiaATfS+#g|JQ$=jYhqc4b)_5W*VK*!AY-Hrdcf>pSpd#sd<Hu*h`H<X~6rwL1XIO^qlmdT)$i3qS?&FA7mpq#?$BkfpMEV$EIZ9pEZR?~;cVzJKQX5TMtk0A(KJf9)Q21&WgAHY|w@;!EQHsmv{_7SH#IsWR|o^`g^Cz6}P+a}z~?1;RF82JR*Yj_JVXUe-{W`fxPYo3_Z{C?;oa46S_Eqz&mthr-z)W*xmb6jsDBjsw7mVS9!0aBSjR+&OrPIr~J^vg_K6<o+^ycd`JqL=dxZ|LAPz=4#&ewLi!?twDfncn0)M#=KRzvo{&f>qvjbvcWLf{~)rC;vlhHo?7m=+bu@eNuUB1wgA+Owt5Q5IhCljTOb1W_H0S8MaCH;d7coqbYf&@zh>x`_puEW4oCyIK#3x2eNkYp&^%fxaC}U3De+SJ7j<Se`2F$P;r7;SyM?^hX5Rc(Fw&Bx?_a<c~9uQOe%lk&;{Wq0cid9sXb!}CCL$O&UK*P^=WDY*9^`cDR%65RCP27&Jrz{`8NQvi-~oxz^vE&j>=-^5ww$ko1`Y63Nb_^Z(Jh6t2*eO$o5(m2Uy+pM`!hwv|@6H4#KgQD)9*DX$xIh*rtalKDwoqwn(msA3cYr>2R`F4|N$KTwe*FAf&}z^7#)6;>5AS5RJEXX9@vQOEPgXr5JXSSXx{47^@u^|LEAI&RvN3@Ui!WO!L+Mh{K;enp`Xc+$=W>nk8Uv8e8iDVn|voS2lx)@$K?7`$opwy|(51Vk(D&4wj##{HNP4ThQ1=f;s!ZN=MX)MebgCp}-JQJC*3gZtW+}7_=+(-ryFQO6OQ&04`Okp$_<Z17K(aTes_$9wBM=w_lHm=5DFi)t1yFM%t`!jU!HfHwXNZac;@h3DaO0XXGKsv1usaWX={CIeUw+<z+b5)N}<j8C1S1w%^S3iIO_|*&2sX%#yQgQ3D7$T@H6QtHx!HYZ1-e#&2X`?s_WF-UJukiW;>L8L(QxxiJY`r@r6lQQ}wS8|fh`L0LS4O_!=e30eM<y7fxi<@WkX*J_Sv*F3?1nWE-expqbyEY?`$HSc^tovJV4qO7EVHQ{KzMj?B4u^lP96fhDwzD9-b+{$~>Vac2P4JBey_hSo^WsAC|FHRp2dE`gQj1;|-pJcXFbxPO-#U1vhaoCP{6MdVhMZej_VNirqZ{D~parY;y(-jFg=^uBbT}W>%g1wV7DCdksv0TW>pnP76Ur$Ur)Ufu?xFN8Xp~%hbp2*{-F5zZlG2g-Hh1yG2d*s|vZ-yUxH3zByc!5#VIH_nSbaMdIB9jAX+g5H<g8@Ax&Em#W`tHhK-rGC*nU*P)4>ZV8Jn<9WUS(3(#cN8*k>@~C;{x*RpqQlw5=PkTSqehU9c1f5E2tWec*P_NWyZU+WN>s&a7j9b@PG(QC|4REr2MI|0P7oK1>06i9QW%qM(`~JU>JI!5$4j%QId_mc_OZ34g9_TIsP1S+jC<9$?p<}DlRhv*a8Vnfk5qFxOl%Le_?=A-eEdgHJb}dGT8NHjBbLU)N}Y817yX^;29rY0hfvtNWKN7WNY0g7CD`&TWo%T0`eF4V^k-PFQX5??HPCR^%xy(K69+a{fgYlsI4VO$;GPJxluRL1ga=*I@z<#?$&}4X7S9xL2^{$!iGf7OhjMK1}L=<J4^IHIo=-^FW5K%l(W=(|Kb~IrsaK6zepXMdH7TdXw8Ljg-mTilYN})G=3)W9OKI@1ZqWBYP=E^rE0*ys$m$Erunu2R|vwxT7z6Udf#-c?Jrh;KMQQjRE$XDvUIp+{Dv$1UIG|+m201p2NkHXGs@Z7##LqER2g^%qzF$-FC7UrH)J~;!}$v7<9ucO<y2P}YGULPk<N3&og#liHy#gst5I=EJhqAa$FOE!PI0u}V(U#*2})m0-~0CsRHcrKME1E8_YsiR!+0ih{buY7q?;f%33_h|ELWvnehJf_n<vhwfF>c(P3;vtU7Fp++mdrhG^MJFeIbb;=|ep<Uikn2A)MF%z&2B6p81n${b6Blt<XoTU+wtORFjfWIs?H*uRzDhX1x%`OPbQ1ZSFA-SRqM_LQpUadQO6L=fSTtE2I{x(6k2H#)Ae51QBuT!<cT`H-hGUx)N|DM>Z}m@ASfk&y2YNIMa40PgVL<&MeQ7p0f`Xz<La)o84c#`z(`cweFWQ1X_wrot#7su&0r|!+;bY(o67<6!^nk+%LFwabayWDBLxR=1U=7&CmT7iM}8C#3jrK?bcFWtV|AKdArn;xkqWYa2lj%km`Adb~=+_ttdYs>mcym59|r-{FZ@uFx|KCd_H1_J>H^r9E&CE=9x~AvOUSduM-&8jJoe3$pTm(1Mtp0qirtqh9UTW@4p9Qo7E)Pu^GfV<0-#Z&XXtk_;X<ERi%ilzH7FAsrXF?47`--724B69?OJVT<RY_JU+HPFtte+g#9(mHN7hT)o0d*stfMXFSg9j%{nwV(m;D$F;JM7M6IcGR0NT4dyyS%!A9UpJrRS3H2rV?9hi;#(wb5L?U)rJzM}xd+vD+*o)HIk<)|f{5%cLnS**)kx;Cm<0plNQOsJko0_h&r^l7vq>iIu83yD_VRa=kA0jd(*1fe@TM4ucKY0OK@^e0|y7*H&DQ(3g*RT<y=8_z_%O+r1&%{OFs?VWsaNQ3kT{A7Ve3)Hok`fzvyaMgckP#H!zsG6jFkb8RjPEk`(?|f_I-x~O_GJWuNK#MwCC1Me+x@w4qeQN%?E*VU`VZCGYW<3mS(wN>XRH|slN$^{-@jq?Mt~bs`BQQXs1@N0!hhc%i$WmIQyjx^BSbNf;#-H~D89I&L9@lS}gD5lIHPC6twQ05JlSp2hBg)Z0)JLuB{)NvMT>M8Zu}s~2-(D~gGkJa<d+Q;R-DHVj>KE#|{BDgfbEBV@rxI%4%oLNit}a^~_@rO!O%W;qr1W!i-i=Yob|u_W=Bspi1`EQ_7d!p=!8TjHJiwo>o=`Uc=|+f0nKu{%U0~(T(v#gptB&^5W%{<S9U*aN73ZN)Q7mhw(8Cov92{9?zI|`LWLgVH&_j5B7utddu?#t*Mq72l!0|oV*?3?)hPP`lkz~OZgLV6CSC-!Ejr%Qgi1{vtR&l|h#2P}`fo<HQjshTufEQX;mU^->9E6pDlmc7ks>HSf2HrTH<ic*%Qtadi%~Dtd(gKvl2Vn`}51JLvP;)Ly-|~&&9kapoKb*VbD08A%LX^?^$3n@x9W64=f;@t|zpmK|S>IUS34bJYM8=palQqP68i75}ssc4v94IDKVs{1{(q2$c-K@ca7>~RqPQ5Wr&*-JcSMmvbWOk(BX0s&d5jJIrYVPi`0<XB4rW|>KSwgxrxbhQmz_9xj#v`<??h<3U`_qtC{)sfc%gpJJYy1m%qWM3Zqpn03CV{kz^vJ!paU(?5ZwP&@r7_Z}dQ>!;R=g=f7{X?oEp?kp4kWzkIdhhi(fsfnE^k*zA$VEcE^+IUINRDM)Kj*`M7nZwDFpZfI41~g@fi)t#6y3+Y1m=ZoF1w!J~ds%Ikupf=!=cG@0FtnHbA7!*Dp0fp)o<|+>7eu0M_nms0)|7yWy;aB&1E<cv8uy^Gdm|<q(eAlKKyNyEEa>jK&WknS>=$g~ch}YS7?=@Ue*#-iUv}>iCS&m8oPP{caZaa69^ocF4|zQzLu8(~T_$y@m;=Bz%1pah(MciFS}HOD@T842~%v>Z9hmDXT}zUIFm)`xL^)PX&s##{*Yfj7}QhoTdr;X0?`L+baRDw=&fM1smrFWA3NtO!<+jErmx`3lI=>za!C|wCsNOY}1*>%)!FBSdlL_><H&GutMD6PvUAW?C5ep&8voEw$sB(Pp4ARP`u89bLc+d9__U6p>5;)oJH&F4ZCyHq;_oON&E$kqu;s|y9$!Og@q7#p8Zyo*+~cXhii)~MU9tEkY;UvJIU(_q%VbF2?cC<$$Zvk07yN044AWkuQ~p%H9}}?FRa`KCfCfWS+6C1Oml#pBYKuL44Z&yjTy5Sc5Xk&z*)_QiftG&5bC75@Ctk^v0KlS8rpepzxJO!ku+J}W(!FTm$r@GnPru`41rnB=Ev>$JIcna@s-#waJUDxmBYo6ZJ4H?*9EA||8Y`j65(k&&#J2LD|#;5pyynR4ja~=mD{-a)S5Iw?>#<M$r1H?iXH>#Ggy{M4~v>JLhYRf-9#POFbKnt_5V$tW+8|AwPL}!5KJbzd>iE{DvQ@*gA<xNe;vSm6IF*`c_h(e$=NTVZQ}-uBa2k+mP$$&3ZEL+5lJ_mFw~vW%OgfZqzGZ`Z^YGVlr8iPcV8>vUGRs{122EK=wJ*HKd=g`2CMongDDF%>wzeUe5JZPc0#S@5aB!I@e8L9D^9LLcPFB<LMz=wgpNvFC{cclFI8Dk2psB47ZimCvtQGy386OguiOmY07TrH=9ZZ^FQTiX%%JM|{O5OTboo=2n04dOxO88y5bXtV+znwiV$gFzJm22viU0rr)2tAysd>C(00H7L()|MfFg^4hvBYQl0ssI200dcD""")

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
