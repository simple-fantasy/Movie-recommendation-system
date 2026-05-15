# diagnose_ncf.py - NCF诊断脚本
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app import create_app
from backend.app.ncf_engine import ncf_engine

def main():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("NCF引擎诊断")
        print("=" * 60)
        
        loaded = ncf_engine.load()
        print(f"\n✓ 引擎加载: {'成功' if loaded else '失败'}")
        
        if loaded:
            print(f"\n模型信息:")
            print(f"  用户数: {ncf_engine.num_users}")
            print(f"  电影数: {ncf_engine.num_items}")
            
            # 测试推理
            test_items = [1, 2, 3, 4, 5]
            scores = ncf_engine.score(1, test_items)
            print(f"\n测试推理 (用户1, 电影1-5):")
            print(f"  分数: {scores}")
            
            # 测试排序
            ranked = ncf_engine.rank(1, list(range(1, 100)), top_k=10)
            print(f"\n测试排序 (用户1, Top-10):")
            print(f"  结果: {ranked}")
        else:
            print("\n✗ NCF引擎加载失败，请检查:")
            print("  1. backend/artifacts/ncf.pt 是否存在")
            print("  2. backend/artifacts/ncf_meta.json 是否存在")
            print("  3. 模型文件是否损坏")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
