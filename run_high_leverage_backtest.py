#!/usr/bin/env python3
"""
运行精准高杠杆策略回测
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt

sys.path.append('.')
try:
    from high_leverage_strategy import HighLeverageStrategy
except ImportError:
    print("❌ 无法导入策略模块")
    sys.exit(1)

def fetch_historical_data(exchange, symbol, timeframe, days):
    """获取历史数据"""
    print(f"📊 获取{timeframe} {days}天数据...")
    
    all_ohlcv = []
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    current = start_time
    
    while current < end_time:
        try:
            since = int(current.timestamp() * 1000)
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            
            if not ohlcv:
                break
            
            all_ohlcv.extend(ohlcv)
            current = datetime.fromtimestamp(ohlcv[-1][0] / 1000)
            
            if len(all_ohlcv) % 1000 == 0:
                print(f"  已获取 {len(all_ohlcv)} 根K线...")
                
        except Exception as e:
            print(f"  获取失败: {e}")
            break
    
    if not all_ohlcv:
        return None
    
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    print(f"  ✅ 完成: {len(df)} 根K线")
    return df

def calculate_indicators(df):
    """计算技术指标"""
    # 移动平均线
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df['ema_50'] = df['close'].ewm(span=50).mean()
    df['ema_100'] = df['close'].ewm(span=100).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 布林带
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    
    # 成交量
    df['volume_sma'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()
    df['atr_percent'] = df['atr'] / df['close']
    
    return df

def check_entry_signal(df_15m, df_1h, current_idx):
    """检查入场信号"""
    if current_idx < 1 or len(df_1h) < 1:
        return None, 0, ""
    
    current_15m = df_15m.iloc[current_idx]
    prev_15m = df_15m.iloc[current_idx-1]
    current_1h = df_1h.iloc[-1]
    
    # 1小时趋势
    if current_1h['ema_20'] > current_1h['ema_50']:
        trend = 'LONG'
    elif current_1h['ema_20'] < current_1h['ema_50']:
        trend = 'SHORT'
    else:
        return None, 0, "趋势不明"
    
    conditions = []
    confidence = 0
    
    # 趋势条件
    conditions.append("1h趋势确认")
    confidence += 0.3
    
    # 15分钟信号
    signal_found = False
    
    # EMA交叉
    if (trend == 'LONG' and 
        current_15m['ema_20'] > current_15m['ema_50'] and 
        prev_15m['ema_20'] <= prev_15m['ema_50']):
        conditions.append("15m EMA金叉")
        confidence += 0.2
        signal_found = True
    
    elif (trend == 'SHORT' and 
          current_15m['ema_20'] < current_15m['ema_50'] and 
          prev_15m['ema_20'] >= prev_15m['ema_50']):
        conditions.append("15m EMA死叉")
        confidence += 0.2
        signal_found = True
    
    # MACD
    if (trend == 'LONG' and 
        current_15m['macd'] > current_15m['macd_signal'] and 
        prev_15m['macd'] <= prev_15m['macd_signal']):
        conditions.append("MACD金叉")
        confidence += 0.15
        signal_found = True
    
    elif (trend == 'SHORT' and 
          current_15m['macd'] < current_15m['macd_signal'] and 
          prev_15m['macd'] >= prev_15m['macd_signal']):
        conditions.append("MACD死叉")
        confidence += 0.15
        signal_found = True
    
    if not signal_found:
        return None, 0, "无明确信号"
    
    # 成交量
    if current_15m['volume_ratio'] >= 1.5:
        conditions.append(f"成交量放大{current_15m['volume_ratio']:.1f}倍")
        confidence += 0.2
    else:
        return None, 0, f"成交量不足: {current_15m['volume_ratio']:.1f}倍"
    
    # RSI
    if trend == 'LONG' and current_15m['rsi'] < 70:
        conditions.append(f"RSI {current_15m['rsi']:.1f}(正常)")
        confidence += 0.1
    elif trend == 'SHORT' and current_15m['rsi'] > 30:
        conditions.append(f"RSI {current_15m['rsi']:.1f}(正常)")
        confidence += 0.1
    else:
        return None, 0, f"RSI极端: {current_15m['rsi']:.1f}"
    
    if confidence >= 0.8:
        reason = " + ".join(conditions)
        return trend, confidence, reason
    
    return None, 0, f"置信度不足: {confidence:.2f}"

def calculate_leverage(df_15m, current_idx, base_leverage=60, max_leverage=80):
    """计算动态杠杆"""
    leverage = base_leverage
    
    if current_idx >= 0:
        current = df_15m.iloc[current_idx]
        
        # 波动率调整
        volatility = current['atr_percent']
        if volatility < 0.003:
            leverage += 10
        elif volatility > 0.01:
            leverage -= 10
        
        # 成交量调整
        if current['volume_ratio'] > 2.0:
            leverage += 5
        
        # 布林带宽度
        if current['bb_width'] > 0.03:
            leverage += 5
    
    return min(max_leverage, max(50, leverage))

def run_simple_backtest():
    """运行简化版回测"""
    print("="*70)
    print("🎯 精准高杠杆策略回测 - 200U → 600U (200%月回报)")
    print("="*70)
    
    # 初始化
    config_path = 'config/survival_config.json'
    
    # 读取配置
    with open(config_path, 'r') as f:
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
    
    symbol = config['exchange']['symbol']
    
    # 获取数据
    print("\n📥 获取历史数据...")
    df_15m = fetch_historical_data(exchange, symbol, '15m', 30)
    df_1h = fetch_historical_data(exchange, symbol, '1h', 30)
    
    if df_15m is None or df_1h is None:
        print("❌ 数据获取失败")
        return
    
    print(f"\n📊 数据统计:")
    print(f"  15分钟数据: {len(df_15m)} 根K线")
    print(f"  1小时数据: {len(df_1h)} 根K线")
    print(f"  时间范围: {df_15m.index[0]} 至 {df_15m.index[-1]}")
    print(f"  最新价格: ${df_15m['close'].iloc[-1]:,.2f}")
    
    # 计算指标
    print("\n📈 计算技术指标...")
    df_15m = calculate_indicators(df_15m)
    df_1h = calculate_indicators(df_1h)
    
    # 回测参数
    initial_capital = 200
    capital = initial_capital
    position = None
    entry_price = 0
    entry_idx = 0
    position_size = 0
    leverage = 60
    
    trade_history = []
    equity_curve = [capital]
    daily_trades = 0
    current_day = None
    
    print("\n⚡ 运行回测...")
    
    for i in range(1, len(df_15m)):
        current_time = df_15m.index[i]
        current_day_str = current_time.strftime('%Y-%m-%d')
        
        # 重置每日交易计数
        if current_day != current_day_str:
            current_day = current_day_str
            daily_trades = 0
        
        # 检查是否有持仓
        if position:
            current_price = df_15m['close'].iloc[i]
            
            if position == 'LONG':
                # 计算止损止盈
                stop_loss = entry_price * 0.98  # 2%止损
                take_profit = entry_price * 1.04  # 4%止盈
                
                # 检查平仓条件
                if current_price <= stop_loss:
                    pnl = (current_price - entry_price) * position_size
                    capital += pnl
                    trade_history.append({
                        'time': current_time,
                        'type': 'CLOSE',
                        'direction': 'LONG',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': pnl,
                        'reason': '止损',
                        'leverage': leverage
                    })
                    position = None
                    daily_trades += 1
                    
                elif current_price >= take_profit:
                    pnl = (current_price - entry_price) * position_size
                    capital += pnl
                    trade_history.append({
                        'time': current_time,
                        'type': 'CLOSE',
                        'direction': 'LONG',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': pnl,
                        'reason': '止盈',
                        'leverage': leverage
                    })
                    position = None
                    daily_trades += 1
            
            else:  # SHORT
                stop_loss = entry_price * 1.02
                take_profit = entry_price * 0.96
                
                if current_price >= stop_loss:
                    pnl = (entry_price - current_price) * position_size
                    capital += pnl
                    trade_history.append({
                        'time': current_time,
                        'type': 'CLOSE',
                        'direction': 'SHORT',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': pnl,
                        'reason': '止损',
                        'leverage': leverage
                    })
                    position = None
                    daily_trades += 1
                    
                elif current_price <= take_profit:
                    pnl = (entry_price - current_price) * position_size
                    capital += pnl
                    trade_history.append({
                        'time': current_time,
                        'type': 'CLOSE',
                        'direction': 'SHORT',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': pnl,
                        'reason': '止盈',
                        'leverage': leverage
                    })
                    position = None
                    daily_trades += 1
        
        # 如果没有持仓且未达到每日限制，检查入场
        if not position and daily_trades < 3:
            signal, confidence, reason = check_entry_signal(df_15m, df_1h, i)
            
            if signal and confidence >= 0.8:
                # 计算杠杆
                leverage = calculate_leverage(df_15m, i)
                
                # 计算仓位 (15%本金，高杠杆)
                position_pct = 0.15
                position_usd = capital * position_pct * leverage
                position_size = position_usd / df_15m['close'].iloc[i]
                
                # 确保最小交易量
                min_amount = 0.001  # BTC最小交易量
                if position_size < min_amount:
                    position_size = min_amount
                
                # 开仓
                position = signal
                entry_price = df_15m['close'].iloc[i]
                entry_idx = i
                
                trade_history.append({
                    'time': current_time,
                    'type': 'OPEN',
                    'direction': signal,
                    'price': entry_price,
                    'size': position_size,
                    'leverage': leverage,
                    'reason': reason,
                    'confidence': confidence
                })
        
        # 记录资金曲线
        if position:
            current_price = df_15m['close'].iloc[i]
            if position == 'LONG':
                unrealized_pnl = (current_price - entry_price) * position_size
            else:
                unrealized_pnl = (entry_price - current_price) * position_size
            current_equity = capital + unrealized_pnl
        else:
            current_equity = capital
        
        equity_curve.append(current_equity)
    
    print("✅ 回测完成")
    
    # 计算指标
    print("\n" + "="*70)
    print("📊 回测结果汇总")
    print("="*70)
    
    closed_trades = [t for t in trade_history if t['type'] == 'CLOSE']
    total_trades = len(closed_trades)
    
    if total_trades == 0:
        print("❌ 没有交易记录")
        return
    
    winning_trades = [t for t in closed_trades if t['pnl'] > 0]
    losing_trades = [t for t in closed_trades if t['pnl'] < 0]
    
    total_pnl = sum(t['pnl'] for t in closed_trades)
    total_return = (capital - initial_capital) / initial_capital * 100
    
    # 计算最大回撤
    equity_array = np.array(equity_curve)
    peak = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - peak) / peak
    max_drawdown = np.min(drawdown) * 100
    
    print(f"\n💰 资金表现:")
    print(f"  初始资金: ${initial_capital:,.2f}")
    print(f"  最终资金: ${capital:,.2f}")
    print(f"  总盈亏: ${total_pnl:,.2f}")
    print(f"  总收益率: {total_return:.2f}%")
    
    print(f"\n📊 交易统计:")
    print(f"  总交易次数: {total_trades}")
    print(f"  盈利次数: {len(winning_trades)}")
    print(f"  亏损次数: {len(losing_trades)}")
    print(f"  胜率: {len(winning_trades)/total_trades*100:.2f}%")
    
    if winning_trades:
        avg_win = np.mean([t['pnl'] for t in winning_trades])
        print(f"  平均盈利: ${avg_win:.2f}")
    
    if losing_trades:
        avg_loss = np.mean([t['pnl'] for t in losing_trades])
        print(f"  平均亏损: ${avg_loss:.2f}")
        
        total_win = sum(t['pnl