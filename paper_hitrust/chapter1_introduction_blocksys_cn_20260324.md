# 第一章 引言

说明：本章为中文导师阅览版，正文采用 BlockSys/Springer LNCS 常见的数字引用风格，在文中使用 `[1]`、`[2]` 等顺序编号。参考文献均为真实已发表条目，并附 DOI 链接。

## 1.1 研究背景

联邦式 Web Bot 检测首先面对的不是模型容量问题，而是训练条件本身的约束问题。原始流量、会话关系和交互日志通常分散在不同边缘节点，直接集中化会引入隐私、治理和跨域共享成本，因此联邦学习成为更现实的训练框架 [1-3]。但联邦学习并不会自动带来安全性。相反，现有研究已经指出，联邦训练同时暴露于统计异构、通信受限、推理泄露和投毒攻击等多类风险之下 [1,2,4,5]。在网络安全任务中，这些风险并不是附属问题，而是决定系统是否可部署的核心约束 [3-6]。

对于 Web Bot 检测，这一问题比常规联邦分类更复杂。Bot 行为往往不仅体现为单点特征异常，也体现为账号之间、会话之间和访问模式之间的关系异常。现有图学习研究表明，当任务本身具有显式关系结构时，图神经网络通常比纯特征模型更容易利用局部邻域和结构上下文，从而提升检测能力 [7-10]。这一趋势已经在入侵检测、流量异常识别和社交机器人检测等任务中得到持续验证 [7,9,10]。因此，在联邦 Bot 检测场景中，将结构信息纳入模型设计是合理且必要的。

然而，仅仅把更强的图模型接入联邦管线并不能直接解决鲁棒性问题。网络安全场景中的联邦客户端往往不是一个平坦且可互换的集合。不同客户端可能对应不同角色、不同业务区域、不同局部子图或不同语义分区。如果某轮训练仅依据 trust score 或异常分数删除客户端，那么系统虽然可能减少恶意更新输入，却也可能把某个语义组整体删除，进而损失该组的表示能力。现有联邦安全综述已经较为系统地梳理了攻击面、投毒方式和防御范式 [2,4,5]，但“语义组覆盖是否会在鲁棒过滤中被破坏”这一问题仍缺少显式建模。

## 1.2 问题定义与研究缺口

基于上述背景，本文关注一个更具体的问题：在 topology-aware federated bot detection 场景中，系统如何在抑制 poisoned participation 的同时保留必要的 semantic group coverage。这个问题与传统鲁棒联邦学习的区别在于，本文不把客户端视为扁平池，而是承认它们在结构和语义上存在分组。这样一来，鲁棒性目标就不再只是“尽可能删掉坏客户端”，而是要同时处理两个互相拉扯的目标：一是降低恶意参与和污染更新的影响，二是避免重要语义组因过滤而整体消失。

这一张力在图结构任务中尤为明显。一方面，图模型需要尽可能保留来自不同局部结构的训练信号；另一方面，投毒攻击又会迫使系统采用更严格的过滤策略 [4,5]。如果过滤过于激进，小组或弱组可能被整体去除；如果过滤过于宽松，投毒更新又可能穿透聚合过程。换言之，联邦鲁棒性与语义覆盖在这里不是两个独立问题，而是同一个设计问题的两面。

现有联邦网络安全文献已经证明，联邦训练可以有效应用于入侵检测和分布式安全监测 [3,6]。现有图安全文献也证明，结构建模在入侵检测和社交 Bot 检测中具有明显价值 [7-10]。但将二者直接相加，仍不足以回答本文关心的问题。缺失的不是“是否采用联邦学习”或“是否采用图模型”这类单点选择，而是一个同时约束 trust filtering、grouped aggregation 和 semantic coverage 的整体机制。

## 1.3 本文思路

为解决这一问题，本文提出 HiTrust-FedBot。该框架的核心不是单纯替换 backbone，而是围绕联邦安全控制来组织训练流程。具体而言，HiTrust-FedBot 由三部分组成：客户端级 trust scoring、组内到组间的层次聚合，以及组覆盖约束信任过滤。前两部分负责在异构客户端之间保留结构信息，第三部分负责在过滤低信任更新时避免整个语义组被静默抹除。

本文将这一机制称为 group-coverage-constrained trust filtering。其基本思想是，在按信任阈值执行过滤后，仍为每个语义组保留最低数量的代表客户端。这样做的目的不是追求更高平均 F1，而是将语义覆盖明确纳入鲁棒联邦设计，使系统在面对恶意参与时不会因为过度保守而损失整个结构切片。

但是，这一设计本身也引入了新的边界问题。如果某个小语义组被完全投毒，那么静态 group floor 可能会为了“保组”而强行留下一个本应删除的低信任中毒客户端。因此，本文不仅验证静态 group floor 的平均收益，也进一步分析其 principal failure mode，并引入 conditional trust-mass floor 作为 targeted hardening。也就是说，本文既关注主线方法是否有效，也关注其失败条件是否可解释、可修复。

## 1.4 本文贡献

本文的主要贡献如下。

1. 本文将 topology-aware federated bot detection 明确建模为“poisoning resistance 与 semantic group coverage preservation 的联合优化问题”，并据此提出 trust-aware hierarchical defense，而不是将鲁棒联邦问题简单视为平坦客户端池上的异常更新过滤问题。

2. 本文设计了 group-coverage-constrained trust filtering，将 `min_keep_per_group` 从经验超参提升为具有安全含义的机制参数，并把它与 grouped hierarchical aggregation 统一到同一联邦防御框架中。

3. 本文基于五个 topology-aware 场景、held-out `scenario_e` 和 auxiliary public `NSL-KDD` 构建了较完整的验证链。实验表明，在最关键的 `scenario_h` 上，GraphSAGE 主线在五个随机种子下的平均 F1 在 clean、`sign_flip@0.4` 和 `update_noise@0.4` 条件下分别达到 `0.9785`、`0.9797` 和 `0.9686`；在 `scenario_h` 的 clean 和 sign-flip 条件下，GraphSAGE 相比 FeatureMLP 取得显著提升。更重要的是，held-out `scenario_e` 结果显示，在 `update_noise@0.4` 下，trust-aware filtering 将 retained poisoned clients 从 `4.0` 降至 `0.2`，同时平均 F1 仅发生小幅且不显著变化。这说明 trust-aware filtering 的主要价值是减少 poisoned participation，而不是普遍提高平均精度。

4. 本文通过固定种子机制分析识别出静态 group floor 的 principal failure mode，即 fully poisoned small group 下的边界失效，并进一步提出 conditional trust-mass floor。针对 `scenario_h + update_noise@0.4`，该 hardening 将平均 F1 从 `0.9686` 提升到 `0.9766`，将 retained poisoned clients 从 `0.4` 降到 `0.0`。与此同时，public auxiliary benchmark 的结果也表明，该 hardening 并不是 universal replacement，而应被更谨慎地定位为 targeted hardening。

## 1.5 章节安排

本文其余部分安排如下。第二章回顾联邦网络安全检测、投毒鲁棒联邦学习、图安全分析与通信高效联邦适配等相关工作。第三章介绍 HiTrust-FedBot 的系统设定、威胁模型、trust-aware hierarchical aggregation、group-coverage-constrained filtering 和 conditional trust-mass floor hardening。第四章说明实验设置，包括场景族、攻击设定、评价指标和复现协议。第五章给出主实验、held-out 验证、public auxiliary 验证、机制诊断和 hardening 结果。第六章讨论本文结果真正支持的结论及其边界。第七章总结全文并说明后续工作方向。

## 第一章参考文献

[1] Li, T., Sahu, A.K., Talwalkar, A., Smith, V.: Federated Learning: Challenges, Methods, and Future Directions. *IEEE Signal Processing Magazine* 37(3), 50-60 (2020). DOI: https://doi.org/10.1109/MSP.2020.2975749

[2] Mothukuri, V., Parizi, R.M., Pouriyeh, S., Huang, Y., Dehghantanha, A., Srivastava, G.: A survey on security and privacy of federated learning. *Future Generation Computer Systems* 115, 619-640 (2021). DOI: https://doi.org/10.1016/j.future.2020.10.007

[3] Ferrag, M.A., Friha, O., Maglaras, L., Janicke, H., Shu, L.: Federated Deep Learning for Cyber Security in the Internet of Things: Concepts, Applications, and Experimental Analysis. *IEEE Access* 9, 138509-138542 (2021). DOI: https://doi.org/10.1109/ACCESS.2021.3118642

[4] Liu, P., Xu, X., Wang, W.: Threats, attacks and defenses to federated learning: issues, taxonomy and perspectives. *Cybersecurity* 5(1), Article 4 (2022). DOI: https://doi.org/10.1186/s42400-021-00105-6

[5] Qammar, A., Ding, J., Ning, H.: Federated learning attack surface: taxonomy, cyber defences, challenges, and future directions. *Artificial Intelligence Review* 55(5), 3569-3606 (2022). DOI: https://doi.org/10.1007/s10462-021-10098-w

[6] Hamdi, N.: Federated learning-based intrusion detection system for Internet of Things. *International Journal of Information Security* 22(6), 1937-1948 (2023). DOI: https://doi.org/10.1007/s10207-023-00727-6

[7] Bilot, T., El Madhoun, N., Al Agha, K., Zouaoui, A.: Graph Neural Networks for Intrusion Detection: A Survey. *IEEE Access* 11, 49114-49139 (2023). DOI: https://doi.org/10.1109/ACCESS.2023.3275789

[8] Wu, Z., Pan, S., Chen, F., Long, G., Zhang, C., Yu, P.S.: A Comprehensive Survey on Graph Neural Networks. *IEEE Transactions on Neural Networks and Learning Systems* 32(1), 4-24 (2021). DOI: https://doi.org/10.1109/TNNLS.2020.2978386

[9] Caville, E., Lo, W.W., Layeghy, S., Portmann, M.: Anomal-E: A self-supervised network intrusion detection system based on graph neural networks. *Knowledge-Based Systems* 258, 110030 (2022). DOI: https://doi.org/10.1016/j.knosys.2022.110030

[10] Liu, F., Li, Z., Yang, C., Gong, D., Lu, H., Liu, F.: SEGCN: a subgraph encoding based graph convolutional network model for social bot detection. *Scientific Reports* 14, Article 4122 (2024). DOI: https://doi.org/10.1038/s41598-024-54809-z
