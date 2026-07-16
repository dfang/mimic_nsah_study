# Citation update and final audit report / 引文更新与最终审计报告

**Status / 状态:** Static citation package validation passed; actual citeproc rendering was not run. The package has not undergone `mimic-review` with `journal-reviewer` and is therefore **not frozen or submission-ready**. / 引文包已通过静态验证，但未执行实际 citeproc 渲染；尚未经过 `mimic-review` 的 `journal-reviewer` 审查，因此**未冻结，也未达到投稿就绪状态**。

## Scope and target / 范围与目标

- Target journal: **Intensive Care Medicine (ICM), Original Paper**. / 目标期刊：**Intensive Care Medicine（ICM），Original Paper**。
- This was a targeted citation update and rapid evidence verification, **not a systematic review**. / 本工作是定向引文更新与快速证据核验，**不是系统综述**。
- Source manuscripts were the original English and Chinese files in `dist/`; citation-aware copies were created separately. The originals were not overwritten. / 来源稿件为 `dist/` 中的英文与中文原稿；引文版另存，未覆盖原稿。
- Literature search date: 2026-07-15; audit rerun: 2026-07-16; evidence coverage ended 2026-07-15. PubMed/MEDLINE was the only bibliographic database searched. / 文献检索日期为 2026-07-15，审计复跑日期为 2026-07-16，证据覆盖截至 2026-07-15；书目检索仅使用 PubMed/MEDLINE。
- Search limits were English, publication dates 1800-01-01 through 2026-07-15, and the first 20 relevance-ranked results per query, supplemented by legacy-reference and known-item checks. / 检索限于英文、发表日期 1800-01-01 至 2026-07-15、每条检索式相关性排序前 20 条，并辅以旧引文和已知文献核验。

## Search summary / 检索摘要

| Query / 检索式主题 | Raw count / 原始计数 |
|---|---:|
| Q1 SAH systemic/extracerebral complications / SAH 全身及颅外并发症 | 325 |
| Q2 SAH anemia/hemoglobin/transfusion / SAH 贫血、血红蛋白及输血 | 737 |
| Q3 critical-care unsupervised phenotyping / 重症无监督表型 | 777 |
| Q4 MIMIC-IV/eICU/PhysioNet database provenance / 数据库来源 | 4,236 |
| Q5 SAH/ICU severity scales and reporting statements / SAH、ICU 严重度量表及报告规范 | 17,977 |

The non-unique raw aggregate was 24,052. One hundred candidate slots (20/query) yielded 100 unique PMIDs; 13 legacy strings were checked separately. Twenty-two authoritative records were retained. These counts are not a PRISMA flow and do not establish exhaustive novelty. Exact queries, literal E-utilities parameters, ordered PMIDs, and screening decisions are in `literature_search_log.md`. / 五条检索式原始结果非去重合计 24,052 条；每条前 20 条共 100 个候选位点，对应 100 个唯一 PMID；另单独核验 13 条旧引文。最终保留 22 条权威记录。上述计数不是 PRISMA 流程，也不能证明创新性检索穷尽。完整检索式、E-utilities 参数、PMID 顺序及筛选决定见 `literature_search_log.md`。

## Legacy references / 13 条旧引文处置

“Retained” means the authoritative identity was retained, with corrected/complete metadata where needed; “replaced” means the manuscript uses a separately verified record rather than the conflicting legacy string; “excluded” means the legacy item is not cited in the updated manuscripts. / “保留”表示保留经权威核验的文献身份并补全必要元数据；“替换”表示稿件使用独立核验记录而非冲突旧字符串；“排除”表示更新稿未引用该旧条目。

| Legacy no. | Status / 状态 | Audit disposition / 审计处置 |
|---:|---|---|
| 1 | Retained / 保留 | Macdonald 2017; issue metadata completed; cited for broad SAH acuity, mortality, and disability context. / 补全期号，用于 SAH 高危、死亡与致残背景。 |
| 2 | Retained / 保留 | Seymour 2019; authoritative title differs slightly from legacy wording; cited with an ARDS exemplar for critical-care phenotyping. / 权威题名与旧表述略有差异，与 ARDS 示例共同用于重症表型背景。 |
| 3 | Retained / 保留 | Hunt–Hess original scale record; issue completed. / Hunt–Hess 原始量表记录，补全期号。 |
| 4 | Retained / 保留 | GCS original report; subtitle and issue completed. / GCS 原始报告，补全副标题与期号。 |
| 5 | Replaced and legacy excluded / 已替换且旧条目排除 | Unresolved composite Naidech citation; no matching DOI/PMID. The anemia claim uses verified Rosenberg 2013. PMID 17717494 remains a separately verified related record and was not treated as a repair. / Naidech 旧引文疑为复合冲突，无法匹配 DOI/PMID；贫血主张改用经核验的 Rosenberg 2013。PMID 17717494 仅作为独立相关记录，不视为修复旧引文。 |
| 6 | Retained / 保留 | MIMIC-IV data paper retained for provenance; official MIMIC-IV 3.1 record added for exact version. / 数据论文用于来源说明，另增官方 3.1 版本记录。 |
| 7 | Retained / 保留 | eICU data paper retained for provenance; official eICU-CRD 2.0 record added for exact version. / 数据论文用于来源说明，另增官方 2.0 版本记录。 |
| 8 | Excluded from cited manuscripts / 从引文稿排除 | PhysioNet platform paper is verified and bibliography-eligible but unnecessary once exact official dataset-version records support the access/provenance claims. / PhysioNet 平台论文已核验且可入书目，但精确版本官方记录已直接支持访问与来源主张，故未引用。 |
| 9 | Replaced and legacy excluded / 已替换且旧条目排除 | Legacy SAHARA metadata used the 2024 online year and omitted print details; manuscript uses the separately verified 2025 print record (PMID 39655786). / 旧 SAHARA 条目采用 2024 在线发表年且缺少印刷版信息；稿件改用独立核验的 2025 印刷版记录。 |
| 10 | Retained / 保留 | Chai 2023 identity resolved; all authors and issue restored; use narrowed to supported inflammation/neuro-systemic context. / 已补全作者与期号，引用范围限于有证据支持的炎症及神经-全身背景。 |
| 11 | Retained with scope limit / 限定范围保留 | APACHE II record retained only for the general ICU severity-score domain, not eICU extraction-level version or NSAH criterion validity. / 仅用于一般 ICU 严重度评分背景，不用于证明 eICU 提取版本或 NSAH 效标效度。 |
| 12 | Retained / 保留 | SOFA record retained for the general organ-dysfunction domain; issue and subtitle completed. / 用于一般器官功能障碍领域，补全期号与副标题。 |
| 13 | Retained / 保留 | Canonical STROBE record retained; title and issue completed. / 保留 STROBE 权威记录并补全题名与期号。 |

## Eligible, cited, and intentionally uncited records / 合格、已引与有意未引记录

- The evidence package contains 22 bibliography-eligible records and `references.bib` contains the same 22 stable keys. / 证据包含 22 条书目合格记录，`references.bib` 含相同的 22 个稳定键。
- Both manuscripts use the same 16 unique keys in the same 17 citation clusters. All cited keys resolve in the bibliography, key map, evidence table, and verification table. / 中英文稿使用相同的 16 个唯一键及顺序一致的 17 个引文簇；所有已引键均可在书目、键映射、证据表和核验表中解析。
- Six eligible records are intentionally uncited: / 6 条合格记录有意未引用：

| Record / 记录 | Reason / 理由 |
|---|---|
| `hoh2023guideline` (EV-002) | AHA/ASA guideline was not needed for a verified broad-context claim; recommendation-level use is not cleared because the linked erratum text was inaccessible. / 稿件的广义背景主张无需该指南；因关联勘误全文不可访问，未放行具体推荐级引用。 |
| `naidech2007hemoglobin` (EV-004) | Separately verified related anemia study, but not an inferred repair for legacy 5; Rosenberg 2013 more directly supports the retained anemia wording. / 是独立核验的相关贫血研究，但不能推断为旧引文 5 的修复；Rosenberg 2013 更直接支持保留表述。 |
| `naidech2010hemoglobingoal` (EV-006) | Earlier small randomized hemoglobin-goal study is not needed for the narrowly worded SAHARA-era statement. / 较早的小样本随机血红蛋白目标研究并非当前谨慎 SAHARA 表述所必需。 |
| `goldberger2000physionet` (EV-012) | Platform provenance is superseded for the cited claims by exact official MIMIC-IV 3.1 and eICU-CRD 2.0 version records. / 对当前主张而言，平台来源已由精确的官方数据版本记录更直接支持。 |
| `zimmerman2006apacheiv` (EV-019) | APACHE IV background cannot establish the extracted eICU APACHE version or independent NSAH criterion validity; citing it would overstate CLM-016 support. / APACHE IV 背景不能证明 eICU 实际提取版本或独立 NSAH 效标效度，引用将夸大对 CLM-016 的支持。 |
| `benchimol2015record` (EV-022) | RECORD is relevant and eligible, but the manuscript currently claims STROBE adherence only; no unsupported RECORD-adherence claim was added. / RECORD 相关且合格，但稿件目前仅声明遵循 STROBE，未新增未经落实的 RECORD 遵循声明。 |

## Claim provenance and bilingual synchronization / 主张溯源与中英同步

- The claim audit contains 31 synchronized English/Chinese material-claim rows. External citations were assigned only to supported background, scale, database-provenance, reporting-guideline, and randomized-evidence claims. / 主张审计含 31 条中英同步的重要主张；外部引文仅用于有证据支持的背景、量表、数据库来源、报告规范及随机证据主张。
- Study-generated cohort counts, estimates, phenotype results, sensitivity analyses, and study-specific conclusions remain traced to current internal result artifacts rather than external literature. / 队列计数、效应估计、表型结果、敏感性分析及本研究特定结论仍溯源于当前内部结果工件，而非外部文献。
- Unsupported broad claims were narrowed or explicitly framed as study motivation, operational choices, interpretations, limitations, or recommendations requiring prospective evaluation. / 缺乏完整证据的宽泛主张已收窄，或明确表述为研究动机、操作性选择、解释、局限或需前瞻验证的建议。
- The Structured Abstracts contain no citations. The Chinese manuscript retains Chinese body text and mirrors the English citation identities, membership, and order. / 两个结构式摘要均无引文；中文稿保留中文正文，并与英文稿在引文身份、成员及顺序上同步。

## Unresolved items, conflicts, and access limits / 未解决事项、冲突与访问限制

- Unresolved citation keys: **none**; all 16 cited keys resolve statically. / 未解析引文键：**无**；16 个已引键均通过静态解析。
- Source placeholders: final local ethics/IRB wording and consent/waiver determination remain author/institution responsibilities before submission. Database papers and version pages do not replace the submitting institution's determination. / 来源占位：最终本地伦理/IRB 表述及知情同意/豁免结论仍须作者与投稿机构在投稿前确认；数据库论文与版本页不能替代机构认定。
- Legacy conflicts: legacy 5 remains an unresolved composite and is excluded; legacy 9 remains a year/print-metadata conflict and was replaced by the separately verified 2025 record. / 旧引文冲突：旧条目 5 仍为未解决复合引文并已排除；旧条目 9 存在年份/印刷版元数据冲突，已由独立核验的 2025 记录替换。
- AHA/ASA erratum limit: PMID 38011240 is linked to the 2023 guideline. Identity is unchanged, but the correction text was inaccessible, so no specific recommendation-level use is cleared. / AHA/ASA 勘误限制：2023 指南关联 PMID 38011240；文献身份不变，但因勘误正文不可访问，未放行具体推荐级用途。
- CLM-016/APACHE gap: official eICU schema documents named APACHE/result columns, but not the extracted `apacheversion` value or independent criterion validity in NSAH. The manuscripts now describe eICU-provided severity variables not used in phenotype assignment; they do not claim external criterion validation. / CLM-016/APACHE 缺口：官方 eICU 架构仅证明存在 APACHE/结果字段，不能证明实际提取的 `apacheversion` 值或其在 NSAH 中的独立效标效度；稿件现仅称其为未参与表型分配的 eICU 严重度变量，不再宣称外部效标验证。
- Evidence extraction was abstract/authoritative-metadata-only for most journal records; several historical scale papers had metadata/title-level assessment only. Publisher paywall or anti-bot responses restricted some full texts. Full-text-dependent claim checking remains for human review. / 多数期刊记录仅基于摘要与权威元数据提取，部分历史量表论文仅完成元数据/题名层级评估；部分出版社全文受付费墙或反机器人限制。依赖全文的主张仍需人工复核。
- No direct claim-complete source was found for the study-specific `>=5 units/24 h` exclusion rationale, comparative scarcity of neurocritical phenotyping, or superiority of fixed transport over de novo reclustering. These were retained only as an explicit operational choice or were narrowed/removed. / 未找到直接且完整支持研究特定 `>=5 units/24 h` 排除理由、神经重症表型应用相对稀少或固定迁移优于重新聚类的来源；相关内容仅作为明确操作性选择保留，或已收窄/删除。

## Protocol/design and manuscript deviations / 协议、设计与稿件偏离

- The literature workflow deviated from systematic-review methods by using a targeted PubMed-only, top-20-per-query screen plus known-item verification; it was neither registered nor exhaustive. / 文献流程采用定向、仅 PubMed、每条前 20 条加已知文献核验，偏离系统综述方法；未注册且不穷尽。
- Citation-accuracy edits narrowed unsupported wording but did not change cohort definitions, feature windows, estimands, numerical results, or phenotype assignments. The current implementation applies the study-specific `>=5 units/24 h` operational exclusion, but its prespecification status is not established. Both `protocol.md` and `sap.md` are `DRAFT_BLOCKED` reconstructions created after outcomes had been accessed. Protocol line 146 requires the exclusion's status to be confirmed before freeze and recommends an explicit sensitivity analysis that does not exclude massive transfusion. This exclusion is therefore an unresolved protocol deviation/design decision, not an externally validated threshold. / 引文准确性编辑收窄了缺乏证据的表述，但未改变队列定义、特征时间窗、估计目标、数值结果或表型分配。当前实现采用研究特定的 `>=5 units/24 h` 操作性排除，但其预设状态尚未建立。`protocol.md` 与 `sap.md` 均为查看结局后重建且状态为 `DRAFT_BLOCKED`；protocol 第 146 行要求在冻结前确认该排除的地位，并建议增加“**不排除大量输血**”的明确敏感性分析。因此，该排除是未解决的协议偏离/设计决定，而非经外部验证的阈值。
- CLM-016 was recast from external criterion validation to comparison with eICU-provided severity variables not used for assignment. Claims about neurocritical phenotyping scarcity and fixed-transport superiority were removed or reframed. / CLM-016 已由外部效标验证改写为与未参与分配的 eICU 严重度变量比较；神经重症表型稀少和固定迁移优越性的主张已删除或重构。
- The current protocol and SAP are not frozen; they are `DRAFT_BLOCKED` reconstructions created after outcomes were accessed. A citation audit cannot adjudicate all protocol deviations. Before any freeze, the authors must reconcile the implemented analyses against the protocol/SAP and maintain a deviations log, with particular attention to the massive-transfusion exclusion. / 当前 protocol 与 SAP 尚未冻结，而是查看结局后重建的 `DRAFT_BLOCKED` 文件；引文审计不能裁定全部协议偏离。在任何冻结之前，作者必须将已实现分析与 protocol/SAP 对账并维护 deviations log，尤其需要处理大量输血排除。

## CSL provenance / CSL 来源

This section fulfills the CSL provenance sidecar deferred from Task 3. / 本节兑现 Task 3 延后至本报告记录的 CSL 来源 sidecar。

- Official repository: Citation Style Language `styles`; retrieval date 2026-07-16; pinned commit `439002f8dbcc44acd99e72c05fd6a6880c509d84` (commit date 2026-07-10). Exact upstream raw URLs: `https://raw.githubusercontent.com/citation-style-language/styles/439002f8dbcc44acd99e72c05fd6a6880c509d84/dependent/intensive-care-medicine.csl` and `https://raw.githubusercontent.com/citation-style-language/styles/439002f8dbcc44acd99e72c05fd6a6880c509d84/springer-basic-brackets.csl`. / 官方仓库：Citation Style Language `styles`；获取日期 2026-07-16；固定提交如上（提交日期 2026-07-10）；精确上游 raw URL 如上。
- Dependent ICM style metadata: title `Intensive Care Medicine`; ID `http://www.zotero.org/styles/intensive-care-medicine`; ISSN `0342-4642`; eISSN `1432-1238`; parent `http://www.zotero.org/styles/springer-basic-brackets`; license CC BY-SA 3.0. / ICM dependent 样式元数据包括上述题名、ID、ISSN、eISSN、父样式及 CC BY-SA 3.0 许可。
- Dependent-style SHA-256: `5ff121ec62813de6197d05b8cb61c8390048aab57bcff6a8f9665f5977a706c0`. / dependent 样式 SHA-256 如上。
- Independent parent: `springer-basic-brackets.csl`; ID `http://www.zotero.org/styles/springer-basic-brackets`; license CC BY-SA 3.0; SHA-256 `2f39b2c93cf7a90cb41c72a2945700c4d227ad233682d7fe843c77364a11ba82`. / 独立父样式及其 ID、许可、SHA-256 如上。
- Local `journal.csl` is byte-identical to the official independent parent at the pinned commit. The parent was used locally because the official ICM file is dependent and delegates formatting rules to it; this is a provenance-preserving parent mapping, not a fabricated ICM style. / 本地 `journal.csl` 与固定提交中的官方独立父样式逐字节一致；因官方 ICM 文件为 dependent 样式并将格式规则委托给父样式，故本地使用父样式。这是保留来源的父映射，并非伪造 ICM 样式。

## Rendering and static verification / 渲染与静态验证

- `pandoc`, standalone `citeproc`, `bibtex`, `biber`, and `bibtool` executables were unavailable. Python `bibtexparser`, `pybtex`, and `citeproc` modules were also unavailable. No dependency was added. / 环境中无 `pandoc`、独立 `citeproc`、`bibtex`、`biber`、`bibtool`，亦无 Python `bibtexparser`、`pybtex`、`citeproc` 模块；未新增依赖。
- Therefore, **actual Pandoc/citeproc rendering was not run**. Rendered citation order, bibliography de-duplication, DOI/URL display, and final reference-section typography were not visually inspected. No synthetic render was generated. / 因此，**未运行实际 Pandoc/citeproc 渲染**；未能目视检查渲染后的引文顺序、书目去重、DOI/URL 显示及参考文献版式，也未生成伪渲染。
- Static validation passed for key resolution and unused records; 16 synchronized keys and 17 synchronized clusters; 22 evidence rows × 31 columns and 35 verification rows × 17 columns; BibTeX entry types, balanced braces, authors, DOI/PMID identities and uniqueness; CSL XML and checksum; YAML metadata; absence of hand-numbered references; original hashes; and research-number snapshots. / 静态验证通过项目包括：键解析及未用记录、16 个同步键与 17 个同步引文簇、22×31 证据表与 35×17 核验表、BibTeX 类型/花括号/作者/DOI/PMID 身份与唯一性、CSL XML 与校验和、YAML、无手工编号参考文献、原稿哈希和研究数字快照。

## Original integrity / 原稿完整性

- English original SHA-256: `00a972cf88aff9a28207cbc23651e2aa2f01a490abc6405510a566cd8bc890f1` — unchanged. / 英文原稿哈希未变。
- Chinese original SHA-256: `2a5ecf13b8e2090d577e1f5e9696e76d1eb93d72555ed76a1a8d7c5c532dd55e` — unchanged. / 中文原稿哈希未变。
- Citation-aware copies preserve the original research-number snapshot after excluding YAML, Pandoc citation syntax, and the legacy reference sections. / 在排除 YAML、Pandoc 引文语法和旧参考文献区段后，引文版保留原稿研究数字快照。

## Required next gate / 后续必需门槛

Install or provide a verified Pandoc/citeproc environment and render both manuscripts; inspect the generated references and links; complete ethics/consent wording; perform full-text checks where claims depend on details beyond abstracts; then route the complete package through `mimic-review` with `journal-reviewer`, resolve blocking and major findings, and re-review corrections. Until those steps pass, this package must not be called frozen or submission-ready. / 后续须在经验证的 Pandoc/citeproc 环境中渲染中英文稿并检查参考文献与链接，补全伦理/知情同意表述，对依赖摘要之外细节的主张完成人工全文核验，再交由 `mimic-review` 的 `journal-reviewer` 审查、解决阻断及重大问题并复审修订。在这些门槛通过前，不得称本引文包已冻结或可投稿。
