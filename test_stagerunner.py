import pytest
import asyncio
import os
from stagerunner import run


@pytest.mark.asyncio
async def test_run():
    """测试运行脚本文件"""
    # 使用一个实际的测试脚本
    test_script = "test_script.it2"

    # 创建测试脚本
    with open(test_script, "w", encoding="utf-8") as f:
        f.write("""# 测试脚本
# 设置棋盘参数
cellsize 90
boardcenter 1920 1080

# 等待2秒
sleep 2

# 移动到指定位置
move 1 2

# 点击指定坐标
leftclick 100 100
""")

    try:
        # 运行脚本并等待完成
        await run(test_script)

    finally:
        # 清理测试文件
        if os.path.exists(test_script):
            os.remove(test_script)


if __name__ == "__main__":
    pytest.main(["-v", "test_stagerunner.py"])
