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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;vWGj@?8Kx0S;{*So@k!X(!_$dkC`jWrr3R=U*#h26E`Nq<yw#DvT+=UzIDL7`}m<0`c&cMIVm)q%ttB#GJ>^Lxl&?KpnI%q;AA35|MNiX<&TPiC9=s0cwaE7bba%;NR&>pSL`+wLfFudHgj<VEYbz5J8`ErbIBsv>V#QHt(~6X)34k8iLCs87$~Lo25zQ_+O?`3h0J{IH`ER-uAc0yVZ`JYK-f2Y^M~MAc3aBAgwIJpPe6T-$MK)=3c}u3;39)(44<ADjY_A{oWd*0jH$}V7GWjbnCGt&_$eZE}0CuYhcJG7mc|N!lRJECgB<FSXc=eKTM}j$9HRJ6)aTLJ*Ov+lLbfes|0r;tJl5-1rdYGTl@avs>&|Ay<bbdI%YlTc3mQpvd^^SPY?S%mGOJIyiMw(vzRnHc$132l?x**0xP&^MNurfaZGZ+ORhEYU**&w92$3d#OKG^)eK7IOEk9l{Xb;sxhH-hHaL_oWkq~MxGCKyO4v45!ps2>^f}HLm4ZSGmax}auQt&2B>*T+ucGyeQ4nCsGHI9KJzQkpWTwMWs#*<5w|41ub{H<uJ$!W;Dgz978&_pwNp&kKHm8sFuar=_hR8XH=Cg5wn7=;7Sp?~%M=nY97|B2~acG;784buIhS;iZ<cZEHn>k-XUs?*0!=l?K-`?5VN`wibQl7jf*FA)mAJSN4MD4sBX$3iy%!}v+>AI;s_%RKnOdPYt$clGhG6c57Uy{|65&7&Os>Y^DK<vd>7k_A7#GpGygb;g4O?S$V09A=+cP3{b+Jq~AojLC=!TblbzJ4t;%vy_|7b@92&vw&A_G=1e6|!OS{4FFhYC%94XY7?**eTf_-xm)5ns~SaVpZMqH+#_4+|1$(vZ_>Z`3bgsp8qm3sH~JwWpRvI;21a3_1}PkKzNw30&PPRe6HV{Ys|`<mYyBCkV|W0x5Pf4hgknuj<e$OnAHTx1p!V{dFWIR+(Q8=zDFf!E7#>7-+__kh#Di!ou!OHmnio3tpYMU5NoE)^Kq)y+9_!wi@8TOn9QpikXahT1UCPcC8hYMrys1%mlUM4$p|Vcx}#1-uVUJq^=#d1fo|VLYRLXk#jcRW<ZuM|YOC--WXPptlR8TZ4=Q;C6VkgigYuK*ehS>xt!A3#<S?o=&6Q?@LQvX_@p_(Hh06_JYKeYOU?tlcJzBihM+rq_Xt`+#>D7S#Ms9$k?~%%^@*#1Q9K3+!A0t*iPcAVZ#tk%Pu6q2(fBC#Cyo0auKuI9lyx(Zx_qWFJWyI6*nGTvvO5y4ltvd~bd`A`I;~qr5`b=cDrR~<PA2i9xs1{(<c(6OO`7L&e*0&bTn<?u#phhRhK-&Kbz~r0!CsGT492;le!)GlZ<wk|qNSo{BGi$|#!-#;zbb*F;<2oyVrq=^RaOksH&tC}3>@y(K4HTtRZt5;&VqIWmC9Js@eIZfFGjKDWhwwgkb?LM;<6ygUszpd1kba(j$*Z&ImI?~oJUZVrKxV9acQO?IalTxZVhDc17-k#09pq+am+35qLWtJ*2t`s_r}OoJP_#GFn<s|bEseyK#Z9b2&E_VwI{uvTG85A5UO^LWOQE^W7bhWVduIR#unuBl^H4T4JgUv!H3x8FQyA=S{C)-s8y%E=lHP4^QhkQpV=Ez(B%Jh`re;_tSSO0p+O)oq+LFgaTDX|-{AU<4yQclOYO!T(c0`|=Q2RHNoo$6AIZ2vLK-|9`EGK%+NK__}cm&mT(tq_$qkdCj_5!cP1{+-FeJLoE@mGA3Ry9sXh9P(Ar@X-(1>ouzRpw|Y2sKmAj-&Qdi)Wid{C9({;&V%*vTvkyC+wD)Q~JYIX04xU$Qh(=0pfv4I!l3UNClEgxmy~fH4yc*f$AbAits^)W1m7@tx9b8{LovL`-*pM43=?6y`o;tuZ!kOpG)_=i0imf<fGry1De?JWR=3hWtU&G09Sxi02YaI#08*U=dP2mBf^*@oD&Im@RD{*%d}yZMW84a6y&pi2KUO+8LS?)3cfbsUUZFv({934enE4rp!lgf5g5fSRfMt?DI+_elth=F@7sA^*$C|Aq!5E2F%SKS^?h&jjAp>}l^h!2(TSutuO`<9B?R-t7KQqTf!c8S=i*Zk)z#1y<hoxp!8nid3b^dnyhDgF*5BIAek747XI0TaHcUmDkdj?9(aJ2Blzzt@{fsnbMd^btVF5S^%9KgG(=dz*6(zR$MoWUExP}Ej3~pDZsp6ME;jNQdcIBME5+|t0RK@<<nJHZxyfr-5S<2M#Bk-mHWgEoiu=Orp`uQJC`4l<Hzn0X%cO0xAA_%zH>#3+xQ5EZYIgg^ddiumNZd;PFX+_7<oIF(f$LicR8YvBvvg@+sdb7X)K1MsgMbo3mJJ}@Hh=U*$nS{)&0{P|te|V#bl1#7z*LdFq$vNii2)oE~eF&q`QirM;fv!bozHyd{J**xA{9IA_?Bx(>-o$8i0D&%1f?36K&;SzGAcfKZTIUDM7D>8yB7YVM7a@bXu3G9Re+nqijCCKHLQFuBc!~S~ffhhT72%^*0R2|aSYkdK%Bxc?UaU8_#Pp3QD8X026%%vmCv^&z?fgC>2(Y&!%P<|Wu(z)AsE{%;C1U$D^&De80UZUS`t=OXI+1g&#owofcswfo6MIlB0<ZtdqYu&X*ZVttH+Bwe#gd+B>?B74qg|d5KFSLQvd>q`0f3=Boa)3g3|dp)LdYa=y#c#y#a`7KN!HsHjSWVbYyrectV?c5eH-3z3=%~U$81KNRvqCj@yby9Hx37V?VUBr71`fex=cj}l9+m-xN;->N`$kM34?~Z{z}zDPdB>S&G&E@HX75??tm{~$b^KA<s3}}GAWK<0QtzvJ$V`Q$@N$_tJk$Y7up}<2ZN(@-bL8MH*l85puWair4m^l;=x`?R0Z=T^O+wxB60#?ChGWWjPy12m_?j%f%Nf`OnBWckTba~0lCbkYXtQ%Zj1>mKDHH#P;WY&(^hlZ$f{5gY&m0`&mn<wlw#3<wI0W3M!gVXk>G2J<$DMfLrR@4U|R+Hs6lEdj3GX-oaf!)X%b81uCLt+&=Cv+lupV$s72FpgsBNZpHS@t4D3hMKGD#4^Rgld14~l`6HlfTqBozpA|Xv9X?v#=f9){9N2%|&Q^75CU1KEh#hOGGbaiJ!c_7xijm=@1#EfF>6Mw2>@;D!(4AK#f+H1vv>kxt?&upaUmwu+x6Jn$+3+^9xf*@<elk7RSTwu0%f^e^wt;#spw~Ghni_e167O?J#?80Z`^rD<MRslK4$wLJd`NRT}IC;vmHJ!!A`iCH2C8Fs$t1}k3QR`_1)GaLwk=FUvmkcBxCLuXH*dJjiMcN{2f99TNTO*f}-#hgQTphpL-y>y|rkSP~F{FiOjrF=V&kXLC^5`Y1_Y<@=QCe_06o^GowiTE2O|I4#)B}ByM<2OzaF)z&7L;CfsC$S?t@G}eV|nm{Y<$x?kd7`y4jCNbfXO524&os-o|HnimI$puSd#fxZ8l$B7o8-vZal(}e=MF*Lq|L|j?zDv0ZHR9aXlA!!$_te?Y@i{<fULxXICq}Ir+*HeP`4#HGMlF*a4}!3acO=95YbpX`dDBn(-u59IFgL1IGZs`?bc*(c^|}72LNq4Wf(a>>oDAweiJf2DtAoV%}%{Xk#R?KUk(c(Ew9ngJchy&MWC`NEx|(^kbaeb8(;Uw!c<Dz;jTAG<v+A9ryn=b~l8fiV+)p|4}$vK*$26P0$`Wd=gQ5+|@S2nC&3Goki!1ixI*r<f$3Z>J|z9ufNb{`rq6ee_1fRZ&`R(yvJ8Gfzxq-jx{3itMAj2=In^qd(eZcE)d#^4pbY>*@jY&o+Bc);c1Bc+ki79<GzkIZKO|v*Ev&#R_>x*aDEO+`v<kCe2E}`lh?&h-*Ux+xq<^GEp5GRjT|3D(GZdXrlIGxRa<IrJvejcVk{ia-Gy_?abscOp0?anJ5_Y*NM~PRU8_qH@Fx3ytAiGL>z{(Ho*8++oD&GZJ-_5sna-A3B2;w)h-UXw-EfztV8TjBh{q(z>e0dm!;E~MxORxckdo6*y3V)w3Ar*xE=WAqc3U=|NLR%DNP=G*6pXR(yLyc9KcfQzRNl-pt4a?;L`Z={<9n9vJk)@axQ3Mw)d-c<v(qrgbQXu1lfSVJMNiTVMcit1mB*O$(-WhSYkOW#8Af03a)e>bWP9gDcF)0{c#qPR;j?tW6OL$kgY*A=5XLnHmZ^Wljd(hcC$fb_>?Px@q?1iF5r+%Jdz$TZggsDn-!6HddG(fq$lV8hk#cMjTr~K4wRW=IxwvD{?^8-x_EeRIBTSezz)L50S~ZoO!rB^8J!mo>-OI@Eo!?%*Jy|PH&6+dA9TvZJ!NE_}J?jzlEc4{a_=9+td=hzh=$Ca>NUw!Kmi5m%D%gL^cK6SyDzKKa@_&MbBn>gNTukxB9nvlW4jdYnD;(bP{#ko63ZPEl!yAcQ9KCkyXXiV<>Z19UNf;*g2X?IDqZP@-Idyf>!9FM){Ls5MrJC1gWx;qQOdhIRRgX3}^O1q3lt-SfU$mkxj1HnpvhX=DUOui$^rON|EfqnQ2`sfTCty`5Qbzmj2+ij+8yyl5ApAoT{)2t_pv>!uhbNmaX{IpVE2UwWYBfL^T|n6hW-mu3d$`mV9kI%Y;Crbi0XJMb;Jv|pREN-}OBDAK0FE66=#VI(Wi{$-f`|wpjL7FNhOt;eCUc8u>g7v#;<?;5<>e8r^3Sf7`zmJUi_$1mJelPFt2ePBKD!Q_E3m{#&+Z%>ckk4Mg^KX(1z@gTb5qoqw^+x8)f{UW??Q3ai(Qu`vA32>RIlKb0q^PV`brn(2aK%Sm*}KO>evG)60mChD<A^**FEir@Atgt9uYU!8n5YBEfm4SmSYb=NsSN*N9onyvHq$ej7rauUsb0naIKu2_Uv>s+Knqeg<C`7`MPo1C?VP3`1W);j8J><TgR#18Oe>0FN<rx;j%w`-OmB7VW<CDc!+Ciqn3S9@(lPP>D7*JSL>X*??0-+jsn0fJ*3%}CVdzHQxoI#H@CJ8E?ZL37*9dtBdU*%CU-!V@f+0Ivm!2vv!miwK7w}OL8scD`_3N}JMbuEL<K^sZ*oFLnx7ZoHshdbUhjB`mj>X!Ee@&I<}pIUMKxnI@HX>sRVwRAlI+#7wP9z9_0Y@{yN-(NgNQbwZ;ZQ(Og?qIwb3kmvqOXV%?PlN0e5XbkjmK{wM*^tJ|f7-)^gYjYz8Tv?<|MDjoYv7I3`nx3gDVi)d1(XbfPI3?0@_BF%&UKMx{svAFC!Y1Zm<2Dqbpd5l*L8j{8&sm_xw1gW3&UalS@PU68<ZQfX=@OP7Ct9HE5p9dA`eariL;ne9)I#D%+fu@yW+tE2L&3sPyUmEgG<C>=1ycHgyk{80#5Cm7HQ3Vq<GLHDI*UPgRjdxD5YO&zA{XLnDH9qRl@3CxtI(%n&+htg1=x&iss@@&MhgMg;}Qr_wKQXNm?4`o3G>N}E5N&VrCcHwv2S=@H%lY!1jmk7IZRV_Db@LuVRg!pBOUmN!D45IiR3A*JT$2hfCoCn;LuppGIJr54dO&FOEbF%H$kyd@VpV2fN9(#hl>v|X{*tp<QdWQB2d$CCsI;y-VFA<iscvY^AN;3WeEq$%F@Z4$siS}&wwyqhDk1F*wx$0O)ZZmid{IJ2n4dVbY66UOSC<e&=9?}W3{Bbh>^RFVv*48zHif?&ON3Bb*^Gw!IM=>FIk5<2BIXH}67~XT!xUK;8K>3+HLyEM1O$g6-{u5uW)kSY#9#`Q$F}AQBqp9Oglke+)BHXrv0(gTsh8WZ+COx=IgfV{{eiS${C$vzJ+r8%h9%aI$>cN6if4mW_z_@xvD9IqHUBR!qoV-p|eYT{Cr>R7=oXA8tmIgv=&|mpA9hvw6Mjcs7Qxqs<FMfJ+gL~|WVMwhlJRkn!EW+$?6|JZsW^7F~^QN7U$rzm7CnmGVwdJu;udbWV-11&tD@kbZAC~>+JIPQxVziUD@fPQpgRqpuVZ4KbVf_)NV@{i%^T+H<P(M5h_E)iW<{M&InXQX=OGOSQ@jo#fqS}w$vRRWFs>uySPqD#iOuTc`!f9o3p@Hcuo_A(!FAru+TNmImL$CP^%s3s#5D?#BF5mR{=fC{zv3#Er`C8up``OBhikK}fJnXhyiI|g`mJ-GKNsG!RYC=z3J>(p~R>{-&$An-!r+Zq6m?2k3mmT<o6#^BEERu!YTA!oZZ$wvhdjc{%yY%N<)Y)*~(Cuy=z%EmaVd2P9rUhzFH4A7}F_t>qLw!|-ZjmQ-`=gZJ69Ca(;lAaJCE-Pg-E?sfnM{8mMPhs?uz4|7WOc6JCsC}j@31(FvPu~2tv<kt_~M6oHJYr9k~^94e)V(4BqAi!uH^3j5Ys@50oXTSux%yA($5tHl$jGQko)1ff9sXt(^DsEak^rYu)m%ILdp1DfJU(P5}&C&hbP|%Fv3BFBG)Q-t&_+w2e8t2lYms)BDtEEInHL2x52Z*eq&h0m<4axdf2__k=kzN*<C#2`<6`4Nqu{b3Z2~Y_CG+>mL5Tk!S#V$$yzo429?Zs!dWYY@Ps&M{}@q=7JbN>UjhV14P5%^`UW64T%)76H{N3nKjQVPAkYy@mb(X@b~A&`b|x(*9=jZA+&+N}xL$A98%Ld^DW+r0NQYkLWCRj{6=G(1bQ->qk%i(la-yz{H;<McBs2ES38L5PAIHM^IS&2`03_q6G=rR)nd4y7{W8M@51C7eJF8#g#Quj}Gz$FTvoFQ!o4d4J&H0*W>ZB+o?4wG*C5FF0IAJ*d=yD&*I#E8=vA)8n$VqTdT+}8Kf-6)w+D%W@;KTg1U|Lb%JIn~YY<r6i&g`9>ptizjFjVM*#k=nHv({i*vrsG9LgqoRa_gumZ}LxG=HkC2mFSQj0o{d7@N!0BGPu34*xJF$Zfw`%3hHPQrP)s-w1Eqp45mPDm)SsX+7d_eQMbhJ2OfNkP^rreVC*I3Ytn}QEa9Go_q!!wprWLIN>)1IIgdGdxHo2&VQH~6uR}juIL=0sIEb`^^K`LqA%ed@5;IG^*zh!edo%h?1;WFgL;#L*l_nurgj{jQpcK~zSY#C{nHYu`@9O%b!l%(^baRi-<kvq78EI!(xa(PNtIL6L<S~koAe&-==XPuX6x<mu^LCv}a9EYL#)nMc+<jUBv_kYSdT~bdu&;&6I9&3B$fmR^Mz`Dcm=Y5m!%8mG1kpgV$fkbueEn>OBXQq?$Xu~lXH{#!;4}va%|r>qre4?6i+oMn$Ogh=UEQ?+L&Elq=Eqf2xGo2neDO0p(UJp<@ZcId5^|6CFR8~8qP~{!#()=p8!x6k$&tjE_uR@OXNBG&#(?%lgAsuHQO{+k#og^h@99$c)AoUB!7Nh%2}j8Nr+Z+G20L%Q*=-s5^wHryirETNW6_&DFGZk=J8c`muqK0ZOPC^cZzCx3bzSX^Ymv+%|FIk}szq*!qySfbZk~w7ktz{k&Z^*7WNo)dq0OE?MN$s-pIKo^k&8dQZQ_-m94(|cmjeQM2Buq33N`mv2)q=K&oP3oH>?35O<9_Q7@0PnNfL-@0R?2)mZLEWfar}qW|Y>cV<qVKw)5xAe^l{;;wYDTd|ya@BZB9nbUCk@ixoG8sh7;XC^Wj+Gj_(~$D>OMj4+j1r-Q`s=O9SBRCNzSJ7r0;y6f&dECJIxsDw}kJ5(|0aCH#4pk)6#;z8qjb$RiuY!C7`f~+h!0@oWg$umCElRbZQqLpsf&0He-cE_t=N&NEJgTb*{JQ?`1#$smf-4pk?dpvFH^U&>O<Qq8YiB}|%+pzQ^b)3>kLOp!9af0VOPYwUHezD1nx-B)|nl%l50$QrNriYKjV399gGiYV{Z#}<XJWgEp8`|&2CKQ`}ISAJKgNY!AI8HPRSl4+mI#}DK4Bd4lXCZgyGxl1;?cm8|*?|t7j_z*AywzY(3_AY$kCoGto~W0#7zd(IJr*GXemQhi-$3y#luCGzf9R9(sP|Xk{p}>#oQ`k$R<wMlC!SIh^Df(WkF?6_xarO$fVRDoS^0=@FHXWP7}Af`p!FE`GhT_XVDt=4Y@2n`Rj1ueB9zvS6V4RUaRv7Q5zG*M;}rElAHa+e14=F-Rb(^IrB`txQlMEfeQ4VkQqt{8>G*9b3q?E*4No#4;~WudPpT+_w@1sZL5h|+n=Uw)=oKPO;{ymE{P=m8h;M^CuP6aoLd*dAnuW@3At!?ptgpii%LkJuERmE|5462NF>>ghQ<co_BT78eeBip0^6v=K=E5=P3nQ-uz4jZ4+}37vMSLqreZ}S@$s{`sZDHm{ymPF1?&X!8WFRcZniE0vUW85(o1V_vrm%j(u|rN*vFwGfeL>K4!_nX^PlW2dPB2$?xNO-EPDxeWwX@#z|NLlU>&ob#E)riw0z|8V6YI?F=#?!g9Hr75BH|O7w5L`0q7htqZ=E9b$jtpi$=*`xc1CV*%rcw7!P<k1MH+<ubMm*)CKfYLE*B&4RR^mMs!$>NaAy{~DVPsUJOA>$z07+kuqM{oX2rnZsI{b#!AtUC9)??Hi?slxm5@8?zgfxDK$aG+f<nM!R2Rq4{aTscZXX`4BSk*YFJ5~wE7ST}daC~PZWzJvmfz|J`hI5zm$Hz##*Zsoy8_w5$%4rbLk4qg&p5W6%E|ea1%~QhLM42=uX^dyWm&Pd|HI!EfD(?S?nRV*$YN<B%V)g^d+~gB?Ik9G%-0tGbVRBGlX_*eD~&%XE54pH<1uX+U&l!=FW*^InU_y>Bi}`7{of)2yVP4KgInW<UKW$**2lxO<oy^K>~N5FFMBKK4a<YFgV(LhBUFak&bUs`_h0==b}a{(mS08-#HVhBSNSuI85k~i2b=Kr!9EeLD$kpDMtSE+0{sWr)ef!dBawp~;=Ai6bZlaqi2UXFlHkHgB-J-!JFQ*6NqOQp<FA&N4j_Z_t^0JRhObQo?<TM}`q9)B;b6No+Lr}ROA*G?|0U@CyvhT!P}G8eLbo6NfN{w$e3wL6%p610<}&Ae`v-<|qfOF#v-(UP5_OAENerav3D4R0N(+$KWhJ#rki#U^&TvJ|$g7-)uR)2}?5E+hqY9~sY;4g8LnPVCjqTN`#8J0i$b3>0;{0?p(k+JeP2CtNc;HrP8MFnjT*!NZA%S-uP8;@i^1<a?Q$Y09F89F5HkxW*ef30~G#*nzPDCn_GzEDq7QP;$3qi`IF~`q`wjJ>#odb>43c^<EaJ6?%(&>?9l#Fh--Qpx);!c~j7f?BGVs*UDLs-B%-{R~rD6gg)oOcMa7+hv@sK>j^GRVOhiHDA5>zR)~3S8~)sd(fM>HF%(ZwKIMpj7Y?&s+_3CR>(?_9OR$%~PQE9+#x=(syDgtl$aZ7qgyeL4=`CMr{E!(P8K*1;;CYDq5MbO_dEw>&Rt(XNWF8YJB`gacagsDN`vvS|@1CkEG4GoL<(*RbR%r=<Sm<0P2RNE1R_XA&&8}pz|v(yL<mfZC15mW?+Z|yfv!~mpE4_=%Z{<3$9*35?jOl>m>i+_t2#P0DDfPYs8YXHNpq))_MUU??)<`c;{J1g?fVTF<PhI6kz*DMTH`!ycr+NARA937^M8&A38`WM|xZobkA8S$jP+ZPz(#9$##wCE_|Ax(jxr@#zk6;CE{&M)iZqfuzkxx_6@^7pQh%#s!QyP|M{$fwW=4WHUsDc6)Gn?S*q8)WX9uiKf}hw#9&;Krjk`SWk<sqKisai6O7l7%{Fil8|H-Ue>M19@al60Z`<-6tcxGg%Dgwr>r<%g>-lPV>Yb=i6@#anP!%XCCR>TR-Y<yJDig6o?0?T{36cvQjgDg<`;y?9Y<<w-z#o^^9)o*BftnG(<DMA0OZUbpk~d8SFE4Fn!RS7Is>>0*A}}x|i$kLSv4!mUvM00qAwZn6l0LVuc$!*A%g`wvB`Rf5V=_j=MT4C7w_4*En2Xp*EfEA!u;->F2%-kUBeRdx)cufLQ?5`QI3_U~Wk<$R_NP87{{e1v7u=TX|F|~XY&-Go@5mC-*Ea#fsP|~Z|NqW$nJ`zvc13-&Cc{`mNN)LC`Bw|V5d3a()>`1@glWGDXR|oYp(ih$`MFOtscbnNw+v<e{;0v+P-Z8_^FCTR>Kx3Ucxt78i4MgRp!{}I(1+R@pIDsMdF3=Cl{6IsbIas>xS}3m)JgJ5&~5Sg6j{T96Gh?>kw0F0cgLpTAxx)V1y~>I-XoOysF=q%@C6K#+fvy~kR#$go)4q*LCDMaZPfrMg!t6x#q_ne?x1vTG8!H4zj%az;$}5|1j|Zo&(s+pJ{@4ifG^ze_W<AtE-;wJIkc&Vq_Vub_&~9~c4Oi5Bn+W*O*@V?)$h0!wX*-J^Wf%BYCIw;1_9*aJlG@c&Q~D+OP12^4-LIKA|`>Rux>~E?%zjZX4$Jr7Ox-}qYR1EVIK0>NrvRKB{Wa_#hll}S$YMdhN;yl4irt@VqASKy@A&G%d3-C2PN;i-BeQ;fUbud)}g6}t=0LDsTzA!Q812($g9Wh89gJ-Pbrifm10)nDbOg+W~t-ZvTJw;>U;d`8ND>wrY|OSgb>O~1&1|JvhC}WL{n2g(vq*n!ArqW_7o~iG~DKYEx%*G;*_epa9Rarap#nZKtK^5^tSg4CesmfoO^ipmc_poLxqi-&*zKn<l60$*S$wO$C_Yxk3wkrH;sOF5xF4BrD0O&on*tR4Pv?-kt`Dg+3bX@9!>2Qp<5H!Z7&)nRUlf7j9ai?0Yuxj-K22P@gtn?`7<zCWO+pDlwTpnR#B0@d@%ifR<(z+R^bE?_4A?CTNwEtxGzgGH;m{QAE5%-F$=u<>&!t|do?o)aWAY6qoZfv5^P=tek1`w43U*XagyW*SF#J6V!df%Hi%wlK?i`u3>et0s^fW`?JFiww7J|KUp!-VVJ8@tq@M?F%_Alz4#feS)p7NN{Z6yBcpk~RDepW;e2AX>3$XH^w}Y0QG;<=rfE5buC?p~yjqhp4y)N`{Pm1@@IK!ss#gR%el|(=-x|D^O&i_h935O)R<%7=6G9-*yPR-MF4(yycW0{O6-WKDkqqPjO<GAB<vuI`w8z0@8p*%~lPbMp!E4-)PhWeA@zYZ)NCpDGjd#deV<K7uyBE7jiLu_Me0MrQ>fj(|C5GRtkYS(<Y9v&VoZQeA@r=);cjdy*4tYoa=$$|@k1@mOpsVw0O6MZ@=v=j$=OzLUif(>j3Kq;+fOr>Dwy;?2@54rkli_PsG5C`v0RhCu@o>wv!$;ZEp_3!&zndeo+O0}P&2X1i6ILzi78MN|#26xB3YDR0$zka<RpkQZ>Q+n>}4EOmI5GZ}8UZHsdE>5=ho5u^3{#~h6%pCuj^a-cI?5}QAZP$X&oMfwoN*t<ha<t73iL~}2JTZweOWIuDJm!9oR3(me{jWsO`5cM`n=mg35+e7Y_;juJqvU+0fGy{q=cu%-(Oy%$HboazzLumqXIRmGaO`q4asw}1@5z-%$FCt#P`5jAHPW7Q%4ahWL_;!bNIB8Wcae^$!%mfA+W5$$A62NGYkK`l;-YuW3ZunO5BP_;R(E3IpJlL|_U>^M7ul)^y`<mbjBgLf>6HK{USfu|<J9HrS3ik8OPRZix#p=H*5*2bKdKiJd($U<Y_<GJdXTtGRyoz1PWHqokOE&R|4`2QaqTIQ##~#!`P$A$K~O@t9SF!V!-H>u`L$UHyu}J7X_Pcl=8>*&L0!v;iNbiXJzeFnb%$#<kXBdMTnC)hVe7KT2$wncBp{dQ{hzvXe9mhT`(ok#s5F?|3wmgtW0_=_nut`>6h$h|UMktHPn-h4{Gf&VimA{5EM6K?69A0BDT8vmXxnLQ&sa0>afx_qQ1Jw4dtgzoL>6sCU<4_N(JVvwGLlk$i%qe;M?nDNxZ3h|uz8x$5(9Fa-A=8d&avWG><`ueZ^kBpr!@GKhp<}XuHU_m1SaP5*oQ^BeEiY})B{_*mkkJkIZ={mg!m*!tLh7sgat>zb|wS9q=Odg4=ref$*Ww>+b%F(Jb@t7Jc$ezX8Cz?xACp7MZ5*?xJSDCEjxjcTF)gW{W|>z;syCvm)-rdALPn{dI27QWVcDnd3?^##_8gR$3eGaoe{Mx5RlK7D?l}PY@#a9d+(J*JpNZobuH3$P1+qj>4c)`;*p3Ix*wiwnjO7@W3;!00XRWOOEW(u(ApE+;>d{lq&o7vg<dGJj-qR6>8<TE4((VLk3El87|GSRwLD)BsT|KSTY`HF1MjXfkxe0rB1if}i>5HGi{#Rk+c*C^Vw8AcG@3!KINgruWz3Fm6jC_$ZGPH2G8j$IjYDMAyG8#D$>c;IDksK$JlRGg>6Wx8=|~2e{qU$DW+5bqI4N!TtiIMG&ef}%P*vB;#GHwuc&cns3hjPU{%RN_tfvVXJSIE<27XH@tFGbSC+wy574DDI^K{hbS-cA$fOwKIpx>(@VTW?40x{j$y#$0I)^WpQ+h3_2pl3xCg^-J<xg4&ZDTZVD05@}N_9a!mnk{?|(+pz2=<m9-oYu<{6sp3QHZ?Ae{|RoF{%oj6dSXPpJ#N+`Hy!-DgF+p7Yl9&j-^4dgzCr#q_ELvkkXbOwQcu*fg}(kmOhZ(jTVCTs6%L#?<%jHh4jrydZa)F($yxa?lxU8;a$+9M&vimGekJC)#7v{I^`!g})G}mhvbJ6a4GlP4E*JbvxV1FnNhb}I3YV35b1x?m<8fW01cRaEdG3xSSxN_dOt<&{wOFDW3$B+nQ>`;B`Ki|1z+Fp&v;dg+IjWqNETzSAe1+D#ruB*$ld9!?$O9TeZ}$sQk<)0i+c`vEN$~`nuUQ*N6?oW=cq2~{ieLnWjP5e$t{5)4%?g+>FdlnreX2n7@AEU1Gdd)7KnI6*#k?Cpb%)&bz-V9i6l9O1)>vN1G|~|>artZk0L2iXM*9swTY>O+)CbdJF<K)PA7eQeF#E$*M}sSxicnUVZ&}6Zwsyb(G`M|*-xo%Po$a#~-3JIJu%WM9G*-?2<A#P;upR(G{;qvaRO?*5c_Q>E-lIOJZ70?AYsyhMFDy)b>N`_FO>$=P&kov4oQK@PxdCatz>IqhIpdOBm=~x@v&h(U)@w5Mm2#xy1x5U|HA`SK$xj6-vLAe*snH3DjXZj^D>2wrlCaN^QE#-nl799uh8N`}2H1evyt;Eo_{@6)@e|gP`W(1~Gor((z*rZfiDN~1+RC!Pq}=s+VEF+&P{0|-!1U?#zKMJ+d9ql^=JUsL1$kTj!5h$Q`+23+QVzt-<Pt9>b&iJ@<)1KuJb6}bMXpD<<sfetTCT%<;pUM0eEW>NeNx6JPcL{eXqtMsRX+>lCU>6xHa~{pChltyfJMFy!DH2D4U-^|U4skk>WZ+3{^`gJzRkI;tuqnh+lvR$Pla;A=kZW~_MH9IU-{W3rF&XVPEJaFbvvT^ikK(Gy|b#=KVv^3cXH6zi3ykY?lC!$si~m%lhq65vX{zESe4&HE<U}LrSy1?@%%%y4}5b_R2m`54jRSM(h3{mef<_D$6gMMvS<2xZGa|_-HoX<0q30o!A#O$3c)UL9Ysq6X(qOohBjg6G5!!Kx^Xazs)XWqIg&q|pQLYHEDPqCd!{AEaVo5yvzQQyfp?TYde@S26^aHT0G&KwPWs=ml$@R2ds0WTj&NILrxuo%1(tZ=tD$eZg45iM39vlxO^Y5orJ(IV5BNNnDD?|j&z6L48ez5wao=B{!!emKf^+{Jdp^3$0`hXfiZz$B4~AsB1ZzRU7e_WiN$+ri^O2LoRjxFgcMu8KXUGap`Sm8us)R>yBxC5EBrvdR`RU-w;jfo`=XB%tM5GQd0Mpw=@IKxD6b-N^lv`)FknRbn-w9ztGYP5NTd7JUAt;I8BTjwZ+Q0dea8v9V-iqx9j^FlLr_d~x{$<;k3Nh|6bR&VYK7>-p;}G}k=PX_>F}t)uKB-PK0}Ht7NSZx;(!AU!-NAnau2WHyuU56FYZ%2i$07;F@iFwG^`aDNnK?t5N&Me+!gf0C{aV~T2o&Cd{NTa_h>ceHfz4y10>WG$Np)d2#sB~SB}(uWu(L7v00E9xg1!g<yu9@gvBYQl0ssI200dcD""")

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
