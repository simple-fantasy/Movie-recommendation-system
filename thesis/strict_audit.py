"""Strict graduation thesis audit against all requirements"""
import zipfile, xml.etree.ElementTree as ET, re, sys

with zipfile.ZipFile('thesis/毕业论文-修改版.docx', 'r') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)

texts = []
for t in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
    if t.text: texts.append(t.text)
full = ''.join(texts)

def cn(s):
    return len(re.findall(r'[一-鿿]', s))

# Split document into sections for detailed analysis
abstract_cn_start = full.find('摘  要')
abstract_cn_end = full.find('ABSTRACT')
abstract_en_start = abstract_cn_end
abstract_en_end = full.find('目录')
body_start = full.find('第1章')
toc_start = full.find('目录')
ack_end = full.find('参考文献')
ref_end = full.find('附录')

issues = []
warnings = []

print('=' * 70)
print('毕业设计论文严格审计')
print('青岛理工大学规范对照')
print('=' * 70)

# ===== 1. 字数要求 =====
print('\n━━━ 一、文字量 ━━━')
cn_count = cn(full)
print(f'  中文字数: {cn_count}')
print(f'  要求: >=10000字')
if cn_count >= 10000:
    print(f'  结论: 满足 ({cn_count - 10000}字超额)')
else:
    issues.append(f'字数不足: {cn_count}/10000')

# ===== 2. 结构完整性 =====
print('\n━━━ 二、结构完整性 ━━━')
required_structure = [
    ('封面', '青岛理工大学'),
    ('原创性声明', '原创性声明'),
    ('任务书', '任务书'),  # required by university
    ('中文摘要', '摘  要'),
    ('英文摘要', 'ABSTRACT'),
    ('目录', '目录'),
    ('前言/第1章', '第1章'),
    ('正文(≥4章)', '第2章'),
    ('结论', '第7章'),
    ('致谢', '致  谢'),
    ('参考文献', '参考文献'),
    ('附录', '附录'),
]
for name, kw in required_structure:
    found = kw in full
    if found:
        print(f'    [OK] {name}')
    else:
        print(f'    [MISSING] {name}')
        issues.append(f'缺少: {name}')

# ===== 3. 摘要检查 =====
print('\n━━━ 三、摘要质量 ━━━')
cn_abstract = full[abstract_cn_start:abstract_cn_end]
en_abstract = full[abstract_en_start:abstract_en_end]

cn_abs_chars = cn(cn_abstract)
cn_kw = re.findall(r'关键词[：:]\s*(.+?)(?:\n|$)', cn_abstract)
en_kw = re.findall(r'KEY WORDS:\s*(.+?)(?:\n|$)', en_abstract)

print(f'  中文摘要: ~{cn_abs_chars}字 (要求300字左右)')
if cn_abs_chars < 250:
    issues.append(f'中文摘要偏短: {cn_abs_chars}字')
elif cn_abs_chars > 500:
    issues.append(f'中文摘要偏长: {cn_abs_chars}字')
else:
    print(f'  中文摘要长度: 合适')

if cn_kw:
    kws = [k.strip() for k in cn_kw[0].replace('，', ',').split(',')]
    print(f'  中文关键词: {len(kws)}个 - {kws}')
    if len(kws) < 3:
        issues.append(f'关键词不足3个')
    elif len(kws) > 5:
        warnings.append(f'关键词超过5个')

if en_kw:
    kws_en = [k.strip() for k in en_kw[0].split(',')]
    print(f'  英文关键词: {len(kws_en)}个 - {kws_en}')

# ===== 4. 格式规范 =====
print('\n━━━ 四、排版格式 ━━━')
fmt_checks = [
    ('章节编号体系(1/1.1/1.1.1)', '1.1.1' in full),
    ('各章有独立标题', '第1章' in full and '第2章' in full),
    ('公式编号存在', '(2-1)' in full),
    ('表格有表序表题', '表6-1' in full),
    ('参考文献编号[1][2]格式', '[1]' in full),
]
for name, ok in fmt_checks:
    print(f'    [{"OK" if ok else "FAIL"}] {name}')
    if not ok:
        issues.append(name)

# ===== 5. 参考文献 =====
print('\n━━━ 五、参考文献 ━━━')
ref_section_start = full.find('参考文献')
ref_section = full[ref_section_start:full.find('附录')] if '附录' in full else full[ref_section_start:]
body_text = full[:ref_section_start]

ref_nums_in_list = set()
for m in re.finditer(r'\[(\d+)\]', ref_section):
    ref_nums_in_list.add(int(m.group(1)))

ref_nums_in_text = set()
for m in re.finditer(r'\[(\d+)\]', body_text):
    ref_nums_in_text.add(int(m.group(1)))

print(f'  参考文献列表: {sorted(ref_nums_in_list)} ({len(ref_nums_in_list)}篇)')
print(f'  正文引用: {sorted(ref_nums_in_text)} ({len(ref_nums_in_text)}篇)')
if len(ref_nums_in_list) >= 8:
    print(f'  [OK] 数量满足(>=8)')
else:
    issues.append(f'参考文献不足8篇: {len(ref_nums_in_list)}')

uncited = ref_nums_in_list - ref_nums_in_text
if uncited:
    issues.append(f'文献{uncited}在列表但正文未引用')

cited_not_listed = ref_nums_in_text - ref_nums_in_list
if cited_not_listed:
    issues.append(f'文献{cited_not_listed}在正文引用但不在列表')

# Count foreign refs
foreign_count = 0
for n in ref_nums_in_list:
    # Find this reference text
    pattern = f'[{n}]'
    idx = ref_section.find(pattern)
    if idx >= 0:
        ref_text = ref_section[idx:idx+300]
        if any(c.isascii() and c.isalpha() for c in ref_text[:50]) and not any('一' <= c <= '鿿' for c in ref_text[:30]):
            foreign_count += 1
print(f'  外文文献: >= {foreign_count}篇 (要求>=2)')
if foreign_count < 2:
    issues.append(f'外文文献不足2篇')

# ===== 6. 内容一致性 =====
print('\n━━━ 六、内容一致性 ━━━')

# NCF params
ncf_10 = full.count('--epochs 10') + full.count('epochs=10')
ncf_20 = full.count('--epochs 20') + full.count('epochs=20')
ncf_4096 = full.count('batch-size 4096') + full.count('batch_size=4096')
ncf_8192 = full.count('batch-size 8192') + full.count('batch_size=8192')
ncf_cpu = full.count('device cpu') + full.count('device=cpu')
ncf_cuda = full.count('device cuda') + full.count('device=cuda')

if ncf_20 > 0:
    issues.append(f'NCF训练epochs不一致: 有{ncf_20}处仍写epochs=20(应为10)')
if ncf_8192 > 0:
    issues.append(f'NCF训练batch不一致: 有{ncf_8192}处仍写batch=8192(应为4096)')
if ncf_cuda > 0:
    warnings.append(f'NCF device仍有cuda引用({ncf_cuda}处)，与当前CPU训练不一致')

print(f'  NCF epochs: {ncf_10}处10, {ncf_20}处20')
print(f'  NCF batch: {ncf_4096}处4096, {ncf_8192}处8192')
print(f'  NCF device: {ncf_cpu}处cpu, {ncf_cuda}处cuda')

# Old eval data
old_nums = re.findall(r'(0\.01079|0\.10793|0\.00085|0\.00845|0\.00489|0\.04893|0\.04000|0\.05563)', full)
if old_nums:
    issues.append(f'表6-1/6-2仍有{len(old_nums)}处旧评估数据(需重新实验)')
    print(f'  [ISSUE] {len(old_nums)}处旧评估数据')

# Python version
py_vers = set(re.findall(r'Python\s*(\d+\.\d+)', full))
print(f'  Python版本引用: {py_vers}')
if '3.13' in str(py_vers):
    issues.append('Python版本3.13与实际3.10不一致')

# GPU optimization section
gpu_old = full.count('GPU训练优化') + full.count('RTX 3050')
print(f'  GPU优化旧引用: {gpu_old}处')

# import_movielens residue
if 'import_movielens' in full:
    issues.append('仍有import_movielens旧引用')
    print(f'  [ISSUE] import_movielens残留')

# ===== 7. 图表检查 =====
print('\n━━━ 七、图表与可视化 ━━━')
table_count = len(re.findall(r'表\d+-\d+', full))
fig_count = len(re.findall(r'图\d+-\d+', full))
print(f'  表格引用: {table_count}个')
print(f'  插图引用: {fig_count}个')
if fig_count == 0:
    issues.append('论文中无任何插图引用(需架构图/ER图/截图)')
if table_count < 2:
    issues.append('表格数量不足')

# ===== 8. 章节均衡性 =====
print('\n━━━ 八、章节内容均衡性 ━━━')
chapters_info = [
    ('第1章 绪论', '第2章 相关技术与理论'),
    ('第2章 相关技术与理论', '第3章 系统需求分析'),
    ('第3章 系统需求分析', '第4章 系统总体设计'),
    ('第4章 系统总体设计', '第5章 推荐算法设计与实现'),
    ('第5章 推荐算法与系统实现', '第6章 实验设计与结果分析'),
    ('第6章 实验设计与结果分析', '第7章 总结与展望'),
    ('第7章 总结与展望', '第8章 系统使用指南'),
    ('第8章 系统使用指南', '致  谢'),
]

for ch, next_ch in chapters_info:
    s = full.find(ch)
    e = full.find(next_ch) if full.find(next_ch) > s else len(full)
    if s >= 0 and e > s:
        section_text = full[s:e]
        count = cn(section_text)
        bar = '#' * max(count // 200, 1)
        flag = ''
        if count < 800:
            flag = ' [薄]'
            warnings.append(f'{ch}字数偏少({count}字)')
        if count > 5000:
            flag = ' [厚]'
            warnings.append(f'{ch}字数偏多({count}字)')
        print(f'  {ch}: {count}字 {bar}{flag}')

# ===== 9. 功能覆盖 =====
print('\n━━━ 九、系统功能覆盖 ━━━')
feature_coverage = [
    ('用户注册登录', '注册' in full and '登录' in full),
    ('密码加密存储', '哈希' in full or 'hash' in full.lower()),
    ('管理员权限', 'admin' in full.lower() or '管理员' in full),
    ('电影搜索浏览', '搜索' in full and ('电影' in full or 'movie' in full.lower())),
    ('电影评分(0.5-5.0)', '0.5' in full and '5.0' in full),
    ('三种推荐策略', 'itemcf' in full.lower() and 'ncf' in full.lower() and 'hybrid' in full.lower()),
    ('推荐解释(because)', '推荐理由' in full or 'because' in full.lower()),
    ('推荐反馈', '反馈' in full or 'feedback' in full.lower()),
    ('用户画像(12维)', '用户画像' in full and '12' in full),
    ('行为追踪', '行为追踪' in full),
    ('观影洞察', '洞察' in full),
    ('电影收藏(3类型)', 'favorite' in full.lower() or '收藏' in full),
    ('影评功能', '评论' in full or 'review' in full.lower()),
    ('影单功能', '影单' in full),
    ('通知系统', '通知' in full),
    ('数据看板', '看板' in full or 'dashboard' in full.lower()),
    ('管理后台', '管理后台' in full or 'admin' in full.lower()),
    ('数据导出', '导出' in full or 'export' in full.lower()),
    ('TMDB元数据补充', 'TMDB' in full),
    ('优雅降级', '降级' in full or 'fallback' in full.lower()),
    ('冷启动处理', '冷启动' in full),
    ('离线评估(5指标)', 'Precision' in full and 'NDCG' in full and 'MRR' in full),
    ('消融实验', '消融' in full),
    ('用户使用指南', '使用指南' in full),
]

covered = sum(1 for _, ok in feature_coverage if ok)
total = len(feature_coverage)
print(f'  覆盖率: {covered}/{total}')
for name, ok in feature_coverage:
    if not ok:
        print(f'    [MISSING] {name}')
        warnings.append(f'论文未提及: {name}')

# ===== 10. 附录完整性 =====
print('\n━━━ 十、附录完整性 ━━━')
appendix_checks = [
    ('附录A 数据库表结构', '附录A' in full),
    ('附录B API接口清单', '附录B' in full),
    ('附录C 训练评估命令', '附录C' in full),
]
for name, ok in appendix_checks:
    print(f'    [{"OK" if ok else "MISSING"}] {name}')
    if not ok:
        issues.append(f'缺少{name}')

# ===== FINAL REPORT =====
print()
print('=' * 70)
print('审计结论')
print('=' * 70)

# Categorize issues
critical = [i for i in issues if any(kw in i for kw in ['评估数据', '缺少', '不足', '不一致', '残留'])]
important = [i for i in issues if not any(kw in i for kw in ['评估数据', '缺少', '不足', '不一致', '残留'])]

print(f'\n🔴 必须修复 ({len(issues)}项):')
for i in issues:
    print(f'  ✗ {i}')

if warnings:
    print(f'\n🟡 建议优化 ({len(warnings)}项):')
    for w in warnings:
        print(f'  ⚠ {w}')

print(f'\n总计:')
print(f'  - 必须修复: {len(issues)}项')
print(f'  - 建议优化: {len(warnings)}项')
print(f'  - 字数达标: {cn_count}字')
print(f'  - 功能覆盖: {covered}/{total}')
print(f'  - 参考文献: {len(ref_nums_in_list)}篇(外文~{foreign_count}篇)')
print(f'  - 表格: {table_count}个, 插图: {fig_count}个')
