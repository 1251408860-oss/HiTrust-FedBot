# 第三章 方法设计

说明：本章为中文导师阅览版，正文沿用 BlockSys/Springer LNCS 常见的数字引用风格，在文中使用 `[1]`、`[2]` 等顺序编号。参考文献均为真实已发表条目，并附 DOI 链接。由于该文件当前作为独立章节草稿使用，编号在本章内单独顺排；后续并入整篇论文时可统一重排。

## 3.1 问题设定与符号

本文研究的对象是 topology-aware federated bot detection。与把客户端视为同质样本池的常规联邦分类任务不同，本任务中的每个客户端对应一个局部图切片，其训练信号同时受到节点属性、边连接关系与局部语义角色分布的影响 [1,2,4-7]。因此，服务器端在聚合时不仅要面对 non-IID 与 poisoned update 风险，还必须避免在过滤低信任更新时把某一类关键语义组整体删除。

设全局客户端集合为 `\(\mathcal{C}\)`，联邦训练总轮数为 `\(T\)`，第 `\(t\)` 轮参与训练的活跃客户端集合为 `\(\mathcal{C}^{(t)} \subseteq \mathcal{C}\)`。第 `\(i\)` 个客户端持有局部图

```latex
\[
\mathcal{D}_i = (\mathcal{V}_i, \mathcal{E}_i, X_i, Y_i),
\]
```

其中 `\(\mathcal{V}_i\)`、`\(\mathcal{E}_i\)` 分别表示局部节点集合与边集合，`\(X_i\)` 为节点特征，`\(Y_i\)` 为节点标签。全局模型参数记为 `\(\theta^{(t)}\)`。服务器在进入联邦轮次前先执行少量 warmup，得到较稳定的初始参数 `\(\theta^{(0)}\)`；其目的不是引入额外防御，而是减少短轮次联邦训练中随机初始化带来的波动。

在第 `\(t\)` 轮，每个客户端从 `\(\theta^{(t)}\)` 出发进行本地训练，得到本地参数 `\(\theta_i^{(t+1)}\)` 与本地更新

```latex
\[
\Delta_i^{(t)} = \theta_i^{(t+1)} - \theta^{(t)}.
\]
```

攻击者可控制一部分客户端，并在上传阶段把正常更新 `\(\Delta_i^{(t)}\)` 篡改为攻击更新 `\(\widehat{\Delta}_i^{(t)}\)`。本文方法不访问原始数据，只依赖本地验证表现、更新相似性、时间稳定性和更新幅度来估计客户端可信度，再在“按组保留覆盖”的约束下执行聚合。因而，本文的设计目标可表述为：在尽可能减少 poisoned participation 的同时，保留必要的 semantic group coverage。

为此，我们引入客户端到语义组的映射 `\(g(i)\in\mathcal{G}\)`，其中 `\(\mathcal{G}\)` 表示所有客户端组。记第 `\(g\)` 组在第 `\(t\)` 轮的活跃客户端集合为

```latex
\[
\mathcal{C}_g^{(t)} = \{ i \in \mathcal{C}^{(t)} \mid g(i)=g \}.
\]
```

与传统“仅按信任阈值删客户端”的策略相比，本文显式要求过滤过程与组覆盖约束共同成立。换言之，安全控制变量不再只是“保留多少客户端”，还包括“每个关键语义组是否仍保留可参与聚合的代表客户端”。

## 3.2 客户端图划分与分组联邦

本文实现中的客户端并不是对全图随机抽样得到，而是由局部 IP/流节点归属关系诱导形成。对于第 `\(i\)` 个客户端，系统首先确定其拥有的局部节点子集 `\(\mathcal{V}_i^{\text{own}}\)`，再把共享支撑节点并入可见范围，形成实际用于训练的局部子图。其可写为

```latex
\[
\mathcal{V}_i = \mathcal{V}_i^{\text{own}} \cup \mathcal{V}^{\text{support}},
\qquad
\mathcal{E}_i = \{(u,v)\in \mathcal{E} \mid u\in\mathcal{V}_i,\, v\in\mathcal{V}_i\}.
\]
```

这一处理对应真实网络环境中的常见情形：不同边缘节点各自掌握局部流量视角，但仍共享少量公共上下文。相比把训练样本打散后再分发给客户端，这种划分更接近实际部署时的 non-IID 结构 [1,4]。

仅有客户端划分还不足以表达拓扑语义异质性，因此本文进一步在客户端层面执行 grouped federation。实现上，系统优先依据客户端所覆盖节点的主导 role family 生成组标签；若显式角色信息不足，则退化为基于负载规模的 bucket 分组。由此，每个客户端都对应唯一组标记 `\(g(i)\)`。这一设计不是为了人为增强差异，而是为了让服务器端在做信任过滤时保留“哪些客户端在语义上属于同一局部结构切片”的信息。

从方法角度看，这一步的意义在于把后续聚合从“平坦客户端池上的鲁棒平均”提升为“分组内聚合 + 组间聚合”的两级结构。这样做有两个直接后果。第一，组内仍可利用 trust score 抑制异常更新。第二，即便某些组整体较弱，也不至于在阈值过滤后立刻从全局训练中完全消失。这正是本文与传统 flat aggregation 设定的关键区别。

## 3.3 主干模型与参数更新模式

本文在实现上提供两类主干：一类是仅依赖节点特征的 `FeatureMLP`，另一类是主线使用的 `GraphSAGEAdapter`。前者作为无显式拓扑传播的对照；后者用于刻画邻域关系在 Bot 检测中的贡献 [5-7]。为降低通信成本并支持不同强度的参数更新，模型中显式加入了 adapter 瓶颈层，并配套三种 tuning 模式：`head_only`、`adapter_ft` 与 `full_ft`。

对于 GraphSAGE 主干，记节点 `\(v\)` 的输入特征为 `\(\mathbf{x}_v\)`，则第一层邻域聚合与 adapter 注入可写为

```latex
\[
\mathbf{h}_v^{(1)} = \sigma\!\left(\mathrm{SAGE}_1\!\left(\mathbf{x}_v,\{\mathbf{x}_u : u\in\mathcal{N}(v)\}\right)\right),
\]
```

```latex
\[
\mathbf{a}_v = \sigma(W_{\text{down}}\mathbf{h}_v^{(1)}),
\qquad
\widetilde{\mathbf{h}}_v^{(1)} = \mathbf{h}_v^{(1)} + \alpha W_{\text{up}}\mathbf{a}_v,
\]
```

```latex
\[
\mathbf{h}_v^{(2)} =
\sigma\!\left(\mathrm{SAGE}_2\!\left(\widetilde{\mathbf{h}}_v^{(1)},
\{\widetilde{\mathbf{h}}_u^{(1)} : u\in\mathcal{N}(v)\}\right)\right),
\qquad
\widehat{\mathbf{y}}_v = W_c \mathbf{h}_v^{(2)},
\]
```

其中 `\(\alpha=0.1\)` 为 adapter 残差缩放系数。`FeatureMLP` 采用相同的 adapter 结构，但不执行邻域聚合，只在特征空间内完成前馈映射。

本地训练目标采用类别不平衡加权交叉熵。对客户端 `\(i\)` 的训练节点集合 `\(\mathcal{T}_i\)`，损失函数写为

```latex
\[
\mathcal{L}_i^{(t)}(\theta) =
- \sum_{v\in \mathcal{T}_i} w_{y_v}
\log p_{\theta}(y_v \mid v),
\]
```

其中 `\(w_0=1\)`，正类权重由本地训练划分中的负正样本比给出，

```latex
\[
w_1 = \frac{N_{0,i}}{\max(N_{1,i},1)}.
\]
```

三种 tuning 模式的差别在于可训练参数集合 `\(\Theta_{\text{train}}\)` 不同：`head_only` 仅更新分类头，`adapter_ft` 更新 adapter 与分类头，`full_ft` 更新全部参数。若仅传输可训练参数，则单客户端单轮的通信近似可写为

```latex
\[
B_i^{(t)} \approx 4 \cdot |\Theta_{\text{train}}|,
\]
```

其中系数 `\(4\)` 来自单精度浮点参数的字节数。该估计虽是实现层面的近似，但足以支持后文对 tuning mode 与通信开销关系的比较。

## 3.4 信任感知客户端评分

本文不直接把某个客户端判定为“好”或“坏”，而是先计算连续型 trust score，再基于阈值执行过滤。这样做的原因在于：在非独立同分布且结构异质的场景中，低相似度更新并不总是恶意更新，部分更新只是来自边缘语义组。连续评分能为后续“按组保底”留出操作空间。

首先，服务器在第 `\(t\)` 轮收集所有本地更新，并计算轮内平均更新

```latex
\[
\overline{\Delta}^{(t)} =
\frac{1}{|\mathcal{C}^{(t)}|}
\sum_{j\in\mathcal{C}^{(t)}} \Delta_j^{(t)}.
\]
```

对客户端 `\(i\)`，系统先在验证集上搜索最优分类阈值 `\(\eta_i^{(t)}\)`，并记录对应的验证 `F1` 作为 `val_gain`

```latex
\[
\eta_i^{(t)} =
\arg\max_{\eta\in\{0.10,0.15,\ldots,0.90\}}
\mathrm{F1}_{\mathrm{val},i}^{(t)}(\eta),
\qquad
v_i^{(t)} = \max_{\eta} \mathrm{F1}_{\mathrm{val},i}^{(t)}(\eta).
\]
```

然后，系统分别计算更新相似性、时间稳定性、验证误差惩罚和更新范数惩罚。相似性定义为

```latex
\[
a_i^{(t)} =
\mathrm{clip}\!\left(
1 -
\frac{\left\|\Delta_i^{(t)}-\overline{\Delta}^{(t)}\right\|_2}
{\max\left(\left\|\overline{\Delta}^{(t)}\right\|_2,\varepsilon\right)},
-1,1
\right),
\]
```

稳定性定义为

```latex
\[
b_i^{(t)} =
\begin{cases}
1, & \text{若客户端 } i \text{ 尚无上一轮更新记录},\\[4pt]
\mathrm{clip}\!\left(
1-\dfrac{\left\|\Delta_i^{(t)}-\Delta_i^{(t-1)}\right\|_2}
{\max\left(\left\|\Delta_i^{(t-1)}\right\|_2,\varepsilon\right)},
-1,1
\right), & \text{否则}.
\end{cases}
\]
```

两类惩罚项写为

```latex
\[
c_i^{(t)} = \max\!\left(0, 1-\mathrm{Acc}_{\mathrm{val},i}^{(t)}\right),
\]
```

```latex
\[
n_i^{(t)} =
\min\!\left(
1,
\frac{\left\|\Delta_i^{(t)}\right\|_2}
{\frac{1}{|\mathcal{C}^{(t)}|}\sum_{j\in\mathcal{C}^{(t)}}\left\|\Delta_j^{(t)}\right\|_2}
\right).
\]
```

在此基础上，原始信任分数定义为

```latex
\[
s_i^{(t)} =
0.45\, v_i^{(t)}
\;+\; 0.25\, a_i^{(t)}
\;+\; 0.20\, b_i^{(t)}
- 0.05\, c_i^{(t)}
- 0.05\, n_i^{(t)}.
\]
```

这组权重并非从理论最优推导而来，而是作为保守型安全控制的经验加权：验证表现占最高权重，用于反映本地模型是否至少在验证划分上产生了有意义的判别增益；相似性与稳定性则分别刻画“是否偏离当前群体更新方向”和“是否在时间上突然异常”；验证误差惩罚与范数惩罚用于抑制高误差或幅度异常的更新 [2,3]。

由于不同轮次中 `\(s_i^{(t)}\)` 的数值范围可能波动，服务器进一步在轮内执行 min-max 归一化，得到

```latex
\[
\widetilde{s}_i^{(t)} =
\frac{s_i^{(t)} - \min_{j\in\mathcal{C}^{(t)}} s_j^{(t)}}
{\max\!\left(\max_{j\in\mathcal{C}^{(t)}} s_j^{(t)} - \min_{j\in\mathcal{C}^{(t)}} s_j^{(t)}, \varepsilon\right)}.
\]
```

后续过滤、保底与聚合统一使用归一化后的 `\(\widetilde{s}_i^{(t)}\)`。

## 3.5 组覆盖约束的信任过滤

若仅使用统一阈值 `\(\tau_{\text{trust}}\)` 做过滤，则第 `\(t\)` 轮的基础保留指示变量可写为

```latex
\[
m_i^{(t)} = \mathbb{I}\!\left[\widetilde{s}_i^{(t)} \ge \tau_{\text{trust}}\right].
\]
```

这种写法在平坦客户端池中是自然的，但在本文场景下存在明显问题：一旦某个小组因噪声较大、样本较少或局部攻击而整体得分偏低，该组就可能在单轮内被全部移除。为避免这一现象，本文引入最小组保留数 `\(K\)`，要求过滤后尽量满足

```latex
\[
\sum_{i\in\mathcal{C}_g^{(t)}} m_i^{(t)} \ge K,
\qquad \forall g \in \mathcal{G}_{\text{active}}^{(t)}.
\]
```

当第 `\(g\)` 组中按阈值通过的客户端数不足 `\(K\)` 时，系统在该组内按照如下词典序重新排序客户端：

```latex
\[
r_i^{(t)} =
\left(
\widetilde{s}_i^{(t)},
\mathrm{F1}_{\mathrm{val},i}^{(t)},
-\|\Delta_i^{(t)}\|_2,
-i
\right).
\]
```

这里的排序规则与实现一致，即优先选择更高信任分数、更高验证 `F1` 的客户端；若前两者相同，则偏向更小更新范数与更小客户端编号。随后，系统按该顺序把客户端补入保留集合，直到达到 `\(K\)` 或该组已无候选客户端为止。

这一机制就是本文所说的 group-coverage-constrained trust filtering。需要强调的是，它的目标不是追求更高的平均 `F1`，而是在安全过滤过程中避免语义组被“静默清空”。因此，本方法的核心收益应理解为更保守地控制 poisoned participation，同时尽量维持分组覆盖，而不是保证精度一定上升。

## 3.6 分层聚合

在得到最终保留客户端集合后，本文不直接对所有客户端更新做一次全局平均，而是先在组内聚合，再在组间聚合。对第 `\(g\)` 组，记其最终保留客户端集合为 `\(\mathcal{K}_g^{(t)}\)`，则组内权重定义为

```latex
\[
\omega_i^{(t)} = \max\!\left(\widetilde{s}_i^{(t)}, 0.01\right).
\]
```

对应的组内聚合更新为

```latex
\[
\Delta_g^{(t)} =
\frac{\sum_{i\in\mathcal{K}_g^{(t)}} \omega_i^{(t)} \Delta_i^{(t)}}
{\sum_{i\in\mathcal{K}_g^{(t)}} \omega_i^{(t)}}.
\]
```

随后，服务器对所有有保留客户端的组做简单平均，得到全局更新

```latex
\[
\Delta^{(t)} =
\frac{1}{|\mathcal{G}_{\text{keep}}^{(t)}|}
\sum_{g\in\mathcal{G}_{\text{keep}}^{(t)}} \Delta_g^{(t)},
\qquad
\theta^{(t+1)} = \theta^{(t)} + \Delta^{(t)}.
\]
```

这种 hierarchical aggregation 的直觉非常直接：组内允许更可信的客户端承担更大权重，而组间则避免大组因客户端数量更多而自动垄断全局更新方向。作为比较，系统中也实现了 `mean`、`median` 与 `krum` proxy 等聚合方式，但主线方法使用的是上述两级均值结构。

为了防止极端情况下出现“所有客户端都被过滤掉”而无法更新的空聚合问题，系统在实现层面保留了回退策略：若本轮没有任何客户端通过最终保留规则，则临时恢复所有客户端并使用单位权重聚合。该步骤仅作为数值与流程稳定性的兜底，不改变本文方法的主线逻辑。

## 3.7 条件信任质量保底加固

静态组保底虽然能缓解“语义组被整体删空”的问题，但它也存在一个清晰的 principal failure mode：若某个小组几乎被完全投毒，静态 `group floor` 仍可能为了满足 `\(K\)` 而强行保留一个低信任中毒客户端。换言之，组覆盖约束本身也可能成为攻击面的一部分。

为此，本文进一步引入 conditional trust-mass floor。对第 `\(g\)` 组，定义其轮内信任质量为

```latex
\[
M_g^{(t)} =
\sum_{i\in\mathcal{C}_g^{(t)}} \max\!\left(\widetilde{s}_i^{(t)}, 0\right).
\]
```

若采用 `static` 策略，则无条件执行组保底；若采用 `conditional_trust_mass` 策略，则只有在

```latex
\[
M_g^{(t)} \ge \rho_{\text{mass}}
\]
```

时才允许触发组保底，其中 `\(\rho_{\text{mass}}\)` 为最小组信任质量阈值。在当前实现与主线实验中，` \(\rho_{\text{mass}} = 0.10\)`。于是，最终的保底逻辑可写为

```latex
\[
\text{ApplyFloor}(g,t)=
\begin{cases}
1, & \text{policy}=\texttt{static},\\[4pt]
1, & \text{policy}=\texttt{conditional\_trust\_mass}
\ \text{且}\ M_g^{(t)}\ge \rho_{\text{mass}},\\[4pt]
0, & \text{否则}.
\end{cases}
\]
```

这一加固的意义在于把“保组”从绝对约束改为带条件的安全控制。若某组中仍存在足够的可信质量，则允许通过保底保留语义覆盖；若该组整体信任质量已经过低，则不再强制保留，以避免 fully poisoned small group 把静态保底反向利用。需要强调的是，这一机制是针对静态保底失效模式的 targeted hardening，而不是对所有场景都优于静态保底的 universal replacement。

## 3.8 训练流程伪代码

为便于后续整理论文 LaTeX 正文，本文将主线训练过程整理为如下伪代码。该版本与当前实现保持一致：先本地训练并收集更新，再计算 trust score，随后执行阈值过滤、按组保底和分层聚合，最后更新全局参数。

```latex
\begin{algorithm}[t]
\caption{HiTrust-FedBot Trust-Aware Grouped Federated Training}
\label{alg:hitrust}
\begin{algorithmic}[1]
\Require Initial model $\theta^{(0)}$, rounds $T$, trust threshold $\tau_{\mathrm{trust}}$, minimum keep-per-group $K$, floor policy $\pi$, trust-mass threshold $\rho_{\mathrm{mass}}$
\For{$t = 0,1,\ldots,T-1$}
    \State Server broadcasts $\theta^{(t)}$ to active clients $\mathcal{C}^{(t)}$
    \ForAll{$i \in \mathcal{C}^{(t)}$}
        \State Client $i$ performs local training on $\mathcal{D}_i$ and returns update $\Delta_i^{(t)}$
        \State Evaluate local validation performance and obtain $v_i^{(t)}$
        \State Compute similarity $a_i^{(t)}$, stability $b_i^{(t)}$, penalties $c_i^{(t)}$ and $n_i^{(t)}$
        \State Compute raw trust score $s_i^{(t)}$
    \EndFor
    \State Normalize $\{s_i^{(t)}\}$ into $\{\widetilde{s}_i^{(t)}\}$ by round-wise min-max scaling
    \ForAll{$i \in \mathcal{C}^{(t)}$}
        \State Initialize keep flag $m_i^{(t)} \gets \mathbb{I}[\widetilde{s}_i^{(t)} \ge \tau_{\mathrm{trust}}]$
    \EndFor
    \ForAll{group $g \in \mathcal{G}_{\mathrm{active}}^{(t)}$}
        \State Compute trust mass $M_g^{(t)} = \sum_{i\in\mathcal{C}_g^{(t)}} \max(\widetilde{s}_i^{(t)}, 0)$
        \If{$\sum_{i\in\mathcal{C}_g^{(t)}} m_i^{(t)} < K$ and $(\pi=\texttt{static} \ \textbf{or}\ M_g^{(t)} \ge \rho_{\mathrm{mass}})$}
            \State Rank clients in $\mathcal{C}_g^{(t)}$ by $(\widetilde{s}_i^{(t)}, \mathrm{F1}_{\mathrm{val},i}^{(t)}, -\|\Delta_i^{(t)}\|_2, -i)$
            \State Promote top-ranked unkept clients until the group reaches $K$
        \EndIf
    \EndFor
    \ForAll{group $g$ with kept clients}
        \State Set $\omega_i^{(t)} \gets \max(\widetilde{s}_i^{(t)}, 0.01)$ for each kept client
        \State Aggregate intra-group update $\Delta_g^{(t)} \gets \frac{\sum_i \omega_i^{(t)} \Delta_i^{(t)}}{\sum_i \omega_i^{(t)}}$
    \EndFor
    \State Aggregate inter-group update $\Delta^{(t)} \gets \frac{1}{|\mathcal{G}_{\mathrm{keep}}^{(t)}|} \sum_g \Delta_g^{(t)}$
    \State Update global model $\theta^{(t+1)} \gets \theta^{(t)} + \Delta^{(t)}$
\EndFor
\State \Return $\theta^{(T)}$
\end{algorithmic}
\end{algorithm}
```

综上，HiTrust-FedBot 的方法核心不在于单独发明某一种“更强聚合器”，而在于把 trust scoring、group coverage preservation 与 hierarchical aggregation 组织成同一个安全控制回路。它首先用连续信任分数识别异常参与，再用按组保底避免结构语义被过度清空，最后用两级聚合抑制大组主导效应，并在需要时通过 conditional trust-mass floor 处理静态保底的边界失效模式。

## 第三章参考文献

[1] Li, T., Sahu, A.K., Talwalkar, A., Smith, V.: Federated Learning: Challenges, Methods, and Future Directions. *IEEE Signal Processing Magazine* 37(3), 50-60 (2020). DOI: https://doi.org/10.1109/MSP.2020.2975749

[2] Mothukuri, V., Parizi, R.M., Pouriyeh, S., Huang, Y., Dehghantanha, A., Srivastava, G.: A survey on security and privacy of federated learning. *Future Generation Computer Systems* 115, 619-640 (2021). DOI: https://doi.org/10.1016/j.future.2020.10.007

[3] Cao, X., Fang, M., Liu, J., Gong, N.Z.: FLTrust: Byzantine-robust Federated Learning via Trust Bootstrapping. *Proceedings 2021 Network and Distributed System Security Symposium* (2021). DOI: https://doi.org/10.14722/ndss.2021.24434

[4] Ferrag, M.A., Friha, O., Maglaras, L., Janicke, H., Shu, L.: Federated Deep Learning for Cyber Security in the Internet of Things: Concepts, Applications, and Experimental Analysis. *IEEE Access* 9, 138509-138542 (2021). DOI: https://doi.org/10.1109/ACCESS.2021.3118642

[5] Bilot, T., El Madhoun, N., Al Agha, K., Zouaoui, A.: Graph Neural Networks for Intrusion Detection: A Survey. *IEEE Access* 11, 49114-49139 (2023). DOI: https://doi.org/10.1109/ACCESS.2023.3275789

[6] Wu, Z., Pan, S., Chen, F., Long, G., Zhang, C., Yu, P.S.: A Comprehensive Survey on Graph Neural Networks. *IEEE Transactions on Neural Networks and Learning Systems* 32(1), 4-24 (2021). DOI: https://doi.org/10.1109/TNNLS.2020.2978386

[7] Liu, F., Li, Z., Yang, C., Gong, D., Lu, H., Liu, F.: SEGCN: a subgraph encoding based graph convolutional network model for social bot detection. *Scientific Reports* 14, Article 4122 (2024). DOI: https://doi.org/10.1038/s41598-024-54809-z
