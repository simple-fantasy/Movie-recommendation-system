# 中文摘要

**摘要**

随着互联网信息爆炸式增长，用户面临着日益严重的"信息过载"问题，个性化推荐系统成为解决这一问题的核心技术。本课题以MovieLens 32M大规模电影评分数据集为基础，设计并实现了一个融合多种推荐策略的电影推荐系统CineMatch。

本系统采用Flask框架搭建Web后端，基于SQLAlchemy ORM管理MySQL数据库（共19张数据表），前端使用Jinja2模板与Vue.js 3混合架构实现服务端渲染与客户端交互的结合。在推荐算法层面，系统实现了三种推荐策略：基于物品协同过滤（ItemCF）采用scikit-learn最近邻搜索进行余弦相似度预计算，并支持可解释推荐理由生成；神经协同过滤（NCF）基于PyTorch实现GMF架构的神经网络模型，通过异步加载和单例模式进行高效推理；混合推荐（Hybrid）创新性地采用ItemCF召回+NCF重排的级联架构，在保证推荐精度的同时兼顾可解释性。

系统还实现了用户画像分析（12维特征）、用户行为追踪、推荐反馈收集、影单社交、数据可视化看板（ECharts）和管理后台等完整功能模块。通过统一的离线评估框架（Leave-Last-Out协议），使用Precision@K、Recall@K、MAP@K、NDCG@K和MRR@K五项指标对三种推荐策略进行了对比评估，并通过消融实验分析了关键参数的影响。

关键词：电影推荐系统，协同过滤，神经协同过滤，混合推荐，可解释推荐

---

# 英文摘要

**ABSTRACT**

With the explosive growth of Internet information, users face an increasingly severe "information overload" problem, making personalized recommendation systems a core technology to address this challenge. This project designs and implements a movie recommendation system named CineMatch, integrating multiple recommendation strategies based on the MovieLens 32M large-scale rating dataset.

The system employs the Flask framework for the web backend, manages a MySQL database (19 tables) through SQLAlchemy ORM, and uses a hybrid frontend architecture combining Jinja2 templates with Vue.js 3 for server-side rendering and client-side interaction. At the recommendation algorithm level, three strategies are implemented: Item-based Collaborative Filtering (ItemCF) uses scikit-learn nearest neighbor search for precomputed cosine similarity with explainable recommendation reasons; Neural Collaborative Filtering (NCF) implements a GMF-architecture neural network based on PyTorch with async loading and singleton pattern for efficient inference; the Hybrid strategy innovatively adopts a cascade architecture with ItemCF recall followed by NCF reranking, balancing recommendation accuracy with interpretability.

The system also implements comprehensive functional modules including user profiling (12-dimensional features), user behavior tracking, recommendation feedback collection, movie list social features, data visualization dashboards (ECharts), and an admin panel. Through a unified offline evaluation framework (Leave-Last-Out protocol), five metrics—Precision@K, Recall@K, MAP@K, NDCG@K, and MRR@K—are used to comparatively evaluate the three strategies, with ablation studies analyzing the impact of key parameters.

KEY WORDS: movie recommendation system, collaborative filtering, neural collaborative filtering, hybrid recommendation, explainable recommendation
