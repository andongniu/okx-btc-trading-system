#!/usr/bin/env python3
"""
简化高杠杆策略回测
使用现有数据进行快速验证
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import os

print("🎯 高杠杆策略快速回测分析")
print("="*60)

# 加载现有回测数据
data_file = '/Users/anth6iu/freqtrade-trading/backtest_enhanced_report.json'
if not os.path.exists(data_file):
    print(f"❌ 数据文件不存在: {data_file}")
    exit(1)

with open(data_file, 'r') as f:
    data = json.load(f)

# 分析优化策略表现
opt = data['optimized_strategy']
print("\n📊 现有优化策略表现 (30天回测):")
print(f"  初始资金: ${opt['initial_balance']:,.2f}")
print(f"  最终资金: ${opt['final_balance']:,.2f}")
print(f"  总收益率: {opt['total_return_percent']:.2f}%")
print(f"  交易次数: {opt['total_trades']}")
print(f"  胜率: {opt['win_rate_percent']:.2f}%")
print(f"  盈亏比: {opt['profit_factor']:.2f}")
print(f"  夏普比率: {opt['sharpe_ratio']:.2f}")
print(f"  最大单笔亏损: {opt['largest_loss_percent']:.2f}%")

# 高杠杆策略模拟
print("\n" + "="*60)
print("⚡ 高杠杆策略模拟 (基于现有策略)")
print("="*60)

# 参数设置
initial_capital = 200
target_capital = 600
base_return = opt['total_return_percent'] / 100  # 1.14% -> 0.0114

# 不同杠杆下的模拟
leverages = [10, 20, 30, 40, 50, 60, 70, 80]
results = []

for leverage in leverages:
    # 计算杠杆后收益
    leveraged_return = base_return * leverage
    
    # 考虑杠杆成本 (融资费用约0.01%/天)
    funding_cost = 0.0001 * 30 * leverage  # 0.01%每天 × 30天 × 杠杆
    
    # 考虑爆仓风险 (简化模型)
    # 最大单笔亏损放大杠杆倍
    max_loss_per_trade = abs(opt['largest_loss_percent'] / 100) * leverage
    
    # 爆仓概率估算 (如果最大亏损超过100%)
    bankruptcy_risk = min(1.0, max_loss_per_trade) * 0.8  # 简化估算
    
    # 预期收益 (考虑爆仓风险)
    expected_return = leveraged_return * (1 - bankruptcy_risk) - funding_cost
    
    # 最终资金
    final_capital = initial_capital * (1 + expected_return)
    
    results.append({
        'leverage': leverage,
        'base_return_pct': base_return * 100,
        'leveraged_return_pct': leveraged_return * 100,
        'funding_cost_pct': funding_cost * 100,
        'max_loss_pct': max_loss_per_trade * 100,
        'bankruptcy_risk_pct': bankruptcy_risk * 100,
        'expected_return_pct': expected_return * 100,
        'final_capital': final_capital,
        'target_achieved': final_capital >= target_capital
    })

# 显示结果
print("\n📈 不同杠杆下的模拟结果:")
print("杠杆 | 基础收益 | 杠杆收益 | 融资成本 | 最大亏损 | 爆仓风险 | 预期收益 | 最终资金 | 达标")
print("-"*100)

for r in results:
    achieved = "✅" if r['target_achieved'] else "❌"
    print(f"{r['leverage']:2d}x | "
          f"{r['base_return_pct']:6.2f}% | "
          f"{r['leveraged_return_pct']:7.1f}% | "
          f"{r['funding_cost_pct']:6.2f}% | "
          f"{r['max_loss_pct']:7.1f}% | "
          f"{r['bankruptcy_risk_pct']:7.1f}% | "
          f"{r['expected_return_pct']:7.1f}% | "
          f"${r['final_capital']:7.1f} | "
          f"{achieved}")

# 找到最佳杠杆
feasible = [r for r in results if r['target_achieved']]
if feasible:
    best = min(feasible, key=lambda x: x['bankruptcy_risk_pct'])
    print(f"\n🎯 最佳可行杠杆: {best['leverage']}x")
    print(f"   预期收益: {best['expected_return_pct']:.1f}%")
    print(f"   爆仓风险: {best['bankruptcy_risk_pct']:.1f}%")
    print(f"   最终资金: ${best['final_capital']:.1f}")
else:
    print("\n❌ 当前策略无法在安全杠杆下达成目标")
    
    # 计算需要的基础收益率
    required_base_return = (target_capital / initial_capital - 1) / 50  # 假设50倍杠杆
    print(f"💡 需要将基础收益率从 {base_return*100:.2f}% 提升至 {required_base_return*100:.2f}%")

# 策略改进建议
print("\n" + "="*60)
print("💡 策略改进建议")
print("="*60)

current_metrics = {
    'win_rate': opt['win_rate_percent'],
    'profit_factor': opt['profit_factor'],
    'avg_win': opt['average_win_percent'],
    'avg_loss': opt['average_loss_percent'],
    'sharpe': opt['sharpe_ratio']
}

target_metrics = {
    'win_rate': 65.0,  # 目标65%
    'profit_factor': 1.8,  # 目标1.8
    'avg_win': 0.4,  # 目标0.4%
    'avg_loss': -0.2,  # 目标-0.2%
    'sharpe': 0.5  # 目标0.5
}

print("\n📊 当前 vs 目标指标:")
print("指标         | 当前值   | 目标值   | 改进需求")
print("-"*45)

for key in current_metrics:
    current = current_metrics[key]
    target = target_metrics[key]
    improvement = ""
    
    if key == 'avg_loss':  # 亏损要减小
        if current < target:  # 当前亏损更小
            improvement = "✅ 已达标"
        else:
            improvement = f"需减少 {abs(current-target):.2f}%"
    else:  # 其他指标要增大
        if current >= target:
            improvement = "✅ 已达标"
        else:
            improvement = f"需提高 {target-current:.2f}"
    
    print(f"{key:12} | {current:8.2f} | {target:8.2f} | {improvement}")

# 计算改进后的预期收益
print("\n📈 改进后的预期表现:")
print("假设将指标提升至目标水平:")

# 改进后的基础收益率估算
improved_base_return = 0.02  # 2% (假设改进后)
required_leverage = (target_capital / initial_capital - 1) / improved_base_return

print(f"  改进后基础月收益: {improved_base_return*100:.2f}%")
print(f"  需要杠杆: {required_leverage:.1f}x")
print(f"  OKX最大杠杆: 125x (BTC永续)")

if required_leverage <= 80:
    print(f"  ✅ 在80倍杠杆内可行")
elif required_leverage <= 125:
    print(f"  ⚠️  需要 {required_leverage:.1f}x 杠杆，接近上限")
else:
    print(f"  ❌ 需要 {required_leverage:.1f}x 杠杆，超过平台限制")

# 风险分析
print("\n⚠️ 高风险警告:")
print("1. 高杠杆放大亏损: 2%价格波动 = 100%盈亏 (50倍杠杆)")
print("2. 爆仓风险: 价格反向波动2%即可导致爆仓")
print("3. 资金费率: 高杠杆持仓成本增加")
print("4. 流动性风险: 极端行情可能无法平仓")

# 实施建议
print("\n🎯 实施建议:")
print("1. 先优化基础策略至2%月收益")
print("2. 使用50-60倍杠杆进行测试")
print("3. 严格设置2%止损 (对应100%仓位风险)")
print("4. 每日最多交易3次，提高信号质量")
print("5. 准备紧急预案，单日亏损>$16立即停止")

# 保存分析结果
output = {
    'analysis_date': datetime.now().isoformat(),
    'initial_capital': initial_capital,
    'target_capital': target_capital,
    'current_strategy_performance': opt,
    'leverage_simulation': results,
    'improvement_targets': target_metrics,
    'risk_warnings': [
        "高杠杆放大亏损风险",
        "爆仓风险显著增加",
        "资金成本提高",
        "需要极强风险控制"
    ],
    'recommendations': [
        "先优化基础策略收益率",
        "从低杠杆开始测试",
        "严格风险控制",
        "准备充足备用金"
    ]
}

os.makedirs('logs', exist_ok=True)
with open('logs/high_leverage_analysis.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n💾 详细分析已保存到: logs/high_leverage_analysis.json")
print("\n📋 下一步:")
print("1. 查看详细分析报告")
print("2. 优化策略提高基础收益率")
print("3. 设计高杠杆风险管理方案")
print("4. 小额实盘测试验证")