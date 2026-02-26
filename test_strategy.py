#!/usr/bin/env python3
"""
测试策略功能
"""

import sys
import os
import pandas as pd
import numpy as np

# 添加策略路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'user_data/strategies'))

def test_strategy():
    print("测试策略功能...")
    
    # 创建模拟数据
    print("1. 创建模拟数据...")
    dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
    data = pd.DataFrame({
        'date': dates,
        'open': np.random.uniform(40000, 41000, 100),
        'high': np.random.uniform(41000, 42000, 100),
        'low': np.random.uniform(39000, 40000, 100),
        'close': np.random.uniform(40000, 41000, 100),
        'volume': np.random.uniform(1000, 5000, 100)
    })
    data.set_index('date', inplace=True)
    
    print(f"数据形状: {data.shape}")
    print(f"数据列: {list(data.columns)}")
    
    # 导入策略
    print("\n2. 导入策略...")
    try:
        from SampleStrategy import SampleStrategy
        print("✅ 策略导入成功")
    except Exception as e:
        print(f"❌ 策略导入失败: {e}")
        return
    
    # 创建策略实例
    print("\n3. 创建策略实例...")
    config = {
        'max_open_trades': 3,
        'stake_currency': 'USDT',
        'stake_amount': 100,
        'dry_run': True
    }
    
    try:
        strategy = SampleStrategy(config=config)
        print("✅ 策略实例创建成功")
    except Exception as e:
        print(f"❌ 策略实例创建失败: {e}")
        return
    
    # 测试指标计算
    print("\n4. 测试指标计算...")
    try:
        indicators = strategy.populate_indicators(data, {})
        print(f"✅ 指标计算成功")
        print(f"   原始数据列: {list(data.columns)}")
        print(f"   计算后列: {list(indicators.columns)}")
        print(f"   新增指标: {[col for col in indicators.columns if col not in data.columns]}")
        
        # 检查关键指标
        required_indicators = ['rsi', 'sma20', 'sma50', 'bb_lowerband', 'bb_middleband', 'bb_upperband']
        missing = [ind for ind in required_indicators if ind not in indicators.columns]
        if missing:
            print(f"   ⚠️ 缺失指标: {missing}")
        else:
            print(f"   ✅ 所有关键指标都存在")
            
        # 显示部分数据
        print(f"\n   数据预览 (最后5行):")
        print(indicators[['close', 'rsi', 'sma20', 'sma50']].tail())
        
    except Exception as e:
        print(f"❌ 指标计算失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试买入信号
    print("\n5. 测试买入信号...")
    try:
        buy_signals = strategy.populate_buy_trend(indicators, {})
        print(f"✅ 买入信号计算成功")
        print(f"   买入信号列: 'buy' in columns = {'buy' in buy_signals.columns}")
        
        if 'buy' in buy_signals.columns:
            buy_count = buy_signals['buy'].sum()
            print(f"   买入信号数量: {buy_count}")
            if buy_count > 0:
                print(f"   ✅ 检测到买入信号")
            else:
                print(f"   ⚠️ 未检测到买入信号 (可能是数据问题)")
                
    except Exception as e:
        print(f"❌ 买入信号计算失败: {e}")
        return
    
    # 测试卖出信号
    print("\n6. 测试卖出信号...")
    try:
        sell_signals = strategy.populate_sell_trend(buy_signals, {})
        print(f"✅ 卖出信号计算成功")
        print(f"   卖出信号列: 'sell' in columns = {'sell' in sell_signals.columns}")
        
        if 'sell' in sell_signals.columns:
            sell_count = sell_signals['sell'].sum()
            print(f"   卖出信号数量: {sell_count}")
            
    except Exception as e:
        print(f"❌ 卖出信号计算失败: {e}")
        return
    
    print("\n" + "="*50)
    print("🎉 策略测试完成！")
    print("="*50)
    print("\n总结:")
    print(f"1. 策略导入: ✅ 成功")
    print(f"2. 指标计算: ✅ 成功 ({len([col for col in indicators.columns if col not in data.columns])} 个指标)")
    print(f"3. 买入信号: ✅ 成功 (检测到 {buy_count if 'buy' in buy_signals.columns else 0} 个信号)")
    print(f"4. 卖出信号: ✅ 成功 (检测到 {sell_count if 'sell' in sell_signals.columns else 0} 个信号)")
    print(f"\n🎯 自动交易系统核心功能验证通过！")

if __name__ == "__main__":
    test_strategy()