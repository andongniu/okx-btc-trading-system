#!/usr/bin/env python3
"""
检查所有历史订单和交易记录 - 修复版
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
        orders = []
        trades = []
        has_position = False
        
        # 获取所有成交记录
        print('💰 获取所有成交记录...')
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
        
        # 获取已关闭订单
        print('\n📋 获取已关闭订单...')
        try:
            closed_orders = exchange.fetch_closed_orders(symbol, limit=20)
            print(f'   找到 {len(closed_orders)} 个已关闭订单')
            
            if closed_orders:
                print('\n📊 已关闭订单详情:')
                for order in closed_orders:
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
                    
                    orders.append(order)
            else:
                print('   无已关闭订单')
                
        except Exception as e:
            print(f'   获取已关闭订单失败: {e}')
        
        # 获取未完成订单
        print('\n⏳ 获取未完成订单...')
        try:
            open_orders = exchange.fetch_open_orders(symbol, limit=20)
            print(f'   找到 {len(open_orders)} 个未完成订单')
            
            if open_orders:
                print('\n📊 未完成订单详情:')
                for order in open_orders:
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
                    
                    orders.append(order)
            else:
                print('   无未完成订单')
                
        except Exception as e:
            print(f'   获取未完成订单失败: {e}')
        
        # 检查当前持仓
        print('\n📊 当前持仓状态:')
        positions = exchange.fetch_positions([symbol])
        
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
        
        print('\n🎯 交易历史分析:')
        print('='*40)
        
        if len(trades) >= 3:
            print('📅 完整交易历史:')
            print('1. 第一笔交易 (开仓):')
            print(f'   时间: {datetime.fromtimestamp(trades[2]["timestamp"]/1000).strftime("%Y-%m-%d %H:%M:%S")}')
            print(f'   方向: {trades[2]["side"]}')
            print(f'   价格: ${trades[2]["price"]}')
            print(f'   数量: {trades[2]["amount"]}张')
            
            print('\n2. 第二笔交易 (平仓):')
            print(f'   时间: {datetime.fromtimestamp(trades[1]["timestamp"]/1000).strftime("%Y-%m-%d %H:%M:%S")}')
            print(f'   方向: {trades[1]["side"]}')
            print(f'   价格: ${trades[1]["price"]}')
            print(f'   数量: {trades[1]["amount"]}张')
            
            # 计算第一笔交易的盈亏
            entry_price = trades[2]["price"]
            exit_price = trades[1]["price"]
            amount = trades[2]["amount"]
            pnl = (exit_price - entry_price) * amount * 0.01  # 合约乘数
            print(f'   盈亏: ${pnl:.4f}')
            
            print('\n3. 第三笔交易 (当前持仓):')
            print(f'   时间: {datetime.fromtimestamp(trades[0]["timestamp"]/1000).strftime("%Y-%m-%d %H:%M:%S")}')
            print(f'   方向: {trades[0]["side"]}')
            print(f'   价格: ${trades[0]["price"]}')
            print(f'   数量: {trades[0]["amount"]}张')
            print(f'   状态: 持仓中')
        
        print('\n📊 交易统计:')
        print(f'   总交易次数: {len(trades)}')
        print(f'   当前持仓: {"有" if has_position else "无"}')
        
        if len(trades) >= 2:
            # 计算已平仓交易的盈亏
            if trades[1]["side"] == "sell" and trades[2]["side"] == "buy":
                profit = (trades[1]["price"] - trades[2]["price"]) * trades[1]["amount"] * 0.01
                print(f'   第一笔交易盈亏: ${profit:.4f}')
        
        return orders, trades, has_position
        
    except Exception as e:
        print(f'❌ 检查失败: {e}')
        import traceback
        traceback.print_exc()
        return [], [], False

if __name__ == '__main__':
    orders, trades, has_position = check_all_orders()
    
    if trades:
        print('\n✅ 交易记录检查完成')
        print(f'   找到 {len(trades)} 笔成交记录')
        print('   监控面板应该显示所有交易记录')
    else:
        print('\n⚠️  未找到交易记录')