

# ICA在汽轮机组动静碰磨故障诊断中的应用研究

蔡文方，陆颂元，吴文健，应光耀

(1国网浙江省电力公司电力科学研究院，杭州310014；2东南大学能源与环境学院，南京210096)

摘要:针对旋转机械振动监测和故障诊断面临的噪声干扰和多信号混杂问题,将独立分量分析法(Independent ComponentAnalysis，简称ICA)应用到汽轮发电机组振动信号分离上，该方法可将传感器所测的混合信号分离成相互独立的单个源信号，实现对故障源的准确识别，提高故障诊断精度。对多源信号混合－分离的仿真实验，成功验证了ICA法分离混合信号的有效性。采用ICA法对某台实际机组碰磨的轴振信号进行分离，结果从机组的碰磨信号中成功分离出了代表故障的周期性冲击信号，显示出ICA法对碰磨产生的冲击信号的分离效果，实现了对碰磨故障的诊断。


关键词：汽轮发电机组振动；独立分量分析；动静碰磨；故障诊断；旋转机械

分类号：TK263.6文献标识码：A 文章编号：1001-5884(2017)06-0451-05

# Research on ICA for Rotor-to-Stator Rubbing Diagnosis of Turbo-generator Units 

CAI Wen-fang1,LU Song-yuan2,WU Wen-jian1,YING Guang-yao 

(1 State Grid Zhejiang Electric Power Research Institute,Hangzhou 310014,China;2 Southeast University ,Nanjing 210096, China)

Abstract: To solve the problem that the signals for vibration monitoring and fault diagnosis in field are always interfered by noises or other mechanical signals,a signal separating method called as Independent Component Analysis (ICA) is applied on fault diagnosis of turbo-generator units in this paper. The method can separated the mixed-signals into independent original signals,and it can identify the fault exactly and improve the accuracy of fault diagnosis. The simulation experiments for multi-source signals are studied,and the result shows the feasibility that the ICA can be applied to the signal separation for mixed-signals. The shaft vibration signals of rubbing from turbo-generator unit in field are processed by ICA. At last the periodic impulse signals are extracted out successfully from the rubbing signals of the unit. It shows that ICA is effective for the impulse signal to be separated from rubbing signal and the fault is identified.


Keywords:vibrationof turbo-generatorunit;ICA;rubbing;fault diagnosis;rotating machines 

## 0前言

大型旋转机械振动故障得以消除的重要前提是对故障的准确诊断，该过程需建立在足够真实有效的振动数据及振动信号特征提取上，其中信号处理和分析是提取机械故障特征的关键。



在现场的复杂环境下，传感器获取的信号往往是不同振源产生的多路信号混合，还常常与一些噪声、无用信号等交叠在一起，对于这些源信号及传输特性事先是无法准确预知的。一般的信号处理方法（包括傅里叶变换、小波分析、Hilbert-Huang变换等)是直接进行时域或频域的分析，但显然从混合信号中分离出相互独立的信号源再进行分析和处理，将更有助于我们准确地判断设备的运行状况及故障诊断。由于事先对这样的源信号及其混合方式是未知的，使得这样一个分离过程成为盲源分离过程（BlindSource Separation，简称BSS)。



独立分量分析（Independent ComponentAnalysi，简称收稿日期：201641-21



ICA)是上世纪90年代伴随BSS问题发展起来的一项信号处理技术。该技术的最大优点是它能将多个独立信号源从它们的混合信号中分离出来，获得用于故障诊断的独立信号：能有效解决混合信号的盲源分离问题，其研究对象已渗入

## 1 独立分量分析法的基本原理

### 1.1 ICA模型建立

在现场实际情况下，观测信号来自一组传感器的输出，其中每一个传感器接收到的信号都是多个源信号的一组混合，如图1所示。



M个传感器所接收信号x ${\bf\Pi}_{1}(t),x_{2}(t),\cdots,x_{M}(t)$ 分别是N 个源信号$s_{1}(t),s_{2}(t),\cdots s_{N}(t)$ 的混合，以矩阵形式表示，则混合模型可描述为：

$$x(t)=A s(t)$$

其中$x(t)=\left[x_{1}(t),x_{2}(t),\cdots,x_{M}(t)\right]^T$ 是有噪情况下的M 维随机观测向量；$s(t)=\left[s_1(t),s_2(t),\cdots s_N(t)\right]$ 是N维源

<div style="text-align: center;"><img src="imgs/img_in_image_box_200_153_491_305.jpg" alt="Image" width="24%" /></div>


<div style="text-align: center;">图1信号混合过程示意图</div>


信号，且各分量s（t）假设为统计独立；A为由未知混合系数$a_{_{i i}}$ 构成的$M\times N$ 维满秩混合矩阵



独立分量分析就是寻找一个$N\times M$ 的满秩分离矩阵W，使得分离出的独立分量$\hat{s}(\mathbf{\nabla}t)$ 最大程度地逐步逼近真实的各个源信号$s(\mathbf{\nabla}t)$ ，即定义输出信号$\hat{s}\big(t\big)$ 是源信号s（t)的逼近估计：

$$\hat{s}(t)=W x(t)=W A s(t)$$

该过程的模型图 如图2所示。

<div style="text-align: center;"><img src="imgs/img_in_image_box_133_538_562_679.jpg" alt="Image" width="36%" /></div>


<div style="text-align: center;">图2独立风量分析混合-分离示意图</div>


### 1.2 ICA方法的实现

ICA算法在对混合信号进行盲分离以前，通常要先进行一些预处理，包括中心化和白化两个部分。



#### 1.2.1 中心化预处理

为了使实际信号都能符合以上数学模型的要求，在分离之前需要预先除去信号的均值。设x为均值不为零的随机变量，则中$ 心$ 化即是将观测矢量：$x\left(\mathbf{\nabla}t\right)$ 减去它的均值向量Et)，使得观测矢量$x\big(t\big)$ 变成均值矢量，即$x(t)=x(t)-$ Et)。对于有N个样本的随机变量，则可采用下式除去样本的均值:

$$\bar{x}_{i}(t)=x_{i}(t)=\frac{1}{N}\sum_{i=1}^{N}x_{i}(t)\quad i=1,2,\cdots n $$

#### 1.2.2 白化预处理

白化处理是为了除去信号各分量之间的相关性。首先对随机矢量t $x{\big(}t{\big)}$ 进行一定的线性变换：$\tilde{x}=T x$ ,使得变换后的随机矢量x的相关矩阵满足$R_{\tilde{x}}=E\left[\tilde{x}^{H}\right]=I\left(T\right)$ 为白化矩阵，1为单位阵）。



设混合信号的相关阵为$R_{v}$ ，则由相关矩阵的性质可知，$R_{v}$ 存在特征值分解为：

$$R_{x}=Q\sum^{2}Q^{T}$$

式中，矩阵$\sum^{2}$ 为对角矩阵，其对角元素$\lambda_{1}^{2},\lambda_{2}^{2},\cdots,\lambda_{n}^{2}$ 为矩阵$R_{x}$ 特征值，而正交矩阵Q的列向量为与这些特征值对应的标准正交的特征向量。于是可以取白化矩阵为：

$$T=\sum^{-1}Q^{T}$$

设$\tilde{x}=T x$ 则有：

$$R_{\tilde{x}}=E\left[\tilde{x}\tilde{x}^{T}\right]=TE\left[\tilde{x}x^{T}\right]T^{T}=TR_{x}T^{T}$$

将式（4)和式(5)代入式(6)，有：

$$R_{\bar{x}}=\left(\sum^{-1}Q^{T}\right)\left(Q\sum^{2}Q^{T}\right)\left(\sum^{-1}Q^{T}\right)^{T}=I $$

因此，通过矩阵T的变换，使得混合信号的各分量之间变得不相关了。



然而在实际计算中，混合信号的相关矩阵只能通过混合信号向量的样本来进行估计。设：$x(1),x(2),\cdots,x(N)$ 为混合信号随机向量的一组样本，于是该混合信号的样本相关矩阵由下式估计：

$$\widehat{R}_{x}=\frac{1}{N}\sum_{i=1}^{N}x(i)x(i)^{T}$$

实际计算中是以$\widehat{R}_{*}$ 的特征值分解来求白化矩阵的。

#### 1.2.3 基于负熵判据的快速固定点迭代算法（FastICA)

连续情况下，对于一个随机变量x，如果它的概率密度函数为$p{\big(}x{\big)}$ ，则其熵定义为：

$$H=-\int p(x)\log p(x)\mathrm{d}x $$

在所有的连续概率密度函数中，高斯分布的熵达到最大值。这就意味着，熵值可作为非高斯性的度量，即：若以某一特定高斯分布作为参考，就可以用信息熵来描述一个分布与高斯分布之间的偏离程度，也即非高斯性。因此把任意随机变量的$p(x)$ 和具有相同协方差阵的高斯分布间$p_{G}(x)$ 的KL散度作为该随机变量非高斯性程度的度量，称为负熵$\mathbb{14}$ ，记做J $\left[\mathfrak{p}\left(x\right)\right]$ ，可由下式计算：

$$J\left[p(x)\right]=H_{c}(x)-H(x)$$

负熵的值总是非负的，当且仅当x具有高斯分布时，$ 负$ 熵为0。以负熵为独立性判据，$\mathrm{F a s t~I C A}$ 算法迭代寻优对混合信号实现分离，其推导过程可见参考文献D]，这里直接给出迭代公式：

$$W_{k+1}\gets E\big(x g\big(W_{k}^{T}x\big)\big)-E\big(g\big(W_{k}^{T}x\big)\big)W_{k}$$

式中$,\scriptstyle g(\cdot)$ 为$\mathbf{\mathit{G}}(\mathbf{\nabla}\cdot\mathbf{\nabla})$ 的导数；$g^{\prime}(\cdot)$ 为$\scriptstyle g(\cdot)$ 的导数；$\it G(\nabla\cdot)$ 为一种非线性、非负二次函数。



通过上式寻找合适的解混矩阵，来实现独立分离信号的提取，分离过程是一个迭代逼近的过程。在每次提取一个分量之后，要从观测信号中减去该独立分量，如此重复，直到所有分量都被提取出来为止，若已提取出k个分量，则在下一轮迭代前应当对分离矩阵重新作正交化处理$^{[13,14]}$ :

$$W_{k+1}\longleftarrow W_{k+1}\;-\;\sum_{j=1}^{k}\;\left\langle W_{k+1}\;,W_{j}\right\rangle W_{j}.$$

式中，$\langle\cdot,\cdot\rangle$ 表示内积。于是，总结多个独立分量的逐次提取的算法步骤如下：

（1）对观测的混合数据x去均值，使其均值等于零，即

$\tilde{x}=x-E(x)$ 



(2)对观测的混合数据进行白化处理，对数据进行正交变换，使得$E(x^{T}x)=I$ o 



(3)以$m$ 作为独立分量数目。置$p\leftarrow1\big(p$ 为当前分离的独立源个数）。



(4)选择初始分离矩阵$W_{0}($ 随机或人为给出都可以），但要求其具有单位范数：$\left\|W_{0}\right\|_{2}=1$ 。设置收敛误差$0<\varepsilon\ll1$ 

(5)迭代更新。按式(11)更新分离矩阵$W_{k+1}$ 

(6)根据式(12)，正交化分解矩阵$W_{k+1}$ 」，并进行标准化处理:$W_{k+1}\longleftarrow W_{k+1}/\left\|W_{k+1}\right\|$ 2°



(7)将相邻两次分离矩阵的误差绝对值与收敛误差比较。若$\left|W_{k+1}-W_k\right|\geqslant\varepsilon$ ，未收敛，返回至步骤（5）；若

$\left|\mathbf{\nabla}W_{k+1}-W_{k}\right|<\varepsilon$ ，收敛，分离出一个独立分量；

(8)置$p\leftarrow p+1$ ,若$p<m$ 时，返回步骤（4）继续分离下一个分量；若$p=m$ 时，分离结束。



算法流程如图3所示。

<div style="text-align: center;"><img src="imgs/img_in_image_box_189_262_497_775.jpg" alt="Image" width="25%" /></div>


<div style="text-align: center;">图3 Fast ICA算法流程图</div>


## 2 多个源信号混合分离仿真实验

在实际工程中，现场情况可能很复杂，一个观测信号可能由多个源信号混合而成，而且各源信号可能不只是来自机器的振动信号，还常常包括来自不同地方的噪声信号。仿真实验选取6个常规信号作为独立的源信号，采样频率为$1000\mathrm{H z}$ ，采样长度为1s。如下：

正弦信号：$\mathrm{sig1=8^{*}\sin(8^{*}\pi pi^{*}\pi t)};$ 

随机信号：

$$\mathrm{sig}2=2^{*}\mathrm{randn}(1,1001); ；$$

方波信号：$\mathrm{sig}3=8^{\circ}\quad\mathrm{square}(40^{\circ}\quad\mathrm{t})$ 

冲击信号：$\mathrm{s i g4=i m p u l s e(s y s,t)}$ 

正弦衰减信号：$\mathrm{sig}5=8*\exp(-2.5*\mathrm{t})*\sin(50*\mathrm{pi})$ t);

三角波信号：$\mathrm{sig}6=8*\mathrm{swoth}(60*\mathrm{t},0.5)$ 

根据前面的理论知识，将这些源信号以未知的方式混合成观测信号，由MATLAB程序产生一个$6\times6$ 的随机矩阵A 模拟这样一个未知的混合过程：

$$\left[\begin{matrix}{x_{1}}\\ {\vdots}\\ {x_{6}}\end{matrix}\right]=\left[\begin{matrix}{a_{11}}&{\cdots}&{a_{16}}\\ {\vdots}&{\ddots}&{\vdots}\\ {a_{61}}&{\cdots}&{a_{66}}\end{matrix}\right]=\left[\begin{matrix}{S_{1}}\\ {\vdots}\\ {S_{6}}\end{matrix}\right]$$

根据以上混合矩阵元素$a_{i j}$ 加权叠加后得到混合信号$x_{1}$ ${\cdots}x_{6}$ ，如图4所示。



图中的混合信号的时域波形比较混乱，已无法辨别这组混合信号是由哪些源信号混合而成的，通过FFT变换得到的频谱成分也比较复杂，要从这样的混合信号中识别出单个的

<div style="text-align: center;"><img src="imgs/img_in_chart_box_621_153_1065_505.jpg" alt="Image" width="37%" /></div>


<div style="text-align: center;">图4多源混合信号波形图</div>


源信号是十分困难的。在工程中若采集到这样的信号，传统FFT变换无法对信号实现准确的识别，更不能准确地找到产生这些信号的故障源。



采用ICA法对这些混合信号进行分离时，程序首先默认独立分量个数与观测到的混合信号数目相同，由MATLAB程序随机产生初始分离矩阵，迭代更新得到最终的分离矩阵（也称解混矩阵），将以上混合信号分离成6个独立的源信号（图5）。可见分离信号完整地恢复了各源信号的波形特征，频谱成份也非常清晰，能很容易地实现对各信号的识别。

<div style="text-align: center;"><img src="imgs/img_in_chart_box_621_790_1064_1141.jpg" alt="Image" width="37%" /></div>


<div style="text-align: center;">图5ICA分离出的多源信号波形图</div>


仿真试验中模拟冲击信号的幅值仅为其它信号的1/8，相当于微弱信号。在混合之后，无论在波形还是频谱中都无法被识别，信号被完全掩盖。而采用ICA法对以上混合信号进行分离后，结果得到了明显的冲击信号，且幅值被相对放大，使得分离出的冲击信号十分明显。



在现场实际中，早期碰磨故障并不明显，产生的故障信号比较微弱，很可能被淹没在工频或噪声信号中，从波形或频谱中都很难被发现，这就失去了对早期碰磨故障的诊断机会。长期运行轻微故障就有可能发展为危害机组的严重故障，后期的处理也会耗费更多的人力、财力。所以，对机组早期故障的识别也是目前状态监测和故障诊断的研究方向之一。若以此冲击信号作为对碰磨故障的诊断将是十分有力的证据，可实现对故障的早期诊断。



## 3 某电厂1号机组动静碰磨故障ICA分析

### 3.1 基本概况

某电厂1号机组是西屋引进的350MW亚临界机组，为单轴、两缸两排汽、凝汽再热式汽轮机，轴系结构如图6所示。



<div style="text-align: center;"><img src="imgs/img_in_image_box_143_343_540_398.jpg" alt="Image" width="33%" /></div>


<div style="text-align: center;">图6某电厂1号机组轴系结构图</div>


该机组于2001年4月底完成投产后的第一次大修，其间进行了两次高速动平衡降低了1号瓦和7号瓦振动。但在5月5日和6日机组两次升负荷过程中，都发生了低压缸3、4号瓦轴振上升的现象，其间发现低压缸两侧温差较大，超出正常值，判断是低压缸左右侧温差造成缸体变形，导致动静碰磨故障。5月8日再开机过程中，先带低负荷（45MW)后解列做超速试验，然后并网升负荷，于09:45到130MW，此前振动正常。随后负荷略有降低，持续到10:06时，振动开始增大，如图7所示。



<div style="text-align: center;"><img src="imgs/img_in_chart_box_175_685_513_880.jpg" alt="Image" width="28%" /></div>


<div style="text-align: center;">图7某1号机组升负荷过程4Y振动趋势图</div>


### 3.2 碰磨信号的ICA分析

为验证ICA在初期碰磨故障诊断中的应用，取5月8日10:06机组带负荷至130MW,3、4瓦轴振刚刚开始增大时的振动信号(早期故障)作为研究对象，测点取3X、3Y4Y，采样频率6400Hz，采样长度0.08s。信号时域波形及频谱图如图8所示。



从以上观测信号的时域波形图上看出，所有轴振都为1倍频正弦波信号，其频谱图也是标准的50 Hz工频，所得到的信息十分有限，仅根据这些信息不能做出机组已经发生碰磨的诊断结果。运行FastICA的Matlab程序对以上观测信号进行迭代分离，并选取Symlets函数系中的sym6 小波程序对分离信号进行消噪处理，得到以下消噪后的分离信号，如图9所示。



可见ICA分离信号1、2都为工频正弦信号，是转子旋转产生的强迫振动，分离信号3中在某些地方振幅有突增并振荡的现象，且每次发生都相隔一个几乎固定的时间，这个时间基本与1倍频信号的周期相当，虽然这样的波动不十分清晰但还是可以分辨的。借助经验模态分解(EmpiricalMode Decomposition，简称EMD)对信号3的分解，如图10所示。

可见，分量imfl、imf2、imf3都具有较为明显的冲击信号特征，可以认为是转子受到的冲击信号，它是对碰撞故障的直接表现，表明转子在该时段动静部件已经发生了碰磨，实现了对早期碰磨故障的诊断识别。



<div style="text-align: center;"><img src="imgs/img_in_chart_box_616_153_1066_507.jpg" alt="Image" width="37%" /></div>


<div style="text-align: center;">图8某电厂1号机组3、4 瓦碰磨轴振信号波形及频谱图</div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_615_552_1069_788.jpg" alt="Image" width="38%" /></div>


<div style="text-align: center;">图9消噪后的ICA分离信号波形图</div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_616_831_1071_1356.jpg" alt="Image" width="38%" /></div>


<div style="text-align: center;">图10冲击信号的EMD分解及各分量的频谱图</div>


## 4 结论

(1)ICA法早期运用在语音信号分离领域，文中尝试将其应用在旋转机械振动信号分离上，从仿真模拟实验到实际

机组碰磨信号的分析，都验证了该方法的可行性。尤其是对早期微弱的碰磨信号的识别，有着重要的工程价值。

(2）混合信号由源信号向量与随机混合矩阵相乘，若两者之间互换比例因子对观测信号是没有影响的，这样一个可变的比例因子就使得各独立源信号在幅值上是可变的，这就造成了分离信号在幅值上失真。即便如此，只要分离信号的波形完整，就不影响对信号类型的识别，甚至对某些微弱信号的幅值有放大作用。



（3）理论上ICA能将噪声信号作为独立的源信号分离出来，但实际运用时效果很不理想，文中借助了小波消噪才使得冲击信号得以较为明显的呈现，可见对实际信号的分离效果有限。另外，现场传感器所获得的混合信号不可能都是源信号的简单线性混合，更一般的是信号非线性混选，而对非线性混迭信号的分离要比线性的复杂很多，ICA存在分离失败的可能。



(4)文中初步将ICA与小波和EMD分解相结合，但仅仅尝试了用两者来凸显ICA的分离效果。而更深一步的结合，充分利用小波变换在时频域的伸缩、平移特性及EMD处理非线性、非稳态信号的优势，将提高ICA分离准确性并扩展它的应用范围。



## 参考文献

[1]陆颂元.汽轮发电机组振动M．北京：中国电力出版社2000.
[]张贤达.现代信号处理M．北京：清华大学出版社，20023]Aapo Hyvarinen,Juha Karhunen,Erkki Oja. Independent Component Analysis [M]. 2001.
4C.T.YIAKOPOULOS and I.A.ANTONIADIS Analysis of vibration 

（上接第420页）

按常规热平衡法计算，机组内功率下降1.3720MW，吸热量下降3.1015MW，机组热耗下降1.584kJ/(kW·h)。由此可见，内功率和吸热量变化的计算结果与常规热平衡法误差极小，热耗变化计算公式忽略了二阶无穷小量，误差也只有0.033kJ/(kW·h)



## 12 结论

随着人们对等效焓降法原理研究的深入，等效焓降法的名称也变得越来越不符合实际。完全可以由式(4)、式(5)直接求得抽汽效率和热量比，然后按等效焓降法的原理直接计算机组内功率和吸热量的变化量，从而得到机组热耗的变化量。这一过程既不需要用到抽汽等效焓降，也不需要用到新蒸汽等效焓降的概念。



部分机组按式（5)计算的热量比可能会出现一些偏差，例如一些明显应等于0的热量比不等于0。如偏差较小，可能是热平衡图数据的截断误差和焓熵计算的误差引起的；如偏差较大，则应核查热平衡图并检查计算过程是否正确。

对于不熟悉矩阵运算的工程技术人员，可由式（8）~式(13)依次由低至高求取各段抽汽的等效焓降和等效热量，由式(6)和式(7)求得各段抽汽的抽汽效率和热量比。对于带

responses of defective rolling bearing using Blind Source Separation M.1-6.
5]A.Ypma,R.P.W.Duin,Blind Separation of Rotating Machine Sources:BilinearForms and ConvolutionMixtures[.Neurocomputing,2002,49:349 –368.
[6]Aurobinda Routray,Niva Das,P.K. Dash. Denoising and Whitening inthe Context of Blind Source Separation of Instantaneous Mixtures [A]. Industrial Informatics,In 2007 5th IEEE Interna–
tional Conference [].2007,23-27:377-380.[7]李舜酪，杨涛，基于峭度的转子振动信号分离，应用力
学学报,2007,24(4):560-565.
8Rivet B,Vigneron V,Paraschiv – Ionescu A,and Jutten C. Wavelet de- noising for Blind Source Separation in Noisy Mixtures [D].
Lecture Notes in Computer Science,2004 ,3195:263 -270.9]史习智，等.盲信号处理－理论与实践M：上海：上海交通
大学出版社，2008.
[0]Guillaume Gelle and Maxime Colas Blind Source Separation Applied to Rotating Machine Monitoring and Fault Detection[M].
BLINDSOURCESEPERATION NOISE&VIBRATIONWORLDWIDE OCTOBER 2001 ,11–16.
[1]孙宏凯，李香玲，李彦红，等.概率论与数理统计.[12]杨福生，洪波.独立分量分析的原理与应用M.北京：清
华大学出版社，2006.
[13]季忠，金涛，杨炯明，等.基于独立分量分析的消噪方法
在旋转机械特征提取中的应用．中国机械工程，2005，16(1) :50-53.
[4]王述伟，刘正平.基于FastICA的旋转机械故障特征盲源分离
方法研究.煤矿机械，2008,29(10):207-210.[15]陆颂元，大型机组动静碰磨的振动特征及现场应急处理[
中国电力，2003,36(1):6-11.


外置蒸冷器且蒸冷器出水引至锅炉的机组，内功率变化的计算与常规机组相同，吸热量的变化可用热量比计算。由于回热系统的扰动无非是影响热交换，所有加热器的扰动均可以转化为热量变化问题，因此，各加热器对吸热量影响的计算公式与内功率影响的计算公式相比，只要把抽汽效率改成热量比即可。对于返回汽轮机的抽汽，分别考虑对机组内功率和吸热量的影响即可。



## 参考文献