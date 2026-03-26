# 第五章 实验结果与分析

说明：本章为中文导师阅览版，正文沿用 BlockSys/Springer LNCS 常见的数字引用风格，但本章以结果分析为主，不额外堆叠无必要引用。写作口径保持克制：本文当前最稳的结论不是“trust-aware 普遍提升 F1”，而是“trust-aware filtering 是一种更保守的安全控制，其核心收益是减少 poisoned participation，并在多数设置下把精度代价压到 near-neutral 区间”。

## 5.1 本章定位与图表安排

第五章是全文的重心，因此本章不应被写成“依次读数值”的结果堆砌，而应被组织成一条清晰证据链：先证明 GraphSAGE 主线在 topology-aware 场景家族中整体稳定，再证明结构建模在困难场景中确有增益，随后说明 trust-aware filtering 的真实收益并不在于普遍提高平均 F1，而在于减少被保留的恶意参与；最后，把 principal failure mode、机制诊断与 conditional hardening 连成闭环。

基于当前图表产物，建议正文优先保留以下图表：

- 图 5-1：`cross_scenario_f1_heatmap.png`
- 图 5-2：`backbone_comparison.png`
- 图 5-3：`comm_tradeoff.png`
- 图 5-4：`scenario_e_trust_vs_keepall_seed_comparison.png`
- 图 5-5：`seed11_keep_sweep_h_sage_update_noise_frac0p4_mechanism.png`
- 图 5-6：`scenario_h_update_noise_condfloor_comparison.png`
- 表 5-1：`cross_scenario_sage_full_matrix.json`
- 表 5-2：`hard_case_sage_seed_summary.json`
- 表 5-3：`backbone_clean_f1_significance.json`、`backbone_sign_flip_frac0p4_f1_significance.json`、`scenario_g_backbone_seed_comparison.json`
- 表 5-4：`real_graph_pilot_h_scenario_h_sage_tuning_modes.json`、`tuning_modes_sage_sign_flip_frac0p4_summary.json`、`tuning_modes_sage_update_noise_frac0p4_summary.json`
- 表 5-5：`scenario_h_trust_vs_keepall_seed_comparison.json`、`scenario_e_trust_vs_keepall_seed_comparison.json`、`public_nslkdd_trust_vs_keepall_seed_comparison.json`
- 表 5-6：`aggregation_sign_flip_frac0p4_sage_group_stats.json`
- 表 5-7：`min_keep_per_group_sage_sensitivity.json`
- 表 5-8：`seed11_keep_sweep_h_sage_update_noise_frac0p4_mechanism.json`
- 表 5-9：`scenario_h_update_noise_condfloor_comparison.json`、`scenario_e_update_noise_condfloor_comparison.json`、`public_nslkdd_update_noise_condfloor_comparison.json`
- 表 5-10：`public_nslkdd_update_noise_baseline_comparison.json`

若版面受限，建议优先把以下图表移入补充材料，而不是删掉：

- `aggregation_sign_flip_comparison.png`
- `scenario_h_trust_vs_keepall_seed_comparison.png`
- `public_nslkdd_trust_vs_keepall_seed_comparison.png`
- `min_keep_per_group_sensitivity.png`
- `scenario_e_update_noise_condfloor_comparison.png`
- `public_nslkdd_update_noise_condfloor_comparison.png`
- `public_nslkdd_update_noise_baseline_comparison.png`
- `scenario_h_clean_condfloor_comparison.json`
- `scenario_h_sign_flip_condfloor_comparison.json`

## 5.2 跨场景主线结果：GraphSAGE 主线是否站得住

首先需要回答的不是“某个场景数值高不高”，而是主线方法在多个 topology-aware 场景上是否整体成立。跨场景单次矩阵结果表明，GraphSAGE hierarchical mainline 在五个 pilot scenarios 上都维持了较高水平，没有出现“某一类攻击一来就整体失守”的情形。特别是最关键的 `scenario_h`，在 `clean`、`sign_flip@0.4` 和 `update_noise@0.4` 条件下的单次 `test_f1` 分别为 `0.9692`、`0.9696` 和 `0.9705`。这意味着，在修复后的语义设置下，主线方法并没有出现结构困难场景中的系统性崩塌。

更重要的是，跨场景结果不是“只在最容易的场景里好看”。`scenario_d` 接近饱和，三种条件下 F1 都约为 `0.9966`；`scenario_e` 作为 held-out scenario，三种条件下仍保持在 `0.9826` 到 `0.9835`；`scenario_f` 作为较难的 two-tier 场景，三种条件下分别为 `0.9743`、`0.9720` 和 `0.9767`；`scenario_g` 虽规模较小，但仍在 `0.9756` 到 `0.9938` 之间。这个矩阵支持的主结论是：GraphSAGE 主线在 topology-aware 场景族上具有整体稳定性，而不是只在个别图上偶然表现更好。

> **表 5-1 占位**  
> 表题：GraphSAGE 主线在五个 topology-aware 场景上的单次跨场景结果。  
> 建议来源：`cross_scenario_sage_full_matrix.json`  
> 表注：表中报告 `clean`、`sign_flip@0.4` 与 `update_noise@0.4` 三种条件下的 `test_f1`、`test_recall`、`test_fpr` 与 `kept_poisoned_clients`。建议按场景分组排版，并在备注列中标注 `scenario_h` 为主压力场景、`scenario_e` 为 held-out validation scenario。

> **图 5-1 占位**  
> 图题：GraphSAGE 主线在五个 topology-aware 场景上的跨场景 F1 热力图。  
> 插图建议：`cross_scenario_f1_heatmap.png`  
> 图注：颜色深浅表示 `test_f1`，用于直观展示主线方法在不同拓扑场景与不同攻击条件下的整体稳定性。

## 5.3 困难场景多种子稳定性与 Backbone 证据

单次矩阵只能说明“方法可运行”，不能说明“方法稳定”。因此，真正决定主结论可信度的，是 hardest settings 下的多种子结果。五种子统计显示，`scenario_f` 在三种条件下都非常稳定：`clean`、`sign_flip@0.4` 和 `update_noise@0.4` 的平均 `test_f1` 分别为 `0.9859`、`0.9840` 和 `0.9867`，标准差都很小。相较之下，`scenario_h` 的 `clean` 和 `sign_flip@0.4` 也同样稳定，平均 `test_f1` 分别为 `0.9785` 和 `0.9797`；真正显著抬高方差的只有 `scenario_h + update_noise@0.4`，其平均 `test_f1` 为 `0.9686`，标准差为 `0.0130`。因此，当前主线问题不是“整条方法普遍不稳”，而是“存在一个可以明确定位的边界失效条件”。

在此基础上，backbone 对照进一步说明，GraphSAGE 的收益不是简单来源于更多训练技巧，而是确实来自结构建模。`scenario_h` 上五种子 Welch 检验显示，`clean` 条件下 FeatureMLP 的平均 `test_f1` 为 `0.9417 \pm 0.0180`，GraphSAGE 为 `0.9785 \pm 0.0028`，`p = 0.0095`；`sign_flip@0.4` 条件下 FeatureMLP 为 `0.9512 \pm 0.0071`，GraphSAGE 为 `0.9797 \pm 0.0026`，`p = 3.70\times 10^{-4}`。从实际错误代价看，单次运行层面的 `test_fpr` 也一致支持 GraphSAGE：在 `scenario_h` 的 `clean` 条件下，FeatureMLP 的 `test_fpr` 为 `0.1931`，GraphSAGE 为 `0.0779`；在 `sign_flip@0.4` 条件下，分别为 `0.1433` 和 `0.0530`。这意味着，GraphSAGE 的优势不仅体现在 F1，也体现在误报控制上。

需要同时强调边界。`scenario_g` 不应被误写成 GraphSAGE 的反例。该场景下 clean 条件中 FeatureMLP 与 GraphSAGE 的平均 `test_f1` 分别为 `0.9975` 和 `1.0000`，`p = 0.3739`；`sign_flip@0.4` 条件下分别为 `1.0000` 和 `0.9988`，`p = 0.3739`。这更接近一个 ceiling scenario，而不是“GraphSAGE 在某些场景会稳定退化”的证据。换言之，最稳妥的 backbone 结论应写为：GraphSAGE 在更难、更加依赖结构信号的场景中显著更强，而在接近饱和的小场景中，两类 backbone 并不存在稳定显著差距。

> **表 5-2 占位**  
> 表题：`scenario_h` 与 `scenario_f` 在三种训练条件下的五种子稳定性结果。  
> 建议来源：`hard_case_sage_seed_summary.json`  
> 表注：表中报告 `test_f1`、`test_fpr` 的均值与标准差，用于说明真正显著抬高方差的设置主要集中在 `scenario_h + update_noise@0.4`。

> **表 5-3 占位**  
> 表题：GraphSAGE 与 FeatureMLP 在困难场景中的显著性比较及 `scenario_g` 边界结果。  
> 建议来源：`backbone_clean_f1_significance.json`、`backbone_sign_flip_frac0p4_f1_significance.json`、`scenario_g_backbone_seed_comparison.json`、`scenario_g_backbone_clean_f1_significance.json`、`scenario_g_backbone_sign_flip_frac0p4_f1_significance.json`  
> 表注：建议分为两个 panel。Panel A 报告 `scenario_h` 上 clean 与 sign-flip 的五种子 `F1` 均值、标准差与 `p` 值；Panel B 报告 `scenario_g` 上的 near-ceiling 边界结果，避免正文把 `scenario_g` 误写成反例。

> **图 5-2 占位**  
> 图题：GraphSAGE 与 FeatureMLP 在关键场景上的 backbone 比较。  
> 插图建议：`backbone_comparison.png`  
> 图注：建议保留 `scenario_h` 为主 panel；若版面允许，可在图注中简短说明 `scenario_g` 为 near-ceiling boundary case。

## 5.4 Tuning 与通信开销：主线是否依赖 Full Fine-Tuning

如果主线方法只有在 `full_ft` 下才成立，那么它在边缘联邦部署中的说服力会明显下降。因此，tuning study 的关键问题不是“哪一行数值最高”，而是“主线鲁棒性是否依赖最重的参数更新模式”。结果显示，答案是否定的。

在 `clean` 条件下，`head_only`、`adapter_ft` 和 `full_ft` 的单次 `test_f1` 分别为 `0.9692`、`0.9692` 和 `0.9641`，对应总通信量分别为 `13200`、`123600` 和 `635600` 字节。换言之，`adapter_ft` 只用 `19.45\%` 的 `full_ft` 通信量，就取得了不低于 `full_ft` 的结果；`head_only` 则只用 `2.08\%` 的通信量，也几乎不损失主线表现。

在 `sign_flip@0.4` 条件下，这一趋势更清晰。`adapter_ft` 的 `test_f1 = 0.9696`、`test_fpr = 0.0530`，而 `full_ft` 只有 `test_f1 = 0.9666`、`test_fpr = 0.0935`。在 `update_noise@0.4` 条件下，`full_ft` 的单次 `F1` 为 `0.9716`，与 `head_only` 的 `0.9718` 和 `adapter_ft` 的 `0.9705` 并没有拉开本质差距。基于这些结果，当前最稳妥的工程结论不是“full fine-tuning 更强”，而是“parameter-efficient tuning 已足以支撑主线结果，且更符合通信受限联邦部署的现实约束”。

需要进一步保持克制的是对 `full_ft` 退化原因的解释。当前结果支持一个合理推断：在 heterogeneity 与 poisoning 并存时，更大规模的全参数更新更容易放大局部漂移；同时，trust-aware filtering 会减少有效参与客户端数，使全模型更新在更少有效参与和更强异构的条件下更脆弱。但这一点目前仍属于结果驱动的机制推断，而不是已被独立机制实验完全证明的结论，因此正文不应把它写成确定性机理。

> **表 5-4 占位**  
> 表题：三种 tuning mode 在 `scenario_h` 上的性能与通信开销比较。  
> 建议来源：`real_graph_pilot_h_scenario_h_sage_tuning_modes.json`、`tuning_modes_sage_sign_flip_frac0p4_summary.json`、`tuning_modes_sage_update_noise_frac0p4_summary.json`  
> 表注：建议按 `clean`、`sign_flip@0.4`、`update_noise@0.4` 三个条件分块，列出 `test_f1`、`test_fpr`、`total_bytes_est` 与相对 `full_ft` 百分比。

> **图 5-3 占位**  
> 图题：GraphSAGE 不同 tuning mode 的性能-通信折中。  
> 插图建议：`comm_tradeoff.png`  
> 图注：横轴为估计通信成本，纵轴为主指标表现，突出 `adapter_ft` 与 `head_only` 在部署可行性上的优势。

## 5.5 Trust-Aware Filtering 的真实收益：不是普遍提分，而是减少被保留的恶意参与

这是全文最需要写得克制也最不能写虚的一节。当前证据并不支持“trust-aware universally improves F1”，但稳定支持“trust-aware filtering 是一种 conservative security control，其核心收益是减少 retained poisoned clients，并在多数场景把精度损失压到 near-neutral”。

首先看主压力场景 `scenario_h`。在五种子统计下，`clean` 条件中 trust-aware 与 keep-all 基本持平，平均 `test_f1` 分别为 `0.9785` 和 `0.9783`；`sign_flip@0.4` 条件下也几乎相同，分别为 `0.9797` 和 `0.9797`，但 trust-aware 将平均被保留的恶意客户端从 `4.0` 降到 `3.6`。真正体现 trade-off 的是 `update_noise@0.4`：trust-aware 将平均 `kept_poisoned_clients` 从 `4.0` 降到 `0.4`，但平均 `test_f1` 也从 `0.9732` 降到 `0.9686`，对应 `p = 0.5162`。这说明在 hardest setting 上，trust-aware 的主要价值在于“减毒”，而不是在均值上保证更高 `F1`。

真正最有说服力的结果来自 held-out `scenario_e`。在 `update_noise@0.4` 条件下，trust-aware 的平均 `test_f1` 为 `0.9879`，keep-all 为 `0.9890`，差异很小且不显著，`p = 0.6867`；但平均 `kept_poisoned_clients` 从 `4.0` 大幅降到 `0.2`。这组结果非常关键，因为它不在主叙事反复使用的 `scenario_h / scenario_f` 上，而是在 held-out 外部场景上复现了同样的收益模式：不是普遍提分，而是以 near-neutral 的精度代价显著减少 poisoned participation。

辅助公开验证 `NSL-KDD` 进一步强化了这种方法画像。clean 条件下，trust-aware 的平均 `test_f1 = 0.7595`，略低于 keep-all 的 `0.7666`，但 `test_fpr` 更低；`sign_flip@0.4` 和 `update_noise@0.4` 下，trust-aware 与 keep-all 的平均 `F1` 基本持平，但保留的恶意客户端从 `4.0` 分别降到 `2.33` 和 `0.33`。因此，public auxiliary 也支持“更保守、更少毒参与”的特征，而不是“平均精度普遍提高”的激进口径。

> **表 5-5 占位**  
> 表题：trust-aware filtering 与 keep-all 在 `scenario_h`、held-out `scenario_e` 和 public `NSL-KDD` 上的对比。  
> 建议来源：`scenario_h_trust_vs_keepall_seed_comparison.json`、`scenario_e_trust_vs_keepall_seed_comparison.json`、`public_nslkdd_trust_vs_keepall_seed_comparison.json`  
> 表注：建议按三个数据块排版，每个数据块再按 `clean`、`sign_flip@0.4`、`update_noise@0.4` 三行展开，列出 `test_f1_mean`、`test_fpr_mean`、`kept_poisoned_clients_mean` 与 `p` 值。该表应作为全文最核心结果表之一。

> **图 5-4 占位**  
> 图题：held-out `scenario_e` 上 trust-aware filtering 与 keep-all 的五种子比较。  
> 插图建议：正文优先使用 `scenario_e_trust_vs_keepall_seed_comparison.png`；若版面允许，可与 `scenario_h_trust_vs_keepall_seed_comparison.png` 和 `public_nslkdd_trust_vs_keepall_seed_comparison.png` 合并为三联图。  
> 图注：建议突出 `update_noise@0.4` 条件下“精度差异不显著，但 retained poisoned clients 大幅下降”的核心结论。

## 5.6 更硬对照：聚合器比较与公开基线比较

为了避免 reviewer 认为主线结果只是“挑了一个容易赢的对照”，还需要补两层更硬的比较。第一层是聚合器对照，第二层是 public benchmark 上的 classical robust baselines。

在 `scenario_h + sign_flip@0.4` 的五种子结果中，`hierarchical` 的平均 `test_f1 = 0.9797`，`mean` 为 `0.9794`，两者非常接近；但 `median` 和 `krum` 分别只有 `0.9759` 和 `0.9757`。从 `test_fpr` 看，`mean` 甚至略低于 `hierarchical`，分别为 `0.0181` 和 `0.0212`。因此，这一节不能被写成“hierarchical 在所有指标上绝对碾压”。最稳妥的写法应是：`hierarchical aggregation` 属于 top-tier choice，它的优势不仅在于整体表现位于第一梯队，还在于与本文的 grouped trust-filter design 结构一致；而 `median` 与 `krum` 在当前设定下整体更弱。

在 public `NSL-KDD + update_noise@0.4` 上，trust-aware 与更硬基线的比较同样值得保留。`trust_aware` 的平均 `test_f1 = 0.7882`，与 `hier_keepall` 的 `0.7882` 持平，但 `test_fpr` 从 `0.0741` 降到 `0.0629`，`kept_poisoned_clients` 从 `4.0` 降到 `0.33`。与 `mean`、`median` 和 `krum` 相比，trust-aware 在当前 public benchmark 上的平均 F1 也更高。因此，public harder baselines 支持的不是“trust-aware 在公开数据上也普遍提分”，而是“trust-aware 至少不是靠挑一个很弱的 keep-all 对照取胜，它在公开 benchmark 上仍保持了更保守、更少毒参与的特征”。

> **表 5-6 占位**  
> 表题：`scenario_h + sign_flip@0.4` 下不同聚合器的五种子结果比较。  
> 建议来源：`aggregation_sign_flip_frac0p4_sage_group_stats.json`  
> 表注：建议列出 `hierarchical`、`mean`、`median`、`krum` 的 `test_f1_mean`、`test_f1_std` 与 `test_fpr_mean`，用于支持“hierarchical 是 top-tier choice，而非全指标绝对碾压”的克制结论。

> **表 5-10 占位**  
> 表题：public `NSL-KDD + update_noise@0.4` 上 trust-aware 与更硬 classical baselines 的比较。  
> 建议来源：`public_nslkdd_update_noise_baseline_comparison.json`  
> 表注：建议列出 `trust_aware`、`hier_keepall`、`mean`、`median`、`krum` 的 `test_f1_mean`、`test_fpr_mean` 和 `kept_poisoned_clients_mean`。若正文版面不足，该表可移入补充材料，但建议在正文中保留对其结论的引用。

## 5.7 Group Floor 的默认值与 Principal Failure Mode

如果第五章只写平均结果而不解释失败条件，整篇论文的可信度会明显下降。因此，本节的任务不是继续展示“平均上更好”，而是解释为什么当前最坏情况会出现，以及它究竟来自 backbone、trust score 还是 group floor。

首先看 `min_keep_per_group` 敏感性。单次结果表明，`keep=1` 是当前最合理的静态默认值。clean 条件下，`keep=0` 的 `test_f1 / test_fpr` 为 `0.9666 / 0.0935`，`keep=1` 提升为 `0.9692 / 0.0779`，而 `keep=2` 与 `keep=1` 相同但保留更多客户端；`sign_flip@0.4` 条件下，`keep=1` 也优于 `keep=0` 和 `keep=2`；`update_noise@0.4` 下，`keep=2` 虽有轻微数值提升，但开始保留恶意客户端。这个结果说明 `min_keep_per_group = 1` 不是拍脑袋超参，而是当前最合理的 coverage-security 折中点。

然而，真正提升论文可信度的是 fixed-seed 机制诊断。在 `scenario_h + update_noise@0.4 + seed11` 上，`keep=0` 的结果为 `0.9805 / 0.0156`，但完全失去 benign 组覆盖；`keep=1` 反而跌到 `0.9496 / 0.1028`，并保留了 1 个中毒客户端；`keep=2` 又回到 `0.9779 / 0.0374`。表面上看这很反直觉，但机制分析给出了清晰解释：该种子下 `role:benign_user` 小组的两个客户端均被投毒。`keep=1` 时，静态 group floor 为了“保组”强行留下了 1 个本应被丢弃的低信任代表；其 final-round `trust_norm` 只有 `0.0106`，这说明问题不在于它“被误判为可信”，而在于 floor 机制无条件保组。换言之，当前主坏点并不是 GraphSAGE 崩了，而是 static group floor 在 fully poisoned small group 下存在 principal failure mode。

> **表 5-7 占位**  
> 表题：`min_keep_per_group` 在 `scenario_h` 上的敏感性分析。  
> 建议来源：`min_keep_per_group_sage_sensitivity.json`  
> 表注：建议按 `clean`、`sign_flip@0.4`、`update_noise@0.4` 三个条件分块，列出 `keep=0/1/2` 对应的 `test_f1`、`test_fpr`、`kept_clients` 与 `kept_poisoned_clients`。该表服务于“`keep=1` 是静态默认值的合理折中”这一结论。

> **表 5-8 占位**  
> 表题：`scenario_h + update_noise@0.4 + seed11` 的固定种子机制诊断。  
> 建议来源：`seed11_keep_sweep_h_sage_update_noise_frac0p4_mechanism.json`  
> 表注：建议列出 `keep=0/1/2` 下的 `test_f1`、`test_fpr`、`kept_poisoned_clients`、`benign_kept_clients`、`max_retained_poisoned_trust_norm` 和 `retained_poisoned_groups`，用于直接支持 principal failure mode 的诊断结论。

> **图 5-5 占位**  
> 图题：`seed11` 固定种子下 static group floor principal failure mode 的机制示意。  
> 插图建议：`seed11_keep_sweep_h_sage_update_noise_frac0p4_mechanism.png`  
> 图注：该图是本章机制解释的核心插图之一，建议正文保留，不建议下放到补充材料。

## 5.8 Conditional Trust-Mass Floor：Targeted Hardening 是否真的修复了主坏点

在明确 principal failure mode 之后，第五章必须继续回答一个更关键的问题：conditional trust-mass floor 是不是只是“换了一个地方退化”，还是它真的修复了主线中的边界失效。

在最关键的 `scenario_h + update_noise@0.4` 上，答案是明确偏正面的。`condfloor` 的五种子平均 `test_f1 = 0.9766`，高于 static 的 `0.9686`；平均 `test_fpr = 0.0231`，显著低于 static 的 `0.0449`；平均 `kept_poisoned_clients = 0.0`，而 static 仍为 `0.4`。更重要的是，方差也从 `0.0130` 降到了 `0.0050`。这表明 conditional floor 不是“只是改善平均值”，而是同时改善了最关键的稳定性问题。最典型的例子就是 `seed11`：static 为 `0.9496 / 0.1028`，而 condfloor 修复到 `0.9812 / 0.0125`。这足以支持一个强但仍克制的结论：conditional trust-mass floor 在 topology-aware mainline 上有效修复了 static floor 的 principal failure mode。

但本节必须同时呈现它的边界。held-out `scenario_e + update_noise@0.4` 上，condfloor 的平均 `test_f1 = 0.9891`，略高于 static 的 `0.9879`，与 keep-all 的 `0.9890` 基本持平；平均 `kept_poisoned_clients` 仍保持在 `0.2`。也就是说，在 held-out 场景中，condfloor 没有引入明显退化，整体表现为 near-neutral 到 slight positive。

真正决定其定性的，是 public auxiliary `NSL-KDD + update_noise@0.4`。在这里，condfloor 的平均 `test_f1 = 0.7611`，明显低于 static 与 keep-all 的约 `0.7882`；虽然其 `test_fpr` 更低、`kept_poisoned_clients = 0.0`，但这个代价不能被忽略。因此，正文必须避免把 condfloor 写成新的 universal default。当前最稳妥的口径只能是：它是针对 topology-aware mainline principal failure mode 的 targeted hardening，在主线与 held-out 场景中有效，但在 public auxiliary benchmark 上呈现 mixed behavior。

> **表 5-9 占位**  
> 表题：conditional trust-mass floor 在 `scenario_h`、held-out `scenario_e` 与 public `NSL-KDD` 上的比较。  
> 建议来源：`scenario_h_update_noise_condfloor_comparison.json`、`scenario_e_update_noise_condfloor_comparison.json`、`public_nslkdd_update_noise_condfloor_comparison.json`  
> 表注：建议按三个数据块排版，每个数据块包含 `condfloor`、`static`、`keepall` 三行，列出 `test_f1_mean`、`test_f1_std`、`test_fpr_mean`、`kept_poisoned_clients_mean` 与 `n`。该表应与表 5-8 一起形成“诊断-修复”闭环。

> **图 5-6 占位**  
> 图题：`scenario_h + update_noise@0.4` 上 conditional trust-mass floor 的 hardening 效果。  
> 插图建议：正文优先使用 `scenario_h_update_noise_condfloor_comparison.png`；`scenario_e_update_noise_condfloor_comparison.png` 和 `public_nslkdd_update_noise_condfloor_comparison.png` 建议放补充材料，或在版面允许时合并为三联图。  
> 图注：该图应突出 condfloor 对主坏点的修复，而不是把 condfloor 写成对所有数据点都统一更优的替代方案。

## 5.9 本章小结

综合本章全部证据，可以得到一组强弱分明、边界清楚的实验结论。

第一，GraphSAGE 主线在五个 topology-aware 场景上整体稳定成立，且困难场景 `scenario_h` 并未出现主线崩盘。第二，GraphSAGE 在结构更复杂的关键场景中显著优于 FeatureMLP；`scenario_g` 的 near-ceiling 结果并不构成反例。第三，trust-aware filtering 的主要价值不是普遍提高平均 F1，而是在多数设置下以 near-neutral 的精度代价减少被保留的恶意参与。第四，`min_keep_per_group = 1` 是当前静态 group floor 的合理折中点，但它存在明确的 principal failure mode。第五，conditional trust-mass floor 能在 topology-aware mainline 上有效修复这一坏点，但其公开 auxiliary benchmark 表现为 mixed，因此它应被定位为 targeted hardening，而不是新的 universal default。

如果第五章按上述方式组织，全文叙事就不会停留在“方法有效”这一层，而会提升到“方法有效、失败条件已识别、修复方向已验证、边界也被诚实呈现”。这正是当前版本最有机会说服中上档 cyber-security 期刊审稿人的地方。
