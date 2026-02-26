#!/usr/bin/env python3
"""
平掉当前测试仓位
"""

import ccxt
import json
import time

def close_position():
    print('🔄 平掉测试仓位...')
    print('='*40)
    
    try:
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
        
        # 检查当前持仓
        positions = exchange.fetch_positions([symbol])
        has_position = False
        position_info = {}
        
        for pos in positions:
            if pos['symbol'] == symbol and float(pos.get('contracts', 0)) > 0:
                has_position = True
                position_info = {
                    'contracts': float(pos.get('contracts', 0)),
                    'side': pos.get('side', 'long'),
                    'entry_price': float(pos.get('entryPrice', 0)),
                    'current_price': float(pos.get('markPrice', 0))
                }
                break
        
        if not has_position:
            print('✅ 无持仓，无需平仓')
            return True
        
        print(f'发现持仓:')
        print(f'   合约数量: {position_info["contracts"]} 张')
        print(f'   方向: {position_info["side"]}')
        print(f'   入场价: ${position_info["entry_price"]}')
        print(f'   当前价: ${position_info["current_price"]}')
        
        # 计算盈亏
        if position_info['side'] == 'long':
            pnl = (position_info['current_price'] - position_info['entry_price']) * position_info['contracts'] * 0.01
        else:
            pnl = (position_info['entry_price'] - position_info['current_price']) * position_info['contracts'] * 0.01
        
        print(f'   未实现盈亏: ${pnl:.4f}')
        
        # 执行平仓
        print('\n🚀 执行市价平仓...')
        
        if position_info['side'] == 'long':
            # 多头平仓 = 卖出
            order = exchange.create_market_sell_order(
                symbol=symbol,
                amount=position_info['contracts']
            )
            action = '卖出'
        else:
            # 空头平仓 = 买入
            order = exchange.create_market_buy_order(
                symbol=symbol,
                amount=position_info['contracts']
            )
            action = '买入'
        
        print(f'✅ 平仓订单提交成功!')
        print(f'   订单ID: {order["id"]}')
        print(f'   操作: {action} {order["amount"]} 张合约')
        print(f'   订单状态: {order.get("status", "submitted")}')
        
        # 等待3秒检查
        print('\n⏳ 等待3秒确认平仓...')
        time.sleep(3)
        
        # 检查持仓是否平掉
        positions_after = exchange.fetch_positions([symbol])
        position_closed = True
        
        for pos in positions_after:
            if pos['symbol'] == symbol and float(pos.get('contracts', 0)) > 0:
                position_closed = False
                remaining = float(pos.get('contracts', 0))
                print(f'⚠️  仍有持仓: {remaining} 张合约')
                break
        
        if position_closed:
            print('✅ 仓位已成功平掉')
        else:
            print('⚠️  仓位可能未完全平掉')
        
        # 检查账户余额
        balance = exchange.fetch_balance()
        print(f'\n💰 平仓后账户余额:')
        print(f'   USDT总额: ${balance["total"].get("USDT", 0):.2f}')
        print(f'   可用余额: ${balance["free"].get("USDT", 0):.2f}')
        print(f'   占用余额: ${balance["used"].get("USDT", 0):.2f}')
        
        return position_closed
        
    except Exception as e:
        print(f'❌ 平仓失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = close_position()
    if success:
        print('\n🎉 平仓操作完成，可以开始更新监控系统。')
    else:
        print('\n⚠️  平仓可能未完全成功，请手动检查。')