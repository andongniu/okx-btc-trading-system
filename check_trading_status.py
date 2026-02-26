#!/usr/bin/env python3
"""
检查交易系统状态和订单执行情况
"""

import ccxt
import json
import time
from datetime import datetime

def check_trading_status():
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
        
        print('🔍 检查OKX账户交易状态...')
        print('='*60)
        
        # 获取当前持仓
        print('📊 当前持仓状态:')
        print('-'*30)
        positions = exchange.fetch_positions(['BTC/USDT:USDT'])
        
        has_position = False
        if positions:
            for pos in positions:
                if pos['symbol'] == 'BTC/USDT:USDT' and float(pos.get('contracts', 0)) > 0:
                    has_position = True
                    print(f'✅ 发现活跃持仓:')
                    print(f'   合约: {pos["symbol"]}')
                    print(f'   持仓量: {pos["contracts"]:.4f} BTC')
                    print(f'   方向: {pos["side"]}')
                    print(f'   入场价: ${pos.get("entryPrice", 0):,.2f}')
                    print(f'   当前价: ${pos.get("markPrice", 0):,.2f}')
                    
                    entry_price = float(pos.get('entryPrice', 0))
                    current_price = float(pos.get('markPrice', 0))
                    if entry_price > 0:
                        pnl_percent = ((current_price - entry_price) / entry_price * 100) if pos['side'] == 'long' else ((entry_price - current_price) / entry_price * 100)
                        print(f'   盈亏百分比: {pnl_percent:.2f}%')
                    
                    print(f'   未实现盈亏: ${pos.get("unrealizedPnl", 0):.2f}')
                    print(f'   保证金: ${pos.get("initialMargin", 0):.2f}')
                    print(f'   杠杆: {pos.get("leverage", 0)}x')
                    print(f'   持仓时间: {pos.get("timestamp", "未知")}')
        
        if not has_position:
            print('   无活跃持仓')
        
        # 获取最近订单
        print('\n📋 最近订单记录:')
        print('-'*30)
        
        orders = []
        try:
            # 分别获取开单和已关闭订单
            open_orders = exchange.fetch_open_orders('BTC/USDT:USDT', limit=10)
            closed_orders = exchange.fetch_closed_orders('BTC/USDT:USDT', limit=10)
            
            orders = open_orders + closed_orders
            if orders:
                # 按时间排序，最新的在前
                orders.sort(key=lambda x: x['timestamp'] if x['timestamp'] else 0, reverse=True)
                
                print(f'找到 {len(orders)} 个订单 (显示最近5个):')
                print()
                
                recent_orders = orders[:5]
                for i, order in enumerate(recent_orders, 1):
                    status = order['status']
                    symbol = order['symbol']
                    side = order['side']
                    amount = order['amount']
                    price = order['price'] if order['price'] else '市价'
                    filled = order['filled']
                    order_time = datetime.fromtimestamp(order['timestamp']/1000).strftime('%H:%M:%S') if order['timestamp'] else '未知'
                    
                    status_icon = '✅' if status == 'closed' else '🔄' if status == 'open' else '❌'
                    
                    print(f'{i}. {status_icon} {order_time} - {side.upper()} {amount:.4f} {symbol}')
                    print(f'   价格: {price}, 状态: {status}, 已成交: {filled:.4f}')
                    print(f'   订单ID: {order["id"]}')
                    
                    if status == 'open':
                        print('   ⚠️  订单仍在挂单中，等待成交')
                    elif status == 'closed' and filled > 0:
                        print('   ✅ 订单已完全成交')
                        # 获取成交详情
                        try:
                            trades = exchange.fetch_my_trades(symbol, since=order['timestamp']-60000, limit=5)
                            if trades:
                                print('   成交详情:')
                                for trade in trades:
                                    if trade['order'] == order['id']:
                                        print(f'     - {trade["datetime"]}: {trade["amount"]:.4f} @ ${trade["price"]:,.2f}')
                        except:
                            pass
                    print()
            else:
                print('   无订单记录')
        except Exception as e:
            print(f'   获取订单失败: {e}')
        
        # 检查账户余额
        print('💰 账户资金状态:')
        print('-'*30)
        balance = exchange.fetch_balance()
        usdt_total = balance.get('total', {}).get('USDT', 0)
        usdt_free = balance.get('free', {}).get('USDT', 0)
        usdt_used = balance.get('used', {}).get('USDT', 0)
        
        print(f'USDT总额: ${usdt_total:.2f}')
        print(f'可用余额: ${usdt_free:.2f}')
        print(f'占用余额: ${usdt_used:.2f}')
        
        if usdt_used > 0 and not has_position:
            print('⚠️  有资金被占用但无可见持仓，可能有挂单')
        
        # 获取当前市场数据
        print('\n📈 当前市场数据:')
        print('-'*30)
        ticker = exchange.fetch_ticker('BTC/USDT:USDT')
        print(f'BTC价格: ${ticker["last"]:,.2f}')
        print(f'24h涨跌: {ticker["percentage"]:.2f}%')
        print(f'买一价: ${ticker["bid"]:,.2f}')
        print(f'卖一价: ${ticker["ask"]:,.2f}')
        
        # 系统状态总结
        print('\n🎯 交易系统状态总结:')
        print('='*60)
        
        if has_position:
            print('✅ **交易系统正在运行** - 有活跃持仓')
            print('   建议:')
            print('   1. 监控持仓盈亏变化')
            print('   2. 检查止损止盈是否设置')
            print('   3. 准备根据策略平仓或调整')
        else:
            # 检查是否有挂单
            has_open_orders = False
            if orders:
                for order in orders:
                    if order['status'] == 'open':
                        has_open_orders = True
                        break
            
            if has_open_orders:
                print('🔄 **交易系统正在运行** - 有挂单等待成交')
                print('   建议:')
                print('   1. 监控挂单状态')
                print('   2. 根据市场变化调整挂单价格')
                print('   3. 等待成交或考虑取消')
            elif usdt_used > 0:
                print('⚠️  **资金状态异常** - 资金被占用但无可见订单/持仓')
                print('   建议:')
                print('   1. 检查订单历史确认状态')
                print('   2. 等待系统同步')
                print('   3. 如有疑问联系交易所客服')
            else:
                print('📭 **交易系统待命** - 无持仓无挂单')
                print('   建议:')
                print('   1. 等待交易信号生成')
                print('   2. 监控市场条件变化')
                print('   3. 准备执行新交易')
        
        print('\n⏰ 检查时间:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    except Exception as e:
        print(f'❌ 检查失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_trading_status()