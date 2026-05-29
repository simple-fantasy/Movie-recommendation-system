# Composer Handoff Package

**生成时间**: 2026-05-26
**来源**: academic-paper-strategist 完整工作流
**审计基础**: 3份审计报告 + 2份实验审稿 + 101条证据映射 + ablation_results.json

---

## 1. 最终论文结构

| 章节 | 决策 | 证据完整度 | 需要操作 |
|------|------|:--------:|---------|
| 摘要 | KEEP + 微调 | 85% | 更新实验结论 |
| 第1章 绪论 | KEEP + 微调 | 80% | 更新创新点NCF参数 |
| 第2章 相关技术 | KEEP + 补充 | 90% | 新增 2.6 LightGCN/EASE原理 |
| 第3章 需求分析 | KEEP | 85% | 删除表3-1重复标题 |
| 第4章 系统设计 | KEEP + 精简 | 80% | 精简4.3接口设计 |
| 第5章 算法实现 | REWRITE 5.3 | 70% | 替换全部NCF参数 |
| 第6章 实验分析 | REWRITE 全章 | 95% | 核心重写 ✅ 已大部分完成 |
| 第7章 系统展示 | REWRITE 全章 | 40% | 23 placeholder→10截图 |
| 第8章 总结展望 | REWRITE 8.2 | 70% | 更新局限性 |
| 参考文献 | KEEP + 修复 | 90% | 补全截断页码 |
| 附录 | REWRITE C | 60% | 更新训练/评估命令 |

---

## 2. 每章写作目标与证据来源

### 第5章 算法实现 — 待编辑段落

| 行号 | 旧文本摘要 | 新文本 | 证据来源 |
|------|----------|--------|---------|
| 22331 | "leave-last-out思想" | "三层时间切分（train/val/test严格隔离）" | `evaluation/splitter.py:8-18` |
| 22684 | "embedding_dim（默认32）" | "embedding_dim（64，ncf_v2.pt实际值）" | `ncf_v2_meta.json config.embedding_dim` |
| 22770 | 训练命令 epochs=10, hidden-dim=128, device=cpu, lr=1e-3 | 训练命令 epochs=20, hidden-dim=256, device=cuda, neg-ratio=4, lr=1e-3 | `ncf_v2_meta.json config` |
| 22855 | "epochs=10表示最大训练轮数" | "epochs=20表示最大训练轮数" | `ncf_v2_meta.json config.epochs` |
| 22901 | "hidden_dim=128" | "hidden_dim=256" | `ncf_v2_meta.json config.hidden_dim` |
| 23115 | "保存到ncf.pt" | "保存到ncf_v2.pt" | `ncf_v2_meta.json` |
| 需要新增 | 无 | NCF验证NDCG@10=0.8148 vs 测试NDCG@10=0.04089的gap分析 | `ncf_v2_meta.json train.best_NDCG@K` |

### 第6章 实验分析 — 已完成编辑确认

| 位置 | 内容 | 状态 |
|------|------|:--:|
| 6.2 评估协议 | 三层时间切分 + C_all=13,304 + full_ranking | ✅ |
| 6.2.2 参数列表 | recall_k=200, candidate_mode=full_ranking | ✅ |
| 6.3 核心结论 | ItemCF全面领先, EASE紧随, DL未超传统方法 | ✅ |
| 6.4.2 实验设置 | 2,000用户, 控制变量法 | ✅ |
| 6.4.3 标题 | "消融实验结果" | ✅ |
| 6.4.3 recall_k | recall_k=50最优, NDCG超纯ItemCF 5.6% | ✅ |
| 6.4.3 per_seed | psl=10最优, NDCG +9.9%, Coverage +28.5% | ✅ |
| 6.4.4 小结 | 两个反直觉发现 + 规律总结 | ✅ |
| 表6-1 标题 | C_all=13K公平协议 | ✅ |
| 表6-2 标题 | 混合推荐消融实验结果 | ✅ |

**待完成**: 表6-1和表6-2的**单元格数据**是否需要更新（当前可能是旧数字）。

### 第8章 总结展望 — 待编辑

| 旧文本关键词 | 新文本 | 证据 |
|-------------|--------|------|
| "NCF采用采样候选池" | 删除——v2.0已统一全量排序 | `evaluation/config.py:13` |
| "三种策略的指标不完全处于同一评估协议下" | "当前已统一为全量排序协议，未来可扩展消融实验规模" | — |
| "尚未充分利用电影类型等内容信息" | 保留（仍有效） | — |

### 附录C — 待编辑

| 行号 | 旧命令 | 新命令 |
|------|--------|--------|
| 35722 | `train_ncf --epochs 10 --hidden-dim 128 --device cpu` | `train_ncf_v2 --embedding-dim 64 --hidden-dim 256 --neg-ratio 4 --epochs 20 --device cuda` |
| 35782 | `evaluate_models --models all --k 10` | `run_evaluation --n-users 10000 --models popularity,random,oracle,itemcf,ncf,hybrid,lightgcn,ease --device cuda` |
| 35782 | `evaluate_models --models all --k 10 --ablation` | `run_ablation --n-users 2000 --recall-k-values 50,100,200,500 --per-seed-values 10,25,50,100` |

---

## 3. 全局搜索替换清单

| 搜索内容 | 替换为 | 范围 | 原因 |
|---------|--------|------|------|
| `leave-last-out` | `三层时间切分 (train/val/test)` | 第5章 | 切分策略已变更 |
| `ncf.pt` | `ncf_v2.pt` | 全文 | 当前模型文件名 |
| `embedding_dim（默认32）` | `embedding_dim（64）` | 第5章 | ncf_v2实际值 |
| `hidden_dim=128` | `hidden_dim=256` | 第5章 | ncf_v2实际值 |
| `epochs=10` (NCF上下文) | `epochs=20` | 第5章, 附录C | ncf_v2实际值 |
| `device=cpu` (NCF训练) | `device=cuda` | 第5章, 附录C | ncf_v2默认设备 |
| `evaluate_models` | `run_evaluation` | 附录C | 旧脚本已DEPRECATED |
| `200,949名训练用户` | `170,279名训练用户` | 全文(如存在) | ncf_v2实际值 |
| `84,432个物品` | `71,307个物品` | 全文(如存在) | ncf_v2实际值 |
| `训练最佳NDCG@10.*0.6954` | `验证集最佳NDCG@10为0.8148` | 第5章 | ncf_v2实际值 |

---

## 4. 图表清单

| 图号 | 文件名 | 状态 | 说明 |
|------|--------|:--:|------|
| 图4-1 | `diagrams/fig4-1-system-architecture-v2.pdf` | ✅ 已生成 | 5层架构, 含评估层+7模型 |
| 图4-2 | `diagrams/fig5-2-recommendation-sequence.pdf` | ✅ 已生成 | 推荐请求时序图 |
| 图5-1 | `diagrams/fig5-1-ncf-gmf-architecture.pdf` | ✅ 已生成 | NCF-GMF架构 (64d/256h) |
| 图5-2 | `diagrams/fig5-2-recommendation-sequence.pdf` | ✅ 已生成 | 推荐时序图 |
| 图6-1 | `diagrams/fig6-1-three-way-split.png` | ✅ 已生成 | 三层时间切分示意图 |
| 图6-2 | `figures/fig_eval_comparison.pdf` | ✅ 已生成 | 7模型对比柱状图 |
| 图6-3 | `figures/fig_coverage.pdf` | ✅ 已生成 | Coverage对比 (EASE 6.5x) |
| 图7-1~10 | 待捕获 | 🔴 缺失 | 系统运行截图 |
| 图6-4 | 旧fig6-4_per_seed | 🔴 删除 | 无数据支撑 |
| 图6-5 | 旧fig6-5_accuracy_diversity | 🔴 删除 | 无数据支撑 |

---

## 5. 截图清单

必须使用 `demo/demo123` 账户和 `admin/admin123` 捕获：

| # | 页面 | 角色 | URL |
|---|------|------|-----|
| 1 | 门户首页 | 访客 | `/portal` |
| 2 | 推荐页 (ItemCF策略) | demo | `/app` |
| 3 | 电影详情+评分 | demo | `/movie/1` |
| 4 | 增强数据看板 | demo | `/app` (Dashboard tab) |
| 5 | 用户画像+洞察 | demo | `/app` (Profile tab) |
| 6 | 收藏管理 | demo | `/collections` |
| 7 | 高级搜索 | demo | `/advanced-search` |
| 8 | 管理后台仪表板 | admin | `/admin/dashboard` |
| 9 | 电影管理列表 | admin | `/admin/movies` |
| 10 | 用户管理 | admin | `/admin/users` |

---

## 6. 高风险AI段落 (需人工降AI味)

以下段落来自旧论文，具有明显AI生成特征（三段式结构、宣传性语言、过度连接词）：

- 第1章 P42-P43: 背景描述中"信息过载""个性化推荐模型""内容分发效率"等术语密度过高
- 第2章 P52-P54: "近年来""显著进展""推动了""典型模型包括"——典型的AI综述风格
- 第5章 P305-P306: "有效提升""得到更充分利用""为后续开展...提供了效率保障"——空洞的工程优化描述
- 第8章 P570-P571: "进一步""更加""更全面的"——三连"更"的AI排比句式

**处理方式**: Humanizer-zh 技能处理 + 人工通读降AI味。

---

## 7. 术语统一表

| 术语 | 统一写法 | 禁止写法 |
|------|---------|---------|
| 三层时间切分 | 三层时间切分 (train/val/test) | leave-last-out, leave-one-out |
| C_all候选集 | C_all (13,304部电影) | 候选池, candidate pool |
| 全量排序 | full_ranking (全量排序) | 采样评估, sampled ranking |
| NCF v2 | NCF (GMF) 或 NCF v2 | NCF (易混淆旧版本) |
| 评估协议 | C_all=13K 协议 / 全量80K 协议 | 公平协议 / 不公平协议 |
| 召回-重排 | 召回-重排 | 召回---重排 |
| 消融实验 | 消融实验 | 参数敏感度分析 |

---

## 8. 推荐重写顺序

```
Step 1: 第6章 — 打包验证 ✅ (已完成大部分编辑)
Step 2: 第5章 — 替换 NCF 参数 (6处文本替换)
Step 3: 第8章 — 更新 8.2 局限性 (2处)
Step 4: 附录C — 更新命令 (3处)
Step 5: 全文搜索替换 (ncf.pt→ncf_v2.pt 等)
Step 6: 第7章 — 替换截图 (需先运行系统)
Step 7: 降AI味处理
Step 8: 补全参考文献
Step 9: 最终打包验证
```

---

## 9. 答辩安全表述 (Grill面试确认)

**可以说的**:
- "在统一候选集C_all的全量排序协议下，ItemCF在排序精度上略优于其他模型"
- "EASE在覆盖率上显著最优 (6.5x)，体现了闭式解对长尾物品的挖掘优势"
- "Hybrid在recall_k=50时超越纯ItemCF约5.6%——消融实验验证了召回-重排架构的有效性"
- "per_seed_limit=10时ItemCF的NDCG和Coverage同时提升——'少即是多'的协同过滤规律"

**不能说的**:
- ~~"NCF在准确率与排序指标上最优"~~
- ~~"显著提升""极大优化""明显优于"~~
- ~~任何未在evaluation_results.json中出现的数字~~
- ~~消融实验中未运行的参数组合~~

---

## 10. 参考文件索引

| 用途 | 路径 |
|------|------|
| 工作稿 (当前) | `thesis/毕业论文.working.docx` |
| 工作稿 (备份) | `thesis/毕业论文.原稿.docx` |
| 解包目录 | `thesis/unpacked/word/document.xml` |
| 审计报告 | `docs/thesis_authenticity_audit_2026-05-26.md` |
| 证据映射 | `docs/thesis_evidence_mapping_2026-05-26.md` |
| 实验审稿 | `docs/experiment_review_report_2026-05-26.md` |
| 重写计划 | `docs/thesis_rewrite_plan_2026-05-26.md` |
| 评估数据 | `backend/artifacts/evaluation_results.json` |
| 消融数据 | `backend/artifacts/ablation_results.json` |
| NCF参数 | `backend/artifacts/ncf_v2_meta.json` |
| 全量评估 | `backend/artifacts/full_ranking_final.json` |
