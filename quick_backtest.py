#!/usr/bin/env python3
"""
快速回测 - 获取数据并简单分析
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

print("🚀 快速回测分析")
print("="*60)

# 初始化交易所
exchange = ccxt.okx({
    'apiKey': '9b5ee84f-13fd-43f5-ae6f-b96b2b0ed70d',
    'secret': 'A7EABBD3C6D49A92C5B542E0189F4BEC',
    'password': 'Lhc@930720',
    'enableRateLimit': True,
    'proxies': {
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897'
    },
    'options': {'defaultType': 'swap'}
})

# 获取30天数据
print("📊 获取BTC/USDT永续合约30天5分钟数据...")
symbol = 'BTC/USDT:USDT'
timeframe = '5m'

# 计算时间范围
end_time = datetime.now()
start_time = end_time - timedelta(days=30)

all_data = []
current = start_time

while current < end_time:
    try:
        since = int(current.timestamp() * 1000)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        
        if not ohlcv:
            break
            
        all_data.extend(ohlcv)
        current = datetime.fromtimestamp(ohlcv[-1][0] / 1000)
        
        print(f"  已获取 {len(all_data)} 根K线...")
        
    except Exception as e:
        print(f"  获取数据出错: {e}")
        break

if not all_data:
    print("❌ 无法获取数据")
    exit(1)

# 创建DataFrame
df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

print(f"✅ 数据获取完成: {len(df)} 根K线")
print(f"  时间范围: {df.index[0]} 至 {df.index[-1]}")
print(f"  最新价格: ${df['close'].iloc[-1]:,.2f}")

# 计算基本指标
print("\n📈 计算技术指标...")

# 移动平均线
df['ema_20'] = df['close'].ewm(span=20).mean()
df['ema_50'] = df['close'].ewm(span=50).mean()

# RSI
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['rsi'] = 100 - (100 / (1 + rs))

# 布林带
df['bb_middle'] = df['close'].rolling(window=20).mean()
bb_std = df['close'].rolling(window=20).std()
df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

# ATR
high_low = df['high'] - df['low']
high_close = np.abs(df['high'] - df['close'].shift())
low_close = np.abs(df['low'] - df['close'].shift())
ranges = pd.concat([high_low, high_close, low_close], axis=1)
true_range = ranges.max(axis=1)
df['atr'] = true_range.rolling(window=14).mean()

print("✅ 指标计算完成")

# 简单策略回测
print("\n⚡ 运行简单策略回测...")

initial_capital = 200
capital = initial_capital
position = None
entry_price = 0
trade_history = []
equity_curve = [capital]

for i in range(1, len(df)):
    current = df.iloc[i]
    prev = df.iloc[i-1]
    
    # 生成信号
    signal = 'FLAT'
    reason = ''
    
    # EMA交叉
    if current['ema_20'] > current['ema_50'] and prev['ema_20'] <= prev['ema_50']:
        signal = 'LONG'
        reason = 'EMA金叉'
    elif current['ema_20'] < current['ema_50'] and prev['ema_20'] >= prev['ema_50']:
        signal = 'SHORT'
        reason = 'EMA死叉'
    
    # RSI极端值
    elif current['rsi'] < 30:
        signal = 'LONG'
        reason = f'RSI超卖({current["rsi"]:.1f})'
    elif current['rsi'] > 70:
        signal = 'SHORT'
        reason = f'RSI超买({current["rsi"]:.1f})'
    
    # 布林带触碰
    elif current['close'] <= current['bb_lower']:
        signal = 'LONG'
        reason = '触及布林带下轨'
    elif current['close'] >= current['bb_upper']:
        signal = 'SHORT'
        reason = '触及布林带上轨'
    
    # 如果有持仓，检查平仓
    if position:
        current_price = current['close']
        
        if position == 'LONG':
            # 3%止损，6%止盈
            if current_price <= entry_price * 0.97:
                pnl = (current_price - entry_price) * (capital * 0.1 * 10 / entry_price)
                capital += pnl
                trade_history.append({
                    'type': 'CLOSE',
                    'direction': 'LONG',
                    'entry': entry_price,
                    'exit': current_price,
                    'pnl': pnl,
                    'reason': '止损'
                })
                position = None
            elif current_price >= entry_price * 1.06:
                pnl = (current_price - entry_price) * (capital * 0.1 * 10 / entry_price)
                capital += pnl
                trade_history.append({
                    'type': 'CLOSE',
                    'direction': 'LONG',
                    'entry': entry_price,
                    'exit': current_price,
                    'pnl': pnl,
                    'reason': '止盈'
                })
                position = None
        else:  # SHORT
            if current_price >= entry_price * 1.03:
                pnl = (entry_price - current_price) * (capital * 0.1 * 10 / entry_price)
                capital += pnl
                trade_history.append({
                    'type': 'CLOSE',
                    'direction': 'SHORT',
                    'entry': entry_price,
                    'exit': current_price,
                    'pnl': pnl,
                    'reason': '止损'
                })
                position = None
            elif current_price <= entry_price * 0.94:
                pnl = (entry_price - current_price) * (capital * 0.1 * 10 / entry_price)
                capital += pnl
                trade_history.append({
                    'type': 'CLOSE',
                    'direction': 'SHORT',
                    'entry': entry_price,
                    'exit': current_price,
                    'pnl': pnl,
                    'reason': '止盈'
                })
                position = None
    
    # 如果没有持仓，检查开仓
    if not position and signal != 'FLAT':
        position = signal
        entry_price = current['close']
        trade_history.append({
            'type': 'OPEN',
            'direction': signal,
            'price': entry_price,
            'reason': reason
        })
    
    equity_curve.append(capital)

print("✅ 回测完成")

# 计算结果
print("\n" + "="*60)
print("📊 回测结果")
print("="*60)

total_trades = len([t for t in trade_history if t['type'] == 'CLOSE'])
winning_trades = len([t for t in trade_history if t['type'] == 'CLOSE' and t['pnl'] > 0])
losing_trades = total_trades - winning_trades
total_pnl = sum(t['pnl'] for t in trade_history if t['type'] == 'CLOSE')
total_return = (capital - initial_capital) / initial_capital * 100

print(f"\n💰 资金表现:")
print(f"  初始资金: ${initial_capital:,.2f}")
print(f"  最终资金: ${capital:,.2f}")
print(f"  总盈亏: ${total_pnl:,.2f}")
print(f"  总收益率: {total_return:.2f}%")

print(f"\n📊 交易统计:")
print(f"  总交易次数: {total_trades}")
print(f"  盈利次数: {winning_trades}")
print(f"  亏损次数: {losing_trades}")
print(f"  胜率: {winning_trades/total_trades*100 if total_trades > 0 else 0:.2f}%")

if winning_trades > 0:
    avg_win = np.mean([t['pnl'] for t in trade_history if t['type'] == 'CLOSE' and t['pnl'] > 0])
    print(f"  平均盈利: ${avg_win:.2f}")

if losing_trades > 0:
    avg_loss = np.mean([t['pnl'] for t in trade_history if t['type'] == 'CLOSE' and t['pnl'] < 0])
    print(f"  平均亏损: ${avg_loss:.2f}")
    
    total_win = sum(t['pnl'] for t in trade_history if t['type'] == 'CLOSE' and t['pnl'] > 0)
    total_loss = abs(sum(t['pnl'] for t in trade_history if t['type'] == 'CLOSE' and t['pnl'] < 0))
    profit_factor = total_win / total_loss if total_loss > 0 else float('inf')
    print(f"  盈亏比: {profit_factor:.2f}")

# 计算最大回撤
equity_array = np.array(equity_curve)
peak = np.maximum.accumulate(equity_array)
drawdown = (equity_array - peak) / peak
max_drawdown = np.min(drawdown) * 100

print(f"\n🛡️ 风险指标:")
print(f"  最大回撤: {max_drawdown:.2f}%")

# 生存目标评估
print("\n" + "="*60)
print("🎯 生存目标评估 (200U → 1000U)")
print("="*60)

target_return = 400  # 400%
achievement = total_return / target_return * 100

print(f"\n📈 收益率对比:")
print(f"  月目标收益率: {target_return}%")
print(f"  回测实际收益率: {total_return:.2f}%")
print(f"  目标达成度: {achievement:.1f}%")

if total_return >= target_return:
    print("  ✅ 策略理论上可以达成目标!")
elif total_return >= target_return * 0.7:
    print("  ⚠️  策略接近目标，需要小幅优化")
elif total_return >= target_return * 0.4:
    print("  ⚠️  策略距离目标较远，需要中等优化")
else:
    print("  ❌ 策略无法达成目标，需要重新设计")

# 成本覆盖分析
print(f"\n💰 成本覆盖分析:")
monthly_cost = 50
daily_cost = monthly_cost / 30
avg_daily_pnl = total_pnl / 30

print(f"  月API成本: ${monthly_cost}")
print(f"  日成本需求: ${daily_cost:.2f}")
print(f"  回测日均盈利: ${avg_daily_pnl:.2f}")

if avg_daily_pnl >= daily_cost:
    print("  ✅ 策略可以覆盖运营成本")
else:
    print(f"  ❌ 策略无法覆盖成本，日均缺口: ${daily_cost - avg_daily_pnl:.2f}")

# 风险评估
print(f"\n⚠️ 风险警告:")
if max_drawdown > 25:
    print(f"  ❌ 最大回撤过高 ({max_drawdown:.1f}%)，可能触发紧急停止")
elif max_drawdown > 15:
    print(f"  ⚠️  最大回撤偏高 ({max_drawdown:.1f}%)，需加强风控")

if total_trades < 10:
    print(f"  ⚠️  交易频率过低 ({total_trades}次)，可能无法达成目标")

print(f"\n💡 建议:")
if total_return < target_return * 0.5:
    print("  1. 考虑增加杠杆（但会同时增加风险）")
    print("  2. 优化策略参数，提高收益率")
    print("  3. 增加交易频率或使用更小时间框架")
elif total_return < target_return:
    print("  1. 小幅优化策略参数")
    print("  2. 考虑适度增加杠杆")
    print("  3. 改进止损止盈策略")
else:
    print("  1. 策略表现良好，可以开始实盘测试")
    print("  2. 建议先进行小额测试")
    print("  3. 密切监控风险指标")

print(f"\n📋 下一步:")
print("  1. 根据回测结果优化策略参数")
print("  2. 进行多周期回测验证稳定性")
print("  3. 小额实盘测试（建议$10-20）")
print("  4. 如果测试成功，逐步增加资金")

# 保存结果
import os
os.makedirs('logs', exist_ok=True)

result = {
    'timestamp': datetime.now().isoformat(),
    'initial_capital': initial_capital,
    'final_capital': capital,
    'total_return_percent': total_return,
    'total_trades': total_trades,
    'winning_trades': winning_trades,
    'losing_trades': losing_trades,
    'win_rate': winning_trades/total_trades*100 if total_trades > 0 else 0,
    'max_drawdown_percent': max_drawdown,
    'target_achievement_percent': achievement,
    'can_cover_costs': avg_daily_pnl >= daily_cost,
    'trade_history': trade_history
}

with open('logs/quick_backtest.json', 'w') as f:
    json.dump(result, f, indent=2, default=str)

print(f"\n💾 详细结果已保存到: logs/quick_backtest.json")