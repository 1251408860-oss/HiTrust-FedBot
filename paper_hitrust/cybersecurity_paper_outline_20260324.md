# 面向 Cybersecurity 期刊的高质量论文目录建议

适用稿件：`HiTrust-FedBot`

定位原则：

- 目录应突出“安全机制贡献”，而不是只突出“GraphSAGE backbone 更强”。
- 主线叙事应围绕 `trust-aware hierarchical defense`、`group-coverage constraint`、`mechanism-grounded robustness analysis` 展开。
- 目录结构要服务于当前最稳结论：
  - trust-aware filtering 是 conservative security control
  - 核心收益是 reducing poisoned participation
  - 精度总体 near-neutral, not universally improved
  - `conditional trust-mass floor` 是 targeted hardening，不是 universal replacement

## 推荐题目

`HiTrust-FedBot: Trust-Aware Hierarchical Federated Web Bot Detection with Group-Coverage-Constrained Filtering`

## 推荐论文目录

### Abstract

摘要建议覆盖以下五点：

- 问题背景：federated bot detection 在 edge-constrained、topology-heterogeneous、poisoning-prone 环境中的困难
- 方法核心：trust-aware hierarchical aggregation + group-coverage-constrained filtering
- 主实验结果：`scenario_h / scenario_f` 五种子结果
- 外部补强：held-out `scenario_e` + auxiliary public `NSL-KDD`
- 机制贡献：static floor 坏点诊断 + `conditional trust-mass floor` hardening

### Keywords

建议关键词：

- federated learning
- bot detection
- adversarial robustness
- trust-aware aggregation
- graph neural networks
- edge security

## 1. Introduction

### 1.1 Background and motivation

- 交代 federated bot detection 在边缘环境中的现实需求
- 强调三类约束同时存在：
  - topology heterogeneity
  - communication constraints
  - adversarial client updates

### 1.2 Problem gap

- 指出现有 robust FL 工作多关注“去掉坏客户端”
- 但在语义分组联邦环境中，纯过滤可能直接删掉整个 group
- 引出本文核心张力：
  - poisoning resistance
  - semantic group coverage preservation

### 1.3 Proposed idea

- 简明介绍 HiTrust-FedBot
- 说明不是单纯换 backbone，而是提出：
  - trust-aware scoring
  - grouped hierarchical aggregation
  - group-coverage-constrained filtering

### 1.4 Main findings

- GraphSAGE 在 harder topology-aware scenarios 上显著更强
- trust-aware filtering 的主要收益是减少 poisoned participation
- `min_keep_per_group = 1` 是合理默认折中
- residual failure mode 来自 static floor 的边界坏点
- conditional floor 可以修复主线坏点，但不应被写成 universal default

### 1.5 Contributions

建议用 3 到 4 条，避免太散：

- 提出面向 topology-aware federated bot detection 的 trust-aware hierarchical defense
- 引入 group-coverage-constrained filtering，并把它作为安全机制而非普通超参来分析
- 通过跨场景、五种子、held-out、public auxiliary 和机制实验系统验证方法
- 提出并验证 `conditional trust-mass floor` 作为 targeted hardening

## 2. Related Work

### 2.1 Federated cyber-security detection

- FL for intrusion detection
- FL for distributed cyber monitoring
- 强调你与通用 FL-IDS 工作的区别：图结构、bot detection、topology-aware grouping

### 2.2 Robust federated learning under poisoning

- Byzantine-robust aggregation
- trust-based filtering
- client selection / anomaly-aware filtering
- 点明缺口：多数方法缺少“semantic group coverage”视角

### 2.3 Graph learning for security analytics

- GNNs in intrusion / fraud / bot / anomaly detection
- 引出 GraphSAGE 的合理性，但不要把 Related Work 写成“给 GraphSAGE 背书”

### 2.4 Communication-efficient federated adaptation

- parameter-efficient tuning
- edge-constrained deployment relevance

### 2.5 Position of this work

- 用一个短小总结段收口：
  - 本文位于 federated cyber-security、robust FL、graph security learning、communication-efficient adaptation 的交叉点
  - 主要新意是显式将 group coverage 纳入 trust-filter design

## 3. Method

### 3.1 System setting and notation

- 联邦客户端、服务端、图分区、语义组、每轮训练流程

### 3.2 Threat model

- `sign_flip@0.4`
- `update_noise@0.4`
- 攻击者能力与限制

### 3.3 Trust-aware hierarchical aggregation

- client trust score 计算来源
- group-wise aggregation
- inter-group aggregation

### 3.4 Group-coverage-constrained trust filtering

- 定义 `min_keep_per_group`
- 解释为什么这是必要的安全机制
- 清楚写出它的 trade-off：
  - 覆盖保护
  - 潜在毒客户端泄漏

### 3.5 Conditional trust-mass floor hardening

- 定义 `group_floor_policy`
- 定义 `group_floor_min_trust_mass`
- 说明该模块是后续针对 principal failure mode 的 targeted extension

### 3.6 Backbone and tuning modes

- FeatureMLP
- GraphSAGE
- `head_only`
- `adapter_ft`
- `full_ft`

## 4. Experimental Setup

### 4.1 Datasets and scenario family

- 五个 topology-aware pilot scenarios
- public auxiliary `NSL-KDD`
- 明确说明 `NSL-KDD` 只是 auxiliary external validation

### 4.2 Attack settings

- sign-flip
- update-noise
- malicious fraction = `0.4`

### 4.3 Baselines and comparison groups

- FeatureMLP vs GraphSAGE
- trust-aware vs keep-all
- hierarchical vs `mean/median/krum`
- static floor vs conditional floor

### 4.4 Metrics

- F1
- recall
- FPR
- kept poisoned clients
- communication bytes

### 4.5 Reproducibility protocol

- 5 seeds for critical topology-aware settings
- 3 seeds for public auxiliary benchmark
- artifact / scripts / tables / figures

## 5. Results

这一章建议是全文最核心章节，结构上要从“主线成立”到“机制解释”逐层推进。

### 5.1 Overall robustness across topology-aware scenarios

- 先给 cross-scenario matrix
- 说明主线在五个场景上总体稳定
- 明确 `scenario_h` 是 hardest stress case

### 5.2 Five-seed robustness on the hard scenarios

- 重点报告 `scenario_h` 和 `scenario_f`
- 突出只有 `scenario_h + update_noise@0.4` 方差较高
- 为后续机制分析埋伏笔

### 5.3 Backbone comparison

- 重点讲 `scenario_h`
- clean 和 sign-flip 显著性
- `scenario_g` 作为 saturation case 处理，不写成反例

### 5.4 Communication-efficient tuning

- `head_only / adapter_ft / full_ft`
- 重点强调：
  - mainline 不依赖 full fine-tuning
  - parameter-efficient tuning 已足够支撑主结论

### 5.5 Trust-aware versus keep-all validation

- 建议分成两个小段写

#### 5.5.1 Held-out scenario validation on `scenario_e`

- 核心句式：
  - near-neutral F1
  - sharply reduced poisoned participation

#### 5.5.2 Auxiliary public validation on `NSL-KDD`

- 核心句式：
  - public support is supportive but qualified
  - useful for external strengthening, not same-distribution substitution

### 5.6 Aggregation comparison

- hierarchical vs `mean / median / krum`
- 口径要克制：
  - hierarchical is a top-tier and method-consistent choice
  - not universally dominant on every metric

### 5.7 Sensitivity of `min_keep_per_group`

- 单独证明 `keep=1` 的合理性
- 把它从“经验超参”升级为“有安全含义的设计参数”

### 5.8 Mechanism analysis of the residual worst case

- 用 `seed11` 解释：
  - 问题不是 GraphSAGE collapse
  - 问题是 static floor 在 fully poisoned small group 下强行保代表

### 5.9 Conditional trust-mass floor hardening

- 先写 `scenario_h` 修复效果
- 再写 held-out `scenario_e` near-neutral
- 最后写 public `NSL-KDD` mixed
- 用这一节收束成：
  - targeted hardening
  - not universal replacement

## 6. Discussion

### 6.1 What the results actually support

- trust-aware filtering 应被理解为 conservative security control
- 核心收益是 reducing poisoned participation
- GraphSAGE 是 harder topology-aware settings 上更强的 instantiation

### 6.2 Why the mechanism analysis matters

- 说明为什么解释坏点比回避坏点更能增强论文可信度

### 6.3 Deployment relevance

- communication efficiency
- edge suitability
- interpretability of trust-floor design

### 6.4 External validity and claim discipline

- `NSL-KDD` 的定位
- 为什么不能夸大为 universal F1 gain

## 7. Limitations

建议单列，不要并进 Discussion 里糊过去。

### 7.1 Dataset and deployment limitations

- 不是 live deployment
- public benchmark 不同分布

### 7.2 Method limitations

- condfloor 不是 universal default
- stronger modern baselines 仍可继续扩充

### 7.3 Statistical limitations

- public auxiliary 只有 3 seeds
- 部分分析仍属 targeted validation

## 8. Conclusion

结论建议只做三件事：

- 重述方法贡献
- 重述最稳实验结论
- 重述 principal failure mode 已被解释且可被 targeted hardening 修复

不要在结论里重新扩写所有实验。

## Declarations

建议按期刊常见要求保留：

- Availability of data and materials
- Code availability
- Competing interests
- Funding
- Authors' contributions
- Acknowledgments

## References

- 正式参考文献表

## 推荐附录目录

如果主文篇幅受限，建议把以下内容移入附录或 supplementary material。

### Appendix A. Additional implementation details

- trust score details
- group assignment details
- hyperparameters

### Appendix B. Additional seed-level tables

- 各主场景 seed stats
- `scenario_g` 补充表

### Appendix C. Additional public benchmark results

- `NSL-KDD` seed-level full stats
- baseline raw tables

### Appendix D. Mechanism diagnostics

- `seed11` trust diagnostics
- retained poisoned group details

### Appendix E. Conditional floor ablation

- `0.10` vs `0.05`
- scenario-wise condfloor comparisons

## 推荐主文图表布局

为更符合 `Cybersecurity` 的阅读习惯，主文图表建议控制在“支撑主结论”而不是“把所有实验都堆进正文”。

### 主文建议保留

- Figure 1. Method overview / system pipeline
- Table 1. Scenario family and threat settings
- Table 2. Cross-scenario GraphSAGE main results
- Table 3. Hard-scenario five-seed summary
- Figure 2. Backbone comparison
- Table 4. Tuning and communication comparison
- Table 5. Held-out and public trust-aware vs keep-all summary
- Table 6. `min_keep_per_group` sensitivity
- Figure 3. `seed11` mechanism illustration
- Table 7. Conditional floor hardening summary

### 附录建议放置

- public benchmark baseline full table
- all raw seed tables
- additional condfloor threshold comparisons
- extra trust diagnostics

## 最稳的章节叙事顺序

如果按投稿说服力排序，正文必须遵循下面这个逻辑链：

1. 问题存在：异构 + 攻击 + group coverage tension
2. 方法提出：trust-aware grouped defense
3. 主线成立：跨场景与五种子稳定
4. Backbone 有支撑：GraphSAGE 在 hard cases 显著更强
5. 安全价值澄清：不是普遍升 F1，而是减少 poisoned participation
6. 坏点被解释：static floor 的边界失效
7. 坏点被修复：conditional floor 在主线有效
8. 结论克制：hardening mixed on public auxiliary, so no universal overclaim

## 不建议采用的目录写法

以下几种目录组织方式不建议使用：

- 把论文写成“GraphSAGE vs MLP”式模型比较文
- 把 `conditional trust-mass floor` 提前写成主方法默认设定
- 把 `NSL-KDD` 写成主实验数据而不是 auxiliary validation
- 把 Results 顺序写成杂乱堆表，缺少“主线 -> 验证 -> 机制 -> hardening”的推进逻辑

## 一版可直接使用的英文目录

1. Introduction
2. Related Work
3. Method
4. Experimental Setup
5. Results
5.1 Overall robustness across topology-aware scenarios
5.2 Five-seed robustness on the hard scenarios
5.3 Backbone comparison
5.4 Communication-efficient tuning
5.5 Trust-aware versus keep-all validation
5.5.1 Held-out validation on Scenario-E
5.5.2 Auxiliary public validation on NSL-KDD
5.6 Aggregation comparison
5.7 Sensitivity of min_keep_per_group
5.8 Mechanism analysis of the residual worst case
5.9 Conditional trust-mass floor hardening
6. Discussion
7. Limitations
8. Conclusion
Declarations
References
Appendix A. Additional implementation details
Appendix B. Additional seed-level tables
Appendix C. Additional public benchmark results
Appendix D. Mechanism diagnostics
Appendix E. Conditional floor ablation
