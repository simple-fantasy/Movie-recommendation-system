# train_ncf_verify.py
"""NCF训练验证脚本 - 验证NCF模型训练结果"""
import json
from pathlib import Path
from backend.app import create_app, db
from backend.app.models import Movie, Rating, User
from backend.app.ncf_engine import ncf_engine

def check_model_files():
    """检查模型文件是否存在"""
    artifacts = Path(__file__).resolve().parents[1] / "artifacts"
    ckpt_path = artifacts / "ncf.pt"
    meta_path = artifacts / "ncf_meta.json"
    
    print("=" * 60)
    print("NCF训练验证报告")
    print("=" * 60)
    
    print("\n📁 模型文件检查：")
    files_ok = True
    
    if ckpt_path.exists():
        size = ckpt_path.stat().st_size
        print(f"  ✓ ncf.pt 存在 ({size/1024/1024:.2f} MB)")
    else:
        print(f"  ✗ ncf.pt 不存在")
        files_ok = False
    
    if meta_path.exists():
        size = meta_path.stat().st_size
        print(f"  ✓ ncf_meta.json 存在 ({size} bytes)")
        # 读取meta信息
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        print(f"\n📊 模型配置：")
        print(f"  用户数: {meta.get('num_users', 'N/A')}")
        print(f"  电影数: {meta.get('num_items', 'N/A')}")
        cfg = meta.get('config', {})
        print(f"  embedding_dim: {cfg.get('embedding_dim', 'N/A')}")
        print(f"  hidden_dim: {cfg.get('hidden_dim', 'N/A')}")
        print(f"  训练轮数: {cfg.get('epochs', 'N/A')}")
        
        train_metrics = meta.get('train', {})
        if train_metrics:
            print(f"\n📈 训练指标：")
            print(f"  最终Loss: {train_metrics.get('final_loss', 'N/A'):.4f}")
            print(f"  最佳NDCG@K: {train_metrics.get('best_NDCG@K', 'N/A'):.4f}")
            print(f"  评估K: {train_metrics.get('eval_k', 'N/A')}")
    else:
        print(f"  ✗ ncf_meta.json 不存在")
        files_ok = False
    
    return files_ok

def check_ncf_engine():
    """检查NCF引擎加载状态"""
    print("\n🔧 NCF引擎状态：")
    loaded = ncf_engine.load()
    if loaded:
        print(f"  ✓ NCF模型已加载")
        print(f"  用户数: {ncf_engine.num_users}")
        print(f"  电影数: {ncf_engine.num_items}")
        return True
    else:
        print(f"  ✗ NCF模型加载失败")
        return False

def main():
    files_ok = check_model_files()
    engine_ok = check_ncf_engine()
    
    print("\n" + "=" * 60)
    
    if files_ok and engine_ok:
        print("✅ NCF验证通过")
        return True
    else:
        print("❌ NCF验证失败")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)