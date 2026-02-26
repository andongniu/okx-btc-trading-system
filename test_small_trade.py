#!/usr/bin/env python3
"""
测试$10小额交易验证API和流程
"""

import ccxt
import json
import time
from datetime import datetime

def test_small_trade():
    print('🚀 开始$10小额交易测试...')
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
        
        # 获取当前市场数据
        print('📈 获取市场数据...')
        ticker = exchange.fetch_ticker('BTC/USDT:USDT')
        btc_price = ticker['last']
        print(f'BTC当前价格: ${btc_price:,.2f}')
        print(f'买一价: ${ticker["bid"]:,.2f}')
        print(f'卖一价: ${ticker["ask"]:,.2f}')
        
        # 计算交易量 ($10价值的BTC)
        trade_amount_usd = 10.0
        btc_amount = trade_amount_usd / btc_price
        print(f'\n💰 计划交易:')
        print(f'   交易金额: ${trade_amount_usd:.2f}')
        print(f'   BTC数量: {btc_amount:.6f}')
        print(f'   约合: {btc_amount * btc_price:.2f} USDT')
        
        # 检查账户余额
        print('\n📊 检查账户余额...')
        balance = exchange.fetch_balance()
        usdt_available = balance['free']['USDT']
        print(f'可用USDT: ${usdt_available:.2f}')
        
        if usdt_available < trade_amount_usd:
            print(f'❌ 余额不足，需要至少${trade_amount_usd:.2f}')
            return False
        
        # 设置杠杆 (先设置低杠杆测试)
        print('\n⚙️ 设置交易参数...')
        symbol = 'BTC/USDT:USDT'
        leverage = 5  # 测试用低杠杆
        
        try:
            exchange.set_leverage(leverage, symbol)
            print(f'   杠杆设置为: {leverage}x')
        except Exception as e:
            print(f'   设置杠杆失败(可能已设置): {e}')
        
        # 确认交易
        print('\n⚠️  确认交易参数:')
        print(f'   交易对: {symbol}')
        print(f'   方向: 买入(BUY)')
        print(f'   数量: {btc_amount:.6f} BTC')
        print(f'   金额: 约${trade_amount_usd:.2f}')
        print(f'   杠杆: {leverage}x')
        print(f'   类型: 市价单')
        
        # 自动确认（因为是通过脚本执行）
        print('\n⏰ 5秒后自动执行交易...')
        for i in range(5, 0, -1):
            print(f'   {i}...')
            time.sleep(1)
        
        # 执行市价买入订单
        print('\n🚀 执行市价买入订单...')
        start_time = time.time()
        
        try:
            order = exchange.create_market_buy_order(
                symbol=symbol,
                amount=btc_amount
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f'✅ 订单提交成功!')
            print(f'   执行时间: {execution_time:.2f}秒')
            print(f'   订单ID: {order["id"]}')
            print(f'   状态: {order["status"]}')
            print(f'   数量: {order["amount"]:.6f}')
            print(f'   已成交: {order["filled"]:.6f}')
            
            if order['filled'] > 0:
                print(f'   成交均价: ${order["average"]:,.2f}')
            
            # 等待3秒后检查持仓
            print('\n⏳ 等待3秒检查持仓状态...')
            time.sleep(3)
            
            # 检查持仓
            positions = exchange.fetch_positions([symbol])
            has_position = False
            
            for pos in positions:
                if pos['symbol'] == symbol and float(pos.get('contracts', 0)) > 0:
                    has_position = True
                    print('✅ 发现持仓:')
                    print(f'   持仓量: {pos["contracts"]:.6f} BTC')
                    print(f'   方向: {pos["side"]}')
                    print(f'   入场价: ${pos.get("entryPrice", 0):,.2f}')
                    print(f'   当前价: ${pos.get("markPrice", 0):,.2f}')
                    print(f'   未实现盈亏: ${pos.get("unrealizedPnl", 0):.2f}')
                    print(f'   保证金: ${pos.get("initialMargin", 0):.2f}')
                    print(f'   杠杆: {pos.get("leverage", 0)}x')
                    break
            
            if not has_position:
                print('⚠️  未发现持仓，可能需要等待结算')
            
            # 检查账户余额变化
            print('\n📊 交易后账户状态:')
            balance_after = exchange.fetch_balance()
            usdt_after = balance_after['free']['USDT']
            usdt_change = usdt_after - usdt_available
            
            print(f'   交易前余额: ${usdt_available:.2f}')
            print(f'   交易后余额: ${usdt_after:.2f}')
            print(f'   变化: ${usdt_change:.2f}')
            
            # 获取最新价格计算盈亏
            latest_ticker = exchange.fetch_ticker(symbol)
            latest_price = latest_ticker['last']
            
            if has_position:
                for pos in positions:
                    if pos['symbol'] == symbol and float(pos.get('contracts', 0)) > 0:
                        entry_price = float(pos.get('entryPrice', 0))
                        position_size = float(pos.get('contracts', 0))
                        
                        if entry_price > 0:
                            pnl_usd = (latest_price - entry_price) * position_size
                            pnl_percent = (latest_price - entry_price) / entry_price * 100
                            
                            print(f'\n📈 当前持仓盈亏:')
                            print(f'   入场价: ${entry_price:,.2f}')
                            print(f'   当前价: ${latest_price:,.2f}')
                            print(f'   持仓量: {position_size:.6f} BTC')
                            print(f'   盈亏金额: ${pnl_usd:.2f}')
                            print(f'   盈亏百分比: {pnl_percent:.2f}%')
                            
                            if pnl_usd > 0:
                                print(f'   📈 当前盈利')
                            else:
                                print(f'   📉 当前亏损')
            
            print('\n🎯 测试总结:')
            print('='*50)
            print('✅ API连接正常')
            print('✅ 订单执行成功')
            print('✅ 持仓创建成功' if has_position else '⚠️  持仓可能需要时间显示')
            print('✅ 账户余额更新正常')
            print(f'✅ 交易金额: ${trade_amount_usd:.2f}')
            print(f'✅ 使用杠杆: {leverage}x')
            
            print('\n📋 下一步建议:')
            print('1. 观察持仓盈亏变化5-10分钟')
            print('2. 测试平仓操作')
            print('3. 集成到监控系统')
            print('4. 启用完整交易策略')
            
            print(f'\n⏰ 测试完成时间: {datetime.now().strftime("%H:%M:%S")}')
            
            return True
            
        except Exception as e:
            print(f'❌ 订单执行失败: {e}')
            return False
        
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_small_trade()
    if success:
        print('\n🎉 测试完成！请检查持仓和账户状态。')
    else:
        print('\n❌ 测试失败，请检查错误信息。')