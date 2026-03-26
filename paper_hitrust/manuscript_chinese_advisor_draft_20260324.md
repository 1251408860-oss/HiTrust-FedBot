# HiTrust-FedBot：面向拥塞边缘环境的组覆盖约束信任过滤联邦 Web Bot 检测

说明：本文档为中文导师阅览版草稿，用于在正式英文投稿稿形成前，先以中文完整呈现论文的问题定义、方法设计、实验结果与当前结论边界。作者信息、单位、基金和正式参考文献格式将在后续投稿版中统一补齐。

## 摘要

在拥塞边缘环境中开展联邦式 Web Bot 检测时，系统需要同时面对拓扑异构、通信受限和恶意客户端投毒三类挑战。传统的信任过滤虽然可以压制低质量或恶意更新，但在语义分组联邦环境中也可能产生新的问题：如果某一轮把某个组内客户端全部过滤掉，模型虽然更“保守”，却可能失去对该语义组的表示能力，进而影响全局检测器的稳定性。为此，本文提出 HiTrust-FedBot，一种面向联邦 Bot 检测的信任感知层次聚合框架，其核心是将组内聚合、跨组聚合与组覆盖约束信任过滤结合起来，在抑制投毒参与的同时保留必要的语义覆盖。本文以 GraphSAGE 为主要实例，在五个拓扑感知场景上评估 clean、`sign_flip@0.4` 和 `update_noise@0.4` 三种训练条件。结果表明，在最具挑战性的 `scenario_h` 上，GraphSAGE 主线在五个随机种子上的平均 F1 分别达到 `0.9785`、`0.9797` 和 `0.9686`；在较难的 `scenario_f` 上，对应平均 F1 分别为 `0.9859`、`0.9840` 和 `0.9867`。与 FeatureMLP 相比，GraphSAGE 在 `scenario_h` 的 clean 和 sign-flip 条件下均取得显著提升。进一步的 tuning 对比表明，参数高效微调在显著降低通信开销的同时仍能保持主线性能。held-out `scenario_e` 与 auxiliary public `NSL-KDD` 的补充实验进一步说明，trust-aware filtering 的主要收益并不是普遍提升 F1，而是在总体精度近似不变的前提下显著减少 retained poisoned clients。最后，固定种子机制分析显示，现有最坏情况主要来自静态 group floor 在“小语义组被完全投毒”时的边界失效，而非 GraphSAGE 本身崩溃；针对这一问题引入的 conditional trust-mass floor 在 topology-aware 主线上能够有效修复该坏点，但在 public auxiliary benchmark 上表现 mixed，因此更适合被定位为 targeted hardening，而不是新的 universal default。

**关键词：** 联邦学习；Bot 检测；对抗鲁棒性；信任感知聚合；GraphSAGE；边缘安全

## 1. 引言

随着 Web 服务逐渐部署到异构边缘节点，Bot 检测系统越来越难以依赖集中式数据汇聚完成训练。一方面，原始流量、会话图和交互日志通常受隐私、带宽和治理约束限制，难以直接集中；另一方面，真实边缘环境中的客户端并非同分布，其所对应的流量子图、行为模式和角色分区都可能明显不同。因此，联邦学习为 Web Bot 检测提供了自然的训练范式，但也同时引入了新的安全问题：恶意客户端可以通过上传中毒更新影响全局模型，使联邦过程本身成为攻击面。

如果问题只停留在“如何删除可疑客户端”，那么多数鲁棒联邦学习工作已经给出了相当丰富的方案，例如鲁棒聚合、异常检测、可信客户端选择与基于信任的过滤等。然而，在本文关注的拓扑感知 Bot 检测场景中，仅靠“尽量删掉低信任客户端”并不够。原因在于，不同客户端往往不是一个平坦的、可互换的集合，而是来自不同语义组。例如，它们可能对应不同角色、不同子图结构或不同流量区域。若某轮训练把一个组中所有客户端全部去掉，系统虽然减少了恶意更新输入，但也可能失去对某一重要语义区域的建模能力。换句话说，联邦鲁棒性与语义覆盖之间存在明确张力。

基于这一观察，本文提出 HiTrust-FedBot。该框架并不是单纯地把 GraphSAGE 当作一个更强 backbone 塞入联邦管线，而是围绕“如何在保留必要组覆盖的同时抑制恶意参与”这一安全问题组织方法设计。具体而言，HiTrust-FedBot 由三部分组成：客户端级信任评分、分组层次聚合，以及组覆盖约束信任过滤。核心机制是：在按 trust threshold 执行过滤后，系统仍为每个语义组保留最小客户端数下界 `min_keep_per_group`，以防止整个组因低信任被完全抹除。

这一路线带来两个直接后果。其一，它使得 trust-aware filtering 的目标从“单纯提高平均精度”转变为“在总体精度近似不变时减少 poisoned participation，并控制 false positive risk”；其二，它也引入了新的机制 trade-off，即保组规则在极端情况下也可能把本应丢弃的低信任中毒客户端强行保留下来。因此，本文不仅给出主线实验，也专门分析这一 trade-off 在什么条件下出现、为什么出现，以及是否能够通过一个轻量机制修复。

基于当前实验，本文的主要贡献可以概括为四点。第一，提出了面向 topology-aware federated bot detection 的 trust-aware hierarchical defense，并将 group coverage 作为方法核心，而不是附属超参。第二，系统比较了 GraphSAGE 与 FeatureMLP 在困难结构场景中的表现，证明 GraphSAGE 在 `scenario_h` 上具有显著优势。第三，结合 tuning、held-out validation、public auxiliary validation 与 classical robust baselines，说明该方法的主要安全收益在于降低毒参与，而不是泛化为“普遍提高 F1”。第四，通过固定种子机制分析识别出静态 group floor 的 principal failure mode，并进一步提出和验证 conditional trust-mass floor 作为 targeted hardening。

## 2. 相关工作

### 2.1 联邦网络安全检测

近年来，联邦学习已经被广泛用于入侵检测、恶意流量识别、IoT 安全监测等网络安全任务。相关研究普遍认为，联邦学习可以缓解原始数据集中化带来的隐私与治理问题，但也会放大统计异构性和系统非 IID 性带来的训练不稳定。在这一脉络下，本文的问题与 FL for cyber-security detection 高度相关，但又与常规 FL-IDS 存在差异：本文并非只关注特征向量分类，而是强调图结构上的 Bot 检测，并进一步关心不同客户端组之间的语义覆盖是否在鲁棒过程中被破坏。

### 2.2 投毒环境下的鲁棒联邦学习

鲁棒联邦学习领域已经提出了大量针对 Byzantine、backdoor 和 update poisoning 的方法，包括 Krum、Median、Trimmed Mean、基于异常更新检测的过滤，以及基于可信根或信任评分的聚合策略。这些方法对于理解本文 threat model 十分重要，因为本文同样关注恶意客户端如何通过更新污染全局模型。然而，多数此类方法默认客户端是平坦集合，对“某一语义组是否会被整个删空”缺少显式建模。本文的区别不在于否定这些鲁棒方法的意义，而在于指出：在语义分组联邦环境中，仅靠去掉可疑客户端并不足够，还必须考虑保留最低组覆盖。

### 2.3 图学习与安全分析

图神经网络已经在社交 Bot 检测、欺诈识别、异常检测和入侵检测等安全任务中展示出明显价值。相比仅利用静态特征的模型，图模型可以通过邻居传播捕获结构依赖。在本文所面对的 topology-aware 场景中，这一点尤为重要，因为不同客户端本身就对应不同子图或局部拓扑区域。GraphSAGE 之所以被选为本文主线实例，正是因为它在表达能力与复杂度之间提供了较合理平衡，同时适合在联邦环境下进行参数高效适配。

### 2.4 通信高效联邦适配

随着联邦系统部署到边缘和带宽受限场景，参数高效微调和通信高效优化逐渐成为现实部署的重要问题。对于本文而言，通信效率不是附属系统指标，而是与安全部署可行性密切相关的条件。因此，本文不仅比较了 backbone，也比较了 `head_only`、`adapter_ft` 与 `full_ft` 三种 tuning 模式，以回答一个实际问题：主线鲁棒性是否依赖于通信代价最高的 full fine-tuning。

### 2.5 本文工作定位

综上，本文位于 federated cyber-security detection、robust federated learning、graph-based security analytics 和 communication-efficient adaptation 的交叉点。本文最核心的差异化贡献，不是单纯把 GraphSAGE 用到了联邦 Bot 检测上，而是把 semantic group coverage 显式纳入 trust-filter design，并进一步通过机制实验解释这一设计的收益与边界。

## 3. 方法

### 3.1 系统设定

我们考虑一个由中心服务器和多个边缘客户端构成的联邦 Bot 检测系统。每个客户端在本地持有自身流量生成的图分区，并在不上传原始数据的前提下参与联邦训练。与传统平坦客户端设置不同，本文假设客户端可以根据角色、拓扑来源或分区元数据被划分为多个语义组。服务器的目标是在不集中原始数据的条件下，聚合这些客户端更新，训练一个对 Bot 检测有效且对恶意更新鲁棒的全局模型。

### 3.2 威胁模型

本文考虑参与训练的恶意客户端通过上传污染更新影响聚合结果，主要覆盖两类攻击：

- `sign_flip@0.4`：40% 客户端执行方向翻转类投毒；
- `update_noise@0.4`：40% 客户端注入大幅噪声更新。

该 threat model 并不要求攻击者控制全部客户端，而是关注当少数客户端恶意、且某些语义组本身规模较小时，系统能否维持稳定检测性能。

### 3.3 信任感知层次聚合

HiTrust-FedBot 先为每个客户端计算 trust score，信任信号来自验证表现和更新特征。然后系统并不直接将所有保留客户端放入一个扁平池中求平均，而是先在组内聚合，再在组间聚合。这样做的目的有两点：其一，避免大组更新直接淹没小组信息；其二，为 group-aware filtering 提供自然接口，使 trust filtering 与 grouped aggregation 形成一致设计。

### 3.4 组覆盖约束信任过滤

本文核心机制是在 trust threshold 过滤后，为每个语义组施加最小保留客户端数约束 `min_keep_per_group`。当前静态主线默认采用 `min_keep_per_group = 1`。这样可以避免某一组在某轮训练中因为 trust score 集体偏低而被整个抹除。

这一机制的意义在于，它将“组覆盖”正式提升为联邦鲁棒中的一级目标，而不是事后附会的解释变量。但这一机制也引入明确 trade-off：如果 group floor 过高，则被污染的组也更可能保留恶意客户端；如果 group floor 过低，则容易出现语义组整体消失。因而，本文专门通过敏感性实验来验证 `keep=1` 的合理性，而不是将其作为未经分析的启发式超参。

### 3.5 Conditional Trust-Mass Floor Hardening

静态 group floor 的问题在于它是无条件保组的。即使某个组的所有客户端在最终一轮已经表现出近乎塌缩的 trust mass，系统仍可能为了满足组覆盖而强行保留一个低信任代表。为此，本文实现了 conditional trust-mass floor：仅当某组的总归一化 trust mass 不低于阈值时，才执行 floor repair；否则允许该组 abstain。本文关键 hardening 实验中使用的阈值为 `0.10`。

### 3.6 Backbone 与 Tuning 模式

为区分结构学习与特征学习的贡献，本文比较了两类 backbone：

- `FeatureMLP`：主要依赖特征信息；
- `GraphSAGE`：显式利用图结构邻域传播。

同时，对 GraphSAGE 进一步比较三种 tuning 模式：

- `head_only`
- `adapter_ft`
- `full_ft`

这种设计使得本文能够同时回答 backbone、鲁棒性和通信效率三个问题。

## 4. 实验设置

### 4.1 场景族

主实验基于五个 topology-aware pilot scenarios：

- `scenario_d_three_tier_low2`
- `scenario_e_three_tier_high2`
- `scenario_f_two_tier_high2`
- `scenario_g_mimic_congest`
- `scenario_h_mimic_heavy_overlap`

其中，`scenario_h` 是最核心的语义重叠压力场景，`scenario_f` 是更难的 two-tier 场景，`scenario_g` 规模较小，后续结果表明其更接近饱和场景。除主场景外，本文还引入 `NSL-KDD` 作为 auxiliary public benchmark，以补强外部有效性。但需要强调，`NSL-KDD` 是公开 intrusion benchmark，而非与主任务同分布的公开 bot benchmark，因此它只能被定位为辅助 external validation。

### 4.2 评价指标

本文重点报告：

- `test_f1`
- `test_recall`
- `test_fpr`
- `kept_poisoned_clients`
- `total_bytes_est`

其中，`kept_poisoned_clients` 是解释 trust-aware mechanism 是否真正减少恶意参与的核心指标。

### 4.3 评估协议

实验由以下几部分构成：

- 五场景主线 cross-scenario matrix；
- `scenario_h` 与 `scenario_f` 的五种子稳定性；
- `scenario_h` 上的 GraphSAGE vs FeatureMLP 显著性比较；
- tuning / communication study；
- `scenario_e` 的 held-out trust-aware vs keep-all 对照；
- `NSL-KDD` 的 auxiliary public validation；
- `mean / median / krum` baseline 对照；
- `min_keep_per_group` 敏感性分析；
- `seed11` 固定种子机制诊断；
- `conditional trust-mass floor` hardening 验证。

## 5. 实验结果

### 5.1 跨场景主线结果

单次 cross-scenario matrix 显示，GraphSAGE hierarchical mainline 在五个场景上均维持较高水平。clean 条件下，五个场景 F1 在 `0.9692` 到 `0.9966` 之间；`sign_flip@0.4` 下在 `0.9696` 到 `0.9966` 之间；`update_noise@0.4` 下在 `0.9705` 到 `0.9966` 之间。具体来看，`scenario_h` 作为最具挑战性的压力场景，其单次 F1 仍可达到 clean `0.9692`、sign-flip `0.9696`、update-noise `0.9705`。这说明，在修复后的语义下，GraphSAGE 主线并没有出现“结构稍难就失守”的问题。

### 5.2 硬场景五种子稳定性

相比单次 run，更关键的是 hardest settings 的五种子结果。在 `scenario_h` 上，GraphSAGE 在 clean、sign-flip 和 update-noise 下的平均 F1 分别为 `0.9785`、`0.9797` 和 `0.9686`，对应标准差为 `0.0028`、`0.0026` 和 `0.0130`；在 `scenario_f` 上，对应平均 F1 分别为 `0.9859`、`0.9840` 和 `0.9867`，标准差均较小。由此可见，当前真正显著抬高方差的只有 `scenario_h + update_noise@0.4`，而不是整条主线普遍不稳。

### 5.3 Backbone 比较

GraphSAGE 在 `scenario_h` 上相对于 FeatureMLP 的提升已经得到五种子显著性支撑。clean 条件下，FeatureMLP 平均 F1 为 `0.9417`，GraphSAGE 为 `0.9785`，`p = 0.0095`；sign-flip 条件下，FeatureMLP 为 `0.9512`，GraphSAGE 为 `0.9797`，`p = 3.70e-4`。单次 run 层面的 FPR 也显示 GraphSAGE 显著更低。因此，在最重要的结构重叠压力场景中，GraphSAGE 的优势不仅存在，而且是统计显著的。

与此同时，`scenario_g` 的更新结果提醒我们不能夸大 backbone 结论。该场景 clean 条件下 FeatureMLP 为 `0.9975`、GraphSAGE 为 `1.0000`；sign-flip 条件下 FeatureMLP 为 `1.0000`、GraphSAGE 为 `0.9988`，两者差异均不显著。最合理解释是 `scenario_g` 已接近 ceiling，而不是 GraphSAGE 存在稳定反例。因此，本文对 backbone 的结论应写成“GraphSAGE 在 harder topology-aware scenarios 上显著更强”，而非“GraphSAGE 在所有场景都更优”。

### 5.4 Tuning 与通信效率

通信对联邦边缘部署具有直接现实意义。`scenario_h` 的 tuning study 表明，full fine-tuning 并不是主线成立的必要条件。在 `sign_flip@0.4` 下，`adapter_ft` 的 F1 为 `0.9696`、FPR 为 `0.0530`，而 `full_ft` 的 F1 为 `0.9666`、FPR 为 `0.0935`；同时，`adapter_ft` 只需 `19.45%` 的 full fine-tuning 通信开销。`head_only` 在该条件下也能保持 `0.9692` 的 F1，仅使用 `2.08%` 的 full fine-tuning 字节数。在 `update_noise@0.4` 下，`head_only` 的 F1 甚至略高于 `full_ft`。因此，当前最稳的工程结论是：HiTrust-FedBot 的核心鲁棒性并不依赖 full model adaptation，参数高效 tuning 已足以支撑主线效果。

### 5.5 Trust-Aware 与 Keep-All 对照

这一节是本文最核心的证据之一，因为它直接回答 trust-aware mechanism 究竟带来了什么。

在 `scenario_h` 上，clean 与 sign-flip 条件下，trust-aware 与 keep-all 在平均 F1 上几乎打平；但在 `update_noise@0.4` 下，trust-aware 将 retained poisoned clients 从 `4.0` 降到了 `0.4`，同时 F1 从 `0.9732` 降到 `0.9686`。这说明在 hardest setting 上，trust-aware 的主要贡献不是更高平均精度，而是更少毒参与。

held-out `scenario_e` 的结论更能支撑这一点。在 `update_noise@0.4` 下，trust-aware 平均 F1 为 `0.9879`，keep-all 为 `0.9890`，差异很小且不显著；但 retained poisoned clients 从 `4.0` 显著下降到 `0.2`。这一结果使本文可以更有把握地使用如下叙事：trust-aware filtering 是一种 conservative security control，其关键收益是显著减少 poisoned participation，同时将精度代价控制在 near-neutral 区间。

在 auxiliary public `NSL-KDD` 上也观察到类似模式。clean 条件下，trust-aware 的 F1 略低于 keep-all，但 FPR 更低；sign-flip 和 update-noise 条件下，trust-aware 与 keep-all 的平均 F1 基本持平，但 retained poisoned clients 明显下降。因此，public benchmark 并未支持“trust-aware 普遍提升 F1”，却强化了“trust-aware 更保守、更少毒参与”的方法画像。

### 5.6 聚合器对比

`scenario_h + sign_flip@0.4` 的 aggregation comparison 显示，hierarchical aggregation 的平均 F1 为 `0.9797`，FPR 为 `0.0212`；`mean` aggregation 的平均 F1 为 `0.9794`，FPR 略低；`median` 和 `krum` 的平均 F1 均约为 `0.976`，整体较弱。这个结果要求我们在写作上保持克制：hierarchical aggregation 并不是在每个指标上都绝对最优，但它属于 top-tier choice，而且与本文的 grouped trust-filter design 最一致。因此，本文应强调其“方法一致性 + 顶层性能”，而不是“全指标碾压”。

### 5.7 `min_keep_per_group` 敏感性

敏感性分析支持 `min_keep_per_group = 1` 作为静态主线默认值。clean 条件下，`keep=1` 相比 `keep=0` 提升了 F1 并降低了 FPR；sign-flip 条件下，`keep=1` 同样是最优折中；update-noise 条件下，`keep=2` 虽然在单次 run 上略高，但开始保留 poisoned clients。这说明 `keep=1` 不是拍脑袋设定，而是目前最合理的覆盖-鲁棒性折中点。

### 5.8 固定种子机制分析

进一步的 `seed11` 机制分析解释了为什么 `scenario_h + update_noise@0.4` 会成为当前主坏点。在该种子下，`role:benign_user` 小组的两个客户端都被投毒。`keep=0` 时，系统丢掉整个 benign 组，因此没有 retained poisoned client，但失去了组覆盖；`keep=1` 时，静态 floor 强行保留一个 benign 组代表，而这个代表其实是低 trust 的毒客户端，导致 F1 降至 `0.9496`、FPR 升至 `0.1028`；`keep=2` 时，两个毒客户端先在组内平均，再参与跨组聚合，结果反而比“单个毒客户端独占组代表”更不坏。这个结果说明：现有最坏情况不是 GraphSAGE backbone 崩溃，而是静态 group floor 在 fully poisoned small group 下的边界失效。

### 5.9 Conditional Trust-Mass Floor Hardening

针对上述 principal failure mode，本文实现了 conditional trust-mass floor。当某组总 trust mass 低于阈值 `0.10` 时，不再无条件执行 floor repair。在 `scenario_h + update_noise@0.4` 上，这一 hardening 使平均 F1 从 `0.9686` 提升到 `0.9766`，平均 FPR 从 `0.0449` 降到 `0.0231`，retained poisoned clients 从 `0.4` 降为 `0.0`，并显著降低了种子方差。最关键的是，原本最差的 `seed11` 从 `0.9496 / 0.1028` 修复到了 `0.9812 / 0.0125`。

不过，该 hardening 不应被过度拔高为 universal replacement。在 held-out `scenario_e + update_noise@0.4` 上，它表现为 near-neutral 到 slight positive；但在 auxiliary public `NSL-KDD` 上，它虽然进一步降低了 poisoned participation 和 FPR，却使 F1 从 `0.7882` 降到 `0.7611`。因此，目前最合理的定位是：conditional floor 是针对 topology-aware mainline principal failure mode 的 targeted hardening，而不是新的默认主线。

## 6. 讨论

综合以上结果，本文能够支撑的不是一个“普遍精度提升”的激进叙事，而是一个更克制也更可信的安全叙事。第一，HiTrust-FedBot 的价值主要体现在：在异构、受攻击的联邦图检测环境中，通过 trust-aware grouped defense 减少 poisoned participation，并尽量维持精度近似不变。第二，GraphSAGE 是当前最强的实例化方式，尤其适合结构敏感的困难场景。第三，当前主线确实存在边界坏点，但这一坏点已经被机制分析清楚地解释出来，而且可以通过一个小而可解释的机制进行修复。

从投稿角度看，这种叙事反而比“所有结果都更高”更适合网络安全期刊。原因在于，安全机制的价值并不只体现在平均数值，更体现在它是否解释了攻击面、是否诚实呈现失败模式，以及是否给出了可验证的修复方向。本文当前的实验体系之所以较早期版本更有说服力，正是因为它不再回避静态 floor 的边界问题，而是直接展示：问题发生在哪里、为什么发生、如何修。

## 7. 局限性

当前工作仍有若干局限。第一，主实验仍基于 topology-aware pilot scenarios，虽然已经补充了 `NSL-KDD`，但尚未覆盖与主任务完全同分布的公开 Bot benchmark。第二，public auxiliary benchmark 目前的种子数仍少于主线实验，因此外部结论的统计力度较有限。第三，baseline 集合虽然已纳入 `mean / median / krum` 等经典方案，但尚未穷尽更新的 dynamic abstention 或 personalized robust FL 防御。第四，conditional trust-mass floor 虽然在 topology-aware 主线上有效，但在 public auxiliary benchmark 上表现 mixed，因此不能被过度泛化。

## 8. 结论

本文提出 HiTrust-FedBot，一种将 trust-aware filtering、grouped hierarchical aggregation 和 group-coverage constraint 结合起来的联邦 Web Bot 检测框架。实验结果表明，GraphSAGE 主线在多个 topology-aware 场景上均维持较强鲁棒性，并在最关键的 `scenario_h` 场景中显著优于 FeatureMLP。更重要的是，trust-aware filtering 的核心收益被重新界定为：在总体精度近似不变的条件下显著减少 poisoned participation，而不是简单追求普遍更高 F1。进一步的机制分析说明，当前剩余最坏情况主要来自静态 group floor 在 fully poisoned small group 下的边界失效，而针对这一问题引入的 conditional trust-mass floor 能在 topology-aware 主线上有效修复该坏点。总体而言，这使得 HiTrust-FedBot 不仅在实验上更稳，也在方法解释上更成熟，为后续面向网络安全期刊的正式投稿提供了较坚实基础。

## 附：建议导师重点先看三处

如果用于导师快速审阅，建议优先关注以下三处：

1. 第 5.5 节：trust-aware vs keep-all 的重新定位。
2. 第 5.8 节：`seed11` 机制分析，解释为什么 static floor 会在极端条件下失效。
3. 第 5.9 节：conditional trust-mass floor 作为 targeted hardening 的效果与边界。
