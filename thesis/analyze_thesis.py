"""Deep analysis of thesis quality"""
import zipfile, xml.etree.ElementTree as ET, re

with zipfile.ZipFile('thesis/毕业论文-修改版.docx', 'r') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)

texts = []
for t in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
    if t.text:
        texts.append(t.text)
full = ''.join(texts)
cn = lambda s: len(re.findall(r'[一-鿿]', s))

print('=' * 60)
print('论文全面质量分析报告')
print('=' * 60)

# === 1. 字数统计 ===
cn_chars = cn(full)
print(f'\n【1. 字数统计】')
print(f'  中文字符数: {cn_chars}')
print(f'  要求: >=10000字')
print(f'  结论: {"✓ 满足" if cn_chars >= 10000 else "✗ 不足! 差" + str(10000-cn_chars) + "字"}')

# === 2. 结构完整性 ===
print(f'\n【2. 结构完整性】')
required = [
    '原创性声明', '摘  要', 'ABSTRACT', '目录',
    '第1章', '第2章', '第3章', '第4章', '第5章', '第6章', '第7章',
    '致  谢', '参考文献', '附录'
]
for item in required:
    # Handle items with spaces like "摘  要", "致  谢"
    search = item.replace('  ', ' ')
    found = search in full or item.replace('  ', '') in full
    status = '✓' if found else '✗ 缺失!'
    print(f'  {status}: {item}')

# === 3. 参考文献检查 ===
print(f'\n【3. 参考文献】')
ref_nums = sorted(set(int(n) for n in re.findall(r'\[(\d+)\]', full)))
print(f'  引用编号: {ref_nums}')
print(f'  文献总数: {len(ref_nums)} (要求>=8)')
# Check foreign refs
foreign_titles = ['Sarwar', 'Koren', 'He X', 'Harper', 'Ricci', 'Rendle', 'Wang X', 'Linden', 'Cheng H', 'Guo H']
foreign_count = sum(1 for t in foreign_titles if t in full)
print(f'  外文文献: ~{foreign_count} 篇 (要求>=2)')
print(f'  结论: {"✓ 满足" if len(ref_nums) >= 8 and foreign_count >= 2 else "✗ 不足"}')

# === 4. 数据库表覆盖 ===
print(f'\n【4. 数据库设计完整性】')
all_tables = ['users','movies','ratings','movie_similarity','recommendation_feedback',
    'reviews','review_likes','user_collections','watch_links',
    'notifications','user_notification_preferences','movie_charts','chart_items',
    'user_behaviors','user_profiles',
    'movie_lists','movie_list_items','movie_list_likes','movie_list_comments']
mentioned = {t for t in all_tables if t.lower() in full.lower()}
missing = set(all_tables) - mentioned
print(f'  已提及: {len(mentioned)}/19 张表')
if missing:
    print(f'  未提及: {sorted(missing)}')
print(f'  结论: {"✓ 全面" if len(mentioned) >= 14 else "⚠ 仅" + str(len(mentioned)) + "张, 缺" + str(len(missing)) + "张"}')

# === 5. 旧数据检查 ===
print(f'\n【5. 实验数据状态】')
old_data = re.findall(r'0\.\d{4,6}', full)
if old_data:
    print(f'  ⚠ 检测到 {len(old_data)} 处精确小数 (可能是旧的评估结果)')
    print(f'  示例: {old_data[:8]}')
    print(f'  → 需要运行 evaluate_models.py 获取新数据后填入表6-1/6-2')

# === 6. 关键命令更新检查 ===
print(f'\n【6. 训练命令更新状态】')
checks = [
    ('import_fast.py 替代 import_movielens', 'import_fast' in full, 'import_movielens' not in full),
    ('ItemCF 添加 normalize 参数', '--normalize' in full, True),
    ('ItemCF 添加过滤参数', '--min-ratings-per-movie' in full, True),
    ('NCF epochs: 20→10', '--epochs 10' in full, '--epochs 20' not in full),
    ('NCF batch: 8192→4096', '--batch-size 4096' in full, True),
    ('NCF device: cuda→cpu', '--device cpu' in full, True),
    ('GPU优化改为通用优化', 'CPU' in full, True),
]
for desc, ok, _ in checks:
    print(f'  {"✓" if ok else "✗"}: {desc}')

# === 7. 图表检查 ===
print(f'\n【7. 图表与公式】')
has_table = '表6-1' in full or '表6' in full
has_figure = '图' in full and ('架构' in full or '流' in full)
has_formula = '余弦' in full and '相似度' in full
print(f'  {"✓" if has_table else "✗"}: 有数据表格')
print(f'  {"✓" if has_figure else "⚠"}: 有架构/流程图描述 (建议添加实际图片)')
print(f'  {"✓" if has_formula else "✗"}: 有数学公式描述')

# === 8. 创新点检查 ===
print(f'\n【8. 功能覆盖度】')
features = {
    'ItemCF推荐': 'ItemCF' in full,
    'NCF推荐': 'NCF' in full,
    'Hybrid混合': 'Hybrid' in full or ('混合' in full and '推荐' in full),
    '推荐解释(because)': '推荐理由' in full or 'because' in full.lower(),
    '用户画像(12维)': '用户画像' in full and '12' in full,
    '行为追踪': '行为追踪' in full,
    '评分功能': '评分' in full and 'rating' in full.lower(),
    '收藏功能(favorite等)': '收藏' in full or 'favorite' in full.lower(),
    '影单功能': '影单' in full,
    '评论功能': '评论' in full or 'review' in full.lower(),
    '通知系统': '通知' in full,
    '管理后台': '管理后台' in full or 'admin' in full.lower(),
    '数据看板(ECharts)': 'ECharts' in full,
    'TMDB元数据补充': 'TMDB' in full,
    '推荐反馈': '反馈' in full or 'feedback' in full.lower(),
    '数据导出': '导出' in full or 'export' in full.lower(),
    '优雅降级': '降级' in full or '回退' in full or 'fallback' in full.lower(),
    '碰撞检测负采样': '碰撞' in full,
    '早停机制': '早停' in full,
    '用户均值归一化': '归一化' in full,
}
for feat, ok in features.items():
    print(f'  {"✓" if ok else "✗ 缺失"}: {feat}')

# === 9. 章节内容深度 ===
print(f'\n【9. 章节内容深度（字数）】')
chapters_list = [
    ('第1章 绪论', '第2章'),
    ('第2章 相关技术与理论', '第3章'),
    ('第3章 系统需求分析', '第4章'),
    ('第4章 系统总体设计', '第5章'),
    ('第5章 推荐算法设计与实现', '第6章'),
    ('第6章 实验设计与结果分析', '第7章'),
    ('第7章 总结与展望', '致  谢'),
]
for ch, next_ch in chapters_list:
    s = full.find(ch)
    if s < 0:
        print(f'  ✗ 未找到: {ch}')
        continue
    e = full.find(next_ch, s + len(ch))
    if e < 0:
        e = len(full)
    section_text = full[s:e]
    count = cn(section_text)
    bar = '█' * min(count // 200, 30)
    print(f'  {ch}: {count}字 {bar}')

print()
print('=' * 60)
print('总结')
print('=' * 60)
