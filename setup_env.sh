#!/bin/bash
# 快速设置虚拟环境脚本

set -e

echo "=========================================="
echo "MBTI Regulator Experiment - 环境设置"
echo "=========================================="

# 检查是否在项目目录
if [ ! -f "requirements.txt" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境已创建"
else
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo ""
echo "升级 pip..."
pip install --upgrade pip

# 安装依赖
echo ""
echo "安装项目依赖..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✓ 环境设置完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 配置 API Key: 编辑 ../MBTI-in-Thoughts/.env"
echo "3. 运行实验: python run_comparison_experiment.py --skip_4o --rounds 3"
echo ""
echo "退出虚拟环境: deactivate"
echo "=========================================="
