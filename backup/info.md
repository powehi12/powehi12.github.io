结合你做 LLM agent / EHR 这个方向，我按"从源头到消化"的顺序整理一份，顺带标注哪些对你的子方向特别值得盯。

**一、论文源头**
- arXiv：cs.CL、cs.AI、cs.LG、cs.MA 这几个分类每天扫一遍标题和摘要就够了，别试图全读。可以用 RSS 订阅分类，也可以直接看每日 listing。
- Hugging Face Daily Papers：社区投票筛出来的每日热门论文，一天十几篇，是性价比最高的"每日必刷"，agent、推理方向的论文出现频率很高。
- Google Scholar / Semantic Scholar 提醒：给关键词（"EHR agent""clinical LLM""multi-agent LLM"）和几位重点作者设 alert，新论文自动送上门，是最省力的被动渠道。
- OpenReview：ICLR、NeurIPS 的审稿全程公开，看 reviewer 怎么拆一篇论文，比只读论文本身学得多；自己投稿前更要去看同类论文挨过什么刀。
- Connected Papers / ResearchRabbit：丢一篇种子论文进去生成引用图谱，写 related work、快速摸清一个子领域的神器。
- Papers with Code：查 benchmark 和 SOTA，比如 text-to-SQL 各榜单的最新进展。

**二、会议与期刊**
- ML 三大会：NeurIPS、ICML、ICLR；NLP 看 ACL、EMNLP、NAACL；另外 COLM 是专门做语言模型的新会，agent 和推理方向论文密度非常高，值得整届接收列表都翻一遍。
- 医疗 AI 这条线：ML4H、CHIL、AMIA 三个会，加上 JAMIA、npj Digital Medicine、NEJM AI 几本刊，做 EHR 属于必须盯的名单，EHRSQL、MedAgentBench 这类 benchmark 工作常出自这里。
- Workshop 往往比主会更前沿也更水，但信号来得早——各大会的 agent workshop、GenAI for Health 之类扫一眼接收列表就能感知风向。

**三、社交媒体与社区**
- X/Twitter：信息最快的地方，没有之一。follow @_akhaliq（每日论文搬运）、各大 lab 官号、做 agent 和 RL 的活跃研究者，记得建 list 隔离信息流，不然时间线很快变成垃圾场。
- Reddit：r/MachineLearning 偏学术，r/LocalLLaMA 偏开源模型和工程实践，后者对了解模型真实能力、部署坑点非常有用。
- 中文渠道：机器之心、量子位、PaperWeekly、专知这些公众号做快讯和解读；知乎在顶会放榜季有大量一手讨论和吐槽；MLNLP 社区、智源社区常有讲座和综述分享。
- Discord：Hugging Face、EleutherAI，以及你在用的 agent 框架各自的 server，看别人踩坑和直接提问都很高效。

**四、博客与 Newsletter**
- Lilian Weng 的 Lil'Log：她那篇 LLM Powered Autonomous Agents 基本是 agent 方向的公共入门读物，其他综述质量也极高。
- Interconnects（Nathan Lambert）：RLHF / RL for LLM 的一手分析，你要碰 RL 训练的话建议直接订阅。
- Simon Willison：LLM 应用与 agent 工程实践，更新勤、视角务实。
- Sebastian Raschka 的 Ahead of AI：技术综述向，适合定期补全大图景。
- AI News（smol.ai）：每天自动汇总 Twitter/Reddit/Discord 的讨论，信息密度大到需要跳读，但漏网之鱼极少。
- 公司博客：Anthropic 的工程博客（比如 Building Effective Agents 那篇）、OpenAI、DeepMind 的 research blog，一手信息且常带工程细节。

**五、开源与代码**
- GitHub Trending 加各类 awesome 仓库（awesome-llm-agents、医疗 LLM 相关的 awesome 列表），快速摸清一个方向已有哪些轮子。
- 盯几个 agent 框架的 repo：LangGraph、AutoGen/AG2、CAMEL、MetaGPT、OpenHands，看 issue 和 discussion 比看文档更能了解真实痛点，做多智能体的话前面几个尤其相关。
- Hugging Face 的模型与数据集页；做 EHR 还要加上 PhysioNet——MIMIC 系列数据的老家，相关社区讨论也在那边。

**六、视频与播客**
- B站：李沐的论文精读系列是中文区标杆，顶会 tutorial 的搬运也不少。
- YouTube：Karpathy 的从零手写系列（理解 LLM 底层最好的材料之一）、Stanford CS224N/CS234 公开课、Yannic Kilcher 的论文解读。
- 播客：Latent Space 聊 AI 工程和 agent 落地，Dwarkesh Podcast 的研究者深度访谈质量很高，都适合通勤时听。

**七、别被信息淹没**
- 建议搭一个漏斗：每天 5-10 分钟刷 HF Daily Papers 和推特 list → 值得细看的丢进 Zotero → 每周固定半天精读 1-2 篇。读得少而深，比囤一千篇 PDF 有用得多。
- 用 RSS 阅读器（Feedly、Folo 之类）把 arXiv 分类、博客、公众号统一收进一个入口，减少平台间反复横跳。
- follow 人比 follow 论文高效：你方向里活跃的二三十位作者，他们的新作加上互相引用，基本就覆盖了你需要知道的一切。
- 信息焦虑是研究生标配，但筛选能力比获取能力稀缺——渠道不必全订，挑三五个坚持刷，就已经赢过大多数人了。


这个问题比"关注谁"更本质。我按自己观察到的、真正拉开研究生之间差距的几个维度来讲，尽量不重复前面说过的具体工具。

## 先建立一个认知：信息分层，处理方式完全不同

研究生的问题从来不是信息太少，而是太多。高效的核心是给信息分层，每层用不同的处理强度：
- **索引层（90%）**：绝大多数论文你只需要知道"它存在、解决什么问题、核心 idea 一句话"。每天花 15 分钟扫 arXiv 标题和摘要就够了，目的是建立索引——将来需要时你知道去哪找。扫到就够，别打开 PDF。
- **精读层（~10%）**：每周挑 1~2 篇和你方向强相关的，读懂方法细节、实验设计、局限。你本来就在做论文解读，这个习惯非常好——写解读就是最好的精读方式，输出会暴露你哪里没读懂。
- **复现层（~1%）**：一年认真复现几篇。跑过代码、被坑过、调过参，你对一个方法的理解会碾压只读过论文的人。做 agent 方向尤其如此，很多论文的"效果"你一跑就知道水分多大。

锐评一句：很多研究生把"刷 arXiv"当成做研究，每天看 50 篇摘要获得虚假的充实感。信息囤积不等于认知，认知来自对比、批判和动手。

## 拓宽眼界的四个方向

**1. 横向：盯相邻领域，这是你的低垂果实**
对你做 EHR agent 特别重要的一个事实：这个方向的创新引擎不在医疗圈，在通用 agent 圈。long-horizon、多智能体、agent RL、memory、context management 的进展，通用圈（SWE-bench、WebArena、tool-use RL 这条线）比医疗圈快半年到一年。医疗这边很多"新工作"本质是把通用技术搬进临床场景。所以你的信息配比应该是：通用 LLM/agent 圈至少占一半，医疗 AI 圈占另一半。只盯医疗圈，你永远在追别人搬运过的东西；盯着通用圈，你能自己当搬运的人，甚至预判下一波什么技术会进医疗。

**2. 纵向：读老论文，了解领域史**
知道 RETAIN 时代大家怎么做 EHR 建模、text-to-SQL 为什么在医疗落地了十年还没落地、MIMIC 这个数据集的局限在哪——这些历史让你能识别"新瓶装旧酒"，也让你明白哪些坑前人已经踩过。领域史是最被低估的信息源，因为它不在任何 feed 里，得主动去挖（综述、经典论文的引用链、老教授的 talk）。

**3. 真实世界：走出论文**
- 想办法和临床医生、医院信息科的人聊。EHR 方向大量论文的任务设定是伪需求，只有见过真实 EHR 系统长什么样、医生一天的工作流是什么，你才有判断力。这是你相对纯 NLP 背景研究者的潜在护城河。
- 亲手重度使用 agent 产品（Claude Code、Cursor 这类）。你会对"agent 什么时候靠谱、什么时候崩"建立肉体直觉，这比读十篇 agent 论文有用。
- 有机会就去工业界实习。实习最大的价值不是技能，是彻底刷新你对"什么问题重要"的判断。

**4. 人：眼界的主要来源其实是人**
和强的人聊天是带宽最高的信息获取方式，没有之一。具体做法：会议上 poster session 比 oral 有价值得多，因为能直接聊；组会上多问问题，跨组的 reading group 蹭起来；找到 2~3 个你认为"品味好"的研究者（不一定是大佬，可能是高年级博士生），观察他们关注什么、怎么评价工作——follow 有品味的人，等于把一部分信息筛选外包给了他们的判断力。另外推荐看 OpenReview 上 ICLR/NeurIPS 的公开评审，那是免费观摩"资深研究者如何批判一篇论文"的最佳场所，看多了你自己的批判能力会长得很快。

## 几个具体的深度信息源（补充前面没讲的）

- **Newsletter/博客**：Lilian Weng 的 Lil'Log（概念梳理天花板）；Nathan Lambert 的 Interconnects（RL 和 post-training 方向，和你 RL 训练的兴趣直接相关）；Sebastian Raschka 的 Ahead of AI；Jack Clark 的 Import AI（宏观视野）。长内容建认知，短推文只能建索引。
- **Podcast**：Dwarkesh Podcast、Latent Space、No Priors。通勤时听，性价比高的"被动输入"。
- **技术报告**：DeepSeek、Qwen、Llama 这类开源模型的 technical report 比大多数论文信息密度高，尤其是训练细节和 RL 部分。
- **公开课**：Stanford CS336（从零构建 LLM）、CS224N。发现基础有洞就回去补课，不丢人，丢人的是带着洞硬读前沿论文。

## 最后两条心法

**给信息获取设上限。** 固定时段处理信息（比如早上半小时扫 feed），其余时间关掉。FOMO 是研究生大敌——真正重要的工作会反复出现在你视野里，根本错过不了；能被你错过的，大概率不重要。
**维护一个"问题清单"而不只是文献库。** Zotero/Obsidian 管文献大家都会，但更值钱的是记下你自己的困惑和不满："为什么多智能体在 X 场景没用？""现在的 long-horizon 评测到底在测什么？"研究品味就是从持续追问这些问题里长出来的，而好的研究选题，几乎都藏在你自己清单的某一行里。