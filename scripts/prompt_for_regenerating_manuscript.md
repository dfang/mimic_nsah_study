# 论文生成提示词

## 使用方式

后续每次重新运行分析 pipeline 后，将以下内容发送给 Claude Code 即可自动生成英文 + 中文论文、图表和 PDF。

```
claude ./scripts/prompt_for_regenerating_manuscript.md
```

## 提示词正文

```
请根据最新的研究结果 `dist/YYYYMMDD/analysis_result.md`（将 YYYYMMDD 替换为当前执行日期，如 20260702）完成以下工作：

## 0. 创建目录与记录生成模型 (readme.txt)
创建 `dist/YYYYMMDD` 目录。在该目录下编写一个 `readme.txt`，声明 markdown 和 pdf 文件是由哪个模型生成的（例如你当前是 `claude`、`gemini` 还是 `codex`）。

## 1. 更新图表

运行作图脚本生成 8 张 PNG 图，传入当前日期文件夹作为参数：
```

python3 scripts/generate_manuscript_figures.py YYYYMMDD

```

如果数据有变化，请先根据 `dist/YYYYMMDD/analysis_result.md` 中的新数据更新 `scripts/generate_manuscript_figures.py` 脚本中的硬编码数值，然后再运行。

必需图表清单：
- `dist/YYYYMMDD/figures/fig1_cohort_flowchart.png` — 队列筛选流程图
- `dist/YYYYMMDD/figures/fig2_phenotype_heatmap.png` — K=3 表型标准化中心热图
- `dist/YYYYMMDD/figures/fig3_outcomes.png` — 死亡率/贫血率/输注率柱状图
- `dist/YYYYMMDD/figures/fig_s1_k4_refinement.png` — K=3/K=4 交叉分布堆叠柱状图
- `dist/YYYYMMDD/figures/fig_s2_bootstrap.png` — Bootstrap 稳定性分布图
- `dist/YYYYMMDD/figures/fig_s3_gcs_sensitivity.png` — GCS 变量选择敏感性分析
- `dist/YYYYMMDD/figures/fig_s4_prediction.png` — 死亡预测模型 AUROC/Brier 比较
- `dist/YYYYMMDD/figures/fig_s5_forest_plot.png` — 调整后 OR 森林图

## 2. 更新英文论文

更新 `dist/YYYYMMDD/manuscript_non_traumatic_sah_phenotypes.md`，要求：

**格式规范**：
- 标题保持：Early Multimodal Physiological Phenotypes and Outcomes in Critically Ill Adults with Non-Traumatic Subarachnoid Hemorrhage: A Retrospective Cohort Study Using MIMIC-IV 3.1
- 结构：Abstract → Introduction → Methods → Results → Discussion → Conclusions → References → Tables
- 图表嵌入正文对应位置（不要放在文末），使用 `dist/YYYYMMDD/figures/` 下的相对/绝对路径，每张图后紧跟 `**Figure X.** 说明文字。` 格式的图例
- 所有数据必须与 `dist/YYYYMMDD/analysis_result.md` 严格一致，不得编造

**图表嵌入位置**：
- Figure 1 → Methods / Cohort Selection 段落后
- Figure 2 → Results / K=3 表型特征描述后
- Figure 3 → Results / 紧随 Figure 2
- Figure S2 → Results / Bootstrap 稳定性段落后
- Figure S3 → Results / GCS 敏感性段落后
- Figure S1 → Results / K=4 探索性分析段落后
- Figure S4 → Results / 死亡预测段落后
- Figure S5 → Results / 调整回归段落后

**表格要求**：
- Table 1：基线特征表（Overall + K=3 phenotype 分层，含 demographics、admission、insurance、SAH etiology、outcomes）
- Table 2：核心生理特征表（8 features × 3 phenotypes，median [IQR] + P value）
- Table S1：敏感性分析汇总表（含所有 sensitivity analyses 的 ARI 和死亡率梯度）

## 3. 更新中文论文

同步更新 `dist/YYYYMMDD/manuscript_non_traumatic_sah_phenotypes_cn.md`，要求与英文版内容一致、图表位置相同，专业学术中文表达。

## 4. 生成 PDF

运行转换脚本，传入当前日期文件夹作为参数：
```

DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH" python3 scripts/convert_manuscript_to_pdf.py YYYYMMDD

```

产出：
- `dist/YYYYMMDD/pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf`
- `dist/YYYYMMDD/pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf`

## 5. 质量检查清单

生成完毕后逐项确认：
- [ ] 所有数据与 `dist/YYYYMMDD/analysis_result.md` 一致
- [ ] 8 张图全部嵌入正文正确位置
- [ ] N=1,187，三个表型的 n、死亡率、贫血率数字正确
- [ ] Bootstrap ARI、GCS sensitivity ARI、K-means vs Hierarchical ARI 数值正确
- [ ] 调整后 OR 及 95% CI 与 regression 输出一致
- [ ] 中文论文无"P1/P2/P3"裸标签，使用"表型 1（保留生理功能型）"等完整名称
- [ ] PDF 中表格为三线表格式，图片清晰不越界
- [ ] 标题使用原标题（非"Beyond GCS"版本）
- [ ] `dist/YYYYMMDD/readme.txt` 已成功写入并注明生成模型名。
```

---

## 辅助脚本说明

| 脚本                                     | 作用                             |
| ---------------------------------------- | -------------------------------- |
| `scripts/generate_manuscript_figures.py` | 根据分析结果数据生成 8 张 PNG 图 |
| `scripts/convert_manuscript_to_pdf.py`   | 将 Markdown 论文转为排版后的 PDF |

两个脚本均需根据新的分析数据手动更新其中的硬编码数值后才能正确运行。
