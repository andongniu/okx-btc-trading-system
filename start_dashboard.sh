#!/bin/bash

# 交易系统面板启动脚本

echo "🚀 启动 Freqtrade 交易系统面板..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  未检测到虚拟环境，尝试激活..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ 已激活虚拟环境"
    else
        echo "❌ 未找到虚拟环境，请先创建虚拟环境"
        exit 1
    fi
fi

# 检查必需文件
echo "📁 检查必需文件..."
if [ ! -f "trading_dashboard.html" ]; then
    echo "❌ 未找到 trading_dashboard.html"
    exit 1
fi

if [ ! -f "dashboard_server.py" ]; then
    echo "❌ 未找到 dashboard_server.py"
    exit 1
fi

# 检查回测结果文件
if [ ! -f "backtest_results.json" ]; then
    echo "⚠️  未找到回测结果文件，使用模拟数据"
    # 创建模拟回测结果
    python3 -c "
import json
import random
from datetime import datetime, timedelta

# 生成模拟交易数据
trades = []
initial_balance = 10000
current_balance = initial_balance
start_time = int((datetime.now() - timedelta(days=30)).timestamp())

for i in range(162):
    trade_time = start_time + i * 3600  # 每小时一笔交易
    price = random.uniform(80000, 90000)
    
    if i % 2 == 0:  # 买入
        position = random.uniform(0.05, 0.15)
        trades.append({
            'type': 'buy',
            'timestamp': str(trade_time),
            'price': round(price, 2),
            'position': round(position, 6),
            'balance': 0
        })
    else:  # 卖出
        profit_loss = random.uniform(-0.15, 0.1)  # -15% 到 +10%
        current_balance = current_balance * (1 + profit_loss)
        trades.append({
            'type': 'sell',
            'timestamp': str(trade_time),
            'price': round(price, 2),
            'position': 0,
            'balance': round(current_balance, 6)
        })

results = {
    'initial_balance': initial_balance,
    'final_balance': round(current_balance, 2),
    'total_return': round((current_balance - initial_balance) / initial_balance * 100, 2),
    'num_trades': 162,
    'trades': trades
}

with open('backtest_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print('✅ 已创建模拟回测数据')
"
fi

# 启动服务器
echo "🌐 启动HTTP服务器..."
echo "========================================"
python3 dashboard_server.py