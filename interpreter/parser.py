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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;TMY=Qe6N*0S;|3h-JtAmQdV>R^)nqaLew=?qsP4^0eP+O;!dRbu#2n<#GI5AG|XKGz}(GZ(>Re>CS>>4MgK*ypGtJa`_`Jn2e<v--ucyRfrhMo-{B5GN_jd$<M0+bp_<9&tesWfvi4ebQRJ2z@3(^Eh@7CQm*S~xFoUi#AgNJ`Q`OB63m?9GhBvu;p~T0UjKfNkR&4uyP92A=`TlEFKm!Hj&vAK`PtY!W3Fv7*x$K}p`55t$u0e3=qcV!Y^`j2bo$l){vyzT-0Ni3({X2&jw-g12E)g5&ta^d4Mj&rCGnC=O2G20ORLt*$xiLz7$oDyaD2mo*EG6HG}31SRhjPHX;ovZ)ob8X4JhB*X;3<5K}uo?rQ}iJ=_f?<F=7epRhWg)_WVF}LduQ(g@%O2QpDTNV>C<hEDRkd7(&7&t`QK!6!gYIK5syv@JDt5GlVM-`Yj91K|G9Sk&Fp57yBm89_6GIcoszd+xkIJHH4q=*C7Rz23?F7=$XJ1ANB0=tISP7`RaMXHu6M=di}^<|0N_oY6jdlm=;f}7&b*B7qhcpq~!UhNbrQzjcRzMtoQs+W*8_#;MeQ#XlSZ*Iejr!8w7j!<oyvaP1%^!4v0WQvR(=bmAHfRIU8N+WV2i}cJmU$mInYncue(*mLJe|UPTsh+31IzDpVY2lR{?qWFkUyWP2u`Cy|arhU`L6GtRuSP`Wfu2OyTd+tVLg2@~p(QToO#dw`%m!q*v~p?`}0R9h6V1gl_oDem|7+p<e2YR(u0EsKpv$A62-amq$M(%mALJ$qI7?)F}-FEO(tKlSQh&VOxB-v-9%dM8Y3xeu?%a`V2E4>kLdLBQH%aP$k}@!CT;^7t~m*}w7M@28d}{Wb`UAr3-`PZMU3Y9Ur(!msMdSc`I(ct<UcNwmNiR}n(&$>z1ilGi*&rIIq6NQR5C>GDuuKjP8)0T01q31zf2ixR}AX;8(rF1X0GMpQ7m+&s`WGjZ}f&CDEQHd}$kdLaRNfi_W<V+4t>B8|Ygy31P8xeS$e0`jgPnyviyYLGe*Q|kdAv(?lTQ0)AH5)!Cs0B_OJ$^p2*&RqC|%V>$z3IGOdXPk`7GDlCH>RGNb%SgoZ`&3i3V^?J4<~CG(@!tAeS-BHhnQbCKyWh`~#6FW(fLWP!(V5Sd(M-8Y5b4EDTTcRaEm3Ji34u?WSe`8jR)EH571r2VZy5x_AM>~h^7;RY)3pu{4)2JIpg+uzU+q+2Zn_Ju>3F#I{>!nuBRnfuasij#gC8_#FIfig;SnnL|2ryNLdqglgHvzWnuy$n$_Ii@l2~5CjWK-i&x8?uw&JdO(S`Z?ahz*7kW`EMaUFtA<-FDIaQ#73KN(+<tK641#EYO*eGeUVC(=`TSNeqFD)NKKU$knunZ<6IDEj5@jRCL2B%sv7lCMs3{;|nE$RdQg*X{qlVLLyGY;S<%CmG!yNp2o*k#J1#Jx*!seA?qPbxaqjzjkh8@FedcwU}S>0Y`7=kk<pV@PWOEw*7xY1W9Pq0Clqpb}S9L91^xHIrnYRRdgNq?Om2T>WD4UK!}LK6a`K_>}+`k1@<#LO<x+XF8j-aa3idLtrm>#GIO8EcCf}q?`)s?6{8OyNVjP9Kwd!?Eaf6T^*s?CtFeB4mI_hyLTrop(O%DzD&v_zy3Ga0AW;_J?h&2cK&l(J;aDE0`TnE=CS6?^i2FFWsj~ZE`zx;ZYF?056~>3v(dHSK&+PH%B}E6aiCl>iYL}RQiFTo5;T>B5^X@^B%?(Ob0K-(Ncoczn-R;l<;0@7|Wji?0NjZ1Y$l+mrQfN6%vg7X)`~qyC)X||GhT;X~Pvu=i*s!1%7J7PS&pVfhhjw!1^PpJRu)QA8ob`8Dix7l?=>EQsAJVB(^S(6?31Hg0OVL=f60U3b>NPWx0$`o}c{!G~JqcOK$$r>rqT=5?p~}2yuDU2#R;^B`(1i^fZQSoS-xtEV=U}wH1wH>>)VaT_YofWw%6vU5Lw=bPap&6#7vMRL9Wz}3yfO~v#FrcEIBtNgOX%x+$$OzdnY~R&7HQJG*&x&dnKtu)S3fxgP*|MvsF-iMz^qYniA6*UufkGq0B&+w?^X<veV5_r8ovnC9TBx?>5JVha(3z53RJENtP3kO1{0nM>G-KBo;A^_imh18LyS*snE6%vc;IJ??V2AqAq8xLLE)i&EQ{uNB!+_L2?)+K1NX-%e})0hrk<HnZR4hHbYFIvx$eZ{Eu9bfZ1PIEbslhWc(}5vJhzDEsi9A<${_|#Km|HCv1Zs^&>_rlyt(?+J-uC6mdJUUDaHZr1Z{jpdX@VxPvEWXv|TV~4?u<D6^0`~8r>u=IRm(@zX3?Xo4w+fJ~>S`BC-eHNpXH<)Cz(Xw`Aa?jX)jMY{4_vwJ(1(#3>oD9AX_x&l@oB?>=8?AU2NiIl|kTM3*I6+Di}M#B1n=S$;l*M7oMwd|Ksqa?D4cIn=6Tc3FopSNoQ$<E2pRM1}VfyMC-Q``D8bVVoKw@}&rwj<(OXc~m;i4F{h&=E!Jgl*t6->FOnN7i>!eGRM5%rKmM9MSK;5CTPiZepbO%4hc6fOs$uW;Kv+?hY**Al3K{a8)1nmEr>h-mO)p0_4uH!YObm=OI0$==O|Q|>$0(VxhUJ8T>@__3xc39i>lzKy$*xf*>oPu>e<Js>fmMDny2AVIXjM8S#uBr$sap%ND4QxgarKoP4q*@#Qt&pfJhHSJQB)DspV}sDrxz)0Gd~_JY|vJZ^4-4-}CU~S#S-G@9MamVxetoqd*l@Nws;vwE!s!rog$CX^E0Ui#5Rng%G6`%tHnK&p_o4X_O|~h!j*mOdKD!pG!@0Ri{h-`A=~HVc>3NEuCfD#!tQ5igorK4e|HiQ<;V)lC*j*k8#9Dr4eh-QJ>fMVBL<2*k1Wy{}c=KoNP*MbazM@9E~w2mi=8<hDVzH%5Hqa;dNJ)y#jcNoKBk7Jb6PUYbyClL856|s`8&sa_*_)VXtsJxoGecl727bO!MuTIpn+m7e}mgYMY_<ow{85?Ss?<Db>{CL@8QgX^~r=fcMb>jsK1z>M>_+>1fdtw8bxt(F`wWShUt6^d({?OuxG+4?Dvxc2Ln3kw`?;QD4O4yFx0O9KNagh3M+TSv7I#k(g?gV!OO4nuNW#@?~-<H7r{b&hte^1zH~8Z68LutiMY8F9X-ICy6Ubl|!)^Q6z@<QWceFu=A<Wy_H3mcq`|K{Ol8Y)T6KSI-nF^h2A9A{1UpJAbj-@LJa-!BpO^LQpOSX(%?1<$S$)iDHw_O4InW$v5+y_*sKP`U3V|Y?D90!qpf~sH}Jgc?6kNNE3R&JjJQZUzM2Nds)0hFL4w2dD^y9}{?_xp2LvKiph?X{=0R;J`YtJlMTZ^TTGL>J*U+ocRW)81ztEKyXjW1_eQfCnyY0K1(VBK5Y3H~Z1Na`P%JWBo?K3Q0C6}&6ZM9Uadm1mP4CwGMZ<V!6stzJtUIaz1xqFpAs@6T)Evw<A9#>kfvd>MaT}IvNV5muudmC8<SefsUt8Z8ZY3Nds?7%Lb2Pg_8{X8?>F!&Ij(CM%HC$+`ZN97W%7b}`$WwT@dl#W<7*+~9{{D@!XLm{M`ZXuhMBWGp|`gdZUmt?O64VvOBhTaQ1DNDl}$}aEMsCPm(oQ~A8%Bv=C42x%PK(n(CkdW=cL}B>MNZMq&_`77i{mI8@#N`erzWaW}>PYG`d?E@*ES@+?$3k|g0P^hW6gpoal`OA*)li39nzDg4K_U?odmSd^7bJzvQind(pxEc`>7d|SkVGSkeUkB3E6YM_<fo7FzUawg^>FE@RjX;nT<RnI1FSBy8M<0!<*tYCmZy4mrnh`X2<hGw({rI-T2%D4vn9s8_lphAD^)E4iebz5mVu|+od5NuHCdky^#p3Q8f5FoPaCv?-(a$NdWU@lQ8M4rO3X=fEM_4ui>I2Boh_h!O8c;`CqoZC=+T1alW(iPa`VmlWCgx<4^|Rj;7&6p)FxS_%hCSkdM9R`3W-cXspfy!xLnymHHPUD&<1cUTETPWg(<YcNW1mb-(~m)L3EM-+?c4;JLc?Mi@sd;8WjI1QTqa)<?DU!9M6}5zlV}n5&ZBQIy8&CB(4Qs_r5r8A?5)RHo4WuN+iw<V&8PC%smo5(FKR2d<-r%UI=5SV|5AVCfW8djx=D@Jk%_{o7-qjIa1aE8S?$3BNc_HLX86`?2#yvcbVixZ~0X*q@h2SZbNuTsVblL1gnj<Qr1yxWNyC@ykP21z2UMr5so=pR`lic;^L{rLT}$sp`P`KiInvzZc)N$AivDAKVbMKflWKbD;g`0#%<*!7VN@6M1q62YOW$&4Cek|A<GD@Mj~&+_^`agy9PI#u=S98x5z|gp($7VS7)rWG_uhWPp+KcEZQfs$K2`SO22D>e;7Co_2Ig^Hp*QG|MtzTt8ag{Do^8p_8s;mr^Ts%+WZa`cRGtY(t7wcoyr4^NZZrvbeb)nJt+F`ToM@oS5{zs965^ZSER8#yAa^%Fa!K#uT8J3-W+0b{OM^+fnqGgbnVTV*441KSKM5^_g&&*Yfs21Wyo$LsyRj^dxF7t{o$x|s?|>tNvi6cVPr+}_Qvw`K!nF$>G`zFR;^XiS5!3+MJk0Uv#<BmWqTWKumnNML3S`Z$R`Lae#yzf9CKU^9<F`!po-H^Jh~qvtJ7uy!wHQ%Vwg*tk7ZlIBwK2SN@EO9OOMb^ivEU4w3ICp>Oa4X%L!#6ka9mhD<JvvnsD?tc9Rf8rSiQ2{Od>XLHodkjn@NXw!GDXChXgMpxYz)>#7r#Aj*n6SP8g&g>5T_secOyH1wlrYx)4XIyKs?b$J3=*7m<`1H?<0QC(a@?IWxIaaUM;_C~7<X&3X?;cHt1F)MT4p&<*AxS=kX@L0Z_`{W{u*!zcJ$0zUN+)?W%Tdjgqro|r$1#`H~C$9GjuSdcfjH-Q<nTW~%YI=C&?_xLwvv2Tb485tbznUGI)`r@u2c;9>InN)NKYFI)n~d5Z)OvsJ@F9`Q2H917$8jUv>Fk<g|029k1se<G8jYri=wml*r(fEJ*`EXRpc?dEj3S*yu{$a;a&d}}Kw&Jc>l-?IGe25^O5HNDId3C~>{zI;j#`j*v2{b^W#f_KLzw7&zJE8N{LnktMo>DVq3|=O;sn#TrSTL?vq4vK345%&Pksv46m#+80xv0p%b4SoRuSE(ib!x{&_Q;>yx;b^MB+H7?ziN8aPY{k7j>X!nEiV5T?t?a7Lzl*m5~lDgChf1R5j=DXtKqXOEhowE})L#6YQV9I|J>LQH+@@!=0rJF%B9D6uCth#=0i?1is#1O=2vaotsy+L)nLE2?5}gg=>RH5ky;Velj`gr9kMb{#-Ht)OM1(W4dGBqBdx2v^q?MGszqMVK5!W)%s979?@8bZhXm%s5lJ;{(UOcwxQid65cw`x<2p`0kYe+hC*Um>L;W^8${Ma^7h}(afN#bxsKVv5u#^h``}Nw@Qo@&wwZApFh^pLAr;{DXz?c!wz<;i62)5WzP+L~e=WaHSma$Wy&?Ah<8qYv1VQ!Au<G}alk9>;T+;vdzUCEsWE=7wEEOH&8VDB?^zzs}iJnw~S;UR9LkfdEZoX^eBSpu>;?Pk&u>ycpuq@3cSw^E<a$P_kLWk~4@I#Htu@xX}kirSoZ@SLDhZ&hqtIh-EyO1B-6aP$2{)p!+T0O=cHrr@77=}WjxnN4aEDAfG&UygdXO~a8$6q`e8TU*NOdWm(IS$6C5SsE)bq6Ko`RPfLG}8!wp#OhM=Onk}YvFa}J%4UK@$mOfATt%2_==WJDoGAqY`F}U?dM@|SMZNIA@noNq%K{www{m`Y0#=CWUwHIP3V==8P#v66uYKXDsB<N%*usrERo~|HA6Tb_+Wj4-X6;uI?cjly=+g12p!bswq~>NlOeutlU<MU)pX(bwOjwU8l$%{>kF2j)ESk=s0}x^*xsiE3amX&)?eMtEJ5D&fsStiAOI2$w=&JK)GR7hC1Fye?}0j1d$(l#GR!dTT-@cwqKk-KNs=8vtqdP)(TKjs-g$26HY%4afoI!ja!M*mwS*!yG+HjjZ)R<?)1~E21)CfJc;Pi696_r|iaD0Sm2bhn6Vi@$`L64y@#InMP3K2>66(bte%xfIcHqY`Xxz03Z!b-z4K37h3^C?V3K5~(s$eK@qr%L(B_<lAoBu-n8_8VJSP=vXJGGA)Q`P&|5wy)&(xr4y?Bv)SXn1nzI4KuJ4n)24n`EfZuO|+D8(%6%N;Y|R!CMa5Zh7t@)1#`vLH?Ru84S}t=bxg9KAA4CmM|0rRNeUMnAZ#|gUK*zLaFK{)sugJl!sh*q`~#P_RQCz9wYlwiGR3;a2&gxG^>Io<-v=-tq4v0v6fbTxF0-V@*^Nb606!JcYy4vn`^b-PR<7=2SMdK5&nHrVX6mJwXW`heOSjr75dLkry-qXc&NzU(c2v$4_kwkm)h`g;zXqb)kJ@n*Kv;q@)&wE{@u|8PXusT!+9JNNO}~YGo)^u_0`0-P^aQ9KRv%PUm*bly{M8-_y)V1_!TDR2D||<^+>lE?x9gbWtL}|n<u+s5#Hm4sTyx%+9y6{#+=ew2bCq57Q#)koP1SBRPQbEv4bPBnSXg!`a4FY#=y61p`%0#Ut{IZvw*e4I@3~jR;WN23iY)T5!Xce`d8MXA_^XqS)t-A4rZ(qV5Q;WcSKxUDI#snASA~ckKhBz)jBUJn3S5}k{5Es^_)4uW%9~%Mp)h`(o_LLg#0l2sEw~f<CNH6TpFY!zio!OP^2pQzMRa^2#_0X(UCBu1Xl}tj+~=UxrrYnh)&Uo^3a-kt^*fAs?e>f1e<kpdBM(GL<DmtDAAWmmh3AI=!}H$7>pKJD5FwB?6Bl#KV~1Oe#3SsJw|#JozBHUYA?dYV9ad{x?gK~997VUAHH6g>=GTRU%P`v8y8y;+vp~<u-?Y?kHkxk*P>wLJ)DpuPQEEV`enM<VP?VE_~T#6eeh3>FVK7!=UKQ%1($vJgbR8V4W*`~Nm^S0@8`gp<tQvvwp1hlj(Sd2*<Hltzy=y-rw&7J)8m%Y8aaPVoS2@W;e0~n^HG+rBl6_&TVSwMO=WrMNOk2<_Kv&9+*02L5pMRmq%jWQTuH}T+Wua`3!!cFeK9wIozH-#hjCQ!Y^6DeDbg_j@1uu^*zB1?iJ21r(s@Cb8ckkHzAsW*<B?h1K=GW~uYs^+gqvSKr&9hdgJw1!`yoH*QOenI;6tUlK5krw8A9g#o5(JF02Z_9P6hb?n_~5(bN;rw#auChN1JYe(vvr^O_W~`=YvcE9@_tc9<u^I7)1FRCQt=TUl+<%pLU*MBv2(=oZvnUe6(xSN)x&p6HGyZpkY{25ni%!xBYdhwmf%A{VzF=d|BVTaJW2g>Z89iXHA)kxyJ3jHLa)@mFU<r;5&fka}Zt`C5FY}bh9x+iFI*TNxl5__M|enUa=LhsT{U}_<XLHk+{o>ATbU_{#y`#Xp`b_GU=$IFVFVnu?Ue_yt@iX+Kfp(FT=7`>P*mdhr8RkNGq5H(e+-c6l=#|@ZN4&MhUP^EDmG^p5aMMgL#@FxXbNJLgGV4&bZ{CDUl|Y#&z-hqdw+Chb))qnPAhgVl_#}F#WSdT?FEK{5P&6;s0Cob_jzdu>^TG@CG8gt=Zzp<2zCiq^0-xB7OQLf7_~aE3b~~ovAT}*@kcqV(ZU&BVZ$pe~&QLAL`|!(tIVUz0+jLBK41APzRoc`Pb{GOl0bt2%^URX-t8|2c=tet^QH&_-&*$6#<W??kY^8uwjf^82AgCN)HdakAS-Z!}8J>I3LQgzU|umz2pBzZz|Wi7|YSw-!6~XMQ=hI2V(6G2u3*oOHQ5T$$wY=fD74tFq6R`?pEC^F^KvN9IU3!%|>vv<rZCTOO|Ni={-e*=BP0R%BkD*85hF;VV-Fe{%(*qIR;v&)YDq$Y+96y)Ar`Edgg=lXgf$j(EY=$#zZV|PtrJ!{euida`f*wKJuI+xtS1w3NXKv(|cVm9h^VQLKJlQSyZ#OV21DjVHu1h&a%haJIjk%cf8yO*%n#@K*Zh@PzV`SkCw3u>xXN{yi7;Sq?s1-X5UC20(C$KYDJnZw%OjqAj*govA%Y)3crRH7FzU%6gV(Xg<zH}{(^NUDI1M{VDI@AwX3t0cO9|ruM}z0x0)&sD_d&>GE1&;;SR%`MkrYO3EzFQ?)bF^{*poE`SBf}aCU9Z0UF;FOYJ$CJLk#<O#cx^RbO@AJ^L*p$Di`{2Ba990|IuJG$4;70|-AebP(aZlXyZHP>Dg^v4}Ao1y*@n))W6(GxbWCh;sE)xQKv9-Wq>Na7!&DGhXim>Xr%!;pZRMT{oflhUEGXQY6g{pWTlcUkq7rXY~?0Xs0s63Y24s$`KMfKw%D5yeZ$tLfvvOEH%%;L2)Y4r>|b5_vku+$>yuiZli$}-0V@^$OhL^B0tD};TQDyLhY|B;bSowei<hbZ>n>Cyf7(f{}O04(oj8->noCR+mxiRGty=n`aDu-HlZ@=6K$#vO~k4#D~73oi>F#^dhlc=4b&7XmD?SwehjMpLu01pg&*p(_Ko#~id({_xABD%7C!2uB>VJ!)D4W5sG+VfISmOE>b7iTYKZ*dya56NP&SrTR-M;KYdo{`LcsxA*1<fBdL2_#?MvtnHHL~bSxDrIn*tN2IzR`Z-^7mP0g};oR=mgJ*(ufYn1QMdL)nKP&>(9hWSHFi@&iPQZBDTjA|WG@cU2yazlA>Cn3scFgvhl=(IQ_#qjEnZN$dy-g8LXMSA>&eX6Ck2OwL@xzWvmWV+zFZl7p-d1K6@BO4p+e_sN!cRGRG<?wYy|5DUvi^xcuik9iUe7522tm<h!zsO3)9?8FDXf_%BcxCnWPJ#c?5@B4R49yOGJ4Ok*Z)|)^t6Qi_v00000z|U-%EeW;500HhcjIRU$(>1-&vBYQl0ssI200dcD""")

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
                    raise ValueError(f"Invalid Syntax Unexpected Token {curr_tok}")


def _attribute_apply(attribute, popped_syms, info):
    ast_types = info
    if attribute:
        if len(attribute) == 1:
            if isinstance(attribute[0], int):
                project_index = attribute[0]
                instance = popped_syms[project_index].content  # project up
            elif isinstance(attribute[0], str):
                prod_class = attribute[0]
                arg = popped_syms[0].content
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
        instance = popped_syms[0].content  # project up
    return instance
