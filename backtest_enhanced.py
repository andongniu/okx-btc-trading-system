#!/usr/bin/env python3
"""
增强版回测脚本 - 包含K线展示和完整历史记录
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

# 添加项目路径
sys.path.append('/Users/anth6iu/freqtrade-trading')

def load_historical_data():
    """加载历史数据"""
    data_file = '/Users/anth6iu/freqtrade-trading/okx_btc_perpetual_5m.csv'
    
    if not os.path.exists(data_file):
        print(f"数据文件不存在: {data_file}")
        return None
    
    try:
        # 直接使用date列作为时间戳，忽略timestamp列
        df = pd.read_csv(data_file, parse_dates=['date'])
        print(f"加载数据成功: {len(df)} 行")
        
        # 重命名date列为timestamp
        df['timestamp'] = df['date']
        
        # 确保列名正确
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                print(f"缺少必要列: {col}")
                return None
        
        # 按时间排序
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # 检查时间戳范围
        print(f"时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        
        return df
    except Exception as e:
        print(f"加载数据失败: {e}")
        # 尝试更简单的加载方式
        try:
            df = pd.read_csv(data_file)
            print(f"原始数据加载成功: {len(df)} 行")
            
            # 尝试不同的列名
            if 'date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date'])
            elif 'timestamp' in df.columns:
                # 尝试转换为datetime
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                except:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # 检查是否有有效的时间戳
            if 'timestamp' not in df.columns or df['timestamp'].isnull().all():
                print("无法解析时间戳列")
                return None
            
            # 确保必要的价格列存在
            price_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in price_columns:
                if col not in df.columns:
                    print(f"缺少价格列: {col}")
                    return None
            
            df = df.sort_values('timestamp').reset_index(drop=True)
            print(f"成功处理数据: {len(df)} 行，时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
            
            return df
        except Exception as e2:
            print(f"备用加载方式也失败: {e2}")
            return None

def simulate_trades_with_strategy(df, strategy_type='optimized'):
    """
    模拟交易策略
    strategy_type: 'simple' 或 'optimized'
    """
    trades = []
    position = 0
    balance = 10000  # 初始资金
    trade_history = []
    
    # 技术指标计算
    df['rsi'] = calculate_rsi(df['close'])
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['sma50'] = df['close'].rolling(window=50).mean()
    
    if strategy_type == 'optimized':
        # 优化策略的额外指标
        df['macd'], df['macd_signal'] = calculate_macd(df['close'])
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = calculate_bollinger_bands(df['close'])
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    for i in range(50, len(df) - 1):  # 跳过前50个数据点用于指标计算
        current_price = df['close'].iloc[i]
        current_time = df['timestamp'].iloc[i]
        
        # 买入信号
        buy_signal = False
        if strategy_type == 'simple':
            # 简单RSI策略
            if df['rsi'].iloc[i] < 30 and position == 0:
                buy_signal = True
        else:
            # 优化策略
            if (df['rsi'].iloc[i] < 30 and 
                position == 0 and
                df['volume_ratio'].iloc[i] > 1.2 and
                df['close'].iloc[i] < df['bb_lower'].iloc[i] * 1.02):  # 价格接近布林带下轨
                buy_signal = True
        
        # 卖出信号
        sell_signal = False
        if position > 0:
            if strategy_type == 'simple':
                if df['rsi'].iloc[i] > 70:
                    sell_signal = True
            else:
                if (df['rsi'].iloc[i] > 70 or
                    df['close'].iloc[i] > df['bb_upper'].iloc[i] * 0.98):  # 价格接近布林带上轨
                    sell_signal = True
        
        # 执行买入
        if buy_signal and balance > 0:
            position = balance / current_price  # 全仓买入
            balance = 0
            trades.append({
                'type': 'buy',
                'timestamp': current_time,
                'price': current_price,
                'position': position,
                'balance': balance
            })
        
        # 执行卖出
        elif sell_signal and position > 0:
            balance = position * current_price
            trade_pnl = (current_price - trades[-1]['price']) / trades[-1]['price'] * 100
            
            trade_history.append({
                'entry_time': trades[-1]['timestamp'],
                'exit_time': current_time,
                'entry_price': trades[-1]['price'],
                'exit_price': current_price,
                'position': position,
                'pnl_percent': trade_pnl,
                'duration_minutes': (current_time - trades[-1]['timestamp']).total_seconds() / 60
            })
            
            trades.append({
                'type': 'sell',
                'timestamp': current_time,
                'price': current_price,
                'position': 0,
                'balance': balance
            })
            position = 0
    
    # 最后强制平仓
    if position > 0 and len(df) > 0:
        current_price = df['close'].iloc[-1]
        balance = position * current_price
        trades.append({
            'type': 'sell',
            'timestamp': df['timestamp'].iloc[-1],
            'price': current_price,
            'position': 0,
            'balance': balance
        })
    
    return trades, trade_history, balance

def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

def calculate_bollinger_bands(prices, window=20, num_std=2):
    """计算布林带"""
    middle = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return upper, middle, lower

def create_candlestick_chart(df, trades, output_file='backtest_chart.html'):
    """创建K线图并标注交易点"""
    # 创建子图
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=('BTC/USDT 价格走势', '成交量', 'RSI指标', 'MACD指标')
    )
    
    # 1. K线图
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='价格'
        ),
        row=1, col=1
    )
    
    # 添加移动平均线
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['sma20'],
            name='SMA20',
            line=dict(color='orange', width=1)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['sma50'],
            name='SMA50',
            line=dict(color='blue', width=1)
        ),
        row=1, col=1
    )
    
    # 标注买入点
    buy_times = [t['timestamp'] for t in trades if t['type'] == 'buy']
    buy_prices = [t['price'] for t in trades if t['type'] == 'buy']
    
    fig.add_trace(
        go.Scatter(
            x=buy_times,
            y=buy_prices,
            mode='markers',
            name='买入',
            marker=dict(
                symbol='triangle-up',
                size=10,
                color='green',
                line=dict(width=2, color='darkgreen')
            )
        ),
        row=1, col=1
    )
    
    # 标注卖出点
    sell_times = [t['timestamp'] for t in trades if t['type'] == 'sell']
    sell_prices = [t['price'] for t in trades if t['type'] == 'sell']
    
    fig.add_trace(
        go.Scatter(
            x=sell_times,
            y=sell_prices,
            mode='markers',
            name='卖出',
            marker=dict(
                symbol='triangle-down',
                size=10,
                color='red',
                line=dict(width=2, color='darkred')
            )
        ),
        row=1, col=1
    )
    
    # 2. 成交量图
    colors = ['green' if close >= open else 'red' 
              for close, open in zip(df['close'], df['open'])]
    
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name='成交量',
            marker_color=colors
        ),
        row=2, col=1
    )
    
    # 3. RSI图
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['rsi'],
            name='RSI',
            line=dict(color='purple', width=1)
        ),
        row=3, col=1
    )
    
    # 添加RSI超买超卖线
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    # 4. MACD图（如果计算了）
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['macd'],
                name='MACD',
                line=dict(color='blue', width=1)
            ),
            row=4, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['macd_signal'],
                name='MACD Signal',
                line=dict(color='red', width=1)
            ),
            row=4, col=1
        )
    
    # 更新布局
    fig.update_layout(
        title='BTC/USDT 回测分析图表',
        xaxis_title='时间',
        yaxis_title='价格 (USDT)',
        height=1200,
        showlegend=True,
        template='plotly_dark'
    )
    
    # 更新x轴
    fig.update_xaxes(rangeslider_visible=False)
    
    # 保存图表
    fig.write_html(output_file)
    print(f"图表已保存到: {output_file}")
    
    return fig

def generate_backtest_report(trades, trade_history, final_balance, initial_balance=10000):
    """生成回测报告"""
    total_trades = len([t for t in trades if t['type'] == 'buy'])
    
    if len(trade_history) > 0:
        winning_trades = len([t for t in trade_history if t['pnl_percent'] > 0])
        losing_trades = len([t for t in trade_history if t['pnl_percent'] <= 0])
        
        win_rate = (winning_trades / len(trade_history)) * 100 if len(trade_history) > 0 else 0
        
        avg_win = np.mean([t['pnl_percent'] for t in trade_history if t['pnl_percent'] > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t['pnl_percent'] for t in trade_history if t['pnl_percent'] <= 0]) if losing_trades > 0 else 0
        
        profit_factor = abs(sum([t['pnl_percent'] for t in trade_history if t['pnl_percent'] > 0]) / 
                           sum([t['pnl_percent'] for t in trade_history if t['pnl_percent'] <= 0])) if losing_trades > 0 else float('inf')
        
        avg_duration = np.mean([t['duration_minutes'] for t in trade_history])
    else:
        winning_trades = losing_trades = win_rate = avg_win = avg_loss = profit_factor = avg_duration = 0
    
    total_return = ((final_balance - initial_balance) / initial_balance) * 100
    
    report = {
        'initial_balance': initial_balance,
        'final_balance': final_balance,
        'total_return_percent': total_return,
        'total_trades': total_trades,
        'completed_trades': len(trade_history),
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate_percent': win_rate,
        'average_win_percent': avg_win,
        'average_loss_percent': avg_loss,
        'profit_factor': profit_factor,
        'average_trade_duration_minutes': avg_duration,
        'max_consecutive_wins': calculate_max_consecutive(trade_history, 'win'),
        'max_consecutive_losses': calculate_max_consecutive(trade_history, 'loss'),
        'largest_win_percent': max([t['pnl_percent'] for t in trade_history]) if trade_history else 0,
        'largest_loss_percent': min([t['pnl_percent'] for t in trade_history]) if trade_history else 0,
        'sharpe_ratio': calculate_sharpe_ratio(trade_history) if trade_history else 0,
        'calmar_ratio': calculate_calmar_ratio(trade_history, total_return) if trade_history else 0
    }
    
    return report

def calculate_max_consecutive(trade_history, trade_type):
    """计算最大连续盈利/亏损"""
    if not trade_history:
        return 0
    
    max_streak = 0
    current_streak = 0
    
    for trade in trade_history:
        is_win = trade['pnl_percent'] > 0
        
        if (trade_type == 'win' and is_win) or (trade_type == 'loss' and not is_win):
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    
    return max_streak

def calculate_sharpe_ratio(trade_history, risk_free_rate=0.02):
    """计算夏普比率"""
    if not trade_history:
        return 0
    
    returns = [trade['pnl_percent'] / 100 for trade in trade_history]  # 转换为小数
    
    if len(returns) < 2:
        return 0
    
    avg_return = np.mean(returns)
    std_return = np.std(returns)
    
    if std_return == 0:
        return 0
    
    # 年化夏普比率
    sharpe = (avg_return - risk_free_rate/252) / std_return * np.sqrt(252)
    
    return sharpe

def calculate_calmar_ratio(trade_history, total_return_percent, lookback_period=36):
    """计算Calmar比率"""
    if not trade_history or len(trade_history) < lookback_period:
        return 0
    
    # 计算最大回撤
    balances = [10000]  # 初始资金
    for trade in trade_history[-lookback_period:]:  # 最近36个月易
        balances.append(balances[-1] * (1 + trade['pnl_percent']/100))
    
    peak = balances[0]
    max_drawdown = 0
    
    for balance in balances:
        if balance > peak:
            peak = balance
        drawdown = (peak - balance) / peak * 100
        max_drawdown = max(max_drawdown, drawdown)
    
    if max_drawdown == 0:
        return 0
    
    # 年化Calmar比率
    calmar = (total_return_percent / 100) / (max_drawdown / 100)
    
    return calmar

def main():
    print("开始增强版回测分析...")
    
    # 1. 加载数据
    df = load_historical_data()
    if df is None:
        print("无法加载数据，退出")
        return
    
    print(f"数据时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
    
    # 2. 运行两种策略的回测
    print("\n运行简单RSI策略回测...")
    simple_trades, simple_history, simple_balance = simulate_trades_with_strategy(df, 'simple')
    
    print("\n运行优化策略回测...")
    optimized_trades, optimized_history, optimized_balance = simulate_trades_with_strategy(df, 'optimized')
    
    # 3. 生成报告
    print("\n" + "="*50)
    print("简单RSI策略回测结果:")
    print("="*50)
    simple_report = generate_backtest_report(simple_trades, simple_history, simple_balance)
    print(f"初始资金: ${simple_report['initial_balance']:,.2f}")
    print(f"最终资金: ${simple_report['final_balance']:,.2f}")
    print(f"总收益率: {simple_report['total_return_percent']:.2f}%")
    print(f"总交易次数: {simple_report['total_trades']}")
    print(f"胜率: {simple_report['win_rate_percent']:.1f}%")
    print(f"平均盈利: {simple_report['average_win_percent']:.2f}%")
    print(f"平均亏损: {simple_report['average_loss_percent']:.2f}%")
    print(f"盈亏比: {simple_report['profit_factor']:.2f}")
    
    print("\n" + "="*50)
    print("优化策略回测结果:")
    print("="*50)
    optimized_report = generate_backtest_report(optimized_trades, optimized_history, optimized_balance)
    print(f"初始资金: ${optimized_report['initial_balance']:,.2f}")
    print(f"最终资金: ${optimized_report['final_balance']:,.2f}")
    print(f"总收益率: {optimized_report['total_return_percent']:.2f}%")
    print(f"总交易次数: {optimized_report['total_trades']}")
    print(f"胜率: {optimized_report['win_rate_percent']:.1f}%")
    print(f"平均盈利: {optimized_report['average_win_percent']:.2f}%")
    print(f"平均亏损: {optimized_report['average_loss_percent']:.2f}%")
    print(f"盈亏比: {optimized_report['profit_factor']:.2f}")
    print(f"夏普比率: {optimized_report['sharpe_ratio']:.2f}")
    print(f"Calmar比率: {optimized_report['calmar_ratio']:.2f}")
    
    # 4. 保存报告
    reports = {
        'simple_strategy': simple_report,
        'optimized_strategy': optimized_report,
        'trade_history': {
            'simple': simple_history,
            'optimized': optimized_history
        },
        'timestamp': datetime.now().isoformat(),
        'data_period': {
            'start': df['timestamp'].min().isoformat(),
            'end': df['timestamp'].max().isoformat(),
            'total_candles': len(df)
        }
    }
    
    report_file = '/Users/anth6iu/freqtrade-trading/backtest_enhanced_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(reports, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n详细报告已保存到: {report_file}")
    
    # 5. 创建K线图表
    print("\n创建K线图表...")
    chart_file = '/Users/anth6iu/freqtrade-trading/backtest_chart.html'
    
    # 使用优化策略的交易数据创建图表
    fig = create_candlestick_chart(df, optimized_trades, chart_file)
    
    # 6. 创建交易历史表格
    create_trade_history_table(optimized_history, '/Users/anth6iu/freqtrade-trading/trade_history.html')
    
    print("\n" + "="*50)
    print("回测分析完成!")
    print("="*50)
    print(f"1. 详细报告: {report_file}")
    print(f"2. K线图表: {chart_file}")
    print(f"3. 交易历史: /Users/anth6iu/freqtrade-trading/trade_history.html")
    print(f"4. 优化策略文件: /Users/anth6iu/freqtrade-trading/user_data/strategies/OptimizedStrategy.py")
    
    # 7. 显示关键建议
    print("\n" + "="*50)
    print("策略优化建议:")
    print("="*50)
    
    if optimized_report['total_return_percent'] > simple_report['total_return_percent']:
        improvement = optimized_report['total_return_percent'] - simple_report['total_return_percent']
        print(f"✅ 优化策略比简单策略表现好 {improvement:.2f}%")
    else:
        print("⚠️  优化策略需要进一步调整")
    
    if optimized_report['win_rate_percent'] > 50:
        print(f"✅ 胜率良好: {optimized_report['win_rate_percent']:.1f}%")
    else:
        print(f"⚠️  胜率偏低: {optimized_report['win_rate_percent']:.1f}%")
    
    if optimized_report['profit_factor'] > 1.5:
        print(f"✅ 盈亏比优秀: {optimized_report['profit_factor']:.2f}")
    elif optimized_report['profit_factor'] > 1.0:
        print(f"📊 盈亏比可接受: {optimized_report['profit_factor']:.2f}")
    else:
        print(f"⚠️  盈亏比需要改善: {optimized_report['profit_factor']:.2f}")
    
    if optimized_report['sharpe_ratio'] > 1.0:
        print(f"✅ 夏普比率优秀: {optimized_report['sharpe_ratio']:.2f}")
    else:
        print(f"📊 夏普比率: {optimized_report['sharpe_ratio']:.2f}")
    
    print("\n下一步建议:")
    print("1. 在浏览器中打开 backtest_chart.html 查看K线图和交易点")
    print("2. 查看 trade_history.html 了解每笔交易的详细信息")
    print("3. 根据报告结果进一步调整 OptimizedStrategy.py 中的参数")
    print("4. 考虑添加更多技术指标或机器学习模型")
    print("5. 在不同时间周期上测试策略的稳定性")

def create_trade_history_table(trade_history, output_file):
    """创建交易历史HTML表格"""
    if not trade_history:
        print("没有交易历史数据")
        return
    
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>交易历史记录</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 20px;
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background-color: #2d2d2d;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }
            h1 {
                color: #4CAF50;
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 10px;
            }
            .summary {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            .summary-card {
                background: linear-gradient(135deg, #2c3e50, #4CAF50);
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }
            .summary-card h3 {
                margin: 0 0 10px 0;
                font-size: 14px;
                color: #b0b0b0;
            }
            .summary-card .value {
                font-size: 24px;
                font-weight: bold;
                color: white;
            }
            .summary-card .value.positive {
                color: #4CAF50;
            }
            .summary-card .value.negative {
                color: #f44336;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background-color: #3d3d3d;
            }
            th {
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                text-align: left;
                position: sticky;
                top: 0;
            }
            td {
                padding: 10px;
                border-bottom: 1px solid #555;
            }
            tr:hover {
                background-color: #4d4d4d;
            }
            .profit {
                color: #4CAF50;
                font-weight: bold;
            }
            .loss {
                color: #f44336;
                font-weight: bold;
            }
            .win-rate-bar {
                height: 20px;
                background-color: #555;
                border-radius: 10px;
                margin: 5px 0;
                overflow: hidden;
            }
            .win-rate-fill {
                height: 100%;
                background: linear-gradient(90deg, #4CAF50, #8BC34A);
                border-radius: 10px;
            }
            .filter-controls {
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            .filter-controls select, .filter-controls input {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #555;
                background-color: #3d3d3d;
                color: white;
            }
            .export-btn {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-left: auto;
            }
            .export-btn:hover {
                background-color: #45a049;
            }
            @media (max-width: 768px) {
                .container {
                    padding: 10px;
                }
                table {
                    font-size: 12px;
                }
                th, td {
                    padding: 6px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 交易历史记录</h1>
            
            <div class="summary">
                <div class="summary-card">
                    <h3>总交易数</h3>
                    <div class="value">""" + str(len(trade_history)) + """</div>
                </div>
    """
    
    # 计算统计数据
    winning_trades = [t for t in trade_history if t['pnl_percent'] > 0]
    losing_trades = [t for t in trade_history if t['pnl_percent'] <= 0]
    win_rate = (len(winning_trades) / len(trade_history) * 100) if trade_history else 0
    total_profit = sum(t['pnl_percent'] for t in trade_history)
    avg_profit = np.mean([t['pnl_percent'] for t in trade_history]) if trade_history else 0
    max_profit = max([t['pnl_percent'] for t in trade_history]) if trade_history else 0
    max_loss = min([t['pnl_percent'] for t in trade_history]) if trade_history else 0
    
    html += f"""
                <div class="summary-card">
                    <h3>胜率</h3>
                    <div class="value">{win_rate:.1f}%</div>
                    <div class="win-rate-bar">
                        <div class="win-rate-fill" style="width: {win_rate}%"></div>
                    </div>
                </div>
                
                <div class="summary-card">
                    <h3>总收益</h3>
                    <div class="value {'positive' if total_profit > 0 else 'negative'}">{total_profit:.2f}%</div>
                </div>
                
                <div class="summary-card">
                    <h3>平均收益</h3>
                    <div class="value {'positive' if avg_profit > 0 else 'negative'}">{avg_profit:.2f}%</div>
                </div>
                
                <div class="summary-card">
                    <h3>最大盈利</h3>
                    <div class="value positive">{max_profit:.2f}%</div>
                </div>
                
                <div class="summary-card">
                    <h3>最大亏损</h3>
                    <div class="value negative">{max_loss:.2f}%</div>
                </div>
            </div>
            
            <div class="filter-controls">
                <select id="filterResult">
                    <option value="all">所有交易</option>
                    <option value="profit">盈利交易</option>
                    <option value="loss">亏损交易</option>
                </select>
                <input type="number" id="minProfit" placeholder="最小盈利%" step="0.1">
                <input type="number" id="maxProfit" placeholder="最大盈利%" step="0.1">
                <button class="export-btn" onclick="exportToCSV()">📥 导出CSV</button>
            </div>
            
            <table id="tradeTable">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>入场时间</th>
                        <th>出场时间</th>
                        <th>持仓时间(分钟)</th>
                        <th>入场价格</th>
                        <th>出场价格</th>
                        <th>仓位大小</th>
                        <th>收益率%</th>
                        <th>结果</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # 添加交易行
    for i, trade in enumerate(trade_history, 1):
        pnl_class = "profit" if trade['pnl_percent'] > 0 else "loss"
        result_text = "盈利" if trade['pnl_percent'] > 0 else "亏损"
        
        html += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{trade['entry_time']}</td>
                        <td>{trade['exit_time']}</td>
                        <td>{trade['duration_minutes']:.1f}</td>
                        <td>${trade['entry_price']:,.2f}</td>
                        <td>${trade['exit_price']:,.2f}</td>
                        <td>{trade['position']:.6f}</td>
                        <td class="{pnl_class}">{trade['pnl_percent']:.2f}%</td>
                        <td><span class="{pnl_class}">●</span> {result_text}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
        
        <script>
            // 过滤功能
            document.getElementById('filterResult').addEventListener('change', filterTable);
            document.getElementById('minProfit').addEventListener('input', filterTable);
            document.getElementById('maxProfit').addEventListener('input', filterTable);
            
            function filterTable() {
                const filterResult = document.getElementById('filterResult').value;
                const minProfit = parseFloat(document.getElementById('minProfit').value) || -Infinity;
                const maxProfit = parseFloat(document.getElementById('maxProfit').value) || Infinity;
                
                const rows = document.querySelectorAll('#tradeTable tbody tr');
                
                rows.forEach(row => {
                    const pnlCell = row.cells[7];
                    const pnl = parseFloat(pnlCell.textContent);
                    const isProfit = pnl > 0;
                    
                    let show = true;
                    
                    // 根据结果过滤
                    if (filterResult === 'profit' && !isProfit) show = false;
                    if (filterResult === 'loss' && isProfit) show = false;
                    
                    // 根据盈利范围过滤
                    if (pnl < minProfit || pnl > maxProfit) show = false;
                    
                    row.style.display = show ? '' : 'none';
                });
            }
            
            function exportToCSV() {
                const rows = document.querySelectorAll('#tradeTable tbody tr');
                let csv = '序号,入场时间,出场时间,持仓时间(分钟),入场价格,出场价格,仓位大小,收益率%,结果\\n';
                
                rows.forEach(row => {
                    if (row.style.display !== 'none') {
                        const cells = row.cells;
                        const rowData = [
                            cells[0].textContent,
                            cells[1].textContent,
                            cells[2].textContent,
                            cells[3].textContent,
                            cells[4].textContent.replace('$', '').replace(',', ''),
                            cells[5].textContent.replace('$', '').replace(',', ''),
                            cells[6].textContent,
                            cells[7].textContent.replace('%', ''),
                            cells[8].textContent.includes('盈利') ? '盈利' : '亏损'
                        ];
                        csv += rowData.join(',') + '\\n';
                    }
                });
                
                const blob = new Blob(['\\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', 'trade_history_' + new Date().toISOString().slice(0,10) + '.csv');
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
            
            // 初始排序（按收益率降序）
            let table = document.getElementById('tradeTable');
            let tbody = table.querySelector('tbody');
            let rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.sort((a, b) => {
                let aPnl = parseFloat(a.cells[7].textContent);
                let bPnl = parseFloat(b.cells[7].textContent);
                return bPnl - aPnl;
            });
            
            rows.forEach(row => tbody.appendChild(row));
        </script>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"交易历史表格已保存到: {output_file}")

if __name__ == '__main__':
    main()
