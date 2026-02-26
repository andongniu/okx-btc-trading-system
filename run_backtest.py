#!/usr/bin/env python3
"""
运行生存策略回测
"""

import sys
import os
sys.path.append('.')

try:
    from survival_backtest import SurvivalBacktest
    import json
    import pandas as pd
    
    print("🚀 开始生存策略回测 (30天历史数据)")
    print("="*60)
    
    # 初始化
    backtest = SurvivalBacktest('config/survival_config.json')
    
    # 获取数据
    print("📊 获取历史数据...")
    df = backtest.fetch_historical_data(days=30)
    
    if len(df) < 100:
        print(f"❌ 数据不足: 只有 {len(df)} 根K线")
        sys.exit(1)
    
    # 计算指标
    print("📈 计算技术指标...")
    df = backtest.calculate_indicators(df)
    
    # 运行回测
    print("⚡ 运行回测...")
    backtest.run_backtest(df)
    
    # 计算指标
    print("📊 计算性能指标...")
    metrics = backtest.calculate_metrics()
    
    # 输出结果
    print("\n" + "="*60)
    print("📈 回测结果汇总")
    print("="*60)
    
    print(f"\n💰 资金表现:")
    print(f"  初始资金: ${backtest.initial_capital:,.2f}")
    print(f"  最终资金: ${metrics['final_capital']:,.2f}")
    print(f"  总盈亏: ${metrics['total_pnl']:,.2f}")
    print(f"  总收益率: {metrics['total_return']:.2f}%")
    
    print(f"\n📊 交易统计:")
    print(f"  总交易次数: {metrics['total_trades']}")
    print(f"  盈利次数: {metrics['winning_trades']}")
    print(f"  亏损次数: {metrics['losing_trades']}")
    print(f"  胜率: {metrics['win_rate']:.2f}%")
    print(f"  平均盈利: ${metrics['avg_win']:.2f}")
    print(f"  平均亏损: ${metrics['avg_loss']:.2f}")
    print(f"  盈亏比: {metrics['profit_factor']:.2f}")
    
    print(f"\n🛡️ 风险指标:")
    print(f"  最大回撤: {metrics['max_drawdown']:.2f}%")
    print(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
    
    # 生存目标评估
    print("\n" + "="*60)
    print("🎯 生存目标评估 (200U → 1000U)")
    print("="*60)
    
    target_return = 400  # 400%
    actual_return = metrics['total_return']
    achievement = actual_return / target_return * 100
    
    print(f"\n📈 收益率对比:")
    print(f"  月目标收益率: {target_return}%")
    print(f"  回测实际收益率: {actual_return:.2f}%")
    print(f"  目标达成度: {achievement:.1f}%")
    
    if actual_return >= target_return:
        print("  ✅ 策略理论上可以达成目标!")
    elif actual_return >= target_return * 0.7:
        print("  ⚠️  策略接近目标，需要小幅优化")
    elif actual_return >= target_return * 0.4:
        print("  ⚠️  策略距离目标较远，需要中等优化")
    elif actual_return >= target_return * 0.2:
        print("  ⚠️  策略距离目标很远，需要大幅优化")
    else:
        print("  ❌ 策略无法达成目标，需要重新设计")
    
    # 成本覆盖分析
    print(f"\n💰 成本覆盖分析:")
    monthly_cost = 50
    daily_cost = monthly_cost / 30
    avg_daily_pnl = metrics['total_pnl'] / 30
    
    print(f"  月API成本: ${monthly_cost}")
    print(f"  日成本需求: ${daily_cost:.2f}")
    print(f"  回测日均盈利: ${avg_daily_pnl:.2f}")
    
    if avg_daily_pnl >= daily_cost:
        print("  ✅ 策略可以覆盖运营成本")
    else:
        print(f"  ❌ 策略无法覆盖成本，日均缺口: ${daily_cost - avg_daily_pnl:.2f}")
    
    # 风险评估
    print(f"\n⚠️ 风险警告:")
    if metrics['max_drawdown'] > 25:
        print(f"  ❌ 最大回撤过高 ({metrics['max_drawdown']:.1f}%)，可能触发紧急停止")
    elif metrics['max_drawdown'] > 15:
        print(f"  ⚠️  最大回撤偏高 ({metrics['max_drawdown']:.1f}%)，需加强风控")
    
    if metrics['sharpe_ratio'] < 0:
        print(f"  ❌ 夏普比率为负 ({metrics['sharpe_ratio']:.2f})，风险调整后收益为负")
    elif metrics['sharpe_ratio'] < 0.5:
        print(f"  ⚠️  夏普比率偏低 ({metrics['sharpe_ratio']:.2f})")
    
    if metrics['win_rate'] < 40:
        print(f"  ⚠️  胜率偏低 ({metrics['win_rate']:.1f}%)，考虑优化入场条件")
    
    if metrics['profit_factor'] < 1.2:
        print(f"  ⚠️  盈亏比偏低 ({metrics['profit_factor']:.2f})，考虑优化止损止盈")
    
    # 建议
    print(f"\n💡 优化建议:")
    
    suggestions = []
    
    if metrics['total_trades'] < 15:
        suggestions.append("增加交易频率（调整信号灵敏度或使用更小时间框架）")
    
    if metrics['win_rate'] < 50:
        suggestions.append("优化入场条件（增加确认指标，提高信号质量）")
    
    if metrics['profit_factor'] < 1.5:
        suggestions.append("改进止损止盈策略（动态调整，追踪止损）")
    
    if metrics['max_drawdown'] > 15:
        suggestions.append("加强风险控制（降低仓位，设置更严格止损）")
    
    if actual_return < target_return * 0.5:
        suggestions.append("考虑增加杠杆或使用更激进的策略")
    
    if not suggestions:
        suggestions.append("策略表现良好，可以开始实盘测试")
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")
    
    # 保存结果
    print(f"\n💾 保存详细结果...")
    os.makedirs('logs', exist_ok=True)
    
    # 保存交易记录
    trades_data = {
        'metrics': metrics,
        'trades': backtest.trade_history,
        'equity_curve': backtest.equity_curve,
        'dates': [d.isoformat() for d in backtest.dates] if backtest.dates else []
    }
    
    with open('logs/backtest_results.json', 'w') as f:
        json.dump(trades_data, f, indent=2, default=str)
    
    # 保存简要报告
    report = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'initial_capital': backtest.initial_capital,
        'final_capital': metrics['final_capital'],
        'total_return_percent': metrics['total_return'],
        'target_achievement_percent': achievement,
        'can_cover_costs': avg_daily_pnl >= daily_cost,
        'risk_level': 'high' if metrics['max_drawdown'] > 20 else 'medium' if metrics['max_drawdown'] > 10 else 'low',
        'recommendation': 'proceed_with_caution' if achievement < 70 else 'proceed' if achievement < 100 else 'excellent'
    }
    
    with open('logs/backtest_summary.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ 回测完成！详细结果保存在 logs/ 目录")
    print(f"\n📋 下一步建议:")
    print(f"  1. 查看详细交易记录: logs/backtest_results.json")
    print(f"  2. 根据优化建议调整策略参数")
    print(f"  3. 进行多周期回测验证稳定性")
    print(f"  4. 小额实盘测试验证执行")
    
except Exception as e:
    print(f"❌ 回测失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)