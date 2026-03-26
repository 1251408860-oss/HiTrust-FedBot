# HiTrust-FedBot 详细实验报告

版本日期：`2026-03-24`

本文档基于当前仓库中的结果表、主稿和复现实验产物，对 HiTrust-FedBot 的实验设计、结果表现、机制分析和当前实验质量进行一次系统整理。报告目标不是重复论文摘要，而是回答以下四个更直接的问题：

1. 当前主线方法到底稳不稳，在哪些场景稳。
2. trust-aware 机制到底带来了什么，是提精度还是降风险。
3. 目前最重要的失败点是什么，是否已经被解释清楚。
4. 现在这批实验距离投稿级证据还差什么，还剩哪些风险。

## 1. 实验目标与核心问题

当前实验围绕以下研究问题展开：

- 在拓扑异构、边缘拥塞、客户端投毒并存的联邦环境中，GraphSAGE 主线是否能稳定维持较高检测性能。
- 相比 FeatureMLP，GraphSAGE 是否在更难的结构场景中带来显著增益，而不是只在个别 run 偶然更好。
- trust-aware hierarchical aggregation 的核心价值究竟是什么。
  - 候选解释 A：普遍提升 F1。
  - 候选解释 B：以较小精度代价减少 poisoned participation，并控制 FPR。
- `min_keep_per_group = 1` 这个 group floor 是否合理，是否只是拍脑袋超参。
- 既有坏点是否来自 GraphSAGE 本身不稳定，还是来自 trust-floor 机制边界。
- 针对已识别坏点引入 `conditional trust-mass floor` 后，是否真的修复了主线问题，还是只是换一个地方退化。

## 2. 实验对象与设定

### 2.1 场景与数据

主实验基于五个 topology-aware pilot scenarios：

- `scenario_d_three_tier_low2`
- `scenario_e_three_tier_high2`
- `scenario_f_two_tier_high2`
- `scenario_g_mimic_congest`
- `scenario_h_mimic_heavy_overlap`

其中：

- `scenario_h` 是最重要的重叠与结构干扰压力场景。
- `scenario_f` 是较难的 two-tier 场景。
- `scenario_g` 规模较小，后续被证明更接近饱和场景。
- `scenario_e` 在本轮被用作 held-out validation。

外部补强使用了 auxiliary public benchmark：

- `NSL-KDD`

需要明确的是，`NSL-KDD` 是公开 intrusion benchmark，不是与主任务同分布的公开 bot benchmark。因此它能补强外部有效性，但不能替代主场景家族。

### 2.2 攻击设定

主攻击类型为：

- `sign_flip@0.4`：40% 恶意客户端执行符号翻转或方向性破坏。
- `update_noise@0.4`：40% 恶意客户端注入强扰动噪声更新。

### 2.3 评价指标

报告重点使用以下指标：

- `test_f1`
- `test_recall`
- `test_fpr`
- `kept_clients`
- `kept_poisoned_clients`
- `total_bytes_est`

### 2.4 主要实验线

当前实验由六条线组成：

- GraphSAGE 跨场景主线
- `scenario_h / scenario_f` 五种子稳定性
- GraphSAGE vs FeatureMLP backbone comparison
- tuning / communication comparison
- trust-aware vs keep-all 对照
- `min_keep_per_group` 敏感性 + `seed11` 机制诊断 + conditional floor hardening

## 3. 结果总览

先给结论，再展开细节。

- 结论 1：GraphSAGE 主线在五个 topology-aware scenarios 上整体稳定，最难的 `scenario_h` 也没有出现主线崩盘。
- 结论 2：GraphSAGE 在 `scenario_h` 上显著优于 FeatureMLP，这一点现在有五种子显著性支撑，不再只是单次 run。
- 结论 3：trust-aware filtering 的核心收益不是“普遍提升 F1”，而是减少 retained poisoned clients，并在多数设置下把精度代价压到 near-neutral。
- 结论 4：`min_keep_per_group = 1` 是合理默认值，但它存在明确边界坏点：小组完全被毒化时，静态 floor 可能强行保留低信任毒客户端。
- 结论 5：`conditional trust-mass floor` 在 topology-aware 主线，特别是 `scenario_h + update_noise@0.4` 上有效修复了这个坏点；但它在 public auxiliary `NSL-KDD` 上表现 mixed，因此不能升格为 universal default。

## 4. GraphSAGE 跨场景主线表现

单次 cross-scenario matrix 显示，GraphSAGE hierarchical mainline 在五个场景上都保持高水平。

| Scenario | Clean F1 | Sign-flip F1 | Update-noise F1 | 备注 |
| --- | ---: | ---: | ---: | --- |
| `scenario_d` | 0.9966 | 0.9966 | 0.9966 | 最稳定、接近满分 |
| `scenario_e` | 0.9826 | 0.9835 | 0.9835 | held-out 也较稳 |
| `scenario_f` | 0.9743 | 0.9720 | 0.9767 | 难场景但稳定 |
| `scenario_g` | 0.9756 | 0.9756 | 0.9938 | 后续证实偏饱和 |
| `scenario_h` | 0.9692 | 0.9696 | 0.9705 | 主压力场景 |

第一层判断很明确：修复后的语义下，GraphSAGE 主线没有出现“某类攻击一来就失守”的现象。更重要的是，`scenario_h` 虽然是全表最低一组，但仍维持在 `0.969x ~ 0.970x` 的单次 F1 水平，没有呈现系统性失稳。

## 5. 硬场景五种子稳定性

相比单次 run，更重要的是 hardest settings 的 seed-level 稳定性。

| Scenario | Condition | Mean F1 | Std | Mean FPR |
| --- | --- | ---: | ---: | ---: |
| `scenario_h` | clean | 0.9785 | 0.0028 | 0.0243 |
| `scenario_h` | sign-flip@0.4 | 0.9797 | 0.0026 | 0.0212 |
| `scenario_h` | update-noise@0.4 | 0.9686 | 0.0130 | 0.0449 |
| `scenario_f` | clean | 0.9859 | 0.0021 | 0.0142 |
| `scenario_f` | sign-flip@0.4 | 0.9840 | 0.0039 | 0.0160 |
| `scenario_f` | update-noise@0.4 | 0.9867 | 0.0019 | 0.0136 |

这里可以看到两个非常重要的事实。

第一，`scenario_f` 的三种条件都非常稳，说明 GraphSAGE 主线并不是只在单一困难图上有效。

第二，真正显著抬高方差的只有 `scenario_h + update_noise@0.4`，也就是说，当前主线问题并不是“整个方法普遍不稳”，而是集中在一个可定位的边界条件上。这个观察直接引出了后续的机制分析。

## 6. Backbone 对比：GraphSAGE 是否真的更强

### 6.1 在 `scenario_h` 上，答案是明确的“是”

`scenario_h` clean 五种子 F1 显著性：

- FeatureMLP：`0.9417 +/- 0.0180`
- GraphSAGE：`0.9785 +/- 0.0028`
- `p = 0.0095`

`scenario_h` sign-flip 五种子 F1 显著性：

- FeatureMLP：`0.9512 +/- 0.0071`
- GraphSAGE：`0.9797 +/- 0.0026`
- `p = 3.70e-4`

单次 run 层面的 FPR 也支持同一结论：

- clean：FeatureMLP `0.1931`，GraphSAGE `0.0779`
- sign-flip：FeatureMLP `0.1433`，GraphSAGE `0.0530`

因此，在最关键的结构重叠压力场景上，GraphSAGE 的优势既体现在 F1，也体现在 FPR，且已经有统计显著性支撑。

### 6.2 `scenario_g` 不是反例，而是饱和场景

更新后的 `scenario_g` 五种子结果：

- clean：
  - FeatureMLP `0.9975`
  - GraphSAGE `1.0000`
  - `p = 0.3739`
- sign-flip：
  - FeatureMLP `1.0000`
  - GraphSAGE `0.9988`
  - `p = 0.3739`

这说明 `scenario_g` 并不能被解释为“GraphSAGE 有系统弱点”；更准确的解释是：

- 该场景过于容易，两个 backbone 都接近 ceiling。
- 在 ceiling 区间里，细小数值波动不应被过度解读。

因此，现在最稳的 backbone 结论应写成：

- GraphSAGE 在更难、更依赖结构信号的场景中明显更强。
- 在小型饱和场景中，并不存在稳定显著差距。

## 7. Tuning 与通信开销

### 7.1 Clean 条件

| Mode | F1 | FPR | Total Bytes |
| --- | ---: | ---: | ---: |
| `head_only` | 0.9692 | 0.0748 | 13,200 |
| `adapter_ft` | 0.9692 | 0.0779 | 123,600 |
| `full_ft` | 0.9641 | 0.0717 | 635,600 |

### 7.2 `sign_flip@0.4`

| Mode | F1 | FPR | Total Bytes | 相对 full_ft |
| --- | ---: | ---: | ---: | ---: |
| `head_only` | 0.9692 | 0.0748 | 13,200 | 2.08% |
| `adapter_ft` | 0.9696 | 0.0530 | 123,600 | 19.45% |
| `full_ft` | 0.9666 | 0.0935 | 635,600 | 100% |

### 7.3 `update_noise@0.4`

| Mode | F1 | FPR | Total Bytes | 相对 full_ft |
| --- | ---: | ---: | ---: | ---: |
| `head_only` | 0.9718 | 0.0592 | 13,200 | 2.08% |
| `adapter_ft` | 0.9705 | 0.0685 | 123,600 | 19.45% |
| `full_ft` | 0.9716 | 0.0467 | 635,600 | 100% |

### 7.4 解释

这里的结论比“full_ft 最强”更有价值：

- 在 clean 和 `sign_flip@0.4` 下，`full_ft` 不是最优。
- 在 `update_noise@0.4` 下，`full_ft` 的 F1 也没有显著拉开，`head_only` 甚至略高。
- 从通信成本看，`adapter_ft` 比 `full_ft` 少 `80.55%` 字节，`head_only` 少 `97.92%` 字节。

因此，当前最稳妥的工程结论是：

- HiTrust-FedBot 不依赖 full fine-tuning 才成立。
- parameter-efficient tuning 已经足以支撑主线结论。

关于“为什么 full_ft 在新语义下退化明显”，目前最合理的解释是一个基于结果的推断，而不是直接观测结论：

- `full_ft` 参数更多，在异构图分区和投毒同时存在时，更容易把客户端局部漂移直接放大到全模型更新。
- trust-aware filtering 会减少有效参与客户端数，full model 更新在这种“样本更少、异构更强”的条件下更容易出现不稳定。
- 现有结果支持“full_ft 没必要作为默认主线”，但还不能单独证明完整机理。

换句话说，这一节的严谨写法应是：

- `full_ft` 在当前实验下没有展现出足以覆盖其通信代价的稳定收益。
- 其退化原因可以合理推断为更高维参数更新在 heterogeneity + poisoning 下更脆弱，但该机制仍属于后续可补的分析题。

## 8. Trust-aware vs Keep-all：安全收益到底是什么

这一部分是整套实验的叙事核心。结论已经比较稳定：

- trust-aware filtering 不是 universal F1 booster。
- 它更像 conservative security control。
- 核心收益是减少 poisoned participation，同时尽量把精度和 FPR 代价压小。

### 8.1 `scenario_h`

| Condition | Trust-aware F1 | Keep-all F1 | Trust-aware FPR | Keep-all FPR | Trust-aware kept poisoned | Keep-all kept poisoned |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | 0.9785 | 0.9783 | 0.0243 | 0.0243 | 0.0 | 0.0 |
| sign-flip@0.4 | 0.9797 | 0.9797 | 0.0212 | 0.0224 | 3.6 | 4.0 |
| update-noise@0.4 | 0.9686 | 0.9732 | 0.0449 | 0.0343 | 0.4 | 4.0 |

解释如下：

- clean 与 sign-flip 下，trust-aware 和 keep-all 几乎打平。
- `update_noise@0.4` 下，trust-aware 明显减少 retained poisoned clients，从 `4.0` 降到 `0.4`。
- 但在 `scenario_h` 这组 hardest setting 上，静态 floor 版本确实付出了精度和 FPR 代价。

这说明 trust-aware 在主压力场景上的价值主要体现为“减毒”，而不是“平均 F1 一定更高”。

### 8.2 Held-out `scenario_e`

| Condition | Trust-aware F1 | Keep-all F1 | Trust-aware FPR | Keep-all FPR | Trust-aware kept poisoned | Keep-all kept poisoned |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | 0.9881 | 0.9881 | 0.0123 | 0.0117 | 0.0 | 0.0 |
| sign-flip@0.4 | 0.9896 | 0.9895 | 0.0216 | 0.0204 | 3.8 | 4.0 |
| update-noise@0.4 | 0.9879 | 0.9890 | 0.0123 | 0.0130 | 0.2 | 4.0 |

`scenario_e` 非常关键，因为它不是主叙事里反复使用的 `scenario_h / f`，因此更能说明结论能否外推到“同类但未作为主舞台”的结构图。

这里最重要的一组是 `update_noise@0.4`：

- F1 只从 `0.9890` 变成 `0.9879`
- 且 `p = 0.6867`，不显著
- retained poisoned clients 从 `4.0` 大幅降到 `0.2`

这就是当前论文最稳的 trust-aware 价值表达：

- 不是“普遍提升 F1”
- 而是“以 near-neutral 的精度代价显著减少 poisoned participation”

### 8.3 Auxiliary public `NSL-KDD`

| Condition | Trust-aware F1 | Keep-all F1 | Trust-aware FPR | Keep-all FPR | Trust-aware kept poisoned | Keep-all kept poisoned |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | 0.7595 | 0.7666 | 0.0547 | 0.0671 | 0.0 | 0.0 |
| sign-flip@0.4 | 0.7587 | 0.7583 | 0.0573 | 0.0573 | 2.33 | 4.0 |
| update-noise@0.4 | 0.7882 | 0.7882 | 0.0629 | 0.0741 | 0.33 | 4.0 |

public auxiliary 的信息量也很大：

- clean 下 trust-aware 并没有提升 F1，反而略低。
- 但 FPR 更低。
- `sign_flip@0.4` 和 `update_noise@0.4` 下，F1 基本持平，而 retained poisoned clients 明显下降。

所以 public benchmark 进一步支持的不是“trust-aware 提升平均精度”，而是：

- trust-aware 在公开数据上也保留了“更保守、更少毒参与”的性格。

## 9. 聚合器对比

`scenario_h + sign_flip@0.4` 的 aggregation 汇总如下：

| Aggregation | Mean F1 | Std | Mean FPR |
| --- | ---: | ---: | ---: |
| `hierarchical` | 0.9797 | 0.0026 | 0.0212 |
| `mean` | 0.9794 | 0.0031 | 0.0181 |
| `median` | 0.9759 | 0.0046 | 0.0361 |
| `krum` | 0.9757 | 0.0048 | 0.0374 |

这一节的正确解释也需要克制：

- hierarchical 不是所有指标上都绝对碾压。
- `mean` 在这组实验里 F1 非常接近，FPR 甚至略低。
- 但 `hierarchical` 处于第一梯队，并且与 group-aware trust filtering 的方法设计天然一致。
- `median` 和 `krum` 在当前设定下整体更弱。

因此最稳的写法是：

- hierarchical aggregation 是 top-tier choice。
- 它的价值不只是最终均值，还包括与 grouped trust-filter design 的结构一致性。

## 10. `min_keep_per_group` 敏感性分析

单次敏感性结果如下。

| Condition | keep=0 | keep=1 | keep=2 | 最优解释 |
| --- | --- | --- | --- | --- |
| clean | F1 0.9666 / FPR 0.0935 | F1 0.9692 / FPR 0.0779 | F1 0.9692 / FPR 0.0779 | `keep=1` 修复 coverage，`keep=2` 无额外收益 |
| sign-flip@0.4 | F1 0.9692 / FPR 0.0748 | F1 0.9696 / FPR 0.0530 | F1 0.9685 / FPR 0.0810 | `keep=1` 最优 |
| update-noise@0.4 | F1 0.9705 / FPR 0.0685 | F1 0.9705 / FPR 0.0685 | F1 0.9712 / FPR 0.0654 | `keep=2` 开始保留毒客户端 |

从这一节可以得到两个层次的结论。

第一层，`min_keep_per_group = 1` 不是拍脑袋。

- clean 和 sign-flip 下它都是最合理的平均折中点。
- 它能避免语义组被整体删除。

第二层，它也不是没有代价。

- `keep=2` 在个别条件下数值略好，但开始保留 poisoned clients。
- 这意味着更高 floor 会用“语义覆盖”换“攻击面变大”。

因此，当前把 `keep=1` 作为 static mainline default 是合理的。

## 11. 机制诊断：为什么 `scenario_h + update_noise@0.4` 方差最高

真正提升论文可信度的，不是把坏点藏起来，而是把它解释清楚。`seed11` 机制分析正好完成了这件事。

| Setting | F1 | FPR | Kept Poisoned | Benign Group Retained |
| --- | ---: | ---: | ---: | ---: |
| `keep=0` | 0.9805 | 0.0156 | 0 | 0 / 2 |
| `keep=1` | 0.9496 | 0.1028 | 1 | 1 / 2 |
| `keep=2` | 0.9779 | 0.0374 | 2 | 2 / 2 |

这组现象如果只看表面会很奇怪：为什么 `keep=2` 比 `keep=1` 反而好？

机制解释是：

- `seed11` 中，`role:benign_user` 这个小组的两个客户端都被投毒。
- `keep=0` 时，整个 benign 组被丢弃，所以虽然不符合语义覆盖目标，但没有 retained poisoned client。
- `keep=1` 时，静态 group floor 强行保留 1 个 benign 组代表，而这个代表其实是毒客户端。
- 被强行保留的毒客户端 final-round `trust_norm` 只有 `0.0106`，说明问题不在于它“看起来可信”，而在于 floor 机制“无条件保组”。
- `keep=2` 时，两个毒客户端先在组内被平均，再进入全局层级聚合，反而比“单个毒客户端独占该组代表权”更不坏。

因此，当前最关键的机制结论是：

- 主坏点不是 GraphSAGE 崩了。
- 主坏点是 static group floor 在“小组被完全毒化”时会强行保留近零信任的组代表。

这个结论对论文质量极其重要，因为它把问题从“模型不稳”变成了“机制边界已识别且可修”。

## 12. Conditional Trust-Mass Floor Hardening

针对上面的机制坏点，当前已经实现并验证了 `conditional trust-mass floor`：

- 仅当某组总 `trust mass >= 0.10` 时，才执行 floor repair。
- 若某组 trust mass 已接近坍塌，则允许 abstain，而不是无条件保一个代表。

### 12.1 在 `scenario_h + update_noise@0.4` 上的效果

| Variant | Mean F1 | Std | Mean FPR | Kept Poisoned |
| --- | ---: | ---: | ---: | ---: |
| `condfloor` | 0.9766 | 0.0050 | 0.0231 | 0.0 |
| `static` | 0.9686 | 0.0130 | 0.0449 | 0.4 |
| `keepall` | 0.9732 | 0.0072 | 0.0343 | 4.0 |

这组结果非常强，说明 hardening 不是“讲故事”，而是真修好了主坏点：

- F1 从 `0.9686` 提到 `0.9766`
- FPR 从 `0.0449` 降到 `0.0231`
- retained poisoned clients 从 `0.4` 变成 `0.0`
- 方差从 `0.0130` 降到 `0.0050`

更关键的是最坏 seed 被明确修复：

- `seed11`：static `0.9496 / 0.1028`
- `seed11`：condfloor `0.9812 / 0.0125`

### 12.2 在 held-out `scenario_e + update_noise@0.4`

| Variant | Mean F1 | Mean FPR | Kept Poisoned |
| --- | ---: | ---: | ---: |
| `condfloor` | 0.9891 | 0.0136 | 0.2 |
| `static` | 0.9879 | 0.0123 | 0.2 |
| `keepall` | 0.9890 | 0.0130 | 4.0 |

这里的结论是 near-neutral / slight positive：

- condfloor 没有引入 held-out 明显退化。
- 相比 static 略有正向。
- 相比 keep-all 保持了低毒参与。

### 12.3 在 public auxiliary `NSL-KDD + update_noise@0.4`

| Variant | Mean F1 | Mean FPR | Kept Poisoned |
| --- | ---: | ---: | ---: |
| `condfloor` | 0.7611 | 0.0569 | 0.0 |
| `static` | 0.7882 | 0.0629 | 0.33 |
| `keepall` | 0.7882 | 0.0741 | 4.0 |

这组结果说明为什么 condfloor 不能直接升格为新主线默认值：

- 它更保守。
- 安全性指标更强。
- 但 F1 下降明显。

因此，当前对 condfloor 的最稳定位应当是：

- 它是 targeted hardening / extension。
- 它在 topology-aware mainline 上很有效。
- 它在 held-out `scenario_e` 上 near-neutral。
- 它在 auxiliary public benchmark 上 mixed，因此不能写成 universal replacement。

## 13. Public Baseline 对比

`NSL-KDD + update_noise@0.4` 的 harder baselines 对比如下。

| Method | Mean F1 | Mean FPR | Kept Poisoned |
| --- | ---: | ---: | ---: |
| `trust_aware` | 0.7882 | 0.0629 | 0.33 |
| `hier_keepall` | 0.7882 | 0.0741 | 4.0 |
| `mean` | 0.7571 | 0.0547 | 4.0 |
| `median` | 0.7706 | 0.0673 | 4.0 |
| `krum` | 0.7684 | 0.0660 | 4.0 |

这组对比支撑两个判断：

- trust-aware 至少不是靠“挑一个很弱的 keep-all 对照”取胜。
- 在 public benchmark 上，它和 hierarchical keep-all F1 持平，但显著减少 poisoned participation。
- 与 `mean / median / krum` 相比，它的 F1 更高，同时保留毒客户端显著更少。

## 14. 综合结论

把所有实验线合起来，当前最稳、最不容易被 reviewer 攻击的主结论如下。

### 14.1 能成立的结论

- HiTrust-FedBot 的主线贡献是 trust-aware grouped defense，而不是单纯“换成 GraphSAGE”。
- GraphSAGE 是当前测试中最强的 instantiation，尤其在 `scenario_h` 这类结构敏感场景上有显著优势。
- trust-aware filtering 的核心收益是 reducing poisoned participation，而不是普遍提高平均 F1。
- `min_keep_per_group = 1` 是有实验支持的默认折中点。
- 当前主要坏点已被明确定位为 static floor 在 fully poisoned small group 下的边界失效。
- `conditional trust-mass floor` 可以有效修复 topology-aware mainline 上的 principal failure mode。

### 14.2 不能过度写的结论

- 不能写成 “trust-aware universally improves F1”。
- 不能写成 “condfloor 可以直接替换 static mainline”。
- 不能把 `NSL-KDD` 写成与主任务同分布的公开 bot benchmark。
- 不能把 `scenario_g` 写成 GraphSAGE 的稳定反例。

## 15. 当前实验质量评估

### 15.1 强项

- 有跨场景主线，不是只跑单一数据点。
- 有五种子验证，关键结果不再依赖单次 run。
- 有 backbone 显著性统计，不只是肉眼看差距。
- 有 held-out `scenario_e`，增强了“不是只在主场景成立”的可信度。
- 有 auxiliary public `NSL-KDD`，提升了外部有效性。
- 有 classical robust baselines，对比面比早期版本更硬。
- 有机制诊断实验，能够解释最差 seed 的失败原因。
- 有 hardening 验证，说明问题已被修复而不是只被指出。
- 有 artifact/reproduce 脚本，复现性已经具备投稿价值。

### 15.2 仍然存在的不足

- `NSL-KDD` 不是同分布 public bot benchmark，外部有效性仍未完全封口。
- public auxiliary 实验目前只有 3 seeds，统计力度弱于主线 5 seeds。
- classical baselines 已补，但仍未覆盖更现代的 dynamic abstention / personalized robust FL defenses。
- full_ft 退化机理目前主要是结果推断，还不是独立机制实验。
- condfloor 在 public auxiliary 上 mixed，因此方法叙事必须继续克制。

### 15.3 总体判断

如果把目标定义为“支撑一篇中上档 cyber-security 期刊投稿的实验主体”，当前实验质量已经明显高于最初版本，原因在于：

- 主结论更聚焦
- 反例和坏点被解释了
- 外部补强和更硬基线已经补上
- 文稿口径已经从“泛化提升 F1”收缩为“更保守的安全控制”

当前最需要避免的不是“实验不够多”，而是“写法重新变激进”。只要叙事继续保持克制，这套实验的说服力是成立的。

## 16. 后续建议

如果还要继续增强这份报告对应的投稿把握，优先级建议如下：

1. 再补一个更接近主任务分布的公开或半公开 external validation 点。
2. 如果时间允许，补一个更现代的强 baseline，而不是继续堆经典聚合器。
3. 在附录或补充材料中保留 `seed11` 机制图和 condfloor 对照，主文中则只保留最关键一张图和一张表。
4. 若继续追问 full_ft 退化原因，可以单独补一个“参数规模 vs retained-clients vs update variance”的机制分析。

## 17. 结果来源文件

本报告主要基于以下结果文件整理：

- `paper_hitrust/tables/cross_scenario_sage_full_matrix.json`
- `paper_hitrust/tables/hard_case_sage_seed_summary.json`
- `paper_hitrust/tables/backbone_clean_f1_significance.json`
- `paper_hitrust/tables/backbone_sign_flip_frac0p4_f1_significance.json`
- `paper_hitrust/tables/scenario_g_backbone_seed_comparison.json`
- `paper_hitrust/tables/scenario_g_backbone_clean_f1_significance.json`
- `paper_hitrust/tables/scenario_g_backbone_sign_flip_frac0p4_f1_significance.json`
- `paper_hitrust/tables/real_graph_pilot_h_scenario_h_sage_tuning_modes.json`
- `paper_hitrust/tables/tuning_modes_sage_sign_flip_frac0p4_summary.json`
- `paper_hitrust/tables/tuning_modes_sage_update_noise_frac0p4_summary.json`
- `paper_hitrust/tables/scenario_h_trust_vs_keepall_seed_comparison.json`
- `paper_hitrust/tables/scenario_e_trust_vs_keepall_seed_comparison.json`
- `paper_hitrust/tables/public_nslkdd_trust_vs_keepall_seed_comparison.json`
- `paper_hitrust/tables/aggregation_sign_flip_frac0p4_sage_group_stats.json`
- `paper_hitrust/tables/min_keep_per_group_sage_sensitivity.json`
- `paper_hitrust/tables/seed11_keep_sweep_h_sage_update_noise_frac0p4_mechanism.json`
- `paper_hitrust/tables/scenario_h_update_noise_condfloor_comparison.json`
- `paper_hitrust/tables/scenario_e_update_noise_condfloor_comparison.json`
- `paper_hitrust/tables/public_nslkdd_update_noise_condfloor_comparison.json`
- `paper_hitrust/tables/public_nslkdd_update_noise_baseline_comparison.json`

## 18. 一句话总评

这批实验现在最强的价值，不是证明“trust-aware 一定更准”，而是证明：

在异构、受攻击的联邦图检测中，trust-aware hierarchical filtering 可以作为一种保守但有效的安全控制，在多数场景下以较小精度代价显著减少 poisoned participation；其主要边界失效已被明确诊断，并在 topology-aware 主线中被一个简单、可解释的条件 floor 机制有效修复。
