#!/usr/bin/env python3
"""
检查超快系统状态
"""

import ccxt
import json
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

print('⚡ 超快系统实时状态检查')
print('='*50)
print(f'检查时间: {datetime.now().strftime("%H:%M:%S")}')

try:
    # 检查持仓
    positions = exchange.fetch_positions([symbol])
    has_position = False
    
    for pos in positions:
        if pos['symbol'] == symbol:
            contracts = float(pos.get('contracts', 0))
            if contracts > 0:
                has_position = True
                entry_price = float(pos.get('entryPrice', 0))
                mark_price = float(pos.get('markPrice', 0))
                unrealized_pnl = float(pos.get('unrealizedPnl', 0))
                pnl_percent = (unrealized_pnl / (contracts * 0.01 * entry_price) * 100) if contracts > 0 and entry_price > 0 else 0
                
                print(f'✅ 当前持仓:')
                print(f'   合约: {contracts}张 ({contracts * 0.01:.4f} BTC)')
                print(f'   方向: {pos.get("side", "N/A")}')
                print(f'   入场价: ${entry_price:.2f}')
                print(f'   当前价: ${mark_price:.2f}')
                print(f'   盈亏: ${unrealized_pnl:.4f} ({pnl_percent:.2f}%)')
                print(f'   杠杆: {float(pos.get("leverage", 0))}x')
                break
    
    if not has_position:
        print('📊 当前持仓: 无')
    
    # 检查价格
    ticker = exchange.fetch_ticker(symbol)
    print(f'\n📈 实时价格: ${ticker["last"]:.2f}')
    print(f'📊 24h涨跌: {ticker["percentage"]:.2f}%')
    
    print('\n⏱️  系统频率配置:')
    print('   超快交易系统: 每10秒分析市场')
    print('   交易通知器: 每30秒检查持仓')
    print('   监控面板: 每5秒更新数据')
    print('   Telegram通知: 事件触发立即发送')
    
    print('\n🎯 超快系统特性:')
    print('   • 10秒频率 (原30秒，提高300%)')
    print('   • 0.5%突破阈值 (更敏感)')
    print('   • 快速响应市场变化')
    print('   • 实时监控持仓状态')
    
    print('\n🌐 实时监控: http://localhost:8084')
    print('📱 Telegram通知: @anth6iu_noticer_bot')
    
except Exception as e:
    print(f'❌ 检查失败: {e}')