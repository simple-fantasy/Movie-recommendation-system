# Handoff: 论文全面审计完成 — 进入修复阶段

**时间**: 2026-05-26 17:10
**状态**: ready_for_repair — 审计阶段完成，6项CRITICAL待修复
**关联**: 论文题目《融合协同过滤与深度学习的电影推荐系统设计与实现》

---

## 目标

确保论文与真实代码/实验完全一致，达到本科毕设答辩标准。

---

## 已完成（本次会话产出）

### 审计文档（4份）

| 文档 | 路径 | 内容 |
|------|------|------|
| **论文可信性审计报告** | `docs/thesis_authenticity_audit_2026-05-26.md` | 6 CRITICAL + 6 HIGH + 6 MEDIUM + 6 LOW 问题分级 |
| **论文-代码证据映射系统** | `docs/thesis_evidence_mapping_2026-05-26.md` | 101条主张→证据映射 + Keep/Rewrite/Delete矩阵 + 各章节真实性评分 |
| **推荐系统实验审稿报告** | `docs/experiment_review_report_2026-05-26.md` | 评估协议审计 + 指标验证 + 公平性审计 + 论文安全表述指南 |
| **模型评估成果包** | `docs/模型评估成果包.md` | 7模型×2协议评估结果汇总（用户提供的参考文档） |

### 关键发现

1. **实验结论反转**：论文声称"NCF最优"，但当前v2.0公平协议下 **ItemCF > NCF > LightGCN**
2. **论文描述的是旧NCF模型**：参数全部过时（embedding_dim=32→64, hidden_dim=128→256, num_users=200949→170279等）
3. **论文实验数据不可复现**：表6-1数字无法在任何当前JSON中找到，来自已DEPRECATED的旧evaluator.py
4. **消融实验无实际数据**：6.4节仅有设计描述
5. **23张截图全部placeholder**
6. **Hybrid在最新评估中缺失**
7. **实验框架本身设计合理**：三层时间切分零泄露，全量排序公平，Sanity Check通过，评级B+

---

## 当前在进行

审计阶段已完成。下一个session应从**修复P0问题**开始。

---

## 待完成（按优先级）

### Phase 1: 数据修复

- [ ] **P0-1**: 重跑含Hybrid的完整Phase 2评估
  ```bash
  python -m backend.scripts.run_evaluation \
      --n-users 10000 \
      --models popularity,random,oracle,itemcf,ncf,hybrid,lightgcn,ease \
      --device cuda
  ```
- [ ] **P0-2**: 决定LightGCN/EASE是否纳入论文（建议：纳入，作为扩展对比）

### Phase 2: 论文重写

- [ ] **P0-3**: 重写第5章5.3节 — 全部NCF参数替换为ncf_v2实际值
- [ ] **P0-4**: 重写第6章全章 — 使用evaluation_results.json实际数据，更正结论
- [ ] **P0-5**: 重写/删除6.4节消融实验（无实际数据）
- [ ] **P0-6**: 更新8.2节展望（旧局限性已修复）
- [ ] **P1-1**: 捕获8-10张系统截图替代23张placeholder
- [ ] **P1-2**: 更新附录C训练/评估命令

### Phase 3: 格式修复

- [ ] 全文标题字体修复（宋体→黑体）
- [ ] 参考文献补全截断页码
- [ ] 删除重复内容（表3-1、附录D/第7章重叠）
- [ ] 全文旧参数搜索替换（200949→170279, 84432→71307）

---

## 关键发现/决策

### 论文与代码之间的差距 = 两个大版本迭代

| 维度 | 论文描述 | 当前代码 |
|------|---------|---------|
| NCF模型 | ncf.pt (32/128/neg1/10epoch) | ncf_v2.pt (64/256/neg4/20epoch) |
| 评估协议 | evaluator.py fair_mode (1000候选池) | evaluation/engine.py full_ranking (全量排序) |
| 模型数量 | 3 (ItemCF/NCF/Hybrid) | 7 (含LightGCN/EASE/Popularity/Random) |
| 实验数据 | 来自旧evaluator.py（已覆盖） | evaluation_results.json / full_ranking_final.json |

### 两条评估管线的关系

| | C_all=13K协议（新） | 全量80K协议（旧引擎） |
|------|------|------|
| 用途 | **论文主要数据来源** | 辅助参考 |
| 公平性 | 统一候选池 ✅ | 各模型候选集不完全一致 ⚠️ |
| 切分 | 三层时间切分 ✅ | 二层切分 |
| 统计检验 | 缺失 | 有Wilcoxon+Cohen's d |
| 引擎状态 | 当前主力 | DEPRECATED |

### 论文叙事调整方向

- **不要**强行宣称某个模型"最优"
- **应该**客观报告各模型在不同维度上的表现差异
- **诚实讨论**为什么深度学习方法在MovieLens上未超越传统方法
- **强调**评估协议的严格性和公平性

---

## 关键文件

### 代码（评估模块）
- `backend/evaluation/engine.py` — 主评估引擎，7模型支持
- `backend/evaluation/metrics.py` — 8个指标实现（已验证正确）
- `backend/evaluation/splitter.py` — 三层时间切分（零泄露）
- `backend/evaluation/config.py` — EvalProtocolConfig（单一配置来源）
- `backend/evaluation/ncf_inference.py` — NCF推理（batched_rank）
- `backend/evaluation/checks.py` — Sanity Check + Invariants
- `backend/scripts/run_evaluation.py` — 新协议CLI入口
- `backend/scripts/train_ncf_v2.py` — NCF重训脚本（三层切分）

### 数据（实验产物）
- `backend/artifacts/evaluation_results.json` — **论文新数据来源**（C_all协议 Phase 2）
- `backend/artifacts/evaluation_results.phase1.json` — Phase 1 验证
- `backend/artifacts/full_ranking_final.json` — 全量80K协议（旧引擎）
- `backend/artifacts/ncf_v2_meta.json` — NCF v2 实际参数（64/256/neg4/20epoch/NDCG@val=0.8148）
- `backend/artifacts/ncf_meta.json` — 旧NCF参数（32/128/neg1/10epoch/NDCG@val=0.6954）**已废弃**

### 图表
- `thesis/figures/fig6-1.py` — 存在但数据硬编码，需改为读取JSON
- `thesis/figures/fig6-2.py` — 同上
- `thesis/figures/fig6-3.py` — 同上
- `diagrams/fig4-1-architecture.drawio` — 架构图源文件
- `diagrams/fig4-2-er-diagram.drawio` — ER图源文件（v2精修版）

### 论文
- `thesis/毕业论文——working.docx` — 当前工作稿（616段，8章+3附录）
- `thesis/_scan_text.txt` — 论文全文提取文本（用于审计）
- `thesis_rules.md` — 论文写作规则（11条）

---

## 未解决的问题

1. **Hybrid的实际效果**：当前无数据，需要重跑评估后才知道
2. **LightGCN/EASE是否纳入论文**：建议纳入，但需要补充模型原理描述（第2章+第6章）
3. **消融实验**：时间是否够运行？如果不够，6.4节应删除
4. **ncf_v2实际训练命令行参数**：meta.json中显示(64/256/4/20epoch)，但train_ncf_v2.py默认值是(32/128/1/10epoch)——实际使用的命令行参数未记录
5. **论文图6-4和6-5无生成脚本**：是保留旧图还是重绘？

---

## 相关上下文

- `thesis_rules.md` — 11条论文规则（禁止夸大、禁止虚构实验等）
- `docs/论文完善Prompt手册.md` — 论文修改Prompt参考
- `docs/evaluation_protocol_design.md` — 评估协议v2.0设计文档（含Grill面试决策）
- `docs/evaluation_audit_report.md` — 早期评估审计（发现ItemCF/NCF不公平对比）
- `docs/implementation_plan.md` — 评估模块实施计划

---

## 给下一个Session的第一句话

> "论文审计已完成，发现6项CRITICAL问题。最致命的是：论文实验数据全部来自已废弃的旧评估协议，且结论'NCF最优'与当前v2.0协议数据矛盾（实际ItemCF > NCF）。请从重跑含Hybrid的完整Phase 2评估开始，然后重写第5章NCF参数和第6章实验数据。所有审计文档在docs/目录下。"
