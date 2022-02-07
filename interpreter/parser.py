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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;Xqj-+g$)a0S;|Myp_lPmQdV>R^)nqaLew=?qsP4^0eP+O;!dRbu#2n<#GI5AG|XKGz}(GZ(>Re>CS>>4MgK*ypGtJa`_`Jn2e<v--ucyRfrhMo-{B5GN_jd$<M0+bp_<9&tesWfvi4ebQRJ2z@3(^Eh@7CQm*S~xFqdzr5jRmHjaltZoaaRqlE93#$wk-$#Ng%^}kw$8)tinfQflJx1;<4ramaPxF%W>90rUV&8aq5f+(4;q<HGy>G{v15`N(y)=nGX6yVbr#b``A?`AFW)|llIZe8se&~G8!O<*OXei=PFru7)Fx^Ux+{)L>t$%?drR7h!z6-_x{hDAgTe1Eol2pz?s4j%%l!@TnxyTMVSX33=K`~VC9lhISAjd)dcPa>_=g6<?tIo}570fjG=I!npgD^r}C4uQlk7P@asWo<DO;*}>UA){-S;uW{ijik^+hcau;XEh-DF5bY9?-91$2z?FB+>SYqSV)u`67WyFbyu0fm{BIJ_nVCku#AmZgOX1$Qyze$e1F)`Q|uP9PSG8F5jA#ld!RNhPj<K0tuj%ZlFnLZ8^k`a9$ASqAch`Bd%1^`y{iih*HqXnc+m85)AbF5Vd~OBO}$zjiVzK=c*zacLwRa$Yku1a#zdB7x+mffEor)r{DI?2LkO%LD`tMd!qo!zQRQn?oe6OE?`Qupo;q(IhOL5Fq(#vYh(SkCqf`9a>p(wLxkQe!c{ZXE&MIL2i`cMOHge)UPBk+&n!W=^P8IOB!o5Y`evxJmtv>6r$9+C9pHkNu5*7uGZSng1;&_cy$k0gLseMjlK#;m;=8RqeJxB76S@ny1mME@pztP7QEY`OVQsSN<XZCdf4yR4zi**V3s@GSh{7%?mb-|yziz=E}x`JZJJT1q;4}NEEOdo*layx*Goewjt<2Q!)?{Uk(1BzU+aXb+qNgFk#5sE@cip-rS>0)i`oWctujP(4@K=FF}{+9yu=CL!anA@!J#A{OD)z0oxT-#|S8AC8qz<H3g#)EnCy&1+m2V;p74W$DID&8#?2!FS>)BsSG)AO5w{k7x(xzcV9y!dF5)nSK5A?2>xjMVE{wj~gGS=d0bH^oAN@DLmgp;DlkJie2Wtijthq(0kSf9S-|Nsp<bc$-G5u%9SQ8vV=-%d%RXt>z^kr=&K{eU8Y$Rih-)FyBpF&9h#6>K$u{e{lTBAVso1%b`6sD!yH;1L#h`xevaN_@(~C<+|&U4N)JcJwt0<wv69>V$ABAYWJfm`&e@5UOK=&07Vsq|Jdd2V!O74SGTlcB4{rN-*jxYOP)Yc4Jb}YK)GvA#zm&%v99T)jvP7IQF#2N(N>$8qmoDVB2$VMo6Z+Jthk4cX1pE!$>odY+t+d=LYw`(Jnztx4%WgtxBh-z6EBkY(-N7h60JvH-5MTVDCF0R#xFgGKKm7R*hfzocx_nGy$d=qAR9lm(<~iZo2cGV?{X=qpKg8otmw?w(#;J`$9DI%0?5sM*jeUP_7&>Yk+wB|0m2xIMyp|b27vy>+_;OfGi$}6+R{%j^{kqpH$$@Bt9V|bVvA=wZJ=!8-t6$^22?q#!+dx=KT1``XEdC1cOzW6$X~_CJVa6$VQqqKHFDc}^38T<cR{Y)D5a;!X97`HJXBELG{(4gsbNPZhjS1-Zjv;&UJO1Fi@<@z*Aq*}bX-Ll8Bo_CKX~=jIHR~BO|A~wyKWuvq)nK=Hf?)=>pjMY*SkldFX^fqCsm$@ti`NPmImv3B><pLcIW^rs>(>ku+yY-URko5BtXpzW0AT0<FpZn>|18$7_M&-99N*VG-uk?vChB16jFj4RjRmtv%zMg(?3O9zo&%_E}%$IJ<@fH0Ne44>2`9MB4?*#@D##SE~?RPM@{Ys<lio^zfam$Vx~t~3)A4@c<8R^`PmPsd6wT|+<L4M^6Pn=HoqWzS}3hI2iASyY5Adt2?0%b@y`@>;(8DUZu1bHaFR|yxPJY%?eYk5*15UIk56!@(Ee^Xq{I@CD_GjsB(`I$On<(g4Hn_44=aDAl?SA&p7(iOBDC$|t4wxkmVIh;D46|YruZyu<+T-jJ)3w;F*w4+t7quczQ3Ye4Z|fjD<{^I={$qp;v|QE!UT|wd!~L*R@yB7q+zTAsfnayZNA!r%k4?xNSvo}<f&}80-D@*4EB!)E@e)9a#TA$L_EaR(EN$DrF*(%IVo_-dI#HeKSfg}&dRL+Vs<bjfcjcgPd=y59YN8yg}z<gP1;TG%V3j-5p7G)gyX+0aotn%3oGszcbG1LutU7d`8c5#V!;iGNh?BQnSZ5@p2KUVFDLznC5+YaeMtOhG~>UE{*V+sq7;CC2GK96$aeIJ3W|e7?X%RWv{JWDY>O;Pbb_@haj1l<5B^3!DRk|dYGX*;{7;O5qlmhMyHo@LN4Zgu$N+g30=A3FYsHBoWC+pMIrF?=7jn1ymh0BTUuw&SHGJR@5mLRUA9qp{O8kI+3LbHG!fwDv;xBd<f`x2YL%X+{2cH_y>0FU+7!#Rw22<b1Gy1Q(we~WSqG2RB^dO87D*cjoYuyL^s#m9L)H2|DvyB-L+V+R*d`y{$MWgtf<pysk;rC)Jp30PHH-w%VofvOc6CNv;-Nj?~_CpaD$r1DdwQ;X2>@Hc83%x{jK~3jq-cI|m-*q)b;xYQA>wnhu8wB13^c-^p4~Kj;BoOI&*zn6!X=PEOK1=p{HjM~noqck7ewXs~mE+wo>w9-B;8YyZ;hAmRIg6v1aD(nkLiY6+BFGFIz<xcnd~=$V28m4^*Ns)h<pEE)qY?7D@RKjwNF0{`t-k<C<VF`~GwOoQ?PKlu0Q?Yg)Rbaf^bV-c4hQHEZ4Sg3>9NNOE}+9=G3)GBbt^kf0WJx32vZCg(^wNo;J}J9lmgcAU2k5$NN1)rPcf^mIAH$v$V|A1qfgMj0aav#%N?x1?)tkK<ol%SySz=+^^a#?p;(nom|uW44@2u0U+?8&4Qp{ngk=s93r6B=L)_L#i%mwVDv8)1|5Dxjd*3e1Nt2<s%o<r1>YM1A-_ex6NYlVKV1RhDhp|~-50@Mtr5pDJ9_<w233DPJ)pa`mDGs==dBQ;WZJs+5ZCEQkC~giVTs9?d43Ljdne%$qynJ3cxU^}29dh|EG<$sU=01P%r)7OE;*M96*Q}T$0|%Dk!*-F!U0bziwbBJ=%}^^y<$o!aC=EM#A1soo*7`sGlK7=XGCyF=Kf2;rzpzXza@i&_LHumZG@y;V3B>l#L|MKfd+?v!IsXzK?CBU1k*RL((XW_gdyQA_+2pg+^DQgb&lsJvi8r$xG_||Nny{TEQLWss7}2_$O5gA8HP}}ecyJodyHLbE+?~<f{n!Gw#h0qqe`eoN5rGBjwr~+$cPGCa)JSLdZxt#4!m8Hn6V5gDXKtUzw6jZtH7;tGbkI^ef=iZ3xI=kE^y_%!=L#%>skG_ClXtoeK!Kpr&NBmi3=fV+_Jh{Hi#oC=R$WBqUqu?w!U6L=uV-y;su1>>ImA!1cTr=U!GWgb{omLf_~o5{j6_93F@zi=z`#sI%v2`OX^i<K;li_WEH0*>>)p~tnX4}RBh0Ng>b~YKiehCdGO*T(cHY?j_|;)G_cctzuZW&u<Xx^HpR(;jes>4gKm5(1McQ{Ro2oBeq3M&N-@0LVH^ZtHqQrXUzIJr)9Ze$7{PXJ;*w=N04OcUvzK%spv+RK!uT9TrG>g!@mjb!x-TUHeLaK4&8gZZX#N{){Q*}<4S@t>gv4OMIOOUQpAS=7(yFN*+^$y!P3*5&na1hC!wI{E^zdy`SPSu5)|B-l$NFYxyzPpDCBpk8&;GO$?Wm@i>z{Oq#KoCFg3r$r2!$1PQnL>`n9Kv;t)@Q`3Jq8hV%6`!jEEWo8bxK<H1-2a?r&rV-tYf$!7j-;4fp9}JTJ6WeM1{c{^rZoq59cBOf@f8RP)ZSPm;G&-%4B;=rnEQ{5E945A7t$+bQCeII(s=);vibtV6$S_e&zBLDG&J%X_QsY>$bQaGd=eXUlduce!VeqPpM!*mSUN&%!La0X+>;J$;TjliasIHd)r6$9lJ>n5&+(>^R6MVSdi{mkEZ22ddiE(4KgDeF}a4^?}2&YxkqVc|EfaJm>%iAZdxZALCBt(PrE}QDJqpl{ktt{(yLDXk#^&s^mD?q&}k^caNl{KyqRZly;D>kR4&{?;b1K2M=V)W9wF_&m%N{jJ{j7VFgVFxV%d%fLFvE_@(LuV>U&!aPKH6@$$kqU*50g`aO~Iqn*SxR94JI=83(4@3}pnmB*irD1NF`aIl)vPI4yAwIZ9meQ=a+Z@~ymapsU0|R@WEO+!PGe{ULptefZ6MOJu~R=*)A>o>eo{-5C(nJLLW^D2*A|hYM^M@y{TMp&d$H5=e%EPdI8-v#yyGqKTIBkIjRQI!}pKbP%rz`esar^JCgs^;JnJ{hB$(EN@vxoy3(cuhr&G+QDhcHg(}}%`$t#^cU1_I$ES6bP*OtzZ`-Ro|A6*M9Ts_P6Mx&MTEr*(Gv|Wqrb_mBfDa%Pge8ct#2CnZ)}c-vY1iEzc7XfHE-ZjMnOQB!i@=Km@{!k?S7knTM{x0x`(uZB;u=BUsE3@icHV;gQBn-)e5^Xy{Yu-c{p@+OuTaMk@cHH;#DIm$waID(N)CN<1tw!1=tQ0gV2Eef#3ub>aKSv5rgTOEQ#^L-LGCU-g(NG_q0;ekeo{y6`%hw!kT>HvJ^^YUCRsGOP}&$5l)15N!f9_mUO+L!Vv+Hk+EA!^hX4&cb8{P`h&`)M5afC<lYl&XKv6++Q?lBG_}~5DJVul4VB39djQ<gMQ(YP$Nqkyf-6ewF!UqOunVc_;u(Z#VeopXCsle+4E5QLrLT(6sx?S>oqC9aHU8PN`O@YOO3pw<Q2~ZUXk1HntNYTm2)2aPc3WCr@3hlz-Fs8R|IRRnLe$S7&|Pjv%q8aV_gL3Bx6|9BOo6(aP}%`psg-ovFY?}{Ck1_{m#M;iW!hj%YG5u@OC|=96X+3=ePNyUGP%((Ad;6<-Mc0y>kG{keZ)ZE>b(KtSKN+t!~1L%WEDYyc^~=0<H+Jv7Up79mUBlE5~77Z@L^Uhb^Q&aerd&1SLRI41?U%@J#pOvg=lNNiM#~|4cLr_v#;H@V1#jga}i<1?8#Hp(ipG?567JV_0%X?WDjLiUMv@FQ%W`4is^OSW7jZ1!!)5&sMP~MC@jlrZmy7?LGZW64@N3(G3!{5IEc3Q&}eXPW51oJ04+fQ%C0&u3f{CRW|HtlkFjg}Y&Bey*M!!Jb9#I~q;2?umSm-b!!Stp8lMdO?$L`e0>H*ds<cUFhm9-1^SC5c=V@lHOU;c3pXjQ@R<1Jco^jXY?^Z>BG$SbWrrWMeB3aZN-bRl1P4o3{9xK?=pqew=Wu;6Ut&kuv4qTu0P}Pi&Q%3$ch)e*m>iy=GM9Q=lJ5X0o-rznPSiARb<n2+5l)n&-Xxmp#SbRJ;GM2<RVtAPwXgOrBIcA1VuMMOc*>w&n6Os#=>O%0%o96cGJq84VzcYtBoJ>Ze)HQ8-Nm|MGd%Ax58y=cZ5AoSU$I$J$4=!Qi*LQV2sg_q1pL?DpgAiq(aOmHZ?`R3wmmLK#7l3~!@#jtJbP{Qbmkh~RWunu6?@kC9CcUax6${Nw)W9uKXe0YiZzhQ48fl^kv59~hz`U#*0|Dp)KPI3*EqLo>&7{9#Z1&pbfipecWKfs1A}746y{vtHjJ~VDvC{56&Ixhusl;_@qt&`?s}%wD;pZn7o)hIZA4<&rcGf^^rkdhg#hbiAwHh)WO6a-vUMlvAbw=e#<q;&KH^scjyPXkY9(9GXpVKfrJub7<2_rFtz71v^P^94(gDYj*#0fyX?SurXkp%`fMA|4=U@R|K=<OFvwz&(H@sfG`5N|;2WN@Ip8^JBBbK>KIb+njUOh!!^wYPJ}>jc7B_08*+MK`du`u53b3HHWWT|RDRj+(q+SYX#7)>rdK#PeBerB`wJi{Sa&0bQ-u-yJtq>5Ii7LPoJ9b#j39%9p09w&}Hk(c^igfsaJ;5CoJLglb0vb3f@y-lO8PNXnz2;zn)rFUi<8WnhNNJHILYDGgaXE>j5}gIvD}c<fr>ILWk?`a97j49@&-1xy}6eI^=d29onjk3TE|JUw4zA8*Ut0XUVHmK8;A5Wr0i$JT^$|3>{WsG0OEvn=Tes(|4jP>E!1a5C++E3?T#``txEa!?D_@?t42cb7EJk(ET}0=2BPH-@fXO74`7bx(oA-+M3(cu|)GjoZALLBYEOB4hpjPT^14Dqg>8tfIRM#;NPeMMDokq#%NV3i33iWBWM0vw+f`9lT$OlG%^#`3w4qpmN;lxz160@PKKE;4hi6P1G!op{o)>MXAcxCH36t1Bkb5yIf=J;(@6Iq!-)1XgJ_-yP+|VEKp?lEj`y8((q4x|F+fLRj;kf1r~4w^*9EF`VvbVq6SbT4So=U7ILmaVt9XbN46B6fv{$W=XDWF)J1#aQOa5Tjr^J;<lnk>x92dae6EctwuPoQ?%tSs!ruSoPuG5ycx9lQd+a_iC@7(PJ4M+TW|5nF^i1o&XSEVv6K2}QKOhnyD%_B@Rc7bi9N0uD+k8y!mlnTZ81CiM?j;%}k;c*vjJS&sg&Wdj<f<gMgi3D`1S+)ujioeHA1F|QIv&1Uk_R%u)crfUVtQ&>gh8ybdYi*2`NInVg>D#)-Px!d-h;0gc7K~$NI+LozubD%1KSloh0%i49k2T&3Kv26RJX<U!FNazmP#pu*Z67Vxw~>R{e{#A<Ab7cHlaTd9yq}1z7`By0Hdk_b=qaQ@8mK`vM$*^?vZn_tsJO5#Zd?Em!z;L;>qDUBiup{AqgQZ?o}rI>WwhsdI_M(qs|Q;uT<wYIMnE^T-ZCIS*oL4IMN`SrEAhNWa^j@v_Zhh;~DB>F>)RwgU@YfB8E$-Osu+#VxQQG$Y~6b7@<eRTRVTtP^P_r=-|A!?vU^40!HB0@qV{#<f1f#E(5%n`0TcSO*{D+lU+Mk&)zG(2G;elJKrjt>v5|+D39P!cz?1#f+UJ&UH&_hU~xwL4|YLS-`b@{`YDoKQM`xdM@h9;LO<1YRv2F0oD;`@foNt#nnB1lpIvU2@H!twL_I$V3)a{+dV3}vSXX&fKU#4|z?Bi#l>d&bs5KkR_X_Ob6E~IunXf~GdIf)jg$o(LK0$|G{6skO__jJMt4P1~D%{$$fov~PZormd!XdwV<1{;kH;>OClOY-Ylz!MI*qaTTFS(bbK_C^F0STlc>W0&tBHQ-qU3U4M7Wbk3oZ5S0lt%|pq6l|XN>0Pp(KFm6l6Q1*IV^VAm~0wYpR35y2zi5BQKm|>yq9lY)r<A1n577N#;IiYF9?TTzv3h;p*`Jw!7<=JVr6Ufz<S|z?=ra3heh~tx?ynL1L&3S(gw@L>G)F*82R{iWW^;=3eWMEvqdi3%2}{*L%`4eawaK3X;J(IMB#mhb(Z61#O!653!6K&k884#;lB84=1o;;$lBMbp8*X&_?kJh%cg=^J#R@5z5Lw_F<z!z@9#VPIp!OwClg`y6#jwO4CE!_JI3R;hOUEte)|??UaP|y51sn2Nb+1&1FKQz^Zgm^2>O$#LJick2$nWCzvRC<dR2$=-<f~eQ5fKZF_w3RC9%Hp7DEP-fD&{XNa_1peDv%p^^UH~@A97Y)hpA%*YFqfsyB~v#c#ApO+&aQn2akU&k@>3y%(E9U$-biQhe|y0CsGzQ-s?(2+2>J4^Z((1lhn&zj^xIT#C?3A>=u>hemP_K_^wAKX@#p4}sBG-<L+Op(%?^sGYXP^s~}jfY&0qe|T!+n0%kM6{yctSZ)l1aFHewp!NmUIId1zh;1HrA83^Cw)rW`ocTel+9&fJ>^owy$v;r#@ER5pq*DW6d$UOUz8Lc+-tt2nH^&c0ECx}<ko7S#Xp7Pco86~=@6wTC6lC~eQ`kq}lRf}7go>smF<0VOlHoj!t*E<YMuV)G47JBxW{E$=Md^;c5t({Tt3g^52G)I~hoN1?<qI4%%dcMibUTid&fDzfiaX&)g5niBS5Wirl{*04tBC)CfYxN$Hiyr=0@6Gv|IHTETX)1aY4On72=j~fwV<ZMM-9J$Vej`>*bEfVJ2bI|Y<pU_^cp7{ITG>*zBCWj|4pQF$ZFu?DCWoc_*%^3B9uHmQGrz?3X3&`qhAMBkjnDs-Z-jR?c~T6EL{IE5;i!3``0aqY#2_7_5gTqU%F$<lM|o^1?poS8nF#5i#>odlT2|BQ~CEt%U61V7PvnO*RgUItSFt%+DpAKTDo8!E`Afn)fvmwv-bV4cjHBN&O2bvwKovCG(*k8xe=*n-oY6``VEvGPr^dgTFLv|rHxV6`kP59@lXlzJX8uU#ekxje7XcHGtu`Bzl}nka{EFrj-fo=m6D3hmrw3mIt%_VmDAm~(|$<+=Hp*>+PQE|;meDL@+uO=MTPoFCM=GJ>a9p1kPdCYqc;U_Ks9`JhhaSQVVShkb?z}Q9QVLhccbwaYUTTsO+t%AbH`UXRtl}9gh}NxXEIgj;5ajQ=%xfYH|H`pyaai_E%c<Uoq_6-)Q6Yw&BU8Fh4<Q2$jXj_Zpe(~Mn|{qdNaal*XjKW!pAFnUv_6>@qs$Q__SCpZ0lAD4s|}BMeohFE~B;E^cE0Ol~A95Mh!T^&)6GV-oQwXOiXYF#EdGg!)+!Tq?#L2b7i0*2v}5P%2d(H5mCN02s0S6!=D!REJYgIAIgah9o%3y`<LeoSh26JKMlPhgzF%A%B3bLZ;SX^+Cko2xA}1fI0=f-DD}->t8YBvrRv_5#q_da{N{~lsNO>6jyHSwhr?uk;i%A3f>x1{2?hCez{+^{vUH^lr#U4g-g*Fn5};<|J{ge2R2+*=NbJ(R{vIHyZGtB?w*lzlBopmo3s|*WJ&I9dt~!aQZS%fiLLd_3PO-Ebb(jOC@S=N0Y>3(|&<}N;R1CE|o<oK;g3968po(rzm5f~OV8)#L2<AqK?(Dwwc%<#VXqxcANqCert3kG?A#2mq{1$<-k(Ya2ypP`~6g5Gi<wR>XsWbw-={Dx!)F63^rLW$JXe$P}Cp$U^x`W|cMhn$|@raNv7T5#{%R<9?OV5$-i+)SHApc$PG+*~hfnUjXvptJ`03ui8&+#d+rdLA*iF^ns%sxc`5XY1N{;D9G8|playt8_-#lTHR?vDP`LD)af*<AWV+<<G|k1fCT$9T@ndM`i0psz!#-f4;6P2tQ%eu3>T(DI|L6&(^_S<5CK0U)qH#MBa7@vK5%QWUzj8VtSpQ>Wxl#g+vsZnqx>3}S@zT+0B=m%DBgqW^u6%(^)$f@2U13dF}Uzfig|mY9=Xgmv5<B7yI3BvG_2m8U=%!e<JLkjRKpLXI%>Fxo>q<Fe}<WF{0of?2j*9l<B~i+A<i9iegEJjdFQT7g6oMUUURyr_zhiTGbT8*OBx;<wuTQv<!~ui5`Ut@)<a?Ufh8j~-Nis9BDNUV|Jq158*3=)9ZVRnJ3fU`ON%Kj>(ucd#h_n%XPE>G(o&y!(m5o}R<9B(rH9uNI^w<LzV69B3qxY-3%`0MgfnSZLvE@Ht#~lO@-vE0R=dP3@*j%mO?&%vnEQ0oOS_?s@^OUv1pQg_DRz%lq<yq^iP+CD*7(_t%aS_ShfD=r7lKfs-2P&UB@OfZ#1l`nd6O>9e5MDUtT0s<uuDQhD>y?5<*A-?;)k$<xsvs>M>(whBu4wuhYkq1ujB{Tay-yhL*RW6tUijk2lOG5TF}1g5KlBG2^>PSpur%~*-kDezp;8V-A`6alB)(!lLX3jfWv#aO;Uzq(rC!k^+N?_^KlAKsa<v{FjdzH5KGhyu^Ys9gT<gYBgWzQzj_?Vmpi-U%Z*j@604clq_3#z|I2B!w$O>8E#~(&QftC)AZe)fs^aQT)haFdtB(vtjkKDV=43<p%Vt;F3DR;sPGnbzhJBwc4<ltB0EG4cWqTL!@HATJ0VpChh#mIV04t`RddM|3;VCC@o1>UOsm190z(4nfw)@nsDRSTsU*<>&zo%Rv`;)Fk#OFGoqsl!rVfwcleO1T7bPOR*%<%E2bY|f}1cL)6mtf9e?wI0Bt0_x>wKD5D%E;4x94{GGN!5#b<ubKdv{u=}EYl##KLln3+y%cdrxp*&0|zhF2LmsX=eZ_F#ft{CJf_{5A2a3L`Z(VNnxj+uMOBIi!aB(T46yxInW6P?gNUNRv68zyM&qB(#5qApqHMiS<4EhNrBb7sc9xXCO0Z|4Z;9iCHx6OTT!zxMVX3A5zuefE*}BUZQTmK*x_ppiarb)Zb4iiCD4ki4X~p61H1rxIH&1E=#fmW^~ut(%$&nT3XkGa@#YojLfzg)NMmP_i5%|<J;6aa84i+odNr35Itzfk34%g6BfbEo9dFZ$=UE84(f@2Y%|>c{RqXmQ-9E5r$Zq@hm&o-Z`t9YP>FwT%BS=wX>ba-dAyGbsrOLEeCY_d^!yx8Xo>g=gdszp%p6Nj>hV|vMj@%=@hJ-MSRLZK>@`&mQv$<YmS^N$#5W}e>>S*(G+i97U$8RZkE@9d)$c^^kl6gdKyKLx*eTw(hQq*SeIH^3c$tS@hb2OqLMl#Ii$+ZNSA|;n!%({*XBseIqNwZz-v~esvWGR9c>P$Idu}5--S1uyk<J4Rq4$!|)*<lz0)FR5T$Y4DjtRDy+D4S?epRo<@pkA}u@%jpnYV~29b4k2ZJjyzRF6+=Qr?j1OlRbmQ*rTb!B6o?N`Ry$CRY33ffwc#YRva-Tw6Tt5rk2b?a&!iZN39d>TeVT7H*tBTR|qEHd?qM%Aw0$=-X|LfB+JSM*wyPKpZ3mcxDVVy<-um2xDFIG|Tj+e1Own2cT0$i$dOW<z<I9GvIW0tzoteafm<5(x*pw#T1K-K(N?=Iw{XB9JLcle-mC{;*(IzvA5>Fk!n&vSf9nXks!$1CPoOMWCzJk81B-RpsE%_U(emaa}R&p7K0b@n}d!V`4*Jz=@xFbXgnpw{`k;-qi9pxm3@rRd1=n-9`}3MwS0<<9k`lHYHYd7OJN~()r!yf)klEsP`BngYzqJY;J8$TqOU4*00H+y+JFTB-Dx@jvBYQl0ssI200dcD""")

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
