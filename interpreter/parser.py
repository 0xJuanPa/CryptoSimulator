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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;Yn*9&|LsP0S;|#u3Tl_>$VG6M{muf5|xS3k1kjXl@4U`gv33RoQpLrsnXjXaq4gAMG-CSTh$|`W_rBSgl{P%YH6Y!HdO2QrlN>qDBx)uhX@)Ws8K48X<^vhl^0~<q))JMH;^W%yUG~$r;1%2pwJKoRxMP`EsR-2RlBy^<&vEuj^gIi^!Q0s6<|F>0;UIp!)1UPHs5>(suv|V`%R9~%WbQ^K`rrd!8>T@4d2-o*}{>nzlgme<`3TF`|;5!&|i(260UykOn+97Ox`i8dleDmrheF5R&7zvcL!o@v|N88sA`8%6=WNpCpAi5_`j-z!a*afo;;2U;K%TA>5R5qLNZc042}%1+o$<c9^poDp%Q(}ApGD`yzXPelUq8VtQdyOayxqY8`II#)%a8R6n*Vh-59fxFbFsl{cMB0k(Hpagz$rro0tr}DJ_7#w82L@9wQ&UM;brhQsc4`X`?lW)ep2?9B%5PjxP7zH`yqt9f5uDTQNYfwe|9c8JhHo^+{Y%wa`M4?x`tS9AcF4j!`8&-c9kk_lGTA*X=$#bYD0rhRmR%AM<$?(Da67pkx%$BZ-&oi$EoLT@qIg<9)hq(ak~Rp0Zg@{h^Zx8p9Z4Er7^)8120yIVRUU?Yf27i|lU890K!#K(|M`JJJh~v!EI3)*0?)kNyP*{lo9>2?peU&GZL&_r##7|K(!dYBNN6K=SM$0P)$6AJGnDI5*CwOu>#mNsQ?$HF5f4L#Y=8W6{zNU}J1d?r|44kJGNCx9PVqt{Sh(+a$MTsL_w3A1{M*qE)(M4L8B3AlB&5?)&Zkq*Vo<c+IdWUwP>QyaANjlqu-HUj78;BVVv_?#}xrf^{K6IQ7)4L0od_<5-XXY-MP&EoN%W99bE7N<?n%DxI;_xgU8quuubNX*`kt`3@L}0?ywze)`XwKXAV0`5bE43|hUpQLb!45c0ycS*Py*$uh?jU*3;Yg+psFghDP0zLf2_xN_!`*iLKWsb*W#sWcf9VZE9W)dDv?W&&f!DyJ%e_pQn#%=!6nIGD5+WxDylg%FK&E*Cc9O(nZ3{P0Rk(=rO&Ohk3bQjuBnGpWn@Z8uvyE#sqU9?CP<)rxc;!beqEQ;eqIf<)dJ<oYBNPW9`4lX5D_i|2`Bu&}VKt}V}tq<37E4*pL$6SGKHuGJ=0WJ{jioNUpdYW&hmV30$_&Yb>o==r@M&BFT$)|%7AGNUJ~4D1o_i>NcozGJ_y-f6A$dnq29p=Gv>1OjLKgb(oBx!Y-Rrf;3>U?XM9h&C}*K=Kp|%L~=<+WkMZJ))Ga+1R>I*|shUQgev<brB%{_M%m}eRhIi#$hKvJNjmlIpISKQvlo8{egg{Ig)Mi!vzWr2fW<iQoMfd)5#f?g7ih5*#HLx=1UErNQD;y47qLE_Beir4dD(bZ*wzp+6I;8AE9@g64%b4j?dgU8JxmvAR1{~vXO<~+ZE}F%{rC79o>Nffm=!WH@2GGf|&IoS+)BirFUOiRziiFPNHGykgjzZ+CR<{yplXEw}L!>iszge&B?3C^e)sUH|jTdckbs#rSnV3ei?F|+X?v^cVGH_{Y)QW0b8E7QjcDS@w<8NE?IM6y2n1Y+fn@{a;)MVr9w;cMa^`r)(K?KvEii!!0U2nt^>a@kBvhXfa~{PmuA;FjcS9UANhK5Cb7j)zS;f@=7u-_X06@8Mx?Qg`7{u|MNDWR1$O%9l>ZlN5T^2MlXvj#4W9_@^eAGP)XA=~jp~ufG>(2~P~ZyH$5VUNxVESsui(u?z|lPGr2MxWsGlT^=p&s)8)#rkV%4OKH;P`D7^(jRFl|olktA&CU`W9F5IOK}0&Y;TXarfSl7RU5!ByFVs9=Y_uu*@1qL&G;=jgX7dC8E%LKEqM1lBcA(uqrbUT5EQVEz~6L9liziaDeKw2AZiJz>=?e<Fp`UzO8s;L1mur3R2=#Ji%|$zskz6|d~0;RKp}?5>NmJ0Zo*?_=H##XoG#=`8$mG}IGR4PZL#kO=U}BcP_SVP9E!T*8mCc}hCa0)yX-?&OcuD2a7F4;v)WxdZS~?z)&(*p#RD2KRAph)7s~(7O&c*K#o2q~vhj^2WVeZnp;pA+!=8i<&L;T)StdmU+PCvTq!>Q6id~${Zt&6O$z=j2BdyNfR3?rVo}nog&9Lt|96e^D}w4E~@lMWs)GrcYtj0TLQ<u{E;lDi~j`A>k#c<+Vuj6{JRzdqWgrQ5}*gGy=Qlm1CyB;{F8D#fK{HrV!L}w;2$J`etos7#p*J=N_5vqpeUiZZ(pA&{rjl3I<#-Z7~f%HZU##-8#4C($Rw>v<OlWWhwKZmivU(KKiis3Dz(Dv5y@jZNC)fAYyzmq-JryiY8{;Y-l$L(Bq6#?&OTwZ(f!puvD|O0Y>3dC=RLp>H`A%nw>j9uSwG`2_4VcHHGmhw^900ZQ~EvXTC_gQ3;?cU<sV<8L<`JF$zu@m)PvO)AiIM3XNEOAE0Cn2;91bs@a;+$w=2~Yr;spNOVJZV;Q$zkA(=%{9Ts<$i>!9`e_?`?{4KOaBVw_#U1{akjE}0-n>o`1UMd>^;e+Minr<J?)yd(;X9fSrj*qsW*Z4DIcKiZbr&Nw>`D$O<j8>VBSuW!$ZD$eW(c1|9O3gm{%cny%y~S+QZsBMQxXa+8!->?u#}g85UVxv?QzdNR`&XD{j}t=*;8lx12RyG9Oqor>ZDLO;#5oJy<V6`^G7U?NbDW02WD^(hg!8*e?y};{grY#Ktfu!O6frwXPm`U-z882-rwQU7nweYjBbn`x1?k+rq2I8=DOD|q!gIhhsT<^68Sl;P09_^PGUyG|Cmz$3Va(hK9r7(dS}@vVAt(3qV?MHwV_i{&Eb($Br^C?Fnzd95kiWA9IyaARe+e@O8*qg+_H<Cc$9Go}`zuMtH7kLBeBrO)ClH2Gaf0SNQiuc`3u_R=h@rTjj}fj<6m;VZi{i^Ncn5TpS}}n)z!~m6PyaTR?;pqra91oA$|)8vu}8uNYkYcvS!eUCz9X4T!Ws~T|DS&Qb$ZYNS*T%Uk)%tq*tH#3Mtd&_&Tvn|90>__CEeiST<9kAeOHV@gWc&Lb=Vuk{7my@<;0w@O<6=5-GZWfq#jIP9x&2XANI+x@1Jj(ke$fWd1(te?B2!Su~FT%f!f*>-AuDe_nQNCt!JP(mZs+lf{vj6oiG+)A(GKLW|Ngbsq=R|Ahlq|b{5%zNYH|_0HMCA0#IgDz0n=z+oWEXD*zA9M!&GR<6U}?2S|!8W~}iX2fLL13?x4{%==9h03)t5g$Wi|DMJ{bsc!ozscnZBIcIbVC^YsMJQh#qtn~21b^&h^U2i1?T-KAg0dNqmZCzB&07T8a%@<Nuk&QGEBogT>Z|QHbLa5p{j=S`)kx}@?>YG8cU!-MIJkS#yt?}B!UvXL|F?;rKUog9c+J=vfXHXD1gsA*m!6`+rt1ZRbWik?32!ZB1cPH@&zD6vv%4oDIhw{7Dys15#8=*KTkY#XecNe<Gf|*=s8c`_o{!nwYH(&lj8X|iW|G1z@p;tFxya9EoKqBJ+f_SqCt+;Ed<(fMn#851Qe5Y0oys%kFrD7^t{`w-c^AB+P#v)kGDdgq`#s31(qWOQ{qWOn+ULxk=r)=}5%7zfDc%cy5I-Cbzm5jUmj|P;IY~5%60jOXp4|8%|HK{COnFE(4mumiE4^{(j1}F%bH1!t-2gm?n=|gM2Twa*8mL=H#9=*+|#h}`O?PgB+w$4%QxJjv<(nCN&@HXs^tUo9qF9kB57&9*j(s}%lJzoGfO?Dm;<lT72f53H;5VNC!3OtSnJ)u5_(m;=I;MvdrRfOTflkX^pekxhN<jC{^OpW&~mV!<2<ce~KU4Ay5B4x;8I~w~=KLZ&$9+P@W<HvN@Tu<2Brp&9Y^=skPh&36$J=O}w+mszj#2S-xF2@N5ELib|La{FUl@s4O{&lJDR4<t@{#l3_KnshwyQ^OXX2DpnsGtC7mMg~?RrPvcqQBTp0Lykal^$Il7T*hwA-2(}ieWZkiQ@!A{)MNx+5`A~HfWQEsgdLT6&mIm&qM#?>t8H)H_}pr3(6A%MRi~e)t?Za`#7zOP9FofFWvb7WsE@#?%l&}`g|<=zwh;Yi&xvE(`NYEY}lpI8w<`0Kxb1PS74(nrjdDp^=Eog%3%U?blg4-aeDr|%^TJ+(IfAOehnjYkI$(v>IFVrnHwSd?h+f$3a>$4bYgEY=9@}A{%{Gg<+0n!u}44^Jb9FxE>$oa^ZDawzPr?70)*6FJS1+N>$B5Ni6HW!53bP;h-h4&*DHf?ubC{+p8J&AT4mt~>|K*z`P75HY=^~I35%m1)cem4ZUTTVYQohmNVK~44h|AopHfm~F={*?#i7^fhdlRv40m%YZl2Ns`RKoSSzLgCiF~A5<aMS@3Ju{<)16n_Bp0>D&qo)724?8Z)$g0wp(mvu76Y^2OZ>DD54_2&7&&z&r1oU^FxyswA}9?kckAf7Z~xh)@!e@6B`dJyq9-^81sT!yiPS8zdsIZDr$IOWD}Bj?jZAa0S@-2(l@Gj?;@nB1DcMH})zT^js3z={Hls3Zp>zcfIC~!Yj>qWwtH@ToJt^i>Ft=4hnrWp89^lDQ1~5C#Up6rfxYBZ@+P(mIpi)D-eW@YtXG=MWOS_+nuA!h)llY4rPJJ?~l;>a~^bTe*{fV#~!4*z&a|}@R@b7ioF^C9smese4-6eqmHoy3`B^EN_6~MwMbE0k5Jn$J&8^x4jR+tK*S<nl5<NRA42fB>!?Ct-L^Is6tTbvcoB`r+m%X}4R&=yb0Wqi@Q>xU$z&a0~*+^m)d2S76=OhCZkKUXg4DZ`AdxulxpZC44BWhw=lAhQL!yGG4TO@A_r@^onV<c*`@)F}fXL($NQTX6#nZ38MYvGUzVKo7GVNlZPG<${t)qn4!IaSGbO`<i~N(6$-Ta&q7rNU{)%X^8e^i5t_tVVh!c(*tS?szxYkSHS`K3ig8U%wG$lzx{&3mu1Qf$$E&myZsxuQEuyZcl|LW5;7C=2aBYkb1qP|>FiJh)o0mk(6=WSaozT4M&*@UtRSEn_v_e$V?vpxU>v)7MopJvG$OGIeh?6Fa!?sFQ+}|LtM(GhX*A7?;>f0UViK!-G~tcbRLkspU;D@;JR<R;gLge$R{+^O!VAmBb;i_{&V^-+dQk_%>2kv?`rymQ$0dJ~(i3F~Za3vy<#mPT@k^PZoom}8@SktuVU<fHiKph%_*{_|uw>S>q=5?h8Fo;Dx3cj-;0!B=U2XzH;&N~ZiIW2&aE5cpK>bkAqYi3~l25Iw=stA=idl+v1gdgJ|GjKwxizjKb3}S6H=`^Aeu1Or)AJxNMAX1-pgzb+%Ic;UK0{hpAXcBBry$Cg%^XO|#Pf5O%W>HJ4nhMw&)pOR%}Z^Rl5m|DFL|+(Q-Z`-ryg#H0Sy#34U|E?v+Hw+Eek>@e}W-NREek(TlJkzeaY_SoNhHIEJC^(=e`29=w@{#d`fi2Ii7d)GROBT&2x^k;CJ)L-VZ!i25fOjL&Rv+A$zBU=(rWjP))%6h)sSf)M-cH@tLwYdf<p21<A9nN^j1Ec#`Q6`+=w!?QK&c@AXMD*3=`3T|836nTMn6Vhi0v=3!F`nbtre*c*B?eqi<`>J|z5SIzb_8tTaP=l`ufe)N+2>kcj_@oV)1Bqp~&Dt3&4Nkhmy7_vBQj8cQ5`;-sev6s|iO4Js;y=+?J>mFb9wVZPUM6xDu3Da;!n2CTnk5>d7F@OCIXrgQLV`l939E+Rk3OOq=6*0XO!;AH5dVSZv4*B~tU9|=8Vpfg)>!Xo=8xS}}23Oc1g-D%`+tg<F|JpO$h$xYAf2xdA$5)xUf0ESw^*^U$27(+V7>u)e-%Oq<p2g>Xo&c}Ya(}29N~uME`6pcCfj8D3Zs{eD?a2s=?O`y^5WrV2h$4^Ye&Fd=>m7pp1wmXS+v@zTLR}KOe-lP#Ei-NZT6z<3LxaGm1{SeatHR|DBKE5fX%1V#Y+_!IhT6m;`M~$|sZ@Pf0S6K^RAi&*FrVYe%~fl=^>P|wLWR1NlTOxvMW#+rVkUlM5Az<%rWM|<P8IWrP}?S9vmUp|T*jHhO}>rj&darp4?AGs3#Z6Sxi^vo8~+tgi_S_H@F6o#8%$5oGI5hM_eFs&$-U7-4H%=ozRQ}4`qhiSQ!2VEjXhVlFk5}aq8LYa39uos@&3J+yHeQs&A;O@Fw~K1#~qrIDvv84szYMB1iSu+PQ^^Uhj!DIlt;&=$kTaf*R_~i*%)F_Q>^m-D$N5y&`+YDM;^mGwMI6ODP`jyiBQp=J)Mgf{ZsV=P$23kc1v=sbKEcbplv~Fr$Sm$k&!h0LalV5U9|NXnQTB&<&;e_+v>q%8-!TWE~29l+i~kQT;iJ?O@|Tcv#ey_B`#37gxY3}rT(d<_<3pcGv|Y>OF$9W6d1vCO&9zI1n^Jhz5lxJfnlZTP`L}nEBMJQt!-4cKKPt35*Uez_1ur7$<2KJq+;xxiiF&wFt@=iH#|y5DSayo{)3J6YL_`(gK1YOs41=vxnh+L>vYUInsc6te=#>~yD9|58!ZWcD}t>DJy*D%g@@;DLgLc`E{zRanPukx)%Si$q5Qe*yaXYlDuS9dUS77AI?HQ=krd$iV+z-lChZgOXElx~6NN4egt?~PSWyP4la3B&`)V2*i2}!4IFWX35=nHYj<ectY*Pe=ehc4G$2W%PHqEOmd-~Y*yZ=BA|FKaW<>jp>rB{KW>Rc7$4&7HkF2%6x^W4^jAaj@$X#VT@!vGOp0AV01lJZq3J^W4bWmt<~Q9=NV#~W~b1~6(Hvr@o)WjIEJ`DNE$?(o)k=C{kT0|!aVR?fZt&4XL@fgxn-Gir6byeEePuSL^nk*<gGBcM{I{sxhoxbON%vPD779XK+JDu9}(Uo{iWJ115@>x2PGSr-pRK^yz}`Tjy2u=MV`_PS%#Kq5s}>-cXD7>88`2_G};qBF6b5juc4zG#M+8&5rH!v4*quAH5Nz6}}5QFCaeokk`slB7~)0_d8NgdQf{nI7Y?c&ko{)S`>Br?{~})v%w0O}l7(QAnGLD3ih&;MXw0w%s*$6+KelVd;hMrFksXa1O?@7FGqeTiN>Z0b)cWRow@qD<O8N)$cQG+%EFS%NwHV;WhZzJ`LRl2CEur!FP_^uh_fND=1t0^no!<jdecBBz_m<xY802s<BDhg*>`4B_0{Ij@v7s`pAqNgMM~++`d_gLf5KR=uZ|5kXpCJqLu7~oKzR?v|7Y?L$v|(7Z*(mJRPR&GgKvI{Le|}*60mQVDM{$E6><tQ3sl`<gDmV{t!7qtMx70cD8?uhVXHHtGv0<n>D#_oOr*7{ZR<pV*+0rT!DkuHY11M(fF-Q$!w#Y>=`_EX;5TU$U0LL8R!=K+yHaH&OvORJisIlRe$2Ilc&kk<|}oY14B#7yr)pdLO`?x(U*24M51pO{~UDXS`Kr|JDM~NsUqNRa;G>X`IqJJfmV*Q!o*}AV{;c6%@=RyLNJeN&aW>%Z}w|R;DT^CqeHymy<)du)iMe}$dM;;z-n8LdXNH<4ep#<Ctr)s1O20<&v@jaZe#$9q|1>3d@<8^QPG_<@)BmtiZO*`0D0qh$94Je15~Sz=2^=Q1UFUm4lCZ>Yrixds1CLjX)}-NB~|&Ga%N|h*5-5;$KEq^bSz8-!KwJGe~@u{oQ%UTMv}XP%fm6GUg|Vt#GG*XMP#UZw;YHn#e3YY<n5B&*4!HfFEL_COHyjZ=cG|*k+8&P?i>Z&<t2l{sU~vcY}9F=MU?uhFeW1Hf`v_!I6hkoFHSvKr%h!y^N<qNe<SFqy$Q!rYYqiXNYr`9oP6(F<7#c`U>eJcYEVN<bFepy!OpI}47gZelzqpv2#DCs{m}Hj@6ew8&Zimf`jGOfQo6>a(VJF66lScUB8<YPVWZVOnDJhiGbBM^)Kb*~Ghb;iY8?8>S4U{gT>oy#X=RX|*=`P}Gg9P5D8q2<M0Dm`@hqY(s?%{JOdDD^qXg=rEc!$VDsaoR$WF16@UV4=P|Z)h!A)`d+Uz^V4+-WEkl3ZVc=lQYYl|V>hGe!d?xFy8BXOf;@>Wa-F16CyQK0`>>-N<#j7-C`(G6CkY;|%BWv!rX?8V#h64618tAoVqDts9(521D<PSraXrR@bS2<|`|(sWz=_%r3I0wjOxZ~A){M<S(BfSOqGQ*?A0C*p7SUBL;O+IHiCnyQJG4A0pAvvsdwuI$f(s5J!G!hCKjfetq{72e~Nl!7ps#MK9C0AB1KPMMozo8*c~ydc6=o=`7Z7|)dTrmFpl$BG7l+EcE!;LB|M1{_%S9h3@Ni2njJLM8jdyAam?M+iRF`-2w^;eI=j2+7}!;4wAy=gICWe-K0Fe2j2}0i^^s(-&OF>=w`f>aayZGy`uUa%Jqd%5lwnN%=e=^BlAKTJ7uKt#XKTF3GFCXUNP#Nn)jBh3r&B0`0wOe{)sMGxO0mwta+0j}h|O@%Y*0hq8TId?~i~*C}?ywm|0J&#8>py!cc^E+o)EZ=Cg04iOnO8{D%9hW_MdqV@NSN#2&Lkw5No_>4iP@g$m>kIiZa)o%F}8jFeS!oHNyxpy#+KcCi()t^$DN?KmJHB=jZpvPN_CtS<4^9551&3@-xQeSsPZTCPqEkB^%0H3Fk-iqDaQfZ@I7rNH}l$o%U$L;BN#@#t!KC@5x*Q8+=aJn&HUk`|zO*a6}tS5j3iR(6Fzq!>=In`y{hPX;sb%;rKi`T1Ou3gpoo6Uf<|4(wwo5m?X@V$^45M;!Iyaevkz2u+C9BEI&0t=0>1F<#80BOxuI~+xOsl-qFu+Tc>wb-=^!FWlrp~HuM_zf=n@g^WR`1<BNY(5Z<yiK3sRM1`_bT%^RJ)RP$`7LXD$$E_v+KTT!(g&*BmpM;Us(NEI$P|VZ_HhFnLC21pfpacD^$Nq*1*prKES3NE;cw8w&4ul(SJXi6)@LnFoYF+BSyb2>id=p0mx0d?;w!^4xbRq<7Gb4!VO+Rw_Dnzb;_BP(-%&N`m{r!u^Y2bV_)$E@Q}))|Okf@OH3o?|DV1Z*e6}NoRZW?J5E6P5V~>#jM-Cg84%4tWkvi4FCM%~=@sieJ>jV*fac~6I710WY>lTc#Tm+L0G}o<+XyDR6dOp%($oUS6C1#d;>V?6xX&kiW!<Zz^lh+otXy~4q#V?ggI6=V7PDgPiiU?^!M#F&JDdqDFUOx`w{BgS*m=d!HS6{(VLF<tH-zcDlqN%dUUp0M$uGS`0y>1TWJqhBRFzxY)`Z$tFE_7W6Mq$slW6X~+f84HgwozITDtMu)ujQx_>pP6&hF9tzTY_eU==}8%fgQ76u!rfbIwQmAh3WDcrBVL>@?MLS;DJ<#&G{_QRuVubjl7PqV;TNDnY#KuG*_0kO6iCb+oFi2j8kPbH&1}>VqRCO4kPNrLb+?NBQ4UXF#|2m&0fdXBaVNxpW&GJUZ_v{nY&y28~F#r*0pM0N_{;aDlS+X<uIxL(Ot%(E&QwTF8D}_BE*0iiqR00fpstcH6ZU>n3|<)5_77LJ<`&W8*O&8S>dl4km=G;ceCFfAmt^dN7+h>)#>FY^Ed*OO!N$%T~_#|cY8w+4Q@ObTZ));J*z$@Cg8d~E*S6<DBxiyAE+e@gd&}3ZaPh4rPVW3l07OCs^kLK5iOq_PR#<d84*VnqneL%Xp$wFlS@BFfrMgWos9&h-$h)ediE#J<n^ig@@vy@Wcm;Qs-JJf&kTp500Hbf?2-il=-_K>vBYQl0ssI200dcD""")

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
