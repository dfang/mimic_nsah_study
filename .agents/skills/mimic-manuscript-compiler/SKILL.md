---
name: mimic-manuscript-compiler
description: 将 Markdown 格式的医学论文手稿 (Manuscript) 编译为符合学术期刊投稿规范的 PDF 文件。支持基于 Typst 或 Google Chrome Headless (HTML to PDF) 两种渲染路径，自动处理页边距、双倍行距、连续行号、标题页、图表排版和参考文献排版。
---

# MIMIC-IV 论文手稿 PDF 编译器 (Manuscript PDF Compiler)

本技能用于将医学论文手稿（Markdown 格式，如 `docs/manuscript.md`）及其已核验的 `references.bib`、目标期刊 `journal.csl` 转换为学术期刊投稿格式的 PDF 文件。

编译前先应用 `mimic-data-governance`，确认手稿只包含允许提交的汇总材料。先用 `mimic-submission-packager` 获取目标期刊的实时格式要求；本 skill 负责渲染，不负责推断投稿政策。

Pandoc citeproc 是两条路径唯一的引用解析器。先完成同一套引用 preflight 和 citeproc 解析，再选择 PDF 渲染器；Typst 与 Chrome 不得独立生成参考文献。

本编译器支持两种渲染路径，Agent 应根据本地环境工具链和期刊要求选择：
1. **Typst 编译路径 (推荐)**：需要本地安装 `typst` CLI。适合生成高度专业、完美的学术排版，并原生支持双倍行距、页码和连续行号。
2. **Chrome Headless 编译路径**：需要本地安装 Google Chrome。Agent 将 Markdown 转换为包含医学期刊 CSS 的 HTML 文件，随后调用 Chrome headless 打印为 PDF。

---

## 1. 编译路径执行指南

### 共同前置步骤：引用检查与解析

1. 运行 `pandoc --version`，记录版本。若 Pandoc 不可用，返回阻断状态、缺失依赖和未执行的完整命令；不得退回静态编号或 Typst 原生 `bibliography()`。
2. 以手稿目录或显式项目 resource path 为基准解析 `manuscript.md`、`references.bib`、`journal.csl` 和 citation-verification table。
3. 在渲染前确认：
   - Markdown、BibTeX 和 CSL 文件可读；
   - citation key 唯一，规范化 DOI 无未经审查的重复；
   - 正文使用的每个 key 都存在于 BibTeX，并在核验表中为 `bibliography_eligible: yes`；
   - submission-ready 构建中没有未解决的 source placeholder；
   - 没有把 Pandoc citation syntax 与手写数字参考文献混用；
   - citeproc 没有失败或产生 citation warning。
4. 使用相同的引用输入分别生成可审计的 resolved intermediate。Typst 路径命令形态：

   ```bash
   pandoc manuscript.md \
     --citeproc \
     --bibliography=references.bib \
     --csl=journal.csl \
     --fail-if-warnings \
     --standalone \
     --to=typst \
     --output=resolved-manuscript.typ
   ```

   HTML 路径仅替换输出格式与文件名：

   ```bash
   pandoc manuscript.md \
     --citeproc \
     --bibliography=references.bib \
     --csl=journal.csl \
     --fail-if-warnings \
     --standalone \
     --to=html5 \
     --output=resolved-manuscript.html
   ```

`--fail-if-warnings` 若被证明会因无关警告阻断，可改为两阶段 warning 分类；但所有缺失 key、BibTeX/CSL 解析错误和 citation warning 仍必须阻断。保留 resolved intermediate，不能把它当作新的可编辑手稿源。

### 路径 A：Typst 编译 (Typst CLI)
1. **环境检查**：检查本地是否安装 `typst`（通过运行 `typst --version`）。若未安装，提示用户可运行 `brew install typst`。
2. **格式转换**：将 citeproc 生成的 `resolved-manuscript.typ` 与 `resources/manuscript_template.typ` 的布局设置组合。模板只排版已解析内容，不调用第二个 bibliography engine。
3. **执行编译**：运行编译命令：
   ```bash
   typst compile input.typ output.pdf
   ```

### 路径 B：Chrome Headless 编译 (HTML to PDF)
1. **格式转换**：使用 citeproc 生成的 `resolved-manuscript.html`，并将 `resources/manuscript_template.html` 中的 CSS 样式嵌入其 `<style>` 标签。不得用 JavaScript 重新生成 bibliography。
2. **执行编译**：使用 macOS 本地已安装的 Google Chrome，以 headless 模式执行打印 PDF：
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --print-to-pdf=output.pdf input.html
   ```

---

## 2. 论文排版规范 (Styling Standards)

优先遵循目标期刊当前 author instructions。只有期刊未规定时，才将以下设置作为常见回退值，而不是普适强制标准：

* **页边距 (Margins)**：四周页边距必须为 **1 英寸 (2.54 厘米)**。
* **行距 (Line Spacing)**：正文必须为 **双倍行距 (Double-spaced, line-height: 2.0)**。
* **字体 (Fonts)**：推荐使用通用的衬线或无衬线字体，如 **Georgia**, **Times New Roman** 或 **Arial**，字号为 **11-12pt**。
* **连续行号 (Continuous Line Numbers)**：期刊要求时在页面左侧渲染连续行号。HTML/CSS 路径必须实际检查行号是否逐行且跨页连续；无法可靠实现时改用 Typst 或明确报告限制。
* **页码 (Page Numbers)**：页脚右下角或居中显示页码。
* **段落缩进**：正文段落首行缩进，或者段落间留出清晰的空白，不可发生行与段落重叠。
* **图表排版**：三线表 (Three-line tables) 必须清晰美观，避免复杂的边框；图片必须居中并附带清晰的 Legend。

---

## 3. 手稿基本结构模版

编译时请确保以下部分有清晰的版面分隔：
1. **Title Page (标题页)**：包含 Title, Running Head, Authors, Affiliations, Corresponding Author Info。
2. **Abstract (摘要)**：结构化摘要（Background, Methods, Results, Conclusions）。
3. **Main Text (正文)**：包含 Introduction, Methods, Results, Discussion。
4. **Declarations / Declarations of Interest**。
5. **References (参考文献)**：格式统一。

## 4. 渲染验证

编译后必须检查 PDF 页数、字体嵌入、页边距、分页、行号连续性、表格截断、图片分辨率、链接、页码和缺字。将 PDF 渲染为页面图像，抽查标题页、正文中的代表性引文、宽表、图、References 的前部/中部/末部以及末页；发现问题后重新编译。

缺失 citation key、未核验记录、未解决 placeholder、BibTeX/CSL 错误或 citation warning 会阻断 submission-ready 输出。若仅为诊断排版而保留 PDF，必须明确标记为 non-submission，并在 generation note 中保留阻断问题。

返回最终 PDF、源 Markdown、`references.bib`、`journal.csl`、citation-verification table 和 resolved intermediate 的路径/哈希；Pandoc 与渲染器版本；完整命令；模板版本；所有警告、未解决限制和未满足的期刊要求。将 generation note 与结果交回 `mimic-submission-packager`。
