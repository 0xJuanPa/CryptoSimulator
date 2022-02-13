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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;ru=-K3xDn0S;|f@Xd>FE6RpTFOD`a4BnrU1BpLW7S3^L$i|{j%98m*9{jxrc&nnu<MAf8$y6)i$&5e)tpac%--fa%UC7ETjBMeP<di=3`@Xe8<8X5b15#)0%=3=jXP7dwpUgh!tT5FPN(7HP5l>N}1Uk@b9P0%-OGr`N-YP35q3Vccl`Cp_NLjvOyj%~Aa*Kp0Z`j<^X6IgqGlhp3CchSDtkcw;))Xme4VMR+_4J^4R?R(4o^YiDx=BjiCF;N-5~XV+lk|h!nhEn_<Pj#H*yEu0JVt3+U8dhXy4L(itI40qxR!R$rxP5+rJPIHW5GmWEr#tn1d=e3*gN$`$Fbk{^42jKfett=;-$Pn7}kM?oh_kIrH|}UeCl6Na^cI*2Dl;Fr7{WfOM9%n^7ax!**bKPCpvoCC$!xp5)MCwK>{Es*>b$Bfbx$x{B%=%sn~h#n7~TjY9Zny{xEW;hT9ACu_EhDCIepdE>@w<U$4en9_~+RW;11@LW|oiUp#hO5HvVDH)XFy){by^0FD5nZcrf{xD{$8yV_0Bii9)~G86!gIBw`<RTB!(HzW!Dkn{#G;@M%GFbaiCT|H<DP8&_0@G*zx-<v@sZE-klh3)-Eggv-j_S=0o%flwfgOp763U^<(Hvm86<5j=-LUZ@Lpe(zPy+Bi=q4LR?vO!UfpWhY_UUj!Z=<;3v9B-c|t@WN^n7Nj17KbL)z6Mfn{Dy&A_hRzb2U&5OayU+98=Vc*M=-g9RRMo$I^Q!9_?$&dJ4@4s<BH6jq2Tfcu^%Cr^ml$U?=UjMs$q4e;a^aQn@!!|2bjch2r}u?uOIQVK+^I<K%QyffD#b<R;hk<M_R6l+LRKvZ;ReUS#pMZwAt#FznQwzI0B*b<}@I+;GhAn|J8(6=!Pf7bV*^IUDV8w@TNZTouv_3Z_CnR2|rQkS-C7J21zFRiaH|f%ZmXLgM&w1tDg)kLHx9&My(1wb6!2v<#2K800!R(#FLj7uGRRp9b#4a^fuc<=o2hvR{>bb$zt;xf=amB`%;H?W(17mSebNA1@GHKQ4|v%jXtwREZa?Ao0E|Om5{TQvhL6P0if}GjM_)|byw46$i(B#kQ?KnLs3=&ZXMs?2L0bOy93cnAJ>133Zuj#$sHekOjb!cpVhl1u+9=tpk|76W3X|1hcumt(SionV)_WD{(NCBQPi^&lYduDSRuJYW_<I<-2o1-zyafiLHac#Mr8~xqaf=3N#6B4lZdjN)=S7ppKlBusge|5SzqbtSVyFMR>{>a^ESpe_p&~cXv$#|X}}-tz24mJ8Xwp6wK(*aj5T|)%UTsk#*)v-BoajzP#fsdq=cdvLMOJO;EGNLX#U!Q4upsE_fH_eRhZ0*DjNc8+q3V@)&k27_mqrapSqEdFr!F7dT&p*1RjDxS;B9Ej6RT|Po&||2|)Q)j-TGl?xjYHk$dhLC@H3Ju#_lKMh<iP*=<x|7=;Km3G3-!mZjilc+OEmbJq4cS5PiVjEWzxQJ4erE1H0c7?F`mq;~siFkY^o%Y1=l>$~}uBVpvsd<U?o`??QNCe*y28MTJP(8uvVnp>tkwML6pXz@1)U?!@<U*zd72s18fx-JNdJ#mSGg?z&yw;7zkvQoi1(;xEh73&Avm7aI(nV)NgHNu|rzvMqi`ZkoD8(6D-C3^lV-kbQ`H!GGue@~vDv5mST1nx>8hj5T*9kI09DI!-p2akpUcV-dj7{y?SkDpVb5%qCl*B#+&0s-lhx;EcT?3SFK@|B?|i{#&*1=#@gY(as^L8@~3XDr}AZBh$aMS&Q_8EClaT;r59G^wVv)qoN(q4(57G+WKk*z$T(ot<K+i5>xf{jd$?=Ex*3;wur&=M+?0fnF<#8RhHSYx7OJpvH&s`7U6#bvWw4&%4+Y<p1up*A~T6lWZbN=m=m%I8uq;(*x@E3TNdmCB&q2hlFLTb8KzObp)n{6c-T8?m0A?4!6GlLa&8+bzB-iw!?E?rOOhNyKZ^8%5!)nqDx*Zf(U0<r`9b+l2(*<w5B=OMe~F0)f8fbohC67+1oZGn+N<)tK`z_pP+_y;SJ|BKhS{t$YjUiTJ7gR+aXKmpxsRs00Xv!NHYPo#>68Gx-Lbic=blMU;?i6*vc2uoXqqlc1kIWdIl3Po2m2~4%_I}EHy1h4*l~AdnPQsU)FR=Ss+go{ot1L{g!Z~c%K*zH_pvKXHrG#LlRy=s5E6s>p%b@o)CzCklk&~`AG$?__#OdMO`XLWj@lx1qi(34z?X_fvwjWYZM`5J-eK*lATM~29Yw<4SaVOmNN^FXgBgTGY$J*t4@{9^NS#}Lfben;<ecxfwLuAurTsmSNuGpnV|+A9HG8)y%239@1A$D$@Up#6P&Rxpu?c>mM5fiP1@mL5bJ=ZrB2Y7;f`*CF2GKJjvd{LSV-q9TlL&+EGkEVAH1>dFI@?wiXy}1l^Vj!-QSgt{7HEsA&R%*Cj0SjB}gtw-XN>0cZ8g>k~T0<qHglDtgk(Dv}v@EKZD$W0-&Ev_oeI@TvdRsWyV9t)IsThP)`+T1AT03>{?%%nU&{^DcP$0LDlN=tB97(y?sK@j5L#bltOLxT@wCbu}^PKea1wihkM!&#)n9xIjUb5qKF%%B9q!>P66F^kYU6Wq5rs~yi64>lCsYkf6W-N?{}`Z)vo>7db#WE8q^cbZb={MhUy%RhH~Q-p8%kGFxy|0tAhKcFw68rLPnYm<LHmIal9yZ^$X8AYNY!2Onkv+^sc9aiEeqhzr&ku%dGA{){2o(386~<;w_}e$9cE}AqhFVv&yTi*D!MZm2R^(uENP|?a0LmMD4N0WjyQvn^C1B#Ia!>0(O`Hy=N|aKfBB>M^BxK*FzzQZ(A&nimN?6P*PKei+vaOmz}oWs>EoZn}yzs*Pr(%bFdIDobwO%%8PCVv#P5xnH8P(N1|IiX`S9(xiF&6)A>0#niA~m-{BEkLy5NK_+W|3?D2R`=^fH64Y6x4;wc8QUz;CrSmnM@RW*!#E7GBNfgFBd^pg(<>RoU8oASkLuTgTvz-;K~fUH7PX4)KGmdVp|`JqR-o9hKkeo{<5;dmfRq3;|st<+S>DCm?-f8dII^{-PpFL{OwWr&_?FVEg`NWgQa)ytho`~^L^7L45=_OWd-N9O8rSpeB)$dJj=OSt+ZDMn2jDa+A|;2MdFr@FgO0#&~xegRO-OON&!QtPOm-SJHEnoxVZb3!n5W;IGURRR9SFr**hI&4me|0S4eqjht;y@;s_;37LBKC8vN|LsPE(u*_9w*!ChzYe2XFe14L1<3kGpBVA=-EQOL(F{8V10eZ5q{QDNrWM{jgMaU_s6zJq=M)_AQ0Gf0$srF4#K+`8gg$5g#u_cx$+)`=qfpWTGwRhGezQHBqEl>0Gmq!dD8}eS5x;3<SGc#P-T`qzxN9J8z=C^6wwAA<-z+CEoZQ(cMRW7t&63z5l|AuySQ#KF5i{rQ_>Sb`CCi{Q#G%YX{{q-=Fkd4}%o^!P*`CTwf=0^Lob?nVwGXs5Zzq%j4sNnR3&qv?*tXRNvtK^?MK>qUY2an2^pd8gu6$+~KH8nT*R7MVRrd4$T@+oE>ypeJk|BIJO6EMxJwKkf7L+uy8uZaJW>dK;DZ-?zcPJfaZewJDtJuJSQCdX48R}{lH>}RsGYt)$3Jit6Bwq<ScC10O>Xn|3CU6BELj%<MAx!X*oZHUN1UsfTUN}ms-LM_yOZpYZLx>Yliloqkjzvo^c|F>GDZt&iw9tma5;m-pCMi7GP|rgF9*YT0kkmek{u~ul1W8D3!|)?#@8(%a%e`CLV&YE)OSw8(CQHpr)Nz+?g*B?<?-AhRsPxCo1#A>DO4$0%{^iHc{MK3L4@@bz3PAgXpL`a<F#Fy?#iJ%H6Twsu=;vJVz<&hK!mF|QEl_a^K@2`XHR<}R@OAr&BouLqox;-}=TFun{dhkUT1z46CQXq*9U;efoZsXkY+H;h1NJOX79mGfdx*$tqS%**zOK`FFvMXDw%_Ve#>hhHvtr%tR}#2c3o``3D_t2kdzX-OCRAIxb(R6DLXe?i7TkGdb-W4rlOfGE&r$n&h=X)s@z%zbC_zip-&<}e=R{Y2z{ge-6%#&Wem^wlnf+WIAV%xxVr3q^8|m1^LNa0UmSp;Lp!+55J-W3+G>8z?a)Sx1!Rk^ulZ>eD|Bli`pD=AeDQ<s?WdHlO9ycqe?g>Jw`*u<95)}~U?h7C=1(#{Dj~~@#-X+?DKE=){181s$61BNQe=8z!Q9^R}(>_YdQf&zGmgzGnY0-RR1ctFB6%{<`Hg~XA$t@!X@%QW4Q9ipl0bNrhQx~I^r3l=iXSO;IGHE0LWXA-sIVR-71E%hH0z25=c??Sde#;nv7%us6GB;AZSet34=|lcWB;J=|l&ND{(ZG*=2Q>=Zes~{#PVPt&a(s66qd8nL$^SUk6$&4|HW(c#I?SO+`Gr3WhU~tb{6f=9>F~q@bHT>gPQ?twAzD|)2(iwM7iAx0Pn<c%?ZAg!+W9ift`vs{EJS%g%|Ru--S5>)K90r{rcXwh$gL9V^*qn6%#!Aw%<+gxxpz_!6ZZ^vwr8h0T$nJzA309tcQ5vm&7m3TB5v2IIy#sbJXs)lS(F3y$>m~1u%wTO%sAQt_7;(&$D|dYv4|mNV!6p*4|&P-o?J1PmmJR+?dE$vwW-Lq6F(_oi`cpiydrmM<YoOkg8a~lYokroGZ1?XszwJOq+K8KcWQC3vQkju4*9pWev>71Z$=x19Q=Do$IcJ#gi2)Vy&i^M8)o5K_h2YwX)iSQ;Em9}T%<38V5uZSi=s@Z_5lC*ha1Arcn&#m3;o!KF!bfTW3p>!360e(ZM@5lKs>xwv^_$2`vju+oc=b)jbqMVltd~L?Sb^2X({r({=W5(PjOc9O2h0?C1@{z<wXcbW%!pH{oq+rJx!5$@+^;Xl{c@*WEd|gmM?%4+@I?y>977Jd#cdKny`9}C)mCU;lCtvyp25e<PYf)#jo5)TU_$gQLpZW8lju}JW;=vzmoWUxE4}D7ww7svxwjfF_k*d_Dh0pl%ySxj)7zk6w9uJ*nJ4E#`lhFA?NHN%u?Fbk>>K!|Hl1i(RRQVD#Dx`vW8zQ81)yOh`>U^3gtA9!c+?mA-G;|)*;?gv+M-XYcHrmXBK>XsLTi*yW-IaTPe`fH!}|C$t3TCvM212dTGwZQzo}35OBrTFB-;kAQbPSPM>D495SmdsUZt<a_a((*0z`sTJZoB39R6_pbq^PP)jnkl$<Qs<_AVb|D$a5dzO=b|Mhx|e*3v>^jJ+oleX3RYO_x$4LZ9w<8aeCNdU>z1#%)p1Jn%J2D(JdhXC^aF(Ot<PfaPmcY$U6_W9W*%Bv0wNg#8o0#^ep6}723p%`QE+3a!uUek5!Oy3bo=MWnIb1$*7IOl|^^7b<cvkBV~79#ZL70WU-onS)bw02iHXVsGUGM8aNQPTa+9-T*`!M1gW-^bI?^3S6N{IHYMaaWz5>8|ADZ9;1EyHu$&m84?Uiy_}nqe`+ifOYxn)05%IEMOCw?BOSs^8M}_rP10AcjxGJopd!8-?xB?PC7g;7Xj)f7g{-l0WcBr++;i+12%R9AjdI4l|&oI_<#&~YMA8_-yALwE@|`M?%M52odt)*1bI1z<oNtiY&W4~QuJ8S<l-j|RiTy?uy`5fRn+HcLlcC<$QPy|;aL?1=z03MdsS0uxlaze4Y_nK)~L)=mjj8TOwR7==C{Ul!fypfa)D%(k+d4&sr0I2fDy*#1;mXKct}ji!6-(Os2pqk_D8qKKPD{vxaLj}9_DNqPmQ=_aft(nLI3Is*4wHM3~O(_t3(kcAthO<7c!t|twzs?8nwNPhEESIO@f0A#B)Ux0J{O9sGWaJdAgj*bO&vMAfL_;+ti2Gnn1IwsgxC<?$hNBVQCdGRSz(&PV1p&3+e{5oQ-T`ScT&Z(&Y2AtY)0a3II1S5+1GZ9s?wX!%JwF7w?C{fT>yii|`JwSPkN#q%KvF6wfbtDQ6LO;UJ@n3DeyVi?5qxu)!P#P3fm`cvp?g@34a3>iVGY;ij+x?1*@G$n)){gkCqdH(yx43~3P3xhF}jfN*`o#Fu)^A8_)ncUKLpX|&Nhk2PmmEgjtvh4U}iYL8p<GHg)JQ+`Yn+<eQvw+1Oq;kHrwDy0{wiG>=j*k|#fSIk5Fv_0C3r=dSX2SHU8O@3f$=M0*<1evSE0ziJPRK83A@AWF~AUN+Xwc9_8)3Z5?jkeja^>y8bjElF#eB2teukvzu*4tD~&89j}T$jjRYQrC_bKzcm7c9CEMz)xMHf0g9$byU0c@@OA%`b~t(nRi~&S<rfAvzY$kLIG9<FF2s8&=<`54wadj(`2{yj=~XM>JK@U9z->@C18*m+i4H$cUekH1E)n--N%W*5@hq8#FGZQTH|v=M_C_Hl8%fbh%fc%Y7srZ|T~m(AwtpA##wVy8&=2)k1SD%j1T9x}G*fh=StYwYqbr`z2Vzo2-yL2j`z$K@|W^DJZop8;jS>rKMf<gMXX|Xfx}dX$i&{js}`*bcjFQ$70-s%ShP&%cP#|3NhYUQwI}Uj>#<3%I&F3XT0(n3pk@l^c^OrRHQ#}vDZ^F%gQc1Q<dH?iC3Ju>$2mEi^-yUoImu<fa%hV+)Ry_1k-QL;IN=W6f+@DsIo>8=o=`AN>K-dvx=np;qYja(hu4t`X`74gO%4%=}v!$9oM^be~cVf%lEwrq-Avu4V761)sc>@n&G(7O*gk5Umk5jm>M^Ex-%}?%gW<62p<39_|A`=;epyZs~pA|BYMn6l7b%Str%&ef4qYB(8Fsg$SlYpVtF77${hdJpqCM3eS-homR?^zoEk(NAJjc2(}ZBiWA&QiiKUoZgLRe*SY60~=*(YL)OFOa!Cc#NAeJ+i=}tJ|TB~{Kqe!P+_PQhQhkBdON#=c_q#ka9vr_+ykLh_rQu3&+LPyh=y#rQ05~i59?*3=rgN<wh<e*=<X9P-iS!=PwTH#;|Gk!7=YQp6PG1;7{;>@kYSq1_oCMQEf8!FYS_+aW;7`<pVrO}m@`^*jdWx$ek$<CKi&ToI(K5}FX^qtNm4I>hdFSzy0B`JNE`hJHH=Rctw%%H#c>XYPp^spNq%~|{765^-ua4Or&XD_~P=;n>cgg7ttno3K;h0hzXs*^mg3$iPnNb^VtWBsxCoN<5})BQywm&n<ZJFAOnF^AnNUCc9H5E7*j)4tnEHB8w@pO%b6q@L=|q|g$e(Sp31pUmrl9)&@1Sac%R^|zxm;yY+Qp)V3{&0EWEH{4SsU{5-2IgsE)9Fm%@46|-E7&ONowfK>wA^`h{Vg8KY>zp5D{-9{k&20C7FMBmZt<o~Em`BVzvIOQ@<!RJ!bNd`<w)Y4*o8M-8(}pxdRr(>F7_HPaWI54~pGccEl8J~*HrVu5b*3`NZl>|Na$vlt@N$d{;F!6tuH#zfL6f<zk;`%l^Kr~L=TaBygnXM^vhAglzAKSgFz}+oiW}-kcv4{<t4wAAd1SkZsUfmCBr5iIa1^lLYSeX0ibtF;f9ul8RFry+*oMR})WDU+k&X(`${Iw`X!#+Pqh1whcns988_*V{$qtX7eEs%eLmqH!+Ox8%6+FJaCJALNw59QI|3Nz65w5|3Qwm>$@oCN7#2r-pjFUDDMn95Z&J_6a#i9A~TL)RWr+pReM&7JMT<~LvIl71~U=rV%&bp*ZgUg*f<)-<(4%IyMUuHnGGr`vAo|SO|EjK=D+btA+Q6Eqb<+u#Tx_KT<*KXC5d2f%cXPbex?GVI7&ZP0%-*;BhhHvwTeWXgK1eVQvm{VD~9M$tKdT|sBsNf1zI({=5W<<{Mu!m8c*~H1Dgh~)CA^_Zob+9B-Q;jm2STxE^7Sd8^816K^ITFhYt0b0s6=yf#Jj5~s-yjF&)pFXNT)Zj>yXKt5Tn8dv7xJB_iv9~lhAoJT7AW@#4qm(oJS%goD62^S*lbE0Byl1C?2y+^tSDZapW6<ME-WO;68nn>{WPO06yA!GC;P>C%jYyqqYJ!f0va#M0#ez-{B&{`T`M<vj8bTl@5<Lm(>KYxmSj>9w%v$4;e-jdwoc&#vTYquS|#)Nj+2@Nc4{8NdIluyREgsGFzwh)PTSdmMpS#Vg;d?#gtD{v@;!tOu^z>~KV?2%ZqI<r8AfW*>`sI)k%BCS+X;K>!87MCzfvadC~6VP(ocf3ZyRIneMJKfm*@hZ`KP5OpulwDw0)_g6Wj`<CzjTB__h<w%8ONM*#U<hGPB&B>o^sDd@CQSw-9qE1%o|~ZgQ!48HzwNcBq2V$8kjmsM8v!wPN}Xl%jkCpV;@9|FTJHQtNujjplZ+b4bKOc+qV=Wu7d#O?m%M52(h1qd`FdTCxxv|AJ6v;(&RukAk4{=<0i|hFAJ?h5<%sv&H4~8hpQ?5q!IY&!hqG%}a7|V&Dwryu~LF{WOf=V?Q4L;U9??VkGGaKCTdU?$=!6Vrkal%|=DV>1N*2kWV^ed*{=p=}m38RDduf-V<DHzr@A`3fM16MaL}^-KB`CDf(7{{spvlP@qd?7(SnH)V`UlCqlXeVQ&`hHP1_OW(>5Ezx=6%f^3DF*M|(cYr%=x_ufHBlBt~6iOZMFS!XRH`(qr^@I+AX-hW1VDk4wiC!o4z=ludz7Kx<CCytnb%k<0%$TMdDz9qqE0;uVwwiTu2B5jn?|G6FeyL(DLY0-I&9;6m>inQIE#QlPw+C&WDBvzm|bR*@OXMg@0GiJ$tQ^V7ozL9hOU<XPLdQQ^#qP}b`f~X-;kwDDhG&Jj0U)hQB8}y}_=hmhbjkh)_AJ9FX(EAxoOX;A#E#i@~;&J8((E&*;+?=8|au7Y-%ycvMouI2z7ZM$jw?+2KGo1nWw|cIE{8HQaI#s1x<fe5CQ6E5U!Pun&+@yjeB#!7{B?q|&Yo}90n4-eHHentJJ^H*U?l0xc;Ww!nkDD-0T;<rO>!d06VT24r?UA!G+v3E|wrUS@&db&neYt4cYB9L60{<SpWvwP`(mi1zt*b?V0c*8>?zvg2{XcH1YmkvX@sQJ8hBDezvG8cG+Aj4z(2>d9KrQ`u*H27Ur|PacQ551%HW>%rReETiC5-!3M-1ovNjBknDn1xX7|WvwCk!V`Uc4c<SzDt3w3d`&QsH3HcHE;hi4h@nnDLz3F=O@c6^5tOC3J||y0c&atIBQtb!YMD^IlykeS}~l>dpz{B}Qznsg(iv&?Ssq;aN6vW2;?|PpjZsJv<}Dfq!nDWI+?-u(Gp8jVdVUMT*52jI8d+Y!&9iI>Bbqo}qx1T5d6sTRX9Yn2D(-*bfv?skh!dmmmJ4yTb5gi#Ec4s3rdA2boYh#{*l))XG%TLEh)<@FTWLk}C(=a3@7aKj-fd`=i5%b&=E}z2842!=S7vwmNX|$ZiqSIxhAei9uD3lL`xs{SuH8ReeYy?YXlH@!!{6fMF{^d35_k-!2xD^Gi+->wPYf4q1tt3VP%;T9VTGyfX3s6^W?E-APE5vTX3Mx$h-9)uYD-jwpkJ+EhAjEoF~9SQOq}SCvYWU<h{RyHvs1u@P^K0!P7Z@Ude^UYh334!1i}HgsSHmJwWe=-JsUcQWJ<--mV<41i6Q{mo8*PGZCg&>Y07Q~=ph;Ek}-f@lhZZ-fB|U6rF{j!oYc;q$vVpjc!>Q9+$x2bE<X1-@3MWmZ~k=z=uQ9yvm+J=)kBXVHQKK&}hKNE#@2cXOevUyUm|&7O*{3P^9fPxH>dLbb=Xx`<J}d~J(e&Ik3YD0$vMKVRD<>9w0gY`v|AE0a3hAbZfgdmgO0tW#ki5Pa#VTL2@FGK5t>JNAq5F2Cx3$|Vj+h^hM`Pl?sPF!Xt%Tg;_yJy<o6@qCEikXJsYfM|_N3uC;Es9}qmfZS7sZe8~}YivGpDEg|o@U+a#D<`_bRp~miHB_CnUtos8+rnbe1n198sIY|M!2-ltl{j1d>Q2i}QHuk4@w=T2f|C0<%_NpPw@9gSyY*IXc`>nr{5>E{dXuqxD;)H=MX6Z%R@o_UJR*_-J9*u_Y2VLUrtg-^GG@60e_%ZYuND)w0#WHV1`~YWy^Hq{?%!bEr7lE9YuT7zuXbLS16s?(?TZsha#YuYjb|}L0y$93CLcl+_#p!ALWic|pR@@dh*xdsa9ePHLT>L)9f_4b(mr3BTn>yB6+!}rZ@-PkNo9<XAv6lj6F)is(SzYCyUDnBO%`#lySxcz-7;H68my#yg%GwK2pts|429hv`o<dD%Gw&G7yO=Xn1Eg>QuZ~xIiV6(ZRJ`DRtJ$rU;BYJ$EWia-;uZ#(7?vu)rG)a@$r0A!+fKXrNHv09G1c3iHZD8hS&5q5bl%9l)s<ulph&74676K;!6dKPLxVL_5_+8aBIiT0sStKD^?LTIzo-U1910Wi}i@7f$1X@&XLOfkVZcOo3aJ%t91EGa=v@WNz)>PzFMQR#*m)`-69e#Zsqe3K<wZIX??g0zKdY}7-$Ad#KB3Cwjobieu2=tegrAg1D*Gf#y=67G8kO3!uhI7VpUn+^?Vk9muuCqKbeRxH1l(Sjl!K1g)<-8N2J!A)?eL;14wfy$R4L3$ija+(K%Z(gn-%dx3{N=c;D`gw2Ax17sWDa&-e{hmtYO4isOsLgz3(_a4i6xYpxU)^@Da0zwpfD8KU&u`bLgqMQ>lNG5f`KuCn7wo1_zwK321sF+!?82rzw-VQe;VLhW8DiR(ycE%{FpjUK2V5Qb)SEb0_D^xdeW_yY$Puz%DRf^KRFkD~;O445s6YRZrHq(y=8lxqAe5=_+9iPztvYI6GME_>q`03kK@YEl>A7oTk((N5IQ@V(`*_%9Pq!$y_h4L%@9xTNM<^OAi<mfc=1N#ap4<2GX_Xxbg`>3!54kuqx9pvCPWIHv$~=CYI3dJQ6vuDfX*T3RoHKvZgl3Wxoavv^28(l9=X*bXMP|3P@d*ma@x%gxLMvuujRf~&bhA=)M?>TE3cK!(M4v@w?j>t^ZDkFuboWbb$iOW#%c4LW`;R2Hpt9(J$}^S!W!cy!)z$zEtg9KhPDN}1`o=0RKFbYN&}P;FWhIf0g6^^@mcADWfX0QFJbi5|mRT^~wdt;31ZTyfkq_1X^=REN#Ps*-t%_0EIlx_^ReG%jiHA5U+b`e<H_&2|GhPLvA|Hq{c*I3#~`f&Q|giEEmsTWX37XFp-uirHbObyNxMBmMaxBHH*{RA>WKA(VbJ*VvLnN|!Rr@6Cujlj?fnOrn&_;%j7HE+Mw8gx4YlrUa-V_`|x{7@O_0Tn*%&e`UOfqE>Q#Uo2~uHpTQ{MuP$4GmCT(FZgISkf#mjk;DFRhb9W8SNS<-lz|#LC<M_sPKSx8##L`u$-(vjr=9gE)v$$x(3jd5bi1fDJ&s*?{r-<bJ*czc1orsG;k<e#;rO6~gkLecr3+%djMKb6w%Hsi{_)Cppry@rr--=Q@Y}VvN{&mdUv0Mv3JP77(nta*uwY=2Zj?r9#~kaZ`O!fiCEUMRK6ZMbBe-aw)IRvJzS`E1)7Gx0C_#BCgsI*X%ccpv4_hkBu0P{-nSxm=R&mUhdYCj$9{{zK<vtnw`7c&V55i0OUcAUo<-kEAN|u-s_yH{`VXM4HRdt-P_^1A4Phu4soepA;uh5KTg0~pwXLd1xkv#gPr`wU+DMGCL1muzm4?0iXOSn!AoDr#apEH9slK(bLYRZG#oqhlz83CkodzvqHCZm0dC=FR)`a<`coh+wJh0jH-W^~r4uB{+@`uG5MbR4@F<Iz{}?#zJ`DO{2QKV^l<>l$upVF7KEXDEFKAtBre9)qrf)MmF%gFHx>H_gQv$HnZlet?>_-wWZ}@23ENQa-8IW*Qi9vj6jNp!{W-Ol&i0l7M#|!BTk244<m6nSaSzrFIGLXK()I>nBfC0IrMds9*GH@FWhFvJQJ8^&tpJc5<j8KHm~h-p;vC*NZj!T9Ac!w3te*hQJ4T;uu6Xivm11AR`c!0R~N|c!pW6(KIZ%{ujdBB}?NP(!d=#Gf09+HF8Uo2`ZaP_Qg@OfRnkY53hA1VD%A_g^#`qbvp?A$hn~yJ^Inslbep6k^O7B>jGQ!(pt+O9-=`cNcfd+qM&G8ybWsV)87)sGbk<IX2m)rQ>D#LJ7sUp+FRw5d>~)JmhE&J8hP!MTr#5}*mT6)+y&O2mpp8;`EUjifQ&Z=nM4<@i>9Xh9voB}9BjC-LXsfkI0So1zQWFH5%K7jQZ1rkPe74{Ew-#Fy2|WXWxi7YY!fz9`xYl8dsZ8V)P$F{)86?-i)_y}{Ez;lmN?n45_g@bsDSv^yG@k7Q<lU_LGdz|_Kx1m$0FqUY3X}ghtZ+<yM;uhaW`tA(YG34kzT#thLJ^!TUJ5SG6Mv17~vsMJHWzn$Jy`E^@dCcx|u6-5)3N!RkT+!0h9JblI{_Z(po#~#@8VE#GmSa<8h@g?L)ltL?8cDnPcfB+pgAnPxfukW_*m!oyB-6Hd2rjM!t61GYGg^JU=~wVq~%3NdP^`w@E}I3}$C&teK8eKY&RKn<0pnBFZh-RPdgAn25;yTRH!Pfcg{Vlk^B)5NFxo3b~YwhxWU)o8|+q2L8_Kim-~QJN$$QTWEJDU|EwqSyrXGs#}2{O$kBp&O-$>VtYGsfwycrs9MmoEmzkX#q-~z%iwY*=hrL(sTzQ<5CKm29SSW|P5>j)T^|<x^&@_*L1rA((h%V}D{JZzqt3f7<Fdmc<PsZj^Ae|S5%c0aL^vMaK-j}7w55`Cc!=O#a4l}T{{Pka#+Ce9d1Y43#}>#;tuDhAN{V8=>~{%wJA4D_>>x{CMl&peIMZ9Kkd5K{oxtV%Q9G!(ibH*8s61p4p%tuo{`x^e*^8jEzV>VS#GcEbNJPaIs{#&No;<B>F!<`~n9uR_pB@sO%spzZEWw)>Ad6yXvU*u?w!n&oM8g{hT0*BzJWR}R!MqEJf}dD#xswem(+I)U&36Ju_S6YtuZG_ScNZ?^l~CGIn@fBUJx`q0sYtQWmE_*D$$%xSu}G>3%g7suEJ>o_WC*h|vgoe53D?;Y$8!+zpdAg}&|oY7c|Wb!aj;G>Hg6XsZ#_(S>*DJQY=41}6v<d2YB5K+Og*A%uAXs48kQ^=vYnj5R9=zN`mUn8HaqwwDXRze$`qplOTb5Hy2PSn<U%2srnq{iNMSxLuUxmLD#&&fMzK#4%kzU2!of@<jCZ+E^P13OsIt+<lJ2ByuYne6&JN_*s}4I2kmCVxn@A^8ixG?1XraNs5G^a_L1WglPLI>k(AUbot3tvVQPqtSxIt_c;Btv4P2j^$er-ix-MC5ITC`=4@hR_#=DcK!FY5ER!6}uXg}|7^#a_xvV0DX<Xqv_UEAT9w^&Teyh^olV+USJ-JZD@&a+nS%CyU<tzUf{PQJlOYZiqWn!bn2|x7Y3`_w-;Lz`JY=cEOaf)Gxp;M;vlIgR}D=|MhgA7g+vsn2-`G;RyNJmB^~>OC4j0Jv%7iLUfcsP<os@MvH_Hd|5t!-s;K*ok4o}?INt4yGO;%I)Q$awQf2+;pM+Ll|a@_Jut`ZTt{;%q4qNzdi6V#J#Gty71q#ykz_Q#x)0?DLUtXD=zj*BDb>&wCq>Vpn8(ubiQc5{|AUzpit-r6LAP3=a-J>5=<N$<aTu$%2t$5ePaDl@ceKvTS#KFYCza=(GkjEef?`(zSPczUJ_WRfhvu<_nJJ(DP$=?CQkze=yWxz5i>t<WeD|wMDxQ9~3)d-q@Zn(&*`p98Yd^A{-~+chEaI5@kFcp8rg?j>k+>i7YONewtvivkmjD0&|MO6~ZK>{y00G)mzxW3L{AlD1vBYQl0ssI200dcD""")

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
