#!/bin/bash
# 生存交易系统启动脚本

echo "🚀 启动生存交易系统 - 200U→1000U挑战"
echo "=========================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "📦 检查Python依赖..."
pip install -q ccxt pandas numpy flask

# 创建必要的目录
mkdir -p logs templates

# 检查配置文件
if [ ! -f "config/survival_config.json" ]; then
    echo "❌ 配置文件不存在: config/survival_config.json"
    exit 1
fi

# 检查核心文件
if [ ! -f "survival_trader.py" ]; then
    echo "❌ 交易引擎不存在: survival_trader.py"
    exit 1
fi

if [ ! -f "survival_dashboard.py" ]; then
    echo "❌ 仪表盘不存在: survival_dashboard.py"
    exit 1
fi

# 测试API连接
echo "🔐 测试OKX API连接..."
python3 -c "
import ccxt
import json

try:
    with open('config/survival_config.json', 'r') as f:
        config = json.load(f)
    
    exchange = ccxt.okx({
        'apiKey': config['exchange']['api_key'],
        'secret': config['exchange']['secret'],
        'password': config['exchange']['passphrase'],
        'enableRateLimit': True,
        'options': {'defaultType': config['exchange']['default_type']}
    })
    
    # 简单测试
    ticker = exchange.fetch_ticker(config['exchange']['symbol'])
    print('✅ API连接成功')
    print(f'  当前价格: ${ticker[\"last\"]:,.2f}')
    print(f'  24h涨跌: {ticker[\"percentage\"]:.2f}%')
    
    balance = exchange.fetch_balance()
    usdt = balance.get('total', {}).get('USDT', 0)
    print(f'  账户余额: {usdt:.2f} USDT')
    
except Exception as e:
    print(f'❌ API连接失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ API测试失败，请检查网络和代理配置"
    exit 1
fi

# 启动系统
echo ""
echo "🎯 系统启动选项:"
echo "1. 仅启动监控仪表盘"
echo "2. 启动完整交易系统（交易+监控）"
echo "3. 仅测试策略（不实际交易）"
echo ""
read -p "请选择 (1-3): " choice

case $choice in
    1)
        echo "📊 启动监控仪表盘..."
        python3 survival_dashboard.py &
        DASHBOARD_PID=$!
        echo "✅ 仪表盘已启动 (PID: $DASHBOARD_PID)"
        echo "🌐 访问地址: http://localhost:8080"
        echo "📝 停止命令: kill $DASHBOARD_PID"
        ;;
    2)
        echo "🚀 启动完整交易系统..."
        # 这里需要实现交易引擎的启动
        echo "⚠️  完整交易系统开发中..."
        echo "📊 先启动监控仪表盘..."
        python3 survival_dashboard.py &
        DASHBOARD_PID=$!
        echo "✅ 仪表盘已启动 (PID: $DASHBOARD_PID)"
        echo "🌐 访问地址: http://localhost:8080"
        ;;
    3)
        echo "🧪 启动策略测试模式..."
        python3 -c "
from survival_trader import SurvivalTrader
import time

trader = SurvivalTrader('config/survival_config.json')
print('🧠 策略测试开始...')

for i in range(10):
    signal = trader.analyze_market()
    if signal:
        print(f'测试 {i+1}: {signal.direction.value} | 置信度: {signal.confidence:.2f}')
        print(f'  理由: {signal.reason}')
        print(f'  入场价: ${signal.entry_price:,.0f}')
        print(f'  止损: ${signal.stop_loss:,.0f}')
        print(f'  止盈: ${signal.take_profit:,.0f}')
        print(f'  杠杆: {signal.leverage}x')
        print(f'  仓位: {signal.position_size:.4f} 合约')
    else:
        print(f'测试 {i+1}: 无信号')
    time.sleep(2)

print('✅ 策略测试完成')
        "
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "📋 系统信息:"
echo "  项目: 200U→1000U生存交易挑战"
echo "  时间: 30天 (至2026-03-27)"
echo "  标的: BTC/USDT永续合约"
echo "  策略: 趋势跟踪 + 均值回归"
echo "  风控: 生存优先，成本覆盖第一"
echo ""
echo "⚠️  重要提醒:"
echo "  1. 这是高风险交易系统"
echo "  2. 确保理解所有风险"
echo "  3. 实时监控系统状态"
echo "  4. 设置紧急停止机制"
echo ""
echo "🆘 紧急停止: Ctrl+C 或 kill [PID]"
echo "=========================================="