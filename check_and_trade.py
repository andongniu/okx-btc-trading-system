#!/usr/bin/env python3
"""
检查状态并执行自主交易
"""

import ccxt
import json
import numpy as np
from datetime import datetime

def check_and_trade():
    print('🔍 检查当前状态并执行自主交易...')
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
        
        # 1. 检查账户余额
        balance = exchange.fetch_balance()
        total = balance['total'].get('USDT', 0)
        free = balance['free'].get('USDT', 0)
        print(f'💰 账户余额:')
        print(f'   总额: ${total:.2f}')
        print(f'   可用: ${free:.2f}')
        
        # 2. 检查持仓
        positions = exchange.fetch_positions([symbol])
        has_position = False
        for pos in positions:
            if pos['symbol'] == symbol:
                contracts = float(pos.get('contracts', 0))
                if contracts > 0:
                    has_position = True
                    print(f'📊 当前持仓: {contracts}张合约')
                    break
        
        if not has_position:
            print('📊 当前持仓: 无')
        
        # 3. 分析市场
        print('\n🎯 分析市场...')
        ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        closes = np.array([c[4] for c in ohlcv])
        
        # 计算技术指标
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:])
        current_price = closes[-1]
        
        # 计算支撑阻力
        support = np.min(closes[-20:])
        resistance = np.max(closes[-20:])
        price_position = (current_price - support) / (resistance - support) if resistance != support else 0.5
        
        print(f'📈 市场分析:')
        print(f'   当前价格: ${current_price:.2f}')
        print(f'   20周期均线: ${sma_20:.2f}')
        print(f'   50周期均线: ${sma_50:.2f}')
        print(f'   支撑位: ${support:.2f}')
        print(f'   阻力位: ${resistance:.2f}')
        print(f'   价格位置: {price_position:.2%}')
        
        # 4. 判断趋势
        if current_price > sma_20 > sma_50:
            trend = '上涨趋势'
            print(f'📈 趋势: {trend}')
        elif current_price < sma_20 < sma_50:
            trend = '下跌趋势'
            print(f'📉 趋势: {trend}')
        else:
            trend = '震荡趋势'
            print(f'🔄 趋势: {trend}')
        
        # 5. 生成交易信号
        print('\n🎯 生成交易信号...')
        signal = None
        
        if trend == '上涨趋势' and price_position < 0.3:
            signal = {
                'direction': 'LONG',
                'reason': '上涨趋势，价格接近支撑位',
                'confidence': 0.7
            }
        elif trend == '下跌趋势' and price_position > 0.7:
            signal = {
                'direction': 'SHORT',
                'reason': '下跌趋势，价格接近阻力位',
                'confidence': 0.7
            }
        elif trend == '震荡趋势' and price_position > 0.7:
            signal = {
                'direction': 'SHORT',
                'reason': '震荡行情，价格在阻力位',
                'confidence': 0.6
            }
        elif trend == '震荡趋势' and price_position < 0.3:
            signal = {
                'direction': 'LONG',
                'reason': '震荡行情，价格在支撑位',
                'confidence': 0.6
            }
        
        if signal:
            print(f'✅ 生成信号: {signal["direction"]}')
            print(f'   原因: {signal["reason"]}')
            print(f'   信心度: {signal["confidence"]*100:.0f}%')
            
            # 6. 执行交易
            print('\n🚀 执行交易...')
            
            # 计算波动率
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns) * np.sqrt(365 * 24 * 4)
            
            # 根据波动率设置参数
            if volatility < 0.4:
                vol_level = '低'
                stop_loss_pct = 1.2
                take_profit_pct = 2.4
                leverage = 15
            elif volatility < 0.8:
                vol_level = '中'
                stop_loss_pct = 1.5
                take_profit_pct = 3.0
                leverage = 10
            else:
                vol_level = '高'
                stop_loss_pct = 2.0
                take_profit_pct = 4.0
                leverage = 5
            
            print(f'📊 波动率: {vol_level} ({volatility:.2%})')
            print(f'🛡️  止损: {stop_loss_pct}%')
            print(f'🎯 止盈: {take_profit_pct}%')
            print(f'⚖️  杠杆: {leverage}x')
            
            # 计算仓位大小（1%风险）
            risk_amount = total * 0.01
            position_value = risk_amount / (stop_loss_pct / 100)
            contracts = position_value / (current_price * 0.01)
            
            # 限制仓位大小
            contracts = max(0.01, min(contracts, 0.1))
            contracts = round(contracts * 100) / 100
            
            # 计算止盈止损价格
            if signal['direction'] == 'LONG':
                stop_loss_price = current_price * (1 - stop_loss_pct / 100)
                take_profit_price = current_price * (1 + take_profit_pct / 100)
            else:
                stop_loss_price = current_price * (1 + stop_loss_pct / 100)
                take_profit_price = current_price * (1 - take_profit_pct / 100)
            
            print(f'\n📊 交易详情:')
            print(f'   方向: {signal["direction"]}')
            print(f'   合约数量: {contracts}张')
            print(f'   入场价: ${current_price:.2f}')
            print(f'   止损价: ${stop_loss_price:.2f}')
            print(f'   止盈价: ${take_profit_price:.2f}')
            print(f'   风险金额: ${risk_amount:.4f}')
            print(f'   风险回报比: {take_profit_pct/stop_loss_pct:.2f}:1')
            
            # 询问是否执行
            response = input('\n❓ 是否执行此交易？ (y/n): ')
            if response.lower() == 'y':
                # 设置杠杆
                exchange.set_leverage(leverage, symbol)
                
                # 执行交易
                if signal['direction'] == 'LONG':
                    order = exchange.create_market_buy_order(symbol, contracts)
                    side = '买入开多'
                else:
                    order = exchange.create_market_sell_order(symbol, contracts)
                    side = '卖出开空'
                
                print(f'\n✅ 交易执行成功:')
                print(f'   订单ID: {order["id"]}')
                print(f'   方向: {side}')
                print(f'   合约数量: {contracts}张')
                
                # 记录交易
                trade_record = {
                    'timestamp': datetime.now().isoformat(),
                    'order_id': order['id'],
                    'direction': signal['direction'],
                    'contracts': contracts,
                    'entry_price': current_price,
                    'stop_loss_price': stop_loss_price,
                    'take_profit_price': take_profit_price,
                    'leverage': leverage,
                    'reason': signal['reason'],
                    'confidence': signal['confidence'],
                    'risk_amount': risk_amount,
                    'risk_reward_ratio': take_profit_pct / stop_loss_pct,
                    'status': 'open'
                }
                
                # 保存交易记录
                with open('logs/autonomous_trades.json', 'a') as f:
                    f.write(json.dumps(trade_record) + '\n')
                
                print(f'📝 交易已记录到日志')
                print(f'🌐 请在监控面板查看: http://localhost:8083')
                
            else:
                print('❌ 交易取消')
                
        else:
            print('⚠️  当前无合适交易信号')
            print(f'   条件: 趋势={trend}, 价格位置={price_position:.2%}')
            print('   建议等待更好的入场机会')
            print('🌐 监控面板: http://localhost:8083')
        
        return signal is not None
        
    except Exception as e:
        print(f'❌ 检查失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = check_and_trade()
    if success:
        print('\n🎯 自主交易系统运行中')
        print('   请访问监控面板观察交易')
    else:
        print('\n🔄 系统等待交易机会')
        print('   监控面板将持续更新')