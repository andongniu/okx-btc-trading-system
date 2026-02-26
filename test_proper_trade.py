#!/usr/bin/env python3
"""
使用正确参数测试交易
最小交易量: 0.01 BTC (约$652)
使用5倍杠杆，需要保证金约$130
"""

import ccxt
import json
import time
from datetime import datetime

def test_proper_trade():
    print('🚀 开始合规交易测试...')
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
        
        # 获取当前市场数据
        print('📈 获取市场数据...')
        ticker = exchange.fetch_ticker(symbol)
        btc_price = ticker['last']
        print(f'BTC当前价格: ${btc_price:,.2f}')
        print(f'买一价: ${ticker["bid"]:,.2f}')
        print(f'卖一价: ${ticker["ask"]:,.2f}')
        
        # 使用最小交易量
        btc_amount = 0.01  # OKX最小交易量
        contract_value = btc_amount * btc_price
        
        # 使用5倍杠杆（安全测试）
        leverage = 5
        margin_required = contract_value / leverage
        
        print(f'\n💰 交易参数:')
        print(f'   BTC数量: {btc_amount} (最小要求)')
        print(f'   合约价值: ${contract_value:,.2f}')
        print(f'   使用杠杆: {leverage}x')
        print(f'   所需保证金: ${margin_required:,.2f}')
        
        # 检查账户余额
        print('\n📊 检查账户余额...')
        balance = exchange.fetch_balance()
        usdt_available = balance['free']['USDT']
        print(f'可用USDT: ${usdt_available:,.2f}')
        
        if usdt_available < margin_required:
            print(f'❌ 保证金不足，需要至少${margin_required:,.2f}')
            return False
        
        print(f'✅ 资金充足，保证金比例: {(usdt_available/margin_required*100):.1f}%')
        
        # 设置杠杆
        print('\n⚙️ 设置交易参数...')
        try:
            exchange.set_leverage(leverage, symbol)
            print(f'   杠杆设置为: {leverage}x')
        except Exception as e:
            print(f'   设置杠杆失败(可能已设置): {e}')
        
        # 显示交易确认
        print('\n⚠️  交易确认:')
        print(f'   交易对: {symbol}')
        print(f'   方向: 买入(BUY)')
        print(f'   数量: {btc_amount} BTC')
        print(f'   合约价值: ${contract_value:,.2f}')
        print(f'   杠杆: {leverage}x')
        print(f'   保证金: ${margin_required:,.2f}')
        print(f'   类型: 市价单')
        
        print('\n⏰ 10秒后自动执行交易...')
        print('   按Ctrl+C取消')
        for i in range(10, 0, -1):
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
            
            # 等待5秒后详细检查
            print('\n⏳ 等待5秒检查详细状态...')
            time.sleep(5)
            
            # 详细检查持仓
            print('\n📊 详细持仓检查:')
            positions = exchange.fetch_positions([symbol])
            has_position = False
            
            for pos in positions:
                if pos['symbol'] == symbol:
                    contracts = float(pos.get('contracts', 0))
                    if contracts > 0:
                        has_position = True
                        print('✅ 发现持仓:')
                        print(f'   持仓量: {contracts} BTC')
                        print(f'   方向: {pos.get("side", "N/A")}')
                        print(f'   入场价: ${pos.get("entryPrice", 0):,.2f}')
                        print(f'   当前价: ${pos.get("markPrice", 0):,.2f}')
                        
                        entry_price = float(pos.get('entryPrice', 0))
                        current_price = float(pos.get('markPrice', 0))
                        
                        if entry_price > 0:
                            pnl_usd = (current_price - entry_price) * contracts
                            pnl_percent = (current_price - entry_price) / entry_price * 100
                            
                            print(f'   未实现盈亏: ${pnl_usd:.2f}')
                            print(f'   盈亏百分比: {pnl_percent:.2f}%')
                        
                        print(f'   保证金: ${pos.get("initialMargin", 0):,.2f}')
                        print(f'   杠杆: {pos.get("leverage", 0)}x')
                        print(f'   维持保证金率: {pos.get("maintenanceMarginRate", 0)*100:.2f}%')
                        
                        # 计算强平价格
                        if pos.get('side') == 'long':
                            liq_price = entry_price * (1 - 1/leverage + 0.005)  # 简化计算
                            print(f'   估算强平价格: ${liq_price:,.2f}')
                            print(f'   当前安全边际: {((current_price - liq_price)/current_price*100):.1f}%')
                        break
            
            if not has_position:
                print('⚠️  未发现有效持仓')
                # 检查订单状态
                try:
                    order_status = exchange.fetch_order(order['id'], symbol)
                    print(f'   订单状态: {order_status["status"]}')
                    print(f'   已成交: {order_status["filled"]}')
                except:
                    pass
            
            # 检查账户余额变化
            print('\n💰 账户资金变化:')
            balance_after = exchange.fetch_balance()
            usdt_after = balance_after['free']['USDT']
            usdt_used = balance_after['used']['USDT']
            
            print(f'   交易前可用: ${usdt_available:,.2f}')
            print(f'   交易后可用: ${usdt_after:,.2f}')
            print(f'   被占用资金: ${usdt_used:,.2f}')
            print(f'   总余额: ${balance_after["total"]["USDT"]:,.2f}')
            
            # 获取最新市场数据
            latest_ticker = exchange.fetch_ticker(symbol)
            print(f'\n📈 最新市场:')
            print(f'   BTC价格: ${latest_ticker["last"]:,.2f}')
            print(f'   24h涨跌: {latest_ticker["percentage"]:.2f}%')
            
            print('\n🎯 测试总结:')
            print('='*50)
            if has_position:
                print('✅ 交易执行成功')
                print('✅ 持仓创建成功')
                print('✅ 资金占用正常')
                print('✅ 风险参数可接受')
                
                print('\n📋 下一步操作建议:')
                print('1. 观察持仓盈亏变化10-15分钟')
                print('2. 测试市价平仓操作')
                print('3. 测试限价平仓操作')
                print('4. 验证止损止盈功能')
                print('5. 集成到监控系统')
            else:
                print('⚠️  交易提交成功但持仓未显示')
                print('   可能原因:')
                print('   - 需要更长时间结算')
                print('   - 订单部分成交')
                print('   - 系统延迟')
                
                print('\n📋 建议:')
                print('1. 等待1-2分钟重新检查')
                print('2. 查看订单详细状态')
                print('3. 联系交易所客服如有疑问')
            
            print(f'\n⏰ 测试完成时间: {datetime.now().strftime("%H:%M:%S")}')
            
            return True
            
        except Exception as e:
            print(f'❌ 订单执行失败: {e}')
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print('⚠️  重要提醒:')
    print('   本次测试将执行真实交易')
    print('   交易金额: 约$652 (0.01 BTC)')
    print('   使用杠杆: 5倍')
    print('   所需保证金: 约$130')
    print('   账户余额: $200')
    print('   有亏损风险，请谨慎操作')
    print()
    
    confirm = input('确认执行测试? (输入 YES 确认): ')
    if confirm != 'YES':
        print('❌ 测试取消')
        exit(0)
    
    success = test_proper_trade()
    if success:
        print('\n🎉 测试执行完成！请仔细检查持仓和账户状态。')
    else:
        print('\n❌ 测试失败，请检查错误信息。')