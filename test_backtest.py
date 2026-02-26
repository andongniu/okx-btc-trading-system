#!/usr/bin/env python3
"""
测试回测脚本 - 使用离线模式
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'venv/lib/python3.9/site-packages'))

from freqtrade.configuration import Configuration
from freqtrade.data.history import load_data
from freqtrade.resolvers import StrategyResolver
from freqtrade.optimize.backtesting import Backtesting
import pandas as pd

def main():
    print("开始回测测试...")
    
    # 加载配置
    config = Configuration.from_files(['config/config.json'])
    config['exchange']['name'] = 'binance'
    config['dry_run'] = True
    config['stake_amount'] = 100
    config['max_open_trades'] = 3
    
    # 创建模拟数据
    print("创建模拟数据...")
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='5min')
    data = pd.DataFrame({
        'date': dates,
        'open': [40000 + i * 0.1 for i in range(len(dates))],
        'high': [40100 + i * 0.1 for i in range(len(dates))],
        'low': [39900 + i * 0.1 for i in range(len(dates))],
        'close': [40050 + i * 0.1 for i in range(len(dates))],
        'volume': [1000 + i for i in range(len(dates))]
    })
    data.set_index('date', inplace=True)
    
    # 加载策略
    print("加载策略...")
    config['strategy'] = 'SampleStrategy'
    strategy = StrategyResolver.load_strategy(config)
    
    # 运行回测
    print("运行回测...")
    backtesting = Backtesting(config, strategy)
    
    try:
        results = backtesting.backtest(data)
        print(f"回测完成！总交易数: {len(results)}")
        if len(results) > 0:
            print("交易详情:")
            for trade in results:
                print(f"  - {trade}")
    except Exception as e:
        print(f"回测失败: {e}")
        print("尝试简化测试...")
        
        # 简化测试：直接测试策略指标计算
        print("测试策略指标计算...")
        from user_data.strategies.SampleStrategy import SampleStrategy
        
        strategy_instance = SampleStrategy(config=config)
        
        # 测试populate_indicators
        indicators = strategy_instance.populate_indicators(data, {})
        print(f"指标计算完成！生成的列: {list(indicators.columns)}")
        
        # 测试populate_buy_trend
        buy_signals = strategy_instance.populate_buy_trend(indicators, {})
        print(f"买入信号计算完成！买入信号列: 'buy' in columns = {'buy' in buy_signals.columns}")
        
        # 测试populate_sell_trend
        sell_signals = strategy_instance.populate_sell_trend(buy_signals, {})
        print(f"卖出信号计算完成！卖出信号列: 'sell' in columns = {'sell' in sell_signals.columns}")

if __name__ == "__main__":
    main()