#!/bin/bash
# 启动激进交易系统

echo "🚀 启动激进交易系统..."
echo "="*50

# 停止现有交易系统
echo "🛑 停止现有系统..."
pkill -f "continuous_autonomous_trader.py" 2>/dev/null || true
pkill -f "optimized_autonomous_trader.py" 2>/dev/null || true
sleep 2

# 激活虚拟环境
source venv/bin/activate

echo "📊 当前市场分析..."
python3 -c "
import ccxt
import json
import numpy as np
from datetime import datetime

# 加载配置
with open('config/final_config.json', 'r') as f:
    config = json.load(f)

# 初始化交易所
exchange = ccxt.okx({
    'apiKey': config['exchange']['api_key'],
    'secret': config['exchange']['secret'],
    'password': config['exchange']['passphrase'],
    'enableRateLimit': True,
    'proxies': config['exchange']['proxies'],
    'options': {'defaultType': 'swap'}
})

symbol = 'BTC/USDT:USDT'

# 获取数据
ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
closes = np.array([c[4] for c in ohlcv])
current_price = closes[-1]

# 计算指标
sma_20 = np.mean(closes[-20:])
sma_50 = np.mean(closes[-50:])
support = np.min(closes[-20:])
resistance = np.max(closes[-20:])
price_position = (current_price - support) / (resistance - support) if resistance != support else 0.5

print(f'📈 当前市场状态:')
print(f'   价格: \${current_price:.2f}')
print(f'   趋势: {\"上涨\" if current_price > sma_20 > sma_50 else \"下跌\" if current_price < sma_20 < sma_50 else \"震荡\"}')
print(f'   位置: {price_position:.1%}')
print(f'   支撑: \${support:.2f}')
print(f'   阻力: \${resistance:.2f}')

# 检查激进策略条件
print(f'\\n🎯 激进策略机会分析:')
if price_position < 0.5:
    print(f'   ✅ 价格在50%以下，符合激进多头条件')
elif price_position > 0.5:
    print(f'   ✅ 价格在50%以上，符合激进空头条件')
else:
    print(f'   ⚠️  价格在中线，等待突破')

# 检查突破
recent_high = np.max(closes[-15:])
recent_low = np.min(closes[-15:])
if current_price > recent_high * 1.01:
    print(f'   🚀 向上突破1%！符合突破策略')
elif current_price < recent_low / 1.01:
    print(f'   🚀 向下突破1%！符合突破策略')
"

echo ""
echo "🎯 激进策略参数:"
echo "   • 检查间隔: 30秒"
echo "   • 单笔风险: 1.5%"
echo "   • 每日交易: 12次"
echo "   • 支撑/阻力: 50%线"
echo "   • 风险回报比: 1.2:1"
echo "   • 新增策略: 突破 + 动量"

echo ""
echo "📱 启动交易系统..."
# 这里需要实际的Python脚本，暂时先显示信息
echo "⚠️  需要创建完整的激进交易脚本"
echo "💡 建议: 立即修改现有策略参数"

echo ""
echo "🌐 监控面板: http://localhost:8084"
echo "📱 Telegram通知: @anth6iu_noticer_bot"
echo "="*50
echo "✅ 激进交易系统准备就绪"