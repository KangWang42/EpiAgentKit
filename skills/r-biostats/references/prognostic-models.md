# 预后/预测模型与分期系统：建模 · 验证 · 报告

适用：构建预后评分/列线图、做风险分期系统、与现有分期（如临床 TNM）比较。
本文件的红线优先级高于"把图跑出来"——审稿人最先盯的就是这些。

```r
library(survival); library(rms); library(riskRegression); library(timeROC)
```

---

## 红线 1 · 推导/验证分离与数据泄漏（最高优先，必先确认）

**切点、分组、合并判定一旦用到验证集，"验证"即被污染、判别能力带乐观偏倚。** 这是分期/预后模型论文的头号被拒点。开工前必须答清并在文中如实写明：

- **切点 / 分箱 / 组合归并 / "因 P>0.05 故合并"等任何用到结局的决策，在哪个集合上做的？**
  - 只在**训练集**上确定、锁定后原样套用到验证集 → 可称"独立验证/held-out 验证"。
  - 在**全队列**上确定（哪怕之后再 7:3 拆分）→ 拆分只是"内部一致性展示"，**只能称内部验证**，必须辅以 bootstrap 乐观度校正，且**NEVER** 在正文/摘要冒称"独立验证 / 外部验证"。
- 代码层自查：生成 `stage`/分箱的脚本读的是全量数据还是训练子集？拆分发生在分期赋值**之前**还是**之后**？之后=泄漏。
- 没有独立外部队列时：正文方法/结果**只描述做了什么**（如 7:3 划分 + bootstrap 内部验证），**NEVER** 在正文写"未设独立外部验证队列"这类否定句——正文忽略没做的事；"缺独立外部验证"是**局限，写进讨论/局限节**。关键是**不 claim 独立/外部验证**（不 overclaim、措辞中性即可），而非在正文自陈缺陷。

> 参照 JAMA NPC TNM-9 写法：训练集 RPA 推导 → 验证集复核（并说明两集 host factors/分布可比）→ bootstrap 5000 次内部验证 → 与旧分期在 C-index/Brier/likelihood/分布/bootstrap 优势比例多维比较。

## 红线 2 · 切点如实报告，不自相矛盾

- **报告实际切点数值**（每个变量每个界值）+ **怎么定的**（数据驱动最优切点 maxstat/X-tile？取整？临床预设？）+ **在哪个集合定的**。
- "数据驱动后取整"就老实写"由数据驱动最优切点确定后取整为整数"，**NEVER** 又说成"临床预设"——口径自相矛盾=审稿人追问切点来源。
- 最优切点搜索易过拟合：报告切点同时点明这一点，并用红线 1 的内部/外部验证框架对冲。

---

## 判别能力：点估计不够，要 CI + 正式检验

比较两套预后系统（如新分期 vs 临床 TNM），**只给两个 C-index 点估计不够**，必须给 95% CI 与正式差异检验：

```r
f1 <- coxph(Surv(time, event) ~ new_stage,      data = df)
f2 <- coxph(Surv(time, event) ~ clinical_stage, data = df)
cc <- concordance(f1, f2)                 # 同一数据两相关 concordance
est <- cc$concordance; V <- cc$var
d <- est[1] - est[2]; se <- sqrt(c(1,-1) %*% V %*% c(1,-1))
p_diff <- 2 * pnorm(-abs(d / se))         # 差异检验 P
ci <- function(k) sprintf("%.3f (%.3f-%.3f)", est[k], est[k]-1.96*sqrt(V[k,k]), est[k]+1.96*sqrt(V[k,k]))
# 时间依赖 AUC: timeROC(T, delta, marker=predict(fit,type="lp"), cause=1, times=...)
```

## 校准：定量，不止"贴近对角线"

- 报**校准斜率**（理想=1）与 bootstrap 乐观度校正值；图按数据范围裁剪坐标轴使曲线段铺满（保留 45° 线）。
- `rms::validate(cph_fit, B=1000)` 一次给出乐观度校正的 `Dxy`（→ C-index）与 `Slope`（校准斜率）。

```r
dd <- datadist(df[, model_vars]); options(datadist="dd")   # 只放模型变量, 否则 datadist 抓到坏列报错
fit <- cph(Surv(t_yr, event) ~ ., data = df, x=TRUE, y=TRUE, surv=TRUE)
v <- validate(fit, B=1000)
c_corrected <- (v["Dxy","index.corrected"] + 1) / 2
slope_corrected <- v["Slope","index.corrected"]
```

## Brier 分数（越低越好）

```r
sc <- Score(list(New=f1, Clinical=f2), Surv(time,event)~1, data=df,
            times=c(3,5)*365.25, metrics="brier", null.model=TRUE)
sc$Brier$score   # 每模型每时点的 Brier
```

## bootstrap 优势比例（与旧系统比，JAMA 式）

```r
win <- 0; B <- 1000
for (b in 1:B) { db <- df[sample(nrow(df), replace=TRUE), ]
  if (concordance(coxph(Surv(time,event)~new_stage, db))$concordance >
      concordance(coxph(Surv(time,event)~clinical_stage, db))$concordance) win <- win+1 }
# 报告 "新系统 C-index 在 win/B (xx%) 次重抽样中高于旧系统"
```
> **优势比例只在模型推导独立于重抽样比较时才干净。** 若分期在全队列推导（红线 1），优势比例被内部乐观夸大（常见 100%）——此时**不报该指标**，改用上文 C-index 差异检验说明优劣。
>
> **写作原则（通用）：不报一个还得自我否定的结论。** 一个结果若必须紧跟"但这含乐观成分/不可靠/受污染"才能写，就别写它——要么换成干净、站得住的指标（如差异检验、乐观度校正后的 C-index），要么不写。区分两类：①必要的方法学如实交代（"内部验证而非独立验证""完全病例 N"）——保留；②带自我否定尾巴的弱/虚结果（"100% 占优但偏乐观"）——删。前者是诚实框架，后者是自拆台。

---

## 共线性：联合模型的"不显著"≠"无价值"

新旧分期同入一个模型时往往**高度共线**（都反映同一负荷/分期信息）。此时某系统系数不显著**可能只是共线性导致系数不稳定**，**NEVER** 直接解读为"该系统无独立预后价值"。

```r
rms::vif(coxph(Surv(time,event) ~ new_stage + clinical_stage + covars, df))  # VIF>10 即严重共线
```
报 VIF；结论改以**单变量判别比较**为主，联合模型只作辅证并承认共线局限。

## DCA：给具体数值，不止"净获益更高"

报告**具体阈概率区间 + 净获益数值**（如"5 年、阈概率 20% 时净获益 0.069 vs 0.061"），不写空泛的"更高净获益"。曲线交叉处如实说明只在某区间占优。

## 多重比较

相邻分期两两 log-rank 等多次比较，报 **Holm/Bonferroni 校正后** P，并说明做了校正。

## 缺失协变量（呼应全局 CLAUDE.md：先核原始数据）

- 见 NA/缺失先回原始数据核实是真缺失还是解析丢失（如 `as.numeric()` 把文本"NA"/带单位值强制成 NA——是解析问题不是真缺失）；能由其他字段反算（如身高体重→BMI）就反算。
- 确为真实缺失：**报告缺失例数/比例**；多因素若用**完全病例**，必须写明完全病例的 N 与事件数（与基线表总 N 的差额要可解释），并考虑多重插补（mice）作为更优方案。**NEVER** 静默完全病例导致模型 N 与基线表对不上而不交代。

---

## 报告清单（交付/投稿前逐条过）

- [ ] 切点/分组在训练集还是全队列确定，已如实定性为独立/内部验证，无"独立验证"虚称
- [ ] 实际切点数值 + 确定方式（数据驱动取整/预设）已写明且口径一致不矛盾
- [ ] C-index 给 95% CI；两系统比较给正式差异检验 P（非仅点估计）
- [ ] 校准给斜率（+bootstrap 校正）/Brier，非仅"贴近对角线"
- [ ] DCA 给具体阈概率与净获益数值
- [ ] 新旧系统联合模型报 VIF；不显著不误读为无价值
- [ ] 多重比较已校正并说明
- [ ] 缺失已核原始数据、报告比例与完全病例 N/事件数
- [ ] 文中报告的每个 C-index/HR/AIC 与脚本真实输出逐一核对（改交付稿别信旧 prose，按分析对象重核）
- [ ] 图与正文的分期/变量命名**字面一致**（同一后缀写法，如全用 `IA_TLG` 或全用 `IA(TLG)`，不混用）
