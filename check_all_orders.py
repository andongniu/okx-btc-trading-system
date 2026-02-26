#!/usr/bin/env python3
"""
检查所有历史订单和交易记录
"""

import ccxt
import json
from datetime import datetime

def check_all_orders():
    print('🔍 检查所有历史订单和交易记录...')
    print('='*60)
    
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
        
        # 获取所有订单
        print('📋 获取所有历史订单...')
        try:
            orders = exchange.fetch_orders(symbol, limit=20)
            print(f'   找到 {len(orders)} 个订单')
            
            if orders:
                print('\n📊 订单详情:')
                for order in orders:
                    order_time = datetime.fromtimestamp(order["timestamp"]/1000).strftime('%Y-%m-%d %H:%M:%S')
                    status = order["status"]
                    side = order["side"]
                    amount = order["amount"]
                    filled = order["filled"]
                    price = order.get("price", order.get("average", 0))
                    
                    print(f'   [{order_time}] ID: {order["id"]}')
                    print(f'       方向: {side} | 状态: {status}')
                    print(f'       数量: {amount}张 | 已成交: {filled}张')
                    print(f'       价格: ${price}')
                    print(f'       类型: {order.get("type", "N/A")}')
                    print()
            else:
                print('   无历史订单')
                
        except Exception as e:
            print(f'   获取订单失败: {e}')
        
        # 获取所有成交记录
        print('\n💰 获取所有成交记录...')
        try:
            trades = exchange.fetch_my_trades(symbol, limit=20)
            print(f'   找到 {len(trades)} 笔成交')
            
            if trades:
                print('\n📈 成交详情:')
                for trade in trades:
                    trade_time = datetime.fromtimestamp(trade["timestamp"]/1000).strftime('%Y-%m-%d %H:%M:%S')
                    side = trade["side"]
                    amount = trade["amount"]
                    price = trade["price"]
                    cost = trade["cost"]
                    fee = trade.get("fee", {})
                    
                    print(f'   [{trade_time}] ID: {trade["id"]}')
                    print(f'       方向: {side} | 数量: {amount}张')
                    print(f'       价格: ${price} | 金额: ${cost}')
                    if fee:
                        print(f'       手续费: {fee.get("cost", 0)} {fee.get("currency", "N/A")}')
                    print()
            else:
                print('   无成交记录')
                
        except Exception as e:
            print(f'   获取成交失败: {e}')
        
        # 检查当前持仓
        print('\n📊 当前持仓状态:')
        positions = exchange.fetch_positions([symbol])
        has_position = False
        
        for pos in positions:
            if pos['symbol'] == symbol:
                contracts = float(pos.get('contracts', 0))
                if contracts > 0:
                    has_position = True
                    entry_time = datetime.fromtimestamp(pos.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')
                    print(f'   ✅ 当前持仓:')
                    print(f'       合约数量: {contracts} 张')
                    print(f'       方向: {pos.get("side", "N/A")}')
                    print(f'       入场价: ${pos.get("entryPrice", 0)}')
                    print(f'       入场时间: {entry_time}')
                    print(f'       当前价: ${pos.get("markPrice", 0)}')
                    print(f'       未实现盈亏: ${pos.get("unrealizedPnl", 0)}')
                    print(f'       保证金: ${pos.get("initialMargin", 0)}')
                    print(f'       杠杆: {pos.get("leverage", 0)}x')
                    break
        
        if not has_position:
            print('   无当前持仓')
        
        print('\n🎯 分析结论:')
        if 'orders' in locals() and len(orders) > 0:
            print(f'   1. 历史订单数量: {len(orders)}')
            print(f'   2. 成交记录数量: {len(trades) if "trades" in locals() else 0}')
            print(f'   3. 当前持仓: {"有" if has_position else "无"}')
            
            # 检查最早的测试订单
            if len(orders) > 0:
                earliest_order = min(orders, key=lambda x: x['timestamp'])
                print(f'\n📅 最早的订单:')
                print(f'   ID: {earliest_order["id"]}')
                print(f'   时间: {datetime.fromtimestamp(earliest_order["timestamp"]/1000).strftime("%Y-%m-%d %H:%M:%S")}')
                print(f'   状态: {earliest_order["status"]}')
                print(f'   方向: {earliest_order["side"]}')
                print(f'   数量: {earliest_order["amount"]}张')
        else:
            print('   无历史交易记录')
            
        return orders, trades, has_position
        
    except Exception as e:
        print(f'❌ 检查失败: {e}')
        import traceback
        traceback.print_exc()
        return None, None, False

if __name__ == '__main__':
    orders, trades, has_position = check_all_orders()
    
    if orders:
        print('\n✅ 订单检查完成')
        print('   请检查监控面板是否显示所有订单')
    else:
        print('\n⚠️  未找到订单记录')