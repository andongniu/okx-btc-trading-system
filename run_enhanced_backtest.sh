#!/bin/bash

# 增强版回测启动脚本

echo "🚀 启动增强版回测分析..."
echo "================================"

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "激活Python虚拟环境..."
    source venv/bin/activate
else
    echo "错误: 虚拟环境不存在"
    exit 1
fi

# 检查数据文件
DATA_FILE="okx_btc_perpetual_5m.csv"
if [ ! -f "$DATA_FILE" ]; then
    echo "错误: 数据文件 $DATA_FILE 不存在"
    echo "请先下载历史数据"
    exit 1
fi

echo "数据文件检查通过: $DATA_FILE"

# 检查依赖
echo "检查Python依赖..."
python -c "import pandas, numpy, plotly" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装必要依赖..."
    pip install pandas numpy plotly ta
fi

# 运行增强版回测
echo "运行增强版回测脚本..."
python backtest_enhanced.py

# 检查结果文件
echo ""
echo "📊 生成的文件:"
echo "================================"

if [ -f "backtest_enhanced_report.json" ]; then
    echo "✅ 回测报告: backtest_enhanced_report.json"
    echo "   包含简单策略和优化策略的详细对比"
fi

if [ -f "backtest_chart.html" ]; then
    echo "✅ K线图表: backtest_chart.html"
    echo "   包含价格走势、成交量、RSI、MACD和交易点标注"
fi

if [ -f "trade_history.html" ]; then
    echo "✅ 交易历史: trade_history.html"
    echo "   包含所有交易的详细表格和统计信息"
fi

echo ""
echo "📈 查看结果:"
echo "================================"
echo "1. 在浏览器中打开 backtest_chart.html 查看K线图"
echo "2. 查看 trade_history.html 分析每笔交易"
echo "3. 查看 backtest_enhanced_report.json 获取详细数据"
echo ""
echo "⚙️  优化策略文件: user_data/strategies/OptimizedStrategy.py"
echo "   包含多指标组合的优化交易策略"

# 如果图表文件存在，尝试在默认浏览器中打开
if [ -f "backtest_chart.html" ] && [ "$1" = "--open" ]; then
    echo ""
    echo "正在在默认浏览器中打开图表..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open backtest_chart.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open backtest_chart.html 2>/dev/null || echo "请手动打开: backtest_chart.html"
    else
        echo "请手动打开: backtest_chart.html"
    fi
fi

echo ""
echo "✅ 增强版回测完成!"