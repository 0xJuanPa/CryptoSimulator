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
        self.table: LRtable = LRtable.deserialize("""{Wp48S^xk9=GL@E0stWa761SMbT8$j;YxZQkX-;k0S;{*So@k!X(!_$dkC`jWrr3R=U*#h26E`Nq<yw#DvT+=UzIDL7`}m<0`c&cMIVm)q%ttB#GJ>^Lxl&?KpnI%q;AA35|MNiX<&TPiC9=s0cwaE7bba%;NR&>pSL`+wLfFudHgj<VEYbz5J8`ErbIBsv>VaurD@)MZ|kp@hVhMMg@MI?r_Rg6aX(w}m{$}Fu!aCTy?)m)cmB4gIe2{-m98b$5?6+Uf!7#X2N%85q~?E}jKrGv*{B=ZrV`#qk_CVd{1s%pbVEuSRZ3C6-w8gT0c}8ivEX*7ZFR)!C{w?cP5h-OgWl0K_{m6NMsa_XwC+eg_@m8aTB&m=4?9SpsxB2w`M6vdb6Rn&sCFB#lQ2`p)Y69S+QY3^;q38jM9iHkRW3Wp@T}c&vjT;><O^|c^&j)i_a6iXV2GZlgWcsARp@L@2xHi}>MS2y*>CklbG^!zXQ@`@b0UPSqSoA?>?UKQf|=0KDyw%!bPTE-$xA{fbn4a52*-V>*!HxZt5obKC@M6Z=!U)y+n?MJ=lgYA2pvSM0hn|`4>?yyxig>K;C6=(ojh1Ly#_FC)hy`Qhej&3+q?-#6uHl%f8wZmW<K))U`BWY)1PGw0COQ!dUdW+mLT6?j4pLn4B<p5%M0zu^@rXFS&)%R>Nui+=?A}{94$gg;Z@<~#aX!QtK~0(6(W1OXeB3W*m`0?tvrwg{tX#)_&$2%GGxRNypML#J%3bV9H<O=%V*I4@4;!nX6(7Hz5s(6U{O}vYN>kEO2(!G34_IM6#up`3J_JFbfiQL@r0P&l`H6hZubJaSUBYA{J!`ml(wba5bQA)#&Cc9Oc>YuAdYEwY`7@oI;#C-`@8a{Q9X{J;`mw_2xUp|H3u582!vfARDWZ#jFb_0X5Vu-oK-i6g#!rxtFc1CY=rENC_aE~z2uVulw+b-)t)a_4me2z>wtW27`;{5TH|nnb>rb8WwHHbBMr)ktHaOaG=}_StLDKogT!NDvbv;my;j6f*>DkU6ZOvn9@>nA&6{d0`A?oDa4q^VfU)r3PK^(q@385XzfCyk_uh6sGS#AH-x}v4gtHt5@_5qKuvG1X8t?!Y<^FajkgAQt)UzGQx2zNK*%6q^!@#V{Rrks~J-)mz%Ulzgbd;0EGK%(~^P!*~9hoBmX3V9xyC3eG_S_;CDv-6vqe&ViBrgTe5d+wVnO1o0f?w%gZ^-)aJZLbgxj}s<rU#pEd?X!lhadpEIZ9B?KWFE>3G)vut@WK1so-g3BjLa+Vw-9H)Egz=zkELY4G&rxRT);A9B`^|6`NlfoBv~l2B#s4c1QE9gBMDR5hY||J~^ddR4GZ2<sEksi*dORlk}4z-5UVE=i&hi?-;hZh!am#KJ2<9$MSO})$oSH0U8~^OjSR)O|9GaivQ#JO;ZXT@4sx4Y{+M>{TF5e_b;GzWqttUS5%((0@;&t{?X;xUv$52?u{KRB9Hy&sSDvY1G-n-m0SSaV{+lj@xT+9fbbQ`g366v4}WNL7R}xRm?!x=l=GISl*G`i!Sm|wdY2k6I>A~&$0DLCDblsyN+~yp&b>L-cbmx?EKKt$;;s|L*4O2w7>QV_4zq7si4|!tNSegZCSM#NCESvi^wrIT)Ftk&Pa0H6JF6AhEy8jIj8op$FVB-UUCiRb_JohZA1^6G=q@13wZ1&t+Z(og#w??2jMuf~X*-zP4KXX_;52t<o6A0llyy*Ysg<Sv6<Y_8_1odzh+0C@Evtz^kCO^dVG6J~UP=TsyF@h*JoW&&qVb5roImVv!F5k6k)*ENMr2)1ph>8&{=tlr)%MC7{$fAO<b#zKMV}12z8dql9p2vcfntfCvgw!Wd06ZgB71Cn!J&9Yw>PpMEQ95K|Cz46iT?zy#nT)7Xlzvpd%Ot=o|!6ga#@QB@w7WZk=hF<#8OPs2{oW%$hZ0Bpo(w1>~4H4-jy*dJ*Fnl-k$T|az+7lFP*Z~<?0=Q7aiU}8$j^9Ph|&zW#@Ujh7<Fltke&awvtlBR^I2JFjkHxdkq9&rq4(t7A9G@22x(Lha>efl<z=_{EOwgOf3iFpd$YN=5SN?qUL;#FryWJ@fq*uSLy%K_?*xPBTV|rn;g}+n%mOOC@likFdUxl6`ODj*#1_3T}h?V*w%K9POgR_U@LjlkZjs&ko+Tf^M{DOF@(G^thz|QjY<eg>C=dE?5Y@6n9}S^aNyDJE1>=oTif3(3pWG0RdnEiyh2!3XJjtNutDuz6@G1TKSG`sO#aHcH9+w3T*sCA?D5slQgG%&Ax7&2hx0x90<{nJIe^o9Lj}4v%j2UW3H_7O5?qx*R3CL_s5K}C{C`AdQ+^5|EbjIB1{c#n#Q+INkf8@zlt$gqbBVZgg4157UPQD3DI6iU2|m3#P(xax1tm5GR}rm&It9=E-UOdhpP6_JKI7Wg-KuSSdyGVtE7sDx@O(EHP|?*;;^qFP;>~fi5Qp`<8g)c^&EZF`Vy}7d&V7<8U5#hu%oT`6dRrh^533!pq(LDGGk~1Rg0>fQp9X=>X&Sa1X^G5~JbG!OLS>8G6qI`R+R(}m&o3sN^in|cbgafV6a-+1Mde9xLf{cjT7awyOF7bjcF2W(1mRBqjfjB(E`FdKRAcKdw{aVRG^4;7ixA?Tn#)s<+7_2lGxz?o^%wSG{V<LhCBtml=DZ%INoB-NdkU>^Yz2)LDv}XQ-VnD&s%hSWK8m{(UZM*5h&r-?#^N{f{7;dL6;gfJ7+AV<L8s~IhPBWmsK}#pC#(&ZOjBtoZDYt}Sjwp};@a9+st0c{10qqy2#GoEi~Llhl(J3!1T`dgg@FCaHV9XXvS<ak>ARnAN<}C?F%cnSXVkU&3#?!g5whzeX@Vx0;sdSWvoorDOiapH-_PN|LR6uGe-X@5*|$WA;oSZxag{A<NRUQvu!#w&PMc?!Jif%XbL0hr2U}^f2~(mdJnEw&%VNTdY{Q%VXvf@eif{`3Vy&VpT&@|pl|ERtxA{y^(e|v8vM7NdHZ+VKK$ilw8n%90p%xc?9j@fq5v`%rrDudp;Nex2uqD@$g(6-jg}?s9wg_7(oE*hTvjJx}BahjsGyHd}$0eMBdWIkSRhSE)-9tl>1?Bg8iWMzxqxBV37Ekv`@1VSchx5w*@}6DM9C<_;{z=rZmVw7xt>fg_+*JcMVkfU22-^`fHTegKMW5~$MfT+DWd;p;&x4*SfwGpHq57;f)KTDBqYA_&Dy6v|1KLBO_d~Q4Tft}x#}UX8>F!)p%<gc|J52>cY0jRj%POjH>~Hb@jXi?Fuj19Yyt>)=F^g6UG`ru-9tmYBwOe8jbrb2a|Jy9VGZ4a;YQ-;czDiP{wt*^N8WGo`53H4yGa&DoB5<7(0uN4DqNXEYMgtvO)fR_ZS+!?p@y-nWsbAjU$7rSovsr+o0Iitd{84H8OAkqX_dl76G_MdKVYeY1ZkrBhn%<9)a<pp->3vi{?8Odpg{KHw8l(Zb<W_v)7dgEX0<5Ha!w+_t)bSHFm<5}~u{99JygUW@9AqvT%?KWWxw)s~t2l5r6VNX(+<aJII|^(r!@E>^r2Ng-*n~0rmhF(!t5aZ154j1TTK{jEGuvBfD-Ya>%CJFejveoqoJQ{j97d(9L=u!e?;5K=R`+mrfPCR++;zp_@>JF<aMtUpP-TSn$ytp4;ZybF*{R`?(d(Xx9&85*OI4n<r=BxHx})UzLGJ(kLM``T*@uhCv1Qad#T}%S8cSCcNCOKLVT(pa@Uz?u1^E-g&R%<uw<A32mFSq=lTb8r&5*p^WxZ!dzq*bx5U_hTX$`Btn_1u<cQQy?qK=+u(Gsiy)s0_OKuW`W-@x+{|4d(EPJ(R>Nlugph8#Ts>^!gXe|Vc@8;wIF#NW`?efjJ&{2QSBW6UI&@at&`x+=4NBP)2&dN3PV#rz@fOwauTjja`zs6s!~9}#v_Dj(I!uUL7I(SP}B%cVdI{>EnAiEatQLRtqb=d{6wo1%$EoT7ZjYMypw`pDSrG&?9+0&9;%vWdV{Cd|C#RXL);F3tQZ><8!@P8pPSO}{V>uYr?q?Z61-<V-p)%akNaY;pwZ`0evw<}T5^=jXj=NtJ+|943YnQtM+iinig`+@<tVYe2SH&q?v{<Fi|A0=nn#&@rh?_>)o>;&M0DMg}H=jNaL$eW8ZGm^;z>Z3)s@K8nI2&8l02SQ{0YlTIbqg#Y`Ek4+odS<g!@Y(ojBTu8&f<DjAOs|8pP2jdS{38GLf)xy6i0hNif<*WL48HI)exa>0<LY5<H<7;}?Ar@%5&vEUJsKbgQYn=loo%Li(LG}0I7gv4~Ts|M9D~KH1H3d=fvWt+jKwhv4!jYeY12~F|o66umyJwy`TL$plq^>wj6Okw>hj`*?=DNe}X>@8PDCL%uXZ}mVMWDgfpOHtgBA{aw*;wl>h0FUg|H$6F-3Kzqp`1x5TTH#?#F}>?^u+puUTSc?unf?*)mR2xT2U{V?v_cAHJ{NpWDZnmq-EH-RIvd>j}82TfV$U#0u)zoMSdrNAUm3pd-*aELbCDiStH$sa(w~}_ctzGTj;F{g!0n3Nff~wSke_a1h~grlt!~dNKfKsJ1r$fd&9wT;JjsEmM<h%_jq3at{JElM)IRmnXU`zlZa0y%U6-7H?~9dTSvx0)Ppct=v6&hP8slF5rmFRXA?;`Gy(AhK}MVFEaQk}t^Gc9#u}{^h}_()5&wxzj^J-Co|L8+uyC<(Vwy1cvRb^6ViR1_?8$WbPu~anChxV1<$?=^+MEA^{BV}Ro@OL^%QJT)TD1Uy%%sOvj-|qW-Rpoe5N`fd;V}7kQLxi6v;7ws`i<}`&koL@z%rCiaTR%gI6&n;KBDzyfX<i6V7oa?MP?fbUeq6vdV3j~*7=-(M61S7X20oN>L4?e`E;MGR8unR&7W?+Oxa>OR5pXL2pEHZ2lQS&UhkFOL4-}^+1=#Q1g!qRi2R#|d2~i<gc37(vABI#WqpOFbH`B8*XGG6U-xzG@2lNlm&PI<g>-*t_bVl|d24&8i+GjAt84<$c*L!W0zaeMm3u`?c*NP<y-G_sWu+|@X(CF0dqLhK(~2o_sI!t5J2J<&sBQfQ*-DQT7WD{t2;fiHS58Tv(8>qobAEh?=Y1HT2Fp8!_5sR%HX*iQ8T}rZb1N}G0pI#1$B!lFo@@3WZ4KOk>85OyyFwmYE*s!22LU(&ZzR7qPc4*%1+-c2?~I7ZQ!QZD1?T5E1Y6C;2z?NSCyf5e*dCwoEtliPCpNN_;b#QT@f^B&;E+ez)#B{gc5#kwT_4s7nFP-RClwOF;MMedSgQ_%CAzL*M<nC=ot9jkzWKazmJ(MMTh{;;s&)U3mxa?}Gc=RsFw~S$Ivm4luxEX*<3D~;$T&0sqHfAX4vWY7>eP)e97$@@(HQ1-?P%YU<25Sf7t=Da-L)cQ60Yv?!zUL<(!9P|y>IR<m9W*77=1~a*}9QZ7D4VjqXp-^E^(kB>jEPem#D<s_RWbhudR)xxdQ7uio0FxTNE!1j+GSjSlmJ6@}WGF%D$j9SUj4S_o(Saa`!^eHUMwoa%HVI{nO*?bI^0wskP5M=0em7YMCH}{D%gM^(`|)yKTXF?JHP<INOx`<yWcHz5il>R2P78W83dwc9k}7<Uae`p~f9u^t>VOiC1>v)K2Rr1@%b((kG!y+Y@^va`{Nu#DVF3$F}XdrM?3!sDI=$C-Eu7^nck#1aOLhBt6N~$zlOoF>Lfk(g;oDTuG%xq0r!y-TV^COk*uzdyPxH2n0PU9|P#UOebEPZwSXxcnt{;g)BQbQOJ5W4q)Y6r)$HdlXMmdbVKb&Xt<1CT*6yY+vn&6Q(y%Okc63EeMr~XC;xek(r1zUn`*Q!<g_;GS8<&k=bi#BJgmrDZhcIkJ7woS?R~n#{9ej}&ccI&KEaAn83!j2RG|O*n&Vf7+DJm=f(pY0V~=?;8in=zK>iZ@Pa``A;l9%(X1gJ|sJqtV!2;Y}*j59r9`DfpAZ45H<TK(`9=@I%Rco<ERL{kwD_VPuwbC>yJ^rZdhh(VZWb*0Kdp-$s?7^W#e)?Snjcj+kLn1+9QPVE50JN<R>BL_R^AV+8;}n?fKp~Nez5D2$-`OY1tJb<)Tkxpf2gv<w+jgUfYZA;SsqVbF`K|J==Q3H~;Z`BIP|med_4pCMv4}}dQi@*6DOQk|>$>7HGh!|;8bvQQY<-Z#0@{hW@KTM|s)E-_^q+PgK3-rHM*&^J89RXP3eT2N2EAyaZIk|_VvQT~)xtQAt0o!>Eha`R;IjOYgQ_?UYUi25yF{^aM>!&mPL{s0o#_x4Ra{xP9yA-@ReQ}ie_8|&WVY#;=}u}23(FXC(KKA!aDtjX(&lJY|37?ygq4yA$gBoO8i0d)4QjXulR15EpG<MME=fx!G)l6@!9`RplMD<wDR#oWSGaOlM?8R7OBO_R?CK}=*`0U!t~YOGqmyI%lkpT=8k~uAMG)t7<xaCH0}=(>75$FD9nB6FxDWv6&+h;cTN{yRP9l<|b`^V!D3}57o6Lo`|5xFAN}*6y1ZU66v*;jN$)8qbXtJB3`Ym_VvdL}*jBwB=pn!$|6RFmG1b&n-J1~r7c@HZ+N9je+^i)ETVwX3DD;$wcN_Ub16ZMki{Sa$@ZE0@`|FW#LF-d2EyzxZFMwyq(;}~gDs)ZZsLX69;;`=(gzk)^A-k0=-Ch%K+l}u)ZQwsMC7B(Gavd!3CB4lmXYOB)e${USXJDsj}oBAZcozpX7kX1EnOcBf^0Tn_Gi@Lu;`@P(UVhNRZ$L$vBO-PtzvML<wVki~127~BSlulmic*+=JX44xp^{;}1+idUnR_{iqx<@=yWvm!<D{ea;o#JX1CZ<G28bxB^DRWWR^&Pv<mV3wVC_gvBQ5vwm*@X-+;#J46k@CAC3%;XSB`yk6S`G43rI;7)DAo_FU)!JjDsLOMii@i;9(Kr`tzw2K7TqxD9vR6oyKV2qy8P|_r~5-mCYVcqI1>l?Y8m<@Vf2!?AwN(S>fookcnyo+I#P^PqaO;K9O;X*lUb@HX!QGxor1fnoxfRczM8%$<nWtq7q2*wxgbVR(!z#A89Gr9wAnO1yRZswn_SrJbh8D&MK2$-Bv0e<y}_pM(OS%WpKpzFh4x1XP{k#O#6LAVjg7!EDR$Vlg6jgI(=1410^CB;6c8d5;az@*5#ZBxX@TH|%zn8$M{^E`zcIX%M6bN&rb%0|A%4$7Gd=Wutp4<P5OUbRk3f1v7l1pkS0_pheWp6PCzgc}ixI1vGqMPS$Bnp&SR(c&Nq6X3{Yn51)TCRqk@2is9|ifF{+~p7uz`{Z+0oB*{njsiLb!}2VGePCa*-c-un&_b78?m2ZMa8P2}KL=jcyC5c5X%kmh_$GerwbHG2;V4j#UuvqA#BCGyNx0buG+8lbya}86R1+GOljxmQo6A%)V&n3a^`uDVgfD&8Byo@yMAOD7{g~X*I#dDPC=XuyKvtFRZ!XlM0YrMKeR*FEULeo)IlGF1cpAj@=o9x|F#4AmgNdwpp_G;}+(KKC49yKu~uNbZ!DU&QrJxFGrE1=<bT{q5fpecU;il1Sk_i(cF%<p>d^hj}Zy<0~k$C;V|UYDQ<+jSzF58OUf7Y;Ij3w($+TCn)Q>5touC#ChG^767pue0s_6gv^tlM?RVC5+F{zq!<K6Sxuru;pAzpO@<$qdQ78+w7H?!PmJZU5rRQZf4ny7(?M*CAC~c>k7(_RiYMZ6RJfe)U5ky|C;3@_>;&@PvxcWMiQax9SLg|Aqj7)0jfv9*gV`4oAbIQjh_z~S)v0@yeiSw!dbqU!2g@c0KmS|REJ5!X;ED-k@0TFNPT+N+(D$r>NasjTt2Ut6)MMi`5rpYsfkIBYK%CsN<6k?r++o4o<gmb(7?Q?^|(KzV}fBk-Y+J{)RlERlWNpjw_bBUS=#<0TLciI0;{oJmj)HwwV6v$?s*RwwW+a9wK-6yngPz58dp$hf3>Z?%(KtV9@&L5pGzAX2aV24meI7YUVcy=C9Q|%0|p)pNLsC_`F12ImZ7C<tp)cTyGG78WS>iK<+AvuhdfOx>!-Y1tl@4<aqD=Y#$RIw1jz_%v_W{6*@>G;a5v1Qt<?&{d$cCe(*)AsUo8SftF*6_-a9&)tH0U_`n`tbQU`@rcqW`PwwQ|nJR@P+5OQlvqR#-X#vCBnZ&ZlV5YvVrqi$cbFAcVYCEZ+RTF7C)-|-`<=Mr)6cHe0SA>?$>b%$-n}z24mMb{7o+Ly%&W=O%R~2xM<e!pipePm0{?IC>y+iO>uhPbiH}XtDvVVWD483Ab7Ep4^cBw1Ob;P-(lhjAcR;A&yNgcvXnqscAmOkz3$zQzm)Xpq@f%%)A!UCm%ePk1a;(Oc_;d8lh6cE7B06$M1=nOAps4tt@fes&W9P<$qflLsPXoPSUaWi^mW=SAJ_dC8dDGj#)!NW*^bNHS9wYZh_c?2S$Uu(z;#{dWw-iQiQ1p4r|bdqlKfI?<z!`R1J})Wr>mx7*mFXZYF3W>ahhZHpvf{MNRM)$2UiF7Aw!~a=gYSyw}8&KiN_SpE(r}^8_%9-@oRG4PmeI6bd)rRO?!m8sPMuXTq4Xg;RRg!P~ih0-7D+FZ_{OCh$<YD46zWN)m_qHfv?s}>+AU{gwsD|l07+TwsJK!eJKZg&Y40l5=U!gE^OVyZNSJnk5p;qnHN*CLTymVezM#hQHXEpb4SH=^npi^x^vhXDHw$_@bxDMN~9+WMf!xp*^qZOZc*Ve2`B4ws-1l5dUM;WGu%Db$19Y1@n&ZjoU^grV14l(^w4ZQOM#5sdDZdzVBS^!RsRefyZQ}=5_*^NC>GB%LDn3u>Wh4)1coJQonZzJZOL1OZ@*h3ji=!%!*zXhAJKeqG3$LIG-ZU8k}gwWHy@~h>*IXtF1qICQ*A{1YP2u=>4rkrx)2<3>VU9|z$8z3WE9W6fgVE4Io7zimmQ`rCaT3M#;V7Q98td`bQ#u69FfRFZAXMVp}8yf5{VHdeZiL0wFS`&sAU2ef1Nwovb-5Mun>Hth7uZUcj-6+6kjFJng_~wjGb-&?ctWB^M}|NB^)7bp*{N1dT9**$HNq@UoSt07keiHp(i}2ZaN<TKJX~fJJPv!u|76Huo!zT{tdYANZGv}AxgB=mC5D+^^oJ0^=zst|B0$lTxyPX3jur&XxIH7lgN)~MMiQyF2O?6+;k)k{>C-y?pX#Gf8S9S(O!vCt8md9DCW7N_`p<GorV0hdl1}K=*s^v;M3jD8tM}(JQgIv$%onPrzu>A6;LlI%3%)GXY0sWZ48N|*9hykG~6GHNXDMsWg&ZfC-ep5>mT-8-<UUR)}@Mg%t`F=kdBSN4NY(qi;1jCn_vM#$~-9uYpcZk0})-gfG3BLl7(GVW?ryO@KjEa+tW?U&4h=0ND^KI;T002KVsdcJnN5^%j6XDu=dLOf8eW!yu7QY`=Z3P?Bh&EF3>#+n&Ti~)Bo-13wa=5U>r%SD?v(NjExyv!fti(3hwF#3^Qf#jB)ME_HVHtlR+AvCRuPDQMHgyggoW_j4b7zgi{VrFb{$@3w1cH0+xWKm#Z<*Ax+O1mT8;vJK7^^X`o`-le_!YI$3QU&{dW0RMnm>p~@kf-~Zhp&{3O#;7KBWym!J|{6@cXJz2?&5|7sXXq|2%)y}kC#OBJIwT=TQK1HQi*(tkLz=QHQDWcf#(<(h@KR~MQccDT$Ll(t=8gEHm%y#E)ZTJJC1J2gAzWA-{Rp1IQg!ZwAPekl!4f%Kj<s?EWJwGI1-1+oFTJ`KGx997<7Ki}veTH=Jq>)^;RgkA%>WhtW^-_c$e-s8zn`0Q)bF~sO={N&lZMD9JI8PX5j8&`qcp7#1sbPnPNTFB(lz;^ofL-)xTiN^C&fcl3UhpOHof+a<G<+nn%2`lf-foI6L)oHI6Dv`()Xs{^#LThwlnfp;ev@Uu3&qKNFlU1h9#PJ%JdWke8RQOS^F8+k-E;r|coC+2&-p}z00FE$`;-L$unaIFvBYQl0ssI200dcD""")

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
