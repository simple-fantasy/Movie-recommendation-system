# 第7章 结论与展望

## 7.1 工作总结

本课题以MovieLens 32M大规模电影评分数据集为基础，设计并实现了一个融合多种推荐策略的电影推荐系统CineMatch。系统涵盖数据预处理、模型训练、在线推荐、用户交互、数据分析和系统管理六大功能板块，共19张数据库表、70余个API端点。主要完成的工作包括以下几个方面：

（1）**多策略推荐算法的实现与集成**。实现了ItemCF（基于物品协同过滤）、NCF（神经协同过滤）和Hybrid（混合推荐）三种推荐策略。ItemCF采用scikit-learn最近邻搜索进行高效的相似度预计算，NCF基于PyTorch实现了GMF架构的神经网络模型，Hybrid创新性地采用ItemCF召回+NCF重排的级联架构，在保证推荐质量的同时兼顾了可解释性和计算效率。

（2）**可解释性推荐机制**。在ItemCF和Hybrid策略中实现了推荐理由生成功能，能够向用户展示"因为你喜欢某部电影，所以推荐这部电影"的推荐来源信息，包括贡献来源电影和贡献权重。这一机制有效增强了推荐系统的透明度和用户信任。

（3）**完整的Web应用系统**。基于Flask应用工厂模式构建了完整的Web后端，基于Jinja2+Vue.js 3+Bootstrap 5构建了美观的前端界面，实现了用户注册登录、电影浏览搜索、评分收藏、评论互动、影单管理、通知推送、数据看板、管理后台等全方位功能。

（4）**用户画像与行为分析**。实现了12维用户画像特征计算，包括类型偏好、年代偏好、演员/导演偏好、评分行为特征、观影多样性、用户分层等。同时实现了用户行为追踪系统，以异步方式记录用户操作日志。

（5）**离线评估与消融实验**。设计了统一的离线评估框架，采用Leave-Last-Out协议，计算Precision@K、Recall@K、MAP@K、NDCG@K和MRR@K五项指标的对比评估，并通过消融实验分析了recall_k和per_seed_limit等关键参数对推荐效果的影响。

## 7.2 存在的不足

尽管本系统在功能完整性和推荐效果上取得了一定的成果，但仍存在以下不足之处：

（1）**冷启动问题**。对于完全无评分记录的新用户，系统只能返回热门电影作为兜底推荐，缺乏个性化的冷启动策略。未来可以考虑引入人口统计学特征（如年龄、性别）或利用用户注册时选择的兴趣标签来提供初步的个性化推荐。

（2）**NCF模型的局限性**。当前NCF仅使用了用户ID和物品ID两种特征，未利用电影的元数据特征（如类型、导演、年份）和用户的画像特征。引入更丰富的特征可以进一步提升模型性能。

（3）**实时性不足**。ItemCF的相似度表需要离线训练生成，无法实时反映用户评分行为的变化。当用户新增评分后，推荐结果无法立即调整。可考虑引入实时增量更新机制或在线学习策略。

（4）**缺乏A/B测试验证**。离线评估虽然能够比较不同算法的排序质量指标，但无法完全反映用户真实的满意度。在真实场景中，应通过A/B测试对比不同策略在实际用户使用中的点击率、评分率、停留时长等业务指标。

（5）**推荐多样性不足**。当前推荐策略主要追求排序精度，可能导致推荐结果过于集中在热门或特定类型的电影上，缺少对用户潜在兴趣的探索。可以考虑引入多样性增强机制，如MMR（Maximal Marginal Relevance）等。

## 7.3 未来展望

基于以上分析，本课题未来可以在以下方向进行改进和扩展：

（1）**引入更多特征**。将电影的元数据（类型、导演、演员、年代等）编码为NCF的辅助特征，提升模型的表达能力和泛化能力。

（2）**实时推荐**。引入消息队列（如Kafka）和流计算框架，实现用户新评分后的准实时推荐更新。

（3）**图神经网络**。使用GNN（如LightGCN、NGCF）对用户-物品交互图进行建模，利用高阶连通性提升推荐效果。

（4）**多目标优化**。在推荐精度之外，引入多样性、新颖性、惊喜度等多维度优化目标，提升用户的整体推荐体验。

（5）**部署优化**。通过Docker容器化部署、前后端分离、Redis缓存加速、CDN静态资源分发等措施，进一步提升系统的可部署性和高并发处理能力。


# 致谢

在本毕业设计论文完成之际，我要衷心感谢在整个毕业设计过程中给予我指导和帮助的所有人。

首先，我要感谢我的指导老师。从选题、方案设计到论文撰写，老师始终给予我耐心的指导和宝贵的建议。老师严谨的治学态度和丰富的专业知识，不仅帮助我顺利完成了毕业设计，更让我在学术思维和工程实践能力上得到了全面提升。

其次，感谢各位任课老师四年来在专业知识和学习方法上的教导。数据结构、数据库原理、机器学习、软件工程等课程的知识为本毕业设计的完成奠定了坚实的理论基础。

感谢我的同学们在学习和生活中给予的帮助和鼓励。在遇到技术难题时，与同学们的讨论和交流往往能带来新的思路和启发。

最后，感谢家人一直以来的理解和支持，为我提供了良好的学习环境和精神动力。

再次向所有关心和帮助过我的人表示诚挚的谢意！


# 参考文献

[1] Sarwar B, Karypis G, Konstan J, et al. Item-based collaborative filtering recommendation algorithms[C]. Proceedings of the 10th International Conference on World Wide Web. Hong Kong, 2001. 285-295

[2] He X, Liao L, Zhang H, et al. Neural collaborative filtering[C]. Proceedings of the 26th International Conference on World Wide Web. Perth, 2017. 173-182

[3] Koren Y, Bell R, Volinsky C. Matrix factorization techniques for recommender systems[J]. Computer, 2009, 42(8): 30-37

[4] Harper F M, Konstan J A. The MovieLens datasets: History and context[J]. ACM Transactions on Interactive Intelligent Systems (TiiS), 2015, 5(4): 1-19

[5] Ricci F, Rokach L, Shapira B. Recommender Systems Handbook[M]. New York: Springer, 2015. 1-34

[6] Rendle S, Freudenthaler C, Gantner Z, et al. BPR: Bayesian personalized ranking from implicit feedback[C]. Proceedings of the 25th Conference on Uncertainty in Artificial Intelligence. Montreal, 2009. 452-461

[7] Wang X, He X, Wang M, et al. Neural graph collaborative filtering[C]. Proceedings of the 42nd International ACM SIGIR Conference on Research and Development in Information Retrieval. Paris, 2019. 165-174

[8] Linden G, Smith B, York J. Amazon.com recommendations: Item-to-item collaborative filtering[J]. IEEE Internet Computing, 2003, 7(1): 76-80

[9] Cheng H T, Koc L, Harmsen J, et al. Wide & deep learning for recommender systems[C]. Proceedings of the 1st Workshop on Deep Learning for Recommender Systems. Boston, 2016. 7-10

[10] Guo H, Tang R, Ye Y, et al. DeepFM: A factorization-machine based neural network for CTR prediction[C]. Proceedings of the 26th International Joint Conference on Artificial Intelligence. Melbourne, 2017. 1725-1731
