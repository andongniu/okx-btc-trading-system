#!/usr/bin/env python3
"""
分析完整交易历史，计算盈亏和策略信息
"""

import ccxt
import json
from datetime import datetime
from collections import defaultdict

def analyze_trade_history():
    print('📊 完整交易历史分析')
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
        
        # 获取所有成交记录
        print('💰 获取所有成交记录...')
        trades = exchange.fetch_my_trades(symbol, limit=50)
        print(f'   找到 {len(trades)} 笔成交')
        
        if len(trades) < 3:
            print('⚠️  交易记录不足，需要至少3笔交易进行分析')
            return
        
        # 按时间排序
        trades.sort(key=lambda x: x['timestamp'])
        
        print('\n📅 完整交易时间线:')
        print('='*40)
        
        # 分析交易对
        trade_pairs = []
        i = 0
        while i < len(trades):
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]
                
                if buy_trade['side'] == 'buy' and sell_trade['side'] == 'sell':
                    # 计算盈亏
                    entry_price = buy_trade['price']
                    exit_price = sell_trade['price']
                    amount = buy_trade['amount']
                    
                    # 盈亏计算 (合约乘数: 1张 = 0.01 BTC)
                    pnl = (exit_price - entry_price) * amount * 0.01
                    pnl_percent = ((exit_price - entry_price) / entry_price) * 100
                    
                    # 计算持仓时间
                    entry_time = datetime.fromtimestamp(buy_trade['timestamp']/1000)
                    exit_time = datetime.fromtimestamp(sell_trade['timestamp']/1000)
                    hold_time = exit_time - entry_time
                    
                    trade_pair = {
                        'entry_time': entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'exit_time': exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'hold_time': str(hold_time),
                        'direction': 'LONG',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'amount': amount,
                        'btc_amount': amount * 0.01,
                        'pnl': pnl,
                        'pnl_percent': pnl_percent,
                        'entry_order_id': buy_trade.get('order', 'N/A'),
                        'exit_order_id': sell_trade.get('order', 'N/A'),
                        'entry_fee': buy_trade.get('fee', {}).get('cost', 0),
                        'exit_fee': sell_trade.get('fee', {}).get('cost', 0),
                        'total_fee': buy_trade.get('fee', {}).get('cost', 0) + sell_trade.get('fee', {}).get('cost', 0),
                        'net_pnl': pnl - (buy_trade.get('fee', {}).get('cost', 0) + sell_trade.get('fee', {}).get('cost', 0))
                    }
                    
                    trade_pairs.append(trade_pair)
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        
        # 显示交易对分析
        if trade_pairs:
            print(f'\n✅ 找到 {len(trade_pairs)} 个完整交易对:')
            
            for idx, pair in enumerate(trade_pairs, 1):
                print(f'\n📈 交易对 #{idx}:')
                print(f'   入场时间: {pair["entry_time"]}')
                print(f'   离场时间: {pair["exit_time"]}')
                print(f'   持仓时间: {pair["hold_time"]}')
                print(f'   方向: {pair["direction"]}')
                print(f'   入场价: ${pair["entry_price"]:.2f}')
                print(f'   离场价: ${pair["exit_price"]:.2f}')
                print(f'   合约数量: {pair["amount"]}张 ({pair["btc_amount"]:.4f} BTC)')
                print(f'   价格变化: {pair["pnl_percent"]:.2f}%')
                print(f'   毛盈亏: ${pair["pnl"]:.4f}')
                print(f'   入场手续费: ${pair["entry_fee"]:.6f}')
                print(f'   离场手续费: ${pair["exit_fee"]:.6f}')
                print(f'   总手续费: ${pair["total_fee"]:.6f}')
                print(f'   净盈亏: ${pair["net_pnl"]:.4f}')
                
                # 策略分析
                if pair['pnl_percent'] > 0:
                    print(f'   🎯 结果: 盈利 (+${pair["net_pnl"]:.4f})')
                else:
                    print(f'   ⚠️  结果: 亏损 (${pair["net_pnl"]:.4f})')
                
                # 建议的止盈止损
                suggested_stop_loss = pair['entry_price'] * 0.985  # 1.5%止损
                suggested_take_profit = pair['entry_price'] * 1.03  # 3%止盈
                print(f'   🛡️  建议止损: ${suggested_stop_loss:.2f} (-1.5%)')
                print(f'   🎯 建议止盈: ${suggested_take_profit:.2f} (+3.0%)')
            
            # 统计信息
            print('\n📊 交易统计:')
            print('='*40)
            
            total_trades = len(trade_pairs)
            winning_trades = [t for t in trade_pairs if t['pnl'] > 0]
            losing_trades = [t for t in trade_pairs if t['pnl'] <= 0]
            
            win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
            total_pnl = sum(t['pnl'] for t in trade_pairs)
            total_net_pnl = sum(t['net_pnl'] for t in trade_pairs)
            total_fee = sum(t['total_fee'] for t in trade_pairs)
            
            print(f'   总交易次数: {total_trades}')
            print(f'   盈利次数: {len(winning_trades)}')
            print(f'   亏损次数: {len(losing_trades)}')
            print(f'   胜率: {win_rate:.1f}%')
            print(f'   总毛盈亏: ${total_pnl:.4f}')
            print(f'   总手续费: ${total_fee:.6f}')
            print(f'   总净盈亏: ${total_net_pnl:.4f}')
            
            if winning_trades:
                avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades)
                print(f'   平均盈利: ${avg_win:.4f}')
            
            if losing_trades:
                avg_loss = abs(sum(t['pnl'] for t in losing_trades) / len(losing_trades))
                print(f'   平均亏损: ${avg_loss:.4f}')
            
            if winning_trades and losing_trades:
                profit_factor = sum(t['pnl'] for t in winning_trades) / abs(sum(t['pnl'] for t in losing_trades))
                print(f'   盈亏比: {profit_factor:.2f}')
        
        # 检查当前持仓
        print('\n📊 当前持仓状态:')
        positions = exchange.fetch_positions([symbol])
        current_position = None
        
        for pos in positions:
            if pos['symbol'] == symbol:
                contracts = float(pos.get('contracts', 0))
                if contracts > 0:
                    current_position = pos
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
                    
                    # 建议的止盈止损
                    entry_price = pos.get('entryPrice', 0)
                    current_price = pos.get('markPrice', 0)
                    if entry_price > 0:
                        pnl_percent = ((current_price - entry_price) / entry_price) * 100
                        print(f'       当前盈亏: {pnl_percent:.2f}%')
                        
                        suggested_stop_loss = entry_price * 0.985  # 1.5%止损
                        suggested_take_profit = entry_price * 1.03  # 3%止盈
                        print(f'       🛡️  建议止损: ${suggested_stop_loss:.2f} (-1.5%)')
                        print(f'       🎯 建议止盈: ${suggested_take_profit:.2f} (+3.0%)')
                    break
        
        if not current_position:
            print('   无当前持仓')
        
        print('\n🎯 策略建议:')
        print('='*40)
        
        if trade_pairs:
            last_trade = trade_pairs[-1]
            if last_trade['pnl'] > 0:
                print('   1. 上一笔交易盈利，继续保持当前策略')
            else:
                print('   1. 上一笔交易亏损，考虑调整入场时机')
            
            print('   2. 建议设置固定止盈止损: 1.5%止损, 3%止盈')
            print('   3. 保持最小仓位测试，验证策略有效性')
            print('   4. 记录每笔交易的原因和策略')
        
        if current_position:
            print('   5. 当前有持仓，建议设置止盈止损保护')
            print('   6. 监控持仓，达到目标及时平仓')
        
        print('\n📝 监控面板改进建议:')
        print('   1. 显示完整交易历史（已实现）')
        print('   2. 显示每笔交易的盈亏和百分比')
        print('   3. 显示持仓时间和策略信息')
        print('   4. 显示建议的止盈止损价位')
        print('   5. 显示交易统计（胜率、盈亏比等）')
        
    except Exception as e:
        print(f'❌ 分析失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    analyze_trade_history()