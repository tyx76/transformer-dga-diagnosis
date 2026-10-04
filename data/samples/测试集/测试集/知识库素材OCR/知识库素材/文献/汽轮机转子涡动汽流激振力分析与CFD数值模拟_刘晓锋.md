

文章编号：1001—2060（2007)03—0245—05

# 汽轮机转子涡动汽流激振力分析与CFD数值模拟

刘晓锋，陆颂元

（东南大学能源与环境学院，江苏南京210096)

摘要：汽轮机转子涡动时轴心偏离静子中心产生轴系失稳的Thomas/Alford汽流激振力，传统的叶顶间隙激振力公式对此不能全面准确评估。该文综合考虑转子涡动以及围带汽封二次流，在动叶通道，根据蒸汽做功分析涡动效应激振力；在叶顶围带汽封，用CFD数值模拟泄漏蒸汽三维粘性流场，确定蒸汽激振力。研究结果表明：小的静偏心和动偏心条件下，转子涡动动偏心在动叶通道诱发的激振力要大于静偏心激振力；围带汽封汽流预旋速度对间隙激振力有重要影响；调门不对称进汽也是蒸汽激振力的另一个重要来源。

关键词：汽轮机；顶隙激振：转子涡动；计算流体动力学中图分类号：TK263.6;0353.1文献标识码：A 

## 引言

20世纪50年代末，Thomas研究与汽轮机负荷相关的异常振动现象时，首先提出了叶顶间隙激振基本理论并给出激振力计算公式；1965年，Alford针对航空发动机振动稳定性从理论上进一步揭示了间隙激振机理。他们的研究表明，偏心转子叶顶间隙周向漏气量不均匀使得小间隙处汽流对动叶产生较大推力，大间隙处产生小推力，叶轮周向合力生成一个垂直于轴心位移，促使转子做非同步涡动的切向激振力，Thomas/Alford(T/A)模型给出了力的表达式：

$$K_{r^{\theta}}=\frac{F_{\theta}}{e}=\frac{T^{\beta}}{D H}$$

式中：$F_{\theta}$ 一切向汽流激振力；e一转子静偏心；T一叶轮扭矩；D一叶片节圆直径；效率系数$\beta_{-}$ 一单位顶隙变化对做功效率的影响，通常取1~2。需要注意地是，式(1)无法计入实际转子，都是在做同步或异步的正向或反向涡动；而且，式中的$\upbeta$ 是人为确定的经验系数。



1993年，Ehrich利用并行压缩机模型提出了2SPC模型$[1]$ ，计算轴流压缩机的$\upbeta;$ 2003年，丁学俊利用级效率变化半经验公式，推导含有叶栅参数和流动参数的$\upbeta$ 计算式[2]。这些模型和公式解决了β选取的困难，但均没有计入转子涡动动偏心。

Song等人1997年提出了包括叶片比例和径向比例模型的叶顶间隙激振力模型[3]；2002年，柴山等人基于均匀流场假设，确定汽流密度随叶顶间隙变化关系，导出直叶片和扭叶片激振力计算式[4];这些模型不能分析围带汽封流体激振力。2006年，刘晓锋等人应用三维CFD 计算了与围带密封类似的静子齿迷宫密封激振力和动特性[5]。试验方面，早在1977年，Urlichs在雷诺数小于$10^{5}$ 条件下，实测围带切向力，发现它是转子涡动的重要激振源[6]。

汽轮机转子中心相对静子中心的静偏心和动偏心都会产生叶顶间隙激振力。近年，Moor应用三维CFD 分析离心水泵零静偏心涡动转子围带和主流道的激振力[7];Spakavsrky提出ISPC叶顶间隙激振模型，研究了轴流压缩机涡动转子激振力[8]。

本文以汽轮机涡动转子为研究对象，在动叶流道，根据蒸汽做功分析动偏心激振力；围带汽封处采用CFD模拟涡动转子泄漏蒸汽二次流的三维粘性流场，确定汽流激振力。



## 1 叶轮涡动产生的蒸汽激振力计算式

根据汽轮机原理，蒸汽作用在某级动叶栅第i 个动叶片上的轮周力为：

$$f_{u}^{i}=q^{i}\left(w_{1}\cos\beta_{1}+w_{2}\cos\beta_{2}\right)$$

式中：$g^{i}{\overline{{\phantom{g^{i}g^{i}}}}}$ 单位时间通过动叶片i流道的蒸汽量；$w^{-}$ 蒸汽相对速度；$\beta_{i}-$ 叶轮旋转平面与相对汽流I 

速度夹角。下标1是动叶进口，2为出口。由于叶顶漏气$\Delta_{g}{}^{i}$ ，动叶i流道实际通过蒸汽量为：

$$g_{\mathrm{b}}^{i}=g^{i}-\Delta g_{\mathrm{t}}^{i}$$

$$\Delta_{g_{t}}^{i}=0.6\delta_{t}^{i}\sqrt{\frac{\Omega_{t}}{1-\Omega_{m}}}\frac{v_{1t}\left(d_{b}+l_{b}\right)}{d_{n}\ln\sin\alpha_{l}}g^{i}$$

上式中当量间隙$\eth_{t}^{i}$ 为：

$$\delta_{t}^{i}=\delta_{z}/\sqrt{1+z_{r}\left(\frac{\delta_{z}}{\delta_{r}^{i}}\right)^{2}}$$

式(4)中：$d^{-}$ 叶栅节圆直径；l一叶栅高度。下标：b一动叶栅；n一静叶栅；$v_{\mathrm{t}}$ 一蒸汽比容；$\Omega_{\mathrm{t}}$ 一动叶顶部反动度；$\Omega_{\mathrm{{_m}}}$ 一级的反动度。式(5)中：$\eth_{z}$ 一开式轴向间隙：$z_{\mathrm{r}}-$ 叶顶径向汽封齿数。



图1示出叶顶间隙几何关系，静子中心$0_{2}$ ，以轴心静态位置$\mathbf{O}(x_{^{0}},y_{^{0}})$ 为原点建立坐标系，轴心$0\mathrm{{i}}$ 围绕O涡动时在X、Y轴的振动位移分别为x和$y$ ,由几何关系得到动叶i的叶顶间隙$\eth_{r}^{i}$ .

<div style="text-align: center;"><img src="imgs/img_in_image_box_121_364_347_541.jpg" alt="Image" width="22%" /></div>


<div style="text-align: center;">图1转子叶顶间隙几何示意图</div>


考虑转子零静偏心的特例，转子围绕静子中心O涡动(见图2)，涡动半径与X轴夹角$\alpha=270^{\circ}$ 时，x 中国知网，xpw.表k中系数便可简

$$\delta_{r}^{i}=\sqrt{R^{2}-\left[\left(y+y_{0}\right)\cos\theta^{i}-\left(x+x_{0}\right)\sin\theta^{i}\right]^{2}}$$

$$\left[(y+y_0)\sin\theta^{\prime}+(x+x_0)\cos\theta^{\prime}\right]-r $$

式中：$R^{\mathrm{ 一 }}$ 静子半径；$r^{-}$ 叶顶围带半径；$\theta 一叶$ 片i 与X轴夹角。



设转子小轨迹圆涡动，轮周力与转子位移、速度呈线性关系，取涡动半径$r_{0}$ 、涡动速度$\Omega$ ，在0点将轮周力按一阶Talor级数展开，得到：

$f_{u}^{i}=f_{u}^{i}\left|_{0}+\frac{\partial f_{u}^{i}}{\partial x}\right|_{0}+\frac{\partial f_{u}^{i}}{\partial y}\left|_{0}+\frac{\partial f_{u}^{i}}{\partial x}\right|_{0}+\frac{\partial f_{u}^{i}}{\partial y}\left|_{0}+\frac{\partial f_{u}^{i}}{\partial y}\right|_{0}$ (7)式中$f_{u}^{i}=(1-c_{1}c_{2})c_{3}g_{b}^{i}$ 一静态力，与转子静偏心有关；$\frac{\partial f_{u}^{i}}{\partial u}\left|_{0}=c_{1}c_{3}c_{4}c_{5}g_{b}^{i},\frac{\partial f_{u}^{i}}{\partial y}\right|_{0}=c_{1}c_{3}c_{5}c_{6}g_{b}^{i}$ 一决定动态力的刚度系数；$\frac{\partial f_{u}^{i}}{\partial\dot{x}}\mid_{0}=\frac{1}{\Omega}c_{1}c_{3}c_{5}c_{6}g_{b}^{i}\cdot\frac{\partial f_{u}^{i}}{\partial\dot{x}}\mid_{0}=\frac{1}{\Omega}$ $c_{1}c_{3}c_{4}c_{5}g_{b}^{i}$ 一决定动态力的阻尼系数。式$(7)$ 能够同时计入转子静偏心和涡动动偏心计算激振力，各系数$C_{i}$ 列于表1。



<div style="text-align: center;">表1动叶通道内蒸汽激振力求解系数</div>



<div style="text-align: center;"><html><body><table border="1"><tr><td>系数 静平衡位置 $(x_{0},y_{0})$</td><td>系数 静平衡位置(0.0)</td></tr><tr><td>δ $0.6\ \sqrt{\frac{\Omega_{t}}{1-\Omega_{m}}}\frac{v_{1t}}{v_{2t}}\frac{(d_{b}+l_{b})}{d_{n}\sin\alpha_{1}}$ $C_{1}$ $\sqrt{1+z_{r}\left[\delta_{z}/\sqrt{R^{2}-\left(y_{0}\cos\theta^{i}-x_{0}\sin\theta^{i}\right)^{2}-\left(y_{0}\sin\theta^{i}+x_{0}\cos\theta^{i}\right)-r}\right]^{2}}$ $C_{2}$ $C_{3}$ $w_{1}\mathrm{c o s}\beta_{1}+w_{2}\mathrm{c o s}\beta_{2}$</td><td>$\frac{\delta_{z}}{\sqrt{1+z_{r}\left(\delta_{z}/c_{r}\right)^{2}}}$ $0.6\ \sqrt{\frac{\Omega_{t}}{1-\Omega_{m}}}\frac{v_{1t}}{v_{2t}}\frac{(d_{b}+l_{b})}{d_{n}\sin\alpha_{l}}$ $C_{1}^{()}$ $C_{2}^{0}$</td></tr><tr><td>$C_{4}$ $\frac{d_{0}\sin\theta^{i}}{\sqrt{R^{2}-d_{0}^{2}}}-\cos\theta, 其中 d_{0}=y_{0}\cos\theta^{i}-x_{0}\sin\theta^{i}$</td><td>$w_{1}\mathrm{c o s}\beta_{1}+w_{2}\mathrm{c o s}\beta_{2}$ $C_{3}^{0}$</td></tr><tr><td></td><td>C0 $-\cos\theta^{i}$ $C_{4}^{0}$</td></tr><tr><td>$\frac{\partial_{\mathcal{Z}_{r}}^{3}}{\left[\sqrt{\left(\partial_{r}^{i}\right)^{2}+z_{r}\partial_{z}^{2}}\right]^{3}},\quad\bar{\partial}_{r}^{i}=\sqrt{R^{2}-\left(y_{0}\cos\theta^{i}-x_{0}\sin\theta^{i}\right)^{2}-\left(y_{0}\sin\theta^{i}+x_{0}\cos\theta^{i}\right)-r}$ $C_{5}$ $C_{6}$ $\frac{d_{0}\cos\theta^{i}}{\sqrt{R^{2}-d_{0}^{2}}}-\sin\theta, 其中 d_{0}=y_{0}\cos\theta^{i}-x_{0}\sin\theta^{i}$</td><td>C0 $\frac{\eth_{z_{r}}^{3}}{\left(\sqrt{c_{r}^{2}+z_{r}\eth_{z}^{2}}\right)^{3}}$ $-\sin\theta^{i}$</td></tr></table></body></html></div>


化为$C_{i}^{()}$ ，则动叶i上的轮周力为：

<div style="text-align: center;"><img src="imgs/img_in_image_box_141_1098_347_1274.jpg" alt="Image" width="20%" /></div>


<div style="text-align: center;">图2转子围绕静子中心涡动</div>


$$f_{u}^{i}=\left[\left(1-c_{1}^{0}c_{2}^{0}\right)c_{3}^{0}-2c_{1}^{0}c_{3}^{0}c_{5}^{0}c_{6}^{0}r_{0}\right]q_{b}^{i}$$

将轮周力沿涡动轨迹切向和径向分解，并求该级全部动叶的切向和径向合力，得到由于转子涡动偏心导致的蒸汽做功不均在这级动叶产生的总切向激振力$F_{t}$ 和径向激振力$F_{r}$ (cid)



$$\begin{aligned}F_{t}=\sum-\sin\theta f_{u}^{i}=\sum-\sin\theta f_{u}^{i}\left[\left(1-c_{1}^{0}c_{2}^{0}\right)\times\right.\\\left.c_{3}^{0}-2c_{1}^{0}c_{3}^{0}c_{5}^{0}c_{6}^{0}r_{0}\right]q_{b}^{i}\\F_{r}=\sum-\cos\theta f_{u}^{i}=\sum-\cos\theta f_{u}^{i}\left[\left(1-c_{1}^{0}c_{2}^{0}\right)\times\right.\\\left.c_{3}^{0}-2c_{1}^{0}c_{3}^{0}c_{5}^{0}c_{6}^{0}r_{0}\right]q_{b}^{i}\end{aligned}$$

式(9)和式(10)是根据蒸汽作用在动叶上的轮周力推导的，动叶几何参数和蒸汽参数确定后，动叶

轮周力由实际通过动叶流道汽量决定，式(9)和式(10)反映了转子涡动动偏心导致叶顶漏气不均产生的激振力，但尚未计入涡动转速对激振力的影响。

## 2 叶顶围带汽流激振力CFD 分析

对涡动转子围带密封蒸汽流造成的激振力用CFD进行了计算分析。为消除因计算域随时间变化在控制方程中产生的时间项，在与转子固连旋转坐标系中求解，把非定常问题转化为定常。

取图2的圆形涡动轨迹，静止坐标系中，蒸汽在围带密封中流动的通用控制方程：

$$d\dot{w}(\theta U^{\phi})=d\dot{w}(\Gamma_{\theta}qrad^{\phi})+S_{\phi}$$

式中：$\varrho-$ 流体密度;$U^{-}$ 流体速度矢量;通用变量φ代表速度u，v，w，$T$ ，k和ε等求解变量；$\Gamma_{\upphi}\mathrm{ 一广 }$ 义扩散系数；$S_{\phi} 一广$ 义源项。



旋转坐标系中的流体相对速度$\rightharpoondown$ 与绝对速度$\overset{\rightharpoonup}{\Omega}$ 有关系：

$$\vec{v}_{r}=\vec{v}-(\vec{\Omega}\times\vec{r})$$

式中：$\overset{\rightharpoonup}{\Omega}$ 一坐标系角速度；$\overset{\rightharpoonup}{r} 二$ 计算节点在旋转坐标系的位置向量。近壁面蒸汽流动采用壁面函数法处理。叶顶围带和密封壁面处流体无相对滑移，流动绝热。旋转系中，围带壁面绕轴心相对转速是$\stackrel{\rightharpoonup}{\underset{w}{}}-\stackrel{\rightharpoonup}{\underset{\Omega}{}}$ ,密封壁面相对旋转坐标系速度$-\underset{\Omega}{\rightleftharpoons}$ 。计算得密封压力场后，积分表面压力便得到激振力$F_{r}$ 和$F_{t}$ 。

## 3 计算实例

汽轮机高压转子段蒸汽参数高，同时由于转子偏心、部分进汽等原因，易于产生强汽流激振力出现振动失稳。本文计算了某330MW汽轮机额定工况和调门全开VWO工况调节级蒸汽激振力。图3为调节级示意图，计算的汽流激振力包括：（1）零静偏心转子圆涡动时动叶通道内蒸汽激振力；（2）叶顶围带汽封汽流激振力。



<div style="text-align: center;"><img src="imgs/img_in_image_box_119_1275_369_1412.jpg" alt="Image" width="24%" /></div>


<div style="text-align: center;">中国知网图tpS调节级杀意图.net </div>


实际汽流激振力是非定常的。计算中简化转子做圆轨迹涡动，轴心在涡动轨迹的任意位置时，转子与汽流的相互作用相同，因此激振力大小不变，但转子的切向和径向激振力的合力方向发生变化。

### 3.1 叶轮涡动蒸汽激振力计算

330MW汽机高调门由4组喷嘴配汽，每组汽道数37，喷嘴组序号如图4所示。调节级动静叶几何参数列于表2，叶顶间隙$C r$ 为1.5mm，轴向间隙$\eth_{\mathrm{z}}$ 为6mm;表3列出额定工况和VWO工况调节级运行参数。该高中压转子重20.22t。



<div style="text-align: center;"><img src="imgs/img_in_image_box_671_423_811_547.jpg" alt="Image" width="13%" /></div>


<div style="text-align: center;">图4调节级喷嘴布置</div>


<div style="text-align: center;">表2调节级动、静叶几何参数</div>



<div style="text-align: center;"><html><body><table border="1"><tr><td>出口角/(°)</td><td>叶片数/只</td><td>叶高/mm</td><td>出口面积/cm²</td></tr><tr><td>喷嘴 15.55</td><td>148</td><td>35</td><td>271.48</td></tr><tr><td>动叶 23.00</td><td>57</td><td>38</td><td>430.59</td></tr></table></body></html></div>


<div style="text-align: center;">表3额定工况和VWO 工况调节级的运行参数</div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td></td><td>额定工况</td><td>VWO工况</td></tr></thead><tbody><tr><td>流量 $/\mathrm{kg}\mathrm{\bullet h}^{-1}$</td><td>982 871</td><td>109 572</td></tr><tr><td>级前压力 $\mathrm{{}^{\mathrm{{/}}}M P a}$</td><td>16</td><td>16</td></tr><tr><td>级前温度/℃</td><td>538</td><td>538</td></tr><tr><td>级后压力 $\mathrm{{}^{\mathrm{/}}M P a}$</td><td>11.752</td><td>13.162</td></tr><tr><td>级后温度/℃</td><td>489.2</td><td>505.5</td></tr><tr><td>绝热焓降/kJ $\bullet\mathrm{k g}^{-1}$</td><td>99.01</td><td>42.16</td></tr><tr><td>级反动度/%</td><td>0.1</td><td>0.1</td></tr><tr><td colspan="3">调门状态 I、Ⅱ、Ⅲ全开，Ⅳ关IIⅡⅢ、全开</td></tr></tbody></table></body></html></div>


#### 3.1.1 VWO工况叶轮涡动激振力

VWO时调门全开，取涡动半径为$C r$ 的10%，根据式(9)和式(10)算得激振力切向和径向分量：$F_{t}=$ $-1144.73\;N;F_{r}=-811.75\;N$ ,其中$F_{t}$ 与涡动同向，加剧原有涡动(见图2)；$F_{r}$ 与偏心同向，加大转子振幅；合激振力与转子自重比为0.71%。

同样在VWO工况，若忽略转子涡动，只考虑$10\%C r$ 的静偏心影响，根据$T/A$ 公式，单纯由静偏心产生的$F_{t}=-400.8$ N，仅为转子总重0.2%，远小于动偏心激振力。需要注意式(9)和式(10)是在

转子小轨迹涡动条件下得到的，因此以上结论仅适于小的静、动偏心。当静偏心增大到与Cr相等，$T^{/}$ A力迅速增加到4008N，这时主要考虑静偏心产生的激振力。涡动转子动偏心激振力可以通过优化叶片几何参数，如静、动叶汽流出口角等来减小。

#### 3.1.2 额定工况叶轮涡动激振力

额定工况时I、Ⅱ、Ⅲ号调门全开，Ⅳ号调门关闭，28.84%的部分进汽度导致不平衡蒸汽力。设转子零静偏心圆涡动，涡动半径为$C r$ 的10%，由式(9)和式(10)得到：$F_{t}=-33\ 117.11\ N,\ F_{r}=-33$ 672.98N，与VWO工况比，$F_{t}$ 增大了30倍，$F_{r}$ 增大了46倍；合力与转子自重比为23.4%。

必须注意此时激振力的剧增是因为部分进气产生的大不平衡蒸汽力，转子动偏心的作用较小，额定工况时即使动偏心为零，这一不对称蒸汽力依然存在。式(9)和式(10)能计算动偏心在动叶流道内诱发的蒸汽激振力，同时也可计算部分进汽产生的不平衡蒸汽力。当IV号调门关闭使IⅣ喷嘴组后14个动叶不受蒸汽力作用，式(9)和式(10)计算的是I、ⅡI和ⅢI喷嘴组后动叶激振力，IⅡ号调门受力平衡，Ⅲ号调门受力无法抵消，故产生了大不平衡力。

### 3.2 叶顶围带激振力

与动压滑动轴承的油膜类似，密封中汽膜的交叉刚度k是促使转子做低频涡动的激振力来源，直接阻尼D可以生成对这种低频涡动的抑制力。

本文利用CFD/Fluent计算了高压调节级围带汽封中蒸汽流场，确定汽流激振力和密封动特性。叶顶围带和密封的几何参数如图5所示，汽封为尖形静子直齿，密封工作条件列于表4。围带中的汽膜是连续的，此时不考虑部分进汽的影响。

<div style="text-align: center;"><img src="imgs/img_in_image_box_110_1064_375_1229.jpg" alt="Image" width="26%" /></div>


<div style="text-align: center;">图5调节级叶顶围带汽封</div>


<div style="text-align: center;">表4叶顶围带密封工作条件</div>



<div style="text-align: center;"><html><body><table border="1"><tr><td>入口压力 /MPa</td><td>入口温度 /℃</td><td>出口压力 /MPa</td><td>出口温度 /℃</td></tr><tr><td>额定工况 12.176 8</td><td>495</td><td>11.752</td><td>489.2</td></tr><tr><td>中国知网3.44</td><td>$\frac{1}{2}\times\frac{1}{2}=\frac{1}{2}\times\frac{1}{2}\times\frac{1}{2}=\frac{1}{2}$</td><td></td><td>505.5</td></tr></table></body></html></div>


首先采用二维轴对称模型计算围带汽封漏汽量和汽封入口处蒸汽紊流状态和预旋速度，模化时增加了密封入口上游区，共4411个节点(见图6)，近壁面处节点间距离比1.1。图7是叶顶围带表面静压轴向分布计算结果。



<div style="text-align: center;"><img src="imgs/img_in_image_box_621_266_880_377.jpg" alt="Image" width="25%" /></div>


<div style="text-align: center;">图6二维轴对称计算网格</div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_595_496_878_666.jpg" alt="Image" width="28%" /></div>


<div style="text-align: center;">图7叶顶围带轴向压力分布(额定工况)</div>


表5给出计算得到的围带汽封漏汽量和汽封入□湍动能、耗散率以及预旋速度，显示汽封入口具有很高的正向预旋速度，这对激振力会产生重要影响。

<div style="text-align: center;">表5漏汽量、密封入口紊流条件和预旋速度</div>



<div style="text-align: center;"><html><body><table border="1"><tr><td></td><td>泄漏量 $/\mathrm{k q}\bullet\mathrm{s}^{-1}$</td><td>入口 $/\mathrm{m}^{2}\bullet\mathrm{s}^{-2}$</td><td>入口E $/\mathrm{m}^{2}\bullet\mathrm{s}^{-3}$</td><td>入口预旋 $\mathbf{m\bullet}\mathbf{s}^{-1}$</td></tr><tr><td>额定工况</td><td>2.742</td><td>275.9056</td><td>1 506 105</td><td>271.2</td></tr><tr><td>VWO工况</td><td>3.075</td><td>61.028 8</td><td>147 256</td><td>227.8</td></tr></table></body></html></div>


调节级围带密封激振力计算采用三维模型，模化时将围带壁面沿Y轴负向平移，在偏心状态下生成三维网格，周向网格数100,总节点374100。

<div style="text-align: center;"><img src="imgs/img_in_chart_box_610_1174_881_1379.jpg" alt="Image" width="27%" /></div>


<div style="text-align: center;">图8围带汽封切向和径向力随涡动转速变化</div>


在旋转坐标系中求解三维流场，再积分围带壁面压力得总激振力。Chlids在实验和理论研究中发现转子小轨迹涡动时（一般涡动半径为间隙的10%以内)激振力与涡动转速承线性关系。本文计算

$\Omega=0$ 

速的线性曲线(见图8)。



零静偏心转子圆涡动的切向和径向激振力与汽膜的刚度、阻尼存在下列关系[5]



$$\begin{aligned}&F_{r}/e^{=-(K+d\Omega)}\\&F_{t}/e^{=-K-D\Omega}\\ \end{aligned}$$

将$\Omega=0$ 和0.5ω时的气动力带入上两式解得动特性系数，其计算结果见表6。



<div style="text-align: center;">表6围带汽封动特性系数计算结果</div>



<div style="text-align: center;"><html><body><table border="1"><tr><td>直接刚度 $/\mathrm{{N}}\mathrm{{\bullet}m}^{-1}$</td><td>交叉刚度 $/\mathrm{{N}}\mathrm{{\bullet}m}^{-1}$</td><td>直接阻尼 $/\mathrm{Ns}\mathrm{\bullet m}^{-1}$</td><td>交叉阻尼 $/\mathrm{Ns}\mathrm{\bullet m}^{-1}$</td></tr><tr><td>额定工况 $4.51\times10^{5}$</td><td>$-9.55\times10^{6}$</td><td>$5.14\times10^{2}$</td><td>$7.05\times10^{3}$</td></tr><tr><td>VWO工况 $4.83\times10^{5}$</td><td>$-9.85\times10^{6}$</td><td>$9.25\times10^{2}$</td><td>-- $1.60\times10^{3}$</td></tr></table></body></html></div>


由于围带密封入口蒸汽预旋速度高，算得的刚度、阻尼数量级较大，交叉刚度达到$10^{6}$ ，这对轴系稳定性有显著影响。因此，高中压转子动特性计算分析时，应计入围带汽封激振力才能得到轴系稳定性全面正确的结果。



## 4 结论

建立了汽轮机转子涡动状态下叶顶间隙激振力的计算模型，包括动叶流道内蒸汽做功不均的激振

高效电力生产

力和围带汽封蒸汽激振力。

计算表明：小静偏心和动偏心情况时，涡动动偏心激振力大于静偏心激振力，传统的激振力计算式忽略了这一重要力源；汽轮机顺序阀进汽时的不平衡力导致圆轨迹涡动转子激振力远大于单阀进汽的激振力；计算分析还表明：叶顶围带汽封中高预旋速度的蒸汽流能够产生强激振力，汽膜交叉刚度数量级达到$10^{6}$ ，对轴系稳定性有重要影响。

## 参考文献：

[1]EHRICHFF·Rotowhrlforcesinducedbythetipclaanceeffectin axial flow compressor[J].J Vibr Acoust,193,115.509—515.[2]丁学俊·Alford力中效率系数的一种计算方法[J]·华中科技大学学报（自然科学版）,2003,31(4)：66-68.
[3]SONG S J,MARTINEZ SANCHEZ M·Rotordynamic forces due to tur bine tip leakage :Part Iblade scale effects[J] ·ASME Journal of Tur bomachinery,1997,119,695—703.
[4]柴山，张耀明，曲庆文·汽轮机间隙激振力分析[门J]·中国工程
科学，2001,3(4):68-72.
[5]刘晓锋，陆颂元·迷宫密封转子动特性三维CFD数值分析方法
研究[J]·热能动力工程，2006,21(6):641－645.[6]ULRICH'S K·Leakage flow in thermal turbo machines as the origin of vibration-exciting lateral forces[R].NASA TT F—17409,1977.[7]MOORE JJ·Rotordynamic force prediction of whirling centrifugalim peller shroudpassaqes usinq computational fluid dynamic techniques [J]·Journalof Engineering for Gas Turbines and Power,2001,123,910-918.
[8] SPAKOVSZKY Z S·Analysis of aerodynamically induced whirling forces in axial flow compressors[J]·Journal of Turbomachinery. 200,122.
761-768.
[9]DARA CHILDS-Turbomachinery rotordynamics:phenomena,modeling,
andanalysis[M]New York:Wiley,1993.


(编辑辉)

## 美国首台7H联合循环装置将投入使用

据《Gas Turbine World》2006年9～10月号报道，在工厂试验完成以后，GE Enerqy把两台7H燃气轮机中的第一台发运到加利福尼亚洲里弗赛德市附近的Inland Empire EnergyCenter，用于安装并进行现场试验。

电站具有两个联合循环装置，预期在2008年夏季开始运行。

以天然气作为燃料，每台S107H联合循环装置的净输出功率为400MW，热耗率为6003kJ/(kWh)（热效率为60%)。



单轴联合循环装置由一台7H燃气轮机、一台不补燃的余热锅炉、一台三压再热汽轮机和一台具有氢冷转承国知的发电机成ww.cnki.net 



（吉桂明供稿）

conditions of heat transfer and mechanics theory have been automatically generated based on the historical operating data and structural geometric parameters· A mesh dissection was conducted of a geometric model by using a Delaunay non structural automatic dissection algorithm· The load spectrum treatment and damage build-up were seamlessly inserted into a finite-element analysis process· On this basis,fomed was an integrated system of rotor service-life evaluation based on a complicated numerical method· The above system can provide such functions as the analysis of rotor steady-state and transient temperature, stress and strain fields as well as the evaluation of rotor damage and service life,thus visually displaying the distribution of rotor damaqe fields and their evolution, and at the same time overcoming some technically in tractable hindrances specific to traditional methods· Key words:steam turbine rotor,finite element,service life evalua tion，fatigue 



汽轮机转子涡动汽流激振力分析与CFD 数值模拟 AnalysisandCFD（ComputationalFluidDynamics）Numerical Simulation of Steam Flow Excitation Force Leading to a Whirling of Steam Turbine Rotors [刊,汉]/LIU Xiao-feng,LU Song yuan (College of Energy Source and Environment under Southeast University，Nanjing,China,Post Code: 210096)//Journalof Engineering for Thermal Energy &Power.— 2007,22(3).—245~249

During the whirling of a steam turbine rotor，its shaft center will deviate from that of the stator，thus producing a Thomas/Alford steam-flow excitation force leading to a loss of stability due to vibrations·In such a case,however,the calculation formula of a traditional bladetip clearance excitation force can not provide an overall and a correct evaluation of the above force·With the whirlingof the rotor and the secondary flow around the blade shroud being comprehensively taken into account in rotating blade passages,the whirling-caused excitation force was analyzed based on the work done by the steam· In the gland seal of the blade tip shroud,CFD values were used to simulate a three-dimensional viscous flow field of the leaking steam,thus determining the magnitude of the steam excitation force·The research results show that under the condition of a small static and dynamic eccentricity,the excitation force in the rotating blade passages in duced bythe dynamic eccentricityof therotor whirlingis greaterthanthatinduced by the static ecentricityandthe pre swirling velocity of steam flows in the shroud gland has an important influence on the excitation force in the clearance.The non-symmetric steam admission is another important source of the steam excitation force· Key words: steam turbine,tip clearance excitation vibration, eddy whirling of rotor,computational fluid dynamics (CFD)

刷式密封泄漏流动特性影响因素的研究A Studyof the Influenceof Brush-type Seals on Leaking Steam Flow Characteristics [刊,汉]/LI Jun,YAN Xin,FENG Zhen-ping (Research Institute of Turbo-machinery under Xi'an Jiao tong University，Xian，China，Post Code:71049)//Journalof Engineeringfor Thermal Energy&Power—207,22(3).-250~254



By employing techniques for seeking a solution to Reynolds-Averaged Navier Stokes equation based on an improved Dar cian porous medium model, a numerical analysis and study has been conducted of the law governing the influence of pres−sure ratio and bristle pack thickness on the leakinq steam flow characteristics of brush type seals under the condition of a given radial clearance· Based onthe test data published for leaking steamflow ratesof brush type seals,determined was the permeability coefficient of the porous medium of the bristle pack· By using the permeability coefficient of the bristle−pack porous medium thus obtained,calculated respectively were the leaking steam flow rates and flow patterns of brush type seals at theendsof a shaftundertheconditionof7pressure ratios and5kindsof bristle pack thickness at a given radial clearance· The calculation results indicate that both the pressure ratio and bristle pack thickness can influence the leaking steam flow rate of a brush type seal· Under the condition of a given pressure ratio,the leaking steam flow rate will decrease with an increase of bristle pack thickness· At a given bristle pack thickness,the leakinq steam flow rate will incirs:wwuiAs the leakingsteamflowrateof a brush typesealassumes approximately linear variation relationship with the pressure ratio and bristle pack thickness,the impact of the latter two items on the 