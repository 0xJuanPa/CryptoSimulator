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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;vW7i&0PRM0S;|f@Xd>FE6RpTFOD`a4BnrU1BpLW7S3^L$i|{j%98m*9{jxrc&nnu<MAf8$y6)i$&5e)tpac%--fa%UC7ETjBMeP<di=3`@Xe8<8X5b15#)0%=3=jXP7dwpUgh!tT5FPN(7HP5l>N}1Uk@b9P0%-OGr`N-YP35q3Vccl`Cp_NLjvOyj%~Aa*KpnOxWDhX6IgqGlhp3CchSDtkcw;))X~Q*_Q{J_4CFqy#&AvB(vrMUxto{XPSdE+irxI^8CTk1EjWya!R3MDq%5-80@jH4q83T(y*NTYvbtGKxLPS2?vDV7G4$SLpd<|#mNl=y-jBznc)L5wPksDrU>q+vH)MH!`Ge$=nWUt(Q@LM%rL+OgsV>qCCAu@q<BY_WJp7XKZvm`dp-=_#P}5FN)8Br`8W>K{<~ToWuq?^OQsy{zpwtb+XP+>FgrfW)x}tI#St<f9Y@<l47O2|N<Bjf(psep+O^21L#i}VVLOOEs&GRlkvL8CbH)G$4};jpyL0QL0CZ)*o39&f5r0ACN)j0jLSLy;#IHEOuYB3rhgsBr9f;{hDS%<er_OgCSFoug<4z)44onKx#3Hy_oV#_vS;`vhy^boS>S-{ul~vq7AR}4MXj=6>sD8Uh44%T@QZ<nMFv8&7l+VlVRUC9q_eA!m-#O+7GSA;>K&2l9EOFBwHIpmEl{=C_Le*Y)?w0+c#1EB!W{Cw5On-V9qsiOqBbpFGM7JJk^#%-%v)dc4;E1l3Y}K?3I+u6p_G55mVaIfIUz<|<9_Fw!r0;XmjrLEs*=D7cQXjKx^W_v|)COUU60NrXXYkmCLLZwo4|~XRQ=ECP0A}0=4e!^&7Y~1T^~Fi1ft4816o|f+xCQJ@hy73WLT&K%LwMCp%&V13PLYos+Zg7)pAI_mBHT$l(4Lj!jFigCk$5=gK>6zdENA?&Ce1l=wwpVvHr_oE)1Js8jK{Ai0T!ln{D)SqR|NCPE6Z<4XOL9SZ&?j>5DFjG48Q%twBTi<ZdyvR4{BeE-BRI@d!~^UsziEtp@u0UBtySI!rq!a8fE0|<V7xloQ=p(!rc*m16(qBYekwhHdw;Hs?<2)HW*>(*k7_mpstKqyy~NIiBE?LjvW$kFucIT>k1}<EF0agru;O5b{4rOdZHHe42XuV<#WQD@}pjoU{+gPUDx7w(3c(9xrYc$FyEr?J4ohr{#M4>9*n=Du8s5UCh@xIBTq~#>1~>vv)j>Up8s@Z=4p0dh%zqH#BsAol)x?}Oj5PHm#x+W%!E}-sR<ll9DCNVdUJ90A+m#+y6zZR+tJ1SVAhbBqi<JduHB&n!IJ{aUIKbdRoIW}3HgcvlZWc)Y~X<AaW_sf!WXpxiuKC28s3tYzd=nAWztL1U1pjvP>zvG*pygMiT%rRrch+t<yOY$kcGRRh2V*ivT-AC|Erm62C)XJ(eOKg_OMiZQltU$dvzgzYyU`W(1a*te4H7>!DN|?ZdyxS@B6i3H6Uj<hu7;fR<t1U0Y$FXnBqqNRrRt)E`cfZ3EA}-jLLA`k0KY+s0Drm%dR;@e+u{z$vbv`+3mKkS?GHSXn+tsD_r#_0B%nC^;Dbi6<&f}mZFEqUh}zvQSGrLcF?UK#~?OKZ;K`|A=`gQv`ree+_~eht^VEs1R7KWQ1NbDK>#&)QGJ|n1N&++|6a3VYPwBC6wRxDgII@QzOw8t7PMxn8I@FjgTM>u&=Oq!iI&a{+r0e9Sq!3juZtV)#3u5ozv27~MFe1lXxqhVMh{1w@&pxKX{<QGmNNiSDc79tao`vX3=%$&I2Xf#gScZTE`R=0KI^_7Mucgw7odvWCZ_>at}<y^nl!SKl&VqZ^SmENn?9CPPeoUA6g$7k{@&MXEx6A9?6$*(wA++x(FzV+D45$`U<+HJrW%WbIF8S!dKIF*lJuzYg^!`%RN`-=7=JtT5y?v=J7?tQd!V?Vp(;!N--taBSnoXFDkvAt;tbGmKl>?b8<n7iTESM16ent}&^#1yi%+B(-y}?A(5qyhcpi6aZXrUj$vqIE$Q0)ph3l@<CZ%1KdNu|F`>RT6-rWL<Fj68MqI!=vIfQ4?(rhu3;9(IXDdunh@f+2VHhKnG9HCI}{!vCXfgmd9q*<n+<OH6yC-9kKQJi_CkkHZiro0i~^dNdctRf`b4#OE>6wN<->&ZdwcEMQ*YZ!R7C-MpvmO9uyN@|*9!j|~w&YHuRsv@QHImf}&vRiR4)@@c5ONqFo(|I(<7>fQ_{P!FM!b%&_r)*BrE{j?|XeIA3xR1I7p`EK?lRNj^T5aA9+B~6SNdzVj=J)b1u7bV)A}1oz@Pq+`3nRhJ5I6GEytd)}6HDN+-p;vFgVI6jck8Z*f6DAzfWCF60=H%>>$a`77Y7avLSRS8z+KlZ(;}q$3(Trn-3LJ?@vx)WjiuK`i8n)$%4{0%5KJAx^sEa)|0QjojUCXYDguMp%SgrYdsEA0pGo6*_?J=-xF>^IY9@o4<OJ~l!0s?+-(J4K+jAj`Jj@lXkxr_<K`tp)01rYWWj{0h%px7aq*VLO7l6GpB|hUyMDNdCB>wj~5O$zwn#hD)+#^SIHMnW1(^3^)5ITIqg-t)wjEtRb7^`=Eb5}8TI1UeuPh?}vzj@G9o7r<-UmM1pWzjpTPOWmblANDE?W$9hPRt4Lo?@QrafLN(Qimgr30{dFCUM$R4^pT>*wPcs!`$wux4a*yymtM0>MOp*l}4GXu^17YMBX>3^>)$)`rU$g=Z07!)bVt$O5UM~^WSkss@bJgq}~=-P8<4097*8G@VdvF>(*=TQby#4<tJ)&4awwMGYF~DdQxhf2;zfUlH~NCD7q2=I<U1J-alV>2z9t~QqNGab%xGOg(InAm0^Gvr!lA40ugKAD#9Z*jA#H9Q&k#rNv~z+5*}jvyO$-Cu|l!Lhz_BMm)D!KLQ*Q=tqz$jG7sIv_w1=g>&;(|&dssP-jf$r=8DO*J~5oBg->AousXLE=Lm<IXL_nH#GlcA%(*|Qyt?$f|FkwDms6sA@a%LR`+R_1ZjzQn!#*!yFsV3NG1Qu6n{f83R-xD-=OXPM<WV;nSM1_?u;>M$yf+$K;3yRVTgTHxdK?PtI<N?CL+_o8Jt&gvPi0Z9tk69>0k?1l%DYEt>hw@2ONbBHEBYg2D(7r`7eAE>eAFKh`@u+Jfz4ElpOYACQLlX{tU8N9eZY$C(ieuZ_vGIEpC{s8`){Pwf!FsPuiOvlbr&8~`8eLxK5Uyb1R=i8yM>lSyxC)UJ_u$-&~Pz$<#UAY<TE~dK=Me;IhxjOEV_vombg}~f&<|~JM5HF%~iX9K%K@2qDpyPWDE;z37})yXf7KAu5wtm0MPTmwe@oEPvG4g7-6sI;#Wn5DQM*=I|?Xy^czJQKt~6ln<F1LhNKDXuRpbFBY9nMSw&wTsY&w9yz-N`2IHTV&&_{t$CQkH^63MS>lZ^c*x*v-DP%&R?8)D7T<BJJs@QCIb_wgxfj#2o!LyNe?oUXGohB4$nSPK!ucdjF7Z6JcDYUoBJ!fS*y37d%OoZ_QhLvd=FJsqdb4jO(r)hTjIu)w9A@@)WAi?p4Bwe}wiD_i4stojm2eZ@A3uwkqQim7=n)j}F2GRr^)mMr-3W~0WLV$72^TrS>A|Cja8<d-1Qb`kP)~hDjkpmj$%?-&Jy-<^7`evkn{0$DxrFqwVHJ^@4*s>M!a;NG3mcuxJaydlPVXS6{m<LL<x9Z5^RGHY`&a~};+DDUt2~Ci>d?bb~mpbu()wMEMcBP8bIsRGWEW)I8^vc$ICt&Qq5Iy+db8U9GKh8-EED6G);0q0E(`|*rzO#o8-1Z=wN5p3v_|8*sqSh(ZY8vg^B8V(CrGM16=}o32v*^0%<UHYCzZ1t>_)Kb(IP7zzQ9Y5~8<MrL*V|P$*kGeW7iOX0OxAg{SL7ityEZg;1e%H4tGaWle=h$p?PtF`kXcLA3t0|Wmx1?wRuKgG7)}W0fNb&wpwC#$Trd9+WJPZp6__W+u|WykT=dh;-oDixGSG8ZNS#Bv!Jq9k429;P>WG{yuIY0QaOW}e57AYrTAV13WzjWG@s$)L3!K^|$TPgI#fsMcKH#b0?k%1QVg+Ho29T`&w*L4z)HwqG(f@vF{iL4SFbc@mhDH?DTE+%jT88^H6oJ^MJ<dRbbci|LPL2YnZD3MQj7`^}FO@Hm{RFc2e8F_JdeoRDj~iKkQRy%v<cJP7eL&nfOij!Jc8Q+Lb5ztIE2s<G5ZhtFGt;$@%8u|2yo}#h(&2(nTK`ReChW6F_0yK`6i73r)!WGhxQ`2#y@CU{oG}KWdHXMC^XPwy=X!t&@Le=?-GL)ztA9R1qOh2;5q3zpL;gck5ZtJ@SnMR}Hz*mcl#T>*Uf@)$h->k|T;{84*ab(jM_Y)TCl{0})ZGWE=8I&_<v4}g{sk*}R5TCz_x{E`9|lG8n-V@G3yQ$#a0vTk+#T%qe>gXdr0GVWQ2z^NwG)qn5MeX<4_BODHV;TWWo{Gt5gTV=^(6llFH`wB?A5ZN{Rg1ki>&J*!iK{=O@2^)=-zz_s@9yxGZF@p#GIq-0Ll_<CTG5jL#0u<z>gm`WBv6$7nh;;?rmO{XJH)Vz$`Zs?wKk=E~E|oKQ<*Gf|^>g(6e;=VN5SzJ(5}p)kRLDNKp$F{)kP+*E*cM>m(WopoUMIR8o--qF)VwY&Uvc$c~{ry92ejh??S4cDB59gq3;{MI_ZpfRDhVPxTE>EOxQ+S5`uv0mD=gFj-f#lf)e2l>Y$>+x_b>Uu9lwgO<=?wSb3DWHB&4)8*R2wK?6Q?O=QZZ{jE1Yp(16_Y}Y2?p%{bQuMaKlK;78>kADR;aT&!X>n1<eKP=51tU^H;sve9k8*qVAVlcj9c=j$ADauq$!STEh|d2qZ~UPBZ%!>^zWrb$G2;Pegl$xOLP7P|GW@bn`5ID704<2>-__;l&CdHM`hJ)ga(o>ZTeN7r8}C_fm(eJCeb}wA?lb_-(7g!CBEg(PYe`F3x(n#$kZJ$}lyDf4{@}ROu{elOnSCYW4+B}B3-)sxv<QMm*h9fRQA*Vud;@Ux{89UI9e3%BdQ6Ux_(j>lirZpDA`Kze1ITo9Ws{c<o3rr3HCe>tad)McYb{;Othr0;?G^H02Ad&IUq9U^<id_|c)_7W&DjrV#9yuiYgn`!T>G#bI+|&s3{6f+F8zyuBOu=oOY$;6>m6Z?BNC)MNLdf-Vz^{+)EH_3)_ru0a*k?%?lLuT?N2orMoGd}Fn96M@`oGq^2>RJN`eqqJ9RGN`TfxptnHFxE=`EkJ58c!c9Io1%GRSbmDdZo=j@k#ppjO$V2q(;pR_lYrA=YBbOeSV5dqQ`&Vna6Sjd!Jz9gT~=70s(^)|B>AF(@Dz&lYvIr^6Z9n5I}IK_k2uH7-MTqWNDpW=r$2{J)6rzDLVM_^_Mq=FP$-gvUx3Cr$~$>bB|5R2^FJ1W*>TSN2e{{XJ20Cj=B%*#N(wbC_72*}U>Fu-8k`_>u=Z)k>@C++UKgB{4UPE7-dM?1vB1X)fi(uo>hFPgWCi~kQL1D|_hqsiOyv5y|>4p)@gRn7A8BF36BP`|0+<=Me@oEg?l$1kNej)QT=y7tvSfa}Yi<&a3aJC(^$RFVz(Hz?h>qDFG94OvUBC2dqFE*Aag+pL58@X9SWi^vp7%wr>89T({evj1?B67l6%IPK=3R@R(NW`PbgA}h=WtdWb6vj_X1*>y%ICtHL+<~u?;Ugi|NE6H;Q^<L)#BQdG6g{TVFViDDGiX;HHhDZ~pHyxX3J87?01^Uz-XzJu;BD4;&w+%YEZ&k0w`A7VR9T3L7n5C?nJt7BEgCE(PXW6PR^3Va_t^{39pcjcOBc*NCgsmKLhbPG;GCQtxG7!$u$gm9(JArCIE9JHEIiS2R#l&12u;8E9OzA-`)|)LXR+@~$L08K>e#qpSl`_y|)$h1+;=|8l@n4gScu`J&Iq!}?Jb)Qz8Vqcxhf4jy5b3O;&r%`m;+uhUXH@hKbd{Uv_;jzsOa%0Gl5p4vXB?dzh?489mHAM_(S)P+?%E^ycdUwA*At#XPt$^Y7gOdMeOohlOHT5I<k<VbB1ky|^Nq)IUe?}(4rwOMR@Ff)V-vC>liUzD^RIZAwRl3t2Tta9xXenCgR!x(ITrcvQnvZxAe~RL%$M7&?VxHW8a|+$=yZ{2j)GwuPG(E!W^cHRj34hk=@p3qB6#cuPmQQ_Z&T=N#wB8RYOZvwsSN*JJY{FTPxUCR0N^~kHj~4>a1HL28|xWi!NOu05Q82SR@v|_%QNZEoRZa(x#)?WeeK(g+^go@N|z&#Yty>xV;`Tpw|-f-u6GXU6h~3%0k)C`@1G;jQO*KtYOq)@0M_CS5pjq|=A=>t2t}YEovNHFsAUn~+Ws#rj-T{~BNuyAbfe7Ff!Hc`yYgc7R(VDoYuglmrl1u^x9!(It~k0E5d55W;XHEaew+V?&TC!>F5i^|S@dZ$Xs}Vd3SjV3d{_E7ClwG~13JQe2&)14|7jiEis*;PVrDGJoTKju54*fr050FTke?AVjGfk6GYyDHUIWk}(djf=XPP7@>lB`^ubD|y3{{+6+w{B@_)p*QoCyVt<(#PY&aqzbnVOGgdYhK!^mCu%+3|t45;{sR@MwYlq~K~WyK<Q*pm<<21W+q+ij3n2O_veB5QRsE)KVc>4yjRq6}&IVQc~m3{_ha_e_+$5__!TNQjsEeo*)AW4CbXXVCXj2*e|K|z9S%og5^PdF`T~$AM;v}kC)6IBI^x!iB~((ot&m&^L<QVZ7+LGHL6m3-E7lfJ9reMc?R5hk>fK|RN5d>G^P*#C58DHI_%Kj(<<*86FG#p4-{*#$2IH}mzo$_hxPq&C|TPQui=bvjEpt_kAY%0<f!{7Qee(Ze&xmWSsD#0m--Syxn%^K+){La*0bGWb%Vh)%KfPaI9mW^75h|G>JrDi&i)3W4b*$qEs#Z2H(EJp4!l#~)S)9@-}9-L;Y%1q+nK%2Xo5H$bR~-oGs8h+fffI7_h<ysFi>j27fd`o`)XcDGJh1y`)WNmYWrXeGBk;|R{Al11w-gME1`78bF4=^ByblRp_hKn1A~*N7<+SpJEJKjSl+lN`adz;l5`+RjguF=!eK$f4oZQC-iZ4!aaffI23zR<re~gT@aBYGsXH@6#0R>b9pIOHvC<*MI-%ra3Denbp@zRQPm$;c_u!1{0%A=5N!d?Lw}_X2^;;x2O>fpSe$FBq?J`B!y%sQEX-UUa3(B7%nttep-j@|HsUFq4B>2RK0{P(0;UG)-ekq{jxNHrk@Q~pU;6#8hb0D$d1AXJ&G^g(}J}vCPWDJe9vfNEQ=0Ww`RFC>Th+Mkp^FwllyanzkOFuDJGL^x=c|=RG;n9*r2dDgA(Q@39-K!A}1`ALRA|GLJNoI`3FwM~;H0FOvoz8MsO~U^%eY*q99q!=@TgtP|&9V6ncmpaFF1TAUsvwjBri1*VZ7YP;yW5drv1}^<bTrTpjw&tGL-V9Ag~f9p(@GtPY=Z%6N_Iq(vdjaTlU-zs?pmURgv7ms@5e2w#R3TR_heQSIXA{fh6$TbBNdT<B3#>vzcgVg2WD_)YxD0wCON>;EOX+q)!#Lmvg%q0R$CH>I0=$@nX~1|Y6OZ%B(Xee2^A{ZbN#|9;(K9qI?dH@b08F41wq>RU)=^(UOgl=$y1lRac^2GartCxJ8}NoF-$9XO5370>EmviBS_(|Lsc$+V=HfVW_4JB*BEn2%@-|i&8O|Jq^LCx^&?>A56JcA@Y_An8#rEsJ!Yz30IZx0O&*!stS0Q?T$1R$s(7=DofI$um)y1CgA6HTW8tY$damAYyrT06k8T^%pfNa?GS!)^;J3(Js&$-CZ0wkc2$vts<VxB3l3jIgNJ;2Nln<v0q8rM!qLJm72e*wXUxLZzo9Shc^cUEA3-Cx!WAK?qZEsk)_lkF_@_fL|zYcZmHlxOB<S_W(#GS-#CDNOu0<5ks@FVB^kM%Eq3sEiq>KMWw<SPT$OVF|-MYz4QGgWSKoshIaJ-%?9MU&gNy3^Q8uJCygUbx4yGZx1<f9^5Lj<+U_TTi{hg+rd3Snm;IIRYDcu3PRjX9zOFYZ%|Gw^{z@p}41Q6dPiGos5Nv1fBy%^Qn?A5yt&MC(E223hPp2*QsRL+iQa_DcU>iXRvdyG51^^^P3j%Ido|Q2lsv!ZRUuZtH#cG^#rj!J*-QF_mQ<kjG0W=K1*{bqk{ZR+YZAg5idTFMF#CRY@<TR*pY3qzx|_~Wa9JA%S?r73=$U^97pN*FAXL^Ie+ZAng#c8YM`R%buU%@#g1q8;JVSEyZInMV68be#a2Os<!#o{@A$?#G&k~ksCY}wMu?2@ADTT%f==MPs8Y3^vHS@APda|7f1vpLF*R#f_z`xjMHsm>(Bw95sP?a=)hz))$sKz`x&$}NJLWRkt}MFI`(Pf>VlK>q8M*i1o7={-W-h{92`7RRcuOixo=z;y4%9{A;#hMd3SeBM%Jd%eHQ<?@`{ECAy!R7a>8W;1M{DMB6{OX-S1Yc?lIkWz1RJr@Ag&Y3o&>aQ4Gew6fm_&gkE5%78$xN9H1qJ-e2mq9%+=!!XT4X_1hFno_BP#910upK0rA;oLCE(e*3cCv$)GbEMg<&U!E0JQW$JP(WMZ}Ou63Ul39j>!9nXyAe(h)%UCqiNDLP~xu4JY`+5^xL&x|$i8PEYy5zEp+GUvkSjL`+f=Db+Wl&e$Rn>hOw+|sU5iENY?c;=`WdoeaY;@N}^N=BjZcL#Pvv|hwQ=n|Cm`bm+#J$Kkwy>@?4g1GXi6grmadf8;#JipN;OLeUF2@h27Y6)PuuUE90LKZ}v(fNi}{gqnJf|AML%2+jRa^jSfpZr=>=oErbKFSW5?n!kfC$0h<(851$)+^pvyceF+ukk=CKB66I2`G#7j);Yu<7YY-Nq}))9DbQ@YEs!5f?@Z%WCW1(oOpyJHy?8v_y=udySP@)6%wnzKt-pKdMIgYTQ>h-i(r%j#^1U}|L<(Kt~>4kAWA+3k%jN+IgWnab=R3l9RI9Q#jgWae{_3Ws}8)%#9>!9N>ryp;Jm2!{zmxX)XGn&JI|dYv7|9nw`IIpHgOHyh3?2z=C*o94Qjo>$*;S&SvHiVrNvM6K^C$@$kLIEi_|DrVT+`O%nIPvQI7Ce?08lswKt!{+N~XLn#N&H(!KgV);@>})8-R%1*XJV7;vs5s7ZI^tbcJ`v>2RbPe35C9lYGIz-|=ojl1@4(*k1*2a33QNK>Lt;$Ra<bi?Ft_|!L3Ps(et$d<&nb!Vd)ie@}hAgoy8IbK9bGb0c|v^RoQFs-on2JkS)Xk5pY_UEX&!wUJ0Le08WMmej`TuBqMP>R=%n^2Lv$8xWIN@6)!Ky8}E11QAeO^*x7GD~QUq~kThJ#6Yvd3LkgQDj7L&6!4{mbX+jXe@)*-NpJUCuX8-$l174$j4}uc$?9UrK-8Bq_@Z_!2Y{?Wg*~<Ljb;a2Cf>)(A!b__wegegU-9og%<cLIG_V6%Og0o0`pyZxE@2va6K@0`Ju{$Pc988kd5Qwo;}O|M97ESE9Pd6aJAphAz;MX=J?S%PXPzF2sd1~GFV9M^w>B1mp0dxhN42@S-Rqqp(U*U5F;phy479}+`)7XtQbIt6z+kqo0-JAU+Xe$7olC&WS!wCiw|u7xpuzdGTL;J14!FqW2ngt7h}qYdd%)CtCC#KH=Vtj*9<E;_p%x!?W?Y#4cCT-U+$ktilEY{xfWL_jymEERv8xC_@L;X%*-XRbSL-&JPRUx?ghn}0XF!#nRV414%{MGJuQx>@m;$D)%EuvIlgJr0NdEPv(e*Mx^hyw*t4bkMyyLo1$-v~4E+8$qNF5vTB~%dj;;B>r6_T7G~)r^#9DGq#c4w_3O0BK$szy8$R8cRtLp~gb_*;O?Y@gm^l}(w6A;*yZ#Ji1ej@C(B1=Uq3sM_I%Ug&UY~OXBrd&oMyS3D@&_H57XElhXVNG*YIB{)#xlS?Tgbw~v+kY81Vmtrp-=g1Umz;Q@p70Y%I)UUDA%}VhataCa2;f;gryW^8{b6e*xVL-F$iIoOpYOYj*^;zGvER?3)XoYZXKV>QYHQyZY=KLqe9pdcL>m|&IFPBM#hfV5u2f`mo%31*GGXVOB<)ij@Z2xNLG)jtp9BWPueq@-(*=VIY2)q~K0Nd+er2cJXAeq?w$zxtM|?V)1730&5-{2uLL?uFb<${5o7$=ps3qk%(jx9o9FK0#pz%54PTUeN@~%^Zg&l#`7fRE^1Yr4-Al*<FqCu?aNq%$L;F$rKK>YTEQL6l`%B^*+Nf3?kVsb1s+0LyXGE4v26|RltBT>>Ec3}qZG00J%Rh0qA1TTOwwst|46knb9-Ow{nf%|0LQFpt+;{0E79diYD$s?qr3=t%A;n9+xxSb0~rlFOzNo8f?pdy$?8KB^f5;zc7jk!jqux3XbxRR}yCv>;CBVA$~T*M{OSt0ez^qIce_eT%4MY;KvrRc9opzbNymG$+!(V$gAl&wsWwwr(hGA4kNt{z%P%Lj!e5@9?_&bOb{X|EN~B3)&?9u`b?Tb<nQS7Z+%<z)yvQ`se1s_PmVA&oCN9(wfnYGO0?E&UPP^}41Wm5~_@CCFP2up@QGB*q~bV-^fzcju3?NvpiKdkwDULr^$&#0x|sH`eq!o=<ODKCLcE3u7D|by+u1nX|Vwy6ySp9^YvU2Tcxw+94RUBE3eYf-5?P5EH?~q<xxH+I0(}Cgo=gL}4VSiR@&0+KGF`Q#(gseXip#qrhzRwndq|7h%Po<gK9LY}xd-DUkIvsr+mpHg-Y?#HWi7!hz2qf92+<ZYWYXC!KtPji%9d2!bIR1>+=INMjI+Pk~la$OmTw|GWoOywNQuIK9GS=`SWQQ9DI}0Ag1Hvy`j^-~L&xHIy4y8B7BF2sHHQ1@r|cX{XopzSP0RFubHg(TF%(ZmZWGbyCuv9`W!l#iiNNtG(-r77M>&EefEfbta=``z6xi+sfiAzvS9D0~~&S{z+rt=^C!`uc&vrB?_iCeDfUzh1B>GwXqRIYlkK?I+C`R13R$Aiw?$W5j+O`xcMkDY%`oe5xO$?sWe;$h`|(5O-^t_viH7`^weU0Xgu9eZ6S{rxHdrcNzgqh6=@jw*+i0tJ_rrv*xPDAG(>0F#R02>A!cbInwk>}n-@<GPxPS)h)MSu3xqOW6=SMqH}E8v5M}4a7}<q<F5>>G50=tN9U*QCvo#a`4mx-T#arkJuLmFObPVp^s*<fFzMJsohmuL<V0!;dMBDJ$O1Y{9*zkW@f?m%$<4k0K=64>k$E5zCc6fdI8=d&9l9C!ZUASMV-63ET61{l33i*H70;LHu;^)6c>CtSGI*%*PtCg{2+L0JmP&WL%+ZwH}$jZ}cW5ES&#=mdZv)>&BD@WGmT-Y9$cW6^^4sDGqCQ`ejp)^?&uPuLRAyc+@q^7||&|XWK$~S*8EOQjM8ZY0HahG1#E)7?}M`hccB0a({+*nNWLpPb=HnB||sy|4$3+{L*91DqDZnZE&-K@`7j|M0`q2Ok`VV?cOdTt@7nkXOk8QF+Dylo>xj;fqp1)pPXjg)Y}5kLX%NOi@{tBI6qACyA#izX}4K+~iczbN!vEN)|=@~FIRQ&`ov`T6U`RU=E7VuGQkhdB7V1chQcwf)fCY_-3At`a0?$!Y=%d%EFNolBj3HI%?trs{-w=jb4D?q^m*?xFtTlPdhZYP=>EY*FwlS1|ibyy4bI=T~;owsL<#kDMmGP&j6y4_&Fs#1iV56A`LsIoK@Dwxe+)TPF{%?hcUY0K)C9Ca!R&uh3$NmX}QOST|cRHwI-sL*~UBk_*Ktnqw%=X}(OuUd_l<NO3j8WP-XS7ZsPBT$z8eX;QtyJ|tOgI=S7e8%b87h~$`LnC}}C{S?Oah7@W{SrFx^TSWQWNg?h<Oy`7Fw!yn%gyLZ6`2kYS(;*7qYF}nJybOlBJmCf?2JFKIP}j0hyvX*uT)j4S-Su2jY8m5qwv~MX6}NVec^oGqL1&bLe4DPUM`6qy-Lv0+-^NDsQ!TahS4&m}l=Y}Zf>pbd<;u`8id~l5c#q59(^Z$$r7L`i`k_;Qdh?UjG7+6ANcva3H>(|50X~CxJt{Hj13vw&ZAyMygl-rw>h&Q7Ncx))DMX&y2WCj$N;ELAX+{kcE!Nm)p$#uPj_j+Ko&R%`hYh*Ma{G+s)S^^j!-uOl@gYbPG9k!}1mbl&G+e3>yAPwnTFHhenXKI6>YLm-MebFL`ZF$IUGXRN9K?~j6mvNzt2no}pZ<x(mwo2DA;%ZW1<dY>>JHCw>OqDztNAD#<)bXTVa7@%l3M24H)l9%_!B`t{dv`llN2&(A0!yqj|u$jZ}O=M7A6c7%0CF;=3FuZc|L3PGB^W7oTvLm;ngod8w*P%oLFmCiyR<~`=J-Ek#Kc8p@o$CkF$ypuHIW8uR!H`p&xZNcoa`;ZLC?m#4!H_MJ<2aV^7h|zP<Y9XYi&Pi~61jg=5H1GU8!~c)CFUMblfgD%&o4;b9b@>cJu2<*2WMYNp09q{HPFiQC}zDa8caB$hi<cIXlFDFYL;f+P$SI<P;obBHrt=nUXsbx$bf*BOm{i18B)|DU74Iy(~<X|jV_n4~Q{s(p;X&Ac^wS-I&<9*QDb`UOFAh)8y0XSk|+_QR#_+X-fzxu8S#aT}3m*;N9QcWzREt|Ocf=oWfNSEFP7Qy8Qmd+Q{F2l=JLQ|N_a=$e?Ul0d4fciR}MpJY3JFfR%3$N={haa{yi5xGn|6@P4qB=lSCurH6)V)vNFS;GmA93stEjbAK-J=xo!Flpuiw}4gk1mZO7MvxR4mj;_RGM&{YuFqf@FA@YWki8bHb#=6jLC;2={D!bug>~Ui_CjhMY<tM*hUFC#3$6!xl$U_?<|E$ac6d}!f+E9yP@WsK`?-^@lOY^tPTfi7q3@_|!B~v{-$AmD?=(M+&~yqX27NZ7hM^3x2wOr5Pl!q4?>5)C9+!<6%1&Yf$O#W8ag@PSEgwttE@wK{a6N-r+vq@iUFbeV*SsTd`o^b`OcpA9K&|ZXPioo0sMmB0f!?V^vZp7p8e<*A#f95>FL282yXeuTG?{n1@jL*hVJ^{i=@!PZ?EL^A6Kz9KyWIA?<!?mdFrueqD-%Yo$@j3}gwZ9d3}uT1b-JBN^Z9DgnI?%ww<4zeaqGX*00~^ik5>;y#F8%?`G9V7@)Qq~G`4&pB(Wmv$?MOM8x&sgOb9K>o6AZl^71FhbH)=<$yS2Tq98GFB}5VhFntvzvis`XMlwcJZuwp|-CHC1F?!gXIr<<jBs@K1IJ6__`k1GUz0R+-JbSk1hcZ&E7$G($<1l22I$B@zag{q2_Gd8K$P1^hznG;Kwb7?Kv&CTa6UfpAe^X|e?wf>)oK<36uQgBR(<0!2Ts!Sl0uD-N0pcVQFvktn^KZ?lpaROY%Ef?Z=SFQM#PG=yXx#W2we8hevw0j7#-2I>2bK2}j)Q|=sQxt+06xlr)g}SYa*mO0t*G1c@sWY!x)liElo~qmU^*ngjpo*9rX|cE<Gc!j47269ASy)~=Q<IDFIEPDQPFbOE-f=FX!_;^=<o%mQeCdo#i3A)gb{sNeU*b$F>@1^QG=pLi(*>~d>s5<AaT!VMu)T3zTsn81Of~+T-t+0HqcYk5?Qgq8^b%$gP2(h5Z-@fS?`slX7;bW4Sbf}qtzOD^<^tOR0yui;`5m=YV_R)@7Ms}A~X^Q10F_@E|ghM@PTd90hZ@i5d{H2FqWK(hZvlo*db9s*Htn1PfrY}9a8L=z=*lC&jAoMP3n)%M@Z@oR-LeAD!pu8u}Q2MjY36lHTFkzVbSbgq5iu^pqZjpOcps&+bVPFbX!#foi$@l-swaLqZm|hq&8_{aBH-jiFw;Kd#-Y|mWK)_CXaw3`#aF;wZmUrwcvm9E@=VWD_v2d8>hnl-!K#4)8vZ5LG6(&n3}tcgZ{Ba^87gjzK_JBs}B!q0phmE&~^oCo6`vs)uXe#d~-JtKcaKG@`RUe`ZOG+ir~6VE43@;`J1SA_(nPbPVxTkX`@*aD-4<?T+MdVtLL^=>@_QEQFx(*y(vj+z3eY1>tSdT82D#7fzkEh23i%mW|+NQg~#J-c=v7wDHevdqSA{52w}W-y!Dt-r%W`6D~?}qhz<hg;?RZjFtShJ8*x(o-N-L$OGe1ogetZ=5utj6C7wgO4aO#q4o!Hn!)Hhm5Tp1)oq?!#J%gYnuyM_{M_;>Hp}^8>8(xA6NDjPTtemFiJ=!vygR`pdAN=>m0y+2W|F%<@Kg@9^R@nCj2*ocS|95H=#rKmCb3R7we`&3Ukx!FSDfgEgmnxl!-!Z1QbsKu$(n@7od#Sjeu}V4i;M0*X>}6_)`C_z5+VxwsRiI#!3%VfkE}$m?$FvU4=GcR2hQp2gqQo00CXa-TN0pjqc1LY8zC~#<HBh4sdYxiC?M21Ck2CS5D%>1l%mlFLzaQZk8u*}mnem{O1xYkbaaOO1HF~$oMlszvKCfGT+bu%ET1hB;>E;_z=cn@0`pkub86!^)-}nXV$~kEQ??_03^;`XQd504F`@FVMvCmgcB8;<r>?U9J00000JBE5-973$D00HS)|GfwRm(oWZvBYQl0ssI200dcD""")

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
