# evaluate_verify.py
"""离线评估验证脚本 - 验证评估结果"""
import json
from pathlib import Path
from backend.app import create_app, db
from backend.app.models import MovieSimilarity

def main():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("离线评估验证报告")
        print("=" * 60)
        
        # 评估结果文件
        artifacts = Path(__file__).resolve().parents[1] / "artifacts"
        result_path = artifacts / "evaluation_results.json"
        
        print("\n📁 结果文件检查：")
        if not result_path.exists():
            print(f"  ✗ evaluation_results.json 不存在")
            print(f"\n请先运行: python -m backend.scripts.evaluate_models --models all")
            return False
        
        print(f"  ✓ evaluation_results.json 存在")
        
        # 读取评估结果
        with open(result_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # 验证JSON结构
        print("\n📋 评估配置：")
        config = results.get('config', {})
        print(f"  K: {config.get('k', 'N/A')}")
        print(f"  like_threshold: {config.get('like_threshold', 'N/A')}")
        print(f"  min_ratings: {config.get('min_ratings', 'N/A')}")
        print(f"  recall_k: {config.get('recall_k', 'N/A')}")
        
        # 验证结果
        eval_results = results.get('results', [])
        print(f"\n📊 评估结果 ({len(eval_results)} 组)：")
        
        required_models = ['itemcf', 'ncf', 'hybrid']
        found_models = set()
        
        print("\n" + "-" * 100)
        print(f"{'Model':<12} {'P@K':<10} {'R@K':<10} {'MAP@K':<10} {'NDCG@K':<10} {'MRR@K':<10} {'Coverage':<10}")
        print("-" * 100)
        
        all_valid = True
        for r in eval_results:
            model = r.get('model', 'unknown')
            found_models.add(model)
            
            p = r.get('precision_at_k', 0)
            rec = r.get('recall_at_k', 0)
            m = r.get('map_at_k', 0)
            n = r.get('ndcg_at_k', 0)
            mr = r.get('mrr_at_k', 0)
            cov = r.get('coverage', 0)
            
            # 验证指标范围
            valid = 0 <= p <= 1 and 0 <= rec <= 1 and 0 <= m <= 1 and 0 <= n <= 1
            if not valid:
                all_valid = False
            
            # 检查NaN
            has_nan = any(x != x for x in [p, rec, m, n, mr])
            if has_nan:
                all_valid = False
            
            status = "✓" if valid and not has_nan else "✗"
            print(f"{model:<12} {p:<10.4f} {rec:<10.4f} {m:<10.4f} {n:<10.4f} {mr:<10.4f} {cov:<10.4f} {status}")
        
        print("-" * 100)
        
        # 检查必需模型
        print("\n✅ 模型检查：")
        for model in required_models:
            if model in found_models:
                print(f"  ✓ {model}")
            else:
                print(f"  ✗ {model} 缺失")
                all_valid = False
        
        # 指标范围验证
        print("\n📈 指标范围验证：")
        print("  所有指标应在 [0, 1] 范围内")
        print(f"  验证结果: {'✓ 通过' if all_valid else '✗ 失败'}")
        
        print("\n" + "=" * 60)
        return all_valid

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)