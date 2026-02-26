#!/usr/bin/env python3
"""
实时检查持仓和价格
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

print('📊 实时持仓查询')
print('='*50)
print(f'查询时间: {datetime.now().strftime("%H:%M:%S")}')

try:
    # 1. 查询持仓
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
                leverage = float(pos.get('leverage', 0))
                margin = float(pos.get('initialMargin', 0))
                
                pnl_percent = (unrealized_pnl / (contracts * 0.01 * entry_price) * 100) if contracts > 0 and entry_price > 0 else 0
                
                print(f'✅ 当前持仓:')
                print(f'   方向: {pos.get("side", "N/A")}')
                print(f'   合约数量: {contracts}张 ({contracts * 0.01:.4f} BTC)')
                print(f'   入场价: ${entry_price:.2f}')
                print(f'   当前价: ${mark_price:.2f}')
                print(f'   浮动盈亏: ${unrealized_pnl:.4f}')
                print(f'   盈亏百分比: {pnl_percent:.2f}%')
                print(f'   杠杆: {leverage}x')
                print(f'   占用保证金: ${margin:.2f}')
                break
    
    if not has_position:
        print('📊 当前持仓: 无')
    
    # 2. 查询账户余额
    balance = exchange.fetch_balance()
    total = balance['total'].get('USDT', 0)
    free = balance['free'].get('USDT', 0)
    used = balance['used'].get('USDT', 0)
    
    print(f'\n💰 账户余额:')
    print(f'   总额: ${total:.2f}')
    print(f'   可用: ${free:.2f}')
    print(f'   占用: ${used:.2f}')
    
    # 3. 查询当前价格
    ticker = exchange.fetch_ticker(symbol)
    print(f'\n📈 市场数据:')
    print(f'   当前价: ${ticker["last"]:.2f}')
    print(f'   24h涨跌: {ticker["percentage"]:.2f}%')
    print(f'   更新时间: {datetime.fromtimestamp(ticker["timestamp"]/1000).strftime("%H:%M:%S")}')
    
    print('\n⏱️ 系统自动更新频率:')
    print('   监控面板: 每5秒更新')
    print('   交易系统: 每30秒分析市场')
    print('   通知器: 每30秒检查持仓')
    print('   Telegram: 事件触发立即通知')
    
    print('\n🌐 实时查看: http://localhost:8084')
    print('📱 通知Bot: @anth6iu_noticer_bot')
    
except Exception as e:
    print(f'❌ 查询失败: {e}')