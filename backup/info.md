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