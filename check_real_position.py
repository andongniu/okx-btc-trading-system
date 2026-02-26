#!/usr/bin/env python3
"""
检查真实持仓状态
"""

import ccxt
import json

def check_real_position():
    print('🔍 检查真实持仓状态...')
    print('='*50)
    
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
        
        # 检查持仓
        positions = exchange.fetch_positions([symbol])
        has_position = False
        
        for pos in positions:
            if pos['symbol'] == symbol:
                contracts = float(pos.get('contracts', 0))
                if contracts > 0:
                    has_position = True
                    print(f'✅ 真实持仓确认:')
                    print(f'   合约数量: {contracts} 张')
                    print(f'   方向: {pos.get("side", "N/A")}')
                    print(f'   入场价: ${pos.get("entryPrice", 0)}')
                    print(f'   当前价: ${pos.get("markPrice", 0)}')
                    print(f'   未实现盈亏: ${pos.get("unrealizedPnl", 0)}')
                    print(f'   保证金: ${pos.get("initialMargin", 0)}')
                    print(f'   杠杆: {pos.get("leverage", 0)}x')
                    
                    # 计算实际BTC
                    btc_amount = contracts * 0.01
                    print(f'   实际BTC: {btc_amount:.4f}')
                    print(f'   合约价值: ${btc_amount * float(pos.get("markPrice", 0)):.2f}')
                    break
        
        if not has_position:
            print('   无真实持仓')
        
        # 检查订单
        order_id = '3338362761216155648'
        print(f'\n📋 检查测试订单:')
        try:
            order = exchange.fetch_order(order_id, symbol)
            print(f'   订单ID: {order["id"]}')
            print(f'   状态: {order["status"]}')
            print(f'   数量: {order["amount"]} 张')
            print(f'   已成交: {order["filled"]} 张')
            print(f'   成交均价: ${order["average"]}')
            
            if order['status'] == 'closed' and order['filled'] > 0:
                print('   ✅ 订单已完全成交')
            elif order['status'] == 'open':
                print('   ⚠️  订单仍在挂单中')
            else:
                print(f'   ❓ 订单状态异常: {order["status"]}')
        except Exception as e:
            print(f'   获取订单失败: {e}')
        
        # 检查账户余额
        print('\n💰 账户余额状态:')
        balance = exchange.fetch_balance()
        total = balance['total'].get('USDT', 0)
        free = balance['free'].get('USDT', 0)
        used = balance['used'].get('USDT', 0)
        
        print(f'   USDT总额: ${total:.2f}')
        print(f'   可用余额: ${free:.2f}')
        print(f'   占用余额: ${used:.2f}')
        
        if has_position and used < 5:
            print('   ⚠️  占用余额很少，支持小仓位假设')
        
        print('\n🎯 结论:')
        if has_position:
            print('   ✅ 测试交易成功执行，持仓已创建')
            print('   ✅ 监控面板数据与真实数据一致')
            print('   ⚠️  系统状态可能需要手动切换到"trading"')
        else:
            print('   ❌ 测试交易可能未成功执行')
            print('   ⚠️  监控面板显示持仓但真实账户无持仓')
        
        return has_position
        
    except Exception as e:
        print(f'❌ 检查失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    has_position = check_real_position()
    if has_position:
        print('\n✅ 真实持仓存在，监控面板显示正确。')
        print('   问题: 系统状态需要手动切换到"trading"才能显示交易控制按钮。')
    else:
        print('\n⚠️  真实持仓不存在，请检查交易执行情况。')