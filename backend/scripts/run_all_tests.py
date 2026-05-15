# run_all_tests.py
"""一键运行所有测试 - 训练与评估验证管道"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n🔄 执行: {description}")
    print(f"   命令: {cmd}")
    import subprocess
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    print(f"   状态: {'成功' if result.returncode == 0 else '失败'}")
    if result.stdout:
        print(f"   输出: {result.stdout[:500]}..." if len(result.stdout) > 500 else f"   输出: {result.stdout}")
    if result.stderr:
        print(f"   错误: {result.stderr[:500]}..." if len(result.stderr) > 500 else f"   错误: {result.stderr}")
    return result.returncode == 0

def verify_data():
    """验证数据导入"""
    print_header("步骤1: 数据验证")
    
    # 运行数据验证脚本
    success = run_command(
        "python -m backend.scripts.verify_data",
        "验证数据导入结果"
    )
    
    return success

def train_itemcf():
    """训练ItemCF"""
    print_header("步骤2: 训练ItemCF")
    
    # 运行ItemCF训练
    success = run_command(
        "python -m backend.scripts.train_itemcf --topk 50",
        "训练ItemCF模型"
    )
    
    return success

def train_ncf():
    """训练NCF"""
    print_header("步骤3: 训练NCF")
    
    # 运行NCF训练（使用CPU）
    success = run_command(
        "python -m backend.scripts.train_ncf --device cpu --epochs 5 --batch-size 4096",
        "训练NCF模型（CPU模式）"
    )
    
    return success

def evaluate_models():
    """运行离线评估"""
    print_header("步骤4: 离线评估")
    
    # 运行评估脚本
    success = run_command(
        "python -m backend.scripts.evaluate_models --models all",
        "运行离线评估"
    )
    
    return success

def main():
    print("\n" + "#" * 70)
    print("#" + " " * 68 + "#")
    print("#    电影推荐系统 - 训练与评估验证管道")
    print("#" + " " * 68 + "#")
    print("#" + " " * 68 + "#")
    print("#    执行顺序:")
    print("#    1. 数据验证")
    print("#    2. 训练ItemCF")
    print("#    3. 训练NCF")
    print("#    4. 离线评估")
    print("#" + " " * 68 + "#")
    print("#" * 70)
    
    start_time = time.time()
    
    # 执行所有步骤
    steps = [
        ("数据验证", verify_data),
        ("训练ItemCF", train_itemcf),
        ("训练NCF", train_ncf),
        ("离线评估", evaluate_models),
    ]
    
    all_success = True
    for name, func in steps:
        success = func()
        if not success:
            all_success = False
            print(f"\n❌ {name}失败，继续执行后续步骤...")
        else:
            print(f"\n✅ {name}成功")
    
    elapsed = time.time() - start_time
    
    print_header("验证总结")
    
    print(f"\n⏱️  总耗时: {elapsed:.2f}秒")
    
    if all_success:
        print("\n🎉 所有步骤执行成功！")
        print("\n📁 生成的文件:")
        print("  - 相似度数据: 数据库 movie_similarity 表")
        print("  - NCF模型: backend/artifacts/ncf.pt")
        print("  - NCF元数据: backend/artifacts/ncf_meta.json")
        print("  - 评估结果: backend/artifacts/evaluation_results.json")
    else:
        print("\n❌ 部分步骤执行失败，请检查上述输出")
    
    print("\n" + "#" * 70 + "\n")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())