# 第四章 实验设置

说明：本章为中文导师阅览版，正文沿用 BlockSys/Springer LNCS 常见的数字引用风格，在文中使用 `[1]`、`[2]` 等顺序编号。参考文献均为真实已发表条目，并附 DOI 链接。由于该文件当前作为独立章节草稿使用，编号在本章内单独顺排；后续并入整篇论文时可统一重排。

## 4.1 实验目标与设计原则

本章实验设置服务于四个相互关联的问题。第一，HiTrust-FedBot 在 topology-aware federated bot detection 场景中是否具有跨场景稳定性，而不是只在单一示例图上偶然成立。第二，主线 GraphSAGE 实例化是否确实优于只依赖节点特征的 FeatureMLP，尤其是在结构重叠更强、局部语义更复杂的困难场景中 [1-3]。第三，trust-aware filtering 的核心价值究竟体现为平均精度提升，还是体现为更保守地减少 poisoned participation [1,4]。第四，静态 group floor 的边界失效是否可被明确诊断，并通过轻量 hardening 机制修复。

围绕这些问题，本文没有把所有实验混成一组大表，而是按证据链组织实验设置。具体而言，实验分为五个层次：跨场景主线评估、困难场景多种子稳定性、backbone 与 tuning mode 对照、trust-aware 与 keep-all 的安全收益对照，以及 conditional trust-mass floor 的 targeted hardening 验证。这样的设计目的不是堆叠更多数值，而是让每一组实验回答一个清晰问题，并让不同实验之间形成递进关系。

## 4.2 数据与场景家族

### 4.2.1 Topology-Aware Pilot Scenarios

主实验基于五个 bootstrap graph pilot scenarios。它们分别是 `scenario_d_three_tier_low2`、`scenario_e_three_tier_high2`、`scenario_f_two_tier_high2`、`scenario_g_mimic_congest` 和 `scenario_h_mimic_heavy_overlap`。这些图均已预构建并写入 `data_hitrust/bootstrap_graphs/graphs/`，图索引文件显示五个场景均构建成功。五个场景的图统计如表 4-1 所示。

| 场景 | 节点数 | 边数 | 流节点数 | 良性流节点 | 攻击流节点 | 特征维数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `scenario_d_three_tier_low2` | 4596 | 5533 | 4595 | 698 | 3897 | 7 |
| `scenario_e_three_tier_high2` | 5976 | 8142 | 5975 | 2137 | 3838 | 7 |
| `scenario_f_two_tier_high2` | 4794 | 6656 | 4793 | 1996 | 2797 | 7 |
| `scenario_g_mimic_congest` | 1407 | 1657 | 1406 | 870 | 536 | 7 |
| `scenario_h_mimic_heavy_overlap` | 6985 | 9755 | 6984 | 2123 | 4861 | 7 |

这五个场景承担的角色并不完全相同。`scenario_h` 是本文主叙事中的核心压力场景，因为它同时包含更强的语义重叠与更复杂的局部结构干扰；`scenario_f` 是较难的 two-tier 场景，用于检验主线是否只在某一种图结构上有效；`scenario_e` 在本文中被视为 held-out validation scenario，用于补强“不是只在主舞台成立”的证据；`scenario_g` 规模较小，后续结果表明其更接近饱和场景，因此主要用于说明 backbone 结论的边界，而不是作为主证据来源。

对于这五个 bootstrap 图，训练、验证和测试划分采用时间窗口驱动的 temporal split。实现上，系统依据 `window_idx` 进行 `60\% / 20\% / 20\%` 的 train/val/test 划分，并且仅将 flow nodes 纳入损失计算和最终评估；共享支撑节点只提供图上下文，不单独作为评测对象。这样的设置与联邦网络安全检测中的时间因果约束更一致，也避免了把后续窗口信息泄漏到训练过程 [1,2]。

### 4.2.2 Auxiliary Public Validation

为了补强外部有效性，本文进一步引入 `NSL-KDD` 作为 auxiliary public benchmark。需要明确的是，这一公开数据点承担的是“辅助外部验证”而不是“同分布主任务替代品”的角色。也就是说，它能够检验 trust-aware filtering 的保守安全控制特征是否能迁移到公开 intrusion benchmark 上，但并不能把主场景家族中的 topology-aware 证据完全替代掉。

当前公开图版本的 `NSL-KDD` 统计如下：共 `14000` 条样本，`117` 维特征，`73631` 条边，`151` 个 owner，协议角色数为 `3`，其中训练/验证/测试划分分别为 `8000 / 2000 / 4000`。标签分布为 `7062` 个 normal 与 `6938` 个 attack，攻击比例约为 `0.4956`。该公开图的边构建还记录了 `owner_bucket_size = 128` 与 `knn_k = 8`。这些统计表明，`NSL-KDD` 并不是一个极端稀疏或极端失衡的辅助点，而是一个足以检验主线机制是否具备一定外推性的公开图数据点。

## 4.3 联邦协议与默认超参数

除非实验明确改变某一因素，本文主线实验统一采用相同的联邦协议。默认配置文件 `real_graph_pilot_h_scenario_h_sage_clean.json` 和 `public_nslkdd_hierarchical_sage_clean.json` 显示，主线设置为：`num_clients = 10`、`partition_mode = topology_noniid`、`aggregation = hierarchical`、`num_groups = 3`、`hidden_dim = 32`、`adapter_dim = 8`、`backbone = sage`、`tuning_mode = adapter_ft`、`global_warmup_epochs = 8`、`rounds = 5`、`local_epochs = 1`、`lr = 0.01`、`trust_threshold = 0.35`、`min_keep_per_group = 1`。因此，第四章中的各组对照实验可以被解释为“在统一联邦协议上改变单个关键变量”，而不是多种因素同时漂移。

其中，`topology_noniid` 划分方式对应本文的 deployment assumption，即客户端拥有不同局部子图，语义与负载天然异构。`num_groups = 3` 为 grouped federation 提供最小可解释结构，使后续 trust-aware filtering 与分层聚合能够在组层面展开。`adapter_ft` 被设为默认 tuning mode，不是因为它天然最优，而是因为前期实验显示 parameter-efficient tuning 更适合在通信开销与鲁棒性之间取得稳定折中 [1,5]。

在所有主线运行中，模型先进行 `8` 个 epoch 的 global warmup，然后进入 `5` 轮联邦训练，每轮每个活跃客户端执行 `1` 个本地 epoch。本文没有把本地训练轮数设得很高，原因是我们更关注边缘联邦条件下“短轮次、轻更新、可落地”的安全控制，而不是用更长本地优化去掩盖聚合与过滤设计本身的边界。

## 4.4 攻击设置与比较对象

### 4.4.1 攻击设置

本文使用三类训练条件：

1. `clean`：无投毒客户端，即 `poison_frac = 0.0`，`poison_type = none`。
2. `sign_flip@0.4`：`40\%` 恶意客户端执行符号翻转攻击，对应 `poison_frac = 0.4`、`poison_type = sign_flip`、`poison_scale = 1.0`。
3. `update_noise@0.4`：`40\%` 恶意客户端注入高斯噪声更新，对应 `poison_frac = 0.4`、`poison_type = update_noise`、`poison_scale = 0.2`。

实现上，恶意客户端集合由当前轮活跃客户端中抽取，因而与“真实能参与训练的客户端池”一致，而不是在理论全集上预先硬编码。本文之所以将主攻击比例固定为 `0.4`，是因为该强度既足以显著暴露静态 floor 的 failure mode，也不会强到让所有比较对象同时完全失效，从而保留方法差异的可观察性 [1,4]。

### 4.4.2 对照对象

为保证实验叙事自洽，本文设置了四类对照。

1. `backbone` 对照：`GraphSAGE` 对比 `FeatureMLP`，用于检验结构建模本身是否有增益。
2. `trust-aware` 对照：默认主线对比 `keep-all`。其中 `keep-all` 通过设置 `trust_threshold = 0.0` 和 `min_keep_per_group = 0` 实现，即不做 trust filtering，也不做 group floor 修复。
3. `aggregation` 对照：在统一 GraphSAGE 与相同攻击条件下，比较 `hierarchical`、`mean`、`median` 与 `krum` proxy。
4. `tuning` 对照：比较 `head_only`、`adapter_ft` 与 `full_ft` 三种参数更新模式。

除此之外，本文还进行了两类机制诊断实验。第一类是 `min_keep_per_group` 敏感性分析，分别考察 `keep=0`、`keep=1` 和 `keep=2`。第二类是 `conditional trust-mass floor` hardening，即在默认 `trust_threshold = 0.35`、`min_keep_per_group = 1` 基础上，引入 `group_floor_policy = conditional_trust_mass` 与 `group_floor_min_trust_mass = 0.10`，用于验证静态 floor principal failure mode 是否可修复。

## 4.5 评价指标与统计协议

### 4.5.1 指标体系

本文主要报告六类指标：

1. `test_f1`：作为总体检测效果的主指标。
2. `test_recall`：用于观察恶意流量的召回能力。
3. `test_fpr`：用于约束误报风险。
4. `kept_clients`：记录过滤后仍参与最终聚合的客户端数。
5. `kept_poisoned_clients`：记录最终仍被保留的恶意客户端数。
6. `total_bytes_est`：基于可训练参数数量估计的总通信字节开销。

其中，`kept_poisoned_clients` 是本文解释 trust-aware filtering 安全价值时的关键指标。因为本文当前最稳的结论并不是“trust-aware 普遍提高 F1”，而是“trust-aware 在多数设置下以 near-neutral 的精度代价减少 poisoned participation”。如果不报告这一指标，方法收益会被错误压缩为单纯的精度比较。

通信开销指标 `total_bytes_est` 则服务于 tuning study。实现上，它由单精度参数字节数、每轮活跃客户端数和总轮数共同决定，因此更适合作为相对开销比较，而不是作为硬件无关的绝对部署成本。

### 4.5.2 阈值选择与测试协议

每轮训练结束后，系统先在验证集上搜索分类阈值，再用该阈值计算测试集指标。具体而言，验证阈值在 `0.10` 到 `0.90` 之间以 `0.05` 步长枚举，并选择验证 `F1` 最高的阈值作为该轮的 best threshold。最终报告的测试 `F1`、`Recall` 与 `FPR` 均由最终轮 best threshold 计算得出。

这一设置有两个作用。第一，它避免了固定 `0.5` 阈值在不同场景、不同攻击条件下造成额外偏差。第二，它使 trust-aware 与 keep-all、GraphSAGE 与 FeatureMLP 之间的比较建立在相同的 validation-to-test protocol 上，从而减少阈值选择策略本身对结论的污染。

### 4.5.3 多种子与显著性检验

单次运行主要用于跨场景主线矩阵、调参图和机制示例，默认种子为 `42`；更关键的稳定性结论来自多种子实验。对 `scenario_h`、`scenario_f` 以及 held-out `scenario_e`，本文使用五个随机种子 `11, 22, 33, 44, 55` 进行 seed sweep。对 public auxiliary `NSL-KDD`，当前使用三个随机种子 `11, 22, 33`，其统计力弱于主线五种子实验，因此本文在叙事上始终将其定位为“补强证据”，而不是主判断来源。

对于多种子对照，本文统一报告均值和标准差，并在需要比较 backbone 或 trust-aware/keep-all 的主指标时，使用 Welch two-sample t-test 计算 `p` 值。实现脚本 `build_significance_report.py` 中显式采用 `stats.ttest_ind(..., equal_var=False)`，因此第四章后续出现的显著性结果均可解释为不等方差双样本 `t` 检验，而不是依赖人工挑选单次 run。

## 4.6 复现产物与实验输出组织

为了支撑投稿阶段的 artifact 叙事，当前实验流程会为每次运行写出三类核心文件：`summary.json`、`trust_trace.json` 和 `client_partition.json`。其中 `summary.json` 记录最终指标、通信估计与轮级结果；`trust_trace.json` 保留轮级 trust score 轨迹；`client_partition.json` 保存客户端划分与分组信息。后续所有图表与汇总表均从这些运行产物生成，而不是人工抄写或手工拼表。

当前 artifact 清单还明确给出了两份复现实验脚本：`core_experiments/reproduce/reproduce_public_nslkdd_validation.sh` 与 `core_experiments/reproduce/reproduce_conditional_floor_validation.sh`。对应结果表图分别落在 `paper_hitrust/tables/` 与 `paper_hitrust/figures/` 下。这一组织方式意味着第四章的实验设置不仅可读，而且具有明确的产物路径、复现实验入口和结果到图表的映射关系。

综上，本章实验设置的核心特点不是“参数很多”，而是“变量控制清楚”。主协议、默认超参数、攻击强度、种子集合、比较对象与显著性方法都被显式固定，从而使第五章的结果讨论能够尽量建立在单因素比较与可追踪产物之上，而不是建立在隐含配置漂移之上。

## 第四章参考文献

[1] Li, T., Sahu, A.K., Talwalkar, A., Smith, V.: Federated Learning: Challenges, Methods, and Future Directions. *IEEE Signal Processing Magazine* 37(3), 50-60 (2020). DOI: https://doi.org/10.1109/MSP.2020.2975749

[2] Ferrag, M.A., Friha, O., Maglaras, L., Janicke, H., Shu, L.: Federated Deep Learning for Cyber Security in the Internet of Things: Concepts, Applications, and Experimental Analysis. *IEEE Access* 9, 138509-138542 (2021). DOI: https://doi.org/10.1109/ACCESS.2021.3118642

[3] Bilot, T., El Madhoun, N., Al Agha, K., Zouaoui, A.: Graph Neural Networks for Intrusion Detection: A Survey. *IEEE Access* 11, 49114-49139 (2023). DOI: https://doi.org/10.1109/ACCESS.2023.3275789

[4] Mothukuri, V., Parizi, R.M., Pouriyeh, S., Huang, Y., Dehghantanha, A., Srivastava, G.: A survey on security and privacy of federated learning. *Future Generation Computer Systems* 115, 619-640 (2021). DOI: https://doi.org/10.1016/j.future.2020.10.007

[5] Pouriyeh, S., Shahid, O., Parizi, R.M., Sheng, Q.Z., Srivastava, G., Zhao, L., Nasajpour, M.: Secure Smart Communication Efficiency in Federated Learning: Achievements and Challenges. *Applied Sciences* 12(18), 8980 (2022). DOI: https://doi.org/10.3390/app12188980
