# 第六章 讨论、局限性与威胁模型边界

说明：本章为中文导师阅览版，正文采用 BlockSys/Springer LNCS 常见的数字引用风格，在文中使用 `[1]`、`[2]` 等顺序编号。与前文保持一致，本章不追求“扩大结论”，而是追求“把证据能支持到哪里、不能支持到哪里”写清楚。就当前版本而言，最稳妥的总体定位不是“本文提出了一种在各类联邦投毒环境中普遍优于现有方法的通用方案”，而是“本文给出了一条面向 topology-aware federated bot detection 的保守安全控制主线，并识别、诊断和部分修复了其关键边界失效模式”。

## 6.1 本文当前真正能够支撑的结论

结合第五章全部结果，本文当前最有把握支撑的结论可以收束为五点。第一，`GraphSAGE` 主线在五个 topology-aware pilot scenarios 上整体成立，说明当客户端之间的关系结构确实包含任务相关信号时，结构建模能够为联邦 Bot 检测提供稳定收益 [6-8]。第二，`GraphSAGE` 的优势主要体现在更困难、更加依赖结构语义的场景上，而不是在所有数据点上无条件扩大边际收益；`scenario_g` 这类接近饱和的边界场景并不支持夸张表述。第三，`trust-aware filtering` 的主要作用不是普遍提高平均 `F1`，而是减少被保留的恶意参与，并在多数设置下把精度代价压到 `near-neutral` 区间。第四，静态 `group floor` 的默认值 `min_keep_per_group = 1` 是一个合理折中，但它并非没有代价，而是在 fully poisoned small group 条件下存在明确的 principal failure mode。第五，`conditional trust-mass floor` 能在 topology-aware 主线中有效修复这一主坏点，但其收益并不自动外推到所有 auxiliary public benchmark。

这些结论共同构成了一个较为克制但更可信的研究画像。换言之，本文最强的论点不是“trust-aware 普遍提分”，也不是“condfloor 全面替代 static floor”，而是：在面向结构化客户端关系的联邦安全检测任务中，结构建模与信任过滤可以被组织成一个保守的安全控制回路；该回路的主要价值在于抑制 poisoned participation，并在识别出 principal failure mode 之后继续给出可验证的 targeted hardening 方向。

> **表 6-1 占位**  
> 表题：本文当前可直接支持的结论、证据基础与不宜采用的过度表述。  
> 表注：建议设置四列：`结论主题`、`直接证据`、`当前安全写法`、`应避免的过度写法`。该表不依赖额外实验文件，可根据第 5 章与本章正文人工整理，用于在全文定稿阶段统一压住叙事口径。

## 6.2 威胁模型边界

### 6.2.1 攻击能力边界

本文当前覆盖的是客户端侧更新投毒场景，且主要聚焦于 `sign_flip` 与 `update_noise` 两类训练阶段攻击。这一选择与现有联邦安全研究中对模型投毒和鲁棒聚合的经典问题设定一致 [2-5]，因此足以支撑“本文方法对一类典型恶意更新具有防护价值”的结论；但它并不等价于“本文已经覆盖了联邦环境中的全部攻击面”。例如，本文尚未系统评估自适应白盒攻击、显式协同攻击、Sybil 型多身份攻击、针对后门触发器的语义注入攻击，以及专门针对 trust score 设计的规避型攻击。对于这些更强攻击者，当前结果最多只能提供启发，而不能提供确定性保证。

此外，本文默认攻击者的主要控制对象是部分客户端，而不是中心协调端。系统中 `validation gain`、更新相似度、稳定性与范数惩罚的计算，都要求协调端能够观察并评估客户端更新。这意味着本文默认服务器侧控制逻辑本身是可信的，至少不是本文重点分析的攻击对象。若把威胁模型扩展到服务器被攻陷、服务器验证集被污染，或服务器与部分恶意客户端串通的场景，则当前 defense pipeline 的有效性需要重新评估。

### 6.2.2 系统与数据边界

本文的主证据主要来自五个 topology-aware pilot scenarios、一个 held-out scenario，以及一个 auxiliary public `NSL-KDD` 验证设置。这样的设计兼顾了可控机制分析与一定程度的外部验证，但其外推边界也必须诚实说明。首先，pilot scenarios 虽然已经覆盖多种图拓扑与组结构变化，但它们仍属于围绕主任务语义构造的实验家族，而不是多个完全独立来源的大规模真实平台数据。其次，`NSL-KDD` 的公开验证价值主要在于补强“方法不是只在内部数据上成立”，而不是证明“方法已经在公开 Bot benchmark 上完成同分布复现”。因此，`NSL-KDD` 应被理解为 auxiliary external validation，而非主任务的完全替代物。

从系统规模看，当前默认协议采用 `10` 个客户端、`3` 个语义组、`5` 轮联邦训练和较短本地更新周期。该设定适合做机制对照和多种子复现，但仍不足以代表跨设备大规模联邦网络中更强的异步性、掉线率、负载波动和超大规模 non-IID 分布 [1,6,9]。因此，本文可以较有把握地讨论“小到中等规模、分组语义明确、存在结构信号”的联邦安全检测环境，但不应直接把现有结果上升为“大规模开放联邦系统的通用性能结论”。

### 6.2.3 防御机制边界

本文中的 trust score 本质上是一个基于验证增益、相似度、稳定性与正则惩罚项组合形成的连续启发式指标，而不是带有严格最优性证明或安全下界证明的形式化判据。换言之，较高的 `trust_norm` 更接近“在当前轮、当前验证协议和当前组结构下更值得保留”，而不是“该客户端在更一般意义上可信”。这一区别非常重要，因为它决定了本文的防御结论应保持统计性和经验性，而不应写成形式化安全保证。

同样地，`conditional trust-mass floor` 的定位也应保持克制。第五章已经显示，它在 topology-aware 主线和 held-out 场景中对 static floor 的 principal failure mode 具有明确修复作用，但在 auxiliary public benchmark 上呈现 mixed behavior。由此可以看出，condfloor 更像一个针对已识别主坏点的局部 hardening 机制，而不是可以脱离任务语义、数据分布与组结构直接推广的 universal default。

> **表 6-2 占位**  
> 表题：本文威胁模型边界、已覆盖风险与未覆盖风险。  
> 表注：建议设置五列：`维度`、`当前覆盖`、`未覆盖或仅部分覆盖`、`对论文结论的影响`、`后续补强方向`。维度可包括 `攻击者能力`、`服务器可信性`、`客户端规模`、`数据分布`、`聚合可见性` 与 `公开验证范围`。该表同样建议由正文内容人工整理。

## 6.3 当前方法的主要局限性

### 6.3.1 外部有效性仍然有限

尽管本文已经加入 held-out `scenario_e` 和 auxiliary public `NSL-KDD`，当前证据仍然主要建立在 topology-aware 主线语义之上。从外部有效性的标准看，这样的设计已经明显优于“只做单数据集单场景单种子”的实验组织，但仍不足以完全封闭外部有效性问题。更具体地说，本文目前能够说明“该方法在一个具有明确结构语义的场景家族中成立，并在一个公开辅助数据上保留了部分保守防御特征”，但还不能说明“只要是公开网络安全数据，本文方法都会以同样方式成立”。

### 6.3.2 攻击空间仍然偏窄

从鲁棒联邦学习的完整攻击面来看，现有实验主要覆盖了恶意更新扰动，而尚未覆盖更复杂的适应性攻击路径 [2-4]。这意味着，本文现在更接近一篇“机制清楚、边界清楚的 targeted defence study”，而不是一篇已经遍历大部分联邦攻击面的大而全防御论文。这样的定位并不削弱研究价值，但要求正文在结论外推上保持克制。

### 6.3.3 防御依赖可见更新，尚未处理与隐私机制的张力

本文的 trust-aware pipeline 需要服务器侧获得足够多的更新层面信息，才能计算 `validation gain`、更新相似度、稳定性和范数惩罚。因此，该设计与“服务器不可见单客户端更新”的严格隐私聚合机制之间天然存在张力。进一步说，若未来需要同时引入 secure aggregation、差分隐私噪声或更强的加密计算协议，则 trust scoring 的计算方式、代价以及精度鲁棒性平衡都可能发生变化。当前版本尚未解决这一问题，因此本文更适合被理解为“在服务器具有观测和控制能力的受管联邦环境中的安全控制设计”，而不是“对隐私增强联邦训练同样无缝适用的通用框架”。

### 6.3.4 系统代价评估仍以通信为主，尚未形成完整工程画像

第五章已经说明，`adapter_ft` 在性能与通信量之间给出了很好的折中，这一点与联邦系统中对通信效率的长期关注一致 [1,9]。但当前代价分析仍主要停留在 `total_bytes_est` 层面，尚未系统报告 wall-clock latency、客户端显存占用、分组构图开销、trust scoring 附加计算代价，以及不同硬件平台下的端到端训练时间。对于真正面向部署的论文，这些因素都会影响方法的工程说服力。因此，本文现阶段更适合声称“通信层面具备较好的部署可行性”，而不是“整体系统开销已经全面受控”。

### 6.3.5 阈值与分组语义仍带有任务依赖性

当前主线使用的 `trust_threshold = 0.35`、`min_keep_per_group = 1` 以及 `group_floor_min_trust_mass = 0.10` 已在现有实验中得到较充分支持，但这些设置并不应被误写为与任务无关的普适默认值。尤其是，组语义本身直接影响 trust filtering 与 group floor 的行为边界。若未来应用场景中的分组不是由相对稳定的行为语义构成，而是更松散、更嘈杂甚至被攻击者主动操控，那么当前机制的有效性可能明显下降。换言之，本文方法对“分组是否有意义”这一前提具有依赖性。

## 6.4 对实际部署的含义

尽管存在上述限制，本文结果仍然给出了一些明确而实用的部署启示。首先，对于存在客户端关系结构、又受通信预算限制的受管联邦环境，`GraphSAGE + adapter_ft` 可以作为比 `full_ft` 更稳妥的默认主线。它的优势不只是通信更轻，还在于在当前语义下并不依赖更重的全参数更新才能维持主线性能。

其次，`trust-aware filtering` 更适合作为一种 safety-first 的安全控制，而不是被理解为追求平均分数最大化的性能增强器。也就是说，若系统目标更关注“尽量减少恶意参与被保留到聚合环节”，那么 trust-aware 的部署价值是明确的；若系统目标单纯追求某一项平均分类指标的最大化，则其收益应结合具体数据分布谨慎评估。

再次，`conditional trust-mass floor` 不宜被当作默认总开关，而更适合在已经识别出 small-group fully poisoned 风险时按条件启用。当前证据支持把它写成“针对主坏点的局部硬化模块”，而不是“替代 static floor 的普遍最优方案”。从工程角度看，这意味着部署时应额外监控组级 trust mass、被保留恶意参与数量以及误报变化，而不是只盯住平均 `F1`。

> **表 6-3 占位**  
> 表题：面向受管联邦安全检测部署的建议配置与启用条件。  
> 表注：建议列出 `模块`、`建议默认值`、`适用条件`、`不建议启用的情形` 与 `建议监控指标` 五列。可覆盖 `backbone`、`tuning mode`、`trust-aware filtering`、`static floor` 与 `conditional trust-mass floor`。该表有助于把论文讨论部分与未来 artifact/系统实现对接。

## 6.5 后续工作方向

结合当前结果，后续工作至少有五条方向值得优先推进。第一，补充更接近主任务分布的公开图安全数据或公开 Bot 数据，以进一步加强外部有效性。第二，系统评估自适应攻击、协同攻击、Sybil 攻击和后门攻击，检验 trust scoring 与 group floor 在更强攻击者下的脆弱点。第三，研究与 secure aggregation 或隐私增强机制兼容的 trust surrogate，使服务器不必直接暴露在完整客户端更新之上。第四，把当前 `10` 客户端级别的实验扩展到更大规模、更强异步、更高掉线率的设置，以补足系统层证据。第五，继续完善 artifact release，把场景生成、运行脚本、表图生成和主结论复现路径打包成更标准的可复现实验资产。

需要强调的是，这些后续方向并不是为了“推翻”当前工作，而是为了把本文从一篇机制清楚、证据链完整的 topology-aware defence study，进一步推进为一篇兼具外部验证、攻击覆盖和工程可部署性的更强系统安全论文。

## 6.6 本章小结

本章的核心任务不是继续增加结果，而是界定结果的含义边界。综合全文可以看到，本文已经形成了一条相对完整的研究闭环：通过结构建模与分组联邦建立主线，通过 trust-aware filtering 实现保守安全控制，通过 fixed-seed 机制诊断识别 static floor 的 principal failure mode，再通过 conditional trust-mass floor 给出可验证的 targeted hardening。与此同时，本文也明确存在若干不能回避的限制，包括攻击空间尚未充分展开、公开外部验证仍偏辅助、系统代价评估尚不完整，以及方法对服务器可见性和分组语义具有依赖。

因此，最适合本研究的总体表述应当是：本文并未声称给出一种对所有联邦安全问题普适有效的防御框架，而是针对 topology-aware federated bot detection 提出并验证了一条更保守、更可诊断、边界更清楚的安全控制主线。对于当前版本而言，这种克制并不是弱点，恰恰是使全文更可信、更接近成熟网络安全论文写法的关键。

## 第六章参考文献

[1] Li, T., Sahu, A.K., Talwalkar, A., Smith, V.: Federated Learning: Challenges, Methods, and Future Directions. *IEEE Signal Processing Magazine* 37(3), 50-60 (2020). DOI: https://doi.org/10.1109/MSP.2020.2975749

[2] Mothukuri, V., Parizi, R.M., Pouriyeh, S., Huang, Y., Dehghantanha, A., Srivastava, G.: A survey on security and privacy of federated learning. *Future Generation Computer Systems* 115, 619-640 (2021). DOI: https://doi.org/10.1016/j.future.2020.10.007

[3] Liu, P., Xu, X., Wang, W.: Threats, attacks and defenses to federated learning: issues, taxonomy and perspectives. *Cybersecurity* 5(1), Article 4 (2022). DOI: https://doi.org/10.1186/s42400-021-00105-6

[4] Qammar, A., Ding, J., Ning, H.: Federated learning attack surface: taxonomy, cyber defences, challenges, and future directions. *Artificial Intelligence Review* 55(5), 3569-3606 (2022). DOI: https://doi.org/10.1007/s10462-021-10098-w

[5] Cao, X., Fang, M., Liu, J., Gong, N.Z.: FLTrust: Byzantine-robust Federated Learning via Trust Bootstrapping. *Proceedings 2021 Network and Distributed System Security Symposium* (2021). DOI: https://doi.org/10.14722/ndss.2021.24434

[6] Ferrag, M.A., Friha, O., Maglaras, L., Janicke, H., Shu, L.: Federated Deep Learning for Cyber Security in the Internet of Things: Concepts, Applications, and Experimental Analysis. *IEEE Access* 9, 138509-138542 (2021). DOI: https://doi.org/10.1109/ACCESS.2021.3118642

[7] Bilot, T., El Madhoun, N., Al Agha, K., Zouaoui, A.: Graph Neural Networks for Intrusion Detection: A Survey. *IEEE Access* 11, 49114-49139 (2023). DOI: https://doi.org/10.1109/ACCESS.2023.3275789

[8] Wu, Z., Pan, S., Chen, F., Long, G., Zhang, C., Yu, P.S.: A Comprehensive Survey on Graph Neural Networks. *IEEE Transactions on Neural Networks and Learning Systems* 32(1), 4-24 (2021). DOI: https://doi.org/10.1109/TNNLS.2020.2978386

[9] Pouriyeh, S., Shahid, O., Parizi, R.M., Sheng, Q.Z., Srivastava, G., Zhao, L., Nasajpour, M.: Secure Smart Communication Efficiency in Federated Learning: Achievements and Challenges. *Applied Sciences* 12(18), 8980 (2022). DOI: https://doi.org/10.3390/app12188980
