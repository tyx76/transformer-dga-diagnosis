

文章编号：1001—2060（2006)06—0635—05

# 迷宫密封转子动特性三维CFD数值的研究

刘晓锋，陆颂元

（东南大学振动控制与信息系统研究所，江苏南京210096）

摘要：迷宫密封中流体产生的气动力是导致轴系失稳的重要来源，密封动特性系数描述了这个气动力。本文建立了涡动转子一迷宫密封三维CFD数学模型，并以压缩机入口迷宫密封为实例，利用通用CFD软件Fluent计算转子表面气动力，进而计算密封动特性系数。计算结果与另一CFD软件TASCflow和整体流的迷宫密封计算程序Dynlab的结果进行比较，表明三维CFD方法对于失稳力的计算精度高于整体流方法。最后，深入计算分析了密封入口预旋速度、间隙变化、密封锥形轴向间隙等因素对密封稳定性的影响，为减小密封汽流激振提供理论依据。


关键词：迷宫密封；计算流体动力学；汽流激振；转子动特性系数



中图分类号：TK26文献标识码：A 

## 1 引言

旋转机械转子系统中的非接触密封在阻止流体泄漏的同时，还会产生重要的流体激振力，影响转子振动稳定性。与动压滑动轴承的油膜类似，密封中流体膜(汽膜、水膜或油膜)动力特性中的交叉刚度k是促使转子做非同步低频涡动的激振力来源，直接阻尼C可以生成对这种低频涡动的抑制力。多年来，研究人员对密封的动特性从理论分析、数值计算、试验测定等各方面做了深入研究。传统的密封动特性分析采用基干整体流理论的控制容积法，近年开始了计算流体动力学(ComputationalFluidDy namics，CFD)数值分析的研究。



Scharrer和Childs将回流速度比例系数作常数处理[1]，计入腔内回流速度对壁面剪应力的影响，建立了较完善的整体流两控制容积模型。至今，两容积模型一直是迷宫密封动特性分析研究的主要方法，但它的缺陷是不能准确描述密封中的回流，计算泄漏量精度较高，计算动特性的精度不理想。

Dietzen和Nordman首先提出了二维CFD摄动模

型[2]，用有限差分法求解不可压缩流体$N^{-}S$ 方程，获得了环状密封的动特性系数；其后，Tam采用三维CFD方法分析了环状密封和迷宫密封的动特性[3]；2003年,JeffreyMoore 利用商业 CFD 程序 Sciseal计算了静子齿的8齿迷宫密封动特性[4；同年，Kirk和Toshio 等人应用另一商用CFD 程序TASCflow计算分析了压缩机和汽轮机的迷宫密封动特性[5]。

国内，鲁周勋和谢有柏1991年用流线分离法划分两控制容积的界限[6]，计算了迷宫密封动特性；2003年，李松涛和黄典贵用自编程序求解迷宫密封三维非定常流场[7]，得到迷宫密封动特性系数。

本文的研究是建立涡动转子一迷宫密封三维CFD数学模型；应用通用CFD软件Fluent计算压缩机叶轮入口迷宫密封流场以及转子壁面气动力，然后计算密封动特性系数，取得了满意的结果；最后，本文计算分析了密封入口预旋速度、间隙变化以及密封锥形间隙结构等因素对迷宫密封稳定性的影响。



## 2 涡动转子一迷宫密封动力学模型

准确的密封动特性系数是转子系统稳定性计算分析的基本条件。当转子在静子中的某一偏心位置做小轨迹涡动，可用8个动特性系数与转子位移、速度的线性关系来表征气动力[3]：

$$\left\{\begin{array}{l}F_{\mathrm{r a d}}(t)\\ F_{\mathrm{t a n}}(t)\end{array}\right\}=\left[\begin{array}{l l}k_{x x}&k_{x y}\\ k_{y x}&k_{y y}\end{array}\right]\left\{\begin{array}{l}x(t)\\ y(t)\end{array}\right\}+\left[\begin{array}{l l}c_{x x}&c_{x y}\\ c_{y x}&c_{y y}\end{array}\right]\left\{\begin{array}{l}\dot{x}(t)\\ \dot{y}(t)\end{array}\right\}$$

式中：$F_{\mathrm{t a n}}$ 和$F_{\mathrm{r a d}}$ 为密封气动力的切向和径向分量。系数矩阵含有直接刚度$k_{x x}\mathrm{~,~}k_{y y}$ ,交叉刚度$k_{x y}\mathrm{~,~}k_{y x}$ ·直接阻尼$C_{x x}\mathrm{~、~}C_{y y}$ ，交叉阻尼$C_{x y}$ 和$c_{y x}8$ 个密封动特性系数。



实际计算中，设转子静偏心为零，轴心$\mathrm{~o~}^{'}$ 绕静子

几何中心o做圆轨迹涡动，如图1所示，e为涡动半径，Ω为转子涡动角速度，ω为转子旋转角速度。

<div style="text-align: center;"><img src="imgs/img_in_image_box_141_185_361_400.jpg" alt="Image" width="21%" /></div>


<div style="text-align: center;">图1转子在静子中心涡动受到的气动力</div>


式(1)的系数矩阵可简化为对称形式，即$k_{x x}=$ 

$k_{yy}=K,\ c_{xx}=c_{xy}=D,\ k_{xy}=-k_{yx}=k,\ c_{xy}=-c_{yx}=d$ 在$t=0$ 时刻，$x(0)=e,y(0)=0,\dot{x}(0)=0,\dot{y}(0)=$ $e^{\Omega}$ ，作用在转子壁面上的气动力切向分量与径向分量为：

$$\begin{aligned}&F_{\mathrm{rad}}/e=-(K+d\Omega)\\&F_{\mathrm{tan}}/e=k-D\Omega\\ \end{aligned}$$

可以看出，转子静偏心为零时，$F_{\mathrm{r a d}}$ 由直接刚度K和交叉阻尼d决定，对转子的涡动半径有影响；$F_{\mathrm{t a n}}$ 则取决于交叉刚度k和直接阻尼D，影响转子的涡动频率。



算得密封中压力场分布后，积分转子表面压力便可得到$F_{\mathrm{r a d}}$ 和$F_{\mathrm{t a n}}$ 。在两种不同涡动速度边界条件下计算两组$F_{\mathrm{r a d}}$ 和$F_{\mathrm{t a n}}$ ，然后联立求解方程组，可得到式$(2)$ 和式(3)中4个未知动特性系数。

## 3 涡动转子一迷宫密封三维CFD数学模型

### 3.1 控制方程

转子涡动造成的流动是三维非定常的，计算域的几何形状随时间变化。如图1所示，轴心涡动轨迹为圆，若坐标系以转子涡动速度$\overset{\rightharpoonup}{\Omega}$ 旋转，计算域几何形状不再变化，便消除了控制方程中的时间相关项，非定常问题转化为定常问题。



汽封内部的通用控制方程为：

$$\mathrm{div}(\theta U^{\phi})\mathrm{div}(\Gamma_{\phi}\mathrm{grad}^{\phi})+S_{\phi}$$

式中：$\varrho-$ 流体密度；U一流体速度矢量;通用变量代表速度u，v，w，T，k和ε等求解变量；$\Gamma_{\phi} 一广$ 、义扩散系数；$S_{\upphi}-$ 广义源项。



中国知网中标系中流体相对速度$\begin{array}{c}{{\mathfrak{e t}}}\\ {{v\;,}}\end{array}$ 与绝对速

度$\rightharpoondown$ 的关系为：

$$\stackrel{\rightharpoonup}{\boldsymbol{v}}_{r}=\stackrel{\rightharpoonup}{\boldsymbol{v}}-\stackrel{\rightharpoonup}{\boldsymbol{\Omega}}\times\stackrel{\rightharpoonup}{\boldsymbol{r}})$$

式中：$\overset{\rightharpoonup}{\Omega}^{-}$ 坐标系角速度；$\overset{\rightharpoonup}{\underset{r}{}} 一$ 计算节点在旋转坐标系中位置向量。



近壁面采用壁面函数法处理，针对各输运方程，分别给出联系壁面值与内节点的公式。

### 3.2 边界条件

在计算域入口，指定总压、静压、总温和气流预旋速度。入口流体的湍流状态用湍流强度I和湍流长度l描述。



在计算域出口判断流动状态是否超音速。对于空气，入口与出口压比$p_{0}/p>1.893$ 时为超音速，此时不必指定出口压力，程序根据内部流场计算得到出口压力；流动为亚音速时需指定出口静压[8]

在转子和密封壁面处，流体无相对滑移，流动绝热。旋转坐标系中，转子壁面围绕轴心旋转的相对角速度为$\stackrel{\rightharpoonup}{\omega}-\stackrel{\rightharpoonup}{\Omega}$ ，密封壁面围绕原点旋转的相对角速度为$-\underset{\Omega}{\rightrightarrows}$ 



### 3.3 方程的离散和求解

采用有限体积法离散控制方程。连续方程、动量方程和能量方程的离散格式为二阶迎风格式，湍动能和耗散率方程采用一阶迎风格式。

密封中是高速可压缩气体，计算采用耦合式求解器。当连续方程、能量方程、速度、湍动能及耗散率的残差都小于$1\times10^{-5}$ ，并且入口、出口质量流量差值小于5%时，计算收敛。



## 4 迷宫密封动特性CFD-Fluent计算

应用Fluent计算迷宫密封流场和动特性。计算模型取自Kirk和Toshio的压缩机叶轮入口迷宫密封模型[5]，该密封的静子带有5个锥型直齿，转子光滑，密封的几何参数和工作条件示于表1。

<div style="text-align: center;">表1密封几何参数和工作条件</div>



<div style="text-align: center;"><html><body><table border="1"><tr><td>转子直径/mm</td><td>274.8</td><td>入口压力 $/\mathrm{M P a}$</td><td>3.447</td></tr><tr><td>齿顶间隙/mm</td><td>0.292</td><td>出口压力/MPa</td><td>1.724</td></tr><tr><td>齿数</td><td>5</td><td>入口温度/K</td><td>366.7</td></tr><tr><td>轴转速 $/\mathrm{r}\mathrm{{\bullet}m i n}^{-1}$</td><td>11 097</td><td>入口预旋 $/\mathbf{m\bullet}\mathbf{s}^{-1}$</td><td>0</td></tr><tr><td>流体</td><td>空气</td><td>流动</td><td>湍流</td></tr></table></body></html></div>


### 4.1 密封计算网格划分

如图2所示，计算模型将齿顶与转子壁面间隙

定义为区域$R_{\mathrm{1}}$ ，密封腔划分为$R_{2}$ 和$R_{^3}$ 两个域。$R_{1}$ 和$R_{2}$ 的径向网格数$n_{1}=10$ ，轴向网格数分别为$n_{3}=10,\;n_{4}=20;\;R_{3}$ 的径向网格数$n_{2}=20$ ，轴向网格$n_{4}=20$ $n_{5}=36$ 。为了提高求解精度，在近壁面增加了网格密度，使相邻两节点间距离之比为1.1。取密封间隙10%作为转子涡动半径，在偏心状态下生成三维网格，图3为网格轴向剖面图。



$$n_{s}=36$$

<div style="text-align: center;">图2密封几何参数及网格划分区域</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_20_670_475_900.jpg" alt="Image" width="45%" /></div>


<div style="text-align: center;">图3计算网格轴向剖面图</div>


### 4.2 计算结果和分析

对上述密封模型用 CFD-Fluent计算了漏气量、速度矢量图、流线图、轴向压力分布、气动力以及动特性系数。为了验证本文的计算结果，下面同时给出了Kirk和 Toshio用TASCflow和Dynlab 对同一模型的计算结果。



<div style="text-align: center;">表2 计算漏气量比较</div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td></td><td>Fluent</td><td>TASCflow</td><td>Dynlab</td></tr></thead><tbody><tr><td>漏气量 $\scriptstyle{\mathrm{t}}/{\mathrm{k g}}\bullet{\mathrm{s}}^{-1}$</td><td>0.99</td><td>1.08</td><td>1.28</td></tr><tr><td>差额/%</td><td>0</td><td>9</td><td>22.7</td></tr></tbody></table></body></html></div>


#### 4.2.1 漏气量计算

表2列出的漏气量计算结果显示，Fluent与TASC国知计算较接近s存在的微小偏着是因为两个CFD模型上游区和下游区网格不同。整体流Dynlab 计算结果比Fluent和TASCflow的大，整体流采用的是半经验公式，其中的动能携带系数和流动系数的取值对计算结果影响很大。



#### 4.2.2 速度矢量图与流线图

计算得到的迷宫密封流体速度场如图4所示。齿顶间隙处的流体呈射流态，密封腔室内部存在大的旋涡：正是齿顶的节流和密封腔内的动能耗散过程起到了密封作用。图5显示了密封圆周的气体流线，由于转子壁面旋转，流体具有切向速度，流线呈螺旋状，这对转子壁面切向气动力影响较大。

<div style="text-align: center;"><img src="imgs/img_in_image_box_523_415_977_559.jpg" alt="Image" width="45%" /></div>


<div style="text-align: center;">图4迷宫密封内部流体速度场</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_524_641_977_839.jpg" alt="Image" width="45%" /></div>


<div style="text-align: center;">图5密封腔室中漏气的流线图</div>


#### 4.2.3 迷宫密封轴向压力分布

图6给出了转子表面静压轴向分布计算结果，显示了静压沿轴向呈阶梯降低的分布规律，密封中压力降主要发生在齿顶，腔内的压力值基本相等。

<div style="text-align: center;"><img src="imgs/img_in_chart_box_576_1074_884_1251.jpg" alt="Image" width="30%" /></div>


<div style="text-align: center;">图6转子表面静压轴向分布的计算结果</div>


#### 4.2.4 气动力与密封动特性系数计算

转子偏心量为密封间隙10%以内时，气动力与涡动转速按线性关系处理，计算直$\Omega=0$ 和0.5时气动力，得到两者的关系曲线如图7所示。CFD计算

结果与整体流结果具有相同变化趋势，但Fluent和TASCflow的计算值要大于整体流。



<div style="text-align: center;"><img src="imgs/img_in_chart_box_48_188_451_423.jpg" alt="Image" width="40%" /></div>


<div style="text-align: center;">图7密封中气动力随涡动角速度变化规律</div>


计算得到气动力值后，将$\Omega=0$ 和0.5ω时的气动力带入式(2)和式(3)求解动特性系数，结果见表$3_{\circ}$ ，CFD-Fluent和TASCflow的计算结果较吻合，但两者与Dynlab 计算结果相差较大。



<div style="text-align: center;">表3迷宫密封动特性系数计算结果</div>



<div style="text-align: center;"><html><body><table border="1"><tr><td colspan="4">计算程序 $D/\mathrm{Ns}\mathrm{\bullet mm}^{-1}$ $K/\mathrm{N\cdot m m}^{-1}$ $k/\mathrm{N\cdot m m}^{-1}$ $d/\mathrm{Ns}\mathrm{\bullet mm}^{-1}$</td></tr><tr><td>Fluent</td><td>1520</td><td>-7770 1290</td><td>1300</td></tr><tr><td>TASCflow</td><td>1880</td><td>-7200 1600</td><td>1240</td></tr><tr><td>Dynlab</td><td>3760 -2820</td><td>1000</td><td>3970</td></tr></table></body></html></div>


## 5 迷宫密封稳定性主要影响因素计算分析

为了比较各参数改变对稳定性的影响程度，引入涡动比$\gamma_{\circ}$ ，Y是产生不稳定切向力的交叉刚度与产生失稳抑制力的直接阻尼的无量纲比值，即：

$$\gamma=k/\omega D $$

涡动比越小稳定性越高。

<div style="text-align: center;"><img src="imgs/img_in_chart_box_64_1121_413_1300.jpg" alt="Image" width="34%" /></div>


<div style="text-align: center;">图8交叉刚度与直接阻尼随入口预旋速度的变化</div>


### 5.1 入口预旋速度对迷宫密封稳定性的影响

中国预旋速度/wv为@nkj5/$10\mathrm{{\bf{m}}/\mathrm{{s}}}$ 、15

$\mathrm{m/s}$ 时密封的k和D，结果如图8所示。图中横坐标的预旋比为W与转子表面线速度$W s$ 的比值。随$W$ 的提高，k和D均增加，两者相比，k的变化更敏感，出现了较强的正交叉刚度；同时，Y增大(见图9)，表明稳定性恶化。W对密封动特性影响较大。

<div style="text-align: center;"><img src="imgs/img_in_chart_box_555_284_927_467.jpg" alt="Image" width="37%" /></div>


<div style="text-align: center;">图9涡动比随预旋速度和密封间隙的变化</div>


### 5.2 密封间隙与稳定性的关系

计算了间隙为0.192mm、0.292mm、0.392mm 时密封的k和$D_{\circ}$ 图10显示了计算的$k$ 和D随密封间隙变化的曲线，横坐标为密封间隙$C r$ 与转子半径$R s$ 的间隙比。$C r$ 增大时，k略有减少，D增加，Y减小(见图9)，密封稳定性增大；但是，随间隙增大，密封漏气量也相应增加，对应本例中的3种密封间隙，漏气量分别为0.68 kg/s、0.99 kg/s、1.90$\mathrm{k g/s}$ 

<div style="text-align: center;"><img src="imgs/img_in_chart_box_587_848_904_1038.jpg" alt="Image" width="31%" /></div>


<div style="text-align: center;">图10交叉刚度与直接阻尼随密封间隙的变化</div>


### 5.3 锥形轴向间隙对密封稳定性影响的计算

从设计和制造角度，迷宫密封齿顶连线与转轴表面的径向间隙可以是等距离，也可带有椎度，如图11所示，密封1是轴向间隙沿流动方向收敛的，3是发散的，2为等间隙。计算时取3种密封最大间隙相同。计算结果表明，与等间隙相比，收敛间隙密封的交叉刚度增大，而且产生了负直接阻尼，涡动比增大，这对于稳定性不利；发散间隙密封能够产生较强的负交叉刚度，同时直接阻尼也有所增大，涡动比减小，这种结构稳定性较好。漏气量计算(见表4)表明，等间隙密封漏气量最大，这是因为锥形间隙密封

平均间隙相对较小。

<div style="text-align: center;"><img src="imgs/img_in_image_box_107_141_408_279.jpg" alt="Image" width="30%" /></div>


<div style="text-align: center;">图11密封椎度结构示意图</div>


<div style="text-align: center;">表4密封动特性及漏气量</div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td>密封类型 $k/\mathrm{N\cdot m m}^{-1}$</td><td>−1 $D/\mathrm{Ns\bullet mm}$</td><td>γ</td><td>泄漏量/kgs</td></tr></thead><tbody><tr><td>1 -2360</td><td>-2080</td><td>0.0976</td><td>0.625</td></tr><tr><td>2 -7770</td><td>1 290</td><td>-0.5184</td><td>0.990</td></tr><tr><td>3 -1391</td><td>1.400</td><td>-0.8551</td><td>0.729</td></tr></tbody></table></body></html></div>


## 6 结论

采用数值方法计算分析了压缩机叶轮入口迷宫密封流场、转子壁面气动力以及密封动特性系数，得出结论如下：

(1）三维CFD模型能正确描述密封内流体的回流特征，速度、压力、密度等流动参数的解更准确。

(2）密封入口正向预旋速度增大能产生较强的正交叉刚度，而直接阻尼增加地相对较小，从而导致作用在转子表面与转动同向的切向气动力增加，易于诱发轴系失稳。



(上接第634页)

## 4 结论

通过对不同参数的喷嘴的雾化特性的实验测量研究，结果表明：

(1）此喷嘴在较小的气液比条件下可以达到较好的雾化状态，在以水为工质的条件下，气液比为4%~6%时，液雾射流中心的SMD可以达到40m；

(2）随着压力和气液比的增加，雾化水平有一定的改善，从实验结果来看，可以使SMD降低约10m;但是由于实验中压力变化范围不大，所以雾化改善的程度也不大；

中国知的结构参数对雾化的影响程度很小。这点对喷嘴的设计是有利的，可以选择不同结构参

(3)增大密封间隙，转子稳定性提高，但同时漏气量增大，热效率降低；与等间隙迷宫密封相比，间隙收敛形密封的交叉刚度较大，同时产生负直接阻尼，不能为转子提供抑制失稳的正阻尼；间隙发散密封能产生较强的负交叉刚度和正直接阻尼，对抑制转子失稳有利。



## 参考文献：

[1] SCHARRER J K,CHILDS D W.Theory vs experiment for the rotodynamic coefficients of labvrinth seals,parts 1&2[J].Jof Vibration，Acoustics，Stress and Reliability in Design,1988,110(3): 270287.
[2]DIETZED F J,NORDMANN R·Calculating coefficients of seals by finite-difference techniques[J]·ASME J Tribol,1987,109,388-394.[3]TAMLT,PRZEKWAS AJ,MUSZYNSKAA,et al·Numericalandan alyticalstudy of fluid dynamic forces in seals and bearinq[J]·ASME JVibr Acoustic,1988,110.315—325.
[4]JEFFREY MOORE J·Three dimensional CFD rotordynamic analysis of gas labyrinth seals [J]·Journal of Vibration and Acoustics, ASME,
2003,125.427-433.
[5]TOSHIO HRANO, GUO ZENGLIN,GORDON KIRK R·AppliCatiOn of fluid dynamics analysis for rotatinq machinery-part ll :labyrinth seal analysis[J]·Journal of Enqineeringfor Gas Turbine and Power,
2005,127,820-826.
[6]鲁周勋，谢友柏，丘大谋.200MW汽轮机高压缸中汽流激振对
轴系稳定性的影响[J]·动力工程，1994,14（1).2-6[7]李雪松，黄典贵·迷宫密封三维非定常流场及转子动特性数值
仿真[J]·机械工程学报，2003,39(4):136－140.[8]FLUENT INC·Fluent 6.2 Users Guide[M]·Lebanon:Centerra Re source Park, 2005.


(何静芳编辑)

数的喷嘴而达到同等的雾化水平。

## 参考文献：

[1] LEFEBVRE AH·Atomization and spray[M]· Hemisphere Publishing Corporation,1989.
[2]吴道洪·WDH型气泡雾化喷嘴的流量特性研究[J]·冶金能源，
1998,17(6):37-44.
[3]马玉峰·奥里乳化油蒸汽雾化机理及雾化蒸汽参数的选择[J]·
中国电力，1999,32(7)：70,76.
[4]仇性启，王宗明，王丽娟，等.气动旋流雾化原油喷嘴雾化特性
的实验研究[J]·石油机械，2001,29(2).5一7.[5]龚景松，傅维标.“旋转型气一液雾化喷嘴”流量特性的实验研
究[J]·热能动力工程，2004,19(4):376-379.[6]龚景松，傅维标.“旋转型气一液雾化喷嘴”的雾化角与流量分
布特性研究[J]·冶金能源，2004,23(1):44-47.

(何静芳编辑)

and Power Engineerinundrthe Xia JiaotongUversityXianChinaPost Code:10049)//Journalof Engieer ing for Thermal Energy &Power.— 2006, 21(6). -628~631

A method has been established for solving a full polarization electrochemical model for solid oxide fuel cells (SOFC) coupled with a potential equation and N-S one·A three-dimensional numerical simulation was conducted for the thermoelectric characteristics of the tubular SOFC. The calculated values of power generation characteristics of the cells obtained are in good agreement with the experimental ones· Meanwhile,the electric motive force distribution,electric current density and temperature distribution,electrochemical reactionproduced heat and Ohm heat distribution characteristics were also analyzed· The calculation results show that cathode Ohm polarization and activation polarization losses of the cells would account for 85%of thetotal losses,while chemical reactionproduced heat would account for about92% and Ohm heat for 8%of thetotal heatgenerated· Key words:tubular solidoxidefuelcll，numerical simulation,thermoelectric char acteristics 



旋转型气-液雾化喷嘴的雾化特性研究=A Studyof Atomization Characteristicsof “Swirling Gas-liquid Spray Atomizers"[刊,汉]/GONG Jing-song，FU Wei-biao(Engineering Mechanics Department，Tsinghua University，Beijing,China,Post Code:100084)//Journal of Engineering for Thermal Energy &Power.— 2006,21(6).-632~634,639



By using a laser-phase Doppler analyzer (PDA),an experimental study was conducted of the atomization characteristics of "Swirling Gas-liquid Spray Atomizers". Water was used as the liquid to be atomized instead of oil and compressed air employed as an atomization medium· The parameters of atomization characteristics under different operating conditions were measured, such as Sotyl mean diameter and particle speed of atomized droplet particles etc· The experimental mea−surement results indicate that the atomizer can achieve a comparatively good atomization state under the condition of a relatively small gas-liquid ratio with the average SMD of droplets at the center reaching 40 m· With an increase in pressure and gas-liquid ratio,the atomization level will be enhanced accordingly. However,it is scarcely affected by the structure of the atomizer· The research findings can provide an underlying basis for the practical design of atomizers· Key words:"Swirling Gas-liquid Spray Atomizers"，PDA (Phase Doppler Analyzer)，atomization characteristics 

迷宫密封转子动特性三维CFD 数值的研究=AStudyof MethodsUsed for Three-dimensionalCFD（Computational Fluid Dynamics) Numerical Analysis of Dynamic Characteristics of Rotors with Labyrinth Seals [刊,汉]/LIU Xiao-feng, LU Songyuan (Vibration Control and Information System Research Institute under the Southeast University，Nanjing,China,Post Code：210096)//Journal of Engineering for Thermal Energy y&.Power.— 2006, 21(6).635~639



The aerodynamic force produced by fluid in labyrinth seals is a major factor that may lead to instability of a shaft system ·This aerodynamic force can be described by a factor of seal dynamic characteristics· A vortex rotor-labyrinth seal three di mensional CFD (computational fluid dynamics) mathematical model was established· With a labyrinth seal at the inlet of a compressor serving as a specific case,the aerodynamic force at the rotor suface was calculated by using a general-purpose CFD software Fluent followed by a calculation of the seal dynamic characteristics factor· The calculated results when compared with those obtained by using another CFD software TASCflow and integrated-flow labyrinth seal calculation pro gram DYNLAB indicate that the accuracyof lossofstability calculation under the three-dimensional CFD method is higher than that obtained by using the integrated-flow method· Finally，the impact of such factors as pre-swirling speed at the seal inlet,variation in clearances and cone-shaped axial clearance of seals etc· on seal stability was also calculated and analyzed in detail,thus providing a theoretical basis for decreasing steam flow excitations in seals· Key words: labyrinth seal，computationalfluid dynamics,steamflowexcitation，rotordynamiccharacteristics factor 

低质量速垂直筒屏技术的愿理卤应用分析=Analysis of Working Principleand Applicationof Low Mass Flow-speed Vertical Tube-platen Technology[刊,汉]/LI Yan，ZHAO Xinmu，YUE Guangxi,etal(Thermal Energy 