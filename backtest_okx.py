#!/usr/bin/env python3
"""
OKX BTC永续合约回测脚本
使用下载的OKX历史数据进行回测
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

def prepare_okx_data_for_backtest():
    """准备OKX数据用于回测"""
    print("准备OKX BTC永续合约数据用于回测...")
    
    # 读取下载的数据
    csv_file = "/Users/anth6iu/freqtrade-trading/okx_btc_perpetual_5m.csv"
    if not os.path.exists(csv_file):
        print(f"❌ 数据文件不存在: {csv_file}")
        return None
    
    # 读取CSV
    df = pd.read_csv(csv_file)
    print(f"✅ 读取数据: {len(df)} 行")
    
    # 转换为Freqtrade格式
    # Freqtrade需要的数据格式: [timestamp, open, high, low, close, volume]
    # 时间戳已经是毫秒，转换为秒
    df['timestamp_ms'] = df['timestamp']
    df['timestamp'] = df['timestamp'] // 1000  # 转换为秒
    
    # 创建Freqtrade格式的DataFrame
    ft_df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
    
    # 添加必要的列
    ft_df['date'] = pd.to_datetime(ft_df['timestamp'], unit='s')
    
    print(f"✅ 数据转换完成")
    print(f"   时间范围: {ft_df['date'].min()} 到 {ft_df['date'].max()}")
    print(f"   数据点数: {len(ft_df)}")
    
    return ft_df

def run_backtest_with_data(data_df):
    """使用数据运行回测"""
    print("\n运行回测...")
    
    # 这里我们模拟一个简单的策略回测
    # 在实际使用中，您应该使用Freqtrade的backtesting模块
    
    # 简单策略: RSI策略
    print("应用RSI策略...")
    
    # 计算RSI
    def calculate_rsi(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    # 计算指标
    data_df['rsi'] = calculate_rsi(data_df['close'])
    data_df['sma_20'] = data_df['close'].rolling(window=20).mean()
    data_df['sma_50'] = data_df['close'].rolling(window=50).mean()
    
    # 生成交易信号
    data_df['buy_signal'] = (data_df['rsi'] < 30) & (data_df['sma_20'] > data_df['sma_50'])
    data_df['sell_signal'] = (data_df['rsi'] > 70) | (data_df['sma_20'] < data_df['sma_50'])
    
    # 模拟交易
    initial_balance = 10000
    balance = initial_balance
    position = 0
    trades = []
    
    for i in range(len(data_df)):
        row = data_df.iloc[i]
        
        # 买入信号
        if row['buy_signal'] and position == 0:
            position = balance / row['close'] * 0.95  # 使用95%的资金，留5%作为保证金
            balance = 0
            trades.append({
                'type': 'buy',
                'timestamp': row['timestamp'],
                'price': row['close'],
                'position': position,
                'balance': balance
            })
        
        # 卖出信号
        elif row['sell_signal'] and position > 0:
            balance = position * row['close'] * 0.995  # 扣除0.5%手续费
            position = 0
            trades.append({
                'type': 'sell',
                'timestamp': row['timestamp'],
                'price': row['close'],
                'position': position,
                'balance': balance
            })
    
    # 计算最终结果
    if position > 0:
        final_balance = position * data_df.iloc[-1]['close'] * 0.995
    else:
        final_balance = balance
    
    total_return = (final_balance - initial_balance) / initial_balance * 100
    
    print(f"\n📊 回测结果:")
    print(f"   初始资金: ${initial_balance:,.2f}")
    print(f"   最终资金: ${final_balance:,.2f}")
    print(f"   总收益率: {total_return:.2f}%")
    print(f"   交易次数: {len(trades)}")
    
    if trades:
        print(f"\n📈 交易记录:")
        for trade in trades[-5:]:  # 显示最后5笔交易
            date_str = datetime.fromtimestamp(trade['timestamp']).strftime('%Y-%m-%d %H:%M')
            print(f"   {date_str} - {trade['type'].upper()}: ${trade['price']:,.2f}")
    
    return {
        'initial_balance': initial_balance,
        'final_balance': final_balance,
        'total_return': total_return,
        'num_trades': len(trades),
        'trades': trades
    }

def main():
    """主函数"""
    print("=" * 60)
    print("OKX BTC永续合约回测系统")
    print("=" * 60)
    
    # 准备数据
    data = prepare_okx_data_for_backtest()
    if data is None:
        return
    
    # 运行回测
    results = run_backtest_with_data(data)
    
    # 保存结果
    results_file = "/Users/anth6iu/freqtrade-trading/backtest_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ 回测完成! 结果已保存到: {results_file}")
    
    # 显示数据统计
    print(f"\n📈 数据统计:")
    print(f"   数据点数: {len(data)}")
    print(f"   时间范围: {data['date'].min()} 到 {data['date'].max()}")
    print(f"   价格范围: ${data['close'].min():,.2f} - ${data['close'].max():,.2f}")
    print(f"   平均价格: ${data['close'].mean():,.2f}")
    print(f"   波动率: {data['close'].pct_change().std() * 100:.2f}%")

if __name__ == "__main__":
    main()