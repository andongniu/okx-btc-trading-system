#!/usr/bin/env python3
"""
分析市场表现和策略优化
"""

import ccxt
import json
import numpy as np
from datetime import datetime, timedelta

def analyze_market_performance():
    print('🔍 分析昨晚至今的市场波动...')
    print('='*50)
    
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
    
    try:
        # 获取4小时K线数据（查看更大时间范围）
        ohlcv = exchange.fetch_ohlcv(symbol, '4h', limit=50)
        closes = np.array([c[4] for c in ohlcv])
        times = [datetime.fromtimestamp(c[0]/1000) for c in ohlcv]
        
        print('📈 最近50根4小时K线分析:')
        print(f'   开始时间: {times[0].strftime("%Y-%m-%d %H:%M")}')
        print(f'   结束时间: {times[-1].strftime("%Y-%m-%d %H:%M")}')
        print(f'   价格范围: ${closes.min():.2f} - ${closes.max():.2f}')
        print(f'   总波动: {(closes.max() - closes.min()) / closes.min() * 100:.2f}%')
        
        # 计算波动率
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * np.sqrt(365 * 6)  # 4小时数据年化
        print(f'   年化波动率: {volatility:.2%}')
        
        # 分析最近24小时
        recent_24h = closes[-6:]  # 4小时×6 = 24小时
        print(f'\n⏰ 最近24小时分析:')
        print(f'   开始价: ${recent_24h[0]:.2f}')
        print(f'   当前价: ${recent_24h[-1]:.2f}')
        print(f'   24h涨跌: {(recent_24h[-1] - recent_24h[0]) / recent_24h[0] * 100:.2f}%')
        print(f'   24h波动: {(recent_24h.max() - recent_24h.min()) / recent_24h.min() * 100:.2f}%')
        
        # 分析当前策略条件
        print('\n🎯 分析当前策略条件...')
        
        # 获取15分钟数据用于策略分析
        ohlcv_15m = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        closes_15m = np.array([c[4] for c in ohlcv_15m])
        
        # 计算技术指标
        sma_20 = np.mean(closes_15m[-20:])
        sma_50 = np.mean(closes_15m[-50:])
        current_price = closes_15m[-1]
        
        # 计算支撑阻力
        support = np.min(closes_15m[-20:])
        resistance = np.max(closes_15m[-20:])
        price_position = (current_price - support) / (resistance - support) if resistance != support else 0.5
        
        print(f'📊 当前技术指标:')
        print(f'   价格: ${current_price:.2f}')
        print(f'   SMA20: ${sma_20:.2f}')
        print(f'   SMA50: ${sma_50:.2f}')
        print(f'   支撑: ${support:.2f}')
        print(f'   阻力: ${resistance:.2f}')
        print(f'   价格位置: {price_position:.2%}')
        
        # 判断趋势
        if current_price > sma_20 > sma_50:
            trend = '上涨趋势'
        elif current_price < sma_20 < sma_50:
            trend = '下跌趋势'
        else:
            trend = '震荡趋势'
        
        print(f'📈 趋势判断: {trend}')
        
        # 分析为什么没开单
        print('\n❓ 分析未开单原因:')
        
        if trend == '上涨趋势':
            if price_position > 0.3:
                print(f'   ❌ 价格上涨趋势，但价格位置 {price_position:.2%} > 30%')
                print(f'   💡 建议: 放宽支撑区条件到 <40% 或 <50%')
            else:
                print(f'   ✅ 符合开多条件，但可能其他条件不满足')
        elif trend == '下跌趋势':
            if price_position < 0.7:
                print(f'   ❌ 价格下跌趋势，但价格位置 {price_position:.2%} < 70%')
                print(f'   💡 建议: 放宽阻力区条件到 >60% 或 >50%')
            else:
                print(f'   ✅ 符合开空条件，但可能其他条件不满足')
        else:
            print(f'   ❌ 震荡趋势，需要高波动率才开单')
        
        # 检查波动率
        returns_15m = np.diff(closes_15m) / closes_15m[:-1]
        volatility_15m = np.std(returns_15m) * np.sqrt(365 * 24 * 4)
        print(f'\n📊 当前波动率: {volatility_15m:.2%}')
        
        if volatility_15m < 0.4:
            print(f'   📉 波动率较低 ({volatility_15m:.2%} < 40%)')
            print(f'   💡 建议: 降低波动率阈值或调整参数')
        elif volatility_15m < 0.8:
            print(f'   📊 波动率中等 ({volatility_15m:.2%})')
        else:
            print(f'   📈 波动率较高 ({volatility_15m:.2%} > 80%)')
        
        # 模拟如果放宽条件会怎样
        print('\n🎯 模拟放宽条件后的机会:')
        
        opportunities = []
        
        # 放宽支撑区到40%
        if trend == '上涨趋势' and price_position < 0.4:
            opportunities.append('放宽支撑区到40% → 符合开多条件')
        
        # 放宽阻力区到60%
        if trend == '下跌趋势' and price_position > 0.6:
            opportunities.append('放宽阻力区到60% → 符合开空条件')
        
        # 震荡趋势也开单（中等波动率）
        if trend == '震荡趋势' and volatility_15m > 0.3:
            if price_position < 0.3:
                opportunities.append('震荡趋势+支撑区 → 符合开多条件')
            elif price_position > 0.7:
                opportunities.append('震荡趋势+阻力区 → 符合开空条件')
        
        if opportunities:
            print('   ✅ 放宽条件后可开单机会:')
            for opp in opportunities:
                print(f'      • {opp}')
        else:
            print('   ⚠️  即使放宽条件也无合适机会')
        
        print('\n🎯 优化建议总结:')
        print('   1. 放宽价格位置条件 (如: 支撑区<40%，阻力区>60%)')
        print('   2. 降低波动率阈值 (如: 中波动率从40%降到30%)')
        print('   3. 增加震荡趋势的开单条件')
        print('   4. 提高每日交易次数限制')
        print('   5. 降低风险回报比要求 (如: 从1.5降到1.3)')
        print('   6. 增加突破策略 (价格突破阻力/支撑时开单)')
        
        return {
            'current_price': current_price,
            'trend': trend,
            'price_position': price_position,
            'volatility': volatility_15m,
            'opportunities': opportunities
        }
        
    except Exception as e:
        print(f'❌ 分析失败: {e}')
        return None

if __name__ == '__main__':
    result = analyze_market_performance()
    
    if result:
        print('\n' + '='*50)
        print('📋 立即优化方案:')
        print('='*50)
        
        print('\n🔄 方案A: 温和优化 (推荐)')
        print('   1. 支撑区: <40% (原<30%)')
        print('   2. 阻力区: >60% (原>70%)')
        print('   3. 中波动率: >30% (原>40%)')
        print('   4. 震荡趋势也开单')
        print('   5. 风险回报比: >1.3 (原>1.5)')
        
        print('\n🚀 方案B: 激进优化')
        print('   1. 支撑区: <50%')
        print('   2. 阻力区: >50%')
        print('   3. 低波动率: >20%')
        print('   4. 所有趋势都开单')
        print('   5. 风险回报比: >1.2')
        print('   6. 增加突破策略')
        
        print('\n⚠️  风险提示:')
        print('   • 激进策略会增加交易频率')
        print('   • 可能降低单笔胜率')
        print('   • 需要更严格的风险控制')
        print('   • 建议从温和优化开始')