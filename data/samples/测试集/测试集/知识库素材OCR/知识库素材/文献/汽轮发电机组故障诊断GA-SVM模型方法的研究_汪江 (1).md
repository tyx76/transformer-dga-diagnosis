

# 汽轮发电机组故障诊断GA-SVM模型方法的研究

汪江，陆颂元

（东南大学振动控制与信息系统研究所，南京210096）

摘要：基于结构风险最小化[1]的支持向量机是一种新的机器学习方法，具有适应小样本学习和提高学习机泛化性能的优点，详细介绍了将其应用于汽轮发电机组的故障诊断的研究结果，包括结合遗传算法进行模型参数的优化选择，建立联合模型，通过对现场采集的故障样本进行的分类试验，并同BP神经网络方法进行了比较，结果显示本文所述方法具有较高的诊断准确率。


关键词：汽轮发电机组：故障诊断：遗传算法：神经网络

分类号：TP267文献标识码：A 文章编号：1001-5884（2005)01-0001-03

# The Study of GA -SVM on Turbo−genera tor Fau lt D iagnosis 

WANG Jiang LU Songyuan 

(Vibration Control and Info m ation System Institute Southeast University, Nanjing 210096, China)

## Abstract
 Support vectors m achine is a new m achine leaming method based on m inim um structural risk which characteri zes adaptingto little sam ples'leaming and improvedgeneralization Thepaper introduced SVM in detail and then usedit in turbo-generator fault diagnosis A genetic algorithm method which helping to select model and model param eter for SVM，was used to build a jointGA SVMmodel Tests of diagnosis on fault samples from the filed and com parison with BP neural networks showed that the method this paper in troduced can improve preciseness of diagnosis considerab ly 

Keywords turbo-generator;fau lt diagnosis genetic algorithm;neuralnetwork 

## 0前言

故障诊断技术经过几十年的发展已取得了较大的进展，人工智能的产生使得其已从最初的领域专家人工诊断逐渐走向智能化自动诊断。自从1968年美国Stanford大学开发第一个专家系统DENDRAL起，专家系统就逐渐广泛应用于故障诊断，如西屋公司的TubineAID。近20年来兴起的人工神经网络技术进一步加快了智能诊断的发展步伐。神经网络具有良好的知识自学习能力，国内外很多学者通过大量的试验，试图将神经网络应用于故障诊断，已取得了一些进展。同时，这两种方法也存在各自的缺点，制约着它们在汽轮发电机组故障诊断中的应用。如专家系统存在知识获取的“瓶颈”问题、知识难以维护，推理能力弱等等。神经网络为了能很好地逼近所要预测的模型，需要不断调整网络结构及连接权值，使得模型过于复杂，造成模型过学习（overfit $\mathrm{t i n g)}$ 和泛化性能（generalization）下降。故障诊断领域的另一个瓶颈问题是学习样本不足，这也是上述两种方法无法解决的。



期出现的一种基于统计学习的机器学习方法，它建立在结构风险最小化原则的基础上，机器学习策略是保持经验风险值而最小化置信范围。与人工神经网络相比，统计学习理论具有一套坚实的理论基础，为小样本问题的解决提供了一个统一的框架。由于SVM完备的理论基础和出色的学习性能，已成为当前机器学习界研究的新热点。SVM在模式识别方面最突出的应用研究是贝尔实验室对美国邮政手写数字库进行的试验[2]，试验结果表明SVM方法较传统方法有明显的优势。现今，SVM已成功应用于人脸识别、手写数字识别、文本分类、三维物体识别、多维函数预测等多个领域。

汽轮发电机组故障诊断在本质上是模式识别问题，应用多类支持向量机，结合遗传算法用于优化模型选择，建立了联合模型，通过对现场采集的故障样本进行试验，结果表明该模型能有效提高诊断准确率。



## 1 支持向量机理论

支持向量机方法是从线性可分情况下的最优分类超平面问题发展而来的。基本思想可用图1所示的二维情况来说明：圆和矩形代表两类样本，H为分类超平面，$\mathrm{H_1}、\mathrm{H_2}$ 平行于H分别为两类中离分类超平面最近的样本所构成的平面，它们之间的距离叫分类间隔（margin）。假设n个样本的训练集$\mathrm{D}=\left\{\left(x_{i},y_{i}\right)\mid i=1,2,\cdots,n\right\},x\in\mathrm{R}^{n},y\in[+1,-1]$ 能被一个超平面$w\cdot\mathrm{x}-b=0$ 没有错误地分开，并且离超平面

最近的向量与超平面之间的距离是最大的，则说训练集被这个最优超平面无错误地分开，保证了经验风险最小（为零）：使分类间隔的距离最大，保证推广性界的置信范围最小，从而使真实风险最小，使分类间隔最大实际上就是对推广能力的控制，这是SVM的核心思想$ 之一$ 



<div style="text-align: center;"><img src="imgs/img_in_image_box_106_239_394_410.jpg" alt="Image" width="28%" /></div>


<div style="text-align: center;">图1最优分类面</div>


要求分类超平面对所有样本正确分类，必须满足：

$$y_{i}\left[(w\cdot x_{i})+b\right]-1\geqslant0\qquad i=1,\cdots,n $$

此时，分类间隔等于2w，分类间隔最大等价于=$_\mathrm{w}\parallel$ 2最小。最优超平面就是满足上式并且使得$\Phi_{\mathrm{~(~w~)~}}=$ ‖${\bf\Pi}_{\mathrm{w}}\left\|{\bf\Pi}^{\mathrm{~\tiny~2~}}\right.$ 2最小的超平面，$\mathrm{H_{1},H_{2}}$ 上的样本点，即使式（1）中等号成立的点称为支持向量（SupportVectors)。

上述最优超平面的求解可以转化为求解一个典型的二次规划问题。



$$\left\{\begin{aligned}m in\quad&\Phi(w)=\|\mathbf{\Phi}_{w}\|^{2}/2\\ s\quad&y_{i}(w\cdot x_{i}+b)\geq1\end{aligned}\right.$$

此二次规划优化问题的解由下面的Lagrange函数的鞍点给出



$$\mathrm{L}(\mathrm{w},\mathrm{b},\mathrm{a})=(\mathrm{w}\cdot\mathrm{w})/2-\sum_{i=1}^{n}\mathrm{a}_{i}\left[\mathrm{y}_{i}\left(\mathrm{w}\cdot\mathrm{x}_{i}+\mathrm{b}\right)\right]$$

其中，$_{\mathrm{a_{i}}>0}$ 为拉格朗日系数。对于多数样本$\mathbf{a}_{i}$ 将为零，取值不为零的$\mathbf{a}_{\mathrm{i}}^{\mathrm{{\bar{\bar{\mathbf{a}}}}}}$ 对应于使式（1)等号成立的样本，即支持向量，它们通常只占全体样本中的很少一部分。

解上述问题最后得到的最优分类决策函数为：

$$\mathrm{D}(\mathrm{x})=\mathrm{sgn}[\mathrm{x}\cdot\mathrm{w}+\mathrm{b}]=\mathrm{sgn}\left[\sum_{i=1}^{\mathrm{n}}\mathrm{a}_{i}^{*}\mathrm{y}_{i}(\mathrm{x}_{i}\cdot\mathrm{x})+\mathrm{b}^{*}\right]$$

对于线性不可分情况，引入非负松弛变量$\xi_{\mathrm{i}}^{\mathrm{~\tiny~\geqslant~}}0,$ 式(2)变成：

$$\left\{\begin{aligned}\min\Phi(w,\xi)=\|\mathbf{x}\|^{2}/2+C(\sum_{i=1}^{n}\xi_{i})\\ \text{s}\xi_{i}\quad\text{y}(w\cdot\mathbf{x}_{i}+b)+\xi_{i}\geq1\end{aligned}\right.$$

_$\left\|\mathbf{\xi}^{2}/2+C\left(\sum_{i=1}^{n}\mathbf{\xi}_{i}\right)\right\|$ 取最小，是为了折衷考虑最少错分样本和最大分类间隔，就得到广义最优分类面。其中，$\scriptstyle\mathrm{c}\geq$ 0是一个常数，它控制对错分样本惩罚的程度。$ 广$ 义最优分类面求解与线性可分情况下几乎完全相同。

对非线性问题，可以通过非线性变换转化为某个高维空间中的线性问题，在变换空间求最优分类面，决策函数相应变成：

$$\mathrm{D}(\mathrm{x})=\operatorname{sgn}\left[\sum_{\mathrm{i}=1}^{\mathrm{n}}\mathrm{a}_{\mathrm{i}}^{*}\mathrm{~y}_{\mathrm{i}}\mathrm{K}\left(\mathrm{x}_{\mathrm{i}},\mathrm{x}\right)+\mathrm{b}^{*}\right]$$

其中，$\mathrm{K}(\mathrm{\boldmath~x_i,~}\mathrm{\boldmath~x_i~}$ )称为满足Mercer条件的核函数$[1]$ 。目前核函数的形式主要有4种：

(1)线性核函数：$\mathrm{K}(\mathrm{x}_{\mathrm{i}},\mathrm{x}_{\mathrm{j}})=\mathrm{x}_{\mathrm{i}}\cdot\mathrm{x}_{\mathrm{j}}$ 

(2)多项式核函数：$\mathrm{K}(\mathrm{x}_{\mathrm{i}},\mathrm{x}_{\mathrm{j}})=[(\mathrm{x}_{\mathrm{i}}\cdot\mathrm{x}_{\mathrm{j}})+1]^{\mathrm{d}}$ (3)径向基核函数：$\mathrm{K}(\mathrm{x}_{\mathrm{i}},\mathrm{x}_{\mathrm{j}})=\exp\left(-\frac{\left\|\mathrm{x}_{\mathrm{i}}-\mathrm{x}_{\mathrm{j}}\right\|^{2}}{2\sigma^{2}}\right)$ (4)Sigmoid函数：$\mathrm{K}(\mathrm{x}_{\mathrm{i}},\mathrm{x}_{\mathrm{i}})=\tanh[\mathrm{U}(\mathrm{x}_{\mathrm{i}},\mathrm{x}_{\mathrm{i}})+\mathrm{c}]$ 

## 2 基于支持向量机的多类分类器

支持向量机原本是用来解决两类的分类问题，对于多类问题，目前的解决方案主要分为两种：

一种是“all—together"多类分解算法[3]，这一算法以经典SVM为基础，重新构造多类分类模型，定义目标函数，对目标函数进行优化完成分类。该算法的目标函数非常复杂，优化计算困难。



另一种方案是通过构造多个二值分类器来实现分类。根据分类器构造方法不同，又分为$\mathrm{o n e\_a g a i n s t\_a l l^{[1]}}$ 和$\mathbf{o n e^{-}a^{-}}$ $\mathrm{{\bf{g a i n s t\bar{\phi}o n e}^{[4]}}}$ 。对于n个训练样本的k类分类问题，$\mathbf{o n e^{-}a^{-}}$ gainstall算法如下：构造k个二值分类器，第i个分类器用第i类样本作为正的训练样本，其余的所有样本作为负的训练样本，由此得到k个决策函数：对于一个未知的待判样本x 分别在上述k个二值分类器中进行分类，最后判给决策函数值取最大的那一类。one-againstone算法构造$\mathrm{k}(\mathrm{k}-1)$ 2个二值分类器，决策规则使用Maxwins即在上述$\mathrm{k}(\mathrm{~k~}\mathrm{~-~}1)$ /2个二值分类器中使用投票法，得票最多的类即为样本x所属的类。Platt对Maxwins决策规则进行修改，构造一个DDAG （Decision Directed AcyclicGraph）来决定样本x所属类别，提出了$\mathrm{D A G S V M}^{\mathrm{~[~5~}}$ 算法。



$\mathrm{C h i h-J e n~L i n^{[6]}}$ 通过试验对one-againstalloneagains one和DAGSVM进行了比较，结果指出one-againstone和DAGSVM更适合于实际应用，one-againstone在样本训练、测试时间及预测准确率上比其它两种方法好。

## 3 GA—SVM联合模型及其在实际机组故障诊断中应用方法的研究

### 3.1 GASVM联合模型

采用SVM进行分类时，通常是人工对模型进行选择，导致相同的问题得到的分类结果可能相差甚远。此外，在模型确定以后，模型参数（损失参数C核参数gama多项式核参数dgree等)的选择对分类结果影响也很大。$\operatorname{C h i h}-\operatorname{J e n}\operatorname{L i n}$ 提供的LIBSVM采用网格法结合交叉验证$\mathrm{(C r o s s-V a l i d a-}$ tion)方法对分类器模型参数进行选择。



本文采用了遗传算法用于SVM模型及模型参数的选择，建立了$\mathrm{G A}\mathrm{\text--}\mathrm{S V M}$ 联合模型，并利用$\mathrm{U C I^{[7]}}$ 标准样本集对联合模型进行检验，结果表明分类准确率得到了较大的提高。



遗传算法（GeneticAlgorithms）是60年代后期JH.Hol land首先提出的一种改进的优化算法，通过模拟生物界的进化现象（优胜劣汰，交叉，变异等），达到全局搜索寻优的目标。目前遗传算法已被广泛应用于优化、控制等领域。

结合遗传算法的标准操作过程，，$\mathrm{G A}\mathrm{~\text--~}\mathrm{S V M}$ 算法的4个

基本步骤为：

（1）对模型参数进行编码，建立初始种群。采用二进制进行编码，编码总长度为23位，共4个基因段，分别为2位、10位、8位和3位二进制串，对应于模型类别tC、gama和degree4个参数。初始种群个数为50。



（2）计算种群中各个体的适应度。根据（1）中编码的定义，对各种群个体进行译码，以译码后得到的值作为分类器模型参数，利用该分类器对学习样本进行训练，以学习样本的10重交叉验证识别率作为个体的适应度。

（3)根据生物界遗传规律，执行下列操作，生成新的种群：选择（Selection）。从当前种群中选择适应度高的优良个体；复制$(\mathrm{R e p r o d u c t i o n})_{\circ}$ 将优良个体复制后添入新的种群中，删除适应度低劣质个体：交换（Crossover)。按照某种规律选择2个个体，将它们的部分二进制编码进行交换，产生新的个体并添加到新的种群中：变异（Mutation）。随机地改变某一个体的编码，产生新的个体并添加到新的种群中。

（4)以种群最大适应度收敛或以指定迭代次数为结束，反复执行23步骤。选择最佳个体作为遗传算法的结果，对应的SVM模型即所求的最优分类器。



### 3.2 $\mathsf{G A}^{-}\mathsf{S V M}$ 模型与SVM的分类结果比较

为了验证$ GA-SVM$ 模型的有效性，选取了部分UCI标准样本对$ GA-SVM$ 进行测试，并与采用网格法选择模型参数的SVM(采用one-againstone)相比较，10重交叉验证识别率如表1所示。



<div style="text-align: center;">表 1SVM与GA-SVM分类结果比较</div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td rowspan="3"></td><td colspan="2">SVM</td><td colspan="2">$\mathrm{G A}\mathrm{\text--S V M}$</td></tr><tr><td>(1 C, gam a)</td><td>识别率</td><td>(1 C, gam a)</td><td>识别率</td></tr></thead><tbody><tr><td>Iris</td><td>) $(\mathrm{2,~2^{12},~2^{-9}~})$</td><td>97.333%</td><td>(1,3749. 21,0.16549)</td><td>98 67%</td></tr><tr><td>Wine</td><td>X $(\mathrm{2,~2^{7},~2^{-10}})$</td><td>99. 438%</td><td>(2,23,0.007575)</td><td>99. 438%</td></tr><tr><td>G lass</td><td>$(\mathrm{\it 2,2^{11},2^{-2}})$</td><td>）71.495%</td><td>(2,26503,0.2173)</td><td>74.766%</td></tr><tr><td>Vowel</td><td>$(\mathrm{\boldmath~2,~2^{4},~2^{0}~})$</td><td>99.053%</td><td>(2,15.509,0.8686)</td><td>99. 62%</td></tr></tbody></table></body></html></div>


由表1可以看出，采用$ GA-SVM$ 选择优化模型后，分类器识别率得到了提高。



4种样本训练时间与采用网格法相当或略有增加，考虑到SVM一般是作为离线训练，加上实际机组故障诊断应用中样本维数较低，这种影响不大。



### 3.3 GA-SVM在实际机组故障诊断中的应用

在上述对$ GA-SVM$ 模型和参数选择优化的研究基础上，进而采用实际机组现场测试的振动记录信号，对汽轮发电机组3种常见振动故障（不平衡、动静碰磨、油膜振荡）进行诊断分类，然后与3层BP神经网络的识别结果进行比较，以确定$ GA-SVM$ 方法诊断的效果与精度。

研究所采用的现场3种故障振动波形信号来源和它们对应的故障分别为：

（1）Y电厂2号机组（600MW）3号轴振，质量不平衡，故障代号为1；

（2）M电厂2号机组（50MW）2号轴振，油膜振荡，故障代号为2；

（3）D电厂1号机组（350MW）3号轴振，动静碰磨，故障代号为3。



这3种信号所对应的故障类型，是根据实际处理后的结

论而确定的。处理的结论，又来自于作者实际参与的处理前期分析判断、处理措施及效果。因而，上述3种信号与它们各自的故障是一一对应的。



故障的学习样本和待识别样本的特征选为6维向量，为经过归一化处理的频谱：



$\left(\left(0,01\sim0,4\right)f_{1},\left(0,4\sim0,9\right)f_{1},f_{2},\left(1\sim2\right)f_{1},2f_{2},3f_{1}\right)$ 其中，为工频。



对上面3种振动故障记录信号各取出不同时刻的50组记录，再将每种中的30组信号作为模型训练样本，另20组作为待分类的试验样本。



采用$ GA-SVM$ 的分类试验结果表明：在$t=2,\quad\mathrm{gama}=$ $025,\mathrm{C}=2$ 0时模型最优，对应的10重交叉验证识别率最高，得到的试验样本分类结果如表2所示。

<div style="text-align: center;">GA-SVM分类结果</div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td>故障类型</td><td>故障1</td><td>故障2</td><td>故障3</td></tr></thead><tbody><tr><td>故障1</td><td>20</td><td>0</td><td>0</td></tr><tr><td>故障2</td><td>0</td><td>19</td><td>0</td></tr><tr><td>故障3</td><td>0</td><td>1</td><td>20</td></tr></tbody></table></body></html></div>


为了做对比性分类试验，将完全同样的故障样本输入到采用LevenbergMarquardt学习算法的3层BP神经网络进行训练。神经网络隐含层神经元个数取为5，输出层神经元个数为3.变换函数取tansig函数。然后对与采用$ GA-SVM$ 的分类试验同样的20组试验样本进行识别，分类结果如表3所示。



<div style="text-align: center;">BP神经网络分类结果</div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td>故障类型</td><td>故障1</td><td>故障3</td><td>故障3</td></tr></thead><tbody><tr><td>故障1</td><td>20</td><td>0</td><td>0</td></tr><tr><td>故障3</td><td>0</td><td>18</td><td>1</td></tr><tr><td>故障3</td><td>0</td><td>2</td><td>19</td></tr></tbody></table></body></html></div>


从表2表3可以看出，采用$ GA-SVM$ 模型进行故障分类时，60个试验样本中仅有1个样本发生错分，将动静碰磨错分为油膜振荡，识别准确率达到9833%；而采用3层BP 神经网络进行分类时，有2个动静碰磨故障被错分为油膜振荡，1个油膜振荡故障被错分为动静碰磨，准确率为95%。

上述的试验结果初步表明：$\mathrm{G A}\mathrm{~\text--~}\mathrm{S V M}$ 模型用于汽轮发电机组故障诊断时，可以获得比较高的故障识别率，识别效果优于神经网络故障诊断模型。



## 4 结论

支持向量机是建立在结构风险最小化原则的基础之上，在保持经验风险最小的同时，最小化置信范围，适应于小样本集的训练学习，具有较强的泛化性能和模式识别能力。

采用遗传算法建立$ GA-SVM$ 模型，将其应用于汽轮发电机组的故障诊断，对现场采集到的3种不同故障信号的小样本进行试验，取得了满意的效果。与BP神经网络的对比试验进一步表明$\mathrm{G A}\mathrm{\text--}\mathrm{S V M}$ 可以获得较神经网络更高的故障识别率。这些结论表明了SVM在汽轮发电机组故障诊断领域具有很好应用前景。(下转第16页)

<div style="text-align: center;"><img src="imgs/img_in_chart_box_46_103_454_316.jpg" alt="Image" width="40%" /></div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_548_104_952_316.jpg" alt="Image" width="40%" /></div>


<div style="text-align: center;">图4$\delta=0245\mathrm{m m}$ 时，静态应力分布情况</div>


<div style="text-align: center;">图5$\delta=0245\mathrm{m m}$ 时，动态应力分布情况</div>


<div style="text-align: center;">表 1</div>


<div style="text-align: center;">不同过盈量下，静态和动态的计算结果</div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td rowspan="2">计算结果</td><td colspan="2">静态</td><td colspan="2">动态</td></tr><tr><td>$\delta=0175mm$</td><td>245mm $\delta=0$</td><td>$\delta=0175mm$</td><td>$\delta=0245\mathrm{m m}$</td></tr></thead><tbody><tr><td></td><td></td><td></td><td></td><td></td></tr><tr><td>轴外表面（目标面）上的VonMises应力：MPa 叶轮内表面（接触面）上的VonMises应力，MPa 轴与叶轮的接触情况 接触情况 $\left(u_{x}\right)_{ 轮 }-\left(u_{x}\right)_{ 轴 }$</td><td>轴外表面（目标面）上的VonMises应力：MPa</td><td>58.2 189 $0.127\;8-(-0.045)$</td><td>89.4 264 $178-(-0.0633)$</td><td>8.85 308 02477-000746 松脱 $0.24024>0.175$</td></tr><tr><td>02477-000746</td><td>0.2504—0.0064</td><td></td><td>=0.172 接触</td><td>接触 $=0\;241\;3$</td></tr><tr><td>接触情况</td><td>松脱</td><td>临界状态</td><td></td><td></td></tr></tbody></table></body></html></div>


情况最大值为$271\mathrm{{\tt M}Pa}$ 发生在叶轮的接触面附近。此时$\left(\mathrm{u}_{x}\right)_{轮}-\left(\mathrm{u}_{x}\right)_{轴}=0.2504-0.0064=0$ 244≈0.245,处于临界状态，只有增大过盈量才能保证不松脱。

（3)两种过盈量下，静态和动态的计算结果如表1所示。

## 4 结论

提出的基于有限元软件ANSYS利用接触单元对叶轮、轴过盈联接进行分析的方法，可以精确反映叶轮、轴在一定过盈量下静态和动态的接触面间的受压情况和各自的应力分布情况。和传统的二次应力法相比，所得结果更加符合实际和可靠。



（1)对套装转子中叶轮与轴的过盈配合分析计算表明过盈量是影响接触面附近应力的主要因素，若过盈量过大，则有可能使静态时接触面附近的过盈应力过大，使叶轮内孔开裂；若过盈量过小，则有可能使动态时接触面间的过盈不足，叶轮与轴发生松开。故设计时应严格控制过盈量，以保证装配质量，降低静态时接触面附近的应力集中和保证动态时接触面的紧密配合是设计的关键。



(2)按传统的设计方法，过盈量取轴径的1.1%~1.8%进行设计，存在一定的盲目性，因为接触面附近的应力分布

## (上接第3页）

## 参考文献

[1]Vapnik V. N. Statistical leaming theory[M].New York: Wiely,1998
[2]VapnikV.N.张学工译，统计学习理论的本质[M].北京：清
华大学出版社，200Q 
[3]Weston JWatkins C Multi-class support vector machines[A]
Proceed ings of ESANN99 C.Bmssel1999.[4] U. KreBel Pairwise classification and support vector machines [M]. Advances in Kemel Methods-Support Vector Leaming 

与接触情况，不仅与轴径有关，还与工作载荷有关，从表1可知：若按轴径的11%决定过盈量，则动态时过盈不足，要发生松脱，按1.5%0设计，则静态时接触面间的应力过大，强度不足，可能使内孔发生开裂，此时不能再增加过盈量，若按1.8%0设计，情况更加危险。故设计时要具体问题进行具体分析。



（3)从以上分析过程中可知：有限元分析可以全面而精确地反映叶轮与轴配合面间的接触情况和应力场的分布，对于叶轮和轴的过盈联结设计具有较大的指导意义。

## 参考文献

[1]吴厚钰，透平零件结构和强度计算[M]．北京：机械工业出版社，1983
[2]WEILI,G. P STEVEN. Shape design for two—and three-dimensional con tact prob lems using an evolu tionary m ethod[J]. In temational Joumal of Conputational Engineering Science 2001,2(2):181-198
[3]赵华，尹辉.各种柱筒与轴的过盈配合分析[J]，石油机
械，1998(2）:7-10
[4]陈道礼，过盈联接的有限元分析[J].机械设计，2001（2）:46~48


255-258,M TPress Cambridge M as-sachusetts 1999.[5]Platt JC，CristianiniN.，Shaawe-Talor J Large margin DAGs for mu ltic lass classification [M. Advances in Neural Infom ation Processing Systems Volume 12MIT Press 200Q.[6]Hsu C W..Lin C J A Com parison ofmethods formulticlass sup port vectormachines[M]. Taipei National Taiwan University [7]C L Blake and C JMer UCIrepository ofmachine leaming da tabases[R]. Irvine CA:University of Califomia Deparmentof Infom a tion and Com puter Science 1998