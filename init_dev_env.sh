#!/bin/bash
# QUANTAXIS 开发环境初始化脚本
# 适用于 Python 3.9-3.11

set -e

echo "🚀 QUANTAXIS 开发环境初始化"
echo "================================"

# 检查 Python 版本
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "📌 检测到 Python 版本: $PYTHON_VERSION"

# 安装 pip (如果不存在)
if ! command -v pip3 &> /dev/null; then
    echo "📦 安装 pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    python3 /tmp/get-pip.py --break-system-packages
fi

# 核心依赖安装
echo "📦 安装核心依赖..."

CORE_DEPS=(
    "pandas<3.0"
    "numpy"
    "pymongo>=4.0"
    "motor>=3.0"
    "tornado>=6.0"
    "scipy"
    "numba"
    "pyecharts>=2.0"
    "seaborn"
    "matplotlib"
    "requests"
    "bs4"
    "lxml"
)

for dep in "${CORE_DEPS[@]}"; do
    echo "  安装: $dep"
    pip3 install "$dep" --break-system-packages -q 2>/dev/null || true
done

# 数据源依赖
echo "📦 安装数据源依赖..."
DATA_DEPS=(
    "tushare"
    "pytdx>=1.72"
    "clickhouse-driver"
    "flask"
)

for dep in "${DATA_DEPS[@]}"; do
    echo "  安装: $dep"
    pip3 install "$dep" --break-system-packages -q 2>/dev/null || true
done

# 策略/分析依赖
echo "📦 安装策略分析依赖..."
STRATEGY_DEPS=(
    "backtrader"
    "empyrical"
    "pyfolio"
    "statsmodels"
    "zenlog>=1.1"
    "retrying"
    "apscheduler"
    "websocket-client"
)

for dep in "${STRATEGY_DEPS[@]}"; do
    echo "  安装: $dep"
    pip3 install "$dep" --break-system-packages -q 2>/dev/null || true
done

# czsc 缠论模块依赖
echo "📦 安装缠论模块依赖..."
CZSC_DEPS=(
    "dill"
    "transitions"
    "python-docx"
    "deprecated"
    "jsonpickle"
)

for dep in "${CZSC_DEPS[@]}"; do
    echo "  安装: $dep"
    pip3 install "$dep" --break-system-packages -q 2>/dev/null || true
done

# 其他依赖
echo "📦 安装其他依赖..."
OTHER_DEPS=(
    "janus==0.4.0"
    "async_timeout"
    "lz4"
    "pyarrow"
    "pika"
    "qaenv>=0.0.4"
)

for dep in "${OTHER_DEPS[@]}"; do
    echo "  安装: $dep"
    pip3 install "$dep" --break-system-packages -q 2>/dev/null || true
done

echo ""
echo "================================"
echo "✅ 环境初始化完成!"
echo ""
echo "📝 注意事项:"
echo "   1. Python 3.11 需要修改 QAAsyncThread.py 以兼容 janus"
echo "   2. MongoDB 需要单独安装并启动"
echo "   3. 完整功能需要 Tushare Pro token"
echo ""
echo "🚀 快速测试:"
echo "   cd /ws/QUANTAXIS"
echo "   python3 -c \"from QUANTAXIS.QAUtil.QADate import QA_util_to_datetime; print('OK')\""
