# train_itemcf_verify.py
"""ItemCF训练验证脚本 - 验证ItemCF算法训练结果"""
import time
from backend.app import create_app, db
from backend.app.models import MovieSimilarity
from sqlalchemy import func

def main():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("ItemCF训练验证报告")
        print("=" * 60)
        
        # 检查相似度表
        similarity_count = MovieSimilarity.query.count()
        
        print(f"\n📊 相似度统计：")
        print(f"  相似度记录数: {similarity_count}")
        
        if similarity_count == 0:
            print("\n❌ 验证失败: 相似度表为空，请先运行训练")
            return False
        
        # 相似度分数范围
        min_sim = db.session.query(func.min(MovieSimilarity.score)).scalar()
        max_sim = db.session.query(func.max(MovieSimilarity.score)).scalar()
        avg_sim = db.session.query(func.avg(MovieSimilarity.score)).scalar()
        
        print(f"\n📈 相似度分数分析：")
        print(f"  最小值: {min_sim:.6f}")
        print(f"  最大值: {max_sim:.6f}")
        print(f"  平均值: {avg_sim:.6f}")
        
        # 验证分数范围
        score_range_ok = 0.0 <= min_sim <= max_sim <= 1.0
        print(f"\n✅ 分数范围验证: {'✓ 通过 (0~1之间)' if score_range_ok else '✗ 失败'}")
        
        # 每部电影的相似电影数量
        per_movie_stats = db.session.query(
            MovieSimilarity.movie_id,
            func.count(MovieSimilarity.id).label('cnt')
        ).group_by(MovieSimilarity.movie_id).all()
        
        if per_movie_stats:
            counts = [s.cnt for s in per_movie_stats]
            print(f"\n📋 每部电影相似电影数量统计：")
            print(f"  电影总数: {len(counts)}")
            print(f"  平均相似电影数: {sum(counts)/len(counts):.1f}")
            print(f"  最少: {min(counts)}, 最多: {max(counts)}")
        
        # 相似度分布
        bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        print(f"\n📊 相似度分布：")
        for i in range(len(bins)-1):
            count = MovieSimilarity.query.filter(
                MovieSimilarity.score >= bins[i],
                MovieSimilarity.score < bins[i+1]
            ).count()
            pct = count / similarity_count * 100
            print(f"  [{bins[i]:.1f}~{bins[i+1]:.1f}): {count} ({pct:.1f}%)")
        
        # 高相似度对
        high_sim = MovieSimilarity.query.filter(MovieSimilarity.score >= 0.8).count()
        print(f"\n🎯 高相似度对 (≥0.8): {high_sim} ({high_sim/similarity_count*100:.1f}%)")
        
        print("\n" + "=" * 60)
        return score_range_ok and similarity_count > 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)