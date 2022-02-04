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
                    graph.node(str(id(chd)), label=str(chd.id))
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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;X+d&=Uo6m0S;{$t{u%=x~#|q3Hz-!-dfNKIsLjaNtrmy5$H)!qoTBFc9U<Q71sDpG*a|GAIM_J0<nDDf2wj#ETlrWsxh5ECc8wS)HgoH=yVk8g>j4fLPf1j%_B@F{y}Gvj)gOi{`$kAJkSdnycPWi$VUmnZFgP7-04InFEK85DwJ-W*l~EUvs}5@BKx$}{zbGFj#l4G9?#3Ro=y>eNK{xgMgFr$@qR{b5fU}^2@^x?F(A0c<T&?^k9!S2u~t$n2@$Q*ZLKtI)6i*@2c~;to4bZaMy&F!C^RX*tH-i#5+`TR2kd8W&B$>a^TCB9OO{q$l_itt!6n&5fH7N@#Zx$8GXd}%Y*@49V*;N<6XzwUCU|wsDt22Ji;J6$m7-&lowPpOSx*|SMrTsWF?#o6!2St>1o(*$`4~zpQmdu?Y>rvr{rDFcH%?FndkUjh%k6|nN9)sk?OBYmr}6s@PpPQ_b>mkCStjeo!`^M0)gr(eZqv&yBeZh1|0OQRONHbtr~SrU$~+xZR$bH2&6;MKaUaC*oz)DUr-6(2FSZcLUniD6PT$&wQeT9OJ&<Fy5gEoCChhc-ePclHZF*LxaPFiKrPRt8*zb)=hl|0~ypq81PY2KT$CX*=I<jt@UT20<2*Nny9<B2idrRua_=GyUdHopCkZ)0@KYq=qK9}=AGq*^l5lp-;%#NvMkEKa`2!0B%g#%1<SS@29<@g=g>cL+<FrsvHiNaK`EBsM}?fBRm{wxmvqFGsgVIEOP91$F@1L#nSRt!W4g}vXuJ!X$BZ?<0iAYYyBE3`%9I5=7`BZPBkKXVLeewszeAFF1-UECto2{CF4+mvCfcDHGXbS3pCz!&8#4^ajlC^l0;-pOk9=c)ok=+&a&$L^T!Y^umyf9mdi`_CSr=A{bvX!7luJF97^pO{PC$Ck=QtM@7s790{?<%S=AEKe9ipkivMkDmWlPR@V|f(g`58a@uw6KzX333sk?Or~~jb31u_AO)CezK-Z3*XD;GgI|=MdqvP7A4A5ZD(*Og{amP_NUf_-oF)%+7b2P?dK}IpyS&YWQ0f6I4cwTe<06R{__A}6%Qb=SoqqC)1Bwg2-v<|Da9f&gIH+y=3mm>4W*NsvsO!88g$m=D9Bj9)`rZ2wwk!aXM>yh?;<tAQrut7durhCezA%xV>0^-BhlmDKeQW6$%n}eDP`(uYW<KTw7EI>nr{<Z>j-HcAFM`=uJt)H69!6oBw@JJVetR37dvjbGSWx8g_V~b|1Or{<<job1mIeUcu<M5BLIy5e9R1kK%kirR@Hm5NokM66JMT-pUejbDvURS^DDheP4`ABa>RWBDQMKE<1Kmg#_9*0yyV%5_syaUgYKNNb@sq6_8h_{#BcK-AZ@?>tmUO8j93(NEW~fgvU><$$sY1<gSmmqM*ogGBWa*yqX@OcD{b3!>oJ4XW=<>Kb0+rJl#OjIYvEFB}nYcbnNCY#Ct{Y11<Q7HG6*<ZO2(KBI5a`Q5Fnk(AOhqxf#q&zBdPR}ED9E6y=&@n$JD^-Ab_id!X$$arP`;!G7m2qPhD%h`aw{`rSM|ILTPqos{iMBNP8%+CYDmnx#w+<(IFIXeUld|KOs+-Fjs?<kN83YA<ZaQ|E$E{U7En&ZIsrCB^!xr7K%|F17?h!UD<CYdN(+(%7u0%Y2*5vve4>(-=y;sbG`OqP{v?s<a6<AmAtbY?18Vz=A>e|2&eBjJrKF%M(_*dx@nwBc)cV!{ss%+f0~~>_{oYvv1lVQ;5f893T?Ci&e$gW~{QJ3>B#7K0AhlcG%mK$ff)(aAuupH>%INLzTDda9ZC!De|FcdVc!Q00{xKp18x=bVf&~i1F<^0X8O@qUFvJw4GZc%N&ctBUs+e_!62l=2jx^aQrQrx@5qBhmyMh!XHHHi~Ln#*Z7~)t?kHT7zPfoxoHr1T9VyFGX`-Z2ZpYD}?Lj$cKwhq`kF|zMlyE%m5&;pL4T-=wvgG6{9g^i}udn|ilXf_hFcmcE>Ci3n$60xPwM~b?X5w{Z%gQ}{+FqLT$>DWSo^x_O(F|B03N$1}yaq;~Di_D>DC_%W&*qQLxCzPH6MW)NAB9x{p;x0>raqb{3=$j1Jr%64{ys&~v(CsihkAr0@0gi7fb0@Kn(7EH#=?x{PQdal}RUN-s*>wLK{WLjw2<*B2QD;-Pf76_9%vD!dQi;E{3}WCA5=LLs_~Ta;8cv$~48xCsnDT8f2nisnTAJSU=3$l`YCj#tBpeJU>A1HmKne5%HP?uNn*)h3k$FbVf6_<pBlPfxu~1XVF}_>NXrcty&+?ci9)J`U38cr|J-!1KdCT(-82xUqK#v(NjFXI6p_eJen0bps8(-cKfpHV-yH!Q=|FXA<yA^W4`UwO{2i;<`#l_f3pbE)@9~3Oih;o;{6442q2w7%q#LIN+g+G7)RN$H)-V(rz;mXaIn=m8af#VpExsYIW7yxgF?v^(8Mzd&cjbY;wvX@Hi5qaZBXt2gW1pWT44wmT+ARy2=qFb>1S!oXeiLfRa-F>4gxHE<%@Ajp@fvtRkS_tX6UIp*uqjsKUxec}-v<qY8E+p|u)SbOdqLF*jgSCEAfx_TF=T9BH!yymFf!&J)Z+qMha;GMxJzqEqt_es)0ETw8x%Mv>j{!0ypswGyRqu`cd|gF%7y;jwIilY+k@`+|32o7D-I730TB3YNc&!_afS>eU4UNW#^4ncO@fym8uO`s|@s4&0YCLVskVAB9y()9cIx_;ZWrm_&t|jq@$3YTcnKJ*5i@3xglwMO_(L4Gm*O1c}%#&y&EM1N-s+7wjJOX$mMowGlxB!kp1LiJUX!a=!KyKgYCBZ1~oV)g`SM-w{O=&!%l9$FR_`>a-ZhnBUnih3T(0=izE;WWI0Jv(8qx|HN!DB*7^a^OjHEStSFnzmvDNR7|r{GJ&_zks2Q8kAwCP=*qT5~RDzyi$k83QLYP%?7UTCk1fL4^1=%XQfAn%3=YS3=#auEuqEaDqPFp-%c_*IYzU&a%w_#nb44f)N(mDtfN+rM8BYvQ{EsdoNAcFtl8?eRADb*QtzI*0*v6&;&~Jm2BR|%68Gh(clhhw)Frjo^ev`2UDeiB_B9Mjip#+L}__9Xon6jSRMR}<(w-s9{PcOs4#H6@3zQ|CLk8PE#~)bh=$+vlF)HkC1;>m3FKhJRCpefbPhGrd0Aaho^Z+`dHOPEGC?=4rO2o&#E}sML_~-AjkUAV*N#G(x*h5s%#M*+8vIW3Bi&fRTQnD%568kE5pPu4<Ad3QA`ESm(`^y#w|N^FAQB|jVLeDT>K}ewxh<Rm;NY9e0+BJ91L3idwEJgvg}<vg$d+Hd)2ROAtjTxd*$NgZMklY*BUa(@@;X`EEI*VeJ?~ndy>*E-?x9ewjh^b0#(S01vuHK0=OeQvga|$Cn3etd>G-8kdH8+_#DGtCjY<X*%j3KP;eGT=egaP34s%!5wrQzcbfFJUWNpUIAb?r6JFRSSP)>I^x>UKsGLblwX+cmvK^c^__R-EA0-&6OB-Dwjfw0=5RJdiVlku!H9?%*;W-B5%27{QkL`ropb8hx_FQqkt4O>bG$6GvMPqRL|Nw4g*AZb65pRzWPBK`Q{G0!0?Ddn8;L*STe*qMeM!1TJxlL^VUjNz7UkJAkX=o@6pr2-4JjfIic=x{ldh$L+XIS}Xbh`XzeML?{^Y)JL`MJ}cjtm6cDP>#0_K6#xEe~I_Tn{Nx`Nr8YY*mpvm?{QUFk`_6HYmV7B1H1ec0~bmPo+$A=n>jE8qfBePSbnEDMhpTMb8$vL4>W5jSkEZOlUq_tId>UnwICYD(8ManuqD{Y;eo}F;=bwK!&;`Eo?HckdUP4>aT@>F2IvksP^_K4c00d)!8$XPMd&&J0+Cmr7KlPxYbO>wCG+&zu}Ay(GUuhZWxQBFe*YerEZQJApPyreItKD$U%OZeGsH=FV&vEM_(tG(-W@07%OucEdO|T4XG1db%V_|`MtA+Rc*8$s6m5EHrZ`sa)T5L&8W+L|HYGseji%|v;E3ZGn|YAyPCg;sN)%g4hcXgp0UiZo4D>owk>Ypc9OudoP(jMw1z;-%XsSRe*Ss4s%^#_9{9ZDRLSCu^lh{Oa;->P$Iktys|D6fGY9rZSyAErL=pIF$IFI;KKm65Hq6{WD-Gz-qtB9)tiY{>{SO_up4$Ry<9KoRTNLUPsI#yTIp2L20cW1+l4JPjMXOtTJCgaNq9u277ta{UZ7uLj5!z$iQr@83JH;`dA42>=<i<w|{U^4>0l2Oefr<hCbl1`jPwr~Vx>s2x+S1rtlZBFuFh&N%}J6vQ{-a`Vk!kV`*<{ao*%_TzuDFON-Jny$o0dLHBO}DD8OOy7U&drhlc7VB08*)k(BUV|$%}Dh2R9GT~>lj9}l;X-L94_yZM`*UFb@colF3=6T_OXI-btf*eHlrlv!HEJuf7d1n2BXpv$F=Iz7b0Q|SI%X;JcY1F!KgD8m4QzHQm<W-M3B<5=yLS}?Ceg67(uezwR#5`c_@otw_lPtVJQa6S`*J74i<^f;#W!|PJ;5;`pY9o)q|Ce-VHi!cYUrN-AVJ<Amyfk#PyS<_!c9Lhma_mx94tkn99%>cNau-<I+3OXjOY}z`=jV-$B&h>t&hK%{+bTA9`gD9nZSNeL{aeqH80eIVKgy3@QvLCCtd-IvO9tHyAx?ip6Qb1tCzQ)VJVRrX7))wR3F8Ky%2uoYof<<=&V(M@kYopXFpC{e;`LOB5=r%qUGAcIM0kby^|cug8^BQN;mgs=GuyRK{77;rwnEP})a3MpWrZ$d4^b`*4>gFMxnP#$3a@2PKD1`MmUzN0`a{n19Wd?3yq5bZ*OH%SM=C3Rb)epNM;^s!@?{{O6AFH;04{oM7?8q>G*Wh97s7NKOksXR~{8dB^W%JvMjy?U#)1h&dvF8Oqe`wS_pS-{?uneFy>Od~DK|k@gFMMpez2E}KZWu%77E|9YMD*k*E7c#kdCldTJ}Qf(&^^x2oxq2(=mT`b$?AH^wXI`z7RAHKo&JJ%K7VN4N)_8U^>-0}rq;%h~M?@s+9EMXgl-VS*BoIaGlN7j_cWgc5iJ53)qD>KW0_3RcCakb5m!S?-v@l7BzHK5Mh?<p74A)5uMw5DKTkyiNg4MFp5ZKo4UN8p$F53zB%YNP<Hcu$!}0&5DPd-We4M83I=jZ7j?1MN9@L0P@F-r&}}ilCr@*RywWxM9a@(+d~3pLpecC;HRkI?ja4;okNA@_j<d=t(8aRw;=9ul+bq0n+b6<4pF8>L&(cLX6{9(va~o2yb)irMz3Dw%{&`Zg5{;R0-U;9OKZZDTcf(k?sH%9H)!FfUu_@w$d?^Rh%}E=x>Ujk8TC|+{*jrnLpCdoZ#2~SPA{^dxV*@ne|9ssx(v@ym*vJHIbGwe-a|y>5;+B2G}^nH<9-qE9Li?3@L-#9=k*;Z8dS1G5(qvJBeI44FY%tri#^+fYFOC!`tROO|Ec<>knovJa9I2Gyc7)-%G$w7$8@uqBxF#)rIQEfQtY19O!&9<>Hc;=lwF@JhC?h3`fp+h#o2TO`yLMm`e#+i+aM<vy{+qOx(qrkS|uLgkdESu{0!sq2>@$(cRn?RCO*esU%uvMDxaDEZiY6yIM~dkO7yX+NA>ksMNV2Pw=0@7*p?Qu?KLKYja5-a1RcH93)ML(NLO*s;X4O1LP9T3F=2WabnFabwmu8+*>l@2OE;q+Qt1VpT72NGrcH)JBp4cyni87cg{AO=h-bL3olU*PR9RH|5qNi5dG0?uA?21G6r8ClWrV@lss%PTx(xn^8qUq&pZ|8pj0_0Z^E=K)Fwj#`X-QV0MWO=FsMANx=Trew3V2lbPP&KJEH-*kS-@^NE6$g)c%6&Qu8wLTA$Tp!PF51VBCq7ZFfTM*oi`ayd-v8D2jYfvn~>NH}H0={3a8!4_2G3=N#9{eTr5fFFq>u@hh`b0;kPLVqzNJQ5iG62fJg^a3ByMX8$yi&X_#DZb+<z6x<u{HvLp775i4rGbwS3CO<<6c1^EUz8UhP50~rq{ZBDKDq@6HImMtc)+Z}n;!IsnVIhvd50gS7b-0jyQ93>#^_m-P;)|TGLBZ6n{=oJ<7*wxfO^M_A6m>C061Z+Jq%gxt7t-0`Yg0g99^FYym5oT^^V!F7z&F^d02U<763N;ZPJtNslnCyE<#$rz);)l0<s1VeTTX%x-p->$oe92n29uYijy^$iwdo=zTU~TnYN@>g1A?Y|hky4=*#OrqDI9`8D>->vEM@bX;TAvawZ@pyzS0(MGNa?pbi}4cW0xGj2w}$6y@C1!%ELtfsA2JKQ`-&r!rULk5ti_spN|c62#N?8{)cU}cU;<YM-$JUjcxCM({D~Nj%6<0<t&%BEKFPspdKC_X~a0@QNd>7%_wtkI&5L|W?Ytvyrq}l*B*AENX<K`)Kxi~PY08*-;0*kIzg9ztnj>f#>g?=g)0AaeKz&w*V}>JQ|7jELcBv6R6Pu?qUFf}G6Jr*B|>>uVwB{b_TiZK_f*LDw|?pn@O&c!L9BS|Yt;ldc_ytZyMjRR=0)CmK@j%8S&XzdQKC@%ZOsF#PDCVQ94HGxbFM3zFl_h`7hK`ele1{Cx6hul=nIN!^a2b<eUx?;SboJW4RT9Huc9=9P^HxQXTo4LhdB8MmUR}?s|FE443>@@yC?J2T9+xcUMiV_C}xSB&(VPk#ZUi#nrl=Oq$tCr9{wge?Y5_N+H1B7Cc!}?uVMXqf=6WCvCH#~+cfE5=M)bwls)T-*8rT7WAQ7rEiCHXAfK%6THGM4Y$d-Tzz(kVwe8Ij79_HI!Qa=1BF&7R&c@)$fSd(IDMHrK;J#uAEm+`GQ)g6=Z;txaiooIx+x*k1B@^U0=hCN~cdxojDL3psU*ji?%KU+&@s|Mhq0YVCh<|gr%iw-+&@^p_v9Bk29!K`|q-1@X_$9J(<4BGQ`_*L5wNtDMH}=(?;t^;DxA?hQyd&gT81uK!kpRNQ+3%Lk)PA7#6-=233fcJP?NY3DVg{cabpz1u-?q65n`sh|aXDQwzB*_xKs?Q-ap9}Q4~Z3#NaptFXP>EAX#Or$pp4=`ze6F)!+^7p|6U5r;~Ay5Cce<s_DUs&N&!1*LQtG28M&XMSmH#d75um(yyZT*y4`djUdAbxC>@It_%0qcG|V0yrm;!0A)tqyX;l1R_Ue_AGMoF79&J8oALejV;MIO79;rp>OpF9+k$>4Na=-JaFQc2yL0vx#jeJ^ehjV(ICml!|8Ah6IKBNt3BK<+QI&P`x%F2@pp?XMfHj4ox6mcFB_`nF>hQ|F<kkHM(s3n?oCG=5N?<EjLqW0&OR2)g+3F8q}#T$uQg6>;xjFA@>ML*ADP{;dDW#&np+n8bp6JHqz_?DZ|WzmGWt{z+VmOD9;q;bQ_Vm6nHj}(b5yUO~%6(5s7w`P#IF=;VJSp^7YY<KVDz2Wrs;d$<*F^ZN?XjLV#@7&{peTs=)#J@<-w@YcM{C2^qvIO=2;l>w~gXF00z?$q#%=)8@W@`RF>TL>U;DlT%yZzs-sQ1iGEICXeFL++_pSq0L(7^Wt^0&4)2MC+h`}FNSuT7yD#j&pAnMN{LSnIgz<)D>_Y?#usUr$#xWCnwZVW*vk4e_ZP2G`+26y;)1GI}Bt3!18WR8Hn2ku=wmn=7rkQh{sVr%hwn5~1U(>g-FYosgr*zPx<?2FZTuENKQVq0#9D_DRbD54M+RM<L$=;Nd8)r%Yev5av2=ncM=H2|mD^c|U+hTe?xyF*T{1E$PE2lgJDp-Ph9oGKSzyYSO1c!yuOEPn8pPFTFUgs!(XAW?4)Z#FIua_;Rkcb`v+0+7r*dvjbhhJ?vM1`nlNAK~E_DDFq4H`?Q6!)B-!J8TopPMP~O7PA~H6d&ZlhNQ`U3C>p7=D$AV+;Aog4dF$j0(8uVM8rU}5YEk0YYKa|;aYpe)TP#r)&j1^<@D~4s1S!CJ1q`#qocMe(gS8{-FM@q;*`p79Y<`};TtYAD<<C#JYZy=x6{q7~+8p^RUE9D%!7=sm`xBH!VNC*Zcz&x(Jw-nnL*+>h&tBA7tv@qyqz2Z1!ywQy?(c(ZkoKb-Y`$|?ql#(fZ!=H~Z=s-Z!tH8-KALVRmxd|uHPzSrj>kM&N?7r=G7y>}+=~~mY7j?gYrJ@xr{$c4neH1=6?yQ&H68fmI|0e(gTOUE*@UhXr7<nq{}&P^pnnFPpEk;m(XJJfU?3pxxr!>G;=Zip!<{xb_G)xqnfVo`{~b!Js||1dObO?c)c_cvUE6cYkKi7Ks-I=X#V>`(dQaeFhJ^k&wERDTpjl4FzeUS;eiY}xrBz@RUM@t)acr3y5uQgm<;-S71zfl{V<e^y-#p-gha{S~*}Gxbi+|7Y<i^|e$bp<f+2|xw+h}J*pIAcl4VPxu_mt0K2urNHuWz98P4Sh5R;oj97O6CoC;5c$u7ue@$Y**CDqB!)6mz^nbkOGtNID;dH<)vD5%_Hh4~1vn8O$s>coWmxR|P#o^SpPbAf{6yR^P@4d7a#mwrlv1aYkO+4FAtEXP%{@e%=`l2-6|;s(Hqa|Cb^K1f1!i+~jmu7<s7<p6#c}SR<Q&XD1^)j`I~5I}3DYxmro<u88}(r=V>Z%Z&P($VUddwf0m*S30jWj{Mp%MX==o;@9f#nSWd|)?rq>um`LD?iI9j?r}_)fC)~bOK5Q?JZ)Xz75IUTf6}uqi`E@ZFCS|(CbMH^y634)MWjBxoTjDR@bW@56~2U()@YzpI^F%SZ8QKGBUtP>=%Pm0O(v~&9;8o@?BR6Lv2VZCYn}HN!0rb4My+-z#Z>&mw+uFuJt}pW&L-TxoF=d~ogq@oKtIo&U9cIGW|{mc{-vlsTmH-Sq--F9rSzjdmww<(pIOvlD`;E5;Qz$(eALV#Q6CDC?Uk>d?JTW8qs-yQ1>Y6a68rgi%(KJFX;2O~<K}&nd|F%w>h*6)=faw`=Kn>NwH=@eG}YCIcUqqStM(*`;^`;E`o~$v&PKwgaFD3@SW64klc(B8f-|ppVmCOj1-x^9N*|<!r*(ac0w#CCR(2Rj215$N2cW{@bML2>zY_D?uMEid28wU%)jj|a79$eHmI#iQ5`}5fMo+76V9Skh)+c{4>-^(mXhQl&i)YN<%jN=s`~wmdKRhtDv>`dk1Gj529LEANQV$4LgKxIHrG7MTVr^VITqFgV1Wf?sp=!;8X({sH*%~&7F!EIRcaIw99K}E69UYj(;wz3?{w2E4vg}$+ox=qYp{%^mY<3967z(<i5{Jqlc`5cntVFDR#`K~pyr4Wd>?!_RRU?Ge)uh2ZkG=XG%!seGzJ0mjD1R5WMeI!%n`>sr(ah413T~BG%?HFhx!z)in{B4adwW3P&taSb8RD)7+<ogLPeO)EC$buB&U1i6A-ABb;E_{RJ13v{;3MqNKz-5sJlo$}F>90*UgQ#nOZ+Wh$Mf&L{;)27L%9PsMWK2ojJaEP8N%Eo9$os<HI>zu8+QNqlI(T-O5PT)hs@ov>7b72G8YGcPHM8r52BTn<Fy^z?>@0ppgH^*(q9b#m#%Tc%h27|Qf@H!DY)D}vylZx{P`VA%PJlaxuqR2vMxB2)WmpJHtjhLI~Hoe*Dd@Ah^==xbev~2KCCO7RDMyvtl2ps@imWnUBh_)NRVzgs2_V=SGtbIV-$BC==%2$%)njw4OO!WwR?!BkH`_u7FVHeHLURJA5wmbA^u-(&nOyBAQ-$YW1pwUfg$?al9z&94Tz#I(wS39vp`w?)O^dEQ#Kr@u~KRco5hB$M4YcI?Y#hy5Ie166}nb_wxPXkVBxT+dexe?POTQx7cr(iXI@aOE!%oA0Bw|wGz!m)vrtwT#G1>?H!4r0oSu4F@fi1UF7a#onnPUxJ|2au1jTAV3M+psAyyIC4H9`BGsZ!+mkZijO$8x<xc>{S_3CTi4yvF<y8O<?2r6jhm3iq_bjtnxh-vpLQeJFzV3WWc=x*WXT?&wa2b<*kQ^Y#tI{^P@O=VS9od7apqRc5m`v$2Ue<wn3{$}r)(U4(;Rvqo^&6)~Xm=}3+!s6XJ;h5Up5^7K}0B%!kMP~|m+e4u_B{=V6MEX-Ix?#^bpljzk5|$(&3&Yf*{o@hS3>5-0KqRrJ*!t$=g)o#nD4T<>=sjx88%NuuNU`pX&h^sLFnUoPdc71ZnK#b&PUDD+h8E?8ZAdGs-zqkWSz&IvT>GB`=tJR3C)iDbN~zB)o-G+K<~Ly8&jPB`J2XEau~`NXA2@-OO5Mw44Nzz#k=%5biu_#qDwxgT-b5>aT&2*ltZ1;7Pt92eg~W%wY9gG0(Edy<@^Zh{6L0bx?Bx*C=LH0G>!c=ZB;4TEQPkp_yD=y5(`6`|<}!TXnrp%zsk@dkp~FcIYNr|5?#8-K#-f+5m_ouo^_sg<7PC8{f2N)grXqxv%#f+y_0)Y8bzt^<Gcb4z7z=Qw4pyDg>Qos(2yzxBIjI*pS#|O)aRxLv&NDYvOu$47jdw~DNenU)Z0>Q|pW~3)Mv*_Z?p}I8O)(fT{!>(NzuL%=)h!sUQK-$`UlYt(&y0oGr&ckUb16s<SN#mYpU&i_KU6d8m`ttLVdeVsd`;X>M&w*%Elo<cc`y=y)xse{4;TtS`&h$WIeI~uqk6ItWN6^Zd`MH?-8D20fLQsXN`rFs)B+vTY>_%1LWfqF$`pZ2UG=n*tNZTIl;oe@>|aH|^Q124)qXXR^PE{02ekkIu57w)3<PTc00DzS)Pw~9RnR|6vBYQl0ssI200dcD""")

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
                    new_sym = ParserSymbol(curr_tok.id, curr_tok)
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
