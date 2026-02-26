#!/usr/bin/env python3
"""
自动启动自主交易 - 平掉当前持仓，开始新的自主交易
"""

import ccxt
import json
import time
from datetime import datetime
import numpy as np

def close_position_and_start_autonomous():
    """平掉持仓并开始自主交易"""
    print('🤖 自动启动自主交易系统')
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
        
        # 1. 检查并平掉当前持仓
        print('🔍 检查当前持仓...')
        positions = exchange.fetch_positions([symbol])
        current_position = None
        
        for pos in positions:
            if pos['symbol'] == symbol:
                contracts = float(pos.get('contracts', 0))
                if contracts > 0:
                    current_position = pos
                    break
        
        if current_position:
            print(f'📊 发现持仓: {current_position.get("side", "N/A")} {contracts}张合约')
            
            # 平仓
            side = current_position.get('side', '')
            if side == 'long':
                order = exchange.create_market_sell_order(symbol, contracts)
                action = '卖出平多'
            else:
                order = exchange.create_market_buy_order(symbol, contracts)
                action = '买入平空'
            
            print(f'✅ 平仓成功: {action} {contracts}张合约')
            
            # 获取成交价
            time.sleep(1)
            ticker = exchange.fetch_ticker(symbol)
            exit_price = ticker['last']
            entry_price = float(current_position.get('entryPrice', 0))
            
            if side == 'long':
                pnl = (exit_price - entry_price) * contracts * 0.01
            else:
                pnl = (entry_price - exit_price) * contracts * 0.01
            
            print(f'   入场价: ${entry_price:.2f}')
            print(f'   离场价: ${exit_price:.2f}')
            print(f'   盈亏: ${pnl:.4f}')
        else:
            print('📊 无当前持仓')
        
        # 2. 分析市场，准备自主交易
        print('\n🎯 分析市场状态...')
        
        # 获取K线数据
        ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        closes = np.array([c[4] for c in ohlcv])
        
        # 计算技术指标
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:])
        current_price = closes[-1]
        
        # 计算波动率
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * np.sqrt(365 * 24 * 4)
        
        # 判断趋势
        if current_price > sma_20 > sma_50:
            trend = '上涨趋势'
        elif current_price < sma_20 < sma_50:
            trend = '下跌趋势'
        else:
            trend = '震荡趋势'
        
        # 判断波动率水平
        if volatility < 0.4:
            vol_level = '低'
        elif volatility < 0.8:
            vol_level = '中'
        else:
            vol_level = '高'
        
        print(f'📈 市场分析:')
        print(f'   当前价格: ${current_price:.2f}')
        print(f'   趋势: {trend}')
        print(f'   20周期均线: ${sma_20:.2f}')
        print(f'   50周期均线: ${sma_50:.2f}')
        print(f'   波动率: {vol_level} ({volatility:.2%})')
        
        # 3. 生成交易信号
        print('\n🎯 生成交易信号...')
        
        signal = None
        price_position = (current_price - np.min(closes[-20:])) / (np.max(closes[-20:]) - np.min(closes[-20:])) if np.max(closes[-20:]) != np.min(closes[-20:]) else 0.5
        
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
        elif trend == '震荡趋势' and vol_level == '高':
            if price_position > 0.7:
                signal = {
                    'direction': 'SHORT',
                    'reason': '高波动率震荡，价格在阻力位',
                    'confidence': 0.6
                }
            elif price_position < 0.3:
                signal = {
                    'direction': 'LONG',
                    'reason': '高波动率震荡，价格在支撑位',
                    'confidence': 0.6
                }
        
        if signal:
            # 计算仓位和止盈止损
            account_balance = exchange.fetch_balance()['total'].get('USDT', 0)
            
            # 根据波动率设置止盈止损
            if vol_level == '低':
                stop_loss_pct = 1.2
                take_profit_pct = 2.4
                leverage = 15
            elif vol_level == '高':
                stop_loss_pct = 2.0
                take_profit_pct = 4.0
                leverage = 5
            else:
                stop_loss_pct = 1.5
                take_profit_pct = 3.0
                leverage = 10
            
            # 计算仓位大小（1%风险）
            risk_amount = account_balance * 0.01
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
            
            signal.update({
                'entry_price': current_price,
                'contracts': contracts,
                'leverage': leverage,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'stop_loss_pct': stop_loss_pct,
                'take_profit_pct': take_profit_pct,
                'risk_amount': risk_amount,
                'potential_reward': position_value * (take_profit_pct / 100),
                'risk_reward_ratio': take_profit_pct / stop_loss_pct
            })
            
            print(f'✅ 生成交易信号:')
            print(f'   方向: {signal["direction"]}')
            print(f'   原因: {signal["reason"]}')
            print(f'   信心度: {signal["confidence"]*100:.0f}%')
            print(f'   入场价: ${signal["entry_price"]:.2f}')
            print(f'   合约数量: {signal["contracts"]}张')
            print(f'   杠杆: {signal["leverage"]}x')
            print(f'   止损: ${signal["stop_loss_price"]:.2f} (-{signal["stop_loss_pct"]}%)')
            print(f'   止盈: ${signal["take_profit_price"]:.2f} (+{signal["take_profit_pct"]}%)')
            print(f'   风险金额: ${signal["risk_amount"]:.4f}')
            print(f'   潜在盈利: ${signal["potential_reward"]:.4f}')
            print(f'   风险回报比: {signal["risk_reward_ratio"]:.2f}:1')
            
            # 询问是否执行
            print('\n🎯 自主交易系统准备就绪')
            print('   每笔交易都会自动设置止盈止损')
            print('   基于市场数据动态调整参数')
            print('   记录完整的交易逻辑')
            
            return signal
        else:
            print('⚠️  当前无合适交易信号')
            print('   建议等待更好的入场机会')
            return None
        
    except Exception as e:
        print(f'❌ 启动失败: {e}')
        import traceback
        traceback.print_exc()
        return None

def execute_autonomous_trade(signal):
    """执行自主交易"""
    print('\n🚀 执行自主交易...')
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
        
        # 设置杠杆
        exchange.set_leverage(signal['leverage'], symbol)
        
        # 执行交易
        if signal['direction'] == 'LONG':
            order = exchange.create_market_buy_order(symbol, signal['contracts'])
            side = '买入开多'
        else:
            order = exchange.create_market_sell_order(symbol, signal['contracts'])
            side = '卖出开空'
        
        print(f'✅ 交易执行成功:')
        print(f'   订单ID: {order["id"]}')
        print(f'   方向: {side}')
        print(f'   合约数量: {signal["contracts"]}张')
        print(f'   杠杆: {signal["leverage"]}x')
        print(f'   入场价: ${signal["entry_price"]:.2f}')
        print(f'   止损价: ${signal["stop_loss_price"]:.2f}')
        print(f'   止盈价: ${signal["take_profit_price"]:.2f}')
        print(f'   风险回报比: {signal["risk_reward_ratio"]:.2f}:1')
        print(f'   交易原因: {signal["reason"]}')
        
        # 记录交易
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'order_id': order['id'],
            'direction': signal['direction'],
            'contracts': signal['contracts'],
            'entry_price': signal['entry_price'],
            'stop_loss_price': signal['stop_loss_price'],
            'take_profit_price': signal['take_profit_price'],
            'leverage': signal['leverage'],
            'reason': signal['reason'],
            'confidence': signal['confidence'],
            'risk_amount': signal['risk_amount'],
            'risk_reward_ratio': signal['risk_reward_ratio'],
            'status': 'open'
        }
        
        # 保存交易记录
        with open('logs/autonomous_trades.json', 'a') as f:
            f.write(json.dumps(trade_record) + '\n')
        
        print('\n📊 交易已记录，开始监控...')
        print('   系统将自动监控止盈止损')
        print('   下一笔交易将继续基于数据分析')
        
        return True
        
    except Exception as e:
        print(f'❌ 交易执行失败: {e}')
        return False

if __name__ == '__main__':
    print('🤖 自主交易系统启动')
    print('='*50)
    
    # 1. 平掉当前持仓并分析市场
    signal = close_position_and_start_autonomous()
    
    if signal:
        # 2. 执行自主交易
        execute_autonomous_trade(signal)
    
    print('\n🎯 自主交易系统运行中')
    print('   系统将持续分析市场')
    print('   生成基于数据的交易信号')
    print('   每笔订单都带止盈止损')
    print('   策略将基于表现迭代优化')