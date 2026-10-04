

# 液体环形密封转子动力特性CFD数值计算分析

杨绍宇，陆颂元

（东南大学振动控制与信息系统研究所，南京210096)

摘要：首先研究建立环形密封物理模型和划分计算区域网格的方法：然后选择计算模型，确定边界条件，利用有限体积法的CFD一Flent软件，计算该密封流体激振力和泄漏量；最后依据转子动力模型和激振力方程，计算环形密封动特性系数，与Lindsey的实验结果和Childs的理论计算结果进行了比较，结果表明本文的CFD数值计算结果比基于整体流动理论的计算结果更接近实验值。


关键词：CFD-Fluent环形密封：泄漏量：动特性

分类号：TB42文献标识码：A 文章编号：1001-5884（2007)01-0023-04

# Application of CFD Analysis for Liqu id Annu lar Pressu re Seals 

YANG Shao-yu LU Songyuan 

(Vibration ControlandInfomation SystemInstitute of SoutheastUniversity,Nanjing 21096, Chia)

## Abstract
 First the paper builds physicalmodel and creates mesh of the liquid annular pressure seal And follow ing decides m odel for calcu lation and boundary cond itions calcu lates the forces on shaft and m ass flow rate through the sealwith CFD-Fluentwhich bases on finitevolume Finally, builds model for rotor dynam ics and linear equation system， figures out dynam ic coefficients of the seal The resu lts of CFD approxim ate to experim entalresu lts ofLindsey com pare with theoretical pred ictions resu lts of Childs whichbasedonbu lkflowmodels 

Key words CFD —fluent; annu lar pressure sea l; leakage; dynam ic coefficients 

## 0前言

流体旋转机械转轴上密封的作用是减小或控制流体工质的泄漏量，通常密封两端压差很大，密封内流体流动复杂，会产生大的流体激振力，导致转子失稳。



密封流体激振的研究中，早期普遍采用基于薄膜假设的整体流动模型（Bulk—FlowModels），这是一种根据Hirs的湍流润滑理论推导出的经验性模型：Childs随后在Hirs的湍流方程基础上又提出了“有限长度理论”。Antunes等人[]采用整体流动模型和Hirs壁面摩擦系数方程研究了大间隙密封环流中转子静、动特性，在一定的假设下推导了解析解；Hsu和Brennen[3]对泵和透平机械的环形密封整体流动模型所需的方程进行汇总，提出一种通用的数值计算方法，但是，当密封流场的工作情况超出薄膜假设的适用范围时就不再适用。国内，孙启国等人[4]采用紊流整体流动模型和Moody 壁面摩擦系数方程，建立间隙环流3D非线性微分方程，运用摄动法求解了间隙环流中同心涡动转子动特性系数；张新敏等人[]利用有限长度理论对锅炉给水泵密封环的间隙力进行了数值计算，据称计算结果与试验结果基本相符。

20世纪80年代开始，针对流场的计算流体动力学（CFD）研究逐渐活跃，使用CFD求解密封流场的时均N一S 方程与流体动力润滑理论相结合，能够得到比较准确的密封流体动力特性。国外主要利用CFXTASCFlow软件研究了迷

收稿日期：2006-07-16

宫气体密封，计算精度高于整体流动模型[6]，但对流体机械液体环形密封的CFD数值研究，国内外已做工作极少。

本文利用CFD-Flent软件对液体环形密封进行建模，采用准稳态全三维模型，对密封间隙内流场进行计算分析，进而计算静、动特性，并将计算结果和Childs的理论计算结果，以及Lindsey的实验结果进行了详细的比较，得到了一些有意义的结果。



## 1 环形密封模型及网格划分

计算用环形密封和间隙的几何参数[7]见图1,工质为54纯水，轴转速10200r/min。对密封和轴之间的间隙(图2)使用Gambit建模。假设转子偏心为间隙的10%，转子绕密封中心涡动，设涡动轨迹为圆，此时，流体激振力与刚度、阻尼、附加质量为线性关系[8]。



环形间隙区域内网格划分见图3.网格数：轴向X径向×周向$600\times15\times36=32$ ，其中径向采用两边对称的等比网格，比例为115，这样做的目的是细化流动特性变化较大的近壁面区域，在湍流充分发展的流动中心位置变量梯度较小，网格相对较疏。



## 2 Fluent参数设置

对于该密封，选择3D耦合求解器，隐式格式求解；用标

<div style="text-align: center;"><img src="imgs/img_in_image_box_60_102_440_350.jpg" alt="Image" width="37%" /></div>


<div style="text-align: center;">图1密封几何参数</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_119_399_383_655.jpg" alt="Image" width="26%" /></div>


<div style="text-align: center;">图2转子偏心</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_33_708_465_855.jpg" alt="Image" width="43%" /></div>


<div style="text-align: center;">图3径向等比网格示意图</div>


准$\mathrm{k}\mathrm{ 一 }\upvarepsilon$ 方程和标准壁面函数描述湍流；流体控制方程采用二阶迎风格式离散，湍流方程采用一阶迎风格式离散：计算时当所有方程的残差小于$1\times10^{-}$ 5时判定解收敛，此时进出□质量流量基本相等。



环形密封与轴间隙内介质静压为$1.38\mathtt{M P a}$ 时，密度$\varrho=$ $986\mathrm{~7{k g/m}^{3}}$ ，动力黏度$\mu=5~17\times10^{-4}\mathrm{p_{a}\cdot\mu_{s}}$ ，取旋转轴为Z 轴的旋转坐标系，轴转速与涡动转速相同，使得间隙内流体在旋转坐标系内为定常。



进口边界条件设为压力入口，静压$p_{s}=1.38\mathrm{M}\mathrm{P}_{a}$ 入口压力损失系数Q1。利用以下公式计算总压和湍流参数：

总压：$p_{0}=p_{s}+\rho|\mathbf{\nabla}_{\mathrm{v}}|^{2}$ 

湍流强度：$I=016(R e)^{-1/8}$ 

湍流尺度：$\mathrm{l}=0.07\mathrm{L}$ 

其中，$\mathrm{R e}^{\mathrm{~\tiny~=~}\frac{\rho_{\mathrm{v}}}{\mu}}$ ；L为水力学直径，对于该物理模型$L=D-d$ 

出口边界条件取压力出口，出口静压为零。

环形间隙外侧为静止状态的密封内壁面，边界条件设为静止壁面：间隙内侧为转轴表面，设为旋转壁面，绝对转速10 200r/min旋转轴起点为$(\mathrm{~0.~007~6_{m m},~0,~0~})$ ，方向为Z轴正向。



## 3 环形密封转子动力学模型

根据以上计算模型建立转子动力学模型（见图4），密封流体激振力、刚度、阻尼、附加质量的方程如下：

$$\begin{aligned}-\left[\begin{array}{c}\mathrm{F}_{\mathrm{r}}(\mathrm{t})\\\mathrm{F}_{\mathrm{r}}(\mathrm{t})\end{array}\right]=&\left[\begin{array}{cc}\mathrm{k}_{xx}&\mathrm{k}_{xy}\\\mathrm{k}_{yx}&\mathrm{k}_{yy}\end{array}\right]\left[\begin{array}{c}\mathrm{X}(\mathrm{t})\\\mathrm{Y}(\mathrm{t})\end{array}\right]+\left[\begin{array}{cc}\mathrm{d}_{xx}&\mathrm{d}_{xy}\\\mathrm{d}_{yx}&\mathrm{d}_{yy}\end{array}\right]\left[\begin{array}{c}\mathrm{X}(\mathrm{t})\\\mathrm{Y}(\mathrm{t})\end{array}\right]\\+&\left[\begin{array}{cc}\mathrm{m}_{xx}&\mathrm{m}_{xy}\\\mathrm{m}_{yx}&\mathrm{m}_{yx}\end{array}\right]\left[\begin{array}{c}\mathrm{X}(\mathrm{t})\\\mathrm{Y}(\mathrm{t})\end{array}\right]\end{aligned}27
$$

其中，$k_{xx}=k_{yy}=k.\;k_{xy}=-k_{yx}=k\;d_{xx}=d_{yy}=D.\;d_{xy}=-d_{yx}=d$ $\mathrm{m}_{xx}=\mathrm{m}_{yy}=\mathrm{M},\mathrm{~m}_{xy}=-\mathrm{m}_{yx}=0,$ F为径向力，$\mathrm{F}_{\tau}$ 为切向力。

<div style="text-align: center;"><img src="imgs/img_in_image_box_633_412_882_658.jpg" alt="Image" width="24%" /></div>


<div style="text-align: center;">图4转子动力学模型</div>


在旋转坐标系下流动是定常的，为便于分析，取$t=0$ 时刻进行研究，有：

$$\begin{align*}\mathrm{X}(0)=\mathrm{e}_{\mathfrak{H}},\mathrm{Y}(0)=0,\mathrm{X}(0)=0,\mathrm{Y}(0)=\mathrm{e}_{\mathfrak{H}}\Omega,\\\mathrm{X}(0)=-\mathrm{e}_{\mathfrak{H}}\Omega^2,\mathrm{Y}(0)=0\end{align*}$$

因此，式（4）简化为：

$$\left\{\begin{array}{l}{\scriptstyle\mathrm{F_{r}}/\mathfrak{H}}=-\mathrm{K}-\mathrm{d}\Omega+\mathrm{M}\Omega^{2}}\\ {\scriptstyle\mathrm{F_{r}}/\mathfrak{H}}=\mathrm{k}-\mathrm{p}\Omega}\end{array}\right.$$

表示涡动的振幅，$\mathrm{F}_{\mathrm{~r~}}$ 大于零时将导致涡动振幅增大；$\mathrm{F}_{+}$ 为造成涡动的力，大于零时，方向同涡动方向相同，促进涡动，导致失稳。由式(5)可知，取3个不同的涡动值，便可$ 产$ 生3组方程，联立这3组方程组即能够解出密封动特性系数。

## 4 计算结果分析

计算时取$\Omega/\omega=0.05.$ 1,3个值计算密封动特性和泄漏量，并对静压为$1.\ 38\mathrm{~M}\mathrm{P}_{\mathrm{a}}\Omega/\omega=0$ 5的流场进行分析，同时计算静压为241M $\mathrm{P a}$ 和$\mathrm{345M P a}$ 时的密封性能，与Lindsey的实验结果和Childs的理论计算结果比较，验证CFD方法的精度。



### 4.1 流场分析

图5为计算得到的速度矢量图，图中根据颜色可以看出进口处速度较小，出口处较大：近密封处速度较小，近轴面处速度较大：进口处近密封壁面以轴向为主，但近轴面的速度具有较大的切向分量，流体经过密封至出口时流动方向发生偏转，这是由于旋转轴表面的黏性剪切力的作用。

图6显示了静压沿轴向的分布，从图中可以看出，静压沿轴向呈线性下降。



<div style="text-align: center;"><img src="imgs/img_in_chart_box_28_100_471_329.jpg" alt="Image" width="44%" /></div>


<div style="text-align: center;">图5速度矢量图</div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_61_372_438_650.jpg" alt="Image" width="37%" /></div>


<div style="text-align: center;">图6压力沿轴向变化情况</div>


### 4.2 泄漏量

图7显示了所有工况下泄漏量随$\Delta_{\mathrm{p}}$ 增加而呈线性增加。Childs用MUDY理论计算时，为尽量与实验吻合，减少误差，参数选择如下：进口压力损失系数$\xi_{\mathrm{i n}}=0\quad1$ ，出口压力恢复系数$\mathbf{\xi}_{_{\mathrm{e x}}}=1,$ ，即出口没有压力恢复，转子表面相对粗糙度$\in_{r}=0\ 001$ ，密封内表面相对粗糙$ 度 \in\mathbb{Z}_s=0\ 001$ 。

图7表明，本文CFD计算结果和Childs的计算结果都小于Lindsey的实验结果，本文方法与实验值的误差为16%，Childs的误差为20%。压差增大时误差的百分比基本不变。

### 4.3 密封动特性

图8比较了不同压差下刚度阻尼的$\mathrm{C F D}\mathrm{~\text--~}\mathrm{F}\mathrm{~h e n}$ 计算结果、Childs的MUDY计算结果以及Lindsev的实验结果。定性来讲，3种结果的共性表现为动特性系数随压力增加而增

<div style="text-align: center;"><img src="imgs/img_in_chart_box_556_115_941_303.jpg" alt="Image" width="38%" /></div>


<div style="text-align: center;">图7不同压差下的泄漏量</div>


加，其中交叉刚度系数增加较小。

Lindsey实验值中，主刚度$\mathrm{k_{x}}$ 和$\mathrm{k_{y y}}.$ 交叉刚度$ k_{xy} 和 -k_{y}$ x 不相等，但有$\mathrm{k}_{xx}\cong\mathrm{k}_{yy},\mathrm{k}_{xy}\cong-\mathrm{k}_{yx}$ ，图中只显示了主刚度K和交叉刚度k的平均值。主刚度的实验值最大，计算值都比实验值小：从趋势上看，随压力增大，实验值和计算值逐渐逼近，计算值呈线性增长。交叉刚度的计算值大于实验值；趋势上看，Fluent计算值与实验值较为接近，随压力呈增长趋势。



实验结果的主阻尼$\mathrm{d}_{x}$ 和$\mathrm{d}_{_\mathrm{y y}}.$ 交叉阻尼$ d_{xy} 和 -d_{y}$ $ d_{xy} 和 -d_{y}$ 也不相等，但同样有$\mathrm{d}_{x}$ c:$\mathrm{d}_{\mathrm{y y}},\mathrm{d}_{\mathrm{x y}}\cong-\mathrm{d}_{\mathrm{y x}}$ ，图中还是取平均值表示。对于主阻尼，3种方法的结果基本接近，MUDY和Flent理论预测随压力变化的趋势与实验值相同。



### 4.4 涡动比

主刚度提高：转子临界转速提高：交叉刚度是导致转子失稳的因素，交叉刚度越大，转子越容易失稳：主阻尼是抑制转子失稳的因素，主阻尼越大，转子越不易失稳。因此，为提高流体旋转机械的稳定性能，就需要减小交叉刚度，增大主刚度和主阻尼。为衡量密封对转子稳定性的影响，引入涡动比f，对于环形液体密封，涡动比$[7]$ 可近似定义为

$$\mathrm{~\it~f~}=\frac{\mathrm{~k~}}{\omega\mathrm{D}}$$

式（6)表示失稳因素同稳定因素的比值，f越小，转子越稳定。图9显示了涡动比的计算值和实验值随压力增加而一致减小，即随压力增加，密封稳定性有所提高，理论预测值明显高于实验值，说明密封稳定性的理论计算对出现失稳的预测，较实测偏于严重，但Fluent预测值较为接近实验值。

<div style="text-align: center;"><img src="imgs/img_in_chart_box_134_1048_862_1422.jpg" alt="Image" width="72%" /></div>


<div style="text-align: center;">图8不同压差下的密封动特性</div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_51_104_447_283.jpg" alt="Image" width="39%" /></div>


<div style="text-align: center;">图9涡动比随压力变化</div>


## 5 总结

本文使用CFD方法计算分析环形密封动力特性，对该密封环形间隙区域内使用Gambit划分网格时，经过计算比较，最终确定最佳的三维网格密度和两边对称的等比网格结构；同时，迭代计算发现，必须选择耦合求解器解才会收敛，且残差设置能够满足计算精度要求。



本文的CFD—Fluent计算结果同Lindsev的实验结果以及Childs的理论计算结果的比较显示，泄漏量都随$\Delta_{\mathrm{p}}$ 增加而线性增加，计算值低于实验值，但Flent理论预测值较接近于实验值。主刚度的实验值大于计算值，随压力增大，实验值和计算值逐渐逼近。交叉刚度的实验值偏小，计算值偏大，Fluent计算值与实验值较为接近。



对于主阻尼，3种方法的结果基本接近。从涡动比的角度看，随压力增加，密封稳定性有所提高，理论预测值都明显高于实验值，其中Flent预测值较为接近实验值。

各项计算结果表明，本文CFD-Flen的结果较Childs 

（上接第22页）Samsung-20020318targz内核编译完成以后，在/uClinux-Samsung/images目录下看到两个内核文件：imageram和imagerom，其中，可将image rom烧写到RoM/SRAM/FLASHBank0对应的Flash存储器中，当系统复位或上电时，内核自解压到SDRAM，并开始运行。

(2)BootLoader的移植[4]。在嵌入式系统中，BootLoader 的作用相当于PC机上的BIOS它是在操作系统内核运行之前运行的一段小程序。通过这段小程序可以初始化硬件设备、建立内存空间的映射图，从而将系统的软硬件环境带到一个合适的状态，以便为最终调用操作系统内核准备好正确的工作环境。在本文中，BootLoader存储在一片Flash芯片中。BootLoader作为系统复位或上电后首先运行的代码，从起始物理地址0×0开始。Bios—1t是一种适合于S3C4510B 的BootLoadeF支持Flash、串口、网络3种装载方式，Bios-lt 默认系统配置为：

ROM BANKO: 512K×8 Flash(SST39VF040)

ROM BANK1:1M×16Flash(SST39VF160)

SDRAMBANK0:2M×16×4BankSDRAM(K4S281632C—TL75)



CPU CLOCK: 50MHz 

因为默认设置与本系统所选硬件适合，可以直接输入“Make"命令，得到影像文件：/imgtools/img/biosimg将文件烧写到ROMBANKO即可。



### 2.4 uClinux下应用程序的开发

应用程序一般用C语言编写，编写完成后，需要将其加

的MUDY结果更接近Lindsey实验结果，这对流体机械密封动特性计算分析方法的深入研究具有一定的实际意义。

## 参考文献

[1]Childs D W. Finite-length solution for rotordynam ic coefficients of turbu lent annu lar seals[ J]. ASME Joumal ofLubrication Tech no logy1983,105:437-444.
[2]AntunesJ AxisaF,Gmnenwald T Dynam ics of rotors immersed in eccentric annu lar flow. Part1: Theorv[J]. JoumalofFluidand Structures 1996, 10: 893-918[3]Hsu Y， Brennen CE Fluidflow equations for rotordynam ic flows in seals and leakage paths[J]. ASMEJoumalof Fluids Engineer ing 2002, Vol 124
[4]孙启国，虞烈，谢友柏：间隙环流中同心涡动转子动特性的
研究「J.机械强度，2003，25（D：021-024[5]张新敏，于慎波，李良，等.锅炉给水泵密封间隙力的数值分
析「J].沈阳工业大学学报，1995，17（3）
[6]Tosh io H irano Zenglin Guo R， Gordon K irk Application of com putational fluid dynam ics analysis for rotating m achinery part I labyrinth seal analysis[J]. ASME Joumal of Engineering for Gas Turbines and Powe 2005, Vol127: 820-826[7]Lindsev WT,Childs DW.The effect of converging anddiverging axial taper on the rotordynam ic coefficients of liquid annular pres sure seals Theory Versus Experiment[J]. ASME Joumal ofVi bration and Acoustics 2000, Vol 122[8]Sator Kaneko Takashi Ikeda Takuro Saito et al Experimental study on static and dvnam ic characteristics of liquid annular con vergent- tapered dam per seals with honeycomb roughness pattem [J].ASME JoumalofTribology, 2003, Vol125:592-599.

载，通常做法是将应用程序和uClinux的内核编译在一起。其步骤如图2所示。



<div style="text-align: center;"><img src="imgs/img_in_image_box_524_876_973_993.jpg" alt="Image" width="44%" /></div>


<div style="text-align: center;">图2uClinux下应用程序加载流程</div>


## 3 结束语

在电力、石化、冶金、机械行业中，旋转机械处于举足轻重的关键地位，将嵌入式系统技术引入到旋转机械状态监测中来，研制成功嵌入式旋转机械状态监测系统，将会具有广阔的应用场景和较高的市场价值。



## 参考文献

[1]崔福东．汽轮机发电机组振动故障诊断数据库及其网络化研究[D]，南京：东南大学动力工程系，2003[2]ARM应用系统开发详解基于S3C4510B的系统设计「M].北
京：清华大学出版社，2003
[3]东南大学自控系，数字信号处理[M].南京：东南大学出版
社，2001.
[4]基于ARM嵌入式系统的通用bootloader的设计与实现（doc 55)[DB/0L].http://www.3726cn/softdown/2005