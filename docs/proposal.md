项目策划书：面向经贸领域的“术语-政策-舆情”多粒度英汉双语语料库构建
Project Eco-Insight: A Multi-Granularity Bilingual Corpus for Economic Analysis
1. 项目背景与立意 (Background & Motivation)
1.1 痛点分析
当前经贸领域的语料资源存在严重的“两极分化”与“碎片化”问题，难以满足复合型人才培养及深层研究需求：
●	缺乏对齐 (Alignment Gap)： 经济学专业学生难以准确理解英文原版术语的细微差别，而外语/翻译系学生缺乏经济学背景知识，市面上缺乏权威、动态更新的“双语对齐”领域知识库。
●	维度单一 (Dimensional limitation)： 现有语料库要么仅是静态的词典（术语层），要么仅是纯文本的新闻堆砌（语料层），缺乏将“微观概念（术语）”、“宏观政策（官方报告）”与“实时市场情绪（新闻舆情）”打通的整合型资源。
1.2 项目目标
本项目旨在构建一个垂直于经济贸易领域的智能化英汉双语语料库系统 (Eco-Insight)。
不同于传统的静态语料库，本项目利用 AI 技术（LLM） 与现代开源工具链，实现从数据采集、清洗、对齐到标注的全流程自动化，构建一个包含三个维度的立体语料库：
1.	微观层 (Micro)： 英汉双语经济学术语定义与知识图谱。
2.	宏观层 (Macro)： 中美央行/政府财政金融报告平行/可比语料。
3.	动态层 (Real-time)： 带有情感标注 (Sentiment Labeling) 与趋势映射的财经新闻语料。
2. 总体架构 (Architecture)
我们将语料库设计为“金字塔”结构，底层稳固，顶层灵动，强调数据的多维联动：
Layer 1: 核心知识库 (Knowledge Base)
●	内容： 经济学核心术语（如 Inflation, GDP, Fiscal Policy, Quantitative Easing）。
●	形式： 结构化数据 (JSON)，包含中英双语定义、相关概念链接（Graph Links）。
●	来源： Wikipedia (Category: Economics), Investopedia, IMF Terminology。
Layer 2: 政策平行与可比库 (Policy & Comparable Corpus)
●	内容： 长文本报告。重点对齐中国人民银行《货币政策执行报告》 vs 美联储 (Fed) 会议纪要/Beige Book。
●	形式： * 段落级对齐 (Paragraph-aligned)： 针对具有官方译文的报告。
○	主题级聚类 (Topic-aligned)： 针对结构不同的报告，通过 NLP 提取“通胀”、“就业”、“利率”等相同主题段落进行对照。
●	来源： 官方政府网站 PDF/HTML。
Layer 3: 市场情绪与趋势库 (Sentiment & Trend Corpus)
●	内容： 短文本。财经新闻标题、快讯（Bloomberg, Reuters, 财新）。
●	形式： 带有标签的数据 (Tag: 利好/利空, 置信度: 0.9, 涉及术语ID)。
●	创新点： 术语热度趋势图 —— 将语料频率与市场指数（如标普500、上证指数）时间轴叠加，不仅辅助语言学习，更辅助经济研判。
3. 技术路线与开源工具链 (Tech Stack & Open Source Tools)
核心策略：“拒绝重复造轮子，利用开源工具 + LLM 实现降维打击”。
3.1 数据采集 (Data Acquisition)
●	维基百科抓取： 使用 wikipedia-api (Python)。
○	优势： 直接提取 Summary 和 Language Links，无需解析复杂 HTML，保证基础定义的准确性。
●	PDF 报告解析： 使用 Marker (GitHub: VikParuchuri/marker)。
○	优势： 基于 AI 的 PDF 转 Markdown 工具，能完美处理央行报告中的复杂表格和数学公式（优于 PyPDF2），保留经济数据的完整性。
3.2 数据清洗与对齐 (Cleaning & Alignment)
●	简繁转换： 使用 OpenCC，统一中文数据标准。
●	智能对齐策略： * 使用 LF Aligner 进行基础的句子/段落对齐。
○	针对非严格平行文本，引入 Sentence-BERT 计算语义相似度，实现“软对齐”（Soft Alignment），解决中美报告行文逻辑差异大的问题。
3.3 智能标注与人机回环 (Intelligent Annotation & HITL)
采用 "Human-in-the-loop" (人机回环) 模式，确保数据质量：
1.	预标注 (Pre-annotation)： 编写脚本调用 LLM (Gemini/GPT) 对新闻数据进行初级情感打标和实体抽取。
2.	标注平台： 使用 Doccano (Vue开发)。
3.	专家校验 (Expert Review)： 由经贸学院学生（及邀请外语系同学）在 Doccano 界面中快速校对 LLM 的标注结果。
○	优势： 既利用了 AI 的效率，又发挥了学生的专业学科背景，产出高金标准数据。
3.4 成果展示与应用 (Presentation & Application)
●	Web 交互平台： Laravel + Vue.js
○	功能： “搜一个词，出定义、出政策、出新闻”的联动检索。
○	可视化： 集成 ECharts 展示术语热度趋势。
●	专业格式导出： * TMX 导出： 支持生成 Translation Memory eXchange 格式文件，可直接导入 Trados 等计算机辅助翻译软件（CAT），服务于翻译专业教学。
●	语料库分析： 使用 AntConc 生成 KWIC 索引图，验证学术价值。
4. 数据合规与伦理说明 (Data Compliance & Ethics)
为确保项目的可持续性与合规性，我们将严格遵循以下原则：
1.	数据来源合规： 仅采集公开可访问的政府报告（Public Domain）及允许爬取的百科数据。
2.	合理使用 (Fair Use)： 针对有版权的新闻媒体数据，仅在数据库中存储和展示摘要 (Snippet) 或标题，并提供原文跳转链接，不进行全文转载。
3.	非商用承诺： 本项目产出的数据集仅用于学术研究、教学及比赛展示，不进行商业售卖。
5. 实施计划 (Roadmap)
根据比赛时间轴（2025年12月-2026年3月），分阶段实施：
●	阶段一：原型验证 (2025.12 - 寒假前)
○	跑通 Layer 1 数据流程，获取 50+ 核心经济术语 JSON。
○	测试 Marker 对《中国货币政策执行报告》的解析效果。
○	完成《语料库构建技术方案》初稿。
●	阶段二：批量生产与跨学科协作 (2026.01 - 寒假)
○	全量抓取选定类别的术语。
○	跨学科组队： 邀请英语/翻译系同学加入，启动 Doccano 平台，开展“人机协作”数据清洗与校对。
○	完成后端 API 开发。
●	阶段三：平台开发与成果包装 (2026.02)
○	Laravel + Vue 前端开发，实现趋势图可视化。
○	生成 TMX 格式文件与 AntConc 分析报告。
○	撰写详细文档，重点突出“经贸+AI”的复合背景优势。
6. 预期成果与创新点 (Highlights)
1.	工具链智能化： 引入 Marker (OCR) 和 LLM 辅助标注，相比传统人工构建，效率提升 10 倍以上，且解决了PDF表格解析难点。
2.	数据立体化与趋势分析： 独创“术语-政策-舆情”三级联动，并引入时间序列分析，挖掘术语背后的经济周期规律。
3.	应用场景多元化： 不仅提供 Web 检索，还提供 TMX 专业翻译记忆库导出，同时服务于经济学研究者（看趋势）和翻译学习者（看对齐）。
4.	开源精神： 项目代码（爬虫、清洗脚本、Web源码）将整理开源，回馈社区。
