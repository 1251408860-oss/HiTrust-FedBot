# 第二章 相关工作

说明：本章为中文导师阅览版，正文采用 BlockSys/Springer LNCS 常见的数字引用风格，在文中使用 `[1]`、`[2]` 等顺序编号。参考文献均为真实已发表条目，并附 DOI 链接。由于该文件当前作为独立章节文档使用，编号在本章内单独顺排；后续并入整篇论文时可统一重排。

## 2.1 联邦网络安全检测

联邦学习在网络安全场景中的应用已经从通用分类问题延伸到入侵检测、恶意流量识别、IoT 监测和分布式安全分析等方向 [1-4]。现有研究普遍认为，联邦学习的优势在于保留数据本地性，减少跨域原始数据共享；但其局限同样明显，即客户端统计异构、训练过程攻击面和通信效率问题会在安全任务中被同时放大 [1-4]。以 IoT 和边缘安全为代表的应用场景尤其如此，因为客户端通常来自不同设备域、网络域或业务域，其数据分布本身就不一致 [1,3,4]。

从现有成果看，联邦网络安全检测已经证明“分布式训练可行”，但尚未自动解决“在异构结构环境下如何稳定聚合”的问题。Ferrag 等人系统总结了联邦深度学习在 IoT 网络安全中的概念、应用和实验分析，说明联邦范式在安全监测中具有实际潜力 [3]。Hamdi 进一步展示了联邦学习在 IoT 入侵检测中的有效性 [4]。然而，这一类工作多数仍默认客户端是平坦集合，或主要关注特征级分类性能，很少显式处理客户端之间的语义分组、结构覆盖和投毒过滤之间的联动关系。因此，对于 topology-aware federated bot detection 而言，现有联邦安全检测研究提供了问题背景和部署动机，却不足以直接回答本文关注的“组覆盖与鲁棒性如何兼顾”这一核心问题。

## 2.2 面向投毒攻击的鲁棒联邦学习

鲁棒联邦学习是与本文最直接相关的工作线之一。现有研究已经从综述、攻击面分析和具体防御机制三个层面对这一问题展开了系统讨论 [1,5,6]。Mothukuri 等人从安全与隐私角度总结了联邦训练中的攻击风险和防御需求 [1]。Liu 等人以及 Qammar 等人进一步从 threats、attack surface、taxonomy 和 cyber defence 角度梳理了联邦学习在投毒、推理和系统层面的主要脆弱点 [5,6]。这些工作共同表明，联邦训练并非天然安全，而是一类暴露面较广的分布式学习机制。

在具体防御方法上，现有工作已经提出了多种面向恶意更新的鲁棒策略，其中较有代表性的包括基于可信根的 trust bootstrapping 方法和基于异常更新筛除的鲁棒聚合方法。FLTrust 通过服务器侧可信引导来约束客户端更新方向，是近年来较有影响力的 trust-based federated defence 之一 [7]。这类方法对本文的启发在于，trust signal 可以作为联邦安全控制的一部分，而不必被限制为事后分析指标。

不过，现有鲁棒联邦学习方法大多把客户端视为平坦池，其主要目标是识别和抑制恶意更新，而不是维护客户端组之间的语义覆盖 [5-7]。在这类设定下，只要删除足够多的低信任客户端即可被视为“更鲁棒”；但在本文所研究的 topology-aware 联邦 Bot 检测中，这一逻辑并不充分。若某一组客户端整体被过滤掉，模型虽然更少接收恶意输入，却也可能丢失该组所对应的局部结构信息。因此，本文与传统鲁棒联邦学习的差异不在于是否重视投毒防御，而在于进一步把 semantic group coverage 纳入防御目标，并将其与 trust filtering 一起设计。

## 2.3 图学习与安全检测

图学习研究为本文的方法设计提供了第二条关键技术脉络。已有综述表明，图神经网络能够通过局部结构传播建模关系依赖，因此在异常检测、入侵检测、社交机器人识别和欺诈检测等任务中通常优于仅依赖静态特征的模型 [8,9]。在安全领域，Bilot 等人专门总结了图神经网络在入侵检测中的应用，指出关系建模能够有效补充传统基于特征或序列的方法 [8]。Wu 等人的 GNN 综合综述则从更一般的角度说明，图结构学习在处理节点关系、邻域上下文和局部模式传播方面具有天然优势 [9]。

更贴近本文应用的是，图模型已经在具体安全任务中展现出可验证收益。Caville 等人提出的 Anomal-E 说明，自监督图神经网络可以有效用于网络入侵检测 [10]。Liu 等人提出的 SEGCN 则表明，在社交 Bot 检测中，子图编码和图卷积建模能够提升对机器人行为的识别能力 [11]。这些工作共同说明，安全检测任务并不只是“给更强分类器喂更多特征”，而是经常依赖结构上下文本身。

然而，现有图安全研究大多假设训练数据可集中使用，或至少不重点讨论联邦条件下的异构聚合问题 [8-11]。因此，它们支持本文选择 GraphSAGE 作为主要实例化 backbone，但并未直接解决“在联邦且受攻击的场景中，如何避免结构信息在鲁棒过滤中被过度损失”的问题。本文正是在这一空白处，把图结构建模与 trust-aware federated aggregation 结合起来。

## 2.4 通信高效联邦训练与适配

通信效率是联邦系统能否落地到边缘环境的现实条件之一。Li 等人指出，联邦学习的基本困难不仅在于 non-IID 数据，也在于客户端与服务器之间的有限通信预算 [2]。此后，多项研究从无线网络、6G 场景和系统角度讨论了联邦训练中的通信瓶颈 [12,13]。Liu 等人从 6G 通信视角总结了联邦学习在未来网络中的挑战与方法，进一步强调通信成本是联邦部署中不可绕开的系统约束 [12]。Pouriyeh 等人则从“secure smart communication efficiency”的角度说明，在考虑安全性的同时优化通信效率，本身已经成为联邦研究的重要方向 [13]。

对本文而言，这一线工作的意义在于两点。第一，边缘 Bot 检测天然处于带宽受限环境，因此 full fine-tuning 是否必要必须通过实验回答，而不能默认成立。第二，现有通信高效联邦研究主要关注参数压缩、轮次控制和系统开销，却很少把“语义覆盖”与“鲁棒过滤”一起纳入讨论。本文的 tuning study 正是在这一背景下展开：我们不仅比较不同 tuning 模式的通信量，还考察其在投毒条件下的性能是否足以支撑主线方法。

## 2.5 本文与现有工作的区别

综合来看，现有工作分别回答了几个相邻但不相同的问题。联邦网络安全检测研究说明，联邦框架适合安全场景，并且在 IoT 和分布式监测中具有现实意义 [3,4]。鲁棒联邦学习研究说明，投毒攻击是联邦训练的核心风险，trust-based defence 和鲁棒聚合是必要方向 [5-7]。图安全分析研究说明，在入侵检测和 Bot 检测等任务中，结构建模通常优于纯特征建模 [8-11]。通信高效联邦研究则说明，边缘部署要求模型适配具备较低通信开销 [2,12,13]。

本文工作的区别不在于简单叠加这几条线，而在于把它们组织到同一个问题框架下：在 topology-aware federated bot detection 中，系统需要同时面对结构异构、投毒攻击和通信约束，而且 trust filtering 不能以破坏 semantic group coverage 为代价。围绕这一点，本文提出的 HiTrust-FedBot 既不是单纯的鲁棒聚合器，也不是单纯的图模型替换，而是一个将 trust scoring、grouped hierarchical aggregation 和 group-coverage-constrained filtering 联合起来的联邦安全控制框架。进一步地，本文还通过 fixed-seed mechanism analysis 解释了静态 group floor 的 principal failure mode，并用 conditional trust-mass floor 给出 targeted hardening。就当前文献格局而言，这正是本文相对现有工作的核心区分点。

## 第二章参考文献

[1] Mothukuri, V., Parizi, R.M., Pouriyeh, S., Huang, Y., Dehghantanha, A., Srivastava, G.: A survey on security and privacy of federated learning. *Future Generation Computer Systems* 115, 619-640 (2021). DOI: https://doi.org/10.1016/j.future.2020.10.007

[2] Li, T., Sahu, A.K., Talwalkar, A., Smith, V.: Federated Learning: Challenges, Methods, and Future Directions. *IEEE Signal Processing Magazine* 37(3), 50-60 (2020). DOI: https://doi.org/10.1109/MSP.2020.2975749

[3] Ferrag, M.A., Friha, O., Maglaras, L., Janicke, H., Shu, L.: Federated Deep Learning for Cyber Security in the Internet of Things: Concepts, Applications, and Experimental Analysis. *IEEE Access* 9, 138509-138542 (2021). DOI: https://doi.org/10.1109/ACCESS.2021.3118642

[4] Hamdi, N.: Federated learning-based intrusion detection system for Internet of Things. *International Journal of Information Security* 22(6), 1937-1948 (2023). DOI: https://doi.org/10.1007/s10207-023-00727-6

[5] Liu, P., Xu, X., Wang, W.: Threats, attacks and defenses to federated learning: issues, taxonomy and perspectives. *Cybersecurity* 5(1), Article 4 (2022). DOI: https://doi.org/10.1186/s42400-021-00105-6

[6] Qammar, A., Ding, J., Ning, H.: Federated learning attack surface: taxonomy, cyber defences, challenges, and future directions. *Artificial Intelligence Review* 55(5), 3569-3606 (2022). DOI: https://doi.org/10.1007/s10462-021-10098-w

[7] Cao, X., Fang, M., Liu, J., Gong, N.Z.: FLTrust: Byzantine-robust Federated Learning via Trust Bootstrapping. *Proceedings 2021 Network and Distributed System Security Symposium* (2021). DOI: https://doi.org/10.14722/ndss.2021.24434

[8] Bilot, T., El Madhoun, N., Al Agha, K., Zouaoui, A.: Graph Neural Networks for Intrusion Detection: A Survey. *IEEE Access* 11, 49114-49139 (2023). DOI: https://doi.org/10.1109/ACCESS.2023.3275789

[9] Wu, Z., Pan, S., Chen, F., Long, G., Zhang, C., Yu, P.S.: A Comprehensive Survey on Graph Neural Networks. *IEEE Transactions on Neural Networks and Learning Systems* 32(1), 4-24 (2021). DOI: https://doi.org/10.1109/TNNLS.2020.2978386

[10] Caville, E., Lo, W.W., Layeghy, S., Portmann, M.: Anomal-E: A self-supervised network intrusion detection system based on graph neural networks. *Knowledge-Based Systems* 258, 110030 (2022). DOI: https://doi.org/10.1016/j.knosys.2022.110030

[11] Liu, F., Li, Z., Yang, C., Gong, D., Lu, H., Liu, F.: SEGCN: a subgraph encoding based graph convolutional network model for social bot detection. *Scientific Reports* 14, Article 4122 (2024). DOI: https://doi.org/10.1038/s41598-024-54809-z

[12] Liu, Y., Yuan, X., Xiong, Z., Kang, J., Wang, X., Niyato, D.: Federated learning for 6G communications: Challenges, methods, and future directions. *China Communications* 17(9), 105-118 (2020). DOI: https://doi.org/10.23919/JCC.2020.09.009

[13] Pouriyeh, S., Shahid, O., Parizi, R.M., Sheng, Q.Z., Srivastava, G., Zhao, L., Nasajpour, M.: Secure Smart Communication Efficiency in Federated Learning: Achievements and Challenges. *Applied Sciences* 12(18), 8980 (2022). DOI: https://doi.org/10.3390/app12188980
