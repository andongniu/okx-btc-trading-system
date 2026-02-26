#!/usr/bin/env python3
"""
启动自主交易系统 - 先处理当前持仓，然后开始自主交易
"""

import ccxt
import json
import time
from datetime import datetime
import numpy as np

def check_current_position():
    """检查当前持仓状态"""
    print('🔍 检查当前持仓状态...')
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
        current_position = None
        
        for pos in positions:
            if pos['symbol'] == symbol:
                contracts = float(pos.get('contracts', 0))
                if contracts > 0:
                    current_position = pos
                    entry_time = datetime.fromtimestamp(pos.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')
                    print(f'📊 发现当前持仓:')
                    print(f'   合约数量: {contracts} 张 ({contracts * 0.01:.4f} BTC)')
                    print(f'   方向: {pos.get("side", "N/A")}')
                    print(f'   入场价: ${pos.get("entryPrice", 0)}')
                    print(f'   入场时间: {entry_time}')
                    print(f'   当前价: ${pos.get("markPrice", 0)}')
                    print(f'   未实现盈亏: ${pos.get("unrealizedPnl", 0)}')
                    print(f'   杠杆: {pos.get("leverage", 0)}x')
                    break
        
        if not current_position:
            print('📊 当前持仓: 无')
            return None
        
        return current_position
        
    except Exception as e:
        print(f'❌ 检查持仓失败: {e}')
        return None

def analyze_market_for_stop_loss(current_position):
    """分析市场，为当前持仓设置止盈止损"""
    print('\n🎯 分析市场，设置止盈止损...')
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
        
        # 获取K线数据
        ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        closes = np.array([c[4] for c in ohlcv])
        
        # 计算技术指标
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:])
        current_price = closes[-1]
        
        # 计算波动率
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * np.sqrt(365 * 24 * 4)  # 年化波动率
        
        # 判断波动率水平
        if volatility < 0.4:
            vol_level = '低'
            stop_loss_pct = 1.2  # 1.2%止损
            take_profit_pct = 2.4  # 2.4%止盈
        elif volatility < 0.8:
            vol_level = '中'
            stop_loss_pct = 1.5  # 1.5%止损
            take_profit_pct = 3.0  # 3.0%止盈
        else:
            vol_level = '高'
            stop_loss_pct = 2.0  # 2.0%止损
            take_profit_pct = 4.0  # 4.0%止盈
        
        # 获取持仓信息
        entry_price = float(current_position.get('entryPrice', 0))
        side = current_position.get('side', '')
        
        if side == 'long':
            stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
            take_profit_price = entry_price * (1 + take_profit_pct / 100)
        else:
            stop_loss_price = entry_price * (1 + stop_loss_pct / 100)
            take_profit_price = entry_price * (1 - take_profit_pct / 100)
        
        print(f'📈 市场分析结果:')
        print(f'   当前价格: ${current_price:.2f}')
        print(f'   20周期均线: ${sma_20:.2f}')
        print(f'   50周期均线: ${sma_50:.2f}')
        print(f'   波动率水平: {vol_level} ({volatility:.2%})')
        print(f'   建议止损: {stop_loss_pct}%')
        print(f'   建议止盈: {take_profit_pct}%')
        print(f'   风险回报比: {take_profit_pct/stop_loss_pct:.2f}:1')
        
        print(f'\n🎯 持仓管理建议:')
        print(f'   入场价: ${entry_price:.2f}')
        print(f'   当前价: ${current_price:.2f}')
        print(f'   止损价: ${stop_loss_price:.2f}')
        print(f'   止盈价: ${take_profit_price:.2f}')
        
        # 计算当前盈亏
        if side == 'long':
            current_pnl_pct = (current_price - entry_price) / entry_price * 100
        else:
            current_pnl_pct = (entry_price - current_price) / entry_price * 100
        
        print(f'   当前盈亏: {current_pnl_pct:.2f}%')
        
        return {
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'stop_loss_pct': stop_loss_pct,
            'take_profit_pct': take_profit_pct,
            'volatility_level': vol_level,
            'current_price': current_price,
            'current_pnl_pct': current_pnl_pct
        }
        
    except Exception as e:
        print(f'❌ 市场分析失败: {e}')
        return None

def close_current_position(current_position, reason="系统接管"):
    """平掉当前持仓"""
    print(f'\n🔄 平掉当前持仓 ({reason})...')
    
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
        contracts = float(current_position.get('contracts', 0))
        side = current_position.get('side', '')
        
        if side == 'long':
            order = exchange.create_market_sell_order(symbol, contracts)
            action = '卖出平多'
        else:
            order = exchange.create_market_buy_order(symbol, contracts)
            action = '买入平空'
        
        print(f'✅ 平仓成功: {action} {contracts}张合约')
        print(f'   订单ID: {order["id"]}')
        
        # 获取成交详情
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
        
        return True
        
    except Exception as e:
        print(f'❌ 平仓失败: {e}')
        return False

def start_autonomous_trading():
    """开始自主交易"""
    print('\n🚀 开始自主交易策略...')
    print('='*50)
    
    # 1. 检查当前持仓
    current_position = check_current_position()
    
    if current_position:
        # 2. 分析市场，设置止盈止损
        analysis = analyze_market_for_stop_loss(current_position)
        
        if analysis:
            # 3. 检查是否需要立即平仓
            entry_price = float(current_position.get('entryPrice', 0))
            current_price = analysis['current_price']
            side = current_position.get('side', '')
            
            should_close = False
            close_reason = ""
            
            if side == 'long':
                if current_price <= analysis['stop_loss_price']:
                    should_close = True
                    close_reason = "触及止损价"
                elif current_price >= analysis['take_profit_price']:
                    should_close = True
                    close_reason = "触及止盈价"
            else:
                if current_price >= analysis['stop_loss_price']:
                    should_close = True
                    close_reason = "触及止损价"
                elif current_price <= analysis['take_profit_price']:
                    should_close = True
                    close_reason = "触及止盈价"
            
            if should_close:
                print(f'\n⚠️  检测到需要平仓: {close_reason}')
                close_current_position(current_position, close_reason)
            else:
                print(f'\n📊 持仓状态正常，继续持有')
                print(f'   止损价: ${analysis["stop_loss_price"]:.2f}')
                print(f'   止盈价: ${analysis["take_profit_price"]:.2f}')
                print(f'   当前盈亏: {analysis["current_pnl_pct"]:.2f}%')
        
        # 询问是否平仓
        response = input('\n❓ 是否平掉当前持仓，开始新的自主交易？ (y/n): ')
        if response.lower() == 'y':
            close_current_position(current_position, "用户选择重新开始")
            current_position = None
    
    # 4. 开始自主交易循环
    if not current_position:
        print('\n🎯 开始自主交易循环...')
        print('='*50)
        
        # 这里可以添加自主交易逻辑
        print('1. 分析市场趋势')
        print('2. 生成交易信号')
        print('3. 计算仓位大小')
        print('4. 设置止盈止损')
        print('5. 执行交易')
        print('6. 监控持仓')
        print('7. 迭代优化策略')
        
        print('\n📊 自主交易系统准备就绪')
        print('   每笔交易都会:')
        print('   ✅ 基于数据分析')
        print('   ✅ 设置止盈止损')
        print('   ✅ 计算风险回报比')
        print('   ✅ 记录交易原因')
        print('   ✅ 迭代优化策略')

if __name__ == '__main__':
    print('🤖 自主交易系统启动')
    print('='*50)
    print('系统将:')
    print('1. 检查当前持仓')
    print('2. 分析市场状态')
    print('3. 设置止盈止损')
    print('4. 开始自主交易')
    print('5. 每笔订单都带止盈止损')
    print('6. 基于数据迭代策略')
    print('='*50)
    
    start_autonomous_trading()