

# 发电设备RCM实施方法的研究与探讨

刘晓锋，陆颂元

（东南大学，振动控制与信息系统研究所，南京210096）

摘要：分析了影响RCM实施的障碍，结合我国发电企业的实际提出了发电设备RCM操作性强的实施方法。建议在健全和完善各种先进维修技术的基础上实施RCM，通过维修评价反馈RCM分析所需要的信息，动态实施RCM：以CMMS作为数据存储和管理平台，论述了建议的RCM和CBM与CMMS数据交互方式，提高RCM项目的实施效果。


关键词：可靠性维修：状态维修：计算机化维修管理系统：实施方法：发电设备

分类号：TK268文献标识码：A 文章编号：1001-5884（2005）04-0244-04

# Research and D iscussion on Im p lem en ta tion S tra tegy of G enera ting Equ ipm en ts'RCM 

LIU X iao-feng LU Song-yuan 

(SoutheastUniversity Vibration Control and Infom ation System Institu te Nanjing 210096, China)

## Abstract
 Obstacles that affect the implementation approach of RCM have been identified Based on the analyzed results and characters of native power plants the effective implemen ta tion approach of RCM was put forw ard The proposed solution based on the perfectness of various m ain tenance strategies is to im plem ent dynam ic RCM with the feedback info m ation by m aintenance assessm ent; based on CMMS which stores and m anages corre lative data the system architecture of the RCMand CBM based CMMS in tegrated so lu tion was proposedto acce lerate imp lemen tation of RCMproject 

KeywordsRCM;CBM ;CMMS;implem en tation stra tegy;generating equipm en ts 

## 0前言

以可靠性为中心的维修（ReliabilityCenteredMainte nanceRCM），是一种先进的维修优化方法，用于分析设备的维修需求，决策最佳的维修方式。RCM的特点在于它提供了一种系统的框架，能够将不同的先进技术融合在一起，包括新的决策支持工具，如FMEA，新的维修技术，如定期视情作业、定期检修、隐患检查、必须重新设计等。成功的经验已经表明，实施RCM能够提高设备的可利用率和可靠性，保证设备安全高效运行，同时使维修工作量和维修经费大幅减少。



从实施效果来看，RCM实施中应该优先考虑的问题之一是提高具体工作人员对标准形式RCM的掌握程度和实施能力，然而这需要大量的人力、物力资源投入，并且难于组织管理。已经有案例，RCM在电力、加工制造等行业实施时遇到了困难，甚至一些单位最终放弃了这一计划。本文针对我国电力系统特点，论述实施RCM的障碍，以及RCM同各种维修技术及CMMS的有机集成，最后提出了建议的发电设备RCM实施方法，供实施RCM的相关人员参考。

## 1 实施RCM的难点和评估准则

在掌握了RCM的内容、优势后，准备着手实施前，还应

该了解实施RCM项目的难点和实施成功的评估准则是什么，它涉及RCM本身的技术难点，以及RCM项目组织管理方面的困难，也关系到进行该项目所追求的具体目标应该是什么。



### 1.1 RCM技术本身的难点

#### 1.1.1 发电设备故障模式分析是一项消耗人力、物力和时间的工作

故障模式分析是RCM中的主要工作内容之一。由于发电设备的复杂性和多样性，故障模式的种类繁多，对一个企业来说，经验丰富的故障模式分析工程师十分缺少。因此，故障模式分析是实施RCM中的一个难题。再者，根据国外对实施RCM工作的统计，实施过程中，仅仅完成系统划分，功能、性能标准的定义，就占RCM分析总工作量的约30%[1]，而此时的工作还未涉及到具体维修活动的决策，只是对于实现RCM项目的长远目标是有益的，对于当前的维修需求还没有产生直接的作用。



#### 1.1.2 RCM要求实施者全面掌握各种先进维修方式

RCM具体的维修活动实施是在故障模式和后果分析（FMEA）维修方式逻辑决策后开始的。这种维修活动滞后于维修决策的状况给RCM分析带来了困难：第一，RCM分析中FMEA需要的维修技术数据可能是不全面的，如平均故障时间（MTBF）、P一F间隔和维修费用、工时等：第二，不利于分析者确定故障模式的分析级别。针对于每一功能故障，故障模式的列举是分级别的，分析级别的确定原则是：在这

一级别上分析故障模式时，可以定义和选择正确的故障维修方式[2]。这就要求分析者必须熟悉各种维修方式，具备在分析时权衡各种维修技术的能力。



### 1.2 RCM的组织管理方式

采用RCM优化维修需要将企业内的设备进行分级，对于不同级别的设备采取不同的维修策略、不同的维修间隔和维修规模。对于这样复杂的管理、协调工作以及在维修决策过程中对大量复杂数据的统计分析，仅仅依靠传统的纸笔管理方式是无法满足要求的，必须求助于高水平的计算机化维修管理系统（CMMS），CMMS可以充分发挥计算机在信息处理上的优势，满足RCM项目管理的需求。电力企业应该将RCM的实施与CMMS的实施同时考虑，为RCM提供数据存储、数据管理等先进的技术支持手段。



### 1.3 国内缺乏RCM实施效果的评估准则和实施指南

### 1.31 RCM实施成功的评估准则

让企业的领导层、管理层和RCM的实施者看到RCM计划的收益和可行性，是推动RCM实施的动力。目前，我国火电系统中RCM实施的效益还没有被定量地论证，同时也缺乏真正成功的应用经验。1984年，美国电科院（EPRI在核电站刚开始推广这项技术时，就论证RCM的有效性。1988年，在罗切斯特气体厂和吉纳核电站，以及南加利福尼亚州埃迪逊圣奥佛利核电站，EPRI开始了RCM技术可行性的大规模论证。两年后，研究者获得了精练的RCM实施方法，同时对工厂系统进行RCM分析，进行维修决策，制定维修计划，并评估其有效性。吉纳核电站有21个系统实施了RCM 技术，实施者建议改进的计划维修项目大约有1300项之多。在圣奥佛利核电站，首先实施了RCM技术的4个系统，经评估比原来节省了8000个维修工时。这些成果推动了美国核电站广泛地采用RCM技术。从EPRI的经验可以得出RCM 实施效果的评估准则，一方面要实现RCM分析所预期的维修效果，即是否优化了旧的维修计划，减少冗余维修项目避免过修，添加必要的维修项目防止失修，同时缩短维修工时：另一方面还要权衡实施这项技术的投资与收益是否合理，要评估维修费用减少、设备可用率提高所带来的经济效益是否大于实施RCM的投入。



### 1.32 RCM的实施指南

为了推动RCM的实施，提高实施效果，我国电力行业制定了RCM实施指南(征求意见稿）[3]。目前的RCM实施指南还只停留在对RCM基本原理方法的说明上，缺乏对RCM 相关维修技术和维修管理技术的说明，以及如何将这些技术与RCM有机结合的指导性意见。一个完整的RCM实施指南应该包括RCM的原理方法：RCM实施效果的评价标准：各种维修技术和管理技术的核心内容和实施指导，特别是针对发电设备的状态监测与诊断技术应该给出详细论述和实施指导；以及各种技术与RCM的集成策略等。

## 2 与RCM相关的维修技术和维修管理技术

## 21 维修技术

维修技术可分为两大类，一是主动维修（ProactiveMain tenance），它是在功能故障发生前采取合适的维修措施阻止故障发生的维修活动；二是被动维修（ReactiveMainte nance），这包含主动维修之外的其它维修活动。图1所示维修技术的分类，包含了RCM维修决策涉及的所有维修技术。

<div style="text-align: center;"><img src="imgs/img_in_image_box_550_189_931_411.jpg" alt="Image" width="37%" /></div>


<div style="text-align: center;">图1RCM维修技术分类</div>


### 21.1 主动维修

#### 21.1.1 计划维修（PreventiveMaintenance PM）

计划维修是基于固定时间间隔的维修技术，它不考虑某一台具体设备的实际状态，只是根据同型设备或同类设备共有的故障发生规律和损坏规律来确定检修时间间隔。计划维修包括对设备或零部件周期性的预定检查、调整、清洁、润滑、备件更换、标定、修复。计划维修基于两条原则，第一，设备故障率和运行时间成正比。第二，构件或设备的故障率可以依靠统计确定，据此部件能够在故障发生前被修复或更换。通常，简单设备或者具有主导故障模式的复杂系统的故障发生与时间相关，这类故障是由于设备部件和工质直接接触发生磨损；或者与疲劳、腐蚀、氧化等相关，如果没有更有效的维修方式，通常采用计划维修。



计划维修任务的间隔根据MTBF确定。故障率数据仅仅能够确定上述种类故障的平均故障时间，而实际设备还有一类故障是随机发生的，如和安装质量相关的故障，这类故障的发生与平均故障时间无关。因此，基于一个固定的时间周期来维修随机性故障的设备容易造成过修或失修。对以随机性故障为主的设备，没有预测维修周期的办法，最好的手段就是对设备状态进行监测。



#### 21.1.2 状态维修（Condition-based Maintenance CBM/Pred ic tive M a in tenance PdM)

状态维修通过对设备状态进行监测、分析设备状况及故障，判断异常，确定故障情况，这是状态维修技术的关键环节。状态维修的维修决策阶段没有很复杂的理论和方法，在故障发生前进行检修，即根据设备健康状态来安排检修计划，实施检修[4]。实施状态维修的目标是延长维修周期、减少计划维修工作内容、减少故障维修次数。

建议CBM实施的具体策略，首先应该完善状态监测手段，充分利用已配置的在线监测系统，挖掘其可以为状态维修服务的功能；结合已有的DCSMISSIS建立设备状态数据库：从状态维修角度，完善监测手段：振动、油液、红外热成像、电机电流、超声波等；积极采用新的监测方法，如远程监测等；加强技术队伍、人员、组织等建设。同时，利用各种监测数据的相关性。根据设备特性选用合理的监测技术，综合分析设备的状态和故障，提高分析的准确性。

在实施状态维修时，设备的监测频度依据P一F间隔确定，P一F间隔是从潜在故障产生故障征兆到其演变成为功

能故障的时间间隔。对尚无法确定P一F间隔的设备，可根据故障历史或同类设备维修经验安排，开始时采取保守的做法，监测频度稍高，积累一定经验后再逐步调整。

#### 2.1.2 被动维修(ReactiveMaintenance RM)

被动维修是在设备已经发生功能故障的情况下采取的维修方式，它包括隐患检查（FailureFinding）事后维修（Run to-FailureMaintenance)、重新设计（Redesign)。

被动维修的实施特别强调隐患检查。随着设备的复杂程度和自动化水平的提高，大约有40%的故障属于隐蔽性故障[5]。这种故障不会造成直接的后果，所以对设备使用人员和维修者没有明显表征，但增加了发生多重故障的风险。80%的隐蔽性故障可通过隐患检查发现，隐患检查是一种重要的维修方式，它的任务就是探测设备或装置是否处于正常工作状态中。实施隐患检查的关键是确定隐患检查间隔，检查间隔可以根据设备平均故障时间和可用度，利用经验公式求得。



## 22 计算机化维修管理系统（CMMS)

CMMS目前被电力企业用来进行维修管理。

RCM对设备维修需求做出决策，需要对多种信息进行综合分析，包括反映设备功能与性能的运行信息、状态变化趋势信息、设备维修历史信息等，同时还要对维修活动进行经济分析。这些复杂的分析任务必须由CMMS来担当，RCM 与CMMS的集成，是使RCM获得成功的一个关键环节。

## 3 RCM的实施方法

为了克服实施RCM遇到的技术和管理方面的难点，并将RCM与先进的维修技术和管理技术相结合。本文建议在健全和完善各种先进维修技术的基础上实施RCM，重点是健全状态维修，然后通过维修评价反馈RCM分析需要的信息，优化已实施的维修活动，动态实施RCM；另一方面，为了结合CMMS在维修数据管理方面的优势，建议对RCM、CBM与CMMS之间的数据交互，采用更为合理的方式。

### 3.1 在健全和完善各种先进维修技术的基础上实施RCM 

目前关于RCM实施方法的很多讨论有一个共同点，都是以FMEA为起点开始工作，然后依据FMEA分析结果进行维修需求决策，给出技术可行且值得实施的最优维修方式。然而目前我国发电企业的检修体制仍然是以计划维修为主，状态维修还处在探索试行阶段，没有全面开展，在这种单一的计划维修模式下，RCM的优化对象是什么呢？缺少待优化、待选择的对象，如何优化？因此，对于电力企业来说，在RCM实施初期，更为有效、收益更快的改进维修的方法是从维修活动入手健全和完善各种先进的维修技术，主要是健全状态维修。这样既可以满足设备当前的维修需求，又增强了RCM实施人员对于维修技术的熟悉程度，反过来通过这些维修技术的实施和经验积累，促进RCM的实施。美国航天局路易斯研究中心在实施RCM时放弃了传统以FMEA为起点开始工作的步骤，延缓功能、性能标准和功能故障的分析识别工作，简化了计划维修的实施；同时以状态维修为工作重点，根据该中心设备的特点配置相应的监测装置，加强状态监测和故障诊断队伍建设[6]。这些措施为路易斯研究中心RCM的成功实施奠定了基础。

维修评价是实现RCM动态实施的关键。定期评价维修活动，提取并反馈RCM分析所需要的信息，提高RCM的实施效果。评估内容包括维修任务的适用性、维修任务的执行间隔、故障根源因分析、可靠性计算（MTBF，Weibull分布）等。另外，参与RCM实施的工作人员应该由最熟悉设备的操作者和维修者组成，所有成员应该熟悉系统边界划分，功能和性能标准定义，功能故障定义，FMEA等RCM技术内容。同时，RCM的分析过程应该按照标准RCM程序进行，避免采用简化的RCM即SRCM（Stream linedReliability Centered Maintenance)。SRCM与标准RCM相比，虽然在分析时间和费用上有所减少，却含有逻辑上或程序上的缺陷，降低了对最优化的要求，风险增大，不能得到和真正的RCM相同的结果[7]。



## 32 RCM、CBM与CMMS的数据交互方式

发电企业需要高效的CMMS来对设备进行全寿命周期维修活动管理，然而当前的CMMS存在如下问题：CMMS提供的维修信息只包括设计、制造单位的说明或设备的维修历史，不能根据设备的“健康状态和生产运行情况做出状态维修决策；系统主要集中于对维修作业过程管理，并不能在维修任务下发前进行优化，这使得CMMS要完善维修优化方面的功能[8]。同时CBM和RCM的成功实施需要CMMS提供完整准确的数据支持。



RCM、CBM与CMMS集成的关键是数据如何交互，这种交互的基本要求是：建立统一的数据平台，实现数据格式的标准化和规范化，避免过多的数据接口和转换，这就要求先进的维修技术（CBM），维修优化技术（RCM），维修管理技术（CMMS）在一个企业应该同步开展。同时需要注意，CMMS 作为管理工具处于一个从属服务地位，系统功能要根据RCM 和CBM的需求不断调整。



CBM和RCM与CMMS集成，实现三者之间的数据交互，由CMMS提供基础数据，RCM利用这些数据优化维修任务，CBM则利用这些数据评估设备健康状态，三者数据交互方式见图2。CMMS的维修管理模式以计划维修为主，它的管理模块的基本功能包括设备信息管理、缺陷管理、工单管理、备件管理等：它的数据库管理资产清单、设备设计、制造、安装资料，维修历史数据、备件信息等。CMMS根据设备的定检周期，制定、管理计划维修任务；或对上报缺陷登记后，下达维修任务并管理实施过程。



目前的CMMS只能满足计划维修和被动维修的要求。在状态维修实施后，CMMS的工作方式应有所改变。CMMS 初始下达的状态维修任务只是与状态监测相关的任务，如监测手段，监测频度，测点布置等，在获取设备状态数据后，还要评估设备健康状态趋势，并将评估结果反馈到CMMS系统，指导具体维修任务的制定和管理。设备状态评估要综合利用状态监测数据、生产运行数据以及CMMS数据库中关于设备的设计、制造技术资料和维修历史数据等。目前EPRI 的运行维修工作站（Operation&MaintenanceWorkstationO &M）和恩泰克（Entek）公司的设备检修集成系统（Enshare）都是状态维修分析管理系统，系统综合获取各种状态监测数据，通过这些数据评估设备状态，指导维修，这两个系统都可

以实现与CMMS数据接口。电厂要以优化维修的思路来开展维修活动，因此RCM是整个系统中最重要的一个环节。RCM与CMMS集成后，RCM从CMMS中提取FMEA信息，在维修优化决策后，实施维修任务，然后反馈维修结果，对维修活动进行评价，并将维修历史数据存储到CMMS数据库中。维修历史数据除了记录维修过程、备件更换情况、工时、维修费用等数据外，更重要的是详细记录有关维修技术适用性、故障根源因分析、可靠性计算、维修任务间隔等维修技术评价内容，这些信息将促进RCM的进一步有效实施，这是RCM 动态实施的关键。



<div style="text-align: center;"><img src="imgs/img_in_image_box_38_376_488_596.jpg" alt="Image" width="44%" /></div>


<div style="text-align: center;">图2CBM、RCM与CMMS的数据交互方式</div>


## 4 结论

对于RCM在我国电力企业的实施，建议应该在健全和完善各种维修技术的基础上实施RCM，重点是健全状态维修

## (上接第 243页）

明，带冠叶片的研究工作已经有了一定的工作基础，但还有很多问题值得开展深入的研究工作。主要问题如下：

1)带冠叶片的减振机理，尤其是碰撞条件下的叶片振动特性问题；

2)具有边界非线性的带冠叶片振动局部化问题；

3)具有不同型式叶冠的带冠叶片的动应力优化问题；

4)带冠叶片的疲劳寿命分析问题。

带冠叶片同三元流设计一样为蒸汽轮机设计的新颖技术，有大量理论和工程实际问题需要研究解决。通过深入的研究工作，全面解决带冠叶片设计中的问题，可以形成带冠叶片设计体系，对研制安全、可靠的汽轮机带冠叶片意义重大。

## 参考文献

[1]吴厚钰，透平零件结构和强度[M].北京：机械工业出版社，1986.
[2]谢永慧，汽轮机叶片疲劳失效寿命预测及设计分析系统的研
究[D].西安交通大学，1997.
[3]V.Karadag Dynam ic Analysis of PracticalB lades with Shear Cen ter Effect[J]. Joumalof Sound and Vibration1984,92(4):471-490.
[4]A.W.Leisse JK. Lee andA.JWang RotatingBlade Vibration Analysis Using ShellsJ].ASMEJoumalofEngineering for Pow er1982,104:296-302
[5]A.V.Srinivasan and BN.CassentiANon linear Theorv ofDynam ic System s with Dry Friction Forces[ J].ASME， Joumalof Engi 

技术，要以优化维修的思路来开展维修活动，通过维修评价反馈信息，动态实施RCM。同时，CMMS是实现RCM维修管理不可或缺的工具，在实施过程中CMMS要为RCM维修优化决策和CBM设备状态评估提供完整准确的数据。RCM的实施是一项复杂的系统工程，管理层要高度重视和有效管理，并建设一支稳定的研究和实施队伍，积极探索与实践才能取得成功。



## 参考文献

[1]Marvin Rausand Reliability centered Maintenance[J].Reliabiit Engineering and System Safety, 1998, 60:121—132[2]Moubray JReliability−centered Maintenance−2nded[M]. Lon−don: Butterworth H einem ann 1997.
[3]火力发电厂设备以可靠性为中心的维修（RCM）分析技术导则
（征求意见稿）[S].中华人民共和国电力行业标准DL/T一
2004.
[4]陆颂元．美国几个电厂状态检修技术的发展过程及特点[A].
全国发电设备状态检修技术研讨会论文集[C].宁波：2002，7.[5]MoubrayJ Maintenance Management a New Parad igm「EB/OL].
A ladon Ltd 1995.
[6]R.A. Danks JA. Cmz and K. A. Keams RCM Implementation at NASA Lew is Research Center C. M FPT Proceedings the 53d M eeting 1999
[7]Moubray J The case against SRCM [EB /OL]. Aladon Ltd 200Q.[8]Hossam A. Gabbar eto Com puter aided RCM—based plantma in tenance m anagem ent system[J]. Robotics and Com puter Inte grated Manufacturing 2003,19:449-458

neering forGas Turbines and Powe 1986,108(3):525—530.[6]周传月，等，燃气轮机带冠叶片耦合振动分析[J]哈尔滨工业大学学报，2001,33（1）:129-133[7]季葆华.汽轮机叶片阻尼机理及带阻尼结构汽轮机叶片振动特
性研究[D].西安交通大学，1996[8]陈予恕，非线性振动[M.天津：天津科学技术出版社，1983[9]Chia-Hsiang Menq J H. Griffin A Com parison of Transientand Steady State Finite Element Analyses of the Forced Response of a Frictionally Damped Beam[J].ASME，Joumal of VibrationA coustics Stress and Reliability in Design.1985,107(1):19—25.[10]李辛毅.大型汽轮机组复杂连接形式长叶片静动力特性研究
[D].西安：西安交通大学，1996.
[11]SDubow skyT N. Gardner Dynam ic Interactions ofLink Elastic ity and C learance Connections in Planar Mechanical System s[ J].
Joumalof Engineering for Industry,1975,97B(2):652-661.[12]T.W.Lee A. C W ang On the Dynam ics of in Tem it Tentmo tion Mechanisms Part I Dynam ic Model and Response[J].
Joumal ofMechanisms Transm issions and Autom ation in Design 1983,105:534-540.
[13]金栋平，胡海岩，等．弹性梁碰撞阻尼识别的新方法「J]：航
空学报.1999,20（2）:111-113[14]闻雪友：叶片弹性扭角的试验研究「J]：透平锅炉，1982，
(5):1-4.
[15]S Heath.and M.Im regun An Improved Single—Parameter TipTim ing M ethod for Turbom achinery B lades V ibration M easure ments Using Optical Laser Probles[ J]. Int JMech Sci,1996,
38(10):1047-1058
