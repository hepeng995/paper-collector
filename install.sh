#!/bin/bash
# Paper Collector 安装脚本

echo "📚 正在安装 Paper Collector..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3"
    exit 1
fi

# 检查 requests
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 正在安装 requests..."
    pip install requests
fi

echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "  python3 scripts/collect.py"
echo ""
echo "或直接运行："
echo "  ./collect.sh"
