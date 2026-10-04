

# ALSTOM超（超）临界汽轮机现场动平衡 方法研究 

何国安12，吴志强，康伟4，姜广政12，张卫军12，张学延1,2（1.西安热工研究院有限公司，陕西西安710054；2.西安西热节能技术有限公司，陕西西安710054；3.北方魏家煤电有限责任公司，内蒙古鄂尔多斯010308；4.华能云南滇东能源有限责任公司，云南昆明650214)

## [摘

要]基于大量现场动平衡试验数据，对ALSTOM技术生产的超（超）临界汽轮机采用的不对称高压转子、无支撑中压转子和单支撑低压转子的动平衡方法进行研究。研究结果表明：高压转子振型存在严重不正交问题，在动平衡计算中必须考虑振型干扰系数；中压转子可以依据临界转速区域1号和2号轴承处的振动峰值及相位关系，来识别一阶不平衡状况，在定速3000r/min运行时，可通过2号和3号轴承处的振动幅值和相位关系，来推断中压转子的一阶或二阶不平衡状况；低压转子无支撑侧可以借助相邻轴承的振动信息进行不平衡振型的识别与分解。


[关键词]汽轮机；振动；不平衡状况；转子；轴承

[中图分类号]TK268.+1[文献标识码]A[DOI编号]10.19666/j.rlfd.202206093

[引用本文格式]何国安，吴志强，康伟，等.ALSTOM超（超）临界汽轮机现场动平衡方法研究[J].热力发电，2022,51(12):106-111.HE Guoan, WU Zhiqiang, KANG Wei, et al. Research ondynamic balance of ALSTOM (ultra) supercritical turbine[J].Thermal Power Generation, 2022, 51(12): 106-111.



# Research on field dynamic balance of ALSTOM (ultra) supercritical turbine 

HE Guoan1,2, WU Zhiqiang3, KANG Wei4, JIANG Guangzheng1,2,

ZHANG Weijun1,2, ZHANG Xueyan 

(1.Xi'an Trmlowr RrcIntituteCo.d.XianCin;2.XiaTRIEngyCorvionTcologCo..Xia4,Cna 3.North Weijiamao Coal and Power Co.,Ltd. Ordos 010308,China; 4. Huaneng Yunnan Diandong Energy Co.,Ltd.,Kunming 650214, China)

Abstract: Based on large amounts of field dynamic balance test data, the dynamic balance methods of asymmetric high-pressure rotor, unsupported medium pressure rotor and single supported low-pressure rotor used in the supercritical or ultra supercritical turbine produced by ALSTOM technology are studied. The results show that,there is a serious non orthogonal problem in the vibration mode of high pressure rotor, and the interference coefficient of vibration mode must be considered in the dynamic balance calculation. The first-order unbalance condition of the intermediate pressure rotor can be identified according to the vibration peak value and phase relationship at the No.1 and No.2 bearings in critical speed region. At a constant speed of 3 000 r/min, the firstorder or second-order unbalance condition of the intermediate pressure rotor can be inferred from the vibration amplitude and phase relationship at the No.2 and No.3 bearings. The unsupported side of the low pressure rotor can identify and decompose the unbalanced vibration mode by using the vibration information of adjacent bearings.


Key words: steam turbine; vibration; unbalance condition; rotor; bearing 

目前，我国引进ALSTOM公司的技术生产的电厂累计投运了20余台；同时，采用ALSTOM技超（超）临界汽轮发电机组在平圩、贵溪、平凉等术对国内40多台大型汽轮发电机组进行了通流改

造，更换了除外缸以外的所有汽轮机部件[1]。因此，ALSTOM技术生产的汽轮发电机组在我国电力生产中具有较重要的地位。现场动平衡是汽轮发电机组检修中常见试验[2]，但现有的动平衡方法均针对双支撑、对称转子进行计算分析[3-8]，而对ALSTOM 超（超）临界汽轮机的无支撑、单支撑、不对称转子的动平衡技术却鲜有报道。文献[9]通过振动矢量和振型谐分量计算，对汽轮机整个轴系不平衡型式进行分析，并据此在多根转子、不同位置进行配重。这种方法给单支撑轴系动平衡提供了一种思路，但该方法计算工作量大，现场可操作性不强。文献[10]采用有限元方法对单支撑超超临界1000MW汽轮机不平衡响应进行理论计算，指出单支撑轴系各转子之间存在较强的振动耦合。



本文在上述工作的基础上，结合大量动平衡实践经验，对ALSTOM超（超）临界汽轮机不对称高压转子、无支撑中压转子、单支撑低压转子的现场动平衡问题进行分析研究，归纳出这些转子的动平衡技巧，为该型机组现场动平衡试验提供参考。

<div style="text-align: center;"><img src="imgs/img_in_image_box_163_767_1022_858.jpg" alt="Image" width="72%" /></div>


<div style="text-align: center;">图1ALSTOM超（超）临界机组轴系结构示意</div>


<div style="text-align: center;">Fig.1 Schematic diagram of the shaft system of the ALSTOM (ultra) supercritical steam turbine </div>


<div style="text-align: center;">表1ALSTOM超（超）临界汽轮发电机组转子临界转速</div>


单位：r/min 

<div style="text-align: center;">Tab.1 The critical speed of the rotor of ALSTOM (ultra) supercritical steam turbine generator unit </div>



<div style="text-align: center;"><html><body><table border="1"><tr><td>项目</td><td></td><td>高压转子</td><td>中压转子</td><td>低压1转子</td><td>低压2转子</td><td>发电机转子</td><td>励磁小轴</td></tr><tr><td>600MW等级</td><td>一阶</td><td>2 170</td><td>1 620</td><td>1 410</td><td>1470</td><td>660</td><td>>3 300</td></tr><tr><td>机组临界转速</td><td>二阶</td><td>>3 300</td><td>>3 300</td><td>>3 300</td><td>>3 300</td><td>1 930</td><td>>3 300</td></tr><tr><td>1 000MW等级</td><td>一阶</td><td>2 350</td><td>1 850</td><td>1 450</td><td>1 250</td><td>650</td><td>>3 300</td></tr><tr><td>机组临界转速</td><td>二阶</td><td>>3300</td><td>>3 300</td><td>>3300</td><td>>3 300</td><td>1 950</td><td>>3 300</td></tr></table></body></html></div>


<div style="text-align: center;">表2某660MW汽轮机通流改造前后的转子质量变化</div>


<div style="text-align: center;">Tab.2 Changes in rotor quality of a 660 MW steam turbine before and after flow path modification </div>



<div style="text-align: center;"><html><body><table border="1"><tr><td>转子名称</td><td>高中压转子</td><td>低压1转子</td><td>低压间短轴</td><td>低压2转子</td></tr><tr><td>通流改造前质量/kg</td><td>34496</td><td>77 999</td><td>4091</td><td>80 624</td></tr><tr><td>通流改造后质量/kg</td><td>27831</td><td>73 550</td><td>2394</td><td>75 710</td></tr><tr><td>通流改造前、后的质量变化率/%</td><td>-19.3</td><td>-5.7</td><td>-41.5</td><td>-6.1</td></tr></table></body></html></div>


不正交问题[11]。

## 2 高压转子平衡状况分析

### 2.1 振型的不正交特征

对于高、中压分缸机组而言，高压转子采用单流布置，其结构不对称，再加上轴承支撑刚度的差异，导致高压转子配重响应都存在不同程度的振型

## 1 轴系特征

ALSTOM超（超）临界机组轴系结构如图1所示。由图1可见，轴系由高压转子（HP）、中压转子（IP）、低压1转子（LP1）、低压2转子（LP2）、发电机转子（GEN）和励磁小轴（EXC）组成，各转子之间均采用刚性联轴器连接，其中高压转子采用单流、不对称设计：中压转子无支撑轴承：2根低压转子采用单支撑轴承；发电机和励磁小轴采用三支撑结构。整个轴系由7个轴承支撑，其中2号轴承为推力-支撑联合轴承，分别置于落地式的球墨铸铁轴承箱内。



表1为实测的该型汽轮发电机组转子临界转速。相较于其他同容量汽轮机，该型机组转子设计更轻，表2比较了ALSTOM公司对某国产660MW 汽轮机通流改造前后的转子质量，由表2可见，在同样跨距下，汽轮机总质量下降了9%左右。因此，该型机组轴系不平衡响应比其他同容量机组要大。

但与其他机组相比，ALSTOM超（超）临界汽轮机高压转子振型不正交问题尤为严重，其主要原因是中压转子无支撑，且与同容量机组相比，该型机组1号轴承设计最单薄，如：超超临界1000MW 汽轮机1号轴承（Φ200mm）仅为85kg左右，抗

扰动能力弱。这两方面都加剧了高压转子两端约束的不对称。



现以某660MW机组高压转子的振动响应为例来介绍其振型的不正交特征，具体如下：

1）图2为高压转子两端叶轮对称配重的响应实测结果。由图2可见，对称配重不仅对高压转子的同向振动分量（即一阶振型，下同）有显著影响，而且对反向振动分量（即二阶振型，下同）影响明显，特别是在3000r/min工况，反向振动分量的配重响应更为明显。



<div style="text-align: center;"><img src="imgs/img_in_chart_box_129_483_553_847.jpg" alt="Image" width="35%" /></div>


<div style="text-align: center;">图2高压转子对称配重的振动响应</div>


<div style="text-align: center;">Fig.2 Vibration response of HP rotor with symmetric weighting </div>


2）图3为高压转子两端叶轮反对称配重的响应实测结果。由图3可见，反对称配重不仅对高压转子的反向振动分量有显著影响，而且对同向振动分量影响明显，即反对称配重不能忽略对临界转速区域振动的影响。这在其他机型的高压转子上未出现类似特征。



<div style="text-align: center;"><img src="imgs/img_in_chart_box_132_1121_550_1455.jpg" alt="Image" width="35%" /></div>


<div style="text-align: center;">图3高压转子反对称配重的振动响应</div>


<div style="text-align: center;">Fig.3 Vibration response of HP rotor with antisymmetric weighting </div>


3）高压转子无论是对称配重还是反对称配重，其配重响应除了在其本身的一阶临界转速区域存在明显的振动峰值外，也会在中压转子一阶临界转速区域存在明显的振动峰值。



### 2.2 高压转子动平衡技巧及案例

ALSTOM超（超）临界汽轮机高压转子主要表现了3种振型：高压转子一、二阶振型和中压转子一阶振型。因此，对高压转子动平衡计算分析时，首先要确认1号和2号轴承在中压转子一阶临界转速区域振动相对平稳，以排除中压转子的一阶振型干扰；然后对高压转子一、二阶振型模态进行分析。在计算配重质量时，必须考虑振型干扰因素，即：

$$\binom{W_1}{W_2}=-\binom{\alpha_{11}\quad\alpha_{12}}{\alpha_{21}\quad\alpha_{22}}^{-1}\binom{A_0}{B_0}$$

式中：$W_{1}$ 、$W_{2}$ 分别为一、二阶平衡配重；$\alpha_{11}$ 为对称配重对临界转速下一阶振型的影响系数；$\alpha_{12}$ 为对.称配重对定速工况下二阶振型的影响系数；$\alpha_{21}$ 为反对称配重对临界转速下一阶振型的影响系数；$\alpha_{22}$ 为反对称配重对定速工况下二阶振型的影响系数；$A_{0}$ ,$B_{0}$ 分别为配重前临界转速下一阶振动分量和定速工况下二阶振动分量。



某ALSTOM超（超）临界1000MW机组高压转子振动偏大，其中1号轴振过临界转速区域的峰值达到230um左右，在3000r/min工况下振动达到130um左右（图4）。为此，决定对高压转子进行现场动平衡试验，具体过程如下：

1)1号和2号轴振过中压转子的临界转速区域较为平稳，说明不平衡质量在高压转子上；

2）考虑到该高压转子过临界转速区域峰值不稳定，且未达到振动保护限值，因此首次配重时，仅以校正3000r/min工况下二阶振型作为目标；

3）在高压转子1号和2号轴承侧反对称配重355g后，发现1号轴振过临界转速区域振动明显增大，最大峰值达到360um左右；

4）通过分析启停机过程的振动数据，发现反对称配重对一阶振型干扰较为明显，因此第2次配重计算中，就考虑了振型干扰系数，重新在2号轴承侧配重360g，就较好地校正了高压转子的一、二阶振型。



由于该机组是ALSTOM超(超)临界1000MW 高压转子首次现场配重，以往经验表明反对称配重对一阶振型影响甚微，因此，首次配重没有考虑反

对称配重对临界转速下一阶振型的干扰系数，造成首次配重效果不佳。



<div style="text-align: center;"><img src="imgs/img_in_chart_box_128_224_555_543.jpg" alt="Image" width="35%" /></div>


<div style="text-align: center;">图4某高压转子配重前后的振动波德图</div>


<div style="text-align: center;">Fig.4 Vibration BODE diagram of a HP rotor before and after weighting </div>


## 3 中压转子平衡状况分析

### 3.1 中压转子不平衡响应特征

ALSTOM超（超）临界汽轮机的中压转子没有支撑，也没有在该转子上设置任何振动测点，如何判断中压转子的平衡状况就成了疑难问题。

通过对该型机组多根中压转子动平衡试验的结果进行分析，发现其不平衡响应存在一定的共性特征。图5、图6分别为某ALSTOM超临界660 MW汽轮机的中压转子发生弯轴事故后的弯曲曲线及其振动响应情况。



<div style="text-align: center;"><img src="imgs/img_in_image_box_109_987_569_1106.jpg" alt="Image" width="38%" /></div>


<div style="text-align: center;">图5中压转子及其弯曲型线</div>


<div style="text-align: center;">Fig.5 The IP rotor and its bending curve </div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_129_1174_554_1530.jpg" alt="Image" width="35%" /></div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_631_150_1059_488.jpg" alt="Image" width="35%" /></div>


<div style="text-align: center;">图6某中压转子弯轴后的振幅和振动相位</div>


<div style="text-align: center;">Fig.6 The vibration amplitude and phase of the IP rotor after bending </div>


由图5、图6可以看出：

1）中压转子发生弯曲后，平衡状况恶化，引发了高压转子振动大幅增大，但低压转子振动变化不明显；

2）在中压转子临界转速区域（1650r/min附近)，1号和2号轴承处振动存在明显的振动峰值；

3)对高压转子而言，中压转子的不平衡属于跨外不平衡，因此，1号和2号轴承处振动在高压转子或中压转子的一阶临界转速区域的一倍频相位存在明显差别，这与高压转子本身的质量不平衡有显著区别。



### 3.2 中压转子动平衡技巧及案例

基于上述的不平衡响应特征，总结ALSTOM超（超）临界汽轮机中压转子的平衡状况，分析判据如下：

1）1号和2号轴振在中压临界转速区域存在明显的振动峰值，表明中压转子存在一阶不平衡；

2）当转速低于高压转子一阶临界转速时，1号和2号轴振相位差不小于60°，验证中压转子存在一阶不平衡；

3）在3000r/min工况下，2号和3号轴振呈现明显的同向或反向振动，也预示着中压转子存在一阶或二阶不平衡。



表3列出了某ALSTOM超临界660MW汽轮机1~3号轴承X方向轴振数据。基于以上不平衡判据分析及表3数据，该机组中压转子存在明显一阶质量不平衡。为此，利用停机机会，在中压转子两端末级叶轮上对称配重1380g。配重后发现，该配重显著降低了1~3号轴承处的振动幅值。

<div style="text-align: center;">表3某中压转子配重前后的振动基频幅值和相位</div>


单位：$\upmu\mathrm{m}\angle$ 

<div style="text-align: center;">Tab.3 The amplitude and phase of fundamental frequency vibration of the IP rotor before and after weighting </div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td>工况/(r-min-1)</td><td>1号轴振</td><td>2号X方向 轴振</td><td>3号X方向 轴振</td></tr></thead><tbody><tr><td rowspan="4">1 600 1 700 配重前</td><td>281∠274</td><td>93∠184</td><td>112∠301</td></tr><tr><td>305∠301</td><td>106∠216</td><td>109∠339</td></tr><tr><td>1 800</td><td>325∠342 102∠256</td><td>41∠353</td></tr><tr><td>3 000</td><td>68∠153 53∠314</td><td>84∠311</td></tr><tr><td rowspan="4">配重后</td><td>1 600 80∠271</td><td>36∠19</td><td>86∠321</td></tr><tr><td>1 700 98∠299</td><td>27∠356</td><td>82∠346</td></tr><tr><td>1 800</td><td>78∠334 41∠342</td><td>69∠354</td></tr><tr><td>3 000</td><td>28∠230 39∠61</td><td>58∠322</td></tr></tbody></table></body></html></div>


## 4 低压转子平衡状况分析

### 4.1 低压转子振型特征

ALSTOM超（超）临界汽轮机的低压转子属于单支撑，只能得到转子单侧的振动信息，该振动信息不能完全反映转子的振动特性。按照常规的振型分解方法，也得不到该转子的振型，这给低压转子的现场动平衡处理带来很大的困难。

为此，通过对该型机组多根低压转子反对称配重前后数据对比，发现低压转子的振型分析可以借助于相邻轴承的振动数据。现以某ALSTOM超（超）临界660MW汽轮机低压1号转子现场动平衡试验为例（图7），来说明低压转子两端末级叶轮上反对称配重后，在各转速下的不平衡响应特性，即：

<div style="text-align: center;"><img src="imgs/img_in_chart_box_126_973_556_1298.jpg" alt="Image" width="36%" /></div>


<div style="text-align: center;">图7低压1转子反对称配重的振动响应</div>


<div style="text-align: center;">Fig.7 The vibration response of LP1 rotor with antisymmetric weighting </div>


1）在低压转子一阶临界转速区域（1250~1450r/min），振动响应有1个峰值，转速超过2000r/min后，不平衡力偶的振动响应迅速增大，对2500r/min以上工况的振动产生较大影响。

2）在不平衡力偶作用下，两侧轴承在低转速下的振动相位相近，临界转速处相位变化明显，随着转速升高，两侧轴承振动相位呈现反向。

因此，对于单支撑转子振型判断，可以借助于相邻转子的振动数据，即低压1转子不平衡振型判断或分解可以采用3号和4号轴承处的振动数据；低压2转子不平衡振型判断或分解可以采用4号和5号轴承处的振动数据。



### 4.2 低压转子动平衡技巧及案例

基于上述低压转子振型特征，可以采用如下方法进行转子振型分解。



低压1转子一阶振型：

$$\phi_{\mathrm{L P1}}^{(1)}=\frac{A_{3}+A_{4}}{2}$$

低压1转子二阶振型：

$$\phi_{\mathrm{L P I}}^{(2)}=\frac{A_{3}-A_{4}}{2}$$

低压2转子一阶振型：

$$\phi_{\mathrm{LP}2}^{(1)}=\frac{A_4+A_5}{2}$$

低压2转子二阶振型：

$$\phi_{\mathrm{L P2}}^{(2)}=\frac{A_{4}-A_{5}}{2}$$

表4是该ALSTOM超（超）临界660MW汽轮机低压1转子现场动平衡试验前后数据。由表4可见：通过在两端末级叶轮上方向配重380g，有效降低了相关测点的振动幅值。



<div style="text-align: center;">表4某低压1转子配重前后的基频振动幅值和相位单位：m∠°</div>


<div style="text-align: center;">Tab.4 The amplitude and phase of fundamental frequency vibration of LP1 rotor before and after weighting </div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td>工况</td><td>测点</td><td>3号轴振</td><td>4号轴振</td><td>二阶分量</td></tr></thead><tbody><tr><td rowspan="2">配重前</td><td>X</td><td>135∠107</td><td>98∠243</td><td>108∠89</td></tr><tr><td>Y</td><td>52∠238</td><td>85∠334</td><td>52∠184</td></tr><tr><td rowspan="2">配重后</td><td>X</td><td>45∠110</td><td>48∠261</td><td>45∠95</td></tr><tr><td>Y</td><td>22∠223</td><td>35∠340</td><td>25∠184</td></tr></tbody></table></body></html></div>


## 5 结论

1）ALSTOM超（超）临界汽轮机高压转子结构不对称，存在严重的振型干扰，现场进行动平衡时，不仅要考虑对称配重对二阶振型的影响，还要考虑反对称配重对一阶振型的影响。

2）该型机组中压转子无支撑，本身没有振动测点，可以借助于1号和2号轴振过中压转子临界转速区域的振动幅值和相位来判断其一阶平衡状况；

在3000r/min时，可以借助2号和3号轴振相位关系来判断其一阶和二阶平衡状况。



3）该型机组低压转子属于单支撑，可以借助于相邻轴承的振动数据来识别转子振型。

## [参考文献]

[1]张学延，张卫军，何国安.火电厂旋转机械振动诊断及治理技术[M].北京：中国电力出版社，2019:1.ZHANG Xueyan, ZHANG Weijun, HE Guoan. Vibration diagnosisand treatment technology of rotating machinery in thermal powerplant[M]. Bejing: China Electric Power Press, 2019: 1.
[2]何国安，张学延，张卫军.汽轮发电机组轴系振动研
究进展及趋势[J].热力发电,2016,45(11):1-4.
HE Guoan, ZHANG Xueyan, ZHANG Weijun. Research status and development trends of turbo-generator shaft system vibration[J]. Thermal Power Generation, 2006,
45(11): 1-4.
[3]刘石，屈梁生．全息谱技术在轴系现场动平衡方法中
应用[J].热能动力工程，2009,24(1):24-30.
LIU Shi, QU Liangsheng. A study of methods for an onsite shafting dynamic balance based on holographic spectrum technology[J]. Journal of Engineering for Thermal Energy and Power, 2009, 24(1): 24-30.[4]施维新.轴系平衡一次加准法的研究及应用[J.中国
电力，2005,38(3):47-53.
SHI Weixin. Research and application of shifting balancing without trial weights[J]. Electric Power, 2005,
38(3): 47-53.
[5]何国安，常屹，张学延，等，大型汽轮发电机组轴系
预平衡方法的研究与应用[J].热力发电，2012,41(7):
92-100.
HE Guoan, CHANG Yi, ZHANG Xueyan, et al. Research and application of tubro-generator units shaft prebalancing method[J]. Thermal Power Generation,
2012, 41(7): 92-100.
[6]王浩．一次加准法在1000MW汽轮发电机组现场动

平衡中的应用[J.中国电力，2016,49(10):38-42.WANG Hao. Application of shaft dynamic balancing without trial weights to 1 000 MW turbo-generator set[J].Electric Power, 2016, 49(10): 38-42.
[7]柴岩，钟良，杨建刚.汽轮机低压缸轴承座振动分析
和动平衡试验研究[J].汽轮机技术,2017，59(1):50-52.
CHAI Yan, ZHONG Liang, YANG Jiangang. Bearing pedestal vibration analysis and balance test of a turbine low pressure rotor with bearing located on exhaust cylinder[J].Turbine Technology, 2017, 59(1): 50-52.[8]何国安，张世军，张学延．大型汽轮发电机组渐变式
弯曲转子的动平衡方法研究[J].汽轮机技术，2014，
56(6): 439-442.
HE Guoan, ZHANG Shijun, ZHANG Xueyan. Dynamic balance research on progressive bending rotor faults of large turbo-generator units[J]. Turbine Technology, 2014,
56(6): 439-442.
[9]应光耀，吴文健，蔡文方．单支撑轴系汽轮机多转子
联合平衡法[J].浙江电力，2017,36(1):50-53.
YING Guangyao, WU Wenjian, CAI Wenfang. Multiroto rintegrated balancing method of single-shafting steam turbines[J]. Zhejiang ElectricPower, 2017,36(1):50-53.[10]高庆水，邓小文，张楚，等.单支撑1000MW超超临
界汽轮机轴系不平衡响应分析[J].振动与冲击，2014，
33(14): 201-205.
GAO Qingshui, DENG Xiaowen, ZHANG Chu, et al.
Unbalance response of 1 000 MW ultra supercritical turbine with single bearing support[J]. Journal of Vibration and Shock, 2014, 33(14): 201-205.[11]何国安，闵昌发，张学延，等.国产 600MW汽轮发电
机组轴系动平衡研究[J].动力工程学报，2012,32(4):
282-288.
HE Guoan, MlN Changfa, ZHANG Xueyan, et al.
Dynamic balancing of theshaftsystemfor adomestic 600 MW turbo-generator set[J]. Journal of Power Engineering,2012,32(4):282-288

（责任编辑杜亚勤）