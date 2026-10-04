

文章编号：1004-132X(2001)07-0800-04

# 基于多Agent的汽轮发电机组故障诊断系统

邱忠宇王一欧顾晃吴昭同

摘要：介绍了多Agent诊断系统的总体结构及组成部分；探讨了多Agent诊断系统中的若干关键技术，在知识表达、通信协调、诊断方法等方面提出了一些新的思路，以基本知识单元及Agent诊断知识类为基础，通过系统的通信协调机制可以进行面向故障类型的模糊规则诊断；经过实践检验，系统诊断的结果是正确的。


关键词：故障诊断；多Agent；汽轮发电机组；知识表达

中图分类号：TH165.3;TP206.33文献标识码：A 

<div style="text-align: center;"><img src="imgs/img_in_image_box_771_202_892_406.jpg" alt="Image" width="12%" /></div>


邱忠宇博士

## 1 多Agent诊断系统的总体结构

### 1.1 多Agent 系统

"Agent"有"主体"、"智能体"、"代理机"等含义[1]，多Agent系统中的Agent通常被认为是在一定的环境下能够持续自主地运行的实体，它既可以完成某个子任务，又可以与其它Agent合作完成给定的任务。Agent之间在追求局部目标时直接或间接通信，全局目标的实现是单个Agent 相互协作的结果，Agent在尽力获得局部利益时，它的目标没有必要与整体相联系，即Agent可作为一个自治的独立实体存在于整个系统中。

多Agent系统的主要特点如下[2:①自治性。每个Agent可以解决自己局部子系统的问题，可以动态响应外部环境的变化，并且可以实现同其它Agent之间的协调。②通信能力。Agent之间可以互相通信，获得自己所需的信息，解决自己局部不能解决的问题。③高度柔性。可以动态重组以适应不同需求，可以通过添加和删除更新系统。④智能性。Agent具有知识，可以根据自己的知识解决问题。



### 1.2 系统框架

对于汽轮发电机组这样复杂的系统，其故障具有不均匀性、渐进性和并存性等特点，其故障原因与征兆之间的因果关系错综复杂，而且在监测诊断过程中存在着许多并行和协作机制，如监测与诊断的并行与协作，诊断与诊断的并行与协作等，所以很难对整个诊断空间建立起一个通用诊断模型，需要将故障诊断任务划分成相应的子问题，根据各个子问题的性质和特点，采用相应的诊断方法来处理。

设备故障诊断任务的分解有许多种方法，如基于设备结构和功能，基于工作状态和基于诊断过程等。根据汽轮发电机组故障诊断的特点，按照多Agent理论进行建模，笔者提出了基于多Agent的智能诊断体系结构（见图1)，这种结构把传统的多故障综合诊断化为了面向故障类型的多Agent分模块诊断，每个诊断Agent针对一种特定类型的故障（这里我们只讨论轴系振动故障)，它具有自己的任务.求解知识及过程，诊断机制更加灵活、准确，而且易于修改、扩充，即修改其中一个Agent，并不影响其它Agent的结构。

<div style="text-align: center;"><img src="imgs/img_in_image_box_501_899_922_1237.jpg" alt="Image" width="44%" /></div>


<div style="text-align: center;">图1多Agent诊断系统结构图</div>


在多Agent诊断系统中，系统管理Agent、诊断Agent和功能Agent是系统中的3种不同性质的Agent。系统管理Agent是进行任何诊断任务的第一步，是系统运行的基础，它主要负责诊断系统中Agent的任务分配、管理与协调，体现了系统诊断的思路与策略。诊断Agent真正完成各

个子故障的诊断，确定整套设备的状态好坏。功能Agent则协调系统管理Agent完成一系列任务，如用户交互、征兆获取等。通信Agent作为一种特殊的功能Agent在本系统中被单独提出来，它是整个系统运行的核心，所有Agent之间的协作和交互都要通过它来进行，它管理着系统全局数据区。



### 1.3 组成部分

(1)系统管理Agent系统管理Agent由系统检测器、任务分配器、系统调度机构成其核心操作模块，配合信息处理及通信接口、局部黑板构成了1个整体。这里采用了3种子任务分类方法，基于规则的元知识分类，如按照振动频谱的分布可分为低频类、基频类、倍频类和高频类；基于模糊隶属度的综合评判分类；基于模糊神经网络的分类。然后对3种分类的结果求并集，列出所有的候选故障集，再发送信息启动相应的诊断Agent进行诊断。



（2）诊断Agent诊断Agent可根据诊断对象工作的不同阶段和不同的诊断方法来组织其结构。考虑到汽轮机发电机组故障原因的复杂性以及表现征兆的不确定性，不同故障很难用同一种算法来进行推理或网络识别，因此笔者采用了面向故障类型的诊断Agent结构，诊断Agent结构包括以下几个部分：①信息处理机。接受和发送信息，并对信息进行处理与转发。②征兆表征。包括各种数据分析、图形处理的结果，与该故障产生有关的因素都可包含进来，构成广义征兆表征。③智能诊断结构。包括专用的知识库或神经网络结构等。④协调调度机制。设置诊断的调度顺序，定义如何根据规则推理或符号处理的要求去获取相应征兆，并调用相应算法进行诊断。③结果综合与评价。各种方法诊断结果的综合处理。⑥故障事例库。通过故障发生时的数据记录和历史经验的学习，动态生成的各种状态下的故障事例。⑦局部黑板。存储所有中间过程及征兆值。

(3)功能Agent功能Agent协调管理Agent工作，及时处理通信Agent传来的信息，进行一些常规功能调用，如用户界面交互、征兆获取等，这是一类不受应用对象影响的工具Agent。

通信Agent作为一种特殊的功能 Agent在多Agent诊断系统中有着举足轻重的作用，它所采用的通信方法和策略，是整个系统运行的桥梁。本文采用一个信息集中传递Agent模块来管理所有Agent的通信[]，通信Agent对所有其它A gen中面晶共的t维护着chn的功能信息库，每个新加入系统的对象实体都要向通信A gent注册其功能服务信息，即各个Agent只与通信Agent建立直接通信链接，而再由通信Agent 通过查询功能服务信息库来建立与目的对象Agent 的通信链接。



多Agent诊断系统中的信息流见图2。

<div style="text-align: center;"><img src="imgs/img_in_image_box_498_257_924_747.jpg" alt="Image" width="44%" /></div>


<div style="text-align: center;">图2多Agent诊断系统信息流图</div>


## 2 多Agent诊断系统的关键技术

### 2.1 知识表达

基于多Agent的智能诊断系统以故障为对象单位将事实性知识、经验性知识、控制性知识和过程性知识分别封装在一个个相对独立的Agent 实体中，每一Agent对象可以选择独特的推理、映射机制，使得我们可以很方便地将规则、隶属函数和神经网络等多种知识表示方法有机的统一于一个Agent结构中，形成各个Agent的知识对象。各知识对象都有自身的推理控制机构，它们之间的相互联系都是通过信息的传递来实现，而不存在"控制"的不一致性和不统一性。

汽轮发电机组的运行状态和很多因素都有关系，因此，基于多Agent的故障诊断系统的知识表示也与很多因素有关。我们把和机组故障产生有关的因素都统称为基本知识单元，这样的知识表示方法定义了诊断知识的最小粒度，具有完备性和统一性。根据大量的资料和领域专家的意见，并考虑到知识表达的开放性和继承性，把汽轮发电机组故障基本知识单元分为5大类，10多个小类，100多个具体项，每一类分别反映了汽轮发电

机组的不同状态特性(见图3)。

<div style="text-align: center;"><img src="imgs/img_in_image_box_16_106_447_339.jpg" alt="Image" width="45%" /></div>


<div style="text-align: center;">图3基本知识表示单元分类</div>


在基本知识单元的研究基础上，笔者提出了一种面向多Agent诊断的知识表达方法--Agent 诊断知识类(agent diagnosis knowledge objectclass，ADKOC)。Agent诊断知识类以多种知识表示和面向对象思想为核心，综合了诊断的深层知识及模型知识，有很强的知识表达能力。

ADKOC的CLASS抽象结构定义如下：CLASS{



CLASS_NAME；//诊断知识类的名字

CID;//诊断知识类的标识

PARENT;//诊断知识类的父诊断知识类的名称



ATTRIBUTE；//诊断知识类的属性

METHOD;//诊断知识类的知识表示方法



VARIABLE;//诊断知识类所有诊断对象共享的变量



ROLE;//诊断知识类同其它诊断知识类的关系



CONSTRAINT，//诊断知识类的属性之间的语义约束



### 2.2 通信协调机制

诊断系统内各Agent之间的合作可分为纵向合作和横向合作[4]。纵向合作关系如下:系统管理Agent发出信息启动诊断Agent、诊断Agent 综合评判决策后决定Agent的具体执行方式等。横向合作关系如下:管理Agent及诊断Agent分别与功能Agent的交互，根据需要获取征兆信息;诊断Agent之间互相传递信息，当一诊断Agent诊断失败或中止时，可发出信息触发其它诊断Agent。



笔者以ACL(agent communication language)通信语言为参考标准定义了一套多Agent间的信息传详机制信息可分为如下i类：一类在.802.



Agent内部传递和处理的信息，称为内部信息；另一类在Agent之间传递和处理的信息，称为外部信息，外部信息的传递通过通信Agent来实现。通信Agent中的信息控制采用信息黑板结构，分为入信息黑板和出信息黑板，由收发成员函数对信息进行管理，信息黑板的定义如下：

CLASS MESSAGE_QUEUE{

$\mathrm{L I S T}<_{\mathrm{M E S S A G E}}>\mathrm{{\mathrm{{\mathrm{{\scriptsize~*~}}}}}_{\mathrm{\scriptsize~r b o a r d}}};$ ；//入信息黑板



$\mathrm{L I S T}<_{\mathrm{M E S S A G E}}>\mathrm{{\mathrm{{\mathrm{{\scriptsize~*~}}}}}_{\mathrm{s b o a r d}}}$ ；//出信息黑板



MESSAGE*smsg；//正在发送的信息

### 2.3 诊断方法

对于诊断Agent来说，它接收到管理Agent 传来的信息后，对当前系统的状态、征兆特征及诊断要求建立一个模糊评价模型，这个模糊评价模型具有自学习与存贮功能，根据这个模型分析的结果，选用相应的策略与算法。目前提供了2种算法，模糊规则类和神经网络。



模糊规则类是在模糊集理论的基础上提出的一种面向故障类型的规则结构。每类故障都被模型化为一个诊断Agent，这个Agent中的知识表示被抽象为故障知识类，领域知识中与该故障目标有关的规则组成一个类规则集，按照知识的继承和派生关系形成了一系列的规则链，每条规则表示为一个对象实例。关于规则的数据结构与关于规则的操作封装成一个实体，形成一个独立运行的知识模型，推理过程中采用收敛控制算法和波动事务处理算法[5完成整个推理过程。

规则类结构可定义为如下格式：

CLASS RULE 

{ATTRIBUTE:Symptom//类中的征兆说明Number//规则号ActiveTag//规则激活标志Fact//用户证据值(事实)Reasoning Direction//推理方EMY 



向

RULE:Condition//前提

Result//结论

CF//结论可信度

Point//下一条规则指针

METHOD:Acquisition//询问证据

Algorithm//推理或计算



每个规则类由属性和规则以及方法3部分组

成，其中属性用来描述与该类有关的事实；规则用来描述具体的规则实体，包括前提、隶属度、结论、可信度等；方法描述了证据、征兆获取的方式以及与推理计算有关的算法。如何确定一个类中的具体规则，其主要依据是属于该类的规则中各个征兆及前提的逻辑关系，对具有与关系的某类征兆或前提，把它们全取为同一规则的条件，对具有或关系的征兆或前提，让它们都分别单独作为一条规则的条件，并支持同一结论。



在征兆信息不够、慢变量信号不易获取的情况下，诊断Agent采用Rule型模糊联想记忆(FAM）网络诊断模型，结合传统的BP网络算法形成辨识当前故障Agent状态的子网络结构，它仅有一个输出及相对较少的输入。



诊断Agent的学习机制中包括规则向诊断网络结构的转化、诊断事例的记忆存贮及诊断Agent的自适应调整等。



## 3 应用实例

某发电厂2号机组安装了本系统，运行至1998年8月11日，系统维护员在例行检查系统中，发现系统诊断模块有被触发的标志，马上检查现场和历史分析诊断记录，发现最近一段时间的频谱和波形有些异常，而且系统诊断提示可能有松动类故障存在。由于系统设置是人工控制精确诊断状态，有故障隐患时提示报警，系统维护员立即触发松动Agent诊断模块。系统根据机组信息及获取的征兆启动了面向Agent的规则诊断，经过模糊规则匹配推理，提示可能是螺栓松动故障，请求技术人员进行检修。技术人员赶到现场，发现1号轴承箱盖水平结合面扩建端螺栓的确松动，拧紧螺栓后返回控制室，系统故障警告没有了，频谱、波形也趋于正常，可见系统诊断是正确的，其诊断流程见图4。



<div style="text-align: center;"><img src="imgs/img_in_image_box_94_637_863_1089.jpg" alt="Image" width="80%" /></div>


<div style="text-align: center;">图4 多Agent诊断流程图</div>


## 参考文献：

[1]周永林，潘云鹤·面向Agent的分析与建模.计算机研究与发展,1999,36(4):410～416[2]Wooldridge M,Jennings NR·Intelligent Agents:Theory and Practice· The Knowledge Engineering Review.1995,10(2),115~152[3]林守勋，林宗楷.多Agent协同工作环境MACE·计
算机学报，1998,21(2):188～192[4] Stephen T C W·Coping with Conflict in Cooperative Knowledge − Based Systems·IEEE TRANSACTIONONSYSTEM，MANANDCYBER中国知网1http//W.cnki.net 

[5]李龙澎，程慧霞.一种面向对象产生式系统的体系结构和规则模型.计算机研究与发展，1997，34(6)：415~420



(编辑 马尧发)

Abstract:A new method is presented to solve the open architecture problem and to improve the reliability of CNC system by using softw are reuse and component technology in this paper· At first,the feasibility of developing CNC system with software component is discussed,and the conception of CNC softw are components and the integrated and normative description of the component are also offered· Under this condition, this paper introduces a method for the analysis of reuse and the common principles that should be follow ed in the process for developing CNC systems with softw are component technology·Then the steps for developing softw are CNC system is described from the points of view of a developer and a consumer respectively· In the end, an example demonstrating the specific implement of this kind of thought is shown·This method is proved to be effective by developing a prototype example 


Key words: CNC system softw are component reuse open architecture 

Dynamic Optimal Control of Redundant Robot Based on Neural Network MAGuang(Mechanical Engineering College of Wenzhou University, Wenzhou, China) CAI Hegao p 787-789



Abstract:The motion control for redundant robot is still the focal point for the researchers· In this paper,we investigate the problem about the dynamic optimal control of redundant robot in order to obtain good dynamic performance and track precision·A global optimal method is used due to the limitations of the local optimal on method·Based on the global optimization idea, the algorithm about the dynamic optimal control of redundant robot is presented· Owing to the difficulty for resolving the control algorithm,a neural network is used to approach the complex nonlinear function in the algorithm and then the resolution becomes simple· Simulation resultsverifythegooddynamicperformance,quick operation and the feasibility of engineering application about thecontrol algorithm 


Key words:redundant robot optimal control neural netw ork algorithm 

Research on Capital Flowing Management System for New Product Development WANG Xu( Chongqing University，Chongqing,China)ZHOU XiuliWANG Gaolou WANG Fengchun p 790-793

Abstract:In order to decline risk and reduce product cost, the paper provides a definition of the system model of New Product Development(NPD)· First,the proceeding of NPD Capital Flowing M anagement( CFM S) is analyzed and the concept model which is based on the mode of CE(current engineering) is proposed·Secondly,the function model of (CFM S) is established· Method of assigning target cost and dealing with accounts is provided·Finally,the characteristics of CFMS and the relationship between CFMS and traditional svstem are described 

中国知网：nemttpsdwwwlepknet capital LV .



flowing management ABC accounts costing 

Research on Structure Analysis of Platen of Locking Mechanism in Die- Casting Machine Based on Artificial Neural Network ZHAO Han (Hefei University of Technology,Hefei China) CHEN Ke KE Zunzhong p 794-796



Abstract:During structure analysis of platen of locking mechanism in die− casting machine, an artificial neural netw ork for the structure analysis is trained by a small number of finite element analysis samples， due to the nonlinear mapping ability of artificial neural network·This artificial neural network is able to predict the structure analysis' results with respect to different structuresThis strategy solves the bottleneck problem of structure optimum design —- the contradiction between the fast iteration of optimum algorithm and finite element analysis large number of calculations· This strategy is appliedto design a platen of locking mechanism in die- casting machine· The results show that this method is of validity 

Key words: artificial neural network structure optimum design  mechanical optimum design finite element analysis die−casting machine 

Research on CBR Based Cold Forging Process Planning 

LEI Yonggang(Shanghai Jiaotong University，Shang hai，China） PENG YinghongRUAN Xueyup 797799



Abstract:Following the analysis of the deficiency of rule-based reasoning based cold forging process planning expert system and numerical simulation based cold forging process planning system, a case - based reasoning based cold forging process planning system model is proposed, and several key points including feature − based part representation, logical hierarchical process plan model,hierarchical retrieval model and knowledge based multiple cases integrated case adaptation model are given 

Key words:case−based reasoning cold forging computeraided process planning expert system 

Multi-agent- based Fault Diagnostic System for Turbo generator QIU Zhongyu( GE Lighting Technical Cn nter,Shanghai, China) WANG Yiou GU Huang WU Zhaotong p 800-803



Abstract: Based on turbogenerator fault diagnostic system,a multi−agent − based fault diagnostic technique is proposed, as well as it s general structure and component parts are analyzed· With knowledge representation,transmission coordination,diagnostic method and soon being concerned， multi — agent diagnostic system's key technigue is discussed, and a series of new ideas and methods are put forw ard· According to such ideas, system is developed and corresponding diagnostic case study has been used to verify the proposed scheme·

Key words:fault diagnosis multi−agent turbogenerator knowledge representation 